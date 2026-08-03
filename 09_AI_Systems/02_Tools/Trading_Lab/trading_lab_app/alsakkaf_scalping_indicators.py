"""Deterministic Decimal-only technical indicators for ALSAKKAF SCALPING
(TRL-R2-012 contract Section 8.1).

Every function consumes **closed bars only** -- the current, unfinished
bar is never accepted here; callers pass it separately only for spread/
execution-price checks (never for a directional indicator value). All
arithmetic uses ``Decimal``; no binary float ever participates in a
canonical indicator value.
"""

from decimal import Decimal

from .alsakkaf_scalping_data import ScalpingDataValidationError, quantize_4


class IndicatorInputError(ScalpingDataValidationError):
    """Raised when insufficient or malformed closed-bar data is supplied."""


def _decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _closes(bars):
    return [_decimal(bar["close"]) for bar in bars]


def _require_min_bars(bars, minimum, label):
    if not isinstance(bars, (list, tuple)) or len(bars) < minimum:
        raise IndicatorInputError("{} requires at least {} closed bars".format(label, minimum))


def ema_series(values, period):
    if period < 1:
        raise IndicatorInputError("ema period must be >= 1")
    if len(values) < period:
        raise IndicatorInputError("ema requires at least `period` values")
    multiplier = Decimal(2) / Decimal(period + 1)
    seed = sum(values[:period]) / Decimal(period)
    series = [seed]
    for value in values[period:]:
        previous = series[-1]
        series.append((value - previous) * multiplier + previous)
    return series


def ema(bars, period):
    _require_min_bars(bars, period, "EMA")
    series = ema_series(_closes(bars), period)
    return quantize_4(series[-1])


def rsi(bars, period=14):
    _require_min_bars(bars, period + 1, "RSI")
    closes = _closes(bars)
    gains = []
    losses = []
    for index in range(1, len(closes)):
        delta = closes[index] - closes[index - 1]
        gains.append(delta if delta > 0 else Decimal(0))
        losses.append(-delta if delta < 0 else Decimal(0))
    average_gain = sum(gains[:period]) / Decimal(period)
    average_loss = sum(losses[:period]) / Decimal(period)
    for index in range(period, len(gains)):
        average_gain = (average_gain * Decimal(period - 1) + gains[index]) / Decimal(period)
        average_loss = (average_loss * Decimal(period - 1) + losses[index]) / Decimal(period)
    if average_loss == 0:
        return quantize_4(Decimal(100))
    relative_strength = average_gain / average_loss
    value = Decimal(100) - (Decimal(100) / (Decimal(1) + relative_strength))
    return quantize_4(value)


def _true_ranges(bars):
    true_ranges = []
    previous_close = None
    for bar in bars:
        high, low, close = _decimal(bar["high"]), _decimal(bar["low"]), _decimal(bar["close"])
        if previous_close is None:
            true_ranges.append(high - low)
        else:
            true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
        previous_close = close
    return true_ranges


def atr(bars, period=14):
    _require_min_bars(bars, period + 1, "ATR")
    true_ranges = _true_ranges(bars)
    average = sum(true_ranges[1:period + 1]) / Decimal(period)
    for value in true_ranges[period + 1:]:
        average = (average * Decimal(period - 1) + value) / Decimal(period)
    return quantize_4(average)


def adx(bars, period=14):
    _require_min_bars(bars, (period * 2) + 1, "ADX")
    plus_dm = []
    minus_dm = []
    true_ranges = []
    for index in range(1, len(bars)):
        up_move = _decimal(bars[index]["high"]) - _decimal(bars[index - 1]["high"])
        down_move = _decimal(bars[index - 1]["low"]) - _decimal(bars[index]["low"])
        plus_dm.append(up_move if (up_move > down_move and up_move > 0) else Decimal(0))
        minus_dm.append(down_move if (down_move > up_move and down_move > 0) else Decimal(0))
        high, low = _decimal(bars[index]["high"]), _decimal(bars[index]["low"])
        previous_close = _decimal(bars[index - 1]["close"])
        true_ranges.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))

    def wilder_smooth(values):
        smoothed = [sum(values[:period])]
        for value in values[period:]:
            smoothed.append(smoothed[-1] - (smoothed[-1] / Decimal(period)) + value)
        return smoothed

    smoothed_tr = wilder_smooth(true_ranges)
    smoothed_plus = wilder_smooth(plus_dm)
    smoothed_minus = wilder_smooth(minus_dm)

    dx_values = []
    for tr_value, plus_value, minus_value in zip(smoothed_tr, smoothed_plus, smoothed_minus):
        if tr_value == 0:
            dx_values.append(Decimal(0))
            continue
        plus_di = (plus_value / tr_value) * Decimal(100)
        minus_di = (minus_value / tr_value) * Decimal(100)
        denominator = plus_di + minus_di
        if denominator == 0:
            dx_values.append(Decimal(0))
        else:
            dx_values.append((abs(plus_di - minus_di) / denominator) * Decimal(100))

    if len(dx_values) < period:
        raise IndicatorInputError("ADX requires at least {} smoothed values".format(period))
    adx_value = sum(dx_values[:period]) / Decimal(period)
    for value in dx_values[period:]:
        adx_value = (adx_value * Decimal(period - 1) + value) / Decimal(period)
    return quantize_4(adx_value)


def macd(bars, fast=12, slow=26, signal=9):
    _require_min_bars(bars, slow + signal, "MACD")
    closes = _closes(bars)
    fast_series = ema_series(closes, fast)
    slow_series = ema_series(closes, slow)
    offset = slow - fast
    macd_line_series = [
        fast_series[offset + index] - slow_series[index]
        for index in range(len(slow_series))
    ]
    signal_series = ema_series(macd_line_series, signal)
    macd_line = macd_line_series[-1]
    signal_line = signal_series[-1]
    histogram = macd_line - signal_line
    return {
        "macd_line": quantize_4(macd_line),
        "signal_line": quantize_4(signal_line),
        "histogram": quantize_4(histogram),
    }


def swing_points(bars, arm=2):
    """5-bar fractal swing highs/lows (2 bars each side by default)."""
    _require_min_bars(bars, (arm * 2) + 1, "swing points")
    highs, lows = [], []
    for index in range(arm, len(bars) - arm):
        window = bars[index - arm:index + arm + 1]
        pivot_high = _decimal(bars[index]["high"])
        pivot_low = _decimal(bars[index]["low"])
        if pivot_high == max(_decimal(item["high"]) for item in window):
            highs.append({"index": index, "price": quantize_4(pivot_high)})
        if pivot_low == min(_decimal(item["low"]) for item in window):
            lows.append({"index": index, "price": quantize_4(pivot_low)})
    return {"swing_highs": highs, "swing_lows": lows}


def nearest_support_resistance(bars, current_price):
    current_price = _decimal(current_price)
    points = swing_points(bars)
    resistances = [item["price"] for item in points["swing_highs"] if item["price"] > current_price]
    supports = [item["price"] for item in points["swing_lows"] if item["price"] < current_price]
    return {
        "nearest_resistance": quantize_4(min(resistances)) if resistances else None,
        "nearest_support": quantize_4(max(supports)) if supports else None,
    }


def candle_statistics(bar):
    open_price, high, low, close = (
        _decimal(bar["open"]), _decimal(bar["high"]), _decimal(bar["low"]), _decimal(bar["close"]),
    )
    body = abs(close - open_price)
    price_range = high - low
    body_ratio = quantize_4(body / price_range) if price_range > 0 else quantize_4(Decimal(0))
    return {"body": quantize_4(body), "range": quantize_4(price_range), "body_ratio": body_ratio}


def spread_to_atr_ratio(spread, atr_value):
    spread, atr_value = _decimal(spread), _decimal(atr_value)
    if atr_value == 0:
        raise IndicatorInputError("spread-to-ATR ratio requires a positive ATR")
    return quantize_4(spread / atr_value)


def multi_timeframe_direction(confirmation_bars, period=21):
    """EMA(period) slope sign over the confirmation timeframe's closed bars."""
    _require_min_bars(confirmation_bars, period + 1, "multi-timeframe direction")
    closes = _closes(confirmation_bars)
    series = ema_series(closes, period)
    if len(series) < 2:
        raise IndicatorInputError("multi-timeframe direction requires at least two EMA points")
    slope = series[-1] - series[-2]
    if slope > 0:
        return "UP"
    if slope < 0:
        return "DOWN"
    return "FLAT"


__all__ = (
    "IndicatorInputError",
    "adx",
    "atr",
    "candle_statistics",
    "ema",
    "ema_series",
    "macd",
    "multi_timeframe_direction",
    "nearest_support_resistance",
    "rsi",
    "spread_to_atr_ratio",
    "swing_points",
)
