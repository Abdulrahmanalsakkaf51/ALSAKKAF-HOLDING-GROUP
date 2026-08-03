"""Cross-cutting safety tests for ALSAKKAF SCALPING (TRL-R2-012).

Covers: no martingale, no uncontrolled grid, no live-account authority
(independent of ModeService), unrelated-order protection, no credential
exposure, and the exact capability-matrix amendment (contract Section 16).
"""

import inspect
import unittest
from decimal import Decimal

import alsakkaf_scalping_test_support as support
from trading_lab_app import alsakkaf_scalping_data as data
from trading_lab_app import alsakkaf_scalping_mt5 as mt5a
from trading_lab_app import alsakkaf_scalping_risk as risk
from trading_lab_app import alsakkaf_scalping_service as svc
from trading_lab_app import mode_service as ms


class NoMartingaleTests(unittest.TestCase):
    def test_lot_size_never_a_function_of_prior_outcome(self):
        """calculate_lots's signature has no "prior loss"/"streak"
        parameter at all -- martingale is structurally impossible, not
        merely discouraged."""
        signature = inspect.signature(risk.calculate_lots)
        for forbidden in ("loss", "streak", "consecutive", "martingale", "multiplier"):
            self.assertNotIn(forbidden, signature.parameters)

    def test_cooldown_never_increases_risk_percentage(self):
        settings = risk.default_risk_settings()
        self.assertLessEqual(settings["risk_per_cycle_pct"], risk.HARD_MAX_RISK_PER_CYCLE_PCT)
        self.assertEqual(settings["max_consecutive_losses"], risk.DEFAULT_MAX_CONSECUTIVE_LOSSES)


class NoUncontrolledGridTests(unittest.TestCase):
    def test_ladder_bounded_to_six_orders_total(self):
        self.assertEqual(risk.MAX_LADDER_ORDERS, 6)

    def test_ladder_bounded_to_three_per_side(self):
        self.assertEqual(risk.MAX_LADDER_ORDERS_PER_SIDE, 3)

    def test_divide_ladder_risk_rejects_more_than_six(self):
        with self.assertRaises(risk.ScalpingRiskError):
            risk.divide_ladder_risk("60", risk.MAX_LADDER_ORDERS + 1)

    def test_breakout_ladder_cycle_never_exceeds_six_order_plans(self):
        from trading_lab_app import alsakkaf_scalping_strategy as strategy

        service, adapter, _mode = support.make_service(
            target_mode="MT5_DEMO_AUTOMATED", profile_id="ALSAKKAF_BREAKOUT_LADDER",
        )
        entry_bars = support.make_chop_then_breakout_bars()
        confirmation_bars = support.make_chop_then_breakout_bars()
        evaluation = strategy.evaluate_setup(entry_bars, confirmation_bars, entry_bars[-1]["close"], "0.05")
        self.assertEqual(evaluation["classification"], "TRADE_CANDIDATE")
        plans = service._build_cycle_plans("XAUUSD", evaluation)
        self.assertLessEqual(len(plans), risk.MAX_LADDER_ORDERS)
        # Directional single-side ladder in this fixture (evaluation
        # direction is BUY) never exceeds three orders on that side.
        self.assertLessEqual(len(plans), risk.MAX_LADDER_ORDERS_PER_SIDE)


class RealAccountHardLockTests(unittest.TestCase):
    def test_demo_auto_capability_alone_never_authorizes_a_real_account_order(self):
        """Even with ModeService granting alsakkaf_scalping_demo_automation,
        a REAL account is independently rejected at the adapter-preflight
        layer -- the capability grant is necessary but never sufficient."""
        mode_svc = support.make_mode_service("MT5_DEMO_AUTOMATED")
        self.assertTrue(mode_svc.has_capability(svc.CAPABILITY))
        adapter = support.make_fake_adapter()
        adapter.account["trade_mode"] = 2
        adapter.account["trade_mode_name"] = "REAL"
        result = mt5a.run_preflight(adapter, "XAUUSDm", 200, False, False, True, True, 1)
        self.assertFalse(result["passed"])
        self.assertEqual(result["blocking_reason_code"], "SCALPING_ACCOUNT_NOT_PROVEN_DEMO")

    def test_mt5_live_automated_still_fully_unavailable(self):
        self.assertFalse(ms.is_available("MT5_LIVE_AUTOMATED"))
        self.assertFalse(ms.is_available("MT5_LIVE_MANUAL"))

    def test_scalping_capability_granted_only_to_demo_automated(self):
        for mode in ms.MODES:
            with self.subTest(mode=mode):
                granted = svc.CAPABILITY in ms.capabilities_for(mode)
                self.assertEqual(granted, mode == "MT5_DEMO_AUTOMATED")

    def test_real_adapter_never_imports_metatrader5_at_construction(self):
        import sys
        mt5a.RealScalpingMT5Adapter()
        self.assertNotIn("MetaTrader5", sys.modules)


class UnrelatedOrderProtectionTests(unittest.TestCase):
    def test_owned_orders_filter_excludes_foreign_magic(self):
        adapter = mt5a.fake_adapter()
        adapter.set_owned_orders([
            support.owned_order(ticket=1),
            {"ticket": 2, "symbol": "XAUUSDm", "magic": 111111, "comment": "SOME_OTHER_EA"},
        ])
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED", adapter=adapter)
        owned = service.list_owned_orders()
        self.assertEqual([order["ticket"] for order in owned], [1])

    def test_emergency_stop_reports_only_owned_tickets(self):
        adapter = mt5a.fake_adapter()
        adapter.set_owned_orders([support.owned_order(ticket=7)])
        adapter.set_owned_positions([{"ticket": 8, "symbol": "XAUUSDm", "magic": 5, "comment": "UNRELATED"}])
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED", adapter=adapter)
        service.request_state_change("EMERGENCY_STOP")
        events = service.journal_tail(limit=50)
        activated = next(event for event in events if event["event_type"] == "EMERGENCY_STOP_ACTIVATED")
        self.assertEqual(activated["payload"]["cancelled_orders"], [7])
        self.assertEqual(activated["payload"]["closed_positions"], [])


class NoCredentialExposureTests(unittest.TestCase):
    def test_account_status_never_exposes_full_login(self):
        adapter = mt5a.fake_adapter()
        status = adapter.account_status()
        self.assertNotIn("login", status)
        self.assertIn("login_last4", status)

    def test_journal_payload_never_contains_credential_shaped_keys(self):
        service, _adapter, _mode = support.make_service(target_mode="MT5_DEMO_AUTOMATED")
        service.request_state_change("ANALYZE_ONLY")
        for event in service.journal_tail(limit=50):
            payload_text = str(event["payload"]).lower()
            for forbidden in ("password", "investor_password", "access_token", "broker_server"):
                self.assertNotIn(forbidden, payload_text)

    def test_order_plan_never_contains_account_fields(self):
        plan = data.build_order_plan(
            canonical_instrument="XAUUSD", broker_symbol="XAUUSDm", side="BUY",
            order_type="MARKET", profile_id="ALSAKKAF_PRECISION_SCALPING",
            entry_price="1961.00", stop_price="1959.00",
            ordered_target_prices=["1962.00", "1963.00", "1964.00"],
            ordered_target_allocations_pct=["50", "30", "20"],
            lots="0.10", risk_amount="25.00", created_at_utc="2026-08-03T00:00:00.000000Z",
        )
        for forbidden in ("login", "password", "server", "account"):
            self.assertNotIn(forbidden, plan)


class HardCapEnforcementTests(unittest.TestCase):
    def test_dashboard_cannot_exceed_hard_risk_per_cycle_cap(self):
        service, _adapter, _mode = support.make_service()
        with self.assertRaises(Exception):
            service.configure_profile("XAUUSD", "ALSAKKAF_PRECISION_SCALPING", risk_overrides={
                "risk_per_cycle_pct": risk.HARD_MAX_RISK_PER_CYCLE_PCT + Decimal("0.01"),
            })

    def test_dashboard_can_reduce_risk_below_default(self):
        service, _adapter, _mode = support.make_service()
        result = service.configure_profile("XAUUSD", "ALSAKKAF_PRECISION_SCALPING", risk_overrides={
            "risk_per_cycle_pct": Decimal("0.10"),
        })
        self.assertEqual(result["risk_settings"]["risk_per_cycle_pct"], "0.10")


if __name__ == "__main__":
    unittest.main()
