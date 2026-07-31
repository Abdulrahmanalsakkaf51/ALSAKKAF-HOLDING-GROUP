"""Role 1 — Data Quality Partner (TRL-R2-006 Section 2).

Validates observation freshness, spread sanity, and bar/feature
completeness from governed evidence only. A pure function: no timeline,
storage, or network access. The orchestrator (``signal_pipeline.py``)
records this role's returned result as an append-only
``SIGNAL_PIPELINE_STEP`` audit event; this module never writes evidence
itself.
"""

from decimal import Decimal

from .timeline_data import decimal_value, validate_utc_timestamp


ROLE_NAME = "data_quality"
PASS = "PASS"
DATA_QUALITY_REJECTED = "DATA_QUALITY_REJECTED"

MAX_OBSERVATION_AGE_SECONDS = 300
MAX_SPREAD_TO_BID_RATIO = Decimal("0.10")

REASON_MARKET_EVIDENCE_STALE = "MARKET_EVIDENCE_STALE"
REASON_MARKET_EVIDENCE_FUTURE_DATED = "MARKET_EVIDENCE_FUTURE_DATED"
REASON_SPREAD_DATA_INVALID = "SPREAD_DATA_INVALID"
REASON_BAR_SERIES_NON_CAUSAL = "BAR_SERIES_NON_CAUSAL"
REASON_FEATURE_SNAPSHOT_UNAVAILABLE = "FEATURE_SNAPSHOT_UNAVAILABLE"
REASON_MARKET_EVIDENCE_NOT_FOUND = "MARKET_EVIDENCE_NOT_FOUND"
REASON_MARKET_EVIDENCE_HASH_MISMATCH = "MARKET_EVIDENCE_HASH_MISMATCH"


def evaluate(request):
    """request must already be ``signal_data.validate_evaluation_request()``
    output. Returns a bounded typed result dict; never raises for governed
    (already-schema-valid) input — a schema defect upstream is the caller's
    responsibility, not this role's.

    ``signal_service.py`` verifies, before calling this role, that
    ``market_data_observation_id`` actually resolves to an existing
    ``MARKET_OBSERVATION`` timeline event whose stored payload hash
    matches the observation embedded in this request (evidence existence
    and evidence-hash-mismatch checks per Section 6.2), and communicates
    the result via the private ``_evidence_integrity_ok``/
    ``_evidence_integrity_reason`` request fields consumed below. These
    are not part of the governed ``TRL_SIGNAL_EVALUATION_REQUEST.v1``
    schema; they exist only to let this role's failure surface the
    service's evidence-integrity check through the same governed
    DATA_QUALITY_REJECTED failure path as every other Role 1 reason."""
    reasons = []
    if request.get("_evidence_integrity_ok", True) is False:
        reasons.append(request.get("_evidence_integrity_reason") or REASON_MARKET_EVIDENCE_STALE)
    evaluated_at = validate_utc_timestamp(request["evaluated_at_utc"])
    occurred_at = validate_utc_timestamp(request["market_observation_occurred_at_utc"])
    observed_at = validate_utc_timestamp(request["market_observation_first_observed_at_utc"])
    metadata_observed_at = validate_utc_timestamp(
        request["market_observation"]["metadata_observed_at_utc"]
    )

    if occurred_at > observed_at or metadata_observed_at > observed_at:
        reasons.append(REASON_MARKET_EVIDENCE_FUTURE_DATED)
    else:
        age_seconds = (evaluated_at - observed_at).total_seconds()
        metadata_age_seconds = (evaluated_at - metadata_observed_at).total_seconds()
        if age_seconds < 0 or metadata_age_seconds < 0:
            reasons.append(REASON_MARKET_EVIDENCE_FUTURE_DATED)
        elif age_seconds > MAX_OBSERVATION_AGE_SECONDS or metadata_age_seconds > MAX_OBSERVATION_AGE_SECONDS:
            reasons.append(REASON_MARKET_EVIDENCE_STALE)

    observation = request["market_observation"]
    bid = decimal_value(observation["bid"])
    spread = decimal_value(observation["spread"])
    if bid <= 0 or spread <= 0 or spread > bid * MAX_SPREAD_TO_BID_RATIO:
        reasons.append(REASON_SPREAD_DATA_INVALID)

    last_bar_date = validate_utc_timestamp(request["bar_series"][-1]["date"])
    if last_bar_date > evaluated_at:
        reasons.append(REASON_BAR_SERIES_NON_CAUSAL)

    feature_hash = request.get("feature_snapshot_hash")
    if not feature_hash:
        reasons.append(REASON_FEATURE_SNAPSHOT_UNAVAILABLE)

    status = DATA_QUALITY_REJECTED if reasons else PASS
    return {
        "status": status,
        "reasons": reasons,
        "observation_age_seconds": max(0, int((evaluated_at - observed_at).total_seconds())),
        "spread": observation["spread"],
        "bid": observation["bid"],
    }


__all__ = (
    "DATA_QUALITY_REJECTED",
    "MAX_OBSERVATION_AGE_SECONDS",
    "MAX_SPREAD_TO_BID_RATIO",
    "PASS",
    "ROLE_NAME",
    "evaluate",
)
