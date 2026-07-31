"""Deterministic contract tests for the TRL Phase 3 operating-mode state machine."""

from datetime import datetime, timezone
import http.client
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest import mock


BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

import test_forward_paper  # noqa: E402,F401  (import-cleanliness check, item 26)
import test_trading_lab_app  # noqa: E402,F401  (import-cleanliness check, item 26)
from trading_lab_app import app  # noqa: E402
from trading_lab_app import mode_service as ms  # noqa: E402
from trading_lab_app import server as srv  # noqa: E402
from trading_lab_app import service  # noqa: E402


APP_DIRECTORY = BASE / "trading_lab_app"


def _running_server(mode_service=None, paper_service=None):
    httpd = srv.create_server(0, mode_service=mode_service, paper_service=paper_service)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd, thread


def _stop_server(httpd, thread):
    httpd.shutdown()
    httpd.server_close()
    thread.join(timeout=3)


def _request(port, method, path):
    connection = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    connection.request(method, path)
    response = connection.getresponse()
    body = response.read()
    result = response.status, dict(response.getheaders()), body
    connection.close()
    return result


class ModeVocabularyTests(unittest.TestCase):
    def test_all_seven_modes_validate(self):
        # Item 1
        self.assertEqual(len(ms.MODES), 7)
        for mode in ms.MODES:
            self.assertEqual(ms.validate_mode(mode), mode)
        self.assertEqual(
            set(ms.MODES),
            {
                "OFF", "RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL",
                "MT5_DEMO_AUTOMATED", "MT5_LIVE_MANUAL", "MT5_LIVE_AUTOMATED",
            },
        )

    def test_unknown_mode_rejected(self):
        # Item 2
        with self.assertRaises(ms.ModeValidationError):
            ms.validate_mode("NOT_A_REAL_MODE")
        service_instance = ms.in_memory_mode_service()
        result = service_instance.request_transition("NOT_A_REAL_MODE", actor="tester")
        self.assertEqual(result.outcome, "REJECTED")
        self.assertEqual(result.reason_code, "UNKNOWN_MODE")
        self.assertEqual(service_instance.current_mode, "OFF")

    def test_reason_code_vocabulary_is_stable(self):
        expected = {
            "UNKNOWN_MODE", "MODE_UNAVAILABLE", "MISSING_MT5_ADAPTER",
            "MISSING_LIVE_ARMING", "MISSING_PRIVATE_AUTH", "INVALID_TRANSITION",
            "PERSISTED_STATE_INVALID", "PERSISTENCE_FAILED",
            "SUBSYSTEM_ACTIVATION_FAILED", "STARTUP_LIVE_AUTOMATION_FORBIDDEN",
            "CAPABILITY_DENIED", "MODE_CHANGE_REQUIRES_LOCAL_OPERATOR",
        }
        self.assertEqual(set(ms.REASON_CODES), expected)

    def test_event_type_vocabulary_is_stable(self):
        expected = {
            "MODE_STATE_LOADED", "MODE_STATE_DEFAULTED", "MODE_STATE_CORRUPTION_RECOVERED",
            "MODE_TRANSITION_REQUESTED", "MODE_TRANSITION_ACCEPTED", "MODE_TRANSITION_REJECTED",
            "MODE_TRANSITION_COMPLETED", "MODE_TRANSITION_ROLLED_BACK",
            "MODE_CAPABILITY_UNAVAILABLE", "MODE_STARTUP_SAFE_DOWNGRADE",
        }
        self.assertEqual(set(ms.EVENT_TYPES), expected)


class StartupResolutionTests(unittest.TestCase):
    def test_default_startup_is_off(self):
        # Item 3
        service_instance = ms.in_memory_mode_service()
        self.assertEqual(service_instance.current_mode, "OFF")
        history = service_instance.transition_history()
        self.assertEqual(history[-1]["event_type"], "MODE_STATE_DEFAULTED")
        self.assertEqual(history[-1]["payload"]["resulting_mode"], "OFF")

    def test_corrupted_persisted_state_resolves_to_off(self):
        # Item 4
        store = ms.InMemoryModeStateStore()
        store.replace_raw_for_test({"garbage": "not a governed mode store document"})
        service_instance = ms.ModeService(store=store)
        self.assertEqual(service_instance.current_mode, "OFF")
        self.assertEqual(service_instance.startup_diagnostic_code, "PERSISTED_STATE_INVALID")
        history = service_instance.transition_history()
        self.assertEqual(history[-1]["event_type"], "MODE_STATE_CORRUPTION_RECOVERED")
        self.assertEqual(
            history[-1]["payload"]["rejection_reason_code"], "PERSISTED_STATE_INVALID"
        )

    def test_restart_cannot_restore_live_automated_execution(self):
        # Item 12
        store = ms.InMemoryModeStateStore()
        seed = ms.ModeService(store=store, session_started_at_utc="2020-01-01T00:00:00.000000Z")
        now = ms.format_utc(datetime.now(timezone.utc))
        seed._log.append("MODE_TRANSITION_COMPLETED", now, {
            "requested_mode": "MT5_LIVE_AUTOMATED",
            "previous_mode": "OFF",
            "resulting_mode": "MT5_LIVE_AUTOMATED",
            "actor": "forged",
            "transition_id": "forged-id",
            "capability_snapshot": [],
        })
        store.save(ms.storage_document(seed._session_started_at_utc, seed._log))
        restarted = ms.ModeService(store=store)
        self.assertEqual(restarted.current_mode, "OFF")
        history = restarted.transition_history()
        self.assertEqual(history[-1]["event_type"], "MODE_STARTUP_SAFE_DOWNGRADE")
        self.assertEqual(
            history[-1]["payload"]["rejection_reason_code"], "STARTUP_LIVE_AUTOMATION_FORBIDDEN"
        )
        self.assertEqual(history[-1]["payload"]["loaded_mode"], "MT5_LIVE_AUTOMATED")

    def test_restart_cannot_restore_any_mt5_mode(self):
        for mt5_mode in ms.MT5_MODES:
            with self.subTest(mode=mt5_mode):
                store = ms.InMemoryModeStateStore()
                seed = ms.ModeService(store=store, session_started_at_utc="2020-01-01T00:00:00.000000Z")
                now = ms.format_utc(datetime.now(timezone.utc))
                seed._log.append("MODE_TRANSITION_COMPLETED", now, {
                    "requested_mode": mt5_mode, "previous_mode": "OFF",
                    "resulting_mode": mt5_mode, "actor": "forged",
                    "transition_id": "forged-id", "capability_snapshot": [],
                })
                store.save(ms.storage_document(seed._session_started_at_utc, seed._log))
                restarted = ms.ModeService(store=store)
                self.assertEqual(restarted.current_mode, "OFF")


class CapabilityMatrixTests(unittest.TestCase):
    def test_off_grants_no_capabilities(self):
        # Item 5
        self.assertEqual(ms.capabilities_for("OFF"), frozenset())

    def test_research_capabilities(self):
        # Item 6
        granted = ms.capabilities_for("RESEARCH")
        self.assertIn("historical_research", granted)
        self.assertIn("strategy_evaluation", granted)
        self.assertNotIn("forward_paper_fills", granted)
        self.assertNotIn("manual_broker_execution", granted)
        self.assertNotIn("automated_broker_execution", granted)

    def test_synthetic_paper_capabilities_and_subsystem_builder(self):
        # Item 7
        granted = ms.capabilities_for("SYNTHETIC_PAPER")
        self.assertIn("synthetic_evidence", granted)
        self.assertIn("forward_paper_fills", granted)
        self.assertNotIn("mt5_read_only_access", granted)
        self.assertNotIn("live_market_data_read", granted)

        built = []
        service_instance = ms.in_memory_mode_service(
            subsystem_builder=lambda mode: built.append(mode)
        )
        service_instance.request_transition("SYNTHETIC_PAPER", actor="tester")
        self.assertEqual(built, ["SYNTHETIC_PAPER"])

    def test_mt5_demo_manual_represented_but_unavailable(self):
        # Item 8
        self.assertIn("MT5_DEMO_MANUAL", ms.MODES)
        self.assertFalse(ms.is_available("MT5_DEMO_MANUAL"))
        self.assertEqual(ms.unavailable_reasons("MT5_DEMO_MANUAL"), ("MISSING_MT5_ADAPTER",))

    def test_mt5_demo_automated_represented_but_unavailable(self):
        # Item 9
        self.assertIn("MT5_DEMO_AUTOMATED", ms.MODES)
        self.assertFalse(ms.is_available("MT5_DEMO_AUTOMATED"))
        self.assertEqual(
            ms.unavailable_reasons("MT5_DEMO_AUTOMATED"),
            ("MISSING_MT5_ADAPTER", "MISSING_LIVE_ARMING"),
        )

    def test_mt5_live_manual_represented_but_unavailable(self):
        # Item 10
        self.assertIn("MT5_LIVE_MANUAL", ms.MODES)
        self.assertFalse(ms.is_available("MT5_LIVE_MANUAL"))
        self.assertEqual(ms.unavailable_reasons("MT5_LIVE_MANUAL"), ("MISSING_MT5_ADAPTER",))

    def test_mt5_live_automated_represented_but_unavailable(self):
        # Item 11
        self.assertIn("MT5_LIVE_AUTOMATED", ms.MODES)
        self.assertFalse(ms.is_available("MT5_LIVE_AUTOMATED"))
        self.assertEqual(
            ms.unavailable_reasons("MT5_LIVE_AUTOMATED"),
            ("MISSING_MT5_ADAPTER", "MISSING_LIVE_ARMING"),
        )
        service_instance = ms.in_memory_mode_service()
        status = service_instance.mode_status_document()
        self.assertFalse(status["broker_execution_available"])
        self.assertFalse(status["automated_trading_available"])
        self.assertFalse(status["live_arming_available"])
        self.assertFalse(status["private_remote_access_available"])

    def test_capability_matrix_denies_unlisted(self):
        # Item 17
        for mode in ms.MODES:
            with self.subTest(mode=mode):
                granted = ms.capabilities_for(mode)
                for capability in ms.CAPABILITIES:
                    if capability not in granted:
                        self.assertNotIn(capability, granted)
        # tradingview_proposal_intake and private_remote_access are Phase
        # 7/8 concepts: no mode in this checkpoint grants either, ever.
        for mode in ms.MODES:
            granted = ms.capabilities_for(mode)
            self.assertNotIn("tradingview_proposal_intake", granted)
            self.assertNotIn("private_remote_access", granted)
        service_instance = ms.in_memory_mode_service()
        self.assertFalse(service_instance.has_capability("automated_broker_execution"))
        self.assertFalse(service_instance.has_capability("tradingview_proposal_intake"))
        self.assertFalse(service_instance.has_capability("private_remote_access"))
        with self.assertRaises(ms.ModeValidationError):
            service_instance.has_capability("not_a_real_capability")

    def test_direct_calls_cannot_bypass_capability_denial(self):
        # Item 18: even a direct internal call bypassing the CLI cannot make
        # MT5_LIVE_AUTOMATED (or any MT5 mode) current, so its capability
        # row — which does list mt5_order_send for future phases — can never
        # actually be exercised: has_capability against the *current* mode
        # (never an MT5 mode in Phase 3) always denies it.
        service_instance = ms.in_memory_mode_service()
        self.assertFalse(service_instance.has_capability("mt5_order_send"))
        self.assertFalse(service_instance.has_capability("automated_broker_execution"))
        result = service_instance.request_transition("MT5_LIVE_AUTOMATED", actor="tester")
        self.assertEqual(result.outcome, "REJECTED")
        self.assertNotEqual(service_instance.current_mode, "MT5_LIVE_AUTOMATED")
        # No private/internal method exists to set current mode directly
        # without going through request_transition's gates.
        self.assertFalse(hasattr(service_instance, "set_mode"))
        self.assertFalse(hasattr(service_instance, "force_mode"))


class TransitionRuleTests(unittest.TestCase):
    def test_unavailable_transition_leaves_mode_unchanged(self):
        # Item 13
        service_instance = ms.in_memory_mode_service()
        service_instance.request_transition("RESEARCH", actor="tester")
        before = service_instance.current_mode
        result = service_instance.request_transition("MT5_DEMO_MANUAL", actor="tester")
        self.assertEqual(result.outcome, "REJECTED")
        self.assertEqual(result.reason_code, "MISSING_MT5_ADAPTER")
        self.assertEqual(service_instance.current_mode, before)

    def test_failed_persistence_leaves_mode_unchanged(self):
        # Item 14
        store = ms.InMemoryModeStateStore()
        service_instance = ms.ModeService(store=store)
        store.fail_writes = True
        result = service_instance.request_transition("RESEARCH", actor="tester")
        self.assertEqual(result.outcome, "ROLLED_BACK")
        self.assertEqual(result.reason_code, "PERSISTENCE_FAILED")
        self.assertEqual(service_instance.current_mode, "OFF")

    def test_failed_subsystem_activation_rolls_back_safely(self):
        # Item 15
        def failing_builder(_mode):
            raise RuntimeError("simulated activation failure")

        service_instance = ms.in_memory_mode_service(subsystem_builder=failing_builder)
        result = service_instance.request_transition("SYNTHETIC_PAPER", actor="tester")
        self.assertEqual(result.outcome, "ROLLED_BACK")
        self.assertEqual(result.reason_code, "SUBSYSTEM_ACTIVATION_FAILED")
        self.assertEqual(service_instance.current_mode, "OFF")
        history = service_instance.transition_history()
        self.assertEqual(history[-1]["event_type"], "MODE_TRANSITION_ROLLED_BACK")

    def test_off_reachable_from_every_available_mode(self):
        # Item 16
        for mode in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
            with self.subTest(mode=mode):
                self.assertIn("OFF", ms.allowed_destinations(mode) | {"OFF"})
        for mode in ("RESEARCH", "SYNTHETIC_PAPER"):
            self.assertIn("OFF", ms.allowed_destinations(mode))

    def test_exact_transition_matrix(self):
        self.assertEqual(ms.allowed_destinations("OFF"), frozenset({"RESEARCH", "SYNTHETIC_PAPER"}))
        self.assertEqual(ms.allowed_destinations("RESEARCH"), frozenset({"OFF", "SYNTHETIC_PAPER"}))
        self.assertEqual(ms.allowed_destinations("SYNTHETIC_PAPER"), frozenset({"OFF", "RESEARCH"}))
        for mt5_mode in ms.MT5_MODES:
            self.assertEqual(ms.allowed_destinations(mt5_mode), frozenset())

    def test_repeated_identical_transition_is_deterministic(self):
        # Item 19
        service_instance = ms.in_memory_mode_service()
        first = service_instance.request_transition("MT5_LIVE_AUTOMATED", actor="tester")
        second = service_instance.request_transition("MT5_LIVE_AUTOMATED", actor="tester")
        self.assertEqual(first.outcome, second.outcome)
        self.assertEqual(first.reason_code, second.reason_code)
        service_instance.request_transition("RESEARCH", actor="tester")
        same_mode_again = service_instance.request_transition("RESEARCH", actor="tester")
        self.assertEqual(same_mode_again.outcome, "REJECTED")
        self.assertEqual(same_mode_again.reason_code, "INVALID_TRANSITION")

    def test_actor_channel_gate_rejects_non_local_operator(self):
        service_instance = ms.in_memory_mode_service()
        for channel in ("HTTP", "REMOTE", "BROWSER", ""):
            with self.subTest(channel=channel):
                result = service_instance.request_transition(
                    "RESEARCH", actor="x", actor_channel=channel
                )
                self.assertEqual(result.outcome, "REJECTED")
                self.assertEqual(result.reason_code, "MODE_CHANGE_REQUIRES_LOCAL_OPERATOR")
                self.assertEqual(service_instance.current_mode, "OFF")


class AuditAndPersistenceTests(unittest.TestCase):
    def test_audit_events_are_json_serializable_and_deterministic(self):
        # Item 24
        service_instance = ms.in_memory_mode_service(
            session_started_at_utc="2026-01-01T00:00:00.000000Z"
        )
        service_instance.request_transition("RESEARCH", actor="tester", reason="go")
        history = service_instance.transition_history()
        encoded = json.dumps(history, sort_keys=True)
        self.assertTrue(encoded)
        second_encode = json.dumps(history, sort_keys=True)
        self.assertEqual(encoded, second_encode)
        for event in history:
            self.assertEqual(event["schema_version"], ms.MODE_EVENT_SCHEMA)
            self.assertIn(event["event_type"], ms.EVENT_TYPES)

    def test_state_file_has_no_secret_fields(self):
        # Item 25
        store = ms.InMemoryModeStateStore()
        service_instance = ms.ModeService(store=store)
        service_instance.request_transition("RESEARCH", actor="tester", reason="operator requested research mode")
        document = store.load()
        encoded = json.dumps(document).lower()
        for forbidden in ("password", "secret", "credential", "api_key", "apikey", "token"):
            self.assertNotIn(forbidden, encoded)

    def test_storage_round_trip_preserves_current_mode(self):
        store = ms.InMemoryModeStateStore()
        first = ms.ModeService(store=store, session_started_at_utc="2026-01-01T00:00:00.000000Z")
        first.request_transition("RESEARCH", actor="tester")
        second = ms.ModeService(store=store)
        self.assertEqual(second.current_mode, "RESEARCH")


class HttpAndDashboardIntegrationTests(unittest.TestCase):
    def test_mode_status_reflects_server_authority_over_http(self):
        # Item 20
        mode_service = ms.in_memory_mode_service()
        mode_service.request_transition("RESEARCH", actor="tester")
        httpd, thread = _running_server(mode_service=mode_service)
        try:
            status, _, body = _request(httpd.server_address[1], "GET", "/api/mode-status")
            self.assertEqual(status, 200)
            document = json.loads(body)
            self.assertEqual(document["current_mode"], "RESEARCH")
            self.assertFalse(document["broker_execution_available"])
        finally:
            _stop_server(httpd, thread)

    def test_no_http_mutation_route_for_mode(self):
        # Item 21
        httpd, thread = _running_server()
        try:
            for method in ("POST", "PUT", "PATCH", "DELETE"):
                status, headers, _ = _request(httpd.server_address[1], method, "/api/mode-status")
                self.assertEqual(status, 405)
                self.assertEqual(headers["Allow"], "GET, HEAD")
            self.assertEqual(set(srv.MODE_API_ROUTES), {"/api/mode-status"})
        finally:
            _stop_server(httpd, thread)

    def test_start_status_stop_rehearsal_via_http(self):
        # Item 27 (automated equivalent of the manual loopback rehearsal)
        mode_service = ms.in_memory_mode_service()
        httpd, thread = _running_server(mode_service=mode_service)
        try:
            status, _, body = _request(httpd.server_address[1], "GET", "/api/health")
            self.assertEqual(status, 200)
            status, _, body = _request(httpd.server_address[1], "GET", "/api/mode-status")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["current_mode"], "OFF")
        finally:
            _stop_server(httpd, thread)

    def test_synthetic_mode_dashboard_warning_present(self):
        # Item 22
        html = (APP_DIRECTORY / "static" / "index.html").read_text(encoding="utf-8")
        self.assertIn(
            "SYNTHETIC DEMONSTRATION",
            (APP_DIRECTORY / "synthetic_paper_demonstration.json").read_text(encoding="utf-8"),
        )
        self.assertIn("PAPER ONLY", html)
        self.assertIn('id="operating-mode"', html)
        self.assertIn("no MT5 execution adapter or live-arming capability exists yet", html)

    def test_off_and_research_do_not_expose_synthetic_paper_as_active(self):
        # Item 23
        from trading_lab_app.paper_service import DisabledPaperService
        for mode in ("OFF", "RESEARCH"):
            with self.subTest(mode=mode):
                paper = DisabledPaperService()
                document = service.paper_account_document(paper)
                self.assertFalse(document["enabled"])
                self.assertFalse(document.get("synthetic_demonstration_values", False))


class ScopeBoundaryTests(unittest.TestCase):
    def test_existing_r2_005_test_modules_import_cleanly(self):
        # Item 26 — evidenced primarily by the full-suite run; this at
        # least confirms the modules this file imports are intact.
        self.assertTrue(hasattr(test_forward_paper, "ForwardFillAndAccountingTests"))
        self.assertTrue(hasattr(test_trading_lab_app, "ServiceContractTests"))

    def test_no_mt5_module_import_in_mode_service(self):
        # Item 29
        source = (APP_DIRECTORY / "mode_service.py").read_text(encoding="utf-8")
        self.assertNotIn("MetaTrader5", source)
        self.assertNotIn("import mt5_service", source)

    def test_mode_modules_have_no_outbound_network_import_surface(self):
        # Item 30
        import ast
        for filename in ("mode_service.py", "mode_cli.py"):
            path = APP_DIRECTORY / filename
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module.split(".")[0])
            self.assertTrue(
                imports.isdisjoint({"requests", "urllib3", "aiohttp", "ftplib", "smtplib", "socket"}),
                (filename, imports),
            )

    def test_mode_service_module_has_no_broker_call_surface(self):
        # The CAPABILITY_MATRIX legitimately names capabilities like
        # "mt5_order_send" as *identifiers*; the real guarantee is that no
        # actual broker call site (a dotted method call) exists.
        source = (APP_DIRECTORY / "mode_service.py").read_text(encoding="utf-8")
        for forbidden in (
            ".order_send(", ".order_check(", ".positions_get(", ".history_deals_get(",
        ):
            self.assertNotIn(forbidden, source)


class SingleAuthorityTests(unittest.TestCase):
    """Founder correction: legacy CLI flags must not bypass ModeService."""

    def _isolated_localappdata(self):
        tmpdir = tempfile.mkdtemp()
        return tmpdir, mock.patch.dict(os.environ, {"LOCALAPPDATA": tmpdir})

    def _fake_server(self):
        fake_server = mock.Mock()
        fake_server.server_address = ("127.0.0.1", 8765)
        fake_server.serve_forever.side_effect = KeyboardInterrupt
        return fake_server

    def test_off_cannot_construct_active_paper_service(self):
        # Item 1
        service_instance = app._paper_service_for_mode("OFF")
        self.assertFalse(service_instance.enabled)

    def test_research_cannot_construct_active_paper_service(self):
        # Item 2
        service_instance = app._paper_service_for_mode("RESEARCH")
        self.assertFalse(service_instance.enabled)

    def test_synthetic_paper_constructs_only_synthetic_demonstration_service(self):
        # Item 3
        service_instance = app._paper_service_for_mode("SYNTHETIC_PAPER")
        self.assertTrue(service_instance.enabled)
        self.assertTrue(service_instance.is_synthetic_demonstration)

    def test_demo_flag_routes_through_mode_service(self):
        # Item 4
        tmpdir, patcher = self._isolated_localappdata()
        with patcher, mock.patch(
            "trading_lab_app.app.create_server", return_value=self._fake_server(),
        ) as mocked_create:
            code = app.main(["--enable-forward-paper-demo", "--no-browser"])
        self.assertEqual(code, 0)
        called_kwargs = mocked_create.call_args.kwargs
        self.assertIsInstance(called_kwargs["paper_service"], type(
            app._paper_service_for_mode("SYNTHETIC_PAPER")
        ))
        self.assertIsInstance(called_kwargs["mode_service"], ms.ModeService)

    def test_demo_flag_results_in_current_mode_synthetic_paper(self):
        # Item 5
        tmpdir, patcher = self._isolated_localappdata()
        with patcher:
            with mock.patch(
                "trading_lab_app.app.create_server", return_value=self._fake_server(),
            ):
                code = app.main(["--enable-forward-paper-demo", "--no-browser"])
            self.assertEqual(code, 0)
            reloaded = ms.ModeService()
            self.assertEqual(reloaded.current_mode, "SYNTHETIC_PAPER")

    def test_demo_flag_creates_normal_transition_audit_events(self):
        # Item 6
        tmpdir, patcher = self._isolated_localappdata()
        with patcher:
            with mock.patch(
                "trading_lab_app.app.create_server", return_value=self._fake_server(),
            ):
                app.main(["--enable-forward-paper-demo", "--no-browser"])
            reloaded = ms.ModeService()
            history = reloaded.transition_history()
            event_types = [event["event_type"] for event in history]
            self.assertIn("MODE_TRANSITION_REQUESTED", event_types)
            self.assertIn("MODE_TRANSITION_ACCEPTED", event_types)
            self.assertIn("MODE_TRANSITION_COMPLETED", event_types)
            completed = next(
                event for event in history if event["event_type"] == "MODE_TRANSITION_COMPLETED"
            )
            self.assertIn("LEGACY_CLI_FLAG", completed["payload"]["actor"])

    def test_demo_flag_cannot_bypass_a_failed_transition(self):
        # Item 7
        fake_result = ms.TransitionResult(
            outcome="REJECTED", transition_id="forced-rejection-id",
            requested_mode="SYNTHETIC_PAPER", previous_mode="OFF",
            resulting_mode="OFF", reason_code="INVALID_TRANSITION",
        )
        tmpdir, patcher = self._isolated_localappdata()
        with patcher, mock.patch.object(
            ms.ModeService, "request_transition", return_value=fake_result,
        ), mock.patch("trading_lab_app.app.create_server") as mocked_create:
            code = app.main(["--enable-forward-paper-demo", "--no-browser"])
        self.assertEqual(code, 2)
        mocked_create.assert_not_called()

    def test_engine_flag_fails_closed_before_server_startup(self):
        # Item 8
        with mock.patch("trading_lab_app.app.create_server") as mocked_create:
            code = app.main(["--enable-forward-paper-engine", "--no-browser"])
        self.assertEqual(code, 2)
        mocked_create.assert_not_called()

    def test_engine_flag_creates_no_paper_store_network_call_or_execution(self):
        # Item 9
        tmpdir, patcher = self._isolated_localappdata()
        state_path = Path(tmpdir) / "ALSAKKAF" / "TradingLab" / "operating-mode-state-v1.json"
        with patcher, mock.patch("trading_lab_app.app.create_server") as mocked_create:
            code = app.main(["--enable-forward-paper-engine", "--no-browser"])
        self.assertEqual(code, 2)
        mocked_create.assert_not_called()
        self.assertFalse(state_path.exists())

    def test_mode_status_and_paper_status_cannot_disagree(self):
        # Item 10
        for mode_name in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
            with self.subTest(mode=mode_name):
                mode_service_instance = ms.in_memory_mode_service(
                    subsystem_builder=app._paper_service_for_mode
                )
                if mode_name != "OFF":
                    result = mode_service_instance.request_transition(
                        mode_name, actor="tester"
                    )
                    self.assertEqual(result.outcome, "ACCEPTED")
                paper_service_instance = app._paper_service_for_mode(
                    mode_service_instance.current_mode
                )
                httpd, thread = _running_server(
                    mode_service=mode_service_instance, paper_service=paper_service_instance,
                )
                try:
                    _, _, mode_body = _request(httpd.server_address[1], "GET", "/api/mode-status")
                    _, _, paper_body = _request(httpd.server_address[1], "GET", "/api/paper-account")
                    mode_document = json.loads(mode_body)
                    paper_document = json.loads(paper_body)
                    self.assertEqual(mode_document["current_mode"], mode_name)
                    if mode_name == "SYNTHETIC_PAPER":
                        self.assertTrue(paper_document["enabled"])
                        self.assertTrue(paper_document.get("synthetic_demonstration_values"))
                    else:
                        self.assertFalse(paper_document["enabled"])
                finally:
                    _stop_server(httpd, thread)

    def test_direct_helper_calls_cannot_construct_disallowed_service(self):
        # Item 11
        with self.assertRaises(app.ModeSubsystemConfigurationError):
            app._paper_service_for_mode("MT5_LIVE_AUTOMATED")
        with self.assertRaises(app.ModeSubsystemConfigurationError):
            app._paper_service_for_mode("MT5_LIVE_MANUAL")
        self.assertFalse(app._paper_service_for_mode("OFF").enabled)
        self.assertFalse(app._paper_service_for_mode("RESEARCH").enabled)

    def test_deliberate_mismatch_fails_with_configuration_mismatch(self):
        # Item 12
        from trading_lab_app.paper_service import DisabledPaperService

        with self.assertRaises(app.ModeSubsystemConfigurationError) as context:
            app._validate_subsystem_consistency("SYNTHETIC_PAPER", DisabledPaperService())
        self.assertIn(app.MODE_SUBSYSTEM_CONFIGURATION_MISMATCH, str(context.exception))
        with self.assertRaises(app.ModeSubsystemConfigurationError):
            app._validate_subsystem_consistency(
                "OFF", app._paper_service_for_mode("SYNTHETIC_PAPER")
            )

    def test_synthetic_demonstration_still_deterministic(self):
        # Item 13
        from trading_lab_app.paper_service import run_synthetic_demonstration

        first = run_synthetic_demonstration()
        second = run_synthetic_demonstration()
        self.assertEqual(first, second)

    def test_no_eighth_mode_introduced(self):
        # Item 14
        self.assertEqual(len(ms.MODES), 7)
        self.assertEqual(
            set(ms.MODES),
            {
                "OFF", "RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL",
                "MT5_DEMO_AUTOMATED", "MT5_LIVE_MANUAL", "MT5_LIVE_AUTOMATED",
            },
        )

    def test_no_http_mode_mutation_route_introduced(self):
        # Item 15
        self.assertEqual(set(srv.MODE_API_ROUTES), {"/api/mode-status"})
        httpd, thread = _running_server()
        try:
            for method in ("POST", "PUT", "PATCH", "DELETE"):
                status, headers, _ = _request(httpd.server_address[1], method, "/api/mode-status")
                self.assertEqual(status, 405)
                self.assertEqual(headers["Allow"], "GET, HEAD")
        finally:
            _stop_server(httpd, thread)


if __name__ == "__main__":
    unittest.main(verbosity=2)
