"""Tests for the TRL-R2-013 ALSAKKAF SCALPING operational dashboard hotfix:
safe launcher sequencing, the corrected MT5-connection-vs-journal-health
indicator, persisted configuration, the Demo Auto dashboard lock, and safe
new-rendering conventions."""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

import alsakkaf_scalping_test_support as support
from trading_lab_app import alsakkaf_scalping_mt5 as mt5a
from trading_lab_app import alsakkaf_scalping_service as scalping_service
from trading_lab_app.alsakkaf_scalping_data import (
    InMemorySymbolMapStore, ScalpingConfigStore, SymbolMapStore,
)
from trading_lab_app.alsakkaf_scalping_journal import in_memory_journal_writer
from trading_lab_app.alsakkaf_scalping_runtime import ScalpingRuntime

TRADING_LAB_DIRECTORY = Path(__file__).resolve().parent
STATIC_DIRECTORY = TRADING_LAB_DIRECTORY / "trading_lab_app" / "static"
START_SCRIPT = TRADING_LAB_DIRECTORY / "Start_ALSAKKAF_SCALPING_DEMO.ps1"
STOP_SCRIPT = TRADING_LAB_DIRECTORY / "Stop_ALSAKKAF_SCALPING_DEMO.ps1"


class LauncherScriptTests(unittest.TestCase):
    """The R2-012 launcher never requested any mode/state transition at
    all (the Founder-observed root cause). These tests grep the corrected
    script text rather than actually launching MT5/PowerShell, matching
    how this repository already tests its other .ps1 launchers."""

    def test_start_script_requests_research_mode(self):
        text = START_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("mode_cli request-mode RESEARCH", text)

    def test_start_script_requests_analyze_only_product_state(self):
        text = START_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("alsakkaf_scalping_cli scalping-resume", text)

    def test_start_script_never_requests_demo_auto(self):
        text = START_SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("scalping-start-demo-auto", text)
        self.assertNotIn("request-mode MT5_DEMO_AUTOMATED", text)

    def test_start_script_runs_a_real_recheck_before_reporting_status(self):
        text = START_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("scalping-recheck", text)

    def test_start_script_opens_directly_at_scalping_fragment(self):
        text = START_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("--open-fragment", text)
        self.assertIn("alsakkaf-scalping", text)

    def test_stop_script_stops_monitoring_and_requests_off(self):
        text = STOP_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("scalping-monitoring-stop", text)
        self.assertIn("mode_cli request-mode OFF", text)
        self.assertIn("scalping-stop", text)


class Mt5ConnectionVsJournalHealthTests(unittest.TestCase):
    """Root cause 2: the R2-012 dashboard's 'MT5 CONNECTION: OK' badge was
    wired to journal_startup_diagnostic_code, never to a real terminal/
    account read."""

    def test_healthy_journal_but_disconnected_mt5_is_not_ok(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        adapter.terminal["connected"] = False
        self.assertEqual(service.status_document()["journal_startup_diagnostic_code"], "OK")
        self.assertFalse(service.mt5_connected())

    def test_connected_mt5_reported_even_if_journal_unhealthy(self):
        class _FailingJournal:
            events = []
            startup_diagnostic_code = "PERSISTED_STATE_INVALID"

            def acquire_mutation_lock(self):
                raise AssertionError("not used by this test")

            def shutdown(self):
                return True

        service = scalping_service.ScalpingService(
            journal=_FailingJournal(), adapter=support.make_fake_adapter(),
            symbol_map_store=InMemorySymbolMapStore(),
        )
        self.assertTrue(service.mt5_connected())
        self.assertEqual(service.status_document()["journal_startup_diagnostic_code"], "PERSISTED_STATE_INVALID")

    def test_disabled_adapter_never_reports_mt5_ok(self):
        service = scalping_service.ScalpingService(
            journal=in_memory_journal_writer(), adapter=mt5a.disabled_adapter(),
            symbol_map_store=InMemorySymbolMapStore(),
        )
        self.assertFalse(service.mt5_connected())

    def test_unknown_account_type_is_not_demo_verified(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        adapter.account["trade_mode"] = None
        adapter.account["trade_mode_name"] = None
        self.assertFalse(service.mt5_connected())
        runtime = ScalpingRuntime(service)
        document = runtime.live_status_document("XAUUSD")
        self.assertFalse(document["demo_verified"])


class ConfigurationPersistenceTests(unittest.TestCase):
    def test_profile_side_and_monitoring_interval_survive_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            config_path = Path(tmp) / "scalping-configuration-v1.json"
            map_path = Path(tmp) / "scalping-symbol-map-v1.json"

            first = scalping_service.ScalpingService(
                journal=in_memory_journal_writer(), adapter=support.make_fake_adapter(),
                symbol_map_store=SymbolMapStore(path=map_path),
                config_store=ScalpingConfigStore(path=config_path),
            )
            first.save_symbol_map("XAUUSD", "XAUUSDm")
            first.configure_profile("XAUUSD", "ALSAKKAF_INTRADAY", risk_overrides={"risk_per_cycle_pct": Decimal("0.10")})
            first.configure_side("XAUUSD", "BUY_ONLY")
            first.set_monitoring_interval_seconds(30)

            second = scalping_service.ScalpingService(
                journal=in_memory_journal_writer(), adapter=support.make_fake_adapter(),
                symbol_map_store=SymbolMapStore(path=map_path),
                config_store=ScalpingConfigStore(path=config_path),
            )
            self.assertEqual(second.profile_for("XAUUSD"), "ALSAKKAF_INTRADAY")
            self.assertEqual(second.side_restriction_for("XAUUSD"), "BUY_ONLY")
            self.assertEqual(second.monitoring_interval_seconds, 30)
            self.assertEqual(second.configuration_document()["risk_settings"]["risk_per_cycle_pct"], "0.10")

    def test_configuration_editing_blocked_during_demo_auto(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        # Journal-level direct append to reach DEMO_AUTO without ever
        # calling order_check/order_send (this checkpoint's tests never
        # exercise DEMO_AUTO execution) -- proves the new config guard.
        with service._journal.acquire_mutation_lock() as writer:
            writer.append(
                "SCALPING_STATE_CHANGED", {"from_state": "OFF", "to_state": "DEMO_AUTO", "reason": "test"},
                occurred_at_utc=service._now(),
            )
        self.assertEqual(service.current_state, "DEMO_AUTO")
        with self.assertRaises(scalping_service.ScalpingServiceError) as ctx:
            service.configure_profile("XAUUSD", "ALSAKKAF_INTRADAY")
        self.assertEqual(ctx.exception.reason_code, "SCALPING_CONFIG_REQUIRES_NON_AUTO_STATE")

    def test_scalping_stop_cli_resets_emergency_stop_when_owned_state_is_zero(self):
        import unittest.mock as mock
        from trading_lab_app import alsakkaf_scalping_cli as cli

        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        service.request_state_change("EMERGENCY_STOP")
        # TRL-R2-013 Founder shutdown correction: the R2-012 transition
        # table technically allows EMERGENCY_STOP -> OFF directly, but the
        # CLI's scalping-stop command never takes that bare path -- it
        # calls ScalpingService.graceful_stop(), which goes through the
        # governed reset_emergency_stop() (contract Section 14.6) whenever
        # owned broker state is confirmed zero, exactly like an ordinary
        # Founder shutdown from a WAIT-only session should.
        with mock.patch.object(cli, "_build_service", return_value=service):
            exit_code = cli.main(["scalping-stop"])
        self.assertEqual(exit_code, 0)
        self.assertEqual(service.current_state, "OFF")

    def test_scalping_stop_cli_fails_closed_when_owned_orders_remain(self):
        import unittest.mock as mock
        from trading_lab_app import alsakkaf_scalping_cli as cli

        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        service.request_state_change("EMERGENCY_STOP")
        adapter.set_owned_orders([support.owned_order()])
        with mock.patch.object(cli, "_build_service", return_value=service):
            exit_code = cli.main(["scalping-stop"])
        self.assertEqual(exit_code, 1)
        self.assertEqual(service.current_state, "EMERGENCY_STOP")


class LiveStatusDocumentTests(unittest.TestCase):
    def test_unmapped_instrument_reports_explicit_reason(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        runtime = ScalpingRuntime(service)
        document = runtime.live_status_document("EURUSD")
        self.assertEqual(document["mapping_status"], "SYMBOL_NOT_MAPPED")
        self.assertEqual(document["last_analysis"]["reason_code"], "SYMBOL_NOT_MAPPED")
        self.assertIsNone(document["bid"])

    def test_no_bare_dashes_for_operationally_important_fields(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        runtime = ScalpingRuntime(service)
        document = runtime.live_status_document("XAUUSD")
        for field in ("mapping_status", "quote_status", "completed_bar_readiness"):
            self.assertNotEqual(document[field], "—")
            self.assertIsNotNone(document[field])

    def test_live_status_schema_version(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        runtime = ScalpingRuntime(service)
        document = runtime.live_status_document("XAUUSD")
        self.assertEqual(document["schema_version"], "TRL_SCALPING_LIVE_STATUS.v1")


class DemoAutoLockedInDashboardTests(unittest.TestCase):
    def test_index_html_renders_demo_auto_as_locked_and_disabled(self):
        text = (STATIC_DIRECTORY / "index.html").read_text(encoding="utf-8")
        self.assertIn('id="scalping-btn-start"', text)
        self.assertIn("disabled", text.split('id="scalping-btn-start"', 1)[1].split(">", 1)[0])
        self.assertIn("LOCKED PENDING BROKER EXECUTION PROOF", text)

    def test_app_js_never_invokes_start_demo_auto_route(self):
        text = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")
        self.assertNotIn('postScalping("/api/scalping-start-demo-auto"', text)
        self.assertNotIn('bind("scalping-btn-start"', text)


def _function_body(source, name):
    marker = "function {}(".format(name)
    start = source.index(marker)
    depth = 0
    index = source.index("{", start)
    begin = index
    while True:
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[begin:index + 1]
        index += 1


class NoInnerHtmlTests(unittest.TestCase):
    def setUp(self):
        self.source = (STATIC_DIRECTORY / "app.js").read_text(encoding="utf-8")

    def test_no_innerhtml_in_render_scalping(self):
        self.assertNotIn("innerHTML", _function_body(self.source, "renderScalping"))

    def test_no_innerhtml_in_render_scalping_live(self):
        self.assertNotIn("innerHTML", _function_body(self.source, "renderScalpingLive"))

    def test_no_innerhtml_in_wire_scalping_controls(self):
        self.assertNotIn("innerHTML", _function_body(self.source, "wireScalpingControls"))


class ScratchDirectoryWiringTests(unittest.TestCase):
    """Root cause 5: the real running service never passed a
    scratch_directory at all, which would raise TypeError the first time a
    real TRADE_CANDIDATE reached the R2-010 bridge."""

    def test_app_scalping_service_for_mode_supplies_a_real_scratch_directory(self):
        from trading_lab_app.app import _scalping_service_for_mode
        from trading_lab_app.mode_service import in_memory_mode_service

        mode_svc = in_memory_mode_service()
        service = _scalping_service_for_mode(mode_svc.current_mode, mode_svc)
        self.assertIsNotNone(service._scratch_directory)
        self.assertTrue(len(service._scratch_directory) > 0)


class LauncherShutdownCorrectionScriptTests(unittest.TestCase):
    """TRL-R2-013 Founder shutdown correction: the original Stop script
    always called scalping-pause first, which the R2-012 transition table
    never allows from ANALYZE_ONLY (only DEMO_AUTO/PAUSED can reach
    PAUSED) -- so it deterministically fell back to scalping-emergency-stop
    on every ordinary shutdown, latching an unnecessary EMERGENCY_STOP.
    These tests prove the corrected script text no longer does that."""

    def test_stop_script_never_uses_pause_as_a_shutdown_step(self):
        text = STOP_SCRIPT.read_text(encoding="utf-8")
        # Checks the actual CLI invocation, not the header comment (which
        # deliberately documents the prior, corrected-away behavior).
        self.assertNotIn("alsakkaf_scalping_cli scalping-pause", text)
        self.assertNotIn("alsakkaf_scalping_cli scalping-emergency-stop", text)

    def test_stop_script_uses_the_deterministic_state_aware_stop(self):
        text = STOP_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("scalping-stop", text)

    def test_stop_script_verifies_final_state_before_reporting_success(self):
        text = STOP_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("Verifying final state", text)
        self.assertIn('$finalProductState -eq "OFF"', text)
        self.assertIn('$finalOperatingMode -eq "OFF"', text)
        # The success line must be inside the verified branch, not printed
        # unconditionally -- confirmed by it appearing only once, guarded.
        self.assertEqual(text.count("ALSAKKAF SCALPING dashboard stopped."), 1)

    def test_start_script_recovers_stale_emergency_stop_before_analyze_only(self):
        text = START_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("scalping-startup-recover", text)
        recover_index = text.index("scalping-startup-recover")
        resume_index = text.index("scalping-resume")
        self.assertLess(recover_index, resume_index)

    def test_start_script_never_enters_analyze_only_when_recovery_fails(self):
        text = START_SCRIPT.read_text(encoding="utf-8")
        self.assertIn("if ($recoverAccepted)", text)


class GracefulStopStateMachineTests(unittest.TestCase):
    """TRL-R2-013 Founder shutdown correction: ScalpingService.graceful_stop()
    is deterministic, idempotent, and never uses EMERGENCY_STOP as a
    generic fallback."""

    def test_from_off_is_already_off_and_appends_no_event(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        before = len(service.journal_tail(limit=1000))
        result = service.graceful_stop()
        self.assertEqual(result, {"outcome": "ALREADY_OFF", "product_state": "OFF"})
        self.assertEqual(len(service.journal_tail(limit=1000)), before)

    def test_from_analyze_only_transitions_to_off(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        result = service.graceful_stop()
        self.assertEqual(result, {"outcome": "STOPPED", "product_state": "OFF"})
        self.assertEqual(service.current_state, "OFF")

    def test_from_paused_transitions_to_off(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        # PAUSED is reachable only from DEMO_AUTO in the R2-012 table;
        # reached here via a direct journal append (test setup only, never
        # through order_check/order_send) to isolate graceful_stop's own
        # PAUSED -> OFF branch.
        with service._journal.acquire_mutation_lock() as writer:
            writer.append(
                "SCALPING_STATE_CHANGED", {"from_state": "OFF", "to_state": "PAUSED", "reason": "test"},
                occurred_at_utc=service._now(),
            )
        self.assertEqual(service.current_state, "PAUSED")
        result = service.graceful_stop()
        self.assertEqual(result, {"outcome": "STOPPED", "product_state": "OFF"})

    def test_from_emergency_stop_with_zero_owned_state_resets_to_off(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        service.request_state_change("EMERGENCY_STOP")
        result = service.graceful_stop()
        self.assertEqual(result, {"outcome": "STOPPED", "product_state": "OFF"})
        self.assertFalse(service.is_emergency_stopped)

    def test_from_emergency_stop_with_owned_orders_fails_closed(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        service.request_state_change("EMERGENCY_STOP")
        adapter.set_owned_orders([support.owned_order()])
        with self.assertRaises(scalping_service.ScalpingServiceError) as ctx:
            service.graceful_stop()
        self.assertEqual(ctx.exception.reason_code, "SCALPING_GRACEFUL_STOP_OWNED_STATE_REMAINS")
        self.assertEqual(service.current_state, "EMERGENCY_STOP")

    def test_from_emergency_stop_with_owned_positions_fails_closed(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        service.request_state_change("EMERGENCY_STOP")
        adapter.set_owned_positions([support.owned_position()])
        with self.assertRaises(scalping_service.ScalpingServiceError):
            service.graceful_stop()
        self.assertEqual(service.current_state, "EMERGENCY_STOP")

    def test_from_demo_auto_with_zero_owned_state_activates_then_resets(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        # DEMO_AUTO is reached via a direct journal append (test setup
        # only) so this proves graceful_stop's own DEMO_AUTO branch without
        # exercising order_check/order_send anywhere in this test module.
        with service._journal.acquire_mutation_lock() as writer:
            writer.append(
                "SCALPING_STATE_CHANGED", {"from_state": "ANALYZE_ONLY", "to_state": "DEMO_AUTO", "reason": "test"},
                occurred_at_utc=service._now(),
            )
        result = service.graceful_stop()
        self.assertEqual(result, {"outcome": "STOPPED", "product_state": "OFF"})
        self.assertEqual([c for c in adapter.calls if c[0] in ("order_check", "order_send")], [])

    def test_from_demo_auto_with_owned_position_fails_closed(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        with service._journal.acquire_mutation_lock() as writer:
            writer.append(
                "SCALPING_STATE_CHANGED", {"from_state": "ANALYZE_ONLY", "to_state": "DEMO_AUTO", "reason": "test"},
                occurred_at_utc=service._now(),
            )
        adapter.set_owned_positions([support.owned_position()])
        with self.assertRaises(scalping_service.ScalpingServiceError):
            service.graceful_stop()
        # Emergency stop was still activated (owned state flattening
        # attempted); only the final reset-to-OFF step is withheld.
        self.assertEqual(service.current_state, "EMERGENCY_STOP")

    def test_graceful_stop_is_idempotent(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        first = service.graceful_stop()
        second = service.graceful_stop()
        self.assertEqual(first["product_state"], "OFF")
        self.assertEqual(second, {"outcome": "ALREADY_OFF", "product_state": "OFF"})


class RecoverStaleEmergencyStopTests(unittest.TestCase):
    """TRL-R2-013 Section 4: startup-only recovery, used by
    Start_ALSAKKAF_SCALPING_DEMO.ps1 before requesting ANALYZE_ONLY."""

    def test_no_action_when_not_emergency_stopped(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        result = service.recover_stale_emergency_stop()
        self.assertEqual(result, {"outcome": "NO_ACTION_NEEDED", "product_state": "OFF"})

    def test_recovers_when_owned_state_is_zero(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        service.request_state_change("EMERGENCY_STOP")
        result = service.recover_stale_emergency_stop()
        self.assertEqual(result, {"outcome": "RECOVERED", "product_state": "OFF"})
        self.assertEqual(service.current_state, "OFF")

    def test_fails_closed_when_owned_orders_remain(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        service.request_state_change("EMERGENCY_STOP")
        adapter.set_owned_orders([support.owned_order()])
        with self.assertRaises(scalping_service.ScalpingServiceError) as ctx:
            service.recover_stale_emergency_stop()
        self.assertEqual(ctx.exception.reason_code, "SCALPING_STARTUP_RECOVERY_OWNED_STATE_REMAINS")
        self.assertEqual(service.current_state, "EMERGENCY_STOP")

    def test_never_acts_on_demo_auto(self):
        """Startup recovery is narrowly scoped to a stale EMERGENCY_STOP
        latch only -- it must never force-stop a state that could
        represent genuinely active automation from a still-running prior
        process (that is the shutdown script's job, not startup's)."""
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        with service._journal.acquire_mutation_lock() as writer:
            writer.append(
                "SCALPING_STATE_CHANGED", {"from_state": "ANALYZE_ONLY", "to_state": "DEMO_AUTO", "reason": "test"},
                occurred_at_utc=service._now(),
            )
        result = service.recover_stale_emergency_stop()
        self.assertEqual(result, {"outcome": "NO_ACTION_NEEDED", "product_state": "DEMO_AUTO"})
        self.assertEqual(service.current_state, "DEMO_AUTO")


class PauseTransitionDocumentationTests(unittest.TestCase):
    """Documents the exact R2-012 transition-table fact that caused the
    Founder-observed shutdown defect: PAUSED is reachable only from
    DEMO_AUTO/PAUSED, never from ANALYZE_ONLY -- so a shutdown script must
    never rely on scalping-pause as a generic first step."""

    def test_pause_from_analyze_only_is_rejected(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        with self.assertRaises(scalping_service.ScalpingServiceError) as ctx:
            service.request_state_change("PAUSED")
        self.assertEqual(ctx.exception.reason_code, "SCALPING_INVALID_TRANSITION")
        self.assertEqual(service.current_state, "ANALYZE_ONLY")


if __name__ == "__main__":
    unittest.main()
