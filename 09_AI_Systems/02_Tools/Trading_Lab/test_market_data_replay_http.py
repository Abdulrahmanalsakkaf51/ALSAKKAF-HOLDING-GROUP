"""Tests for TRL-R2-011 Market Data Fabric and Replay V0 -- HTTP routes
(``server.py`` integration). Covers contract Section 25 category L (all six
read-only routes, GET, HEAD, 405 mutation behavior, Allow headers, safe
IDs, pagination, bounded output, no path disclosure, no raw exception, no
HTTP mutation).
"""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

import mdr_test_support as support
from trading_lab_app import mode_service as ms
from trading_lab_app import server as srvmod


class MarketDataFabricHttpTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.mode_service = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
        self.mode_service.request_transition("RESEARCH", actor="t", actor_channel="LOCAL_OPERATOR")
        self.service = support.build_service(mode_service=self.mode_service)
        self.manifest = support.import_synthetic_dataset(self.service, source_reference="http-fixture")
        self.session = self.service.create_replay_session(self.manifest["dataset_id"], 0, self.manifest["bar_count"] - 1, 2)
        self.service.replay_next(self.session["replay_session_id"])
        self.server = srvmod.create_server(0, mode_service=self.mode_service, market_data_replay_service_instance=self.service)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self._tmp.cleanup()

    def _get(self, path, expect_status=200):
        req = urllib.request.Request("http://127.0.0.1:{}{}".format(self.port, path), method="GET")
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                return resp.status, json.loads(resp.read())
        except urllib.error.HTTPError as error:
            return error.code, json.loads(error.read())

    def test_market_data_status_route(self):
        status, body = self._get("/api/market-data-status")
        self.assertEqual(status, 200)
        self.assertTrue(body["market_data_research_granted"])

    def test_market_datasets_route(self):
        status, body = self._get("/api/market-datasets")
        self.assertEqual(status, 200)
        self.assertEqual(body["total_count"], 1)

    def test_market_dataset_detail_route(self):
        status, body = self._get("/api/market-dataset/{}".format(self.manifest["dataset_id"]))
        self.assertEqual(status, 200)
        self.assertTrue(body["found"])

    def test_market_dataset_detail_not_found(self):
        status, body = self._get("/api/market-dataset/mds_" + "0" * 32)
        self.assertEqual(status, 404)
        self.assertFalse(body["found"])

    def test_replay_sessions_route(self):
        status, body = self._get("/api/replay-sessions")
        self.assertEqual(status, 200)
        self.assertEqual(body["total_count"], 1)

    def test_replay_session_detail_route(self):
        status, body = self._get("/api/replay-session/{}".format(self.session["replay_session_id"]))
        self.assertEqual(status, 200)
        self.assertTrue(body["found"])
        self.assertEqual(body["replay_session"]["status"], "RUNNING")

    def test_replay_snapshot_route(self):
        status, body = self._get("/api/replay-snapshot/{}".format(self.session["replay_session_id"]))
        self.assertEqual(status, 200)
        self.assertTrue(body["found"])
        self.assertTrue(body["snapshot"]["non_live"])
        self.assertTrue(body["snapshot"]["non_executable"])

    def test_pagination_query_parameters(self):
        status, body = self._get("/api/market-datasets?offset=0&limit=1")
        self.assertEqual(status, 200)
        self.assertEqual(body["limit"], 1)

    def test_invalid_pagination_returns_governed_error(self):
        status, body = self._get("/api/market-datasets?limit=not-a-number")
        self.assertEqual(status, 400)
        self.assertIn("error", body)

    def test_no_physical_path_in_any_response(self):
        for path in (
            "/api/market-data-status", "/api/market-datasets",
            "/api/market-dataset/{}".format(self.manifest["dataset_id"]),
            "/api/replay-sessions", "/api/replay-session/{}".format(self.session["replay_session_id"]),
            "/api/replay-snapshot/{}".format(self.session["replay_session_id"]),
        ):
            _status, body = self._get(path)
            text = json.dumps(body)
            self.assertNotIn(":\\", text)
            self.assertNotIn("AppData", text)

    def test_head_supported_on_every_route(self):
        for path in (
            "/api/market-data-status", "/api/market-datasets",
            "/api/market-dataset/{}".format(self.manifest["dataset_id"]),
            "/api/replay-sessions", "/api/replay-session/{}".format(self.session["replay_session_id"]),
            "/api/replay-snapshot/{}".format(self.session["replay_session_id"]),
        ):
            req = urllib.request.Request("http://127.0.0.1:{}{}".format(self.port, path), method="HEAD")
            with urllib.request.urlopen(req, timeout=5) as resp:
                self.assertEqual(resp.status, 200)
                self.assertEqual(resp.read(), b"")

    def test_post_returns_405_with_allow_header(self):
        for path in (
            "/api/market-data-status", "/api/market-datasets",
            "/api/market-dataset/{}".format(self.manifest["dataset_id"]),
            "/api/replay-sessions", "/api/replay-session/{}".format(self.session["replay_session_id"]),
            "/api/replay-snapshot/{}".format(self.session["replay_session_id"]),
        ):
            req = urllib.request.Request("http://127.0.0.1:{}{}".format(self.port, path), method="POST")
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 405)
            self.assertEqual(ctx.exception.headers.get("Allow"), "GET, HEAD")

    def test_put_delete_also_rejected(self):
        for method in ("PUT", "DELETE", "PATCH"):
            req = urllib.request.Request(
                "http://127.0.0.1:{}/api/replay-session/{}".format(self.port, self.session["replay_session_id"]),
                method=method,
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 405)

    def test_no_import_or_mutation_route_exists(self):
        for method in ("POST", "PUT"):
            req = urllib.request.Request(
                "http://127.0.0.1:{}/api/market-datasets".format(self.port), method=method,
            )
            with self.assertRaises(urllib.error.HTTPError) as ctx:
                urllib.request.urlopen(req, timeout=5)
            self.assertEqual(ctx.exception.code, 405)

    def test_unsafe_id_returns_404_not_service_error(self):
        status, _body = self._get("/api/market-dataset/../etc/passwd")
        self.assertIn(status, (400, 404))


class DisabledModeHttpTests(unittest.TestCase):
    def test_off_mode_routes_report_disabled(self):
        with tempfile.TemporaryDirectory():
            mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
            from trading_lab_app import market_data_replay_service as mdrsvc
            disabled = mdrsvc.disabled_service(operating_mode="OFF")
            server = srvmod.create_server(0, mode_service=mode_svc, market_data_replay_service_instance=disabled)
            port = server.server_address[1]
            thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
            thread.start()
            try:
                req = urllib.request.Request("http://127.0.0.1:{}/api/market-data-status".format(port), method="GET")
                with urllib.request.urlopen(req, timeout=5) as resp:
                    body = json.loads(resp.read())
                self.assertFalse(body["enabled"])
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
