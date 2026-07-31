"""The governed six-role signal-intelligence pipeline (TRL-R2-006 Section 2).

A pure function: given an already-validated
``signal_data.validate_evaluation_request()`` result, runs Roles 1-6 in
their approved order and returns a fully validated ``TRL_SIGNAL_PROPOSAL.v1``
document plus the ordered per-role audit trail. No timeline, storage, mode,
or network access happens here — ``signal_service.py`` is the only caller,
and it owns persistence, mode-gating, and evidence-existence checks against
its own governed timeline.

A ``BLOCKED`` result from any mandatory role stops every downstream role
from being able to authorize a proposal: this is enforced structurally by
early return, not by a flag a later role could ignore or a caller could
skip. Role 4, 5, and 6 still run and are still recorded even when the
Role 3 candidate is HOLD/WAIT, because there is always something to audit
(they simply cannot reject a non-actionable candidate — see each role
module). An unexpected internal exception anywhere in the six roles is
caught here and converted into a fully auditable
``BLOCKED``/``PIPELINE_INTERNAL_ERROR`` proposal (Section 8) rather than
propagating or silently producing an unaudited result.
"""

from copy import deepcopy

from . import signal_confidence
from . import signal_data as sd
from . import signal_llm_adapter as llm_adapter
from . import signal_role1_data_quality as role1
from . import signal_role2_market_regime as role2
from . import signal_role3_strategy as role3
from . import signal_role4_news_risk as role4
from . import signal_role5_independent_risk as role5
from . import signal_role6_execution_eligibility as role6
from . import signal_strategy_registry as registry
from .timeline_data import canonical_decimal, decimal_value, validate_utc_timestamp
from datetime import timedelta


PIPELINE_VERSION = "1.0.0"
RISK_ENGINE_VERSION = "1.0.0"

_NOT_EVALUATED = {"status": "NOT_EVALUATED", "reasons": []}
_NOT_EVALUATED_NEWS = {"status": "NOT_EVALUATED", "reasons": [], "evidence_ids": []}


def _wait_shaped_role_result(role_name, default):
    return deepcopy(default)


def evaluate(request, operating_mode, adapter=None):
    adapter = adapter or llm_adapter.NoOpGenerativeAdapter()
    working_request = dict(request)
    working_request["feature_snapshot_hash"] = sd.feature_snapshot_hash_for(request["feature_material"])

    role_results = {name: _wait_shaped_role_result(name, _NOT_EVALUATED) for name in sd.ROLE_NAMES}
    role_results["news_event_risk"] = deepcopy(_NOT_EVALUATED_NEWS)
    step_results = []

    def record(name, result):
        role_results[name] = result
        step_results.append((name, result))
        return result

    try:
        r1 = record("data_quality", role1.evaluate(working_request))
        if r1["status"] != role1.PASS:
            return _finish(
                working_request, operating_mode, role_results, step_results,
                "BLOCKED", "DATA_QUALITY_REJECTED", None, None, None, adapter,
            )

        r2 = record("market_regime", role2.evaluate(working_request))
        if r2["status"] != role2.PASS:
            return _finish(
                working_request, operating_mode, role_results, step_results,
                "BLOCKED", "REGIME_UNCLASSIFIABLE", r2, None, None, adapter,
            )

        r3 = record("technical_strategy", role3.evaluate(working_request))
        if r3["status"] != role3.PASS:
            return _finish(
                working_request, operating_mode, role_results, step_results,
                "BLOCKED", "NO_STRATEGY_SIGNAL", r2, r3, None, adapter,
            )
        candidate_side = r3["side"]

        r4 = record("news_event_risk", role4.evaluate(working_request, candidate_side))
        if r4["status"] != role4.PASS:
            return _finish(
                working_request, operating_mode, role_results, step_results,
                "BLOCKED", "NEWS_EVENT_RISK_BLOCK", r2, r3, None, adapter,
            )

        entry_reference = None
        if candidate_side in ("BUY", "SELL"):
            entry_reference = canonical_decimal(
                (decimal_value(r3["entry_zone_lower"]) + decimal_value(r3["entry_zone_upper"])) / 2
            )
        r5 = record("independent_risk", role5.evaluate(
            working_request, candidate_side, entry_reference,
            r3.get("stop_loss"), r3.get("candidate_quantity"),
        ))
        if r5["status"] != role5.PASS:
            code = (
                "SIZE_MISMATCH_BETWEEN_PARTNERS"
                if r5["status"] == role5.SIZE_MISMATCH_BETWEEN_PARTNERS
                else "RISK_REJECTED"
            )
            return _finish(
                working_request, operating_mode, role_results, step_results,
                "BLOCKED", code, r2, r3, r5, adapter,
            )

        r6 = record("execution_eligibility", role6.evaluate(working_request, candidate_side))
        if r6["status"] != role6.PASS:
            return _finish(
                working_request, operating_mode, role_results, step_results,
                "BLOCKED", "EXECUTION_INELIGIBLE", r2, r3, r5, adapter,
            )

        return _finish(
            working_request, operating_mode, role_results, step_results,
            candidate_side, None, r2, r3, r5, adapter,
        )
    except Exception:
        return _finish(
            working_request, operating_mode, role_results, step_results,
            "BLOCKED", "PIPELINE_INTERNAL_ERROR", None, None, None, adapter,
        )


def _finish(request, operating_mode, role_results, step_results, side, block_code, r2, r3, r5, adapter):
    evaluated_at = request["evaluated_at_utc"]
    expires_at = validate_utc_timestamp(evaluated_at) + timedelta(seconds=request["expires_after_seconds"])
    from .timeline_data import format_utc
    expires_at_text = format_utc(expires_at)

    regime_classification = (r2 or {}).get("classification", "UNKNOWN")
    strategy_record = registry.get_strategy(request["strategy_id"])
    strategy_version = (r3 or {}).get("strategy_version") or (
        strategy_record["strategy_version"] if strategy_record else "0.0.0"
    )
    candidate_quantity = (r3 or {}).get("candidate_quantity") if side in ("BUY", "SELL") else None
    independent_quantity = (r5 or {}).get("independent_quantity") if side in ("BUY", "SELL") else None

    confidence_score, calibration_source, confidence_status, _breakdown = signal_confidence.compute_confidence(
        side if side in ("BUY", "SELL") else None,
        regime_classification,
        len(request["bar_series"]),
    )

    model_annotation = llm_adapter.annotate_safely(adapter, {
        "model_hypothesis": request.get("model_hypothesis"),
        "final_side": side,
        "block_code": block_code,
    })

    is_executable = side in ("BUY", "SELL")
    is_blocked = side == "BLOCKED"

    common = dict(
        created_at_utc=evaluated_at,
        observed_at_utc=evaluated_at,
        expires_at_utc=expires_at_text,
        instrument=request["instrument"],
        side=side,
        strategy_id=request["strategy_id"],
        strategy_version=strategy_version,
        broker_native_instrument=request["broker_native_instrument"],
        regime_classification=regime_classification,
        feature_snapshot_hash=request["feature_snapshot_hash"],
        data_quality_result=role_results["data_quality"],
        news_event_risk_result=role_results["news_event_risk"],
        confidence_score=confidence_score,
        confidence_calibration_source=calibration_source,
        confidence_status=confidence_status,
        rejection_reasons=[block_code] if is_blocked else [],
        model_rule_versions={
            "strategy_version": strategy_version,
            "risk_engine_version": RISK_ENGINE_VERSION,
            "pipeline_version": PIPELINE_VERSION,
        },
        role_results=role_results,
        maximum_spread=request["risk_policy"]["maximum_spread"],
        active_risk_policy_hash=sd.risk_policy_hash(request["risk_policy"]),
        operating_mode=operating_mode,
        sample_label=request["sample_label"],
        market_data_observation_id=request["market_data_observation_id"],
        news_observation_ids=request["news_context"]["evidence_ids"],
        economic_event_observation_ids=[],
        strategy_basis_ids=["{}.PHASE4_PIPELINE".format(request["strategy_id"])],
        research_basis_ids=["TRL-R2-006.SIGNAL_INTELLIGENCE"],
    )

    if is_executable:
        proposal = sd.build_signal_proposal(
            **common,
            entry_type="ENTRY_ZONE",
            entry_zone_lower=r3["entry_zone_lower"],
            entry_zone_upper=r3["entry_zone_upper"],
            stop_loss=r3["stop_loss"],
            targets=r3["targets"],
            target_allocations_percent=r3["target_allocations_percent"],
            evidence_quality_status="GOVERNED",
            invalidation_reason=(
                "The governed crossover condition that produced this candidate no "
                "longer holds on subsequent governed bars."
            ),
            wait_reason=None,
            beginner_explanation=(
                "Research-only signal proposal from a deterministic six-role "
                "pipeline. Not financial advice and not a trade instruction."
            ),
            explanation=(
                "Regime={}; strategy={} produced a {} candidate; all six governed "
                "roles passed. {}".format(
                    regime_classification, request["strategy_id"], side,
                    signal_confidence.CONFIDENCE_DISCLAIMER,
                )
            ),
            risk_percent=request["risk_policy"]["risk_percent"],
            candidate_quantity=candidate_quantity,
            independent_quantity=independent_quantity,
        )
    else:
        wait_text = {
            "HOLD": "No actionable setup on the latest governed evidence; nothing to watch right now.",
            "WAIT": "Governed evidence is forming but is not yet sufficient for a signal.",
            "BLOCKED": "A governed role rejected this evaluation; see rejection_reasons.",
        }[side]
        proposal = sd.build_signal_proposal(
            **common,
            entry_type="WAIT",
            entry_zone_lower=None,
            entry_zone_upper=None,
            stop_loss=None,
            targets=None,
            target_allocations_percent=None,
            evidence_quality_status="GOVERNED" if side != "BLOCKED" else "LIMITED",
            invalidation_reason=(
                "Not applicable: no executable setup exists for this evaluation."
            ),
            wait_reason=wait_text,
            beginner_explanation=(
                "Research-only signal evaluation from a deterministic six-role "
                "pipeline. Not financial advice and not a trade instruction."
            ),
            explanation="{} outcome for strategy {}. {}".format(
                side, request["strategy_id"], signal_confidence.CONFIDENCE_DISCLAIMER,
            ),
            risk_percent="0",
            candidate_quantity=None,
            independent_quantity=None,
        )

    return {
        "proposal": proposal,
        "role_step_results": step_results,
        "model_annotation": model_annotation,
    }


__all__ = ("PIPELINE_VERSION", "RISK_ENGINE_VERSION", "evaluate")
