"""Tests for the Phase 5 read-only HTTP surface (server.py / service.py)."""

from http.client import HTTPConnection
from pathlib import Path
import threading
import unittest

from trading_lab_app import mode_service as ms
from trading_lab_app import mt5_execution_adapter as maa
from trading_lab_app import mt5_execution_journal as mej
from trading_lab_app import mt5_execution_service as mes
from trading_lab_app import server


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


class ExecutionRoutesAreReadOnlyTests(unittest.TestCase):
    def setUp(self):
        mode = ms.in_memory_mode_service(subsystem_builder=lambda _m: None)
        mode.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
        adapter = maa.FakeExecutionAdapter()
        adapter.set_symbol("XAUUSD")
        service = mes.ExecutionService(
            adapter=adapter, mode_service=mode, journal=mej.in_memory_journal_writer(),
            account_fingerprint=mes.AccountFingerprintConfiguration(login=1, company="C", server="S"),
        )
        self.httpd, self.thread = _running_server(mode_service=mode, execution_service=service)
        self.addCleanup(lambda: _stop_server(self.httpd, self.thread))
        self.port = self.httpd.server_address[1]

    def test_get_execution_status_returns_200(self):
        status, _, body = _request(self.port, "GET", "/api/mt5-execution-status")
        self.assertEqual(status, 200)
        self.assertIn(b"MT5_DEMO_MANUAL", body)

    def test_get_account_status_returns_200_and_redacted(self):
        status, _, body = _request(self.port, "GET", "/api/mt5-account-status")
        self.assertEqual(status, 200)
        self.assertNotIn(b'"login"', body)

    def test_get_terminal_status_returns_200(self):
        status, _, _ = _request(self.port, "GET", "/api/mt5-terminal-status")
        self.assertEqual(status, 200)

    def test_get_execution_journal_returns_200(self):
        status, _, body = _request(self.port, "GET", "/api/execution-journal")
        self.assertEqual(status, 200)
        self.assertIn(b"events", body)

    def test_head_execution_status_returns_200_with_no_body(self):
        status, _, body = _request(self.port, "HEAD", "/api/mt5-execution-status")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")

    def test_post_execution_status_returns_405(self):
        status, headers, _ = _request(self.port, "POST", "/api/mt5-execution-status")
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "GET, HEAD")

    def test_put_execution_journal_returns_405(self):
        status, _, _ = _request(self.port, "PUT", "/api/execution-journal")
        self.assertEqual(status, 405)

    def test_patch_execution_status_returns_405(self):
        status, _, _ = _request(self.port, "PATCH", "/api/mt5-execution-status")
        self.assertEqual(status, 405)

    def test_delete_execution_status_returns_405(self):
        status, _, _ = _request(self.port, "DELETE", "/api/mt5-execution-status")
        self.assertEqual(status, 405)

    def test_no_route_exists_for_order_check_or_send(self):
        for path in ("/api/order-check", "/api/order-send", "/api/execute-demo", "/api/confirm"):
            status, _, _ = _request(self.port, "GET", path)
            self.assertEqual(status, 404)
            status, _, _ = _request(self.port, "POST", path)
            self.assertEqual(status, 405)


class DisabledDefaultTests(unittest.TestCase):
    def test_default_server_has_disabled_execution_service(self):
        httpd, thread = _running_server()
        try:
            port = httpd.server_address[1]
            status, _, body = _request(port, "GET", "/api/mt5-execution-status")
            self.assertEqual(status, 200)
            self.assertIn(b'"enabled":false', body)
        finally:
            _stop_server(httpd, thread)


class DashboardContentTests(unittest.TestCase):
    def test_dashboard_html_contains_required_banners(self):
        html = (APP_DIRECTORY / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("LIVE EXECUTION DISABLED", html)
        self.assertIn("MANUAL CONFIRMATION REQUIRED", html)
        self.assertIn("DEMO ONLY", html)
        self.assertIn("SMA-001", html)
        self.assertIn("FIB-001", html)
        self.assertIn('id="mt5-execution"', html)

    def test_no_innerhtml_added_for_mt5_panel(self):
        js = (APP_DIRECTORY / "static" / "app.js").read_text(encoding="utf-8")
        # The MT5 panel's own render function must not use innerHTML.
        start = js.index("function renderMt5Execution")
        end = js.index("\n\n", start)
        self.assertNotIn("innerHTML", js[start:end])


if __name__ == "__main__":
    unittest.main()
