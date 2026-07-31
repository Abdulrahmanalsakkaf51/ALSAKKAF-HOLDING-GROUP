"""Role 2 — Market Regime Partner (TRL-R2-006 Section 2).

Classifies TREND_UP / TREND_DOWN / RANGE / HIGH_VOLATILITY / UNKNOWN from
the governed bar series only (no strategy-specific parameters, no news, no
account state). A pure function, deterministic for a given bar series.
UNKNOWN is a legitimate classification (features exist but show no clear
regime); REGIME_UNCLASSIFIABLE is the distinct role-level failure emitted
only when there is not even enough governed history to compute a
classification at all.
"""

from decimal import Decimal

from .timeline_data import decimal_value


ROLE_NAME = "market_regime"
PASS = "PASS"
REGIME_UNCLASSIFIABLE = "REGIME_UNCLASSIFIABLE"

MINIMUM_BARS_FOR_CLASSIFICATION = 5
_LOOKBACK = 20
_TREND_THRESHOLD_PERCENT = Decimal("1.0")
_HIGH_VOLATILITY_THRESHOLD_PERCENT = Decimal("2.5")

REASON_INSUFFICIENT_BAR_HISTORY = "INSUFFICIENT_BAR_HISTORY_FOR_REGIME"


def evaluate(request):
    bars = request["bar_series"]
    if len(bars) < MINIMUM_BARS_FOR_CLASSIFICATION:
        return {
            "status": REGIME_UNCLASSIFIABLE,
            "reasons": [REASON_INSUFFICIENT_BAR_HISTORY],
            "classification": "UNKNOWN",
        }
    window = bars[-_LOOKBACK:]
    closes = [decimal_value(bar["close"]) for bar in window]
    first_close = closes[0]
    last_close = closes[-1]
    if first_close == 0:
        return {
            "status": REGIME_UNCLASSIFIABLE,
            "reasons": [REASON_INSUFFICIENT_BAR_HISTORY],
            "classification": "UNKNOWN",
        }
    average = sum(closes) / len(closes)
    mean_abs_deviation_pct = (
        sum(abs(close - average) for close in closes) / len(closes) / average * 100
    )
    change_pct = (last_close - first_close) / first_close * 100

    if mean_abs_deviation_pct > _HIGH_VOLATILITY_THRESHOLD_PERCENT:
        classification = "HIGH_VOLATILITY"
    elif change_pct >= _TREND_THRESHOLD_PERCENT:
        classification = "TREND_UP"
    elif change_pct <= -_TREND_THRESHOLD_PERCENT:
        classification = "TREND_DOWN"
    else:
        classification = "RANGE"

    return {
        "status": PASS,
        "reasons": [],
        "classification": classification,
    }


__all__ = (
    "MINIMUM_BARS_FOR_CLASSIFICATION",
    "PASS",
    "REGIME_UNCLASSIFIABLE",
    "ROLE_NAME",
    "evaluate",
)
