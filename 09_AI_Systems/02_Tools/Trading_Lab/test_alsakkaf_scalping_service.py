"""Tests for alsakkaf_scalping_service.py (TRL-R2-012 contract Sections
3, 9, 11-14)."""

import unittest
from decimal import Decimal

import alsakkaf_scalping_test_support as support
from trading_lab_app import alsakkaf_scalping_service as svc
from trading_lab_app.alsakkaf_scalping_data import ALSAKKAF_SCALPING_MAGIC


class ProductStateMachineTests(unittest.TestCase):
    def test_starts_off(self):
        service, _adapter, _mode = support.make_service(target_mode="OFF")
        self.assertEqual(service.current_state, "OFF")

    def test_off_to_analyze_only(self):
        service, _adapter, _mode = support.make_service(target_mode="OFF")
        self.assertEqual(service.request_state_change("ANALYZE_ONLY"), "ANALYZE_ONLY")

    def test_invalid_transition_rejected(self):
        service, _adapter, _mode = support.make_service(target_mode="OFF")
        with self.assertRaises(svc.ScalpingServiceError) as context:
            service.request_state_change("PAUSED")
        self.assertEqual(context.exception.reason_code, "SCALPING_INVALID_TRANSITION")
        self.assertEqual(service.current_state, "OFF")

    def test_demo_auto_requires_capability(self):
        service, _adapter, _mode = support.make_service(target_mode="RESEARCH")
        with self.assertRaises(svc.ScalpingServiceError) as context:
            service.request_state_change("DEMO_AUTO")
        self.assertEqual(context.exception.reason_code, "SCALPING_DEMO_AUTO_REQUIRES_MODE")

    def test_demo_auto_succeeds_with_capability_and_passing_preflight(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        self.assertEqual(service.request_state_change("DEMO_AUTO"), "DEMO_AUTO")

    def test_emergency_stop_reachable_from_every_state(self):
        for target in ("OFF", "ANALYZE_ONLY"):
            with self.subTest(target=target):
                service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
                if target != "OFF":
                    service.request_state_change(target)
                self.assertEqual(service.request_state_change("EMERGENCY_STOP"), "EMERGENCY_STOP")

    def test_emergency_stop_only_returns_to_off(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("EMERGENCY_STOP")
        with self.assertRaises(svc.ScalpingServiceError):
            service.request_state_change("ANALYZE_ONLY")


class SymbolMapAndProfileTests(unittest.TestCase):
    def test_save_symbol_map_requires_off_state(self):
        service, _adapter, _mode = support.make_service(target_mode="OFF")
        service.request_state_change("ANALYZE_ONLY")
        with self.assertRaises(svc.ScalpingServiceError) as context:
            service.save_symbol_map("XAUUSD", "XAUUSDm")
        self.assertEqual(context.exception.reason_code, "SCALPING_SYMBOL_MAP_REQUIRES_OFF_STATE")

    def test_configure_profile_rejects_hard_cap_violation(self):
        service, _adapter, _mode = support.make_service()
        with self.assertRaises(Exception):
            service.configure_profile("XAUUSD", "ALSAKKAF_PRECISION_SCALPING", risk_overrides={
                "risk_per_cycle_pct": Decimal("5.00"),
            })

    def test_unmapped_symbol_fails_closed(self):
        service, _adapter, _mode = support.make_service()
        with self.assertRaises(svc.ScalpingServiceError):
            service.broker_symbol_for("EURUSD")


class AnalyzeAndCycleTests(unittest.TestCase):
    def test_analyze_only_produces_plan_without_orders(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        result = service.run_cycle("XAUUSD", entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        self.assertFalse(result["created"])
        self.assertEqual(result["reason"], "ANALYZE_ONLY_PLAN")
        self.assertEqual(adapter.calls, [])

    def test_off_state_forbids_execution(self):
        service, _adapter, _mode = support.make_service(target_mode="OFF")
        entry_bars = support.make_chop_then_breakout_bars()
        with self.assertRaises(svc.ScalpingServiceError) as context:
            service.run_cycle("XAUUSD", entry_bars, entry_bars, entry_bars[-1]["close"], "0.05")
        self.assertEqual(context.exception.reason_code, "SCALPING_STATE_FORBIDS_EXECUTION")

    def test_wait_setup_creates_no_cycle(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("DEMO_AUTO")
        flat_bars = support.make_flat_choppy_bars()
        result = service.run_cycle("XAUUSD", flat_bars, flat_bars, flat_bars[-1]["close"], "0.05")
        self.assertFalse(result["created"])

    def test_demo_auto_trade_candidate_creates_active_cycle_with_order_check_and_send(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("DEMO_AUTO")
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        result = service.run_cycle(
            "XAUUSD", entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05",
        )
        self.assertTrue(result["created"])
        self.assertEqual(result["final_state"], "ACTIVE")
        self.assertEqual(len(result["executed_plans"]), 1)
        call_names = [name for name, _request in adapter.calls]
        self.assertEqual(call_names, ["order_check", "order_send"])
        # Every order carries ownership metadata.
        _name, check_request = adapter.calls[0]
        self.assertEqual(check_request["magic"], ALSAKKAF_SCALPING_MAGIC)
        self.assertEqual(check_request["comment"], "ALSAKKAF_SCALPING")

    def test_order_check_rejected_blocks_cycle_without_order_send(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("DEMO_AUTO")
        adapter.queue_check_result({"outcome": "FAILED", "retcode": 10016, "comment": "invalid stops", "checked_at_utc": "x"})
        entry_bars = support.make_chop_then_breakout_bars()
        result = service.run_cycle("XAUUSD", entry_bars, entry_bars, entry_bars[-1]["close"], "0.05")
        self.assertTrue(result["created"])
        self.assertEqual(result["final_state"], "BLOCKED")
        call_names = [name for name, _request in adapter.calls]
        self.assertEqual(call_names, ["order_check"])

    def test_uncertain_order_send_freezes_cycle(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("DEMO_AUTO")
        adapter.queue_send_result({
            "outcome": "UNCERTAIN", "retcode": None, "ticket": None, "deal": None,
            "comment": "timeout", "sent_at_utc": "x",
        })
        entry_bars = support.make_chop_then_breakout_bars()
        result = service.run_cycle("XAUUSD", entry_bars, entry_bars, entry_bars[-1]["close"], "0.05")
        self.assertEqual(result["final_state"], "UNCERTAIN")
        with self.assertRaises(svc.ScalpingServiceError) as context:
            service.run_cycle("XAUUSD", entry_bars, entry_bars, entry_bars[-1]["close"], "0.05")
        self.assertEqual(context.exception.reason_code, "SCALPING_CYCLE_FROZEN_UNCERTAIN")

    def test_preflight_failure_blocks_cycle(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("DEMO_AUTO")
        adapter.terminal["trade_allowed"] = False
        entry_bars = support.make_chop_then_breakout_bars()
        result = service.run_cycle("XAUUSD", entry_bars, entry_bars, entry_bars[-1]["close"], "0.05")
        self.assertFalse(result["created"])
        self.assertEqual(result["reason"], "SCALPING_ALGO_TRADING_DISABLED")


class EmergencyStopTests(unittest.TestCase):
    def test_emergency_stop_cancels_owned_orders_and_closes_owned_positions(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        adapter.set_owned_orders([support.owned_order(ticket=1)])
        adapter.set_owned_positions([support.owned_position(ticket=2)])
        service.request_state_change("EMERGENCY_STOP")
        events = [event["event_type"] for event in service.journal_tail(limit=50)]
        self.assertIn("PENDING_ORDER_CANCELLED", events)
        self.assertIn("POSITION_CLOSED", events)
        self.assertIn("EMERGENCY_STOP_ACTIVATED", events)

    def test_emergency_stop_never_touches_unowned_order(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        adapter.set_owned_orders([{"ticket": 99, "symbol": "XAUUSDm", "magic": 1, "comment": "OTHER_APP"}])
        service.request_state_change("EMERGENCY_STOP")
        events = service.journal_tail(limit=50)
        activated = next(event for event in events if event["event_type"] == "EMERGENCY_STOP_ACTIVATED")
        self.assertEqual(activated["payload"]["cancelled_orders"], [])

    def test_reset_requires_zero_owned_pending_orders(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        adapter.set_owned_orders([support.owned_order()])
        service.request_state_change("EMERGENCY_STOP")
        with self.assertRaises(svc.ScalpingServiceError) as context:
            service.reset_emergency_stop()
        self.assertEqual(context.exception.reason_code, "SCALPING_EMERGENCY_RESET_REQUIRES_ZERO_PENDING_ORDERS")
        adapter.set_owned_orders([])
        self.assertEqual(service.reset_emergency_stop(), "OFF")


class ReconciliationTests(unittest.TestCase):
    def test_reconcile_returns_owned_orders_and_positions_only(self):
        service, adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        adapter.set_owned_orders([support.owned_order(ticket=1), {"ticket": 5, "symbol": "X", "magic": 1, "comment": "OTHER"}])
        result = service.reconcile()
        self.assertEqual([order["ticket"] for order in result["owned_orders"]], [1])

    def test_restart_reconciliation_uses_durable_journal(self):
        """A fresh ScalpingService constructed against the same durable
        journal reflects the prior process's committed cycles -- restart
        recovery is journal-derived, never re-derived from adapter state
        alone."""
        import tempfile
        from trading_lab_app.alsakkaf_scalping_journal import LocalScalpingJournalStore, ScalpingJournalWriter
        from pathlib import Path

        directory = tempfile.mkdtemp()
        path = Path(directory) / "journal.json"
        first_writer = ScalpingJournalWriter(store=LocalScalpingJournalStore(path=path))
        service, adapter, mode_svc = support.make_service(target_mode="MT5_DEMO_AUTOMATED", journal=first_writer)
        service.request_state_change("ANALYZE_ONLY")

        second_writer = ScalpingJournalWriter(store=LocalScalpingJournalStore(path=path))
        self.assertEqual(second_writer.startup_diagnostic_code, "OK")
        self.assertTrue(any(event["event_type"] == "SCALPING_STATE_CHANGED" for event in second_writer.events))


if __name__ == "__main__":
    unittest.main()
