"""Tests for the Phase 6 (TRL-R2-009) read-only basket HTTP surface
(server.py / service.py). Mirrors test_mt5_execution_http.py exactly."""

from http.client import HTTPConnection
from pathlib import Path
import threading
import unittest

from trading_lab_app import basket_execution_service as bes
from trading_lab_app import mode_service as ms
from trading_lab_app import mt5_execution_adapter as maa
from trading_lab_app import mt5_execution_journal as mej
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


class BasketRoutesAreReadOnlyTests(unittest.TestCase):
    def setUp(self):
        mode = ms.in_memory_mode_service(subsystem_builder=lambda _m: None)
        mode.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
        adapter = maa.FakeExecutionAdapter()
        adapter.set_symbol("XAUUSD")
        basket_service = bes.BasketExecutionService(
            adapter=adapter, mode_service=mode, journal=mej.in_memory_journal_writer(),
            account_fingerprint=None,
        )
        self.httpd, self.thread = _running_server(mode_service=mode, basket_service=basket_service)
        self.addCleanup(lambda: _stop_server(self.httpd, self.thread))
        self.port = self.httpd.server_address[1]

    def test_get_basket_execution_status_returns_200(self):
        status, _, body = _request(self.port, "GET", "/api/basket-execution-status")
        self.assertEqual(status, 200)
        self.assertIn(b"MT5_DEMO_MANUAL", body)

    def test_get_execution_baskets_returns_200_empty_list(self):
        status, _, body = _request(self.port, "GET", "/api/execution-baskets")
        self.assertEqual(status, 200)
        self.assertIn(b'"baskets":[]', body)

    def test_get_execution_basket_journal_returns_200(self):
        status, _, body = _request(self.port, "GET", "/api/execution-basket-journal")
        self.assertEqual(status, 200)
        self.assertIn(b"events", body)

    def test_get_unknown_basket_id_returns_404(self):
        status, _, body = _request(self.port, "GET", "/api/execution-basket/" + "bsk_" + "0" * 32)
        self.assertEqual(status, 404)
        self.assertIn(b"BASKET_NOT_FOUND", body)

    def test_get_malformed_basket_id_path_never_crashes(self):
        for suffix in ("not-a-valid-id", "bsk_short", "..%2F..%2Fetc%2Fpasswd", "bsk_" + "G" * 32):
            with self.subTest(suffix=suffix):
                status, _, _ = _request(self.port, "GET", "/api/execution-basket/" + suffix)
                self.assertIn(status, (400, 404))

    def test_head_basket_execution_status_returns_200_with_no_body(self):
        status, _, body = _request(self.port, "HEAD", "/api/basket-execution-status")
        self.assertEqual(status, 200)
        self.assertEqual(body, b"")

    def test_post_basket_execution_status_returns_405(self):
        status, headers, _ = _request(self.port, "POST", "/api/basket-execution-status")
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "GET, HEAD")

    def test_post_execution_baskets_returns_405(self):
        status, headers, _ = _request(self.port, "POST", "/api/execution-baskets")
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "GET, HEAD")

    def test_post_execution_basket_detail_returns_405(self):
        status, headers, _ = _request(self.port, "POST", "/api/execution-basket/" + "bsk_" + "0" * 32)
        self.assertEqual(status, 405)
        self.assertEqual(headers.get("Allow"), "GET, HEAD")

    def test_put_execution_basket_journal_returns_405(self):
        status, _, _ = _request(self.port, "PUT", "/api/execution-basket-journal")
        self.assertEqual(status, 405)

    def test_patch_basket_execution_status_returns_405(self):
        status, _, _ = _request(self.port, "PATCH", "/api/basket-execution-status")
        self.assertEqual(status, 405)

    def test_delete_execution_baskets_returns_405(self):
        status, _, _ = _request(self.port, "DELETE", "/api/execution-baskets")
        self.assertEqual(status, 405)

    def test_no_route_exists_for_build_check_confirm_send(self):
        for path in ("/api/build-basket", "/api/check-basket", "/api/confirm-basket", "/api/send-basket-next"):
            status, _, _ = _request(self.port, "GET", path)
            self.assertEqual(status, 404)
            status, _, _ = _request(self.port, "POST", path)
            self.assertEqual(status, 405)


class DisabledDefaultTests(unittest.TestCase):
    def test_default_server_has_disabled_basket_service(self):
        httpd, thread = _running_server()
        try:
            port = httpd.server_address[1]
            status, _, body = _request(port, "GET", "/api/basket-execution-status")
            self.assertEqual(status, 200)
            self.assertIn(b'"enabled":false', body)
        finally:
            _stop_server(httpd, thread)


class DashboardContentTests(unittest.TestCase):
    def test_dashboard_html_contains_required_banners(self):
        html = (APP_DIRECTORY / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn("AUTOMATED EXECUTION DISABLED", html)
        self.assertIn("MANUAL CONFIRMATION REQUIRED FOR EVERY CHILD SEND", html)
        self.assertIn("DEMO ONLY", html)
        self.assertIn('id="basket-execution"', html)

    def test_no_innerhtml_added_for_basket_panel(self):
        js = (APP_DIRECTORY / "static" / "app.js").read_text(encoding="utf-8")
        start = js.index("function renderBasketExecution")
        end = js.index("\n\n", start)
        self.assertNotIn("innerHTML", js[start:end])


if __name__ == "__main__":
    unittest.main(verbosity=2)
