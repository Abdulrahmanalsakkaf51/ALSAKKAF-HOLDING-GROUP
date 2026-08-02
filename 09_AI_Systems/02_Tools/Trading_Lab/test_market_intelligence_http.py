"""Tests for the TRL-R2-010 read-only Market Intelligence HTTP surface
(server.py / service.py). Mirrors test_basket_execution_http.py exactly."""

from http.client import HTTPConnection
from pathlib import Path
import threading
import unittest

from trading_lab_app import market_intelligence_service as svc
from trading_lab_app import mode_service as ms
from trading_lab_app.market_intelligence_journal import in_memory_mi_journal_writer
from trading_lab_app import server

import mi_test_support as support


APP_DIRECTORY = Path(__file__).resolve().parent / "trading_lab_app"


def _request(port, method, path):
    connection = HTTPConnection("127.0.0.1", port, timeout=5)
    try:
        connection.request(method, path, headers={"Host": "127.0.0.1"})
        response = connection.getresponse()
        body = response.read()
        return response.status, dict(response.getheaders()), body
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


class MarketIntelligenceRoutesAreReadOnlyTests(unittest.TestCase):
    def setUp(self):
        mode = ms.in_memory_mode_service(subsystem_builder=lambda _m: None)
        mode.request_transition("RESEARCH", actor="t", actor_channel="LOCAL_OPERATOR")
        self.mi_service = svc.MarketIntelligenceService(mode_service=mode, journal=in_memory_mi_journal_writer())
        path = support.write_temp_json(support.analysis_envelope())
        try:
            self.result = self.mi_service.analyze_market_snapshot(path)
        finally:
            import os
            os.unlink(path)
        self.httpd, self.thread = _running_server(mode_service=mode, market_intelligence_service_instance=self.mi_service)
        self.addCleanup(lambda: _stop_server(self.httpd, self.thread))
        self.port = self.httpd.server_address[1]

    def test_get_market_intelligence_status_returns_200(self):
        status, _, body = _request(self.port, "GET", "/api/market-intelligence-status")
        self.assertEqual(status, 200)
        self.assertIn(b"RESEARCH", body)

    def test_get_market_opportunities_returns_200_with_recorded_opportunity(self):
        status, _, body = _request(self.port, "GET", "/api/market-opportunities")
        self.assertEqual(status, 200)
        self.assertIn(self.result["opportunity"]["opportunity_id"].encode("ascii"), body)

    def test_get_market_opportunity_detail_returns_200(self):
        opportunity_id = self.result["opportunity"]["opportunity_id"]
        status, _, body = _request(self.port, "GET", "/api/market-opportunity/" + opportunity_id)
        self.assertEqual(status, 200)
        self.assertIn(b'"found":true', body)

    def test_get_unknown_opportunity_returns_404(self):
        status, _, body = _request(self.port, "GET", "/api/market-opportunity/opp_" + "0" * 32)
        self.assertEqual(status, 404)
        self.assertIn(b"MARKET_INTELLIGENCE_OPPORTUNITY_NOT_FOUND", body)

    def test_get_malformed_opportunity_id_path_never_crashes(self):
        for suffix in ("not-a-valid-id", "opp_short", "..%2F..%2Fetc%2Fpasswd", "opp_" + "G" * 32):
            with self.subTest(suffix=suffix):
                status, _, _ = _request(self.port, "GET", "/api/market-opportunity/" + suffix)
                self.assertIn(status, (400, 404))

    def test_get_virtual_opportunities_returns_200(self):
        status, _, body = _request(self.port, "GET", "/api/virtual-opportunities")
        self.assertEqual(status, 200)
        self.assertIn(b"virtual_opportunities", body)

    def test_get_market_intelligence_telemetry_returns_200_empty(self):
        status, _, body = _request(self.port, "GET", "/api/market-intelligence-telemetry")
        self.assertEqual(status, 200)
        self.assertIn(b'"telemetry":[]', body)

    def test_head_market_intelligence_status_returns_200_with_no_body(self):
        status, _, body = _request(self.port, "HEAD", "/api/market-intelligence-status")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")

    def test_head_market_opportunity_detail_returns_200_with_no_body(self):
        opportunity_id = self.result["opportunity"]["opportunity_id"]
        status, _, body = _request(self.port, "HEAD", "/api/market-opportunity/" + opportunity_id)
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")

    def test_post_market_intelligence_status_returns_405(self):
        status, headers, _ = _request(self.port, "POST", "/api/market-intelligence-status")
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "GET, HEAD")

    def test_post_market_opportunities_returns_405(self):
        status, headers, _ = _request(self.port, "POST", "/api/market-opportunities")
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "GET, HEAD")

    def test_post_market_opportunity_detail_returns_405(self):
        opportunity_id = self.result["opportunity"]["opportunity_id"]
        status, headers, _ = _request(self.port, "POST", "/api/market-opportunity/" + opportunity_id)
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "GET, HEAD")

    def test_put_virtual_opportunities_returns_405(self):
        status, _, _ = _request(self.port, "PUT", "/api/virtual-opportunities")
        self.assertEqual(status, 405)

    def test_patch_market_intelligence_telemetry_returns_405(self):
        status, _, _ = _request(self.port, "PATCH", "/api/market-intelligence-telemetry")
        self.assertEqual(status, 405)

    def test_delete_market_opportunities_returns_405(self):
        status, _, _ = _request(self.port, "DELETE", "/api/market-opportunities")
        self.assertEqual(status, 405)

    def test_no_mutation_route_exists_for_analyze_preview_or_record(self):
        for path in ("/api/analyze-market-snapshot", "/api/preview-opportunity-basket", "/api/record-opportunity-outcome"):
            status, _, _ = _request(self.port, "GET", path)
            self.assertEqual(status, 404)
            status, _, _ = _request(self.port, "POST", path)
            self.assertEqual(status, 405)

    def test_query_parameter_cannot_trigger_mutation(self):
        status, _, body = _request(self.port, "GET", "/api/market-intelligence-status?mode=RESEARCH&mutate=true")
        self.assertEqual(status, 200)
        self.assertIn(b"RESEARCH", body)


class DisabledDefaultTests(unittest.TestCase):
    def test_default_server_has_disabled_market_intelligence_service(self):
        httpd, thread = _running_server()
        try:
            port = httpd.server_address[1]
            status, _, body = _request(port, "GET", "/api/market-intelligence-status")
            self.assertEqual(status, 200)
            self.assertIn(b'"enabled":false', body)
        finally:
            _stop_server(httpd, thread)

    def test_off_mode_still_exposes_every_read_only_route(self):
        httpd, thread = _running_server()
        try:
            port = httpd.server_address[1]
            for path in (
                "/api/market-intelligence-status", "/api/market-opportunities",
                "/api/virtual-opportunities", "/api/market-intelligence-telemetry",
            ):
                status, _, _ = _request(port, "GET", path)
                self.assertEqual(status, 200, path)
        finally:
            _stop_server(httpd, thread)


class DashboardContentTests(unittest.TestCase):
    def test_dashboard_html_contains_required_banners(self):
        html = (APP_DIRECTORY / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("RESEARCH ONLY", html)
        self.assertIn("LIVE EXECUTION DISABLED", html)
        self.assertIn("NOT FINANCIAL ADVICE", html)
        self.assertIn("EXECUTION_HANDOFF_NOT_APPROVED", html)

    def test_dashboard_js_never_uses_innerhtml_for_market_intelligence_rendering(self):
        js = (APP_DIRECTORY / "static" / "app.js").read_text(encoding="utf-8")
        start = js.index("function renderMarketIntelligence")
        end = js.index("async function loadMarketIntelligence")
        section = js[start:end]
        self.assertNotIn("innerHTML", section)


if __name__ == "__main__":
    unittest.main()
