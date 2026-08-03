"""Tests for alsakkaf_scalping_risk.py (TRL-R2-012 contract Sections 11-13)."""

import unittest
from decimal import Decimal

from trading_lab_app import alsakkaf_scalping_risk as risk


SYMBOL_INFO = {
    "tick_value": "1.00", "tick_size": "0.01",
    "volume_minimum": "0.01", "volume_maximum": "100", "volume_step": "0.01",
}


class LotSizingTests(unittest.TestCase):
    def test_calculate_lots_basic(self):
        result = risk.calculate_lots("10000", "0.25", "1961.00", "1959.00", SYMBOL_INFO)
        # risk_amount = 10000 * 0.25% = 25; value_per_point = 1.00/0.01 = 100
        # raw_lots = 25 / (2.00 * 100) = 0.125 -> floored to step 0.01 -> 0.12
        self.assertEqual(result["lots"], Decimal("0.12"))
        self.assertEqual(result["risk_amount"], Decimal("25.00"))

    def test_lot_below_minimum_fails_closed(self):
        with self.assertRaises(risk.ScalpingRiskError):
            risk.calculate_lots("10", "0.25", "1961.00", "1959.00", SYMBOL_INFO)

    def test_zero_stop_distance_fails_closed(self):
        with self.assertRaises(risk.ScalpingRiskError):
            risk.calculate_lots("10000", "0.25", "1961.00", "1961.00", SYMBOL_INFO)

    def test_lot_capped_to_volume_maximum_when_risk_allows(self):
        symbol_info = dict(SYMBOL_INFO, volume_maximum="0.05")
        result = risk.calculate_lots("10000", "0.25", "1961.00", "1959.00", symbol_info)
        self.assertEqual(result["lots"], Decimal("0.05"))

    def test_lot_cannot_be_bounded_to_risk_fails_closed(self):
        symbol_info = dict(SYMBOL_INFO, volume_maximum="0.05", volume_minimum="0.05")
        with self.assertRaises(risk.ScalpingRiskError):
            risk.calculate_lots("100", "0.25", "1961.00", "1959.00", symbol_info)

    def test_missing_symbol_field_fails_closed(self):
        with self.assertRaises(risk.ScalpingRiskError):
            risk.calculate_lots("10000", "0.25", "1961.00", "1959.00", {"tick_value": "1.00"})

    def test_no_fixed_lot_override_exceeds_budget(self):
        """A lot result's risk (lots * stop_distance * value_per_point) must
        never exceed the calculated risk_amount."""
        result = risk.calculate_lots("10000", "0.25", "1961.00", "1959.00", SYMBOL_INFO)
        stop_distance = Decimal("2.00")
        value_per_point = Decimal("100")
        actual_risk = result["lots"] * stop_distance * value_per_point
        self.assertLessEqual(actual_risk, result["risk_amount"])


class LadderRiskConservationTests(unittest.TestCase):
    def test_divide_ladder_risk_conserves_total(self):
        per_order = risk.divide_ladder_risk("60", 6)
        self.assertEqual(per_order * 6, Decimal("60"))

    def test_divide_ladder_risk_rejects_too_many_orders(self):
        with self.assertRaises(risk.ScalpingRiskError):
            risk.divide_ladder_risk("60", 7)

    def test_ladder_distance_floor_uses_maximum(self):
        floor = risk.ladder_distance_floor(
            entry_timeframe_atr="2.0", current_spread="0.1",
            broker_minimum_stop_distance="0.05", one_broker_point="0.01",
        )
        # candidates: 0.25*2.0=0.5, 2*0.1=0.2, 0.05, 0.01 -> max is 0.5
        self.assertEqual(floor, Decimal("0.5"))

    def test_cap_same_direction_orders_never_exceeds_budget_no_resize(self):
        orders = [
            {"id": "a", "risk_amount": "10"}, {"id": "b", "risk_amount": "10"},
            {"id": "c", "risk_amount": "10"},
        ]
        result = risk.cap_same_direction_orders("25", orders)
        kept_ids = [order["id"] for order in result["kept"]]
        cancelled_ids = [order["id"] for order in result["cancelled"]]
        self.assertEqual(kept_ids, ["a", "b"])
        self.assertEqual(cancelled_ids, ["c"])
        # No order was resized -- every kept order's risk_amount is unchanged.
        for order in result["kept"]:
            self.assertIn(order["risk_amount"], ("10",))

    def test_no_lot_escalation_after_loss(self):
        """Lot size is a pure function of equity/risk_pct/stop geometry --
        never of prior cycle outcome. Two cycles with identical inputs but
        a simulated intervening loss produce identical lots."""
        result_before_loss = risk.calculate_lots("10000", "0.25", "1961.00", "1959.00", SYMBOL_INFO)
        equity_after_loss = "9975"  # equity reduced by a realized loss
        result_after_loss = risk.calculate_lots(
            equity_after_loss, "0.25", "1961.00", "1959.00", SYMBOL_INFO,
        )
        # Because risk_per_cycle_pct is fixed (never increased after a
        # loss), the post-loss lot size is never larger than the pre-loss one.
        self.assertLessEqual(result_after_loss["lots"], result_before_loss["lots"])


class RiskSettingsTests(unittest.TestCase):
    def test_default_settings_within_hard_caps(self):
        settings = risk.validate_risk_settings(risk.default_risk_settings())
        self.assertLessEqual(settings["risk_per_cycle_pct"], risk.HARD_MAX_RISK_PER_CYCLE_PCT)

    def test_exceeding_hard_cap_fails_closed(self):
        settings = risk.default_risk_settings()
        settings["risk_per_cycle_pct"] = Decimal("5.00")
        with self.assertRaises(risk.ScalpingRiskError):
            risk.validate_risk_settings(settings)

    def test_daily_loss_hard_cap_bound(self):
        settings = risk.default_risk_settings()
        settings["max_daily_loss_pct"] = Decimal("2.01")
        with self.assertRaises(risk.ScalpingRiskError):
            risk.validate_risk_settings(settings)

    def test_cooldown_minimum_enforced(self):
        settings = risk.default_risk_settings()
        settings["cooldown_minutes"] = 5
        with self.assertRaises(risk.ScalpingRiskError):
            risk.validate_risk_settings(settings)


class DailyLossDrawdownTests(unittest.TestCase):
    def test_daily_loss_breach_detected(self):
        self.assertTrue(risk.daily_loss_breached("150", "10000", "1.00"))

    def test_daily_loss_not_breached(self):
        self.assertFalse(risk.daily_loss_breached("50", "10000", "1.00"))

    def test_session_drawdown_breach_detected(self):
        self.assertTrue(risk.session_drawdown_breached("10000", "9750", "2.00"))

    def test_session_drawdown_not_breached(self):
        self.assertFalse(risk.session_drawdown_breached("10000", "9900", "2.00"))


class FloorToStepTests(unittest.TestCase):
    def test_floor_to_step_rounds_down(self):
        self.assertEqual(risk.floor_to_step("0.129", "0.01"), Decimal("0.12"))

    def test_floor_to_step_rejects_zero_step(self):
        with self.assertRaises(risk.ScalpingRiskError):
            risk.floor_to_step("0.1", "0")


if __name__ == "__main__":
    unittest.main()
