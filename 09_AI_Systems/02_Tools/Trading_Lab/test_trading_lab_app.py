# -*- coding: utf-8 -*-
"""Focused tests for the TRL-R2-001 local application foundation."""

import ast
import copy
import http.client
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock


BASE = Path(__file__).resolve().parent
REPOSITORY_ROOT = BASE.parents[2]
APP_DIRECTORY = BASE / "trading_lab_app"
STATIC_DIRECTORY = APP_DIRECTORY / "static"
EXPECTED_RUN_ID = "TRL-RUN-6922AEA31AE2630B4DA1"
EXPECTED_INPUT_HASH = "6cdbca208cd1029b90e5ed3494ab05a3b7042d224ed01293373fc173a85aee56"
EXPECTED_CONFIGURATION_HASH = "3f4c513f275ca034af9fd2f4bbcb4ec382c361969d7706fbb6fb6d26fd26bbbd"
EXPECTED_STRATEGY_HASH = "e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955"
EXPECTED_ENGINE_DIGEST = "f9f555d37e0820c39eb2afe1156fca4912d255debc23c7ab27c6111c31da3952"
EXPECTED_MANIFEST = [
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

sys.path.insert(0, str(BASE))
from trading_lab_app import app, capabilities, server, service  # noqa: E402


class RunningServer:
    def __enter__(self):
        self.httpd = server.create_server(0)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(timeout=3)

    def request(self, method, path, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        connection.request(method, path, headers=headers or {})
        response = connection.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), body
        connection.close()
        return result


class ImportAndLaunchTests(unittest.TestCase):
    def test_import_is_inert_and_does_not_create_server_or_open_browser(self):
        with mock.patch("trading_lab_app.server.create_server") as create, mock.patch(
            "webbrowser.open"
        ) as browser:
            importlib.reload(importlib.import_module("trading_lab_app.app"))
        create.assert_not_called()
        browser.assert_not_called()

    def test_repository_root_and_alternate_cwd_execution(self):
        entry = APP_DIRECTORY / "__main__.py"
        environments = dict(os.environ)
        environments["PYTHONDONTWRITEBYTECODE"] = "1"
        for cwd in (REPOSITORY_ROOT, Path(tempfile.gettempdir())):
            completed = subprocess.run(
                [sys.executable, "-B", "-W", "error", str(entry), "--version"],
                cwd=str(cwd),
                env=environments,
                capture_output=True,
                text=True,
                check=False,
                timeout=20,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertEqual(completed.stdout.strip(), "2.0.0-r2.001")

    def test_no_browser_option_prevents_browser_open(self):
        fake_server = mock.Mock()
        fake_server.server_address = ("127.0.0.1", 8765)
        fake_server.serve_forever.side_effect = KeyboardInterrupt
        with mock.patch("trading_lab_app.app.create_server", return_value=fake_server), mock.patch(
            "trading_lab_app.app.webbrowser.open"
        ) as browser:
            self.assertEqual(app.run_server(open_browser=False), 0)
        browser.assert_not_called()
        fake_server.server_close.assert_called_once_with()

    def test_unavailable_port_fails_without_fallback(self):
        first = server.create_server(0)
        port = first.server_address[1]
        try:
            with self.assertRaises(OSError):
                server.create_server(port)
        finally:
            first.server_close()


class ServiceContractTests(unittest.TestCase):
    def test_demo_result_is_deterministic_and_json_serializable(self):
        first = service.demo_result()
        second = service.demo_result()
        self.assertEqual(first, second)
        encoded = server.deterministic_json_bytes(first)
        self.assertEqual(json.loads(encoded.decode("utf-8")), first)
        self.assertTrue(encoded.endswith(b"\n"))

    def test_demo_inputs_are_not_mutated(self):
        with service.DEMO_PACK_PATH.open(encoding="utf-8") as handle:
            pack = json.load(handle)
        original_pack = copy.deepcopy(pack)
        original_strategy = copy.deepcopy(service.DEMO_STRATEGY)
        with mock.patch("trading_lab_app.service._load_demo_pack", return_value=pack):
            service.demo_result()
        self.assertEqual(pack, original_pack)
        self.assertEqual(service.DEMO_STRATEGY, original_strategy)

    def test_exact_release_1_identity_hashes_and_financial_result(self):
        result = service.demo_result()
        metadata = result["metadata"]
        self.assertEqual(metadata["run_id"], EXPECTED_RUN_ID)
        self.assertEqual(metadata["input_data_hash"], EXPECTED_INPUT_HASH)
        self.assertEqual(metadata["configuration_hash"], EXPECTED_CONFIGURATION_HASH)
        self.assertEqual(metadata["strategy_definition_hash"], EXPECTED_STRATEGY_HASH)
        self.assertEqual(metadata["engine_source_digest"], EXPECTED_ENGINE_DIGEST)
        self.assertEqual(result["final_cash"], 94.9975)
        self.assertEqual(result["final_equity"], 100.22673707083118)

    def test_engine_manifest_parity_excludes_application(self):
        manifest = service.demo_result()["metadata"]["engine_source_manifest"]
        self.assertEqual(manifest, EXPECTED_MANIFEST)
        self.assertFalse(any("trading_lab_app" in path for path in manifest))

    def test_market_chart_document_uses_committed_synthetic_data(self):
        document = service.market_data_document()
        self.assertTrue(document["synthetic"])
        self.assertEqual(document["pack_id"], "TRL-PACK-DEMO-001")
        self.assertEqual(len(document["points"]), 60)
        self.assertEqual(document["points"][50]["signals"][0]["action"], "enter")

    def test_full_report_renders_without_writing_an_artifact(self):
        before = set(BASE.glob("*.md"))
        document = service.report_document()
        after = set(BASE.glob("*.md"))
        self.assertEqual(before, after)
        self.assertIn("# Paper Portfolio Performance Report", document["content"])
        self.assertIn(EXPECTED_RUN_ID, document["content"])
        self.assertIn("PAPER/RESEARCH ONLY", document["content"])

    def test_capability_manifest_is_explicitly_closed(self):
        manifest = capabilities.capability_manifest()
        self.assertFalse(manifest["broker_capability"])
        self.assertFalse(manifest["external_order_capability"])
        self.assertFalse(manifest["credential_storage_capability"])
        self.assertFalse(manifest["telemetry"])
        expected = {
            "External/live market data", "Forward paper portfolio service",
            "Accounts and authentication", "Subscriptions and payments",
            "Customer distribution", "Broker credentials", "Broker connectivity",
            "Assisted execution", "Automated execution", "External orders",
            "Customer funds or custody", "Personalized investment advice",
        }
        self.assertEqual(set(manifest["not_implemented"]), expected)


class HttpBoundaryTests(unittest.TestCase):
    def test_server_binds_only_ipv4_loopback(self):
        httpd = server.create_server(0)
        try:
            self.assertEqual(httpd.server_address[0], "127.0.0.1")
            self.assertEqual(server.BIND_HOST, "127.0.0.1")
            self.assertNotIn("0.0.0.0", APP_DIRECTORY.joinpath("server.py").read_text(encoding="utf-8"))
        finally:
            httpd.server_close()

    def test_health_version_and_capabilities_endpoints(self):
        with RunningServer() as local:
            for path in ("/api/health", "/api/version", "/api/capabilities"):
                status, headers, body = local.request("GET", path)
                self.assertEqual(status, 200)
                self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
                json.loads(body.decode("utf-8"))
            status, _, body = local.request("GET", "/api/health")
            self.assertEqual(json.loads(body)["bind_host"], "127.0.0.1")

    def test_all_read_only_demo_endpoints(self):
        with RunningServer() as local:
            for path in ("/api/demo/market-data", "/api/demo/result", "/api/demo/report"):
                status, _, body = local.request("GET", path)
                self.assertEqual(status, 200)
                json.loads(body.decode("utf-8"))

    def test_static_allowlist_and_directory_traversal_rejection(self):
        with RunningServer() as local:
            for path in server.STATIC_ROUTES:
                status, _, body = local.request("GET", path)
                self.assertEqual(status, 200)
                self.assertTrue(body)
            for path in ("/server.py", "/static/index.html", "/../trading_lab.py", "/%2e%2e/trading_lab.py", "/..%5ctrading_lab.py"):
                status, _, _ = local.request("GET", path)
                self.assertIn(status, (400, 404))

    def test_unsupported_methods_are_rejected(self):
        with RunningServer() as local:
            for method in ("HEAD", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "TRACE"):
                status, headers, _ = local.request(method, "/api/health")
                self.assertEqual(status, 405)
                self.assertEqual(headers["Allow"], "GET")

    def test_nonlocal_host_header_is_rejected(self):
        with RunningServer() as local:
            status, _, body = local.request("GET", "/api/health", {"Host": "example.invalid"})
            self.assertEqual(status, 421)
            self.assertEqual(json.loads(body)["error"], "LOCAL_HOST_REQUIRED")

    def test_security_headers_are_on_success_and_error_responses(self):
        with RunningServer() as local:
            for path in ("/", "/missing"):
                _, headers, _ = local.request("GET", path)
                self.assertIn("default-src 'none'", headers["Content-Security-Policy"])
                self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                self.assertEqual(headers["X-Frame-Options"], "DENY")
                self.assertEqual(headers["Referrer-Policy"], "no-referrer")
                self.assertEqual(headers["Cache-Control"], "no-store, max-age=0")


class DashboardAndNegativeSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (STATIC_DIRECTORY / "index.html").read_text(encoding="utf-8")
        cls.javascript = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")

    def test_dashboard_contains_every_required_section_and_safety_label(self):
        for section_id in (
            "overview", "market-chart", "equity", "signals", "strategy",
            "reports", "risk", "future-modes", "about",
        ):
            self.assertIn('id="{}"'.format(section_id), self.html)
        for wording in (
            "ALSAKKAF Trading Research Lab", "PAPER/RESEARCH ONLY",
            "SYNTHETIC DATA", "RESEARCH SIGNAL — NOT A TRADE INSTRUCTION",
            "not Founder-approved for investment use", "No leverage", "No shorting",
            "No increase to a losing position", "No broker or external-order capability",
            "ASSISTED_EXECUTION_MODE", "DISABLED · UNAUTHORIZED",
            "AUTOMATED_EXECUTION_MODE", "PROHIBITED · UNAVAILABLE",
            "future optional adapter",
        ):
            self.assertIn(wording, self.html)

    def test_accessible_semantic_structure_and_fallbacks(self):
        for element in ("<header", "<nav", "<main", "<section", "<footer", "<table", "<caption"):
            self.assertIn(element, self.html)
        self.assertIn("Skip to dashboard content", self.html)
        self.assertIn('aria-live="polite"', self.html)
        self.assertIn('role="alert"', self.html)
        self.assertIn('prefers-reduced-motion: reduce', (STATIC_DIRECTORY / "styles.css").read_text(encoding="utf-8"))
        self.assertNotIn("<script>", self.html)

    def test_assets_are_local_and_no_analytics_or_external_urls_exist(self):
        combined = "\n".join(
            path.read_text(encoding="utf-8") for path in APP_DIRECTORY.rglob("*") if path.is_file()
        ).lower()
        self.assertNotIn("https://", combined)
        self.assertNotIn("http://0.0.0.0", combined)
        for term in ("google-analytics", "segment.io", "mixpanel", "stripe", "apikey", "api_key"):
            self.assertNotIn(term, combined)

    def test_no_broker_credential_external_order_or_outbound_import_surface(self):
        self.assertEqual(set(server.API_ROUTES), {
            "/api/health", "/api/version", "/api/capabilities",
            "/api/demo/market-data", "/api/demo/result", "/api/demo/report",
        })
        for path in APP_DIRECTORY.glob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertTrue(imports.isdisjoint({"requests", "urllib3", "aiohttp", "ftplib", "smtplib"}), (path, imports))

    def test_validation_creates_no_cache_bytecode_or_generated_report_artifacts(self):
        forbidden = []
        for path in BASE.rglob("*"):
            lowered = path.name.lower()
            if path.is_dir() and lowered in {"__pycache__", ".pytest_cache", ".mypy_cache"}:
                forbidden.append(path)
            if path.is_file() and (path.suffix in {".pyc", ".pyo"} or lowered.startswith("trl-r2-001-synthetic-paper-report")):
                forbidden.append(path)
        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
