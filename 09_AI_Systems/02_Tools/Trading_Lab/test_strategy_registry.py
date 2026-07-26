# -*- coding: utf-8 -*-
"""Focused acceptance tests for TRL-R2-002 strategy registry and vault."""

import ast
import copy
import hashlib
import http.client
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest import mock


BASE = Path(__file__).resolve().parent
APP_DIRECTORY = BASE / "trading_lab_app"
STATIC_DIRECTORY = APP_DIRECTORY / "static"
sys.path.insert(0, str(BASE))

from trading_lab_app import capabilities, server, service  # noqa: E402
from trading_lab_app import strategy_registry as registry  # noqa: E402
from trading_lab_app import strategy_vault as vault  # noqa: E402


EXPECTED_KERNEL_HASH = "e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955"
EXPECTED_RECORD_DIGEST = "3cc2c876ad7c11d2244f9f71ab9a62cdc7f8baac0f5d3964173faa4d9e7e4878"
EXPECTED_BACKLOG_DIGEST = "5029263efdb47563852ba93733f6d84a2cb4c757d32e57a29a604b952ec75a63"
EXPECTED_BUNDLE_DIGEST = "62a549288ab65fd543f7550416c96f01d65a3ecf3f128aa7b31b2de1ddc21d7b"


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

    def request(self, method, path):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        connection.request(method, path)
        response = connection.getresponse()
        body = response.read()
        result = response.status, dict(response.getheaders()), body
        connection.close()
        return result


def without_provenance(result):
    semantic = copy.deepcopy(result)
    metadata = semantic["metadata"]
    for field in ("run_id", "checkpoint_id", "engine_source_digest", "engine_source_manifest"):
        metadata.pop(field, None)
    metadata.pop("engine", None)
    return semantic


class RegistrySchemaTests(unittest.TestCase):
    def setUp(self):
        documents = vault.inspect_catalog()["documents"]
        self.record = documents[vault.EXECUTABLE_FILENAME]
        self.backlog = documents[vault.BACKLOG_FILENAME]

    def test_valid_sma_registry_load_and_exact_inventory(self):
        loaded = registry.load_registry(copy.deepcopy(service.DEMO_STRATEGY))
        self.assertEqual((loaded.status, loaded.reason_code), ("VALID", "REGISTRY_VALID"))
        items = loaded.registry.list_executable()
        self.assertEqual(len(items), 1)
        self.assertEqual((items[0]["record"]["strategy_id"], items[0]["record"]["strategy_version"]), ("SMA-001", "1.0.0"))

    def test_exact_schema_rejects_unknown_and_missing_fields(self):
        unknown = copy.deepcopy(self.record)
        unknown["unknown"] = "blocked"
        missing = copy.deepcopy(self.record)
        missing.pop("description")
        for candidate in (unknown, missing):
            with self.assertRaises(registry.SchemaViolation):
                registry.validate_strategy_record(candidate)

    def test_exact_builtin_container_and_numeric_types(self):
        class DictSubclass(dict):
            pass

        class IntSubclass(int):
            pass

        with self.assertRaises(registry.SchemaViolation):
            registry.validate_strategy_record(DictSubclass(self.record))
        bad_boolean = copy.deepcopy(self.record)
        bad_boolean["parameter_schema"]["fast"]["minimum"] = True
        with self.assertRaises(registry.SchemaViolation):
            registry.validate_strategy_record(bad_boolean)
        bad_subclass = copy.deepcopy(self.record)
        bad_subclass["parameter_schema"]["fast"]["minimum"] = IntSubclass(1)
        with self.assertRaises(registry.SchemaViolation):
            registry.validate_strategy_record(bad_subclass)

    def test_semantic_version_and_identifier_validation(self):
        for field, value in (("strategy_version", "01.0.0"), ("strategy_version", "1.0"), ("strategy_id", "sma-001"), ("strategy_id", "../SMA-001")):
            candidate = copy.deepcopy(self.record)
            candidate[field] = value
            with self.assertRaises(registry.SchemaViolation):
                registry.validate_strategy_record(candidate)

    def test_duplicate_list_item_and_noncanonical_order_rejected(self):
        duplicate = copy.deepcopy(self.record)
        duplicate["supported_timeframes"].append("D1")
        reversed_items = copy.deepcopy(self.record)
        reversed_items["required_market_fields"].reverse()
        for candidate in (duplicate, reversed_items):
            with self.assertRaises(registry.SchemaViolation):
                registry.validate_strategy_record(candidate)

    def test_unsupported_status_combination_has_stable_reason(self):
        candidate = copy.deepcopy(self.record)
        candidate["implementation_status"] = "RETIRED"
        with self.assertRaises(registry.SchemaViolation) as caught:
            registry.validate_strategy_record(candidate)
        self.assertEqual(caught.exception.reason_code, "REGISTRY_STATUS_COMBINATION_INVALID")

    def test_duplicate_strategy_definition_fails_closed(self):
        with self.assertRaises(registry.SchemaViolation) as caught:
            registry._snapshot(
                [self.record, copy.deepcopy(self.record)], self.backlog, [], "0" * 64,
                copy.deepcopy(service.DEMO_STRATEGY),
            )
        self.assertEqual(caught.exception.reason_code, "REGISTRY_DUPLICATE_STRATEGY")

    def test_executable_text_paths_imports_and_code_fragments_are_rejected(self):
        for unsafe in ("import os", "eval(value)", "../secret", "C:\\private\\file", "module.py"):
            candidate = copy.deepcopy(self.record)
            candidate["description"] = unsafe
            with self.assertRaises(registry.SchemaViolation):
                registry.validate_strategy_record(candidate)

    def test_release1_sma_identity_and_configuration_cross_check(self):
        self.assertEqual(self.record["kernel_strategy_definition_hash"], EXPECTED_KERNEL_HASH)
        changed = copy.deepcopy(service.DEMO_STRATEGY)
        changed["strategy_version"] = "1.0.1"
        loaded = registry.load_registry(changed)
        self.assertEqual((loaded.status, loaded.reason_code), ("FAILED", "REGISTRY_IDENTITY_MISMATCH"))
        self.assertEqual(loaded.document()["installed_executable_strategies"], [])

    def test_sma_declarations_are_honest_and_bounded(self):
        self.assertEqual(self.record["supported_timeframes"], ["D1"])
        self.assertEqual(self.record["required_market_fields"], ["close", "high", "low", "open", "volume"])
        self.assertIn("SIMPLE_MOVING_AVERAGE", self.record["required_indicators"])
        self.assertIn("LESS_THAN_SLOW", str(self.record["parameter_schema"]))
        limitations = " ".join(self.record["known_limitations"]).lower()
        self.assertIn("long-only", limitations)
        self.assertIn("one instrument", limitations)
        self.assertNotIn("profitable", self.record["approval_status"].lower())


class VaultIdentityAndFailureTests(unittest.TestCase):
    def test_deterministic_record_backlog_manifest_and_bundle_digests(self):
        first = vault.inspect_catalog()
        second = vault.inspect_catalog()
        self.assertEqual(first, second)
        self.assertEqual(first["manifest"][0]["canonical_json_sha256"], EXPECTED_RECORD_DIGEST)
        self.assertEqual(first["manifest"][1]["canonical_json_sha256"], EXPECTED_BACKLOG_DIGEST)
        self.assertEqual(first["bundle_digest"], EXPECTED_BUNDLE_DIGEST)
        self.assertEqual([item["path"] for item in first["manifest"]], sorted(item["path"] for item in first["manifest"]))

    def test_newline_normalization_parity(self):
        inspected = vault.inspect_catalog()
        entries = []
        for item in inspected["manifest"]:
            filename = item["path"].rsplit("/", 1)[1]
            lf = vault.normalize_newlines((vault.CATALOG_DIRECTORY / filename).read_bytes())
            crlf = lf.replace(b"\n", b"\r\n")
            self.assertEqual(vault.normalize_newlines(crlf), lf)
            entries.append({"path": item["path"], "normalized_bytes": vault.normalize_newlines(crlf)})
        self.assertEqual(vault._bundle_digest(entries), EXPECTED_BUNDLE_DIGEST)

    def test_missing_and_unexpected_catalog_paths_fail_closed(self):
        only_backlog = [vault.CATALOG_DIRECTORY / vault.BACKLOG_FILENAME]
        with mock.patch.object(Path, "iterdir", return_value=only_backlog):
            result = registry.load_registry(service.DEMO_STRATEGY)
        self.assertEqual(result.reason_code, "REGISTRY_FILE_MISSING")
        unexpected = mock.Mock()
        unexpected.name = "unexpected.json"
        unexpected.is_file.return_value = True
        unexpected.is_symlink.return_value = False
        real_paths = [vault.CATALOG_DIRECTORY / name for name in vault.ALLOWED_FILENAMES]
        with mock.patch.object(Path, "iterdir", return_value=real_paths + [unexpected]):
            result = registry.load_registry(service.DEMO_STRATEGY)
        self.assertEqual(result.reason_code, "REGISTRY_UNEXPECTED_FILE")

    def test_invalid_utf8_and_invalid_json_have_specific_reasons(self):
        cases = ((b"\xff\xfe", "REGISTRY_INVALID_UTF8"), (b"{invalid}\n", "REGISTRY_INVALID_JSON"))
        for content, reason in cases:
            with self.subTest(reason=reason):
                fake_path = mock.Mock()
                fake_path.read_bytes.return_value = content
                with self.assertRaises(vault.VaultFailure) as caught:
                    vault._read_json_file(fake_path)
                self.assertEqual(caught.exception.reason_code, reason)
                with mock.patch.object(vault, "inspect_catalog", side_effect=vault.VaultFailure(reason)):
                    result = registry.load_registry(service.DEMO_STRATEGY)
                self.assertEqual((result.status, result.reason_code), ("FAILED", reason))
                self.assertEqual(result.document()["installed_strategy_count"], 0)

    def test_duplicate_json_field_and_nonfinite_material_rejected(self):
        cases = (b'{"a":1,"a":2}\n', b'{"a":NaN}\n')
        for content in cases:
            fake_path = mock.Mock()
            fake_path.read_bytes.return_value = content
            with self.assertRaises(vault.VaultFailure) as caught:
                vault._read_json_file(fake_path)
            self.assertEqual(caught.exception.reason_code, "REGISTRY_INVALID_JSON")

    def test_file_size_and_json_depth_limits_fail_closed(self):
        oversized = mock.Mock()
        oversized.read_bytes.return_value = b" " * (vault.MAX_FILE_BYTES + 1)
        with self.assertRaises(vault.VaultFailure) as caught:
            vault._read_json_file(oversized)
        self.assertEqual(caught.exception.reason_code, "REGISTRY_SCHEMA_INVALID")
        nested = "leaf"
        for _ in range(vault.MAX_JSON_DEPTH + 1):
            nested = [nested]
        with self.assertRaises(vault.VaultFailure) as caught:
            vault._bounded_json_shape(nested)
        self.assertEqual(caught.exception.reason_code, "REGISTRY_SCHEMA_INVALID")

    def test_valid_json_tamper_is_detected_by_identity_anchor(self):
        original_reader = vault._read_json_file

        def altered_reader(path):
            value, normalized = original_reader(path)
            if path.name == vault.EXECUTABLE_FILENAME:
                value = copy.deepcopy(value)
                value["display_name"] = "Tampered strategy"
            return value, normalized

        with mock.patch.object(vault, "_read_json_file", side_effect=altered_reader):
            result = registry.load_registry(service.DEMO_STRATEGY)
        self.assertEqual(result.reason_code, "REGISTRY_IDENTITY_MISMATCH")

    def test_bundle_digest_mismatch_has_specific_reason(self):
        with mock.patch.object(vault, "PACKAGED_BUNDLE_DIGEST", "0" * 64):
            result = registry.load_registry(service.DEMO_STRATEGY)
        self.assertEqual(result.reason_code, "REGISTRY_BUNDLE_DIGEST_MISMATCH")

    def test_schema_failure_from_catalog_preserves_no_partial_registry(self):
        inspected = vault.inspect_catalog()
        documents = copy.deepcopy(inspected["documents"])
        documents[vault.EXECUTABLE_FILENAME]["unexpected"] = "blocked"
        altered = {"documents": documents, "manifest": inspected["manifest"], "bundle_digest": inspected["bundle_digest"]}
        with mock.patch.object(vault, "inspect_catalog", return_value=altered):
            result = registry.load_registry(service.DEMO_STRATEGY)
        self.assertEqual(result.reason_code, "REGISTRY_SCHEMA_INVALID")
        self.assertIsNone(result.registry)
        self.assertEqual(result.document()["research_backlog"]["entries"], [])


class RegistryOperationTests(unittest.TestCase):
    def setUp(self):
        self.loaded = registry.load_registry(copy.deepcopy(service.DEMO_STRATEGY))
        self.snapshot = self.loaded.registry

    def test_exact_get_unknown_strategy_and_unknown_version(self):
        found = self.snapshot.get("SMA-001", "1.0.0")
        self.assertTrue(found["found"])
        for strategy_id, version in (("UNKNOWN-001", "1.0.0"), ("SMA-001", "9.9.9")):
            result = self.snapshot.get(strategy_id, version)
            self.assertEqual(result, {"found": False, "reason_code": "REGISTRY_STRATEGY_NOT_FOUND", "strategy": None})

    def test_research_eligibility_and_explicit_noneligible_reasons(self):
        eligible = self.snapshot.research_eligibility("SMA-001", "1.0.0")
        missing = self.snapshot.research_eligibility("SMA-001", "2.0.0")
        self.assertEqual(eligible, {"eligible": True, "reason_code": "REGISTRY_RESEARCH_ELIGIBLE"})
        self.assertEqual(missing, {"eligible": False, "reason_code": "REGISTRY_STRATEGY_NOT_FOUND"})
        self.assertIn("REGISTRY_NOT_RESEARCH_ELIGIBLE", registry.REASON_CODES)

        inspected = vault.inspect_catalog()
        record = copy.deepcopy(inspected["documents"][vault.EXECUTABLE_FILENAME])
        record["approval_status"] = "FOUNDER_REJECTED"
        record["research_eligibility"] = False
        rejected = registry._snapshot(
            [record], inspected["documents"][vault.BACKLOG_FILENAME], inspected["manifest"],
            inspected["bundle_digest"], copy.deepcopy(service.DEMO_STRATEGY),
        )
        self.assertEqual(
            rejected.research_eligibility("SMA-001", "1.0.0"),
            {"eligible": False, "reason_code": "REGISTRY_NOT_RESEARCH_ELIGIBLE"},
        )

    def test_filters_by_market_timeframe_and_statuses(self):
        positive = (
            {"market": "SYNTHETIC_EQUITY_RESEARCH"},
            {"timeframe": "D1"},
            {"implementation_status": "IMPLEMENTED"},
            {"approval_status": "EXPERIMENTAL_RESEARCH_ONLY"},
        )
        for filters in positive:
            self.assertEqual(len(self.snapshot.list_executable(**filters)), 1)
        for filters in ({"market": "FX"}, {"timeframe": "M1"}, {"implementation_status": "RETIRED"}, {"approval_status": "PAPER_ELIGIBLE"}):
            self.assertEqual(self.snapshot.list_executable(**filters), [])

    def test_backlog_is_separate_and_never_executable(self):
        executable_ids = {item["record"]["strategy_id"] for item in self.snapshot.list_executable()}
        backlog = self.snapshot.list_backlog()
        self.assertEqual(len(backlog), 9)
        for entry in backlog:
            self.assertNotIn(entry["backlog_id"], executable_ids)
            self.assertEqual(entry["status"], "PLANNED_NOT_IMPLEMENTED")
            self.assertIs(entry["execution_eligible"], False)

    def test_returned_state_cannot_mutate_registry_internals(self):
        first = self.loaded.document()
        first["installed_executable_strategies"][0]["record"]["display_name"] = "mutated"
        first["research_backlog"]["entries"].clear()
        second = self.loaded.document()
        self.assertEqual(second["installed_executable_strategies"][0]["record"]["display_name"], "SMA Close Crossing Long-Only Research Rule")
        self.assertEqual(len(second["research_backlog"]["entries"]), 9)

    def test_registry_loading_does_not_run_financial_evaluation(self):
        with mock.patch("trading_lab_app.service.demo_result") as evaluation:
            document = service.strategy_registry_document()
        evaluation.assert_not_called()
        self.assertEqual(document["registry_health"]["reason_code"], "REGISTRY_VALID")


class RegistryApplicationTests(unittest.TestCase):
    def test_registry_api_is_deterministic_read_only_and_path_safe(self):
        with RunningServer() as local:
            first_status, first_headers, first_body = local.request("GET", "/api/strategy-registry")
            second_status, _, second_body = local.request("GET", "/api/strategy-registry")
            self.assertEqual((first_status, second_status), (200, 200))
            self.assertEqual(first_body, second_body)
            self.assertEqual(first_headers["Cache-Control"], "no-store, max-age=0")
            document = json.loads(first_body.decode("utf-8"))
            self.assertEqual(document["registry_health"], {"reason_code": "REGISTRY_VALID", "status": "VALID"})
            self.assertNotIn(str(BASE).lower(), first_body.decode("utf-8").lower())
            for method in ("HEAD", "POST", "PUT", "PATCH", "DELETE"):
                status, headers, _ = local.request(method, "/api/strategy-registry")
                self.assertEqual(status, 405)
                self.assertEqual(headers["Allow"], "GET")
            for path in ("/api/../strategy-registry", "/api/%2e%2e/strategy-registry", "/api/..%5cstrategy-registry"):
                status, _, _ = local.request("GET", path)
                self.assertIn(status, (400, 404))

    def test_existing_api_contracts_remain_available(self):
        expected = {
            "/api/health", "/api/version", "/api/capabilities", "/api/strategy-registry",
            "/api/demo/market-data", "/api/demo/result", "/api/demo/report",
        }
        self.assertEqual(set(server.API_ROUTES), expected)
        with RunningServer() as local:
            for path in sorted(expected):
                status, _, body = local.request("GET", path)
                self.assertEqual(status, 200)
                json.loads(body.decode("utf-8"))

    def test_dashboard_semantics_accessibility_and_governance_wording(self):
        html = (STATIC_DIRECTORY / "index.html").read_text(encoding="utf-8")
        css = (STATIC_DIRECTORY / "styles.css").read_text(encoding="utf-8")
        javascript = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
        for wording in (
            'id="strategy-vault"', "Strategy registry and vault", "PLANNED — NOT IMPLEMENTED",
            "The Registry does not choose the best strategy", "No strategy is approved for investment use",
            "No live data, broker, or execution capability exists", "Vault bundle identity",
            "Registry record digest", "Release 1 kernel definition hash",
        ):
            self.assertIn(wording, html)
        for semantic in ("<section", "<article", "<table", "<caption", 'scope="col"'):
            self.assertIn(semantic, html)
        self.assertIn("prefers-reduced-motion: reduce", css)
        self.assertIn('getJson("/api/strategy-registry")', javascript)

    def test_capability_manifest_is_accurate_and_closed(self):
        manifest = capabilities.capability_manifest()
        for implemented in (
            "Local governed strategy registry", "Local immutable strategy-definition vault",
            "Deterministic registry identities", "Separate non-executable research backlog",
            "Registry dashboard and read-only API",
        ):
            self.assertIn(implemented, manifest["implemented"])
        for unavailable in (
            "External/live market data", "MT5 integration", "News feeds", "Strategy optimization",
            "Strategy ranking", "Regime selection", "Forward paper portfolio service",
            "Broker connectivity", "Order proposals", "Assisted execution", "Automated execution",
            "Cloud backend", "Accounts and authentication", "Subscriptions and payments",
            "Telemetry and analytics", "Customer distribution approval",
        ):
            self.assertIn(unavailable, manifest["not_implemented"])
        for field in (
            "live_market_data_capability", "mt5_capability", "news_feed_capability",
            "strategy_ranking_capability", "strategy_optimization_capability", "regime_selection_capability",
            "order_proposal_capability", "cloud_backend_capability", "telemetry",
        ):
            self.assertIs(manifest[field], False)

    def test_catalog_modules_have_no_dynamic_loading_or_outbound_surface(self):
        forbidden_calls = {"eval", "exec", "compile", "__import__"}
        forbidden_imports = {"pickle", "marshal", "subprocess", "requests", "urllib", "socket"}
        for path in (APP_DIRECTORY / "strategy_registry.py", APP_DIRECTORY / "strategy_vault.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = set()
            calls = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
                elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                    calls.add(node.func.id)
            self.assertTrue(imports.isdisjoint(forbidden_imports), (path, imports))
            self.assertTrue(calls.isdisjoint(forbidden_calls), (path, calls))


class ReleaseOneParityTests(unittest.TestCase):
    def test_two_complete_results_semantic_parity_and_no_input_mutation(self):
        kernel = service._kernel_module()
        pack = service._load_demo_pack()
        strategy = copy.deepcopy(service.DEMO_STRATEGY)
        original_pack = copy.deepcopy(pack)
        original_strategy = copy.deepcopy(strategy)
        first = kernel.run_backtest(copy.deepcopy(strategy), copy.deepcopy(pack), risk_policy=None)
        second = kernel.run_backtest(copy.deepcopy(strategy), copy.deepcopy(pack), risk_policy=None)
        self.assertEqual(first, second)
        self.assertEqual(pack, original_pack)
        self.assertEqual(strategy, original_strategy)
        metadata = first["metadata"]
        self.assertEqual(metadata["input_data_hash"], "6cdbca208cd1029b90e5ed3494ab05a3b7042d224ed01293373fc173a85aee56")
        self.assertEqual(metadata["configuration_hash"], "3f4c513f275ca034af9fd2f4bbcb4ec382c361969d7706fbb6fb6d26fd26bbbd")
        self.assertEqual(metadata["strategy_definition_hash"], EXPECTED_KERNEL_HASH)
        self.assertEqual(metadata["engine_source_digest"], "f9f555d37e0820c39eb2afe1156fca4912d255debc23c7ab27c6111c31da3952")
        self.assertEqual(metadata["run_id"], "TRL-RUN-6922AEA31AE2630B4DA1")
        self.assertEqual((first["outcome"], first["reason_code"]), ("HYPOTHETICAL_FILL", "OPEN_TERMINAL_POSITION"))
        self.assertEqual((len(first["decisions"]), len(first["hypothetical_fills"]), len(first["trade_list"]), len(first["equity_curve"])), (2, 1, 0, 60))
        self.assertEqual((first["final_cash"], first["final_equity"]), (94.9975, 100.22673707083118))
        semantic_digest = hashlib.sha256(kernel.canonical_json(without_provenance(first)).encode("utf-8")).hexdigest()
        self.assertEqual(semantic_digest, "6f66351873fb49dc11fcc7f3c0e3c84d0add65b4e0b315bf78da7008070d5331")

    def test_registry_validation_creates_no_repository_artifacts(self):
        registry.load_registry(copy.deepcopy(service.DEMO_STRATEGY))
        forbidden = []
        for path in BASE.rglob("*"):
            lowered = path.name.lower()
            if path.is_dir() and lowered in {"__pycache__", ".pytest_cache", ".mypy_cache"}:
                forbidden.append(path)
            elif path.is_file() and path.suffix.lower() in {".pyc", ".pyo"}:
                forbidden.append(path)
        self.assertEqual(forbidden, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
