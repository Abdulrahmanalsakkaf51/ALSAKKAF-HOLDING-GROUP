"""Tests for alsakkaf_scalping_mt5.py (TRL-R2-012 contract Sections 2, 6, 7)."""

import unittest

from trading_lab_app import alsakkaf_scalping_mt5 as mt5a


def _passing_preflight_adapter():
    adapter = mt5a.fake_adapter()
    adapter.set_symbol("XAUUSDm", bid="1961.00", ask="1961.05", tick_time_utc="2026-08-03T00:00:00.000000Z")
    return adapter


class DisabledAdapterTests(unittest.TestCase):
    def test_disabled_adapter_denies_everything(self):
        adapter = mt5a.disabled_adapter()
        self.assertFalse(adapter.dependency_status()["available"])
        self.assertFalse(adapter.account_status()["available"])
        self.assertEqual(adapter.order_check({})["outcome"], "FAILED")
        self.assertEqual(adapter.order_send({})["outcome"], "REJECTED")
        self.assertEqual(adapter.discover_symbols("XAUUSD"), [])


class FakeAdapterTests(unittest.TestCase):
    def test_default_account_is_demo(self):
        adapter = mt5a.fake_adapter()
        self.assertEqual(adapter.account_status()["trade_mode"], mt5a.ACCOUNT_TRADE_MODE_DEMO)

    def test_owned_orders_filtered_by_magic(self):
        adapter = mt5a.fake_adapter()
        adapter.set_owned_orders([
            {"ticket": 1, "symbol": "XAUUSDm", "magic": 384512, "comment": "ALSAKKAF_SCALPING"},
            {"ticket": 2, "symbol": "XAUUSDm", "magic": 999, "comment": "OTHER_APP"},
        ])
        owned = adapter.owned_orders(384512)
        self.assertEqual([order["ticket"] for order in owned], [1])

    def test_order_check_and_send_are_recorded(self):
        adapter = mt5a.fake_adapter()
        adapter.order_check({"symbol": "XAUUSDm"})
        adapter.order_send({"symbol": "XAUUSDm", "volume": "0.10"})
        self.assertEqual([call for call, _ in adapter.calls], ["order_check", "order_send"])

    def test_queued_results_are_consumed_in_order(self):
        adapter = mt5a.fake_adapter()
        adapter.queue_check_result({"outcome": "FAILED", "retcode": 1, "comment": "no", "checked_at_utc": "x"})
        result = adapter.order_check({})
        self.assertEqual(result["outcome"], "FAILED")


class PreflightTests(unittest.TestCase):
    def test_all_twenty_checks_pass_for_a_healthy_demo_setup(self):
        adapter = _passing_preflight_adapter()
        result = mt5a.run_preflight(
            adapter, "XAUUSDm", max_spread_points=200, is_emergency_stopped=False,
            event_risk_blocked=False, daily_loss_ok=True, session_open=True, quote_age_seconds=1,
        )
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["checks"]), len(mt5a.PREFLIGHT_CHECK_IDS))

    def test_real_account_rejected_independent_of_every_other_check(self):
        adapter = _passing_preflight_adapter()
        adapter.account["trade_mode"] = 2
        adapter.account["trade_mode_name"] = "REAL"
        result = mt5a.run_preflight(
            adapter, "XAUUSDm", 200, False, False, True, True, 1,
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_ACCOUNT_NOT_PROVEN_DEMO")

    def test_contest_account_rejected(self):
        adapter = _passing_preflight_adapter()
        adapter.account["trade_mode"] = 1
        adapter.account["trade_mode_name"] = "CONTEST"
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, False, True, True, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_ACCOUNT_NOT_PROVEN_DEMO")

    def test_algo_trading_disabled_blocks(self):
        adapter = _passing_preflight_adapter()
        adapter.terminal["trade_allowed"] = False
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, False, True, True, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_ALGO_TRADING_DISABLED")

    def test_disconnected_terminal_blocks(self):
        adapter = _passing_preflight_adapter()
        adapter.terminal["connected"] = False
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, False, True, True, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_TERMINAL_NOT_CONNECTED")

    def test_stale_quote_blocks(self):
        adapter = _passing_preflight_adapter()
        result = mt5a.run_preflight(
            adapter, "XAUUSDm", 200, False, False, True, True,
            quote_age_seconds=mt5a.MAX_QUOTE_STALENESS_SECONDS + 1,
        )
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_QUOTE_STALE")

    def test_market_closed_blocks(self):
        adapter = _passing_preflight_adapter()
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, False, True, session_open=False, quote_age_seconds=1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_MARKET_CLOSED")

    def test_excessive_spread_blocks(self):
        adapter = mt5a.fake_adapter()
        adapter.set_symbol("XAUUSDm", bid="1961.00", ask="1965.00", tick_time_utc="2026-08-03T00:00:00.000000Z")
        result = mt5a.run_preflight(adapter, "XAUUSDm", max_spread_points=5, is_emergency_stopped=False, event_risk_blocked=False, daily_loss_ok=True, session_open=True, quote_age_seconds=1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_SPREAD_EXCEEDS_BOUND")

    def test_symbol_unavailable_blocks(self):
        adapter = mt5a.fake_adapter()
        result = mt5a.run_preflight(adapter, "UNMAPPEDX", 200, False, False, True, True, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_SYMBOL_UNAVAILABLE")

    def test_daily_loss_breach_blocks(self):
        adapter = _passing_preflight_adapter()
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, False, daily_loss_ok=False, session_open=True, quote_age_seconds=1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_DAILY_LIMIT_BREACHED")

    def test_emergency_stop_blocks(self):
        adapter = _passing_preflight_adapter()
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, is_emergency_stopped=True, event_risk_blocked=False, daily_loss_ok=True, session_open=True, quote_age_seconds=1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_EMERGENCY_STOP_ACTIVE")

    def test_manual_event_risk_block(self):
        adapter = _passing_preflight_adapter()
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, event_risk_blocked=True, daily_loss_ok=True, session_open=True, quote_age_seconds=1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_MANUAL_EVENT_RISK_BLOCK")

    def test_mt5_dependency_missing_blocks(self):
        adapter = mt5a.disabled_adapter()
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, False, True, True, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_MT5_DEPENDENCY_MISSING")

    def test_account_disconnected_blocks(self):
        adapter = _passing_preflight_adapter()
        adapter.account["available"] = False
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, False, True, True, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_ACCOUNT_UNAVAILABLE")


class SymbolDiscoveryTests(unittest.TestCase):
    def test_symbol_ambiguity_never_silently_resolved(self):
        adapter = mt5a.fake_adapter()
        adapter.set_symbol_candidates("XAUUSD", ["XAUUSDm", "XAUUSD.a", "GOLDrfd"])
        candidates = adapter.discover_symbols("XAUUSD")
        self.assertEqual(len(candidates), 3)
        # Discovery never returns a single "chosen" value -- the caller
        # (service.save_symbol_map) always requires an explicit selection.
        self.assertIsInstance(candidates, list)

    def test_instrument_aliases_cover_canonical_allowlist(self):
        from trading_lab_app.alsakkaf_scalping_data import CANONICAL_INSTRUMENTS
        for instrument in CANONICAL_INSTRUMENTS:
            self.assertIn(instrument, mt5a.INSTRUMENT_ALIASES)


class RealAdapterProviderAllowlistTests(unittest.TestCase):
    def test_disallowed_provider_method_raises(self):
        adapter = mt5a.RealScalpingMT5Adapter(provider=object())
        with self.assertRaises(mt5a.ScalpingMT5AdapterError):
            mt5a.RealScalpingMT5Adapter._call(object(), "not_allowlisted")

    def test_no_metatrader5_import_at_module_level(self):
        import sys
        self.assertNotIn("MetaTrader5", sys.modules)


if __name__ == "__main__":
    unittest.main()
