# -*- coding: utf-8 -*-
"""Fake-provider acceptance tests for TRL-R2-003 local MT5 read-only data."""

import copy
from collections import namedtuple
import http.client
import importlib
import json
import math
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest import mock

from datetime import datetime, timezone


BASE = Path(__file__).resolve().parent
APP_DIRECTORY = BASE / "trading_lab_app"
FIXED_NOW = datetime(2026, 7, 26, 12, 0, 30, tzinfo=timezone.utc)
FIXED_SECONDS = int(FIXED_NOW.timestamp())

sys.path.insert(0, str(BASE))
from trading_lab_app import app, capabilities, market_data, server, service  # noqa: E402
from trading_lab_app.mt5_connector import (  # noqa: E402
    LocalMT5ReadOnlyConnector,
    PROVIDER_CONSTANT_ALLOWLIST,
    PROVIDER_METHOD_ALLOWLIST,
)
from trading_lab_app.mt5_service import (  # noqa: E402
    MT5ReadOnlyConfiguration,
    MarketDataService,
)


def fixed_clock():
    return FIXED_NOW


def specification(symbol="XAUUSD", **changes):
    value = {
        "name": symbol,
        "visible": True,
        "description": "Gold vs US Dollar",
        "currency_base": "XAU",
        "currency_profit": "USD",
        "currency_margin": "USD",
        "digits": 2,
        "point": 0.01,
        "trade_contract_size": 100.0,
        "volume_min": 0.01,
        "volume_max": 100.0,
        "volume_step": 0.01,
        "trade_stops_level": 10,
        "trade_freeze_level": 5,
        "trade_mode": 4,
        "spread": 25,
        "unexpected_secret": "must never be copied",
    }
    value.update(changes)
    return value


def tick(**changes):
    value = {
        "time": FIXED_SECONDS - 10,
        "time_msc": (FIXED_SECONDS - 10) * 1000 + 321,
        "bid": 2375.12,
        "ask": 2375.37,
        "last": 2375.20,
        "volume": 18,
        "unexpected_account": "must never be copied",
    }
    value.update(changes)
    return value


def bars_for(timeframe, forming=True):
    interval = market_data.SUPPORTED_TIMEFRAMES[timeframe]["seconds"]
    current_open = FIXED_SECONDS - (FIXED_SECONDS % interval)
    latest = current_open if forming else current_open - interval
    return [
        {
            "time": latest - interval,
            "open": 2370.0,
            "high": 2374.0,
            "low": 2369.0,
            "close": 2373.0,
            "tick_volume": 100,
            "spread": 24,
            "real_volume": 0,
        },
        {
            "time": latest,
            "open": 2373.0,
            "high": 2377.0,
            "low": 2372.0,
            "close": 2375.0,
            "tick_volume": 110,
            "spread": 25,
            "real_volume": 0,
        },
    ]


_UNSET = object()


class FakeReadOnlyProvider:
    """Data-source fake only; it has no trading, account, or order behavior."""

    TIMEFRAME_M1 = 101
    TIMEFRAME_M5 = 205
    TIMEFRAME_H4 = 404
    TIMEFRAME_D1 = 1001

    def __init__(
        self,
        symbols=None,
        symbol_specification=_UNSET,
        source_tick=_UNSET,
        rates=None,
        initialize_result=True,
    ):
        self.inventory = copy.deepcopy(symbols if symbols is not None else [{"name": "XAUUSD"}])
        if symbol_specification is _UNSET:
            inventory_names = {
                market_data._field(item, "name") for item in self.inventory
            }
            symbol_specification = specification() if "XAUUSD" in inventory_names else None
        self.specification = copy.deepcopy(symbol_specification)
        self.source_tick = copy.deepcopy(tick() if source_tick is _UNSET else source_tick)
        self.rates = copy.deepcopy(rates if rates is not None else {
            getattr(self, "TIMEFRAME_{}".format(name)): bars_for(name)
            for name in market_data.SUPPORTED_TIMEFRAMES
        })
        self.initialize_result = initialize_result
        self.calls = []
        self.active_sessions = 0
        self.maximum_active_sessions = 0
        self.operation_delay = 0.0

    def initialize(self, **kwargs):
        self.calls.append(("initialize", copy.deepcopy(kwargs)))
        if self.operation_delay:
            self.active_sessions += 1
            self.maximum_active_sessions = max(self.maximum_active_sessions, self.active_sessions)
            time.sleep(self.operation_delay)
        return self.initialize_result

    def shutdown(self):
        self.calls.append(("shutdown",))
        if self.operation_delay:
            self.active_sessions -= 1

    def last_error(self):
        self.calls.append(("last_error",))
        return (5001, "sensitive provider text is intentionally ignored")

    def symbols_get(self):
        self.calls.append(("symbols_get",))
        return copy.deepcopy(self.inventory)

    def symbol_info(self, symbol):
        self.calls.append(("symbol_info", symbol))
        return copy.deepcopy(self.specification)

    def symbol_info_tick(self, symbol):
        self.calls.append(("symbol_info_tick", symbol))
        return copy.deepcopy(self.source_tick)

    def copy_rates_from_pos(self, symbol, timeframe, start, count):
        self.calls.append(("copy_rates_from_pos", symbol, timeframe, start, count))
        return copy.deepcopy(self.rates.get(timeframe, []))


def connector_snapshot(provider=None, **changes):
    arguments = {
        "requested_symbol": "XAUUSD",
        "timeframes": market_data.DEFAULT_TIMEFRAMES,
        "bar_count": 500,
        "timeout_ms": 5000,
        "stale_threshold_seconds": 180,
    }
    arguments.update(changes)
    connector = LocalMT5ReadOnlyConnector(
        provider=provider or FakeReadOnlyProvider(), clock=fixed_clock
    )
    return connector.snapshot(**arguments)


class SequenceClock:
    def __init__(self, *values):
        self.values = list(values)
        self.calls = 0

    def __call__(self):
        index = min(self.calls, len(self.values) - 1)
        self.calls += 1
        return self.values[index]


class IntegerScalar(int):
    def item(self):
        raise AssertionError(".item() must not be called")


class FloatScalar(float):
    def item(self):
        raise AssertionError(".item() must not be called")


class StructuredRecord:
    __slots__ = ("fields",)

    def __init__(self, fields):
        self.fields = fields

    def __getitem__(self, name):
        return self.fields[name]


class StructuredArrayLike:
    __slots__ = ("records",)

    def __init__(self, records):
        self.records = tuple(records)

    def __iter__(self):
        return iter(self.records)


class StartupAndProviderBoundaryTests(unittest.TestCase):
    def test_mt5_is_disabled_by_default_and_cli_controls_require_opt_in(self):
        document = MarketDataService(clock=fixed_clock).snapshot_document()
        self.assertEqual(document["connection_status"], "MT5_DISABLED")
        self.assertIsNone(document["tick"])
        self.assertEqual(app.main(["--mt5-symbol", "XAUUSD", "--no-browser"]), 2)
        self.assertEqual(app.main(["--enable-mt5-read-only", "--no-browser"]), 2)

    def test_dependency_is_lazy_and_missing_dependency_fails_closed(self):
        connector = LocalMT5ReadOnlyConnector(clock=fixed_clock)
        with mock.patch.object(importlib, "import_module", side_effect=ImportError("missing")) as loader:
            document = connector.snapshot("XAUUSD")
        loader.assert_called_once_with("MetaTrader5")
        self.assertEqual(document["connection_status"], "MT5_DEPENDENCY_MISSING")
        self.assertIsNone(document["tick"])

    def test_initialization_failure_is_bounded_and_fail_closed(self):
        provider = FakeReadOnlyProvider(initialize_result=False)
        document = connector_snapshot(provider, timeout_ms=1234)
        self.assertEqual(provider.calls[0], ("initialize", {"timeout": 1234}))
        self.assertEqual(document["connection_status"], "MT5_INITIALIZATION_FAILED")
        self.assertEqual(document["data_quality"]["provider_error_code"], 5001)
        self.assertNotIn("shutdown", [call[0] for call in provider.calls])
        self.assertIsNone(document["tick"])

    def test_timeout_and_bar_bounds_are_rejected_before_provider_access(self):
        provider = FakeReadOnlyProvider()
        connector = LocalMT5ReadOnlyConnector(provider, fixed_clock)
        for timeout in (999, 30001, True):
            with self.assertRaises(ValueError):
                connector.snapshot("XAUUSD", timeout_ms=timeout)
        for count in (0, 2001, True):
            with self.assertRaises(ValueError):
                connector.snapshot("XAUUSD", bar_count=count)
        self.assertEqual(provider.calls, [])

    def test_exact_provider_method_allowlist_and_forbidden_nonuse(self):
        self.assertEqual(PROVIDER_METHOD_ALLOWLIST, {
            "initialize", "shutdown", "last_error", "symbols_get", "symbol_info",
            "symbol_info_tick", "copy_rates_from_pos",
        })
        provider = FakeReadOnlyProvider()
        connector_snapshot(provider)
        self.assertTrue({call[0] for call in provider.calls} <= PROVIDER_METHOD_ALLOWLIST)
        self.assertEqual(PROVIDER_CONSTANT_ALLOWLIST, {
            "TIMEFRAME_M1", "TIMEFRAME_M5", "TIMEFRAME_H4", "TIMEFRAME_D1",
        })
        connector_source = (APP_DIRECTORY / "mt5_connector.py").read_text(encoding="utf-8")
        for forbidden in (
            "account_info", "positions_get", "positions_total", "orders_get",
            "orders_total", "order_check", "order_send", "history_orders_get",
            "history_orders_total", "history_deals_get", "history_deals_total",
            "symbol_select",
        ):
            self.assertNotIn(forbidden, connector_source)

    def test_initialized_session_always_shuts_down(self):
        provider = FakeReadOnlyProvider()
        connector_snapshot(provider)
        self.assertEqual([call[0] for call in provider.calls].count("shutdown"), 1)
        provider = FakeReadOnlyProvider(source_tick=None)
        provider.source_tick = None
        document = connector_snapshot(provider)
        self.assertEqual([call[0] for call in provider.calls].count("shutdown"), 1)
        self.assertEqual(document["connection_status"], "MT5_TICK_UNAVAILABLE")

    def test_cli_has_no_credential_or_remote_connection_controls(self):
        destinations = {action.dest for action in app.build_parser()._actions}
        for forbidden in (
            "login", "username", "password", "investor_password", "api_key",
            "server", "broker_server", "host", "remote_host", "terminal_path",
        ):
            self.assertNotIn(forbidden, destinations)

    def test_provider_exception_is_sanitized_and_snapshot_is_empty(self):
        provider = FakeReadOnlyProvider()
        provider.symbol_info = mock.Mock(side_effect=RuntimeError("C:\\Users\\Person\\secret"))
        document = connector_snapshot(provider)
        encoded = json.dumps(document, sort_keys=True)
        self.assertEqual(document["connection_status"], "MT5_PROVIDER_ERROR")
        self.assertNotIn("Person", encoded)
        self.assertNotIn("secret", encoded)
        self.assertIsNone(document["tick"])

    def test_provider_inputs_are_not_mutated_and_unknown_attributes_are_not_exposed(self):
        provider = FakeReadOnlyProvider()
        before = copy.deepcopy((provider.inventory, provider.specification, provider.source_tick, provider.rates))
        document = connector_snapshot(provider)
        after = (provider.inventory, provider.specification, provider.source_tick, provider.rates)
        self.assertEqual(before, after)
        encoded = json.dumps(document, sort_keys=True)
        self.assertNotIn("unexpected_secret", encoded)
        self.assertNotIn("unexpected_account", encoded)

    def test_calls_are_serialized_across_threads(self):
        provider = FakeReadOnlyProvider()
        provider.operation_delay = 0.03
        connectors = [
            LocalMT5ReadOnlyConnector(provider, fixed_clock),
            LocalMT5ReadOnlyConnector(provider, fixed_clock),
        ]
        results = []
        threads = [
            threading.Thread(target=lambda item=item: results.append(item.snapshot("XAUUSD")))
            for item in connectors
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=3)
        self.assertEqual(len(results), 2)
        self.assertEqual(provider.maximum_active_sessions, 1)


class SymbolResolutionTests(unittest.TestCase):
    def test_exact_symbol_is_preserved_without_suffix_removal(self):
        provider = FakeReadOnlyProvider()
        document = connector_snapshot(provider)
        self.assertEqual(document["resolved_symbol"], "XAUUSD")
        self.assertEqual(document["candidate_symbols"], [])
        self.assertNotIn("symbols_get", [call[0] for call in provider.calls])

    def test_suffixed_symbol_is_candidate_only(self):
        provider = FakeReadOnlyProvider(symbols=[{"name": "XAUUSD.a"}])
        document = connector_snapshot(provider)
        self.assertEqual(document["connection_status"], "MT5_SYMBOL_NOT_FOUND")
        self.assertEqual(document["candidate_symbols"], ["XAUUSD.a"])
        self.assertIsNone(document["resolved_symbol"])
        self.assertEqual([call[0] for call in provider.calls].count("symbol_info"), 1)
        self.assertEqual([call[0] for call in provider.calls].count("symbols_get"), 1)

    def test_alternative_gold_name_is_candidate_not_equivalence(self):
        provider = FakeReadOnlyProvider(symbols=[{"name": "GOLD"}])
        document = connector_snapshot(provider)
        self.assertEqual(document["candidate_symbols"], ["GOLD"])
        self.assertIsNone(document["resolved_symbol"])

    def test_multiple_candidates_are_ambiguous_and_sorted(self):
        provider = FakeReadOnlyProvider(symbols=[
            {"name": "XAUUSD.z"}, {"name": "GOLD"}, {"name": "XAUUSD.a"},
        ])
        document = connector_snapshot(provider)
        self.assertEqual(document["connection_status"], "MT5_SYMBOL_AMBIGUOUS")
        self.assertEqual(document["candidate_symbols"], ["GOLD", "XAUUSD.a", "XAUUSD.z"])

    def test_missing_symbol_has_no_candidates_or_substitution(self):
        provider = FakeReadOnlyProvider(symbols=[{"name": "EURUSD"}])
        document = connector_snapshot(provider)
        self.assertEqual(document["connection_status"], "MT5_SYMBOL_NOT_FOUND")
        self.assertEqual(document["candidate_symbols"], [])
        self.assertIsNone(document["resolved_symbol"])

    def test_candidate_inspection_and_response_are_bounded(self):
        symbols = [{"name": "XAUUSD.{:04d}".format(index)} for index in range(6000)]
        document = connector_snapshot(FakeReadOnlyProvider(symbols=symbols))
        self.assertEqual(len(document["candidate_symbols"]), market_data.MAX_CANDIDATES)
        self.assertNotIn("XAUUSD.5999", document["candidate_symbols"])

    def test_exact_lookup_succeeds_without_inventory_or_beyond_inventory_bound(self):
        for symbols in (
            [],
            [{"name": "S{:04d}".format(index)} for index in range(5000)]
            + [{"name": "XAUUSD"}],
        ):
            provider = FakeReadOnlyProvider(
                symbols=symbols,
                symbol_specification=specification(),
            )
            document = connector_snapshot(provider)
            self.assertEqual(document["resolved_symbol"], "XAUUSD")
            self.assertNotIn("symbols_get", [call[0] for call in provider.calls])

    def test_different_symbol_info_name_is_not_silently_accepted(self):
        provider = FakeReadOnlyProvider(
            symbols=[{"name": "XAUUSD.a"}],
            symbol_specification=specification(symbol="XAUUSD.a"),
        )
        document = connector_snapshot(provider)
        self.assertIsNone(document["resolved_symbol"])
        self.assertEqual(document["candidate_symbols"], ["XAUUSD.a"])
        self.assertEqual(document["connection_status"], "MT5_SYMBOL_NOT_FOUND")

    def test_disabled_or_unavailable_exact_symbol_requests_market_watch_visibility(self):
        provider = FakeReadOnlyProvider(symbol_specification=specification(visible=False))
        document = connector_snapshot(provider)
        self.assertEqual(document["reason_code"], "MT5_SYMBOL_NOT_VISIBLE")
        self.assertIn("Market Watch", document["data_quality"]["diagnostic"])

    def test_unsafe_symbol_and_unknown_timeframe_are_rejected_without_provider_call(self):
        provider = FakeReadOnlyProvider()
        connector = LocalMT5ReadOnlyConnector(provider, fixed_clock)
        for symbol in ("../XAUUSD", "XAU USD", "", "A" * 65):
            with self.assertRaises(ValueError):
                connector.snapshot(symbol)
        with self.assertRaises(ValueError):
            connector.snapshot("XAUUSD", timeframes=("M15",))
        self.assertEqual(provider.calls, [])


class TickAndSpecificationTests(unittest.TestCase):
    def test_valid_bid_ask_raw_spread_and_points_are_preserved(self):
        document = connector_snapshot(FakeReadOnlyProvider())
        normalized = document["tick"]
        self.assertEqual(normalized["bid"], 2375.12)
        self.assertEqual(normalized["ask"], 2375.37)
        self.assertEqual(normalized["spread_price"], 2375.37 - 2375.12)
        self.assertEqual(normalized["spread_points"], (2375.37 - 2375.12) / 0.01)
        self.assertEqual(document["symbol_specification"]["broker_reported_spread_points"], 25)

    def test_crossed_nonfinite_or_boolean_tick_fails_closed(self):
        for changes in (
            {"ask": 2370.0}, {"bid": math.nan}, {"ask": math.inf}, {"bid": True},
        ):
            provider = FakeReadOnlyProvider(source_tick=tick(**changes))
            document = connector_snapshot(provider)
            self.assertEqual(document["reason_code"], "MT5_INVALID_TICK")
            self.assertIsNone(document["tick"])

    def test_invalid_point_digits_and_contract_size_fail_closed(self):
        cases = (
            {"point": 0}, {"point": math.nan}, {"digits": -1}, {"digits": True},
            {"trade_contract_size": 0}, {"trade_contract_size": math.inf},
        )
        for changes in cases:
            document = connector_snapshot(
                FakeReadOnlyProvider(symbol_specification=specification(**changes))
            )
            self.assertEqual(document["reason_code"], "MT5_INVALID_SYMBOL_SPECIFICATION")
            self.assertIsNone(document["symbol_specification"])

    def test_invalid_volume_bounds_and_step_fail_closed(self):
        for changes in (
            {"volume_min": -0.01}, {"volume_min": 0}, {"volume_max": 0.001}, {"volume_step": 0},
            {"volume_max": math.inf},
        ):
            document = connector_snapshot(
                FakeReadOnlyProvider(symbol_specification=specification(**changes))
            )
            self.assertEqual(document["reason_code"], "MT5_INVALID_SYMBOL_SPECIFICATION")

    def test_commission_is_explicitly_unknown(self):
        specification_document = connector_snapshot(FakeReadOnlyProvider())["symbol_specification"]
        self.assertIsNone(specification_document["commission"])
        self.assertEqual(specification_document["commission_status"], "UNKNOWN_NO_GOVERNED_SOURCE")


class BarAndFreshnessTests(unittest.TestCase):
    def test_only_four_timeframe_mappings_are_supported(self):
        self.assertEqual(set(market_data.SUPPORTED_TIMEFRAMES), {"M1", "M5", "H4", "D1"})
        provider = FakeReadOnlyProvider()
        connector_snapshot(provider)
        requested = {
            call[2] for call in provider.calls if call[0] == "copy_rates_from_pos"
        }
        self.assertEqual(requested, {
            provider.TIMEFRAME_M1,
            provider.TIMEFRAME_M5,
            provider.TIMEFRAME_H4,
            provider.TIMEFRAME_D1,
        })

    def test_current_latest_bar_is_forming_and_previous_is_closed(self):
        series = connector_snapshot(FakeReadOnlyProvider())["timeframe_series"]
        for timeframe in market_data.DEFAULT_TIMEFRAMES:
            self.assertEqual([bar["bar_state"] for bar in series[timeframe]["bars"]], ["CLOSED", "FORMING"])
            self.assertEqual(series[timeframe]["closed_bar_count"], 1)
            self.assertEqual(series[timeframe]["forming_bar_count"], 1)

    def test_historical_latest_bar_is_closed(self):
        provider = FakeReadOnlyProvider()
        provider.rates = {
            getattr(provider, "TIMEFRAME_{}".format(name)): bars_for(name, forming=False)
            for name in market_data.SUPPORTED_TIMEFRAMES
        }
        series = connector_snapshot(provider)["timeframe_series"]
        self.assertTrue(all(
            item["forming_bar_count"] == 0 and item["closed_bar_count"] == 2
            for item in series.values()
        ))

    def test_duplicate_and_nonmonotonic_timestamps_fail_entire_bar_snapshot(self):
        for second_time in (
            bars_for("M1")[0]["time"], bars_for("M1")[0]["time"] - 60,
        ):
            provider = FakeReadOnlyProvider()
            provider.rates[provider.TIMEFRAME_M1][1]["time"] = second_time
            document = connector_snapshot(provider)
            self.assertEqual(document["reason_code"], "MT5_INVALID_BAR_DATA")
            self.assertTrue(all(not item["bars"] for item in document["timeframe_series"].values()))

    def test_invalid_ohlc_nonfinite_boolean_negative_volume_or_spread_fail_closed(self):
        changes = (
            ("high", 2360.0), ("low", 2380.0), ("open", math.nan), ("close", math.inf),
            ("open", True), ("tick_volume", -1), ("spread", -1), ("real_volume", -1),
        )
        for field, value in changes:
            provider = FakeReadOnlyProvider()
            provider.rates[provider.TIMEFRAME_M1][0][field] = value
            document = connector_snapshot(provider)
            self.assertEqual(document["reason_code"], "MT5_INVALID_BAR_DATA")
            self.assertIsNone(document["tick"])

    def test_empty_and_partial_timeframe_availability_is_explicit(self):
        provider = FakeReadOnlyProvider()
        provider.rates = {
            getattr(provider, "TIMEFRAME_{}".format(name)): []
            for name in market_data.SUPPORTED_TIMEFRAMES
        }
        document = connector_snapshot(provider)
        self.assertEqual(document["reason_code"], "MT5_BAR_DATA_UNAVAILABLE")
        self.assertFalse(document["data_quality"]["snapshot_valid"])
        provider = FakeReadOnlyProvider()
        provider.rates[provider.TIMEFRAME_M5] = []
        document = connector_snapshot(provider)
        self.assertEqual(document["timeframe_series"]["M1"]["status"], "AVAILABLE")
        self.assertEqual(document["timeframe_series"]["M5"]["status"], "UNAVAILABLE")
        self.assertFalse(document["data_quality"]["snapshot_valid"])

    def test_provider_cannot_expand_response_beyond_bar_limit(self):
        provider = FakeReadOnlyProvider()
        first = provider.rates[provider.TIMEFRAME_M1][0]
        provider.rates[provider.TIMEFRAME_M1] = [
            copy.deepcopy(first) for _ in range(market_data.MAX_BAR_COUNT + 1)
        ]
        document = connector_snapshot(provider)
        self.assertEqual(document["reason_code"], "MT5_INVALID_BAR_DATA")
        self.assertTrue(all(not item["bars"] for item in document["timeframe_series"].values()))

    def test_freshness_uses_injected_clock_and_session_is_unknown(self):
        document = connector_snapshot(FakeReadOnlyProvider())
        quality = document["data_quality"]
        self.assertEqual(quality["tick_age_seconds"], 10.0)
        self.assertEqual(quality["future_tick_skew_seconds"], 0.0)
        self.assertEqual(quality["freshness_status"], "FRESH")
        self.assertEqual(quality["market_session_status"], "MARKET_SESSION_UNKNOWN")

    def test_future_tick_beyond_tolerance_fails_closed_for_seconds_or_milliseconds(self):
        cases = (
            tick(
                time=FIXED_SECONDS + 60,
                time_msc=(FIXED_SECONDS + 60) * 1000,
            ),
            tick(time_msc=(FIXED_SECONDS + 60) * 1000),
        )
        for source_tick in cases:
            document = connector_snapshot(FakeReadOnlyProvider(source_tick=source_tick))
            self.assertEqual(document["reason_code"], "MT5_TICK_CLOCK_SKEW")
            self.assertFalse(document["data_quality"]["snapshot_valid"])
            self.assertIsNone(document["data_quality"]["tick_age_seconds"])
            self.assertNotEqual(document["data_quality"]["freshness_status"], "FRESH")
            self.assertIsNone(document["tick"])

    def test_future_tick_within_tolerance_is_explicit_and_deterministic(self):
        source_tick = tick(
            time=FIXED_SECONDS + 4,
            time_msc=(FIXED_SECONDS + 4) * 1000 + 250,
        )
        first = connector_snapshot(FakeReadOnlyProvider(source_tick=source_tick))
        second = connector_snapshot(FakeReadOnlyProvider(source_tick=source_tick))
        self.assertEqual(first, second)
        quality = first["data_quality"]
        self.assertEqual(first["reason_code"], "MT5_READ_ONLY_SNAPSHOT_VALID")
        self.assertEqual(quality["freshness_status"], "CLOCK_SKEW_WITHIN_TOLERANCE")
        self.assertEqual(quality["tick_age_seconds"], 0.0)
        self.assertAlmostEqual(quality["future_tick_skew_seconds"], 4.25)
        self.assertEqual(first["tick"]["source_timestamp_milliseconds"], source_tick["time_msc"])

    def test_retrieval_completion_time_accepts_new_bar_after_boundary(self):
        request_start = FIXED_NOW.replace(second=59)
        completion = request_start.replace(minute=1, second=1)
        boundary_seconds = int(request_start.replace(minute=1, second=0).timestamp())
        provider = FakeReadOnlyProvider(source_tick=tick(
            time=boundary_seconds,
            time_msc=boundary_seconds * 1000,
        ))
        rows = bars_for("M1")
        rows[0]["time"] = boundary_seconds - 60
        rows[1]["time"] = boundary_seconds
        provider.rates[provider.TIMEFRAME_M1] = rows
        clock = SequenceClock(request_start, completion)
        document = LocalMT5ReadOnlyConnector(provider, clock).snapshot(
            "XAUUSD", timeframes=("M1",), bar_count=2,
        )
        self.assertEqual(clock.calls, 2)
        self.assertEqual(document["retrieval_timestamp_utc"], "2026-07-26T12:01:01.000Z")
        self.assertEqual(document["reason_code"], "MT5_READ_ONLY_SNAPSHOT_VALID")
        self.assertEqual(document["data_quality"]["tick_age_seconds"], 1.0)
        self.assertEqual(
            document["timeframe_series"]["M1"]["bars"][-1]["bar_state"],
            "FORMING",
        )

    def test_stale_quote_is_reported_without_claiming_market_failure(self):
        provider = FakeReadOnlyProvider(source_tick=tick(time=FIXED_SECONDS - 500, time_msc=(FIXED_SECONDS - 500) * 1000))
        document = connector_snapshot(provider)
        self.assertEqual(document["reason_code"], "MT5_STALE")
        self.assertEqual(document["data_quality"]["freshness_status"], "STALE_BY_THRESHOLD")
        self.assertEqual(document["connection_status"], "MT5_CONNECTED")
        self.assertIn("market session is unknown", document["data_quality"]["diagnostic"])

    def test_complete_schema_is_sanitized_and_fixed_input_is_deterministic(self):
        first = connector_snapshot(FakeReadOnlyProvider())
        second = connector_snapshot(FakeReadOnlyProvider())
        self.assertEqual(first, second)
        self.assertEqual(set(first), {
            "schema_version", "source_type", "connector_mode", "connection_status",
            "reason_code", "requested_symbol", "resolved_symbol", "candidate_symbols",
            "retrieval_timestamp_utc", "tick", "symbol_specification", "timeframe_series",
            "data_quality", "limitations",
        })
        encoded = server.deterministic_json_bytes(first)
        self.assertEqual(encoded, server.deterministic_json_bytes(second))
        self.assertNotIn(str(BASE).encode("utf-8"), encoded)


class ProviderConstantCompatibilityTests(unittest.TestCase):
    def test_nonstandard_provider_constants_are_used_exactly(self):
        class NonstandardProvider(FakeReadOnlyProvider):
            TIMEFRAME_M1 = 71
            TIMEFRAME_M5 = 83
            TIMEFRAME_H4 = 97
            TIMEFRAME_D1 = 109

        provider = NonstandardProvider()
        document = connector_snapshot(provider)
        self.assertEqual(document["reason_code"], "MT5_READ_ONLY_SNAPSHOT_VALID")
        calls = [call for call in provider.calls if call[0] == "copy_rates_from_pos"]
        self.assertEqual([call[2] for call in calls], [
            provider.TIMEFRAME_M1,
            provider.TIMEFRAME_M5,
            provider.TIMEFRAME_H4,
            provider.TIMEFRAME_D1,
        ])

    def test_invalid_or_missing_provider_constants_fail_before_bar_access(self):
        invalid_values = (True, 0, -1, 2 ** 63)
        providers = []
        for value in invalid_values:
            provider = FakeReadOnlyProvider()
            provider.TIMEFRAME_M1 = value
            providers.append(provider)
        duplicate = FakeReadOnlyProvider()
        duplicate.TIMEFRAME_M5 = duplicate.TIMEFRAME_M1
        providers.append(duplicate)

        class MissingConstantProvider(FakeReadOnlyProvider):
            def __getattribute__(self, name):
                if name == "TIMEFRAME_D1":
                    raise AttributeError(name)
                return super().__getattribute__(name)

        providers.append(MissingConstantProvider(rates={}))
        for provider in providers:
            document = connector_snapshot(provider)
            self.assertEqual(document["reason_code"], "MT5_PROVIDER_INCOMPATIBLE")
            self.assertFalse(document["data_quality"]["snapshot_valid"])
            self.assertNotIn(
                "copy_rates_from_pos", [call[0] for call in provider.calls]
            )

    def test_conversion_only_constant_is_not_coerced(self):
        class ConversionOnly:
            calls = 0

            def __int__(self):
                self.calls += 1
                return 17

        provider = FakeReadOnlyProvider()
        value = ConversionOnly()
        provider.TIMEFRAME_M1 = value
        document = connector_snapshot(provider)
        self.assertEqual(document["reason_code"], "MT5_PROVIDER_INCOMPATIBLE")
        self.assertEqual(value.calls, 0)


class RealProviderShapeTests(unittest.TestCase):
    def test_namedtuples_structured_array_and_numeric_scalars_are_supported(self):
        SymbolInfo = namedtuple(
            "SymbolInfo",
            (
                "name visible digits point trade_contract_size volume_min volume_max "
                "volume_step trade_stops_level trade_freeze_level trade_mode"
            ),
        )
        TickInfo = namedtuple("TickInfo", "time time_msc bid ask last volume")
        source_specification = SymbolInfo(
            "XAUUSD", True, IntegerScalar(2), FloatScalar(0.01),
            FloatScalar(100.0), FloatScalar(0.01), FloatScalar(100.0),
            FloatScalar(0.01), IntegerScalar(10), IntegerScalar(5), IntegerScalar(4),
        )
        source_tick = TickInfo(
            IntegerScalar(FIXED_SECONDS - 10),
            IntegerScalar((FIXED_SECONDS - 10) * 1000 + 321),
            FloatScalar(2375.12), FloatScalar(2375.37), FloatScalar(0.0),
            IntegerScalar(0),
        )
        provider = FakeReadOnlyProvider(
            symbol_specification=source_specification,
            source_tick=source_tick,
        )
        provider.rates = {
            getattr(provider, "TIMEFRAME_{}".format(timeframe)): StructuredArrayLike(
                StructuredRecord({
                    name: IntegerScalar(value) if isinstance(value, int) else FloatScalar(value)
                    for name, value in row.items()
                })
                for row in bars_for(timeframe)
            )
            for timeframe in market_data.SUPPORTED_TIMEFRAMES
        }
        before = copy.deepcopy((
            provider.specification,
            provider.source_tick,
            [record.fields for value in provider.rates.values() for record in value],
        ))
        document = connector_snapshot(provider)
        after = (
            provider.specification,
            provider.source_tick,
            [record.fields for value in provider.rates.values() for record in value],
        )
        self.assertEqual(before, after)
        self.assertEqual(document["reason_code"], "MT5_READ_ONLY_SNAPSHOT_VALID")
        self.assertEqual(document["tick"]["last"], 0.0)
        self.assertEqual(document["tick"]["volume"], 0)
        self.assertIsNone(document["symbol_specification"]["description"])
        self.assertIsNone(document["symbol_specification"]["broker_reported_spread_points"])
        connector_source = (APP_DIRECTORY / "mt5_connector.py").read_text(encoding="utf-8")
        normalizer_source = (APP_DIRECTORY / "market_data.py").read_text(encoding="utf-8")
        self.assertNotIn("pandas", connector_source + normalizer_source)
        self.assertNotIn(".item(", connector_source + normalizer_source)

    def test_none_provider_results_fail_closed_or_report_empty_data(self):
        missing_symbol = FakeReadOnlyProvider(symbols=[])
        missing_symbol.inventory = None
        self.assertEqual(
            connector_snapshot(missing_symbol)["reason_code"],
            "MT5_SYMBOL_NOT_FOUND",
        )
        missing_tick = FakeReadOnlyProvider(source_tick=None)
        self.assertEqual(
            connector_snapshot(missing_tick)["reason_code"],
            "MT5_TICK_UNAVAILABLE",
        )
        missing_rates = FakeReadOnlyProvider()
        missing_rates.rates[missing_rates.TIMEFRAME_M1] = None
        document = connector_snapshot(missing_rates, timeframes=("M1",))
        self.assertEqual(document["reason_code"], "MT5_BAR_DATA_UNAVAILABLE")

    def test_conversion_only_market_number_is_rejected_without_conversion(self):
        class ConversionOnly:
            calls = 0

            def __float__(self):
                type(self).calls += 1
                return 2375.12

        value = ConversionOnly()
        provider = FakeReadOnlyProvider(source_tick=tick(bid=value))
        document = connector_snapshot(provider)
        self.assertEqual(document["reason_code"], "MT5_INVALID_TICK")
        self.assertEqual(ConversionOnly.calls, 0)


class MarketApiDashboardAndParityTests(unittest.TestCase):
    def _running_server(self, market_service=None):
        httpd = server.create_server(0, market_data_service=market_service)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        return httpd, thread

    @staticmethod
    def _request(httpd, method, path):
        connection = http.client.HTTPConnection("127.0.0.1", httpd.server_address[1], timeout=5)
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), body
        connection.close()
        return result

    def test_connection_health_and_snapshot_apis_with_disabled_default(self):
        httpd, thread = self._running_server()
        try:
            for path in server.MARKET_API_ROUTES:
                status, headers, body = self._request(httpd, "GET", path)
                self.assertEqual(status, 200)
                self.assertEqual(headers["Cache-Control"], "no-store, max-age=0")
                self.assertEqual(json.loads(body)["connection_status"], "MT5_DISABLED")
            status, _, body = self._request(httpd, "GET", "/api/market-connection")
            self.assertEqual(status, 200)
            self.assertEqual(
                set(json.loads(body)["stable_status_codes"]),
                set(market_data.STABLE_STATUS_CODES),
            )
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join(timeout=3)

    def test_enabled_market_apis_use_fake_provider_and_head_only_on_market_routes(self):
        configuration = MT5ReadOnlyConfiguration(enabled=True)
        market_service = MarketDataService(configuration, FakeReadOnlyProvider(), fixed_clock)
        httpd, thread = self._running_server(market_service)
        try:
            status, _, body = self._request(httpd, "GET", "/api/market-snapshot")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["reason_code"], "MT5_READ_ONLY_SNAPSHOT_VALID")
            for path in server.MARKET_API_ROUTES:
                status, headers, body = self._request(httpd, "HEAD", path)
                self.assertEqual(status, 200)
                self.assertEqual(body, b"")
                self.assertGreater(int(headers["Content-Length"]), 0)
            status, _, _ = self._request(httpd, "HEAD", "/api/strategy-registry")
            self.assertEqual(status, 405)
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join(timeout=3)

    def test_unsupported_methods_and_traversal_are_rejected(self):
        httpd, thread = self._running_server()
        try:
            for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
                status, headers, _ = self._request(httpd, method, "/api/market-snapshot")
                self.assertEqual(status, 405)
                self.assertEqual(headers["Allow"], "GET, HEAD")
            for path in ("/api/../market-snapshot", "/api/%2e%2e/market-snapshot", "/api/..%5cmarket-snapshot"):
                status, _, _ = self._request(httpd, "GET", path)
                self.assertIn(status, (400, 404))
        finally:
            httpd.shutdown(); httpd.server_close(); thread.join(timeout=3)

    def test_existing_api_compatibility_and_capability_accuracy(self):
        self.assertEqual(set(server.API_ROUTES), {
            "/api/health", "/api/version", "/api/capabilities", "/api/strategy-registry",
            "/api/demo/market-data", "/api/demo/result", "/api/demo/report",
        })
        manifest = capabilities.capability_manifest()
        self.assertTrue(manifest["local_mt5_read_only_connector_capability"])
        self.assertFalse(manifest["local_mt5_order_capability"])
        self.assertIn("Certified broker compatibility", manifest["not_implemented"])
        self.assertIn("News feeds", manifest["not_implemented"])

    def test_dashboard_accessibility_and_boundary_language(self):
        html = (APP_DIRECTORY / "static" / "index.html").read_text(encoding="utf-8")
        javascript = (APP_DIRECTORY / "static" / "app.js").read_text(encoding="utf-8")
        for wording in (
            'id="market-connection"', "Market connection", "Candidate aliases",
            "Broker-native tick", "UNKNOWN — no governed source",
            "No strategy is being applied to local MT5 data", "No order capability exists",
            "CLOSED", "FORMING", "M1, M5, H4 and D1 broker bar availability",
        ):
            self.assertIn(wording, html)
        self.assertIn('<table><caption>', html)
        self.assertIn('aria-live="polite"', html)
        self.assertIn('getJson("/api/market-snapshot")', javascript)

    def test_release_one_semantics_and_registry_vault_identities_are_unchanged(self):
        first = service.demo_result()
        second = service.demo_result()
        self.assertEqual(first, second)
        metadata = first["metadata"]
        self.assertEqual(metadata["input_data_hash"], "6cdbca208cd1029b90e5ed3494ab05a3b7042d224ed01293373fc173a85aee56")
        self.assertEqual(metadata["configuration_hash"], "3f4c513f275ca034af9fd2f4bbcb4ec382c361969d7706fbb6fb6d26fd26bbbd")
        self.assertEqual(metadata["strategy_definition_hash"], "e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955")
        self.assertEqual(metadata["engine_source_digest"], "f9f555d37e0820c39eb2afe1156fca4912d255debc23c7ab27c6111c31da3952")
        self.assertEqual(metadata["run_id"], "TRL-RUN-6922AEA31AE2630B4DA1")
        registry = service.strategy_registry_document()
        self.assertEqual(registry["vault"]["bundle_digest"], "62a549288ab65fd543f7550416c96f01d65a3ecf3f128aa7b31b2de1ddc21d7b")
        self.assertEqual(registry["vault"]["research_backlog_digest"], "5029263efdb47563852ba93733f6d84a2cb4c757d32e57a29a604b952ec75a63")
        self.assertEqual(registry["installed_executable_strategies"][0]["registry_record_digest"], "3cc2c876ad7c11d2244f9f71ab9a62cdc7f8baac0f5d3964173faa4d9e7e4878")
        self.assertEqual(
            (
                registry["installed_strategy_count"],
                registry["executable_research_strategy_count"],
                len(registry["research_backlog"]["entries"]),
            ),
            (1, 1, 9),
        )

    def test_validation_creates_no_cache_or_generated_artifacts(self):
        forbidden = []
        for path in BASE.rglob("*"):
            if path.is_dir() and path.name in {"__pycache__", ".pytest_cache", ".mypy_cache"}:
                forbidden.append(path)
            if path.is_file() and path.suffix in {".pyc", ".pyo"}:
                forbidden.append(path)
        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
