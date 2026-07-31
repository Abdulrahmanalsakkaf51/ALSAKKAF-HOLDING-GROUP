"""Governed research performance / walk-forward reporting (TRL-R2-006).

Research reporting only. This module never places an order, never calls
``order_check`` or ``order_send``, never connects to MT5, never claims live
performance, does not approve SMA-001 execution geometry (see
``signal_role3_strategy.py``), and does not resolve FIB-001's approval
blocker.

Every report covers exactly one governed sample label (Section 7):
``IN_SAMPLE``, ``VALIDATION``, ``OUT_OF_SAMPLE``, ``WALK_FORWARD``,
``SYNTHETIC_PAPER``, ``BROKER_DEMO``, or ``BROKER_LIVE`` — callers generate
one report per label rather than blending samples into a single headline
number; there is no code path in this module that combines proposals
carrying different ``sample_label`` values into one report.

Because no SMA-001 execution geometry is Founder-approved yet (Role 3
fails closed with ``STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED`` on every
crossing), no signal proposal in this checkpoint can ever become a filled
or completed trade. ``completed_trade_count``, ``open_position_count``,
and ``incomplete_trade_count`` are therefore always zero here — honestly,
not fabricated from direction-only research proposals — and any report
covering fewer than ``MINIMUM_COMPLETED_TRADES`` completed trades (which is
every report in this checkpoint) is marked ``INSUFFICIENT_SAMPLE`` rather
than silently implying validated performance.
"""

from copy import deepcopy

from . import signal_confidence
from . import signal_data as sd
from .paper_data import PaperConfiguration, canonical_decimal
from .timeline_data import (
    TimelineValidationError,
    deterministic_json_text,
    sha256_text,
    validate_utc_timestamp,
)


REPORT_SCHEMA = "TRL_SIGNAL_PERFORMANCE_REPORT.v1"
MINIMUM_COMPLETED_TRADES = 20
SAMPLE_SUFFICIENT = "SUFFICIENT"
SAMPLE_INSUFFICIENT = "INSUFFICIENT_SAMPLE"
NO_BROKER_EXECUTION_STATEMENT = "NO_BROKER_EXECUTION_OCCURRED"
NO_GUARANTEED_PERFORMANCE_STATEMENT = "NO_GUARANTEED_PERFORMANCE_CLAIM_MADE"
OUTCOME_SIDES = ("BUY", "SELL", "HOLD", "WAIT", "BLOCKED")
MAX_PROPOSALS_PER_REPORT = 5000
MAX_SEGMENTS = 200
MAX_TEXT_ITEMS = 32
MAX_TEXT_LENGTH = 500

REPORT_FIELDS = (
    "schema_version",
    "report_id",
    "created_at_utc",
    "strategy_id",
    "strategy_version",
    "sample_label",
    "sample_start_at_utc",
    "sample_end_at_utc",
    "dataset_proposal_ids",
    "dataset_hash",
    "walk_forward_segments",
    "proposal_count",
    "buy_count",
    "sell_count",
    "hold_count",
    "wait_count",
    "blocked_count",
    "completed_trade_count",
    "open_position_count",
    "incomplete_trade_count",
    "minimum_completed_trades",
    "sample_status",
    "fee_assumption",
    "slippage_assumption",
    "spread_assumption",
    "assumptions",
    "limitations",
    "confidence_calibration_status",
    "broker_execution_statement",
    "guaranteed_performance_statement",
    "canonical_report_hash",
)

SEGMENT_FIELDS = (
    "segment_id",
    "start_at_utc",
    "end_at_utc",
    "proposal_count",
    "buy_count",
    "sell_count",
    "hold_count",
    "wait_count",
    "blocked_count",
    "completed_trade_count",
    "open_position_count",
    "incomplete_trade_count",
)

DEFAULT_ASSUMPTIONS = (
    "Every proposal is research-only; none was ever submitted to a broker.",
    "No SMA-001 crossing may become an executable BUY/SELL proposal until "
    "a dated Decision Log entry records Founder-approved execution "
    "geometry (see TRL_BLOCKERS.md).",
    "completed_trade_count/open_position_count/incomplete_trade_count are "
    "always zero in this checkpoint because no executable geometry exists "
    "yet, not because trades were evaluated and excluded.",
)

DEFAULT_LIMITATIONS = (
    "This report never reflects live or demo broker performance.",
    "Confidence scores referenced by any proposal in this dataset are "
    "UNCALIBRATED_HEURISTIC and are not used to derive any figure here.",
)


class ReportValidationError(ValueError):
    """A controlled, non-secret report validation failure."""


def _fail(message):
    raise ReportValidationError(message)


def _bounded_text_list(value, field, maximum=MAX_TEXT_ITEMS):
    if not isinstance(value, (list, tuple)) or len(value) > maximum:
        _fail("{} must be a bounded list".format(field))
    clean = []
    for item in value:
        if not isinstance(item, str) or not item or len(item) > MAX_TEXT_LENGTH:
            _fail("{} contains an invalid entry".format(field))
        clean.append(item)
    return clean


def _outcome_counts(proposals):
    counts = {side: 0 for side in OUTCOME_SIDES}
    for proposal in proposals:
        side = proposal["side"]
        if side not in counts:
            _fail("dataset proposal has an ungoverned side")
        counts[side] += 1
    return counts


def _segment_document(segment_id, start_at_utc, end_at_utc, proposals):
    try:
        start = validate_utc_timestamp(start_at_utc, "segment start_at_utc")
        end = validate_utc_timestamp(end_at_utc, "segment end_at_utc")
    except TimelineValidationError as error:
        raise ReportValidationError(str(error)) from error
    if start >= end:
        _fail("segment start_at_utc must be strictly before end_at_utc")
    counts = _outcome_counts(proposals)
    return {
        "segment_id": segment_id,
        "start_at_utc": start_at_utc,
        "end_at_utc": end_at_utc,
        "proposal_count": len(proposals),
        "buy_count": counts["BUY"],
        "sell_count": counts["SELL"],
        "hold_count": counts["HOLD"],
        "wait_count": counts["WAIT"],
        "blocked_count": counts["BLOCKED"],
        "completed_trade_count": 0,
        "open_position_count": 0,
        "incomplete_trade_count": 0,
    }


def _default_cost_assumptions():
    configuration = PaperConfiguration()
    return {
        "fee_assumption": "{} paper units per unit quantity (research assumption, never charged)".format(
            canonical_decimal(configuration.fee_per_quantity)
        ),
        "slippage_assumption": "{} tick(s) modeled slippage (research assumption, never applied to a real fill)".format(
            canonical_decimal(configuration.slippage_ticks)
        ),
        "spread_assumption": "Each proposal's own governed maximum_spread field (see the proposal dataset)",
    }


def build_report(
    strategy_id,
    strategy_version,
    sample_label,
    proposals,
    created_at_utc,
    sample_start_at_utc,
    sample_end_at_utc,
    walk_forward_segments=None,
    assumptions=None,
    limitations=None,
):
    """proposals: a list of already-validated TRL_SIGNAL_PROPOSAL.v1 dicts.
    walk_forward_segments (only meaningful when sample_label ==
    "WALK_FORWARD"): a list of (segment_id, start_at_utc, end_at_utc,
    segment_proposals) tuples, chronologically ordered and non-overlapping.
    Returns a validated TRL_SIGNAL_PERFORMANCE_REPORT.v1 document; never
    blends more than one sample_label into one report."""
    if sample_label not in sd.SAMPLE_LABELS:
        _fail("sample_label is not governed")
    if not isinstance(proposals, list) or len(proposals) > MAX_PROPOSALS_PER_REPORT:
        _fail("proposals must be a bounded list")
    proposal_ids = []
    for proposal in proposals:
        if proposal.get("sample_label") != sample_label:
            _fail("every proposal in a report must share the report's sample_label")
        if proposal.get("strategy_id") != strategy_id:
            _fail("every proposal in a report must share the report's strategy_id")
        proposal_ids.append(proposal["proposal_id"])
    if len(proposal_ids) != len(set(proposal_ids)):
        _fail("dataset_proposal_ids must not contain a duplicate proposal_id")

    try:
        validate_utc_timestamp(created_at_utc, "created_at_utc")
        start = validate_utc_timestamp(sample_start_at_utc, "sample_start_at_utc")
        end = validate_utc_timestamp(sample_end_at_utc, "sample_end_at_utc")
    except TimelineValidationError as error:
        raise ReportValidationError(str(error)) from error
    if start > end:
        _fail("sample_start_at_utc must not be after sample_end_at_utc")

    segments_doc = []
    if sample_label == "WALK_FORWARD":
        segments = walk_forward_segments or []
        if not segments or len(segments) > MAX_SEGMENTS:
            _fail("WALK_FORWARD reports require at least one bounded segment")
        previous_end = None
        for segment_id, seg_start, seg_end, segment_proposals in segments:
            document = _segment_document(segment_id, seg_start, seg_end, segment_proposals)
            seg_start_dt = validate_utc_timestamp(seg_start)
            if previous_end is not None and seg_start_dt < previous_end:
                _fail("walk-forward segments must be chronologically ordered and non-overlapping")
            previous_end = validate_utc_timestamp(seg_end)
            segments_doc.append(document)
        segment_ids = [item["segment_id"] for item in segments_doc]
        if len(segment_ids) != len(set(segment_ids)):
            _fail("walk-forward segment_id values must be unique")
    elif walk_forward_segments:
        _fail("walk_forward_segments must be empty unless sample_label is WALK_FORWARD")

    counts = _outcome_counts(proposals)
    completed_trade_count = 0
    open_position_count = 0
    incomplete_trade_count = 0
    sample_status = (
        SAMPLE_SUFFICIENT if completed_trade_count >= MINIMUM_COMPLETED_TRADES else SAMPLE_INSUFFICIENT
    )

    cost_assumptions = _default_cost_assumptions()
    clean_assumptions = _bounded_text_list(
        list(DEFAULT_ASSUMPTIONS) + list(assumptions or []), "assumptions"
    )
    clean_limitations = _bounded_text_list(
        list(DEFAULT_LIMITATIONS) + list(limitations or []), "limitations"
    )

    document = {
        "schema_version": REPORT_SCHEMA,
        "created_at_utc": created_at_utc,
        "strategy_id": strategy_id,
        "strategy_version": strategy_version,
        "sample_label": sample_label,
        "sample_start_at_utc": sample_start_at_utc,
        "sample_end_at_utc": sample_end_at_utc,
        "dataset_proposal_ids": sorted(proposal_ids),
        "dataset_hash": sha256_text(deterministic_json_text(sorted(proposal_ids))),
        "walk_forward_segments": segments_doc,
        "proposal_count": len(proposals),
        "buy_count": counts["BUY"],
        "sell_count": counts["SELL"],
        "hold_count": counts["HOLD"],
        "wait_count": counts["WAIT"],
        "blocked_count": counts["BLOCKED"],
        "completed_trade_count": completed_trade_count,
        "open_position_count": open_position_count,
        "incomplete_trade_count": incomplete_trade_count,
        "minimum_completed_trades": MINIMUM_COMPLETED_TRADES,
        "sample_status": sample_status,
        "fee_assumption": cost_assumptions["fee_assumption"],
        "slippage_assumption": cost_assumptions["slippage_assumption"],
        "spread_assumption": cost_assumptions["spread_assumption"],
        "assumptions": clean_assumptions,
        "limitations": clean_limitations,
        "confidence_calibration_status": signal_confidence.CONFIDENCE_STATUSES[0],
        "broker_execution_statement": NO_BROKER_EXECUTION_STATEMENT,
        "guaranteed_performance_statement": NO_GUARANTEED_PERFORMANCE_STATEMENT,
    }
    report_id, digest = _report_id_for(document)
    document["report_id"] = report_id
    document["canonical_report_hash"] = digest
    return validate_report(document)


def _report_id_for(document_without_id):
    material = {key: value for key, value in document_without_id.items() if key not in ("report_id", "canonical_report_hash")}
    digest = sha256_text(deterministic_json_text(material))
    return "spr_" + digest[:32], digest


def validate_report(document):
    if not isinstance(document, dict) or set(document) != set(REPORT_FIELDS):
        _fail("performance report has an invalid field set")
    if document["schema_version"] != REPORT_SCHEMA:
        _fail("performance report schema is unsupported")
    if document["sample_label"] not in sd.SAMPLE_LABELS:
        _fail("sample_label is not governed")
    if document["sample_status"] not in (SAMPLE_SUFFICIENT, SAMPLE_INSUFFICIENT):
        _fail("sample_status is not governed")
    for count_field in (
        "proposal_count", "buy_count", "sell_count", "hold_count", "wait_count",
        "blocked_count", "completed_trade_count", "open_position_count",
        "incomplete_trade_count", "minimum_completed_trades",
    ):
        value = document[count_field]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            _fail("{} must be a non-negative integer".format(count_field))
    if document["buy_count"] + document["sell_count"] + document["hold_count"] + document["wait_count"] + document["blocked_count"] != document["proposal_count"]:
        _fail("outcome counts must sum to proposal_count")
    if document["completed_trade_count"] > document["proposal_count"]:
        _fail("completed_trade_count cannot exceed proposal_count")
    expected_status = (
        SAMPLE_SUFFICIENT
        if document["completed_trade_count"] >= document["minimum_completed_trades"]
        else SAMPLE_INSUFFICIENT
    )
    if document["sample_status"] != expected_status:
        _fail("sample_status does not match the governed minimum-sample rule")
    if document["confidence_calibration_status"] not in signal_confidence.CONFIDENCE_STATUSES:
        _fail("confidence_calibration_status is not governed")
    if document["broker_execution_statement"] != NO_BROKER_EXECUTION_STATEMENT:
        _fail("broker_execution_statement must be the exact governed statement")
    if document["guaranteed_performance_statement"] != NO_GUARANTEED_PERFORMANCE_STATEMENT:
        _fail("guaranteed_performance_statement must be the exact governed statement")
    segments = document["walk_forward_segments"]
    if not isinstance(segments, list) or len(segments) > MAX_SEGMENTS:
        _fail("walk_forward_segments must be a bounded list")
    if document["sample_label"] != "WALK_FORWARD" and segments:
        _fail("walk_forward_segments must be empty unless sample_label is WALK_FORWARD")
    for segment in segments:
        if not isinstance(segment, dict) or set(segment) != set(SEGMENT_FIELDS):
            _fail("walk-forward segment has an invalid field set")
    dataset_ids = document["dataset_proposal_ids"]
    if not isinstance(dataset_ids, list) or dataset_ids != sorted(dataset_ids) or len(dataset_ids) != len(set(dataset_ids)):
        _fail("dataset_proposal_ids must be a sorted, duplicate-free list")
    if document["dataset_hash"] != sha256_text(deterministic_json_text(dataset_ids)):
        _fail("dataset_hash does not match dataset_proposal_ids")
    material = {key: value for key, value in document.items() if key not in ("report_id", "canonical_report_hash")}
    expected_id, expected_digest = _report_id_for(material)
    if document["report_id"] != expected_id:
        _fail("report_id does not match canonical content")
    if document["canonical_report_hash"] != expected_digest:
        _fail("canonical_report_hash does not match canonical content")
    return deepcopy(document)


def report_markdown(document):
    """Render the exact same validated document as Markdown; introduces no
    fact not already present in the JSON document."""
    clean = validate_report(document)
    lines = [
        "# TRL Signal Intelligence Performance Report",
        "",
        "> RESEARCH REPORTING ONLY — {} — {}".format(
            clean["broker_execution_statement"], clean["guaranteed_performance_statement"],
        ),
        "",
        "| Field | Value |",
        "|---|---|",
        "| Report ID | `{}` |".format(clean["report_id"]),
        "| Strategy | {} v{} |".format(clean["strategy_id"], clean["strategy_version"]),
        "| Sample label | {} |".format(clean["sample_label"]),
        "| Sample window | {} to {} |".format(clean["sample_start_at_utc"], clean["sample_end_at_utc"]),
        "| Sample status | {} (minimum {} completed trades) |".format(
            clean["sample_status"], clean["minimum_completed_trades"],
        ),
        "| Confidence calibration status | {} |".format(clean["confidence_calibration_status"]),
        "",
        "## Outcome counts",
        "",
        "| Outcome | Count |",
        "|---|---:|",
        "| Proposals | {} |".format(clean["proposal_count"]),
        "| BUY | {} |".format(clean["buy_count"]),
        "| SELL | {} |".format(clean["sell_count"]),
        "| HOLD | {} |".format(clean["hold_count"]),
        "| WAIT | {} |".format(clean["wait_count"]),
        "| BLOCKED | {} |".format(clean["blocked_count"]),
        "| Completed trades | {} |".format(clean["completed_trade_count"]),
        "| Open positions | {} |".format(clean["open_position_count"]),
        "| Incomplete trades | {} |".format(clean["incomplete_trade_count"]),
        "",
        "## Assumptions",
        "",
        "- Fees: {}".format(clean["fee_assumption"]),
        "- Slippage: {}".format(clean["slippage_assumption"]),
        "- Spread: {}".format(clean["spread_assumption"]),
    ]
    lines.extend("- {}".format(item) for item in clean["assumptions"])
    lines.append("")
    lines.append("## Limitations")
    lines.append("")
    lines.extend("- {}".format(item) for item in clean["limitations"])
    if clean["walk_forward_segments"]:
        lines.append("")
        lines.append("## Walk-forward segments")
        lines.append("")
        lines.append("| Segment | Window | Proposals | BUY | SELL | HOLD | WAIT | BLOCKED | Completed |")
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|")
        for segment in clean["walk_forward_segments"]:
            lines.append(
                "| {} | {} to {} | {} | {} | {} | {} | {} | {} | {} |".format(
                    segment["segment_id"], segment["start_at_utc"], segment["end_at_utc"],
                    segment["proposal_count"], segment["buy_count"], segment["sell_count"],
                    segment["hold_count"], segment["wait_count"], segment["blocked_count"],
                    segment["completed_trade_count"],
                )
            )
    lines.append("")
    return "\n".join(lines) + "\n"


__all__ = (
    "MINIMUM_COMPLETED_TRADES",
    "NO_BROKER_EXECUTION_STATEMENT",
    "NO_GUARANTEED_PERFORMANCE_STATEMENT",
    "REPORT_FIELDS",
    "REPORT_SCHEMA",
    "SAMPLE_INSUFFICIENT",
    "SAMPLE_SUFFICIENT",
    "SEGMENT_FIELDS",
    "ReportValidationError",
    "build_report",
    "report_markdown",
    "validate_report",
)
