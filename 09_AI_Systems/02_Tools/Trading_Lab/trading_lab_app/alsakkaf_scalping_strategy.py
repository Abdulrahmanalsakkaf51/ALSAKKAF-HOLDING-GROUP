"""ALSAKKAF SCALPING scoring, direction, and the R2-010 evidence bridge
(TRL-R2-012 contract Section 8).

**Accelerated-V0 engineering decision (contract Section 8.2/20):** the
mega-prompt fixes the six category *point caps* (trend 25, momentum 20,
market_structure 20, volatility_suitability 15, spread_and_cost 10,
multi_timeframe_alignment 10) but not their internal sub-formulas. This
module implements one deterministic, documented sub-formula per category
below; a later contract may refine them without changing the 100-point
shape. A second accelerated-V0 decision: R2-010's snapshot timeframe
allowlist is ``M5, M15, H1, H4, D1`` (no ``M1``), so the R2-010 bridge
snapshot always uses the *confirmation* timeframe (``M5`` for Precision
Scalping/Breakout Ladder, ``H1`` for Intraday), never the M1/M15 entry
timeframe -- the entry-timeframe indicators still drive the scoring
above, only the R2-010 transport envelope's `timeframe` field differs.

Only an R2-010 ``TRADE_CANDIDATE`` result may proceed to a demo order plan
(contract Section 8.3) -- this module never weakens that gate.
"""

import os
import tempfile
from datetime import datetime, timezone
from decimal import Decimal

from . import alsakkaf_scalping_indicators as indicators
from .alsakkaf_scalping_data import ScalpingDataValidationError
from .timeline_data import format_utc

CATEGORY_CAPS = {
    "trend": 25,
    "momentum": 20,
    "market_structure": 20,
    "volatility_suitability": 15,
    "spread_and_cost": 10,
    "multi_timeframe_alignment": 10,
}
TOTAL_SCORE_CAP = sum(CATEGORY_CAPS.values())

TRADE_CANDIDATE_MIN = 75
WAIT_MIN = 60

CONFIRMATION_TIMEFRAME_FOR_PROFILE = {
    "ALSAKKAF_PRECISION_SCALPING": "M5",
    "ALSAKKAF_BREAKOUT_LADDER": "M5",
    "ALSAKKAF_INTRADAY": "H1",
}

# TRL-R2-013 Section 5: the entry timeframe each profile analyzes on --
# needed by the new server-authoritative bar fetch, which R2-012 never
# implemented (bars were always supplied by the caller).
ENTRY_TIMEFRAME_FOR_PROFILE = {
    "ALSAKKAF_PRECISION_SCALPING": "M1",
    "ALSAKKAF_BREAKOUT_LADDER": "M1",
    "ALSAKKAF_INTRADAY": "M15",
}

# Minimum closed bars needed to compute every Section 8.1 indicator without
# an artificial shortfall (EMA50 is the tallest requirement); the
# confirmation timeframe only needs enough for multi_timeframe_direction's
# 21-period EMA.
MIN_ENTRY_BARS = 60
MIN_CONFIRMATION_BARS = 30


class ScalpingStrategyError(ScalpingDataValidationError):
    """Raised when a setup cannot be evaluated safely."""


def _decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def determine_direction(ema9, ema21, macd_histogram):
    ema9, ema21, macd_histogram = _decimal(ema9), _decimal(ema21), _decimal(macd_histogram)
    if ema9 > ema21 and macd_histogram > 0:
        return "BUY"
    if ema9 < ema21 and macd_histogram < 0:
        return "SELL"
    return "NONE"


def score_categories(bundle, direction):
    """``bundle`` carries every already-computed Section 8.1 indicator
    value; see ``build_evidence_bundle`` below for its exact shape."""
    if direction == "NONE":
        return {key: 0 for key in CATEGORY_CAPS}, 0

    ema9, ema21, ema50 = bundle["ema9"], bundle["ema21"], bundle["ema50"]
    adx_value = bundle["adx"]
    rsi_value = bundle["rsi"]
    macd_histogram = bundle["macd_histogram"]
    body_ratio = bundle["body_ratio"]
    nearest_support = bundle["nearest_support"]
    nearest_resistance = bundle["nearest_resistance"]
    current_price = bundle["current_price"]
    spread_to_atr = bundle["spread_to_atr"]
    mtf_direction = bundle["mtf_direction"]

    trend = 0
    aligned = (ema9 > ema21 > ema50) if direction == "BUY" else (ema9 < ema21 < ema50)
    if aligned:
        trend += 15
    if adx_value >= 25:
        trend += 10
    elif adx_value >= 20:
        trend += 6
    elif adx_value >= 15:
        trend += 3

    momentum = 0
    if direction == "BUY":
        if Decimal("50") < rsi_value <= Decimal("70"):
            momentum += 10
        elif Decimal("40") < rsi_value <= Decimal("50"):
            momentum += 5
    else:
        if Decimal("30") <= rsi_value < Decimal("50"):
            momentum += 10
        elif Decimal("50") <= rsi_value < Decimal("60"):
            momentum += 5
    if (direction == "BUY" and macd_histogram > 0) or (direction == "SELL" and macd_histogram < 0):
        momentum += 10

    market_structure = 0
    if direction == "BUY" and nearest_support is not None and current_price > nearest_support:
        market_structure += 10
    if direction == "SELL" and nearest_resistance is not None and current_price < nearest_resistance:
        market_structure += 10
    if body_ratio > Decimal("0.5"):
        market_structure += 10

    if spread_to_atr <= Decimal("0.15"):
        volatility_suitability = 15
    elif spread_to_atr <= Decimal("0.30"):
        volatility_suitability = 8
    else:
        volatility_suitability = 0

    if spread_to_atr <= Decimal("0.10"):
        spread_and_cost = 10
    elif spread_to_atr <= Decimal("0.25"):
        spread_and_cost = 5
    else:
        spread_and_cost = 0

    if mtf_direction == ("UP" if direction == "BUY" else "DOWN"):
        multi_timeframe_alignment = 10
    elif mtf_direction == "FLAT":
        multi_timeframe_alignment = 5
    else:
        multi_timeframe_alignment = 0

    scores = {
        "trend": min(trend, CATEGORY_CAPS["trend"]),
        "momentum": min(momentum, CATEGORY_CAPS["momentum"]),
        "market_structure": min(market_structure, CATEGORY_CAPS["market_structure"]),
        "volatility_suitability": volatility_suitability,
        "spread_and_cost": spread_and_cost,
        "multi_timeframe_alignment": multi_timeframe_alignment,
    }
    return scores, sum(scores.values())


def classify_score(total_score, direction):
    if direction == "NONE":
        return "WAIT"
    if total_score >= TRADE_CANDIDATE_MIN:
        return "TRADE_CANDIDATE"
    if total_score >= WAIT_MIN:
        return "WAIT"
    return "REJECT"


def build_evidence_bundle(entry_bars, confirmation_bars, current_price, spread):
    """Compute every Section 8.1 indicator from closed bars only. Raises
    ``ScalpingStrategyError`` (via the indicator module) if insufficient
    bar history is supplied -- never silently substitutes a default."""
    current_price = _decimal(current_price)
    spread = _decimal(spread)
    ema9 = _decimal(indicators.ema(entry_bars, 9))
    ema21 = _decimal(indicators.ema(entry_bars, 21))
    ema50 = _decimal(indicators.ema(entry_bars, 50))
    rsi_value = _decimal(indicators.rsi(entry_bars, 14))
    atr_value = _decimal(indicators.atr(entry_bars, 14))
    adx_value = _decimal(indicators.adx(entry_bars, 14))
    macd_result = indicators.macd(entry_bars)
    macd_histogram = _decimal(macd_result["histogram"])
    candle_stats = indicators.candle_statistics(entry_bars[-1])
    support_resistance = indicators.nearest_support_resistance(entry_bars, current_price)
    spread_to_atr = _decimal(indicators.spread_to_atr_ratio(spread, atr_value))
    mtf_direction = indicators.multi_timeframe_direction(confirmation_bars, period=21)
    return {
        "ema9": ema9, "ema21": ema21, "ema50": ema50, "rsi": rsi_value,
        "atr": atr_value, "adx": adx_value, "macd_histogram": macd_histogram,
        "body_ratio": _decimal(candle_stats["body_ratio"]),
        "nearest_support": support_resistance["nearest_support"],
        "nearest_resistance": support_resistance["nearest_resistance"],
        "current_price": current_price, "spread": spread,
        "spread_to_atr": spread_to_atr, "mtf_direction": mtf_direction,
    }


def evaluate_setup(entry_bars, confirmation_bars, current_price, spread):
    bundle = build_evidence_bundle(entry_bars, confirmation_bars, current_price, spread)
    direction = determine_direction(bundle["ema9"], bundle["ema21"], bundle["macd_histogram"])
    scores, total_score = score_categories(bundle, direction)
    classification = classify_score(total_score, direction)
    return {
        "direction": direction, "scores": scores, "total_score": total_score,
        "classification": classification, "bundle": bundle,
    }


# --------------------------------------------------------------------------
# R2-010 evidence bridge (contract Section 8.3)
# --------------------------------------------------------------------------

def _session_for_utc_hour(hour):
    if 0 <= hour < 7:
        return "OFF_HOURS"
    if 7 <= hour < 8:
        return "LONDON"
    if 8 <= hour < 12:
        return "LONDON"
    if 12 <= hour < 16:
        return "OVERLAP"
    if 16 <= hour < 21:
        return "NEW_YORK"
    return "OFF_HOURS"


def _score4(value):
    return format(_decimal(value).quantize(Decimal("0.0001")), "f")


def build_analysis_input(
    canonical_instrument, profile_id, evaluation, entry_bars, observed_at_utc,
    proposed_side, stop_price, ordered_target_prices, ordered_target_allocations_pct,
    expires_at_utc, event_risk_blocked, data_quality_status="SUFFICIENT",
    risk_exposure_severity="0.0000",
):
    bundle = evaluation["bundle"]
    scores = evaluation["scores"]
    timeframe = CONFIRMATION_TIMEFRAME_FOR_PROFILE[profile_id]
    last_bar = entry_bars[-1]
    hour = datetime.strptime(observed_at_utc, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc).hour

    snapshot = {
        "instrument": canonical_instrument, "timeframe": timeframe,
        "observed_at_utc": observed_at_utc,
        "open": str(last_bar["open"]), "high": str(last_bar["high"]),
        "low": str(last_bar["low"]), "close": str(last_bar["close"]),
        "spread": str(bundle["spread"]), "volatility_measure": str(bundle["atr"]),
        "volatility_method": "ATR14", "session": _session_for_utc_hour(hour),
        "data_source_classification": "LOCAL_USER_SUPPLIED",
        "data_quality_status": data_quality_status,
        "event_risk_classification": "HIGH" if event_risk_blocked else "NONE",
    }

    data_quality_strength = {"SUFFICIENT": "0.9000", "DEGRADED": "0.5000", "INSUFFICIENT": "0.1000"}[data_quality_status]
    contradicting = bundle["mtf_direction"] not in ("FLAT", "UP" if proposed_side == "BUY" else "DOWN")

    def item(category, direction, strength, confidence=Decimal("1.0000")):
        # Full confidence by default: every category below is an exact,
        # deterministic calculation over already-validated closed bars
        # (contract Section 8.1), not a subjective judgment -- the *degree*
        # of technical support is carried entirely by normalized_strength,
        # never diluted by an artificial confidence discount.
        return {
            "category": category, "evidence_direction": direction,
            "normalized_strength": strength, "confidence": _score4(confidence),
            "source_classification": "LOCAL_USER_INPUT",
            "source_reference": "alsakkaf_scalping:{}".format(category.lower()),
            "observed_at_utc": observed_at_utc, "expires_at_utc": expires_at_utc,
            "explanation": "ALSAKKAF SCALPING deterministic technical evidence for {}.".format(category),
        }

    evidence_inputs = [
        item("MARKET_STRUCTURE",
             "SUPPORTS" if scores["market_structure"] >= 10 else "NEUTRAL",
             _score4(Decimal(scores["market_structure"]) / Decimal(CATEGORY_CAPS["market_structure"]))),
        item("TREND",
             "SUPPORTS" if scores["trend"] >= 15 else "NEUTRAL",
             _score4(Decimal(scores["trend"]) / Decimal(CATEGORY_CAPS["trend"]))),
        item("MOMENTUM",
             "SUPPORTS" if scores["momentum"] >= 10 else "NEUTRAL",
             _score4(Decimal(scores["momentum"]) / Decimal(CATEGORY_CAPS["momentum"]))),
        item("VOLATILITY", "NEUTRAL",
             _score4(Decimal(scores["volatility_suitability"]) / Decimal(CATEGORY_CAPS["volatility_suitability"]))),
        item("LIQUIDITY_AND_SPREAD", "NEUTRAL",
             _score4(Decimal(scores["spread_and_cost"]) / Decimal(CATEGORY_CAPS["spread_and_cost"]))),
        item("MULTI_TIMEFRAME_ALIGNMENT",
             "SUPPORTS" if scores["multi_timeframe_alignment"] >= 10 else "NEUTRAL",
             _score4(Decimal(scores["multi_timeframe_alignment"]) / Decimal(CATEGORY_CAPS["multi_timeframe_alignment"]))),
        item("EVENT_RISK", "NEUTRAL", "1.0000" if event_risk_blocked else "0.0000"),
        item("EXECUTION_COST", "NEUTRAL", _score4(min(bundle["spread_to_atr"], Decimal("1")))),
        item("RISK_EXPOSURE", "NEUTRAL", _score4(risk_exposure_severity)),
        item("CONTRADICTING_EVIDENCE", "OPPOSES" if contradicting else "NEUTRAL",
             "0.5000" if contradicting else "0.0000"),
        item("DATA_QUALITY", "NEUTRAL", data_quality_strength),
    ]

    candidate_input = {
        "entry_trigger": str(bundle["current_price"]),
        "stop_price": str(stop_price),
        "target_prices": [str(price) for price in ordered_target_prices],
        "target_allocations": [str(pct) for pct in ordered_target_allocations_pct],
        "hypothetical_total_quantity": None,
        "activation_satisfied": True,
        "invalidation_satisfied": False,
        "expires_at_utc": expires_at_utc,
    }

    return {
        "schema_version": "TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1",
        "snapshot": snapshot,
        "proposed_side": proposed_side,
        "strategy_id": "CORTEX-V0-HEURISTIC",
        "strategy_version": "1.0.0",
        "market_regime": "TRENDING" if bundle["adx"] >= 25 else "RANGING",
        "entry_concept": "ALSAKKAF SCALPING {} setup on {}.".format(profile_id, canonical_instrument),
        "invalidation_concept": "Stop-loss geometry breached or opposite-direction confirmation.",
        "stop_concept": "ATR/broker-floor stop distance per the R2-012 contract.",
        "ordered_target_concepts": [
            "Target {} at fixed R-multiple.".format(index + 1) for index in range(len(ordered_target_prices))
        ][:4] if len(ordered_target_prices) >= 2 else [
            "Target 1 at fixed R-multiple.", "Target 2 (mirrored for R2-010 2-4 target requirement)."
        ],
        "evidence_inputs": evidence_inputs,
        "virtual_candidate_inputs": [candidate_input],
        "activation_satisfied": True,
        "invalidation_satisfied": False,
    }


def run_r2010_bridge(market_intelligence_service, analysis_input, scratch_directory):
    """Write the bounded envelope to a same-directory local temp file
    (never persisted, never a network/UNC/symlink path) and call R2-010's
    own unmodified ``analyze_market_snapshot`` -- the sole caller-facing
    entry point this module ever uses. Only ``final_status ==
    'TRADE_CANDIDATE'`` may proceed to a demo order plan (contract
    Section 8.3); this function returns R2-010's decision verbatim and
    performs no independent classification of its own."""
    import json

    os.makedirs(scratch_directory, exist_ok=True)
    handle_fd, temp_path = tempfile.mkstemp(
        prefix="alsakkaf-scalping-mi-input-", suffix=".json", dir=scratch_directory,
    )
    try:
        with os.fdopen(handle_fd, "w", encoding="utf-8") as handle:
            json.dump(analysis_input, handle, ensure_ascii=False, sort_keys=True)
        return market_intelligence_service.analyze_market_snapshot(temp_path)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass


__all__ = (
    "CATEGORY_CAPS",
    "CONFIRMATION_TIMEFRAME_FOR_PROFILE",
    "ENTRY_TIMEFRAME_FOR_PROFILE",
    "MIN_CONFIRMATION_BARS",
    "MIN_ENTRY_BARS",
    "ScalpingStrategyError",
    "TOTAL_SCORE_CAP",
    "TRADE_CANDIDATE_MIN",
    "WAIT_MIN",
    "build_analysis_input",
    "build_evidence_bundle",
    "classify_score",
    "determine_direction",
    "evaluate_setup",
    "run_r2010_bridge",
    "score_categories",
)
