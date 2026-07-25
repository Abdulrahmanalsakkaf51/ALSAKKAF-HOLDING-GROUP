# -*- coding: utf-8 -*-
"""SMA calculations, transition-only signals, and strategy identity."""
import math

from .canonical import (
    NumericSafetyError,
    _checked_divide,
    _checked_result,
    _finite_float,
)

def sma(closes, period):
    """Simple moving averages with no intermediate rounding."""
    if type(period) is not int or period <= 0:
        raise ValueError("period must be a positive integer")
    if type(closes) is not list:
        raise ValueError("closes must be an exact built-in list")
    values = []
    for value in closes:
        converted = _finite_float(value)
        if converted is None:
            raise ValueError("closes must contain finite numeric non-boolean values")
        values.append(converted)
    result = []
    for index in range(len(values)):
        if index + 1 < period:
            result.append(None)
            continue
        window = values[index + 1 - period:index + 1]
        try:
            window_sum = math.fsum(window)
        except (OverflowError, ValueError) as error:
            raise NumericSafetyError("unsafe arithmetic during SMA window sum") from error
        checked_sum = _checked_result(window_sum, "SMA window sum")
        result.append(_checked_divide(checked_sum, period, "SMA average"))
    return result


def _sma_cross_signals_from_series(ohlcv, fast_series, slow_series):
    """Derive transition-only signals from complete, aligned SMA series."""
    if type(ohlcv) is not list:
        raise ValueError("ohlcv must be an exact built-in list")
    if type(fast_series) is not list or type(slow_series) is not list:
        raise ValueError("SMA series must be exact built-in lists")
    if len(fast_series) != len(ohlcv) or len(slow_series) != len(ohlcv):
        raise ValueError("SMA series lengths must match ohlcv")
    signals = []
    for index, bar in enumerate(ohlcv):
        action = "none"
        if index > 0:
            previous_fast = fast_series[index - 1]
            previous_slow = slow_series[index - 1]
            current_fast = fast_series[index]
            current_slow = slow_series[index]
            if None not in (previous_fast, previous_slow, current_fast, current_slow):
                if previous_fast <= previous_slow and current_fast > current_slow:
                    action = "enter"
                elif previous_fast >= previous_slow and current_fast < current_slow:
                    action = "exit"
        signals.append((bar["date"], action))
    return signals


def sma_cross_signals(ohlcv, fast, slow, _sma_function=None):
    """Return only genuine bullish/bearish transitions, never regime repeats."""
    if (type(fast) is not int or fast <= 0
            or type(slow) is not int or slow <= 0
            or fast >= slow):
        raise ValueError("SMA periods must satisfy 1 <= fast < slow")
    if type(ohlcv) is not list:
        raise ValueError("ohlcv must be an exact built-in list")
    closes = [bar["close"] for bar in ohlcv]
    calculate_sma = sma if _sma_function is None else _sma_function
    fast_series = calculate_sma(closes, fast)
    slow_series = calculate_sma(closes, slow)
    return _sma_cross_signals_from_series(ohlcv, fast_series, slow_series)

def _safe_raw_strategy_identity(strategy_rules):
    candidate = None
    if type(strategy_rules) is dict:
        candidate = strategy_rules
    elif (type(strategy_rules) is list and len(strategy_rules) == 1
          and type(strategy_rules[0]) is dict):
        candidate = strategy_rules[0]
    if candidate is None:
        return None
    identity = {}
    for field in ("strategy_id", "strategy_version", "family", "symbol"):
        value = candidate.get(field)
        if type(value) is str:
            identity[field] = value
    return identity or None
