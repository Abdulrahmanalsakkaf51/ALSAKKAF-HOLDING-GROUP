"""Tests for the ALSAKKAF SCALPING HTTP surface (TRL-R2-012 contract
Section 18.2)."""

import json
from http.client import HTTPConnection
from pathlib import Path
import threading
import unittest

import alsakkaf_scalping_test_support as support
from trading_lab_app import server

APP_DIRECTORY = Path(__file__).resolve().parent / "trading_lab_app"


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
    httpd.server_close()


class ScalpingReadRoutesTests(unittest.TestCase):
    def setUp(self):
        self.service, self.adapter, self.mode_svc = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        self.httpd, self.thread = _running_server(scalping_service_instance=self.service)
        self.addCleanup(lambda: _stop_server(self.httpd, self.thread))
        self.port = self.httpd.server_address[1]

    def test_status_returns_200_and_action_token(self):
        status, _headers, body = _request(self.port, "GET", "/api/scalping-status")
        self.assertEqual(status, 200)
        document = json.loads(body)
        self.assertEqual(document["product_state"], "OFF")
        self.assertIn("action_token", document)
        self.assertTrue(document["action_token"])

    def test_cycles_owned_orders_positions_and_journal_read_only(self):
        for path in (
            "/api/scalping-cycles", "/api/scalping-owned-orders",
            "/api/scalping-owned-positions", "/api/scalping-journal",
        ):
            with self.subTest(path=path):
                status, _headers, _body = _request(self.port, "GET", path)
                self.assertEqual(status, 200)

    def test_preflight_route(self):
        status, _headers, body = _request(self.port, "GET", "/api/scalping-preflight/XAUUSD")
        self.assertIn(status, (200, 400))

    def test_preflight_route_rejects_non_canonical_instrument(self):
        status, _headers, _body = _request(self.port, "GET", "/api/scalping-preflight/NOTREAL")
        self.assertEqual(status, 404)

    def test_symbol_candidates_route(self):
        status, _headers, body = _request(self.port, "GET", "/api/scalping-symbol-candidates/XAUUSD")
        self.assertEqual(status, 200)
        self.assertIn("candidates", json.loads(body))

    def test_cycle_detail_not_found(self):
        status, _headers, _body = _request(self.port, "GET", "/api/scalping-cycle/cyc_" + "0" * 32)
        self.assertEqual(status, 404)

    def test_head_matches_get_status(self):
        get_status, _h1, _b1 = _request(self.port, "GET", "/api/scalping-status")
        head_status, _h2, head_body = _request(self.port, "HEAD", "/api/scalping-status")
        self.assertEqual(get_status, head_status)
        self.assertEqual(head_body, b"")


class ScalpingMutationRouteTests(unittest.TestCase):
    def setUp(self):
        self.service, self.adapter, self.mode_svc = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        self.httpd, self.thread = _running_server(scalping_service_instance=self.service)
        self.addCleanup(lambda: _stop_server(self.httpd, self.thread))
        self.port = self.httpd.server_address[1]
        self.token = self.httpd.scalping_action_token

    def test_get_on_mutation_route_is_405_with_allow_post(self):
        status, headers, _body = _request(self.port, "GET", "/api/scalping-pause")
        self.assertEqual(status, 405)
        self.assertEqual(headers["Allow"], "POST")

    def test_post_without_token_is_403(self):
        status, _headers, _body = _request(self.port, "POST", "/api/scalping-pause", body=b"{}")
        self.assertEqual(status, 403)

    def test_post_with_wrong_token_is_403(self):
        status, _headers, _body = _request(
            self.port, "POST", "/api/scalping-pause",
            headers={"X-Scalping-Action-Token": "wrong-token"}, body=b"{}",
        )
        self.assertEqual(status, 403)

    def test_post_with_correct_token_succeeds(self):
        status, _headers, body = _request(
            self.port, "POST", "/api/scalping-resume",
            headers={"X-Scalping-Action-Token": self.token, "Content-Type": "application/json"}, body=b"{}",
        )
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["product_state"], "ANALYZE_ONLY")

    def test_post_to_unregistered_path_is_405(self):
        status, headers, _body = _request(
            self.port, "POST", "/api/scalping-not-a-real-route",
            headers={"X-Scalping-Action-Token": self.token}, body=b"{}",
        )
        self.assertEqual(status, 405)

    def test_save_symbol_map_via_post(self):
        status, _headers, body = _request(
            self.port, "POST", "/api/scalping-save-symbol-map",
            headers={"X-Scalping-Action-Token": self.token, "Content-Type": "application/json"},
            body=json.dumps({"canonical_instrument": "EURUSD", "broker_symbol": "EURUSDm"}).encode("utf-8"),
        )
        self.assertEqual(status, 200)

    def test_oversized_body_rejected(self):
        oversized_body = json.dumps({"padding": "x" * (70 * 1024)}).encode("utf-8")
        status, _headers, _body = _request(
            self.port, "POST", "/api/scalping-configure-profile",
            headers={"X-Scalping-Action-Token": self.token}, body=oversized_body,
        )
        self.assertEqual(status, 413)


class LocalHostOnlyTests(unittest.TestCase):
    def test_non_local_host_header_rejected_for_status(self):
        service, _adapter, _mode = support.make_service()
        httpd, thread = _running_server(scalping_service_instance=service)
        self.addCleanup(lambda: _stop_server(httpd, thread))
        port = httpd.server_address[1]
        connection = HTTPConnection("127.0.0.1", port, timeout=5)
        try:
            connection.request("GET", "/api/scalping-status", headers={"Host": "evil.example.com"})
            response = connection.getresponse()
            self.assertEqual(response.status, 421)
        finally:
            connection.close()

    def test_bind_host_is_loopback_only(self):
        self.assertEqual(server.BIND_HOST, "127.0.0.1")


class DashboardStaticSurfaceTests(unittest.TestCase):
    def test_scalping_section_present_in_index_html(self):
        html = (APP_DIRECTORY / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="alsakkaf-scalping"', html)
        self.assertIn("DEMO ACCOUNT ONLY", html)
        self.assertIn("LIVE MONEY LOCKED", html)
        self.assertIn("EMERGENCY STOP", html)

    def test_no_innerhtml_in_render_scalping(self):
        js = (APP_DIRECTORY / "static" / "app.js").read_text(encoding="utf-8")
        start = js.index("function renderScalping")
        end = js.index("\n}\n", start)
        self.assertNotIn("innerHTML", js[start:end])

    def test_no_innerhtml_in_wire_scalping_controls(self):
        js = (APP_DIRECTORY / "static" / "app.js").read_text(encoding="utf-8")
        start = js.index("function wireScalpingControls")
        end = js.index("\n}\n", start)
        self.assertNotIn("innerHTML", js[start:end])

    def test_dashboard_mutations_call_local_endpoints_only(self):
        js = (APP_DIRECTORY / "static" / "app.js").read_text(encoding="utf-8")
        start = js.index("async function postScalping")
        end = js.index("\n}\n", start)
        snippet = js[start:end]
        self.assertIn("fetch(path", snippet)
        self.assertNotIn("http://", snippet)
        self.assertNotIn("https://", snippet)


if __name__ == "__main__":
    unittest.main()
