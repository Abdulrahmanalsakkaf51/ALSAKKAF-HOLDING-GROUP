"""Deterministic, non-promissory confidence scoring (TRL-R2-006).

Confidence is a descriptive research score, never a profit promise or a
win-probability estimate, and it never influences position size (risk
sizing is Role 3/Role 5's job, entirely separate from this module).

**Correction (2026-08-01):** the first Phase 4 implementation returned a
plain 0-100 integer next to a calibration-source *string* that merely
contained the word "uncalibrated" — a numeric value sitting next to prose
still reads as a calibrated score to any caller that doesn't parse the
string. This module now also returns an explicit, machine-readable
``confidence_status`` (a closed-vocabulary field on the proposal schema,
see ``signal_data.py``) so no caller — dashboard, CLI, JSON consumer, or
future report — can present this number as calibrated without deliberately
overriding the status field. `CONFIDENCE_STATUSES` currently has exactly
one value, ``UNCALIBRATED_HEURISTIC``, because no realized-outcome
calibration study exists yet; a future checkpoint that completes one adds
a second value (e.g. ``CALIBRATED``) rather than silently repurposing this
one.
"""

CONFIDENCE_STATUSES = ("UNCALIBRATED_HEURISTIC",)

CONFIDENCE_DISCLAIMER = (
    "This confidence score is an uncalibrated heuristic research value "
    "only. It is not a win probability, not a profit forecast, and has no "
    "effect on position size or risk."
)

CALIBRATION_SOURCES = {
    "PHASE4_COMPONENT_SCORE_UNCALIBRATED_V1": {
        "description": (
            "Deterministic component score (regime alignment, evidence "
            "quality, sample size) with no realized-outcome calibration "
            "performed yet. Not validated against live or paper trade "
            "outcomes. Bounded 0-100. Always reported with "
            "confidence_status == UNCALIBRATED_HEURISTIC."
        ),
        "validated_against_realized_outcomes": False,
        "confidence_status": "UNCALIBRATED_HEURISTIC",
    },
}

DEFAULT_CALIBRATION_SOURCE = "PHASE4_COMPONENT_SCORE_UNCALIBRATED_V1"
MINIMUM_ROBUST_SAMPLE_BARS = 50


def resolve_calibration_source(name):
    return name in CALIBRATION_SOURCES


def confidence_status_for(calibration_source):
    """Return the governed confidence_status for a resolved calibration
    source, or None if the source does not resolve (fail-closed signal)."""
    record = CALIBRATION_SOURCES.get(calibration_source)
    return record["confidence_status"] if record else None


def compute_confidence(candidate_side, regime_classification, bar_count):
    """Return (score, calibration_source, confidence_status, breakdown).
    score is an int 0-100. Never implies certainty, a win probability, or
    a guaranteed outcome, and confidence_status is always
    UNCALIBRATED_HEURISTIC in this checkpoint."""
    breakdown = {"base": 50}
    score = 50
    if candidate_side in ("BUY", "SELL"):
        aligned = (
            (candidate_side == "BUY" and regime_classification == "TREND_UP")
            or (candidate_side == "SELL" and regime_classification == "TREND_DOWN")
        )
        opposed = (
            (candidate_side == "BUY" and regime_classification == "TREND_DOWN")
            or (candidate_side == "SELL" and regime_classification == "TREND_UP")
        )
        if aligned:
            score += 15
            breakdown["regime_alignment"] = 15
        elif opposed:
            score -= 10
            breakdown["regime_alignment"] = -10
        else:
            breakdown["regime_alignment"] = 0
    else:
        breakdown["regime_alignment"] = 0
    if bar_count < MINIMUM_ROBUST_SAMPLE_BARS:
        score -= 15
        breakdown["sample_size_penalty"] = -15
    else:
        breakdown["sample_size_penalty"] = 0
    score = max(0, min(100, score))
    breakdown["final_score"] = score
    calibration_source = DEFAULT_CALIBRATION_SOURCE
    status = confidence_status_for(calibration_source)
    return score, calibration_source, status, breakdown


__all__ = (
    "CALIBRATION_SOURCES",
    "CONFIDENCE_DISCLAIMER",
    "CONFIDENCE_STATUSES",
    "DEFAULT_CALIBRATION_SOURCE",
    "MINIMUM_ROBUST_SAMPLE_BARS",
    "compute_confidence",
    "confidence_status_for",
    "resolve_calibration_source",
)
