# -*- coding: utf-8 -*-
"""Behavior-level tests for the TRL Release 1 causal research kernel."""
import ast
import copy
import contextlib
import datetime
import hashlib
import importlib
import importlib.util
import io
import json
import math
import os
import runpy
import subprocess
import sys
import types
import unittest
from unittest import mock

import build_demo_pack
import trading_lab as tl


BASE = os.path.dirname(os.path.abspath(__file__))
REPOSITORY_ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
PACKAGE_MODULE_NAME = "09_AI_Systems.02_Tools.Trading_Lab.trading_lab"
EXPECTED_FACADE_CALLABLES = (
    "canonical_json", "canonical_sha256", "validate_market_pack",
    "validate_strategy", "sma", "sma_cross_signals",
    "check_entry_allowed", "run_backtest",
    "performance_report_markdown", "decision_log_entry",
    "_metadata", "_run_validated", "_engine_source_digest",
)


def independent_engine_bundle_digest(source_files):
    digest = hashlib.sha256()
    digest.update(b"TRL_ENGINE_SOURCE_BUNDLE_V1\n")
    for relative_path in sorted(source_files):
        path_bytes = relative_path.encode("utf-8", "strict")
        source_text = source_files[relative_path].decode("utf-8", "strict")
        normalized = source_text.replace("\r\n", "\n").replace("\r", "\n")
        normalized_bytes = normalized.encode("utf-8", "strict")
        digest.update(b"PATH\0")
        digest.update(str(len(path_bytes)).encode("ascii"))
        digest.update(b"\0")
        digest.update(path_bytes)
        digest.update(b"\nSIZE\0")
        digest.update(str(len(normalized_bytes)).encode("ascii"))
        digest.update(b"\0")
        digest.update(normalized_bytes)
        digest.update(b"\nEND\0")
        digest.update(path_bytes)
        digest.update(b"\n")
    return digest.hexdigest()


def without_provenance(report):
    semantic = copy.deepcopy(report)
    metadata = semantic["metadata"]
    for field in ("run_id", "checkpoint_id", "engine_source_digest",
                  "engine_source_manifest"):
        metadata.pop(field, None)
    metadata.pop("engine", None)
    return semantic


def repository_file_state():
    """Return file metadata proving module execution creates no artifact."""
    state = {}
    for directory, directory_names, file_names in os.walk(REPOSITORY_ROOT):
        directory_names[:] = sorted(
            name for name in directory_names if name != ".git"
        )
        for name in sorted(file_names):
            path = os.path.join(directory, name)
            relative_path = os.path.relpath(path, REPOSITORY_ROOT)
            details = os.stat(path)
            state[relative_path] = (details.st_size, details.st_mtime_ns)
    return state


@contextlib.contextmanager
def preserved_process_state():
    """Restore process-global import and execution state exactly on exit."""
    original_cwd = os.getcwd()
    original_sys_path = list(sys.path)
    original_sys_modules = dict(sys.modules)
    original_sys_argv = sys.argv
    original_sys_argv_values = list(sys.argv)
    try:
        yield
    finally:
        os.chdir(original_cwd)
        sys.path[:] = original_sys_path
        sys.argv = original_sys_argv
        sys.argv[:] = original_sys_argv_values
        for name in tuple(sys.modules):
            if name not in original_sys_modules:
                del sys.modules[name]
        for name, module in original_sys_modules.items():
            sys.modules[name] = module


class UnsupportedValue:
    pass


class DictSubclass(dict):
    pass


class ListSubclass(list):
    pass


class StringSubclass(str):
    pass


class FloatSubclass(float):
    pass


def assert_no_nonfinite_float(test_case, value):
    if type(value) is float:
        test_case.assertTrue(math.isfinite(value), repr(value))
    elif isinstance(value, dict):
        for key, item in value.items():
            assert_no_nonfinite_float(test_case, key)
            assert_no_nonfinite_float(test_case, item)
    elif isinstance(value, (list, tuple, set, frozenset)):
        for item in value:
            assert_no_nonfinite_float(test_case, item)


def strategy(**changes):
    rule = {
        "strategy_id": tl.STRATEGY_ID,
        "strategy_version": tl.STRATEGY_VERSION,
        "family": tl.STRATEGY_FAMILY,
        "symbol": "X",
        "fast": 2,
        "slow": 3,
        "paper_size_pct": 5.0,
    }
    rule.update(changes)
    return rule


def pack(closes=None, opens=None, symbol="X", asset_class="equity"):
    closes = list(closes if closes is not None else [100.0] * 5)
    opens = list(opens if opens is not None else closes)
    bars = []
    start = datetime.date(2026, 1, 1)
    for index, (open_price, close_price) in enumerate(zip(opens, closes)):
        high = max(open_price, close_price) + 1.0
        low = max(0.000001, min(open_price, close_price) - 1.0)
        bars.append({
            "date": (start + datetime.timedelta(days=index)).isoformat(),
            "open": open_price,
            "high": high,
            "low": low,
            "close": close_price,
            "volume": 1000,
        })
    return {
        "pack_id": "TEST-PACK-001",
        "as_of": "2026-02-01",
        "prepared_by": "unit test synthetic fixture",
        "note": "SYNTHETIC TEST DATA - NOT REAL MARKET DATA",
        "instruments": [{
            "symbol": symbol,
            "asset_class": asset_class,
            "data_source": "deterministic unit test fixture",
            "data_quality_note": "complete synthetic sequence",
            "ohlcv": bars,
        }],
    }


def run(closes=None, opens=None, rule=None, risk_policy=None):
    return tl.run_backtest(
        rule or strategy(), pack(closes=closes, opens=opens), risk_policy,
    )


class SmaSignalTests(unittest.TestCase):
    def test_exact_sma_values(self):
        values = tl.sma([1, 2, 3, 4, 5], 3)
        self.assertEqual(values, [None, None, 2.0, 3.0, 4.0])

    def test_high_dynamic_range_period_two_values_are_stable(self):
        values = tl.sma([1e150, 1, 2, 1.4], 2)
        expected = [None, 5e149, 1.5, 1.7]
        for actual, wanted in zip(values, expected):
            if wanted is None:
                self.assertIsNone(actual)
            else:
                self.assertAlmostEqual(actual, wanted)

    def test_complete_reviewer_sequence_is_stable(self):
        values = tl.sma([1e150, 1, 2, 1.4, 1], 2)
        expected = [None, 5e149, 1.5, 1.7, 1.2]
        for actual, wanted in zip(values, expected):
            if wanted is None:
                self.assertIsNone(actual)
            else:
                self.assertAlmostEqual(actual, wanted)

    def test_high_dynamic_range_crosses_bullish_then_bearish(self):
        bars = pack([1e150, 1, 2, 1.4, 1])["instruments"][0]["ohlcv"]
        signals = tl.sma_cross_signals(bars, 1, 2)
        self.assertEqual([action for _, action in signals],
                         ["none", "none", "enter", "exit", "none"])

    def test_precomputed_series_match_public_signals_on_normal_data(self):
        bars = pack([3, 2, 1, 4, 5, 2, 1])["instruments"][0]["ohlcv"]
        closes = [bar["close"] for bar in bars]
        expected = tl.sma_cross_signals(bars, 2, 3)
        actual = tl._sma_cross_signals_from_series(
            bars, tl.sma(closes, 2), tl.sma(closes, 3),
        )
        self.assertEqual(actual, expected)

    def test_precomputed_high_dynamic_range_crossings_are_identical(self):
        bars = pack([1e150, 1, 2, 1.4, 1])["instruments"][0]["ohlcv"]
        closes = [bar["close"] for bar in bars]
        expected = tl.sma_cross_signals(bars, 1, 2)
        actual = tl._sma_cross_signals_from_series(
            bars, tl.sma(closes, 1), tl.sma(closes, 2),
        )
        self.assertEqual(actual, expected)
        self.assertEqual([action for _, action in actual],
                         ["none", "none", "enter", "exit", "none"])

    def test_validated_run_calculates_each_sma_once(self):
        with mock.patch.object(tl, "sma", wraps=tl.sma) as calculate_sma:
            report = run([3, 2, 1, 4, 5])
        self.assertEqual(report["validation"]["outcome"], "VALID")
        self.assertEqual(calculate_sma.call_count, 2)
        self.assertEqual([call.args[1] for call in calculate_sma.call_args_list],
                         [2, 3])

    def test_public_signal_helper_calculates_each_sma_once(self):
        bars = pack([3, 2, 1, 4, 5])["instruments"][0]["ohlcv"]
        with mock.patch.object(tl, "sma", wraps=tl.sma) as calculate_sma:
            signals = tl.sma_cross_signals(bars, 2, 3)
        self.assertEqual(len(signals), len(bars))
        self.assertEqual(calculate_sma.call_count, 2)
        self.assertEqual([call.args[1] for call in calculate_sma.call_args_list],
                         [2, 3])

    def test_precomputed_series_lengths_must_match_bars(self):
        bars = pack([3, 2, 1, 4])["instruments"][0]["ohlcv"]
        with self.assertRaisesRegex(ValueError, "lengths must match"):
            tl._sma_cross_signals_from_series(
                bars, [None] * len(bars), [None] * (len(bars) - 1),
            )

    def test_signal_prefix_does_not_access_future_bars(self):
        prefix = pack([3, 2, 1, 4, 5])["instruments"][0]["ohlcv"]
        extended = pack([3, 2, 1, 4, 5, 1000, 0.5])["instruments"][0]["ohlcv"]
        prefix_signals = tl.sma_cross_signals(prefix, 2, 3)
        extended_signals = tl.sma_cross_signals(extended, 2, 3)
        self.assertEqual(prefix_signals, extended_signals[:len(prefix)])

    def test_cancellation_loss_does_not_leave_incorrect_terminal_position(self):
        report = run(
            [1e150, 1, 2, 1.4, 1],
            rule=strategy(fast=1, slow=2),
        )
        self.assertEqual([fill["side"] for fill in report["hypothetical_fills"]],
                         ["BUY", "SELL"])
        self.assertIsNone(report["open_position"])
        self.assertEqual(report["reason_code"], tl.COMPLETED_TRADE_HISTORY)

    def test_sma_summation_overflow_fails_closed(self):
        with self.assertRaisesRegex(tl.NumericSafetyError, "SMA window sum"):
            tl.sma([1e308, 1e308], 2)

    def test_genuine_bullish_crossing_transition(self):
        signals = tl.sma_cross_signals(pack([3, 2, 1, 4])["instruments"][0]["ohlcv"], 2, 3)
        self.assertEqual(signals[-1][1], "enter")

    def test_genuine_bearish_crossing_transition(self):
        signals = tl.sma_cross_signals(
            pack([3, 2, 1, 4, 3, 1])["instruments"][0]["ohlcv"], 2, 3,
        )
        self.assertEqual(signals[-1][1], "exit")

    def test_no_repeated_signals_in_same_regime(self):
        signals = tl.sma_cross_signals(
            pack([3, 2, 1, 4, 5, 6, 3, 1, 0.5])["instruments"][0]["ohlcv"],
            2, 3,
        )
        actions = [action for _, action in signals if action != "none"]
        self.assertEqual(actions, ["enter", "exit"])

    def test_crossing_equality_boundaries_are_events(self):
        bullish = tl.sma_cross_signals(
            pack([1, 1, 2])["instruments"][0]["ohlcv"], 1, 2,
        )
        bearish = tl.sma_cross_signals(
            pack([2, 2, 1])["instruments"][0]["ohlcv"], 1, 2,
        )
        self.assertEqual(bullish[-1][1], "enter")
        self.assertEqual(bearish[-1][1], "exit")

    def test_invalid_sma_periods(self):
        for fast, slow in ((0, 3), (3, 3), (4, 3), (True, 3)):
            with self.subTest(fast=fast, slow=slow):
                report = run(rule=strategy(fast=fast, slow=slow))
                self.assertEqual(report["reason_code"], tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)
        with self.assertRaises(ValueError):
            tl.sma([1, 2], 0)


class InputValidationTests(unittest.TestCase):
    def assert_invalid(self, market_pack):
        report = tl.run_backtest(strategy(), market_pack)
        self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(report["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(report["validation"]["outcome"], "INVALID")
        self.assertIsInstance(tl.canonical_json(report), str)
        assert_no_nonfinite_float(self, report)

    def test_missing_required_pack_fields(self):
        market_pack = pack()
        del market_pack["pack_id"]
        self.assert_invalid(market_pack)

    def test_missing_required_instrument_and_bar_fields(self):
        market_pack = pack()
        del market_pack["instruments"][0]["data_source"]
        del market_pack["instruments"][0]["ohlcv"][0]["volume"]
        self.assert_invalid(market_pack)

    def test_unsupported_structural_fields(self):
        fixtures = []
        market_pack = pack()
        market_pack["surprise"] = 1
        fixtures.append(market_pack)
        market_pack = pack()
        market_pack["instruments"][0]["currency"] = "USD"
        fixtures.append(market_pack)
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["adjusted"] = True
        fixtures.append(market_pack)
        for fixture in fixtures:
            with self.subTest(keys=sorted(fixture)):
                self.assert_invalid(fixture)

    def test_boolean_rejected_as_numeric(self):
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["close"] = True
        self.assert_invalid(market_pack)

    def test_numeric_subclasses_are_rejected_across_public_schemas(self):
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["close"] = FloatSubclass(100.0)
        data_report = tl.run_backtest(strategy(), market_pack)
        strategy_report = run(rule=strategy(paper_size_pct=FloatSubclass(5.0)))
        risk_report = run(risk_policy={"max_position_pct": FloatSubclass(4.0)})
        self.assertEqual(data_report["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(strategy_report["reason_code"],
                         tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)
        self.assertEqual(risk_report["reason_code"],
                         tl.BLOCKED_RISK_OVERRIDE_ATTEMPT)

    def test_nan_and_infinity_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf")):
            market_pack = pack()
            market_pack["instruments"][0]["ohlcv"][0]["open"] = value
            with self.subTest(value=value):
                self.assert_invalid(market_pack)

    def test_extreme_ohlc_integer_and_near_max_float_are_safely_blocked(self):
        for value in (10 ** 400, 1.797e308):
            market_pack = pack()
            market_pack["instruments"][0]["ohlcv"][0]["open"] = value
            with self.subTest(value_type=type(value).__name__):
                self.assert_invalid(market_pack)

    def test_extreme_volume_is_safely_blocked(self):
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["volume"] = 10 ** 400
        self.assert_invalid(market_pack)

    def test_oversized_positive_and_negative_ohlc_integers_are_bounded(self):
        huge = 10 ** 5000
        reports = []
        for value in (huge, -huge):
            market_pack = pack()
            market_pack["instruments"][0]["ohlcv"][0]["open"] = value
            with self.subTest(sign=1 if value > 0 else -1):
                first = tl.run_backtest(strategy(), market_pack)
                second = tl.run_backtest(strategy(), copy.deepcopy(market_pack))
                self.assert_invalid(market_pack)
                self.assertEqual(first, second)
                self.assertEqual(first["metadata"]["input_data_hash"],
                                 second["metadata"]["input_data_hash"])
                self.assertEqual(first["metadata"]["run_id"],
                                 second["metadata"]["run_id"])
                serialized = json.dumps(first, allow_nan=False)
                self.assertLess(len(serialized), 10000)
                self.assertIn("must convert to a finite float", serialized)
                reports.append(first)
        self.assertNotEqual(reports[0]["metadata"]["input_data_hash"],
                            reports[1]["metadata"]["input_data_hash"])

    def test_distinct_oversized_ohlc_integers_have_distinct_stable_hashes(self):
        reports = []
        for value in (10 ** 5000, (10 ** 5000) + 1):
            market_pack = pack()
            market_pack["instruments"][0]["ohlcv"][0]["close"] = value
            reports.append(tl.run_backtest(strategy(), market_pack))
        self.assertNotEqual(reports[0]["metadata"]["input_data_hash"],
                            reports[1]["metadata"]["input_data_hash"])
        self.assertNotEqual(reports[0]["metadata"]["run_id"],
                            reports[1]["metadata"]["run_id"])
        marker = tl.canonical_json({"value": 10 ** 5000})
        self.assertIn('"__oversized_integer__"', marker)
        self.assertLess(len(marker), 300)
        self.assertEqual(tl.canonical_json({"value": 123}), '{"value":123}')

    def test_zero_and_negative_prices_rejected(self):
        for value in (0, -1):
            market_pack = pack()
            market_pack["instruments"][0]["ohlcv"][0]["low"] = value
            with self.subTest(value=value):
                self.assert_invalid(market_pack)

    def test_negative_volume_rejected(self):
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["volume"] = -1
        self.assert_invalid(market_pack)

    def test_invalid_ohlc_relationships(self):
        fixtures = []
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["high"] = 99
        fixtures.append(market_pack)
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["low"] = 101
        fixtures.append(market_pack)
        market_pack = pack()
        bar = market_pack["instruments"][0]["ohlcv"][0]
        bar.update({"open": 100, "close": 100, "high": 90, "low": 95})
        fixtures.append(market_pack)
        for fixture in fixtures:
            with self.subTest(bar=fixture["instruments"][0]["ohlcv"][0]):
                self.assert_invalid(fixture)

    def test_exact_ohlc_ordering_catches_float_rounded_violations(self):
        base = 10 ** 20
        cases = (
            (
                "high_below_open",
                {"open": base + 1, "high": base,
                 "low": base - 1, "close": base},
                "high must be >= max(open, close)",
            ),
            (
                "low_above_open",
                {"open": base, "high": 2 * base,
                 "low": base + 1, "close": 2 * base},
                "low must be <= min(open, close)",
            ),
            (
                "high_below_close",
                {"open": base, "high": base,
                 "low": base - 1, "close": base + 1},
                "high must be >= max(open, close)",
            ),
            (
                "low_above_close",
                {"open": 2 * base, "high": 2 * base,
                 "low": base + 1, "close": base},
                "low must be <= min(open, close)",
            ),
        )
        with mock.patch.object(
                tl, "_run_validated",
                side_effect=AssertionError("financial evaluation must not run")):
            for label, values, expected_error in cases:
                with self.subTest(label=label):
                    market_pack = pack()
                    market_pack["instruments"][0]["ohlcv"][0].update(values)
                    report = tl.run_backtest(strategy(), market_pack)
                    self.assertEqual(report["reason_code"],
                                     tl.BLOCKED_INVALID_INPUT)
                    self.assertTrue(any(
                        expected_error in error
                        for error in report["validation"]["errors"]
                    ))
                    self.assertEqual(report["hypothetical_fills"], [])
                    self.assertEqual(report["trade_list"], [])
                    self.assertIsNone(report["open_position"])
                    self.assertEqual(report["equity_curve"], [])

    def test_integer_float_representability_policy(self):
        exactly_representable = 2 ** 100
        market_pack = pack()
        for bar in market_pack["instruments"][0]["ohlcv"]:
            bar.update({
                "open": exactly_representable,
                "high": 2 * exactly_representable,
                "low": exactly_representable // 2,
                "close": exactly_representable,
                "volume": 2 ** 60,
            })
        self.assertEqual(tl.validate_market_pack(market_pack), [])
        accepted = tl.run_backtest(strategy(), market_pack)
        self.assertEqual(accepted["validation"]["outcome"], "VALID")

        unsafe_pack = pack()
        unsafe_pack["instruments"][0]["ohlcv"][0].update({
            "open": (2 ** 53) + 1,
            "high": 2 ** 54,
            "low": 2 ** 53,
            "close": 2 ** 53,
        })
        rejected = tl.run_backtest(strategy(), unsafe_pack)
        self.assertEqual(rejected["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertTrue(any(
            "without numeric loss" in error
            for error in rejected["validation"]["errors"]
        ))
        self.assertEqual(rejected["hypothetical_fills"], [])
        self.assertEqual(rejected["trade_list"], [])
        self.assertIsNone(rejected["open_position"])
        self.assertEqual(rejected["equity_curve"], [])

    def test_ordinary_integer_and_float_ohlc_remain_valid(self):
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0].update({
            "open": 100,
            "high": 101.5,
            "low": 99,
            "close": 100.25,
            "volume": 1000,
        })
        self.assertEqual(tl.validate_market_pack(market_pack), [])
        self.assertEqual(
            tl.run_backtest(strategy(), market_pack)["validation"]["outcome"],
            "VALID",
        )

    def test_duplicate_timestamps_rejected(self):
        market_pack = pack()
        bars = market_pack["instruments"][0]["ohlcv"]
        bars[1]["date"] = bars[0]["date"]
        self.assert_invalid(market_pack)

    def test_out_of_order_timestamps_rejected_without_sorting(self):
        market_pack = pack()
        bars = market_pack["instruments"][0]["ohlcv"]
        bars[0], bars[1] = bars[1], bars[0]
        before = copy.deepcopy(market_pack)
        self.assert_invalid(market_pack)
        self.assertEqual(market_pack, before)

    def test_multi_instrument_rejected(self):
        market_pack = pack()
        market_pack["instruments"].append(
            copy.deepcopy(market_pack["instruments"][0])
        )
        market_pack["instruments"][1]["symbol"] = "Y"
        self.assert_invalid(market_pack)

    def test_unsupported_asset_class_rejected(self):
        self.assert_invalid(pack(asset_class="crypto"))

    def test_strategy_instrument_mismatch(self):
        report = tl.run_backtest(strategy(symbol="Y"), pack(symbol="X"))
        self.assertEqual(report["reason_code"], tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)

    def test_invalid_iso_date_rejected(self):
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["date"] = "2026-02-30"
        self.assert_invalid(market_pack)

    def test_timestamp_normalization_overflow_is_blocked(self):
        for value in (
                "0001-01-01T00:00:00+14:00",
                "9999-12-31T23:59:59-14:00"):
            market_pack = pack()
            market_pack["instruments"][0]["ohlcv"][0]["date"] = value
            with self.subTest(value=value):
                self.assert_invalid(market_pack)

    def test_ordinary_offset_timestamp_remains_valid(self):
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0]["date"] = (
            "2026-01-01T04:00:00+04:00"
        )
        report = tl.run_backtest(strategy(), market_pack)
        self.assertEqual(report["validation"]["outcome"], "VALID")

    def test_pack_instrument_and_bar_require_exact_builtin_dictionaries(self):
        fixtures = [DictSubclass(pack())]
        market_pack = pack()
        market_pack["instruments"][0] = DictSubclass(
            market_pack["instruments"][0]
        )
        fixtures.append(market_pack)
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"][0] = DictSubclass(
            market_pack["instruments"][0]["ohlcv"][0]
        )
        fixtures.append(market_pack)
        for index, fixture in enumerate(fixtures):
            with self.subTest(location=index):
                report = tl.run_backtest(strategy(), fixture)
                self.assertEqual(report["reason_code"], tl.BLOCKED_INVALID_INPUT)
                self.assertTrue(any("exact built-in dictionary" in error
                                    for error in report["validation"]["errors"]))

    def test_instruments_and_ohlcv_require_exact_builtin_lists(self):
        instruments_pack = pack()
        instruments_pack["instruments"] = ListSubclass(
            instruments_pack["instruments"]
        )
        ohlcv_pack = pack()
        ohlcv_pack["instruments"][0]["ohlcv"] = ListSubclass(
            ohlcv_pack["instruments"][0]["ohlcv"]
        )
        for fixture in (instruments_pack, ohlcv_pack):
            with self.subTest(location=type(fixture["instruments"]).__name__):
                report = tl.run_backtest(strategy(), fixture)
                self.assertEqual(report["reason_code"], tl.BLOCKED_INVALID_INPUT)
                self.assertTrue(any("exact built-in list" in error
                                    for error in report["validation"]["errors"]))

    def test_symbol_and_timestamp_require_exact_builtin_strings(self):
        symbol_pack = pack()
        symbol_pack["instruments"][0]["symbol"] = StringSubclass("X")
        timestamp_pack = pack()
        timestamp_pack["instruments"][0]["ohlcv"][0]["date"] = (
            StringSubclass("2026-01-01")
        )
        for fixture in (symbol_pack, timestamp_pack):
            with self.subTest(value=fixture):
                self.assert_invalid(fixture)

    def test_rejected_subtype_contents_remain_audit_identity_sensitive(self):
        first_pack = pack([3, 2, 1, 4, 5])
        second_pack = pack([3, 2, 1, 4, 6])
        first_pack["instruments"][0]["ohlcv"] = ListSubclass(
            first_pack["instruments"][0]["ohlcv"]
        )
        second_pack["instruments"][0]["ohlcv"] = ListSubclass(
            second_pack["instruments"][0]["ohlcv"]
        )
        first = tl.run_backtest(strategy(), first_pack)
        second = tl.run_backtest(strategy(), second_pack)
        for report in (first, second):
            self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
            self.assertEqual(report["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertNotEqual(first["metadata"]["input_data_hash"],
                            second["metadata"]["input_data_hash"])
        self.assertNotEqual(first["metadata"]["run_id"],
                            second["metadata"]["run_id"])

    def test_exact_builtin_schema_values_remain_accepted_and_content_sensitive(self):
        first = run([3, 2, 1, 4, 5])
        second = run([3, 2, 1, 4, 6])
        self.assertEqual(first["validation"]["outcome"], "VALID")
        self.assertEqual(second["validation"]["outcome"], "VALID")
        self.assertNotEqual(first["metadata"]["input_data_hash"],
                            second["metadata"]["input_data_hash"])

    def test_wrong_container_and_field_types_fail_closed(self):
        fixtures = []
        market_pack = pack()
        market_pack["instruments"] = {"symbol": "X"}
        fixtures.append(market_pack)
        market_pack = pack()
        market_pack["instruments"][0]["ohlcv"] = "not-an-array"
        fixtures.append(market_pack)
        market_pack = pack()
        market_pack["instruments"][0]["asset_class"] = ["equity"]
        fixtures.append(market_pack)
        market_pack = pack()
        market_pack[1] = "unsupported non-string key"
        fixtures.append(market_pack)
        for fixture in fixtures:
            with self.subTest(value=repr(fixture)[:80]):
                self.assert_invalid(fixture)

    def test_insufficient_data_is_valid_no_trade(self):
        report = run([3, 2, 1])
        self.assertEqual(report["validation"]["outcome"], "VALID")
        self.assertEqual(report["outcome"], tl.OUTCOME_NO_TRADE)
        self.assertEqual(report["reason_code"], tl.NO_TRADE_INSUFFICIENT_HISTORY)


class CausalExecutionAccountingTests(unittest.TestCase):
    def assert_sequential_accounting_row_ids(self, report):
        identifiers = [row["accounting_row_id"]
                       for row in report["equity_curve"]]
        expected = ["ACCT-%06d" % index
                    for index in range(1, len(identifiers) + 1)]
        self.assertEqual(identifiers, expected)
        self.assertEqual(len(identifiers), len(set(identifiers)))

    def test_accounting_row_ids_are_sequential_unique_and_repeatable(self):
        first = run([3, 2, 1, 4, 5])
        second = run([3, 2, 1, 4, 5])
        self.assertGreater(len(first["equity_curve"]), 0)
        self.assert_sequential_accounting_row_ids(first)
        self.assertEqual(
            [row["accounting_row_id"] for row in first["equity_curve"]],
            [row["accounting_row_id"] for row in second["equity_curve"]],
        )

    def test_accounting_row_ids_cover_terminal_and_completed_positions(self):
        open_report = run([3, 2, 1, 4, 5])
        completed_report = run(
            [3, 2, 1, 4, 3, 1, 2],
            [3, 2, 1, 4, 10, 1, 20],
        )
        self.assertIsNotNone(open_report["open_position"])
        self.assertEqual(len(completed_report["trade_list"]), 1)
        for report in (open_report, completed_report):
            self.assert_sequential_accounting_row_ids(report)

        invalid_pack = pack()
        del invalid_pack["pack_id"]
        blocked = tl.run_backtest(strategy(), invalid_pack)
        self.assertEqual(blocked["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(blocked["equity_curve"], [])

    def test_signal_at_close_t_fills_only_at_t_plus_one_open(self):
        closes = [3, 2, 1, 4, 5]
        opens = [3, 2, 1, 4, 123]
        report = run(closes, opens)
        decision = report["decisions"][0]
        fill = report["hypothetical_fills"][0]
        self.assertEqual(decision["signal_timestamp"], "2026-01-04")
        self.assertEqual(fill["fill_timestamp"], "2026-01-05")
        self.assertNotEqual(fill["fill_timestamp"], decision["signal_timestamp"])
        self.assertEqual(fill["raw_opening_price"], 123.0)

    def test_entry_adverse_slippage_and_commission(self):
        report = run([3, 2, 1, 4, 5], [3, 2, 1, 4, 10])
        fill = report["hypothetical_fills"][0]
        self.assertAlmostEqual(fill["slipped_fill_price"], 10.005)
        self.assertAlmostEqual(fill["filled_notional"], 5.0)
        self.assertAlmostEqual(fill["commission"], 0.0025)
        self.assertAlmostEqual(fill["slippage_cost"], fill["units"] * 0.005)

    def test_exit_slippage_commission_realized_pnl_and_units(self):
        closes = [3, 2, 1, 4, 3, 1, 2]
        opens = [3, 2, 1, 4, 10, 1, 20]
        report = run(closes, opens)
        buy, sell = report["hypothetical_fills"]
        self.assertAlmostEqual(buy["slipped_fill_price"], 10.005)
        self.assertAlmostEqual(sell["slipped_fill_price"], 19.99)
        self.assertAlmostEqual(sell["commission"], sell["filled_notional"] * 0.0005)
        expected_net = (sell["filled_notional"] - sell["commission"]
                        - buy["filled_notional"] - buy["commission"])
        self.assertAlmostEqual(report["realized_pnl"], expected_net)
        self.assertAlmostEqual(report["final_cash"], 100.0 + expected_net)
        self.assertEqual(report["equity_curve"][-1]["position_units"], 0.0)

    def test_cash_units_and_per_bar_mark_to_market(self):
        report = run([3, 2, 1, 4, 12], [3, 2, 1, 4, 10])
        fill = report["hypothetical_fills"][0]
        row = report["equity_curve"][-1]
        expected_units = 5.0 / 10.005
        self.assertAlmostEqual(fill["units"], expected_units)
        self.assertAlmostEqual(row["cash"], 94.9975)
        self.assertAlmostEqual(row["position_value"], expected_units * 12)
        self.assertAlmostEqual(row["total_marked_equity"],
                               row["cash"] + row["position_value"])
        self.assertAlmostEqual(row["unrealized_pnl"],
                               row["position_value"] - 5.0 - 0.0025)

    def test_subnormal_and_unrepresentable_allocations_are_blocked(self):
        for allocation in (5e-324, 1e-323, 1e-320, 1e-308):
            with self.subTest(allocation=allocation):
                report = run(
                    [3, 2, 1, 4, 5],
                    rule=strategy(paper_size_pct=allocation),
                )
                self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
                self.assertEqual(
                    report["reason_code"],
                    tl.BLOCKED_INVALID_STRATEGY_PARAMETERS,
                )
                self.assertEqual(report["hypothetical_fills"], [])
                self.assertIsNone(report["open_position"])
                self.assertEqual(report["final_cash"], tl.STARTING_CASH)
                self.assertIn("representable nonzero allocation",
                              report["validation"]["errors"][0])
                json.dumps(report, allow_nan=False)

    def test_small_safe_and_standard_allocations_fully_reconcile(self):
        for allocation in (1e-12, 5.0):
            with self.subTest(allocation=allocation):
                report = run(
                    [3, 2, 1, 4, 5],
                    rule=strategy(paper_size_pct=allocation),
                )
                self.assertEqual(report["outcome"], tl.OUTCOME_FILL)
                fill = report["hypothetical_fills"][0]
                row = report["equity_curve"][-1]
                self.assertGreater(fill["units"], 0.0)
                self.assertGreater(fill["commission"], 0.0)
                self.assertGreater(fill["slippage_cost"], 0.0)
                self.assertNotEqual(row["cash"], tl.STARTING_CASH)
                expected_cash = tl.STARTING_CASH - (
                    fill["filled_notional"] + fill["commission"]
                )
                self.assertEqual(row["cash"], expected_cash)
                self.assertTrue(math.isclose(
                    fill["filled_notional"],
                    fill["units"] * fill["slipped_fill_price"],
                    rel_tol=1e-15,
                    abs_tol=0.0,
                ))
                self.assertEqual(
                    fill["commission"],
                    fill["filled_notional"] * tl.COMMISSION_RATE,
                )
                self.assertTrue(math.isclose(
                    fill["slippage_cost"],
                    fill["units"] * (
                        fill["slipped_fill_price"] - fill["raw_opening_price"]
                    ),
                    rel_tol=1e-15,
                    abs_tol=0.0,
                ))
                self.assertEqual(
                    row["cumulative_costs"],
                    row["cumulative_commission"]
                    + row["cumulative_slippage_cost"],
                )
                self.assertEqual(
                    row["position_value"], fill["units"] * row["close"]
                )
                self.assertEqual(
                    row["total_marked_equity"],
                    row["cash"] + row["position_value"],
                )
                json.dumps(report, allow_nan=False)

    def test_unrealized_drawdown_uses_marked_equity(self):
        report = run([3, 2, 1, 4, 0.1], [3, 2, 1, 4, 100])
        final = report["equity_curve"][-1]
        self.assertLess(final["unrealized_pnl"], 0)
        self.assertLess(final["drawdown_pct"], 0)
        self.assertEqual(report["realized_pnl"], 0.0)

    def test_open_terminal_position_is_not_liquidated(self):
        report = run([3, 2, 1, 4, 12], [3, 2, 1, 4, 10])
        self.assertEqual(len(report["hypothetical_fills"]), 1)
        self.assertEqual(report["hypothetical_fills"][0]["side"], "BUY")
        self.assertIsNotNone(report["open_position"])
        self.assertEqual(report["open_position"]["terminal_status"],
                         "OPEN_MARKED_TO_MARKET")
        self.assertAlmostEqual(report["open_position"]["market_value"],
                               report["equity_curve"][-1]["position_value"])
        self.assertEqual(report["cumulative_commission"], 0.0025)

    def test_final_bar_signal_has_audited_no_fill(self):
        report = run([3, 2, 1, 4])
        self.assertEqual(report["outcome"], tl.OUTCOME_NO_FILL)
        self.assertEqual(report["reason_code"], tl.NO_FILL_END_OF_DATA)
        self.assertEqual(report["hypothetical_fills"], [])
        self.assertEqual(report["decisions"][-1]["status"], "NO_FILL")

    def test_compounded_accounting_overflow_fails_closed(self):
        small, large = 1e-150, 1e150
        closes = [3, 2, 1, 4, small, small, large, large]
        opens = [3, 2, 1, 4, small, large, large, small]
        market_pack = pack(closes, opens)
        for bar in market_pack["instruments"][0]["ohlcv"]:
            bar["high"] = max(bar["open"], bar["close"])
            bar["low"] = min(bar["open"], bar["close"])
        report = tl.run_backtest(strategy(fast=1, slow=2), market_pack)
        self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(report["reason_code"],
                         tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)
        self.assertIn("trade net before entry commission",
                      report["validation"]["errors"][0])
        self.assertIsInstance(tl.canonical_json(report), str)
        assert_no_nonfinite_float(self, report)


class RiskOutcomeTests(unittest.TestCase):
    def test_complete_hard_risk_baseline_is_shared_by_valid_and_blocked_runs(self):
        expected = {
            "max_position_pct": 5.0,
            "drawdown_halt_pct": -15.0,
            "max_open_positions": 1,
            "leverage_allowed": False,
            "shorting_allowed": False,
            "increase_to_loser_allowed": False,
        }
        invalid_pack = pack()
        del invalid_pack["pack_id"]
        reports = {
            "valid": run([3, 2, 1, 4, 5]),
            "invalid_pack": tl.run_backtest(strategy(), invalid_pack),
            "invalid_strategy": run(rule=strategy(fast=0)),
            "position_limit": run(rule=strategy(paper_size_pct=6.0)),
            "risk_override": run(risk_policy={"max_position_pct": 6.0}),
        }
        self.assertEqual(reports["invalid_pack"]["reason_code"],
                         tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(reports["invalid_strategy"]["reason_code"],
                         tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)
        self.assertEqual(reports["position_limit"]["reason_code"],
                         tl.BLOCKED_POSITION_LIMIT)
        self.assertEqual(reports["risk_override"]["reason_code"],
                         tl.BLOCKED_RISK_OVERRIDE_ATTEMPT)
        for name, report in reports.items():
            with self.subTest(name=name):
                limits = report["metadata"]["effective_system_risk_limits"]
                self.assertEqual(limits, expected)
                self.assertFalse(limits["leverage_allowed"])
                self.assertFalse(limits["shorting_allowed"])
                self.assertFalse(limits["increase_to_loser_allowed"])

    def test_stricter_valid_policy_is_retained_without_weakening_baseline(self):
        rule = strategy(drawdown_halt_pct=-10.0)
        risk_policy = {"max_position_pct": 4.0}
        valid = tl.run_backtest(rule, pack(), risk_policy)
        invalid_pack = pack()
        del invalid_pack["pack_id"]
        blocked = tl.run_backtest(rule, invalid_pack, risk_policy)
        valid_limits = valid["metadata"]["effective_system_risk_limits"]
        blocked_limits = blocked["metadata"]["effective_system_risk_limits"]
        self.assertEqual(blocked["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(valid_limits, blocked_limits)
        self.assertEqual(valid_limits["max_position_pct"], 4.0)
        self.assertEqual(valid_limits["drawdown_halt_pct"], -10.0)
        self.assertEqual(valid_limits["max_open_positions"], 1)
        for field in ("leverage_allowed", "shorting_allowed",
                      "increase_to_loser_allowed"):
            self.assertFalse(valid_limits[field])

    def test_valid_strategy_identity_survives_invalid_market_pack(self):
        rule = strategy()
        invalid_pack = pack()
        del invalid_pack["pack_id"]
        report = tl.run_backtest(rule, invalid_pack)
        metadata = report["metadata"]
        self.assertEqual(report["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(metadata["strategy_id"], rule["strategy_id"])
        self.assertEqual(metadata["strategy_version"], rule["strategy_version"])
        self.assertEqual(metadata["strategy_parameters"], rule)
        self.assertEqual(metadata["strategy_definition_hash"],
                         tl.canonical_sha256(rule))
        self.assertEqual(report["events"][0]["strategy_id"], rule["strategy_id"])
        self.assertEqual(report["hypothetical_fills"], [])
        self.assertEqual(report["equity_curve"], [])
        self.assertIsNone(report["open_position"])
        self.assertEqual(report["final_cash"], tl.STARTING_CASH)

    def test_valid_strategy_identity_changes_invalid_pack_run_identity(self):
        invalid_pack = pack()
        del invalid_pack["pack_id"]
        first = tl.run_backtest(strategy(paper_size_pct=5.0), invalid_pack)
        second = tl.run_backtest(strategy(paper_size_pct=4.0), invalid_pack)
        self.assertEqual(first["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(second["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertNotEqual(first["metadata"]["configuration_hash"],
                            second["metadata"]["configuration_hash"])
        self.assertNotEqual(first["metadata"]["run_id"],
                            second["metadata"]["run_id"])

    def test_missing_unknown_and_nonfinite_strategy_values_fail_closed(self):
        missing = strategy()
        del missing["family"]
        unknown = strategy(strategy_id="UNKNOWN-001")
        unsupported = strategy(extra_parameter=1)
        nonfinite = strategy(paper_size_pct=float("nan"))
        boolean = strategy(paper_size_pct=True)
        for rule in (missing, unknown, unsupported, nonfinite, boolean):
            with self.subTest(rule=rule):
                report = run(rule=rule)
                self.assertEqual(
                    report["reason_code"], tl.BLOCKED_INVALID_STRATEGY_PARAMETERS,
                )
                self.assertIsInstance(tl.canonical_json(report), str)
                assert_no_nonfinite_float(self, report)

    def test_extreme_strategy_and_risk_numerics_are_safely_blocked(self):
        strategy_report = run(rule=strategy(paper_size_pct=10 ** 400))
        self.assertEqual(strategy_report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(
            strategy_report["reason_code"],
            tl.BLOCKED_INVALID_STRATEGY_PARAMETERS,
        )
        risk_report = run(risk_policy={"max_position_pct": 10 ** 400})
        self.assertEqual(risk_report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(
            risk_report["reason_code"], tl.BLOCKED_RISK_OVERRIDE_ATTEMPT,
        )
        for report in (strategy_report, risk_report):
            self.assertIsInstance(tl.canonical_json(report), str)
            assert_no_nonfinite_float(self, report)

    def test_oversized_strategy_integer_has_stable_bounded_configuration_hash(self):
        huge = 10 ** 5000
        first = run(rule=strategy(paper_size_pct=huge))
        second = run(rule=strategy(paper_size_pct=huge))
        different = run(rule=strategy(paper_size_pct=huge + 1))
        for report in (first, second, different):
            self.assertEqual(report["reason_code"],
                             tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)
            self.assertLess(len(json.dumps(report, allow_nan=False)), 10000)
        self.assertEqual(first["metadata"]["configuration_hash"],
                         second["metadata"]["configuration_hash"])
        self.assertEqual(first["metadata"]["run_id"],
                         second["metadata"]["run_id"])
        self.assertNotEqual(first["metadata"]["configuration_hash"],
                            different["metadata"]["configuration_hash"])
        self.assertNotEqual(first["metadata"]["run_id"],
                            different["metadata"]["run_id"])
        for field in ("fast", "slow"):
            report = run(rule=strategy(**{field: huge}))
            self.assertEqual(report["reason_code"],
                             tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)
            self.assertTrue(any("supported integer range" in error
                                for error in report["validation"]["errors"]))

    def test_strategy_and_risk_policy_mapping_subclasses_are_explicitly_rejected(self):
        strategy_report = run(rule=DictSubclass(strategy(paper_size_pct=4.0)))
        risk_report = run(risk_policy=DictSubclass({"max_position_pct": 4.0}))
        self.assertEqual(strategy_report["reason_code"],
                         tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)
        self.assertEqual(risk_report["reason_code"],
                         tl.BLOCKED_RISK_OVERRIDE_ATTEMPT)
        self.assertIn("exact built-in dictionary",
                      strategy_report["validation"]["errors"][0])
        self.assertIn("exact built-in dictionary",
                      risk_report["validation"]["errors"][0])

    def test_system_position_maximum_cannot_be_raised(self):
        report = run(risk_policy={"max_position_pct": 100.0})
        self.assertEqual(report["reason_code"], tl.BLOCKED_RISK_OVERRIDE_ATTEMPT)
        oversized = run(rule=strategy(paper_size_pct=5.000001))
        self.assertEqual(oversized["reason_code"], tl.BLOCKED_POSITION_LIMIT)

    def test_smaller_strategy_request_is_allowed(self):
        report = run([3, 2, 1, 4, 5], rule=strategy(paper_size_pct=2.0))
        self.assertEqual(report["validation"]["outcome"], "VALID")
        self.assertAlmostEqual(report["hypothetical_fills"][0]["filled_notional"], 2.0)

    def test_drawdown_halt_is_mark_to_market_and_causal(self):
        report = run(
            [3, 2, 1, 4, 0.1, 0.1],
            [3, 2, 1, 4, 100, 0.1],
            rule=strategy(drawdown_halt_pct=-1.0),
        )
        self.assertTrue(report["halted"])
        self.assertEqual(report["reason_code"], tl.BLOCKED_DRAWDOWN_HALT)
        self.assertEqual(len(report["hypothetical_fills"]), 1)
        self.assertIsNotNone(report["open_position"])
        self.assertEqual(report["realized_pnl"], 0.0)

    def test_system_drawdown_limit_cannot_be_weakened(self):
        report = run(risk_policy={"drawdown_halt_pct": -20.0})
        self.assertEqual(report["reason_code"], tl.BLOCKED_RISK_OVERRIDE_ATTEMPT)

    def test_system_minus_fifteen_drawdown_halts_without_same_bar_exit(self):
        closes = [3, 2, 1]
        opens = [3, 2, 1]
        for _ in range(4):
            closes += [4, 1, 0.01, 0.01]
            opens += [4, 100, 0.01, 0.01]
        report = run(closes, opens)
        halt_event = next(event for event in report["events"]
                          if event["outcome"] == tl.OUTCOME_HALT)
        self.assertEqual(halt_event["timestamp"], "2026-01-17")
        self.assertLessEqual(halt_event["context"]["drawdown_pct"], -15.0)
        sells_after_halt = [fill for fill in report["hypothetical_fills"]
                            if fill["side"] == "SELL"
                            and fill["fill_timestamp"] > halt_event["timestamp"]]
        self.assertEqual(len(sells_after_halt), 1)
        self.assertEqual(sells_after_halt[0]["fill_timestamp"], "2026-01-19")

    def test_end_to_end_martingale_increase_is_blocked(self):
        market_pack = pack([3, 2, 1, 4, 5])
        rule = strategy(paper_size_pct=5.0)
        policy, errors = tl._effective_policy(None, rule)
        self.assertEqual(errors, [])
        strategy_hash = tl.canonical_sha256(rule)
        metadata = tl._metadata(
            market_pack, rule, tl.canonical_sha256(market_pack), strategy_hash, policy,
        )
        report = tl._run_validated(
            rule, market_pack, policy, metadata,
            initial_last_loss_size_pct={"X": 4.0},
        )
        self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(report["reason_code"], tl.BLOCKED_INCREASE_TO_LOSER)
        self.assertEqual(report["hypothetical_fills"], [])

    def test_no_cross_is_explicit_no_trade(self):
        report = run([100, 100, 100, 100, 100])
        self.assertEqual(report["outcome"], tl.OUTCOME_NO_TRADE)
        self.assertEqual(report["reason_code"], tl.NO_TRADE_NO_CROSS)

    def test_exit_signal_while_flat_is_explicit(self):
        report = run([1, 2, 3, 1, 0.5])
        self.assertIn(tl.NO_TRADE_NO_OPEN_POSITION, report["reason_codes"])


class CanonicalHashSafetyTests(unittest.TestCase):
    def assert_blocked_without_evaluation(self, report, reason_code):
        self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(report["reason_code"], reason_code)
        self.assertEqual(report["validation"]["outcome"], "INVALID")
        self.assertEqual(report["hypothetical_fills"], [])
        self.assertEqual(report["trade_list"], [])
        self.assertEqual(report["equity_curve"], [])
        self.assertIsNone(report["open_position"])
        self.assertEqual(report["final_cash"], tl.STARTING_CASH)
        self.assertEqual(report["final_equity"], tl.STARTING_CASH)
        json.dumps(report, allow_nan=False)
        assert_no_nonfinite_float(self, report)

    def test_self_referential_pack_is_stable_and_blocked(self):
        first_pack = {}
        first_pack["self"] = first_pack
        second_pack = {}
        second_pack["self"] = second_pack
        with mock.patch.object(
                tl, "_run_validated",
                side_effect=AssertionError("financial evaluation must not run")):
            first = tl.run_backtest(strategy(), first_pack)
            second = tl.run_backtest(strategy(), second_pack)
        for report in (first, second):
            self.assert_blocked_without_evaluation(
                report, tl.BLOCKED_INVALID_INPUT,
            )
        self.assertEqual(first["metadata"]["input_data_hash"],
                         second["metadata"]["input_data_hash"])
        self.assertEqual(first["metadata"]["run_id"],
                         second["metadata"]["run_id"])
        canonical = tl.canonical_json(first_pack)
        self.assertIn("active_container_cycle", canonical)
        self.assertNotIn("0x", canonical.lower())

    def test_self_referential_strategy_list_is_stable_and_blocked(self):
        first_rule = []
        first_rule.append(first_rule)
        second_rule = []
        second_rule.append(second_rule)
        with mock.patch.object(
                tl, "_run_validated",
                side_effect=AssertionError("financial evaluation must not run")):
            first = tl.run_backtest(first_rule, pack())
            second = tl.run_backtest(second_rule, pack())
        for report in (first, second):
            self.assert_blocked_without_evaluation(
                report, tl.BLOCKED_INVALID_STRATEGY_PARAMETERS,
            )
        self.assertEqual(first["metadata"]["configuration_hash"],
                         second["metadata"]["configuration_hash"])
        self.assertEqual(first["metadata"]["run_id"],
                         second["metadata"]["run_id"])

    def test_nested_and_mutually_cyclic_lists_are_blocked(self):
        self_nested = []
        self_nested.append(self_nested)
        mutual_list = []
        mutual_dict = {"back": mutual_list}
        mutual_list.append(mutual_dict)
        for label, malformed in (
                ("self-nested", self_nested), ("mutual", mutual_list)):
            with self.subTest(label=label):
                market_pack = pack()
                market_pack["note"] = malformed
                with mock.patch.object(
                        tl, "_run_validated",
                        side_effect=AssertionError(
                            "financial evaluation must not run")):
                    report = tl.run_backtest(strategy(), market_pack)
                self.assert_blocked_without_evaluation(
                    report, tl.BLOCKED_INVALID_INPUT,
                )
                self.assertIn("active_container_cycle",
                              tl.canonical_json(market_pack))

    def test_excessively_deep_nesting_is_stably_blocked(self):
        def deeply_nested():
            value = "leaf"
            for _index in range(tl._MAX_CANONICAL_DEPTH + 20):
                value = [value]
            return value

        first_pack = pack()
        first_pack["note"] = deeply_nested()
        second_pack = pack()
        second_pack["note"] = deeply_nested()
        first = tl.run_backtest(strategy(), first_pack)
        second = tl.run_backtest(strategy(), second_pack)
        for report in (first, second):
            self.assert_blocked_without_evaluation(
                report, tl.BLOCKED_INVALID_INPUT,
            )
        self.assertEqual(first["metadata"]["input_data_hash"],
                         second["metadata"]["input_data_hash"])
        self.assertEqual(first["metadata"]["run_id"],
                         second["metadata"]["run_id"])
        self.assertIn("maximum_depth_exceeded",
                      tl.canonical_json(first_pack))

    def test_lone_high_and_low_surrogates_fail_closed(self):
        for label, malformed in (("high", "\ud800"), ("low", "\udfff")):
            with self.subTest(label=label):
                first_pack = pack()
                first_pack["note"] = malformed
                second_pack = copy.deepcopy(first_pack)
                first = tl.run_backtest(strategy(), first_pack)
                second = tl.run_backtest(strategy(), second_pack)
                for report in (first, second):
                    self.assert_blocked_without_evaluation(
                        report, tl.BLOCKED_INVALID_INPUT,
                    )
                self.assertEqual(first["metadata"]["input_data_hash"],
                                 second["metadata"]["input_data_hash"])
                self.assertEqual(first["metadata"]["run_id"],
                                 second["metadata"]["run_id"])
                canonical = tl.canonical_json(first_pack)
                canonical.encode("utf-8", "strict")
                self.assertIn("__unicode_codepoints__", canonical)

    def test_valid_arabic_text_remains_deterministic(self):
        first_pack = pack()
        first_pack["note"] = "بيانات عربية صالحة"
        second_pack = copy.deepcopy(first_pack)
        first = tl.run_backtest(strategy(), first_pack)
        second = tl.run_backtest(strategy(), second_pack)
        self.assertEqual(first, second)
        self.assertEqual(first["validation"]["outcome"], "VALID")
        self.assertEqual(tl.canonical_sha256(first_pack),
                         tl.canonical_sha256(second_pack))
        self.assertIn("بيانات عربية صالحة", tl.canonical_json(first_pack))

    def test_streaming_hash_matches_trusted_canonical_json_reference(self):
        value = {
            "arabic": "بيانات عربية صالحة",
            "bars": [
                {"close": 100.25, "date": "2026-01-01", "volume": 1000},
                {"close": 101.5, "date": "2026-01-02", "volume": 1001},
            ],
            "pack_id": "SMALL-REFERENCE",
        }
        reference = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        )
        expected = hashlib.sha256(reference.encode("utf-8", "strict")).hexdigest()
        self.assertEqual(tl._streaming_canonical_sha256(value), expected)
        self.assertEqual(tl._streaming_canonical_sha256(copy.deepcopy(value)),
                         expected)

    def test_large_valid_pack_hashes_all_bars_deterministically(self):
        bar_count = 20000
        market_pack = pack()
        start = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
        bars = []
        for index in range(bar_count):
            bars.append({
                "date": (start + datetime.timedelta(minutes=index)).isoformat(),
                "open": 100.0,
                "high": 101.0,
                "low": 99.0,
                "close": 100.0,
                "volume": 1000 + index,
            })
        market_pack["instruments"][0]["ohlcv"] = bars
        market_pack["as_of"] = bars[-1]["date"]
        rule = strategy(fast=1, slow=2)

        canonical_reference = json.dumps(
            market_pack, sort_keys=True, separators=(",", ":"),
            ensure_ascii=False, allow_nan=False,
        )
        expected_hash = hashlib.sha256(
            canonical_reference.encode("utf-8", "strict")
        ).hexdigest()
        first = tl.run_backtest(rule, market_pack)
        self.assertEqual(first["validation"]["outcome"], "VALID")
        self.assertNotIn("maximum_nodes_exceeded",
                         " ".join(first["validation"]["errors"]))
        self.assertEqual(first["metadata"]["input_data_hash"], expected_hash)
        self.assertTrue(first["metadata"]["paper_research_only"])
        self.assertEqual(first["hypothetical_fills"], [])
        assert_no_nonfinite_float(self, first)
        first_hash = first["metadata"]["input_data_hash"]
        first_run_id = first["metadata"]["run_id"]
        del first

        repeated = tl.run_backtest(copy.deepcopy(rule), market_pack)
        self.assertEqual(repeated["validation"]["outcome"], "VALID")
        self.assertEqual(repeated["metadata"]["input_data_hash"], first_hash)
        self.assertEqual(repeated["metadata"]["run_id"], first_run_id)
        del repeated

        changed_pack = copy.deepcopy(market_pack)
        changed_pack["instruments"][0]["ohlcv"][bar_count // 2]["volume"] += 1
        changed = tl.run_backtest(rule, changed_pack)
        self.assertEqual(changed["validation"]["outcome"], "VALID")
        self.assertNotEqual(changed["metadata"]["input_data_hash"], first_hash)
        self.assertNotEqual(changed["metadata"]["run_id"], first_run_id)
        assert_no_nonfinite_float(self, changed)

    def test_malformed_wide_pack_uses_bounded_fail_closed_hashing(self):
        first_pack = pack()
        first_pack["note"] = [0] * (tl._MAX_CANONICAL_NODES + 100)
        second_pack = copy.deepcopy(first_pack)
        with mock.patch.object(
                tl, "_run_validated",
                side_effect=AssertionError("financial evaluation must not run")):
            first = tl.run_backtest(strategy(), first_pack)
            second = tl.run_backtest(strategy(), second_pack)
        for report in (first, second):
            self.assert_blocked_without_evaluation(
                report, tl.BLOCKED_INVALID_INPUT,
            )
            self.assertTrue(any(
                "maximum_nodes_exceeded" in error
                for error in report["validation"]["errors"]
            ))
        self.assertEqual(first["metadata"]["input_data_hash"],
                         second["metadata"]["input_data_hash"])
        self.assertEqual(first["metadata"]["run_id"],
                         second["metadata"]["run_id"])

        material, issues = tl._safe_for_hash_details(first_pack)
        marker = material["__canonicalization_issue__"]
        self.assertEqual(marker["kind"], "maximum_nodes_exceeded")
        self.assertEqual(marker["visited_nodes"], tl._MAX_CANONICAL_NODES)
        self.assertRegex(marker["traversed_prefix_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(any("maximum_nodes_exceeded" in issue
                            for issue in issues))

    def test_bounded_fingerprint_distinguishes_pack_id_before_cutoff(self):
        def malformed(pack_id):
            market_pack = pack()
            market_pack["pack_id"] = pack_id
            market_pack["wide_payload"] = [0] * (
                tl._MAX_CANONICAL_NODES + 10
            )
            return market_pack

        first_pack = malformed("PREFIX-PACK-A")
        repeated_pack = malformed("PREFIX-PACK-A")
        different_pack = malformed("PREFIX-PACK-B")
        first = tl.run_backtest(strategy(), first_pack)
        repeated = tl.run_backtest(strategy(), repeated_pack)
        different = tl.run_backtest(strategy(), different_pack)
        for report in (first, repeated, different):
            self.assert_blocked_without_evaluation(
                report, tl.BLOCKED_INVALID_INPUT,
            )
            self.assertTrue(any(
                "maximum_nodes_exceeded" in error
                for error in report["validation"]["errors"]
            ))
        self.assertEqual(first["metadata"]["input_data_hash"],
                         repeated["metadata"]["input_data_hash"])
        self.assertEqual(first["metadata"]["run_id"],
                         repeated["metadata"]["run_id"])
        self.assertNotEqual(first["metadata"]["input_data_hash"],
                            different["metadata"]["input_data_hash"])
        self.assertNotEqual(first["metadata"]["run_id"],
                            different["metadata"]["run_id"])

    def test_bounded_fingerprint_tracks_scalar_and_list_prefix_content(self):
        def malformed():
            market_pack = pack()
            market_pack["wide_payload"] = [0] * (
                tl._MAX_CANONICAL_NODES + 10
            )
            return market_pack

        baseline_pack = malformed()
        scalar_changed_pack = malformed()
        scalar_changed_pack["prepared_by"] = "different safe prefix scalar"
        list_changed_pack = malformed()
        list_changed_pack["wide_payload"][7] = 1
        baseline = tl.run_backtest(strategy(), baseline_pack)
        scalar_changed = tl.run_backtest(strategy(), scalar_changed_pack)
        list_changed = tl.run_backtest(strategy(), list_changed_pack)
        for report in (baseline, scalar_changed, list_changed):
            self.assert_blocked_without_evaluation(
                report, tl.BLOCKED_INVALID_INPUT,
            )
        baseline_hash = baseline["metadata"]["input_data_hash"]
        baseline_run = baseline["metadata"]["run_id"]
        self.assertNotEqual(
            scalar_changed["metadata"]["input_data_hash"], baseline_hash,
        )
        self.assertNotEqual(scalar_changed["metadata"]["run_id"], baseline_run)
        self.assertNotEqual(
            list_changed["metadata"]["input_data_hash"], baseline_hash,
        )
        self.assertNotEqual(list_changed["metadata"]["run_id"], baseline_run)

    def test_ordinary_valid_hashes_remain_content_sensitive(self):
        first_pack = pack([3, 2, 1, 4, 5])
        second_pack = pack([3, 2, 1, 4, 6])
        self.assertNotEqual(tl.canonical_sha256(first_pack),
                            tl.canonical_sha256(second_pack))
        first = tl.run_backtest(strategy(), first_pack)
        second = tl.run_backtest(strategy(), second_pack)
        self.assertNotEqual(first["metadata"]["input_data_hash"],
                            second["metadata"]["input_data_hash"])


class FacadeImportCompatibilityTests(unittest.TestCase):
    def demo_inputs(self, module):
        path = os.path.join(BASE, "sample_data", "TRL-PACK-DEMO.json")
        with open(path, encoding="utf-8") as handle:
            market_pack = json.load(handle)
        rule = {
            "strategy_id": module.STRATEGY_ID,
            "strategy_version": module.STRATEGY_VERSION,
            "family": module.STRATEGY_FAMILY,
            "symbol": "DEMO-EQ-A",
            "fast": 5,
            "slow": 20,
            "paper_size_pct": 5.0,
        }
        return rule, market_pack

    @contextlib.contextmanager
    def outside_lab_import_context(self, cached_core=None):
        with preserved_process_state():
            original_cwd = os.getcwd()
            base_identity = os.path.normcase(os.path.realpath(BASE))
            sys.path[:] = [
                entry for entry in sys.path
                if os.path.normcase(os.path.realpath(
                    entry if entry else original_cwd
                )) != base_identity
            ]
            for name in tuple(sys.modules):
                if (name == "trading_lab_core"
                        or name.startswith("trading_lab_core.")):
                    del sys.modules[name]
            if cached_core is not None:
                sys.modules["trading_lab_core"] = cached_core
            os.chdir(REPOSITORY_ROOT)
            self.assertTrue(all(
                os.path.normcase(os.path.realpath(
                    entry if entry else os.getcwd()
                )) != base_identity
                for entry in sys.path
            ))
            self.assertNotEqual(
                os.path.normcase(os.path.realpath(os.getcwd())),
                base_identity,
            )
            yield

    @contextlib.contextmanager
    def package_import_context(self):
        with preserved_process_state():
            sys.path.insert(0, REPOSITORY_ROOT)
            yield importlib.import_module(PACKAGE_MODULE_NAME)

    def assert_sibling_core_modules(self, module):
        expected = os.path.normcase(os.path.realpath(
            os.path.join(BASE, "trading_lab_core")
        ))
        for name in (
            "_canonical", "_constants", "_execution", "_reporting",
            "_risk", "_strategy", "_validation",
        ):
            imported = (module[name] if isinstance(module, dict)
                        else getattr(module, name))
            actual = os.path.normcase(os.path.realpath(
                os.path.dirname(imported.__file__)
            ))
            self.assertEqual(actual, expected, name)

    def test_absolute_file_spec_load_is_cwd_independent_and_restores_path(self):
        facade_path = os.path.join(BASE, "trading_lab.py")
        repository_before = repository_file_state()
        with self.outside_lab_import_context():
            path_before = list(sys.path)
            self.assertNotIn("trading_lab_core", sys.modules)
            spec = importlib.util.spec_from_file_location(
                "trading_lab_file_compatibility", facade_path,
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertEqual(sys.path, path_before)
            self.assertEqual(module.__package__, "")
            for name in EXPECTED_FACADE_CALLABLES:
                self.assertTrue(callable(getattr(module, name)), name)
            self.assert_sibling_core_modules(module)

            rule, market_pack = self.demo_inputs(module)
            original_rule = copy.deepcopy(rule)
            original_pack = copy.deepcopy(market_pack)
            first = module.run_backtest(rule, market_pack)
            repeated = module.run_backtest(
                copy.deepcopy(rule), copy.deepcopy(market_pack),
            )
            top_rule, top_pack = self.demo_inputs(tl)
            top_level = tl.run_backtest(top_rule, top_pack)
            self.assertEqual(first, repeated)
            self.assertEqual(rule, original_rule)
            self.assertEqual(market_pack, original_pack)
            self.assertEqual(
                without_provenance(first), without_provenance(top_level),
            )
            self.assertEqual(
                (first["outcome"], first["reason_code"]),
                (module.OUTCOME_FILL, module.OPEN_TERMINAL_POSITION),
            )
        self.assertEqual(repository_file_state(), repository_before)

    def test_synthetic_dotted_file_spec_uses_complete_sibling_facade(self):
        facade_path = os.path.join(BASE, "trading_lab.py")
        repository_before = repository_file_state()
        cwd_before = os.getcwd()
        path_before = list(sys.path)
        modules_before = dict(sys.modules)
        argv_before = sys.argv
        argv_values_before = list(sys.argv)
        with self.outside_lab_import_context():
            execution_cwd = os.getcwd()
            execution_path = list(sys.path)
            execution_argv = sys.argv
            execution_argv_values = list(sys.argv)
            self.assertNotIn("plugins", sys.modules)
            spec = importlib.util.spec_from_file_location(
                "plugins.trading_lab", facade_path,
            )
            self.assertIsNotNone(spec)
            self.assertIsNotNone(spec.loader)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            self.assertEqual(module.__package__, "plugins")
            self.assertFalse(module._use_package_relative_imports)
            self.assertEqual(os.getcwd(), execution_cwd)
            self.assertEqual(sys.path, execution_path)
            self.assertIs(sys.argv, execution_argv)
            self.assertEqual(sys.argv, execution_argv_values)
            for name in EXPECTED_FACADE_CALLABLES:
                self.assertTrue(callable(getattr(module, name)), name)
            self.assert_sibling_core_modules(module)

            rule, market_pack = self.demo_inputs(module)
            result = module.run_backtest(rule, market_pack)
            top_rule, top_pack = self.demo_inputs(tl)
            top_level = tl.run_backtest(top_rule, top_pack)
            self.assertEqual(
                without_provenance(result), without_provenance(top_level),
            )
            self.assertEqual(
                (result["outcome"], result["reason_code"]),
                (module.OUTCOME_FILL, module.OPEN_TERMINAL_POSITION),
            )

        self.assertEqual(os.getcwd(), cwd_before)
        self.assertEqual(sys.path, path_before)
        self.assertIs(sys.argv, argv_before)
        self.assertEqual(sys.argv, argv_values_before)
        self.assertEqual(set(sys.modules), set(modules_before))
        for name, imported in modules_before.items():
            self.assertIs(sys.modules[name], imported, name)
        self.assertEqual(repository_file_state(), repository_before)

    def test_synthetic_dotted_spec_does_not_use_unrelated_parent_core(self):
        facade_path = os.path.join(BASE, "trading_lab.py")
        unrelated_parent = types.ModuleType("plugins")
        unrelated_parent.__path__ = [REPOSITORY_ROOT]
        unrelated_core = types.ModuleType("plugins.trading_lab_core")
        unrelated_core.__file__ = os.path.join(REPOSITORY_ROOT, ".gitignore")
        unrelated_core.__path__ = []
        with self.outside_lab_import_context():
            sys.modules["plugins"] = unrelated_parent
            sys.modules["plugins.trading_lab_core"] = unrelated_core
            spec = importlib.util.spec_from_file_location(
                "plugins.trading_lab", facade_path,
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.assertFalse(module._use_package_relative_imports)
            self.assertIsNot(module._canonical, unrelated_core)
            self.assert_sibling_core_modules(module)

    def test_absolute_run_path_is_cwd_independent_and_restores_path(self):
        facade_path = os.path.join(BASE, "trading_lab.py")
        repository_before = repository_file_state()
        with self.outside_lab_import_context():
            path_before = list(sys.path)
            self.assertNotIn("trading_lab_core", sys.modules)
            namespace = runpy.run_path(facade_path)
            self.assertEqual(sys.path, path_before)
            for name in EXPECTED_FACADE_CALLABLES:
                self.assertTrue(callable(namespace[name]), name)
            self.assert_sibling_core_modules(namespace)
        self.assertEqual(repository_file_state(), repository_before)

    def test_file_loading_rejects_unrelated_cached_core_package(self):
        facade_path = os.path.join(BASE, "trading_lab.py")
        repository_before = repository_file_state()
        unrelated = types.ModuleType("trading_lab_core")
        unrelated.__file__ = os.path.join(REPOSITORY_ROOT, ".gitignore")
        unrelated.__path__ = []
        with self.outside_lab_import_context(cached_core=unrelated):
            path_before = list(sys.path)
            self.assertIs(sys.modules["trading_lab_core"], unrelated)
            spec = importlib.util.spec_from_file_location(
                "trading_lab_unrelated_core", facade_path,
            )
            module = importlib.util.module_from_spec(spec)
            with self.assertRaisesRegex(
                ImportError, "did not resolve from the facade sibling",
            ):
                spec.loader.exec_module(module)
            self.assertEqual(sys.path, path_before)
        self.assertEqual(repository_file_state(), repository_before)

    def test_historical_top_level_import_remains_operational(self):
        imported = importlib.import_module("trading_lab")
        self.assertIs(imported, tl)
        self.assertEqual(imported.__name__, "trading_lab")
        self.assertEqual(imported.__package__, "")
        for name in EXPECTED_FACADE_CALLABLES:
            self.assertTrue(callable(getattr(imported, name)), name)

    def test_repository_root_package_qualified_import_succeeds(self):
        with self.package_import_context() as module:
            self.assertEqual(module.__name__, PACKAGE_MODULE_NAME)
            self.assertEqual(
                module.__package__, "09_AI_Systems.02_Tools.Trading_Lab",
            )

    def test_package_qualified_module_exposes_public_facade_callables(self):
        with self.package_import_context() as module:
            for name in EXPECTED_FACADE_CALLABLES:
                self.assertTrue(callable(getattr(module, name)), name)
            self.assertEqual(module.run_backtest.__module__, PACKAGE_MODULE_NAME)
            self.assertEqual(
                module.sma_cross_signals.__module__, PACKAGE_MODULE_NAME,
            )

    def test_package_demo_preserves_semantics_hashes_and_inputs(self):
        with self.package_import_context() as module:
            rule, market_pack = self.demo_inputs(module)
            original_rule = copy.deepcopy(rule)
            original_pack = copy.deepcopy(market_pack)
            first = module.run_backtest(rule, market_pack)
            repeated = module.run_backtest(
                copy.deepcopy(rule), copy.deepcopy(market_pack),
            )
            top_rule, top_pack = self.demo_inputs(tl)
            top_level = tl.run_backtest(top_rule, top_pack)

            self.assertEqual(first, repeated)
            self.assertEqual(rule, original_rule)
            self.assertEqual(market_pack, original_pack)
            self.assertEqual(
                without_provenance(first), without_provenance(top_level),
            )
            self.assertEqual(
                first["metadata"]["input_data_hash"],
                "6cdbca208cd1029b90e5ed3494ab05a3b7042d224ed01293373fc173a85aee56",
            )
            self.assertEqual(
                first["metadata"]["configuration_hash"],
                "3f4c513f275ca034af9fd2f4bbcb4ec382c361969d7706fbb6fb6d26fd26bbbd",
            )
            self.assertEqual(
                first["metadata"]["strategy_definition_hash"],
                "e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955",
            )
            semantic_digest = hashlib.sha256(
                module.canonical_json(without_provenance(first)).encode("utf-8")
            ).hexdigest()
            self.assertEqual(
                semantic_digest,
                "6f66351873fb49dc11fcc7f3c0e3c84d0add65b4e0b315bf78da7008070d5331",
            )
            self.assertTrue(first["metadata"]["paper_research_only"])
            self.assertIn("NO LIVE TRADING", first["disclaimer"])
            self.assertEqual(
                (first["outcome"], first["reason_code"]),
                (module.OUTCOME_FILL, module.OPEN_TERMINAL_POSITION),
            )

    def test_package_module_execution_succeeds_without_artifacts(self):
        before = repository_file_state()
        environment = os.environ.copy()
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, "-B", "-m", PACKAGE_MODULE_NAME],
            cwd=REPOSITORY_ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
        after = repository_file_state()
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout, "")
        self.assertEqual(completed.stderr, "")
        self.assertEqual(after, before)


class DeterminismReportingAndBoundaryTests(unittest.TestCase):
    def engine_sources(self):
        sources = {}
        for relative_path in tl._engine_source_manifest():
            absolute_path = os.path.join(
                REPOSITORY_ROOT, *relative_path.split("/"),
            )
            with open(absolute_path, "rb") as source_handle:
                sources[relative_path] = source_handle.read()
        return sources

    def test_engine_source_digest_matches_independent_normalized_source(self):
        report = run([3, 2, 1, 4, 5])
        engine = report["metadata"]["engine"]
        expected = independent_engine_bundle_digest(self.engine_sources())
        digest = engine["engine_source_digest"]
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        self.assertEqual(digest, expected)
        self.assertEqual(report["metadata"]["engine_source_digest"], expected)
        self.assertEqual(engine["engine_source_manifest"],
                         report["metadata"]["engine_source_manifest"])
        self.assertEqual(engine["digest_algorithm"], "SHA-256")
        self.assertEqual(engine["source_normalization"],
                         "UTF-8; CRLF_AND_CR_TO_LF")
        self.assertEqual(engine["checkpoint_id"], tl.CHECKPOINT_ID)
        self.assertEqual(engine["committed_base_revision"], "05f7ba9")
        self.assertNotIn("source_revision", engine)

    def test_atomic_snapshot_enumerates_once_for_digest_and_manifest(self):
        source_paths = [
            ("engine/a.py", "memory-a"),
            ("engine/b.py", "memory-b"),
        ]
        source_bytes = {
            "memory-a": b"first\r\nline\r",
            "memory-b": b"second\nline\n",
        }

        def in_memory_open(path, mode):
            self.assertEqual(mode, "rb")
            return io.BytesIO(source_bytes[path])

        with mock.patch.object(
            tl._canonical, "_engine_source_paths", return_value=source_paths,
        ) as enumerate_paths, mock.patch(
            "builtins.open", side_effect=in_memory_open,
        ) as source_open:
            digest, manifest = tl._engine_source_snapshot()

        enumerate_paths.assert_called_once_with()
        self.assertEqual(source_open.call_count, 2)
        self.assertEqual(manifest, ["engine/a.py", "engine/b.py"])
        self.assertEqual(
            digest,
            independent_engine_bundle_digest({
                relative_path: source_bytes[absolute_path]
                for relative_path, absolute_path in source_paths
            }),
        )

    def test_in_memory_bundle_returns_expected_paired_provenance(self):
        sources = {
            "z/module.py": b"zeta\r\n",
            "a/module.py": b"alpha\r",
        }
        digest, manifest = tl._engine_source_snapshot(sources)
        self.assertEqual(manifest, sorted(sources))
        self.assertEqual(digest, independent_engine_bundle_digest(sources))
        self.assertEqual(tl._engine_source_bundle_digest(sources), digest)

    def test_successive_runs_keep_each_captured_source_pair_atomic(self):
        initial_sources = {"engine/a.py": b"alpha\n"}
        changed_sources = {
            "engine/a.py": b"alpha changed\n",
            "engine/b.py": b"added\n",
        }
        snapshots = [
            tl._canonical._engine_source_snapshot(initial_sources),
            tl._canonical._engine_source_snapshot(changed_sources),
        ]
        with mock.patch.object(
            tl, "_engine_source_snapshot", side_effect=snapshots,
        ) as capture:
            first = run([3, 2, 1, 4, 5])
            second = run([3, 2, 1, 4, 5])

        self.assertEqual(capture.call_count, 2)
        self.assertEqual(
            first["metadata"]["engine_source_digest"], snapshots[0][0],
        )
        self.assertEqual(
            first["metadata"]["engine_source_manifest"], snapshots[0][1],
        )
        self.assertEqual(
            second["metadata"]["engine_source_digest"], snapshots[1][0],
        )
        self.assertEqual(
            second["metadata"]["engine_source_manifest"], snapshots[1][1],
        )
        self.assertNotEqual(snapshots[0], snapshots[1])

    def test_enumeration_failure_blocks_without_second_enumeration(self):
        with mock.patch.object(
            tl._canonical,
            "_engine_source_paths",
            side_effect=tl.ReproducibilityError("simulated enumeration failure"),
        ) as enumerate_paths:
            report = run([3, 2, 1, 4, 5])

        enumerate_paths.assert_called_once_with()
        self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(
            report["reason_code"], tl.BLOCKED_REPRODUCIBILITY_ERROR,
        )
        self.assertIsNone(report["metadata"]["engine_source_digest"])
        self.assertIsNone(report["metadata"]["engine_source_manifest"])
        self.assertIsNone(
            report["metadata"]["engine"]["engine_source_manifest"],
        )
        self.assertEqual(
            report["metadata"]["reproducibility_status"], "FAILED_CLOSED",
        )

    def test_source_read_failure_is_caught_without_reenumeration(self):
        paths = [("engine/unreadable.py", "unreadable-source")]
        with mock.patch.object(
            tl._canonical, "_engine_source_paths", return_value=paths,
        ) as enumerate_paths, mock.patch(
            "builtins.open", side_effect=OSError("simulated read failure"),
        ) as source_open:
            report = run([3, 2, 1, 4, 5])

        enumerate_paths.assert_called_once_with()
        source_open.assert_called_once_with("unreadable-source", "rb")
        self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(
            report["reason_code"], tl.BLOCKED_REPRODUCIBILITY_ERROR,
        )
        self.assertIsNone(report["metadata"]["engine_source_digest"])
        self.assertIsNone(report["metadata"]["engine_source_manifest"])

    def test_metadata_never_reenumerates_after_run_snapshot(self):
        original_paths = tl._canonical._engine_source_paths
        invalid_pack = pack([3, 2, 1, 4, 5])
        del invalid_pack["pack_id"]
        for market_pack in (pack([3, 2, 1, 4, 5]), invalid_pack):
            with self.subTest(valid=market_pack is not invalid_pack):
                with mock.patch.object(
                    tl._canonical, "_engine_source_paths", wraps=original_paths,
                ) as enumerate_paths:
                    tl.run_backtest(strategy(), market_pack)
                enumerate_paths.assert_called_once_with()

    def test_valid_and_invalid_results_receive_the_captured_source_pair(self):
        captured = ("7" * 64, ["memory/captured.py"])
        invalid_pack = pack([3, 2, 1, 4, 5])
        del invalid_pack["pack_id"]
        with mock.patch.object(
            tl, "_engine_source_snapshot", return_value=captured,
        ) as snapshot:
            valid = tl.run_backtest(strategy(), pack([3, 2, 1, 4, 5]))
            invalid = tl.run_backtest(strategy(), invalid_pack)

        self.assertEqual(snapshot.call_count, 2)
        for report in (valid, invalid):
            self.assertEqual(
                report["metadata"]["engine_source_digest"], captured[0],
            )
            self.assertEqual(
                report["metadata"]["engine_source_manifest"], captured[1],
            )
            self.assertEqual(
                report["metadata"]["engine"]["engine_source_manifest"],
                captured[1],
            )

    def test_engine_manifest_is_complete_sorted_and_repository_relative(self):
        manifest = tl._engine_source_manifest()
        expected = [
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab.py",
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/__init__.py",
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/canonical.py",
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/constants.py",
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/execution.py",
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/reporting.py",
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/risk.py",
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/strategy.py",
            "09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/validation.py",
        ]
        self.assertEqual(manifest, sorted(manifest))
        self.assertEqual(manifest, expected)
        self.assertTrue(all("\\" not in path for path in manifest))

    def test_each_engine_module_changes_bundle_digest_and_run_id(self):
        sources = self.engine_sources()
        baseline_digest = tl._engine_source_bundle_digest(sources)
        baseline = run([3, 2, 1, 4, 5])
        market_pack = pack([3, 2, 1, 4, 5])
        rule = strategy()
        policy, errors = tl._effective_policy(None, rule)
        self.assertEqual(errors, [])
        for relative_path in sorted(sources):
            with self.subTest(relative_path=relative_path):
                changed_sources = dict(sources)
                changed_sources[relative_path] += b"\n# deterministic test mutation\n"
                changed_digest = tl._engine_source_bundle_digest(changed_sources)
                self.assertNotEqual(changed_digest, baseline_digest)
                changed_metadata = tl._metadata(
                    market_pack,
                    rule,
                    baseline["metadata"]["input_data_hash"],
                    baseline["metadata"]["configuration_hash"],
                    policy,
                    engine_source_digest=changed_digest,
                )
                self.assertNotEqual(changed_metadata["run_id"],
                                    baseline["metadata"]["run_id"])

    def test_tests_and_samples_are_excluded_from_engine_digest(self):
        manifest = tl._engine_source_manifest()
        self.assertFalse(any("test" in path.lower() for path in manifest))
        self.assertFalse(any("sample_data" in path for path in manifest))
        self.assertNotIn(
            "09_AI_Systems/02_Tools/Trading_Lab/build_demo_pack.py",
            manifest,
        )
        self.assertEqual(tl._engine_source_digest(),
                         tl._engine_source_bundle_digest(self.engine_sources()))

    def test_engine_source_digest_is_part_of_run_identity(self):
        market_pack = pack([3, 2, 1, 4, 5])
        rule = strategy()
        policy, errors = tl._effective_policy(None, rule)
        self.assertEqual(errors, [])
        input_hash = tl.canonical_sha256(market_pack)
        configuration_hash = tl.canonical_sha256(rule)
        first = tl._metadata(
            market_pack, rule, input_hash, configuration_hash, policy,
            engine_source_digest="0" * 64,
        )
        second = tl._metadata(
            market_pack, rule, input_hash, configuration_hash, policy,
            engine_source_digest="1" * 64,
        )
        self.assertNotEqual(first["run_id"], second["run_id"])

    def test_unchanged_execution_repeats_digest_and_run_id(self):
        first = run([3, 2, 1, 4, 5])
        second = run([3, 2, 1, 4, 5])
        self.assertEqual(first["metadata"]["engine_source_digest"],
                         second["metadata"]["engine_source_digest"])
        self.assertEqual(first["metadata"]["run_id"],
                         second["metadata"]["run_id"])

    def test_engine_source_digest_normalizes_lf_and_crlf(self):
        lf_source = b"first line\nsecond line\n"
        crlf_source = b"first line\r\nsecond line\r\n"
        self.assertEqual(tl._normalized_source_sha256(lf_source),
                         tl._normalized_source_sha256(crlf_source))
        self.assertEqual(
            tl._engine_source_bundle_digest({"module.py": lf_source}),
            tl._engine_source_bundle_digest({"module.py": crlf_source}),
        )

    def test_only_provenance_changes_with_engine_bundle(self):
        with mock.patch.object(tl, "_engine_source_digest",
                               return_value="0" * 64):
            first = run([3, 2, 1, 4, 5])
        with mock.patch.object(tl, "_engine_source_digest",
                               return_value="1" * 64):
            second = run([3, 2, 1, 4, 5])
        self.assertNotEqual(first["metadata"]["run_id"],
                            second["metadata"]["run_id"])
        self.assertNotEqual(first["metadata"]["engine_source_digest"],
                            second["metadata"]["engine_source_digest"])
        first_engine = first["metadata"]["engine"]
        second_engine = second["metadata"]["engine"]
        self.assertNotEqual(first_engine["engine_source_digest"],
                            second_engine["engine_source_digest"])
        first["metadata"]["run_id"] = second["metadata"]["run_id"]
        first["metadata"]["engine_source_digest"] = (
            second["metadata"]["engine_source_digest"]
        )
        first_engine["engine_source_digest"] = (
            second_engine["engine_source_digest"]
        )
        self.assertEqual(first, second)

    def test_unavailable_engine_source_digest_fails_closed(self):
        original = tl._engine_source_digest

        def unavailable():
            raise tl.ReproducibilityError("simulated unreadable source")

        tl._engine_source_digest = unavailable
        try:
            report = run([3, 2, 1, 4, 5])
        finally:
            tl._engine_source_digest = original
        self.assertEqual(report["outcome"], tl.OUTCOME_BLOCKED)
        self.assertEqual(report["reason_code"],
                         tl.BLOCKED_REPRODUCIBILITY_ERROR)
        self.assertIsNone(report["metadata"]["engine_source_digest"])
        self.assertEqual(report["hypothetical_fills"], [])
        self.assertIsNone(report["open_position"])

    def test_identical_inputs_produce_identical_results(self):
        market_pack = pack([3, 2, 1, 4, 5])
        rule = strategy()
        self.assertEqual(tl.run_backtest(rule, market_pack),
                         tl.run_backtest(copy.deepcopy(rule), copy.deepcopy(market_pack)))

    def test_compatibility_facade_retains_existing_callables(self):
        for name in EXPECTED_FACADE_CALLABLES:
            self.assertTrue(callable(getattr(tl, name)), name)
        self.assertEqual(tl.run_backtest.__module__, "trading_lab")
        self.assertEqual(tl.sma_cross_signals.__module__, "trading_lab")

    def test_committed_demo_financial_semantics_and_hashes_are_unchanged(self):
        path = os.path.join(BASE, "sample_data", "TRL-PACK-DEMO.json")
        with open(path, encoding="utf-8") as handle:
            market_pack = json.load(handle)
        rule = strategy(symbol="DEMO-EQ-A", fast=5, slow=20)
        report = tl.run_backtest(rule, market_pack)
        self.assertEqual(report["metadata"]["input_data_hash"],
                         "6cdbca208cd1029b90e5ed3494ab05a3b7042d224ed01293373fc173a85aee56")
        self.assertEqual(report["metadata"]["configuration_hash"],
                         "3f4c513f275ca034af9fd2f4bbcb4ec382c361969d7706fbb6fb6d26fd26bbbd")
        self.assertEqual(report["metadata"]["strategy_definition_hash"],
                         "e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955")
        semantic_digest = hashlib.sha256(
            tl.canonical_json(without_provenance(report)).encode("utf-8")
        ).hexdigest()
        self.assertEqual(semantic_digest,
                         "6f66351873fb49dc11fcc7f3c0e3c84d0add65b4e0b315bf78da7008070d5331")
        self.assertEqual((report["outcome"], report["reason_code"]),
                         (tl.OUTCOME_FILL, tl.OPEN_TERMINAL_POSITION))
        self.assertEqual(len(report["hypothetical_fills"]), 1)
        self.assertEqual(len(report["trade_list"]), 0)
        self.assertEqual(len(report["equity_curve"]), 60)
        self.assertEqual(report["final_cash"], 94.9975)
        self.assertEqual(report["final_equity"], 100.22673707083118)

    def test_inputs_remain_unmodified(self):
        market_pack = pack([3, 2, 1, 4, 5])
        rule = strategy()
        before_pack, before_rule = copy.deepcopy(market_pack), copy.deepcopy(rule)
        tl.run_backtest(rule, market_pack)
        self.assertEqual(market_pack, before_pack)
        self.assertEqual(rule, before_rule)

    def test_input_and_configuration_hashes_change_relevantly(self):
        first = run([3, 2, 1, 4, 5])
        changed_data = run([3, 2, 1, 4, 6])
        changed_strategy = run([3, 2, 1, 4, 5],
                               rule=strategy(paper_size_pct=4.0))
        self.assertNotEqual(first["metadata"]["input_data_hash"],
                            changed_data["metadata"]["input_data_hash"])
        self.assertEqual(first["metadata"]["input_data_hash"],
                         changed_strategy["metadata"]["input_data_hash"])
        self.assertNotEqual(first["metadata"]["configuration_hash"],
                            changed_strategy["metadata"]["configuration_hash"])
        self.assertNotEqual(first["metadata"]["strategy_definition_hash"],
                            changed_strategy["metadata"]["strategy_definition_hash"])

    def test_mapping_subclass_content_is_hashed_but_never_accepted(self):
        first_pack = DictSubclass(pack([3, 2, 1, 4, 5]))
        second_pack = DictSubclass(pack([3, 2, 1, 4, 6]))
        first_data = tl.run_backtest(strategy(), first_pack)
        second_data = tl.run_backtest(strategy(), second_pack)
        for report in (first_data, second_data):
            self.assertEqual(report["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertNotEqual(first_data["metadata"]["input_data_hash"],
                            second_data["metadata"]["input_data_hash"])
        self.assertNotEqual(first_data["metadata"]["run_id"],
                            second_data["metadata"]["run_id"])

        first_rule = DictSubclass(strategy(paper_size_pct=4.0))
        second_rule = DictSubclass(strategy(paper_size_pct=3.0))
        first_strategy = tl.run_backtest(first_rule, pack())
        repeated_strategy = tl.run_backtest(copy.deepcopy(first_rule), pack())
        second_strategy = tl.run_backtest(second_rule, pack())
        for report in (first_strategy, repeated_strategy, second_strategy):
            self.assertEqual(report["reason_code"],
                             tl.BLOCKED_INVALID_STRATEGY_PARAMETERS)
        self.assertEqual(first_strategy["metadata"]["configuration_hash"],
                         repeated_strategy["metadata"]["configuration_hash"])
        self.assertEqual(first_strategy["metadata"]["run_id"],
                         repeated_strategy["metadata"]["run_id"])
        self.assertNotEqual(first_strategy["metadata"]["configuration_hash"],
                            second_strategy["metadata"]["configuration_hash"])
        self.assertNotEqual(first_strategy["metadata"]["run_id"],
                            second_strategy["metadata"]["run_id"])

        ordinary_first = run([3, 2, 1, 4, 5])
        ordinary_second = run([3, 2, 1, 4, 6])
        self.assertEqual(ordinary_first["validation"]["outcome"], "VALID")
        self.assertEqual(ordinary_second["validation"]["outcome"], "VALID")
        self.assertNotEqual(ordinary_first["metadata"]["input_data_hash"],
                            ordinary_second["metadata"]["input_data_hash"])

    def test_compact_adversarial_matrix_is_deterministic_and_serializable(self):
        huge_pack = pack()
        huge_pack["instruments"][0]["ohlcv"][0]["open"] = 10 ** 5000
        extreme_pack = pack()
        extreme_pack["instruments"][0]["ohlcv"][0]["open"] = 1.797e308
        custom_pack = pack()
        custom_pack["instruments"][0]["ohlcv"][0]["open"] = UnsupportedValue()
        timestamp_pack = pack()
        timestamp_pack["instruments"][0]["ohlcv"][0]["date"] = (
            "0001-01-01T00:00:00+14:00"
        )
        cases = (
            (strategy(), huge_pack, None),
            (strategy(), extreme_pack, None),
            (strategy(paper_size_pct=5e-324), pack(), None),
            (strategy(), timestamp_pack, None),
            (strategy(), DictSubclass(pack()), None),
            (strategy(), custom_pack, None),
            (strategy(), pack(), None),
        )
        for index, (rule, market_pack, policy) in enumerate(cases):
            with self.subTest(index=index):
                first = tl.run_backtest(rule, market_pack, policy)
                second = tl.run_backtest(
                    copy.deepcopy(rule), copy.deepcopy(market_pack),
                    copy.deepcopy(policy),
                )
                self.assertEqual(first, second)
                json.dumps(first, allow_nan=False)
                assert_no_nonfinite_float(self, first)

    def test_unordered_sets_have_stable_rejected_hashes_and_run_ids(self):
        first_pack = pack()
        second_pack = copy.deepcopy(first_pack)
        first_pack["note"] = set(("alpha", "beta", "gamma"))
        second_pack["note"] = set(("gamma", "alpha", "beta"))
        first = tl.run_backtest(strategy(), first_pack)
        second = tl.run_backtest(strategy(), second_pack)
        self.assertEqual(first["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(second["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(first["metadata"]["input_data_hash"],
                         second["metadata"]["input_data_hash"])
        self.assertEqual(first["metadata"]["run_id"], second["metadata"]["run_id"])
        self.assertEqual(tl.canonical_sha256(first_pack),
                         tl.canonical_sha256(second_pack))

    def test_custom_objects_use_only_stable_type_markers(self):
        first_pack = pack()
        second_pack = copy.deepcopy(first_pack)
        first_pack["note"] = UnsupportedValue()
        second_pack["note"] = UnsupportedValue()
        first = tl.run_backtest(strategy(), first_pack)
        second = tl.run_backtest(strategy(), second_pack)
        self.assertEqual(first["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(second["reason_code"], tl.BLOCKED_INVALID_INPUT)
        self.assertEqual(first["metadata"]["input_data_hash"],
                         second["metadata"]["input_data_hash"])
        self.assertEqual(first["metadata"]["run_id"], second["metadata"]["run_id"])
        canonical = tl.canonical_json({"value": UnsupportedValue()})
        self.assertIn('"__unsupported_type__":"UnsupportedValue"', canonical)
        self.assertNotIn("0x", canonical.lower())

    def test_result_metadata_and_accounting_rows_are_canonicalizable(self):
        report = run([3, 2, 1, 4, 5])
        metadata = report["metadata"]
        self.assertEqual(metadata["strategy_id"], tl.STRATEGY_ID)
        self.assertEqual(metadata["public_schema_type_policy"],
                         tl.PUBLIC_SCHEMA_TYPE_POLICY)
        self.assertEqual(metadata["effective_system_risk_limits"]["max_position_pct"], 5.0)
        self.assertEqual(metadata["effective_system_risk_limits"]["drawdown_halt_pct"], -15.0)
        self.assertEqual(metadata["execution_assumptions"]["execution_bar"],
                         "NEXT_VALIDATED_BAR")
        self.assertTrue(metadata["paper_research_only"])
        self.assertEqual(tl.canonical_json(report), tl.canonical_json(report))
        assert_no_nonfinite_float(self, report)
        for row in report["equity_curve"]:
            self.assertAlmostEqual(
                row["total_marked_equity"], row["cash"] + row["position_value"],
            )

    def test_report_shows_costs_open_position_and_warnings(self):
        report = run([3, 2, 1, 4, 5])
        markdown = tl.performance_report_markdown(report)
        for required in ("Realized P&L", "Unrealized P&L", "Commission",
                         "Slippage", "OPEN", "PAPER/RESEARCH ONLY",
                         "Hypothetical"):
            self.assertIn(required, markdown)
        for forbidden in ("guaranteed return", "proven profitable",
                          "annualized return", "win rate", "Founder-approved"):
            self.assertNotIn(forbidden.lower(), markdown.lower())

    def test_cli_and_reporting_boundary_remain_paper_only(self):
        before = sorted(os.listdir(BASE))
        output = io.StringIO()
        with preserved_process_state():
            sys.argv = [tl.__file__, "--demo"]
            with contextlib.redirect_stdout(output):
                runpy.run_path(tl.__file__, run_name="__main__")
        cli_report = json.loads(output.getvalue())
        self.assertTrue(cli_report["metadata"]["paper_research_only"])
        self.assertIn("NO LIVE TRADING", cli_report["disclaimer"])
        self.assertIn("paper-only", cli_report["performance_disclaimer"])
        self.assertEqual(sorted(os.listdir(BASE)), before)

    def test_sample_generator_exactly_matches_tracked_json(self):
        path = os.path.join(BASE, "sample_data", "TRL-PACK-DEMO.json")
        with open(path, encoding="utf-8") as handle:
            tracked = json.load(handle)
        self.assertEqual(build_demo_pack.build_pack(), tracked)
        self.assertEqual(tl.validate_market_pack(tracked), [])

    def test_news_pack_remains_fictional(self):
        path = os.path.join(BASE, "sample_data", "TRL-NEWS-DEMO.json")
        with open(path, encoding="utf-8") as handle:
            news = json.load(handle)
        self.assertIn("FICTIONAL", news["note"])

    def test_no_network_ai_broker_credentials_or_external_order_dependency(self):
        paths = [
            os.path.join(REPOSITORY_ROOT, *name.split("/"))
            for name in tl._engine_source_manifest()
        ] + [os.path.join(BASE, "build_demo_pack.py")]
        for path in paths:
            with open(path, encoding="utf-8") as handle:
                source = handle.read()
            tree = ast.parse(source)
            imported = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif (isinstance(node, ast.ImportFrom) and node.module
                      and node.level == 0):
                    imported.add(node.module.split(".")[0])
            self.assertTrue(imported <= {
                "copy", "datetime", "hashlib", "json", "math", "os", "random",
                "re", "sys", "trading_lab_core",
            })
            lowered = source.lower()
            for forbidden in ("api_key", "broker_api", "place_order(",
                              "requests.", "urllib.", "socket.", "openai",
                              "credential_field"):
                self.assertNotIn(forbidden, lowered)

    def test_source_open_calls_are_context_managed(self):
        paths = [
            os.path.join(REPOSITORY_ROOT, *name.split("/"))
            for name in tl._engine_source_manifest()
        ] + [
            os.path.join(BASE, "build_demo_pack.py"),
            os.path.join(BASE, "test_trading_lab.py"),
        ]
        for path in paths:
            with open(path, encoding="utf-8") as handle:
                tree = ast.parse(handle.read())
            open_calls = [node for node in ast.walk(tree)
                          if isinstance(node, ast.Call)
                          and isinstance(node.func, ast.Name)
                          and node.func.id == "open"]
            with_open_calls = []
            for node in ast.walk(tree):
                if isinstance(node, ast.With):
                    for item in node.items:
                        with_open_calls.extend(
                            candidate for candidate in ast.walk(item.context_expr)
                            if isinstance(candidate, ast.Call)
                            and isinstance(candidate.func, ast.Name)
                            and candidate.func.id == "open"
                        )
            self.assertEqual(len(open_calls), len(with_open_calls), path)

    def test_decision_log_requires_human_value(self):
        with self.assertRaises(tl.RiskPolicyViolation):
            tl.decision_log_entry("D1", [], {}, "b", "b", ["unknown"],
                                  "AUTO_ACCEPT", "n/a", {})

    def test_modules_resolve_from_local_standard_library_only(self):
        self.assertIsNotNone(importlib.util.find_spec("hashlib"))
        self.assertFalse(math.isnan(run([100] * 5)["final_equity"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
