"""Shared, non-test-discovered fixture builders for the TRL-R2-010 Market
Intelligence V0 (TRL CORTEX V0) test suite. Deliberately not named
``test_*.py`` so ``unittest discover -p "test_*.py"`` never imports it as
its own (empty) test module.
"""

import copy
import json
import os
import tempfile

FAR_FUTURE = "2035-01-01T00:00:00.000000Z"
PAST_OBSERVED = "2026-08-01T10:00:00.000000Z"


def evidence_input(category, direction, strength, confidence, expires=FAR_FUTURE, observed=PAST_OBSERVED):
    return {
        "category": category, "evidence_direction": direction,
        "normalized_strength": strength, "confidence": confidence,
        "source_classification": "SYNTHETIC_FIXTURE", "source_reference": "fixture:{}".format(category.lower()),
        "observed_at_utc": observed, "expires_at_utc": expires,
        "explanation": "synthetic evidence for {} category".format(category),
    }


def strong_evidence_inputs():
    """Eleven evidence items deterministically producing TRADE_CANDIDATE
    with a BUY-side CORTEX-V0-HEURISTIC opportunity (matching the
    committed synthetic fixture's shape)."""
    return [
        evidence_input("MARKET_STRUCTURE", "SUPPORTS", "0.9000", "0.9500"),
        evidence_input("TREND", "SUPPORTS", "0.9000", "0.9500"),
        evidence_input("MOMENTUM", "SUPPORTS", "0.9000", "0.9500"),
        evidence_input("VOLATILITY", "NEUTRAL", "0.5000", "0.9000"),
        evidence_input("LIQUIDITY_AND_SPREAD", "NEUTRAL", "0.6000", "0.9000"),
        evidence_input("MULTI_TIMEFRAME_ALIGNMENT", "SUPPORTS", "0.9000", "0.9500"),
        evidence_input("EVENT_RISK", "NEUTRAL", "0.1000", "0.9500"),
        evidence_input("EXECUTION_COST", "NEUTRAL", "0.1500", "0.9000"),
        evidence_input("RISK_EXPOSURE", "NEUTRAL", "0.1000", "0.9000"),
        evidence_input("CONTRADICTING_EVIDENCE", "NEUTRAL", "0.1000", "0.9000"),
        evidence_input("DATA_QUALITY", "NEUTRAL", "0.9500", "0.9500"),
    ]


def snapshot_input(**overrides):
    base = {
        "instrument": "XAUUSD", "timeframe": "H1", "observed_at_utc": PAST_OBSERVED,
        "open": "2400.00", "high": "2410.00", "low": "2395.00", "close": "2405.00",
        "spread": "0.30", "volatility_measure": "5.20", "volatility_method": "ATR14",
        "session": "LONDON", "data_source_classification": "COMMITTED_FIXTURE",
        "data_quality_status": "SUFFICIENT", "event_risk_classification": "LOW",
    }
    base.update(overrides)
    return base


def candidate_input(**overrides):
    base = {
        "entry_trigger": "2401.00", "stop_price": "2396.00",
        "target_prices": ["2410.00", "2415.00", "2420.00"],
        "target_allocations": ["40.0000", "30.0000", "30.0000"],
        "hypothetical_total_quantity": "1.00000000",
        "activation_satisfied": True, "invalidation_satisfied": False,
        "expires_at_utc": FAR_FUTURE,
    }
    base.update(overrides)
    return base


def analysis_envelope(**overrides):
    base = {
        "schema_version": "TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1",
        "snapshot": snapshot_input(),
        "proposed_side": "BUY",
        "strategy_id": "CORTEX-V0-HEURISTIC", "strategy_version": "1.0.0",
        "market_regime": "TRENDING",
        "entry_concept": "buy dip", "invalidation_concept": "break structure",
        "stop_concept": "below swing low",
        "ordered_target_concepts": ["t1", "t2", "t3"],
        "evidence_inputs": strong_evidence_inputs(),
        "virtual_candidate_inputs": [candidate_input()],
        "activation_satisfied": True, "invalidation_satisfied": False,
    }
    base.update(overrides)
    return base


def write_temp_json(document, directory=None):
    fd, path = tempfile.mkstemp(suffix=".json", dir=directory)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump(document, handle)
    return path


def deep_copy(document):
    return copy.deepcopy(document)
