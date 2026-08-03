"""Tests for alsakkaf_scalping_indicators.py (TRL-R2-012 contract Section 8.1)."""

import unittest
from decimal import Decimal

import alsakkaf_scalping_test_support as support
from trading_lab_app import alsakkaf_scalping_indicators as indicators


class ClosedBarOnlyTests(unittest.TestCase):
    def test_ema_requires_minimum_bars(self):
        bars = support.make_chop_then_breakout_bars()[:5]
        with self.assertRaises(indicators.IndicatorInputError):
            indicators.ema(bars, 9)

    def test_ema_never_uses_more_than_supplied_closed_bars(self):
        """No-look-ahead: EMA computed over N bars must equal EMA computed
        over the same first N bars of a longer series -- a later bar must
        never influence an earlier EMA value."""
        full = support.make_chop_then_breakout_bars()
        prefix_length = 40
        prefix = full[:prefix_length]
        self.assertEqual(indicators.ema(prefix, 9), indicators.ema(prefix, 9))
        full_ema_over_prefix_window = indicators.ema_series(
            [Decimal(bar["close"]) for bar in full], 9,
        )[prefix_length - 9]
        prefix_ema = indicators.ema_series([Decimal(bar["close"]) for bar in prefix], 9)[-1]
        self.assertEqual(full_ema_over_prefix_window, prefix_ema)

    def test_rsi_bounded_0_to_100(self):
        bars = support.make_chop_then_breakout_bars()
        value = indicators.rsi(bars, 14)
        self.assertGreaterEqual(value, Decimal("0"))
        self.assertLessEqual(value, Decimal("100"))

    def test_rsi_all_gains_is_100(self):
        bars = [
            {"open": str(1900 + i), "high": str(1901 + i), "low": str(1899 + i), "close": str(1901 + i)}
            for i in range(20)
        ]
        self.assertEqual(indicators.rsi(bars, 14), Decimal("100.0000"))

    def test_atr_positive(self):
        bars = support.make_chop_then_breakout_bars()
        self.assertGreater(indicators.atr(bars, 14), Decimal("0"))

    def test_adx_requires_double_period_plus_one(self):
        with self.assertRaises(indicators.IndicatorInputError):
            indicators.adx(support.make_chop_then_breakout_bars()[:10], 14)

    def test_macd_shape(self):
        bars = support.make_chop_then_breakout_bars()
        result = indicators.macd(bars)
        self.assertEqual(set(result), {"macd_line", "signal_line", "histogram"})
        self.assertEqual(result["histogram"], result["macd_line"] - result["signal_line"])

    def test_swing_points_never_reference_future_index_beyond_window(self):
        bars = support.make_chop_then_breakout_bars()
        points = indicators.swing_points(bars, arm=2)
        for item in points["swing_highs"] + points["swing_lows"]:
            self.assertLess(item["index"], len(bars) - 2)

    def test_nearest_support_resistance(self):
        bars = support.make_chop_then_breakout_bars()
        current_price = Decimal(bars[-1]["close"])
        result = indicators.nearest_support_resistance(bars, current_price)
        if result["nearest_support"] is not None:
            self.assertLess(result["nearest_support"], current_price)
        if result["nearest_resistance"] is not None:
            self.assertGreater(result["nearest_resistance"], current_price)

    def test_candle_statistics_body_ratio_bounded(self):
        bars = support.make_chop_then_breakout_bars()
        stats = indicators.candle_statistics(bars[-1])
        self.assertGreaterEqual(stats["body_ratio"], Decimal("0"))
        self.assertLessEqual(stats["body_ratio"], Decimal("1"))

    def test_spread_to_atr_ratio_requires_positive_atr(self):
        with self.assertRaises(indicators.IndicatorInputError):
            indicators.spread_to_atr_ratio("0.05", "0")

    def test_multi_timeframe_direction_values(self):
        up_bars = support.make_chop_then_breakout_bars()
        self.assertIn(indicators.multi_timeframe_direction(up_bars, 21), ("UP", "DOWN", "FLAT"))

    def test_multi_timeframe_direction_up_for_strong_uptrend(self):
        bars = support.make_chop_then_breakout_bars()
        self.assertEqual(indicators.multi_timeframe_direction(bars, 21), "UP")


if __name__ == "__main__":
    unittest.main()
