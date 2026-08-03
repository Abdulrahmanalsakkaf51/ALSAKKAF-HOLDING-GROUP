"""Tests for alsakkaf_scalping_strategy.py (TRL-R2-012 contract Section 8)."""

import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import alsakkaf_scalping_test_support as support
from trading_lab_app import alsakkaf_scalping_strategy as strategy
from trading_lab_app.timeline_data import format_utc


def _now():
    return format_utc(datetime.now(timezone.utc))


def _soon():
    return format_utc(datetime.now(timezone.utc) + timedelta(minutes=5))


class ScoreThresholdTests(unittest.TestCase):
    def test_classify_trade_candidate(self):
        self.assertEqual(strategy.classify_score(80, "BUY"), "TRADE_CANDIDATE")

    def test_classify_wait(self):
        self.assertEqual(strategy.classify_score(65, "BUY"), "WAIT")

    def test_classify_reject(self):
        self.assertEqual(strategy.classify_score(30, "BUY"), "REJECT")

    def test_direction_none_forces_wait(self):
        self.assertEqual(strategy.classify_score(90, "NONE"), "WAIT")

    def test_boundary_75_is_trade_candidate(self):
        self.assertEqual(strategy.classify_score(75, "BUY"), "TRADE_CANDIDATE")

    def test_boundary_60_is_wait(self):
        self.assertEqual(strategy.classify_score(60, "BUY"), "WAIT")

    def test_boundary_59_is_reject(self):
        self.assertEqual(strategy.classify_score(59, "BUY"), "REJECT")


class DirectionTests(unittest.TestCase):
    def test_buy_direction(self):
        self.assertEqual(strategy.determine_direction("10", "9", "0.5"), "BUY")

    def test_sell_direction(self):
        self.assertEqual(strategy.determine_direction("9", "10", "-0.5"), "SELL")

    def test_none_when_conflicting(self):
        self.assertEqual(strategy.determine_direction("10", "9", "-0.5"), "NONE")


class EvaluateSetupTests(unittest.TestCase):
    def test_strong_breakout_is_trade_candidate_buy(self):
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        result = strategy.evaluate_setup(entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        self.assertEqual(result["direction"], "BUY")
        self.assertEqual(result["classification"], "TRADE_CANDIDATE")
        self.assertEqual(sum(result["scores"].values()), result["total_score"])
        self.assertLessEqual(result["total_score"], strategy.TOTAL_SCORE_CAP)

    def test_flat_chop_never_trade_candidate(self):
        entry_bars = support.make_flat_choppy_bars()
        confirmation_bars = support.make_flat_choppy_bars()
        result = strategy.evaluate_setup(entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        self.assertNotEqual(result["classification"], "TRADE_CANDIDATE")

    def test_category_caps_never_exceeded(self):
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        result = strategy.evaluate_setup(entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        for category, score in result["scores"].items():
            self.assertLessEqual(score, strategy.CATEGORY_CAPS[category])
            self.assertGreaterEqual(score, 0)


class R2010BridgeTests(unittest.TestCase):
    def test_build_analysis_input_has_eleven_evidence_items(self):
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        evaluation = strategy.evaluate_setup(entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        envelope = strategy.build_analysis_input(
            "XAUUSD", "ALSAKKAF_PRECISION_SCALPING", evaluation, entry_bars,
            _now(), "BUY", "1955.00", ["1962.00", "1963.00", "1964.00"],
            [Decimal("50"), Decimal("30"), Decimal("20")], _soon(), False,
        )
        self.assertEqual(len(envelope["evidence_inputs"]), 11)
        self.assertEqual(envelope["schema_version"], "TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1")
        self.assertEqual(envelope["snapshot"]["timeframe"], "M5")

    def test_event_risk_blocked_forces_maximal_event_risk_evidence(self):
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        evaluation = strategy.evaluate_setup(entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        envelope = strategy.build_analysis_input(
            "XAUUSD", "ALSAKKAF_PRECISION_SCALPING", evaluation, entry_bars,
            _now(), "BUY", "1955.00", ["1962.00", "1963.00", "1964.00"],
            [Decimal("50"), Decimal("30"), Decimal("20")], _soon(), True,
        )
        event_risk_item = next(item for item in envelope["evidence_inputs"] if item["category"] == "EVENT_RISK")
        self.assertEqual(event_risk_item["normalized_strength"], "1.0000")

    def test_run_r2010_bridge_reaches_trade_candidate(self):
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        evaluation = strategy.evaluate_setup(entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        self.assertEqual(evaluation["classification"], "TRADE_CANDIDATE")
        mode_svc = support.make_mode_service("MT5_DEMO_AUTOMATED")
        mi_service = support.make_mi_service(mode_svc)
        import tempfile
        envelope = strategy.build_analysis_input(
            "XAUUSD", "ALSAKKAF_PRECISION_SCALPING", evaluation, entry_bars,
            _now(), evaluation["direction"], "1955.00",
            ["1962.00", "1963.00", "1964.00"], [Decimal("50"), Decimal("30"), Decimal("20")],
            _soon(), False,
        )
        result = strategy.run_r2010_bridge(mi_service, envelope, tempfile.mkdtemp())
        self.assertEqual(result["decision"]["final_status"], "TRADE_CANDIDATE")

    def test_run_r2010_bridge_never_leaves_scratch_file_behind(self):
        import os
        import tempfile
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        evaluation = strategy.evaluate_setup(entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        mode_svc = support.make_mode_service("MT5_DEMO_AUTOMATED")
        mi_service = support.make_mi_service(mode_svc)
        scratch_directory = tempfile.mkdtemp()
        envelope = strategy.build_analysis_input(
            "XAUUSD", "ALSAKKAF_PRECISION_SCALPING", evaluation, entry_bars,
            _now(), evaluation["direction"], "1955.00",
            ["1962.00", "1963.00", "1964.00"], [Decimal("50"), Decimal("30"), Decimal("20")],
            _soon(), False,
        )
        strategy.run_r2010_bridge(mi_service, envelope, scratch_directory)
        self.assertEqual(os.listdir(scratch_directory), [])


if __name__ == "__main__":
    unittest.main()
