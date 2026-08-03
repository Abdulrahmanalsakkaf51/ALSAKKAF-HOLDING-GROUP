"""Tests for the TRL-R2-013 server-authoritative live-analysis path:
server-side bar/quote fetch, ``ScalpingRuntime.analyze_now``, and bounded
read-only monitoring. Uses only fake adapters -- no real MT5 order is ever
sent, and neither ``order_check`` nor ``order_send`` is ever exercised in
this module (every test stays in ``ANALYZE_ONLY``, never ``DEMO_AUTO``)."""

import json
import threading
import unittest
from datetime import datetime, timezone
from http.client import HTTPConnection

import alsakkaf_scalping_test_support as support
from trading_lab_app import alsakkaf_scalping_mt5 as mt5a
from trading_lab_app import server
from trading_lab_app.alsakkaf_scalping_runtime import ScalpingRuntime, ScalpingRuntimeError


def _seed_bars(adapter, broker_symbol):
    entry_bars = support.make_chop_then_breakout_bars()  # 60 bars, matches MIN_ENTRY_BARS
    confirmation_bars = support.make_flat_choppy_bars(30)
    adapter.set_bars(broker_symbol, "M1", entry_bars)
    adapter.set_bars(broker_symbol, "M5", confirmation_bars)
    return entry_bars, confirmation_bars


def _analyze_only_runtime(**kwargs):
    service, adapter, mode_svc = support.make_service(target_mode="MT5_DEMO_AUTOMATED", **kwargs)
    service.request_state_change("ANALYZE_ONLY")
    runtime = ScalpingRuntime(service)
    return runtime, service, adapter, mode_svc


class FetchCompletedBarsTests(unittest.TestCase):
    def test_disabled_adapter_reports_unavailable(self):
        adapter = mt5a.disabled_adapter()
        result = adapter.fetch_completed_bars("XAUUSDm", "M1", 10)
        self.assertFalse(result["available"])
        self.assertEqual(result["reason_code"], "ADAPTER_DISABLED")

    def test_fake_adapter_returns_exact_tail_and_never_fabricates_shortfall(self):
        adapter = mt5a.fake_adapter()
        bars = support.make_flat_choppy_bars(60)
        adapter.set_bars("XAUUSDm", "M1", bars)
        result = adapter.fetch_completed_bars("XAUUSDm", "M1", 60)
        self.assertTrue(result["available"])
        self.assertEqual(len(result["bars"]), 60)
        self.assertEqual(result["bars"][-1]["close"], bars[-1]["close"])

    def test_fake_adapter_insufficient_history(self):
        adapter = mt5a.fake_adapter()
        adapter.set_bars("XAUUSDm", "M1", support.make_flat_choppy_bars(10))
        result = adapter.fetch_completed_bars("XAUUSDm", "M1", 60)
        self.assertFalse(result["available"])
        self.assertEqual(result["reason_code"], "HISTORY_INSUFFICIENT")

    def test_real_adapter_uses_start_pos_one_to_exclude_forming_bar(self):
        """Contract Section 5/8.1: the currently-forming bar must never be
        used as a closed bar. ``start_pos=1`` in ``copy_rates_from_pos`` is
        the only mechanism that guarantees this -- proven here against a
        fake MetaTrader5-shaped provider object (never the real package)."""
        calls = []

        class _FakeProvider:
            TIMEFRAME_M1 = 1
            TIMEFRAME_M5 = 5
            TIMEFRAME_M15 = 15
            TIMEFRAME_H1 = 60
            TIMEFRAME_H4 = 240

            def initialize(self, timeout=None):
                return True

            def shutdown(self):
                return None

            def copy_rates_from_pos(self, symbol, timeframe, start_pos, count):
                calls.append((symbol, timeframe, start_pos, count))
                base = 1_700_000_000
                return [
                    {"time": base + i * 60, "open": 1900.0 + i, "high": 1901.0 + i, "low": 1899.0 + i, "close": 1900.5 + i}
                    for i in range(count)
                ]

        adapter = mt5a.RealScalpingMT5Adapter(provider=_FakeProvider())
        result = adapter.fetch_completed_bars("XAUUSDm", "M1", 5)
        self.assertTrue(result["available"])
        self.assertEqual(len(result["bars"]), 5)
        self.assertEqual(calls, [("XAUUSDm", 1, 1, 5)])

    def test_real_adapter_rejects_unsupported_timeframe(self):
        adapter = mt5a.RealScalpingMT5Adapter(provider=object())
        result = adapter.fetch_completed_bars("XAUUSDm", "M30", 5)
        self.assertFalse(result["available"])
        self.assertEqual(result["reason_code"], "HISTORY_INSUFFICIENT")


class AnalyzeNowTests(unittest.TestCase):
    def test_symbol_not_mapped(self):
        runtime, service, adapter, _mode = _analyze_only_runtime()
        result = runtime.analyze_now("EURUSD")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason_code"], "SYMBOL_NOT_MAPPED")

    def test_terminal_not_connected(self):
        runtime, service, adapter, _mode = _analyze_only_runtime()
        adapter.terminal["connected"] = False
        result = runtime.analyze_now("XAUUSD")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason_code"], "TERMINAL_NOT_CONNECTED")

    def test_quote_unavailable_when_no_symbol_set(self):
        runtime, service, adapter, _mode = _analyze_only_runtime()
        adapter.symbols.pop("XAUUSDm", None)
        result = runtime.analyze_now("XAUUSD")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason_code"], "QUOTE_UNAVAILABLE")

    def test_quote_unavailable_when_stale(self):
        runtime, service, adapter, _mode = _analyze_only_runtime(
            clock=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        adapter.set_symbol("XAUUSDm", tick_time_utc="2020-01-01T00:00:00.000000Z")
        result = runtime.analyze_now("XAUUSD")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason_code"], "QUOTE_UNAVAILABLE")

    def test_history_insufficient_when_no_bars_seeded(self):
        runtime, service, adapter, _mode = _analyze_only_runtime()
        result = runtime.analyze_now("XAUUSD")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason_code"], "HISTORY_INSUFFICIENT")

    def test_successful_analysis_never_calls_order_check_or_order_send(self):
        runtime, service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        result = runtime.analyze_now("XAUUSD")
        self.assertTrue(result["ok"])
        self.assertIn("evaluation", result)
        self.assertIn("total_score", result["evaluation"])
        self.assertEqual([call for call in adapter.calls if call[0] in ("order_check", "order_send")], [])

    def test_analysis_cached_and_retrievable_via_latest_analysis(self):
        runtime, service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        runtime.analyze_now("XAUUSD")
        cached = runtime.latest_analysis("XAUUSD")
        self.assertTrue(cached["ok"])

    def test_latest_analysis_before_any_run_reports_analysis_not_run(self):
        runtime, _service, _adapter, _mode = _analyze_only_runtime()
        cached = runtime.latest_analysis("XAUUSD")
        self.assertFalse(cached["ok"])
        self.assertEqual(cached["reason_code"], "ANALYSIS_NOT_RUN")

    def test_off_state_blocks_analysis(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        _seed_bars(adapter, "XAUUSDm")
        runtime = ScalpingRuntime(service)  # still OFF -- never transitioned
        result = runtime.analyze_now("XAUUSD")
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason_code"], "ANALYSIS_NOT_RUN")
        self.assertEqual(result["detail"], "SCALPING_STATE_FORBIDS_EXECUTION")


class MonitoringLifecycleTests(unittest.TestCase):
    def test_interval_bounds_rejected(self):
        runtime, _service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        with self.assertRaises(ScalpingRuntimeError):
            runtime.start_monitoring("XAUUSD", interval_seconds=4)
        with self.assertRaises(ScalpingRuntimeError):
            runtime.start_monitoring("XAUUSD", interval_seconds=301)

    def test_start_then_stop_lifecycle_leaves_no_thread(self):
        runtime, _service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        status = runtime.start_monitoring("XAUUSD", interval_seconds=5)
        self.assertTrue(status["running"])
        thread = runtime._monitor_thread
        self.assertTrue(thread.is_alive())
        stopped = runtime.stop_monitoring()
        self.assertFalse(stopped["running"])
        thread.join(timeout=2)
        self.assertFalse(thread.is_alive())

    def test_no_overlapping_monitoring_start(self):
        runtime, _service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        runtime.start_monitoring("XAUUSD", interval_seconds=5)
        try:
            with self.assertRaises(ScalpingRuntimeError) as ctx:
                runtime.start_monitoring("XAUUSD", interval_seconds=5)
            self.assertEqual(ctx.exception.reason_code, "SCALPING_MONITORING_ALREADY_RUNNING")
        finally:
            runtime.stop_monitoring()

    def test_terminal_disconnect_blocks_monitoring_start(self):
        runtime, _service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        adapter.terminal["connected"] = False
        with self.assertRaises(ScalpingRuntimeError) as ctx:
            runtime.start_monitoring("XAUUSD", interval_seconds=5)
        self.assertEqual(ctx.exception.reason_code, "SCALPING_MONITORING_PREFLIGHT_FAILED")

    def test_non_demo_account_stops_monitoring_safety_check(self):
        runtime, _service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        adapter.account["trade_mode"] = 2  # ACCOUNT_TRADE_MODE_REAL
        adapter.account["trade_mode_name"] = "REAL"
        reason = runtime._monitoring_safety_check("XAUUSD")
        self.assertEqual(reason, "ACCOUNT_NOT_DEMO")

    def test_product_off_stops_monitoring_safety_check(self):
        runtime, service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        service.request_state_change("OFF")
        reason = runtime._monitoring_safety_check("XAUUSD")
        self.assertEqual(reason, "SCALPING_STATE_FORBIDS_EXECUTION")

    def test_emergency_stop_stops_monitoring_safety_check(self):
        runtime, service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        service.request_state_change("EMERGENCY_STOP")
        reason = runtime._monitoring_safety_check("XAUUSD")
        self.assertEqual(reason, "SCALPING_EMERGENCY_STOP_ACTIVE")

    def test_operating_mode_change_stops_monitoring_safety_check(self):
        runtime, service, adapter, mode_svc = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        mode_svc.request_transition("OFF", actor="tester", actor_channel="LOCAL_OPERATOR")
        reason = runtime._monitoring_safety_check("XAUUSD")
        self.assertEqual(reason, "OPERATING_MODE_NOT_RESEARCH")

    def test_shutdown_stops_running_monitor(self):
        runtime, _service, adapter, _mode = _analyze_only_runtime()
        _seed_bars(adapter, "XAUUSDm")
        runtime.start_monitoring("XAUUSD", interval_seconds=5)
        runtime.shutdown()
        self.assertFalse(runtime.monitoring_status()["running"])


def _request(port, method, path, headers=None, body=None):
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, body=body, headers=dict(headers or {}, Host="127.0.0.1"))
        response = connection.getresponse()
        payload = response.read()
        return response.status, dict(response.getheaders()), payload
    finally:
        connection.close()


def _running_server(**kwargs):
    httpd = server.create_server(port=0, **kwargs)
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.05})
    thread.daemon = False
    thread.start()
    return httpd, thread


def _stop_server(httpd, thread):
    httpd.shutdown()
    thread.join(timeout=5)
    httpd.server_close()


class AnalyzeNowHttpRouteTests(unittest.TestCase):
    def setUp(self):
        self.service, self.adapter, self.mode_svc = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        self.service.request_state_change("ANALYZE_ONLY")
        _seed_bars(self.adapter, "XAUUSDm")
        self.httpd, self.thread = _running_server(scalping_service_instance=self.service)
        self.addCleanup(lambda: _stop_server(self.httpd, self.thread))
        self.port = self.httpd.server_address[1]
        self.token = self.httpd.scalping_action_token

    def _post(self, path, payload):
        return _request(
            self.port, "POST", path,
            headers={"X-Scalping-Action-Token": self.token, "Content-Type": "application/json"},
            body=json.dumps(payload).encode("utf-8"),
        )

    def test_analyze_now_succeeds(self):
        status, _headers, body = self._post("/api/scalping-analyze-now", {"canonical_instrument": "XAUUSD"})
        self.assertEqual(status, 200)
        document = json.loads(body)
        self.assertTrue(document["ok"])

    def test_analyze_now_rejects_client_market_data(self):
        for key in ("entry_bars", "confirmation_bars", "current_price", "spread"):
            with self.subTest(key=key):
                payload = {"canonical_instrument": "XAUUSD", key: "1900.0"}
                status, _headers, body = self._post("/api/scalping-analyze-now", payload)
                self.assertEqual(status, 400)
                self.assertEqual(json.loads(body)["error"], "SCALPING_CLIENT_MARKET_DATA_REJECTED")

    def test_run_cycle_route_no_longer_registered(self):
        status, _headers, _body = self._post("/api/scalping-run-cycle", {"canonical_instrument": "XAUUSD"})
        self.assertEqual(status, 405)

    def test_live_status_route(self):
        status, _headers, body = _request(self.port, "GET", "/api/scalping-live-status?instrument=XAUUSD")
        self.assertEqual(status, 200)
        document = json.loads(body)
        self.assertIn("mt5_connected", document)
        self.assertIn("journal_health", document)

    def test_live_status_rejects_non_canonical_instrument(self):
        status, _headers, _body = _request(self.port, "GET", "/api/scalping-live-status?instrument=NOTREAL")
        self.assertEqual(status, 400)

    def test_configuration_route(self):
        status, _headers, body = _request(self.port, "GET", "/api/scalping-configuration")
        self.assertEqual(status, 200)
        self.assertIn("profiles", json.loads(body))

    def test_monitoring_status_route(self):
        status, _headers, body = _request(self.port, "GET", "/api/scalping-monitoring-status")
        self.assertEqual(status, 200)
        self.assertIn("running", json.loads(body))

    def test_monitoring_start_and_stop_routes(self):
        status, _headers, body = self._post("/api/scalping-monitoring-start", {"canonical_instrument": "XAUUSD", "interval_seconds": 5})
        self.assertEqual(status, 200)
        self.assertTrue(json.loads(body)["running"])
        status, _headers, body = self._post("/api/scalping-monitoring-stop", {})
        self.assertEqual(status, 200)
        self.assertFalse(json.loads(body)["running"])

    def test_save_configuration_route_persists_profile(self):
        status, _headers, body = self._post("/api/scalping-save-configuration", {
            "canonical_instrument": "XAUUSD", "profile_id": "ALSAKKAF_INTRADAY",
        })
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["profiles"]["XAUUSD"], "ALSAKKAF_INTRADAY")

    def test_recheck_route(self):
        status, _headers, body = self._post("/api/scalping-recheck", {})
        self.assertEqual(status, 200)
        document = json.loads(body)
        self.assertIn("mt5_connected", document)


if __name__ == "__main__":
    unittest.main()
