"""Tests for alsakkaf_scalping_data.py (TRL-R2-012 contract Section 15.1)."""

import unittest
from decimal import Decimal

from trading_lab_app import alsakkaf_scalping_data as data


def _plan_kwargs(**overrides):
    kwargs = dict(
        canonical_instrument="XAUUSD", broker_symbol="XAUUSDm", side="BUY",
        order_type="MARKET", profile_id="ALSAKKAF_PRECISION_SCALPING",
        entry_price="1961.00", stop_price="1959.00",
        ordered_target_prices=["1962.00", "1963.00", "1964.00"],
        ordered_target_allocations_pct=["50", "30", "20"],
        lots="0.10", risk_amount="25.00", created_at_utc="2026-08-03T00:00:00.000000Z",
    )
    kwargs.update(overrides)
    return kwargs


class OrderPlanTests(unittest.TestCase):
    def test_build_order_plan_deterministic_identity(self):
        plan_a = data.build_order_plan(**_plan_kwargs())
        plan_b = data.build_order_plan(**_plan_kwargs())
        self.assertEqual(plan_a["order_plan_id"], plan_b["order_plan_id"])
        self.assertTrue(plan_a["order_plan_id"].startswith("plan_"))

    def test_different_side_produces_different_identity(self):
        plan_buy = data.build_order_plan(**_plan_kwargs())
        plan_sell = data.build_order_plan(**_plan_kwargs(
            side="SELL", stop_price="1963.00",
            ordered_target_prices=["1960.00", "1959.00", "1958.00"],
        ))
        self.assertNotEqual(plan_buy["order_plan_id"], plan_sell["order_plan_id"])

    def test_order_plan_owns_magic_and_comment(self):
        plan = data.build_order_plan(**_plan_kwargs())
        self.assertEqual(plan["magic_number"], data.ALSAKKAF_SCALPING_MAGIC)
        self.assertEqual(plan["comment"], data.broker_comment())

    def test_target_allocations_must_sum_to_100(self):
        with self.assertRaises(data.ScalpingDataValidationError):
            data.build_order_plan(**_plan_kwargs(ordered_target_allocations_pct=["50", "30", "10"]))

    def test_stop_equal_entry_rejected(self):
        with self.assertRaises(data.ScalpingDataValidationError):
            data.build_order_plan(**_plan_kwargs(stop_price="1961.00"))

    def test_target_count_bounds(self):
        with self.assertRaises(data.ScalpingDataValidationError):
            data.build_order_plan(**_plan_kwargs(
                ordered_target_prices=[], ordered_target_allocations_pct=[],
            ))

    def test_validate_order_plan_rejects_forged_magic(self):
        plan = data.build_order_plan(**_plan_kwargs())
        forged = dict(plan)
        forged["magic_number"] = 999999
        with self.assertRaises(data.ScalpingDataValidationError):
            data.validate_order_plan(forged)

    def test_validate_order_plan_rejects_tampered_identity(self):
        plan = data.build_order_plan(**_plan_kwargs())
        forged = dict(plan)
        forged["entry_price"] = "1970.00"
        with self.assertRaises(data.ScalpingDataValidationError):
            data.validate_order_plan(forged)


class CycleTests(unittest.TestCase):
    def _cycle_kwargs(self, **overrides):
        plan = data.build_order_plan(**_plan_kwargs())
        kwargs = dict(
            canonical_instrument="XAUUSD", broker_symbol="XAUUSDm",
            profile_id="ALSAKKAF_PRECISION_SCALPING", reference_price="1961.00",
            reference_atr="1.5", reference_spread="0.05",
            order_plan_ids=[plan["order_plan_id"]],
            expiry_utc="2026-08-03T01:00:00.000000Z", total_risk_amount="25.00",
            unallocated_risk_remainder="0", created_at_utc="2026-08-03T00:00:00.000000Z",
        )
        kwargs.update(overrides)
        return kwargs

    def test_build_cycle_starts_planned(self):
        cycle = data.build_cycle(**self._cycle_kwargs())
        self.assertEqual(cycle["state"], "PLANNED")
        self.assertTrue(cycle["cycle_id"].startswith("cyc_"))

    def test_cycle_rejects_more_than_six_order_plans(self):
        with self.assertRaises(data.ScalpingDataValidationError):
            data.build_cycle(**self._cycle_kwargs(order_plan_ids=["plan_x"] * 7))

    def test_cycle_deterministic_identity(self):
        cycle_a = data.build_cycle(**self._cycle_kwargs())
        cycle_b = data.build_cycle(**self._cycle_kwargs())
        self.assertEqual(cycle_a["cycle_id"], cycle_b["cycle_id"])


class SymbolMapTests(unittest.TestCase):
    def test_empty_document_valid(self):
        document = data.validate_symbol_map_document(data.empty_symbol_map_document())
        self.assertEqual(document["mappings"], {})

    def test_rejects_non_canonical_instrument(self):
        document = data.empty_symbol_map_document()
        document["mappings"]["NOTREAL"] = "X"
        with self.assertRaises(data.ScalpingDataValidationError):
            data.validate_symbol_map_document(document)

    def test_in_memory_store_round_trip(self):
        store = data.InMemorySymbolMapStore()
        document = store.load()
        document["mappings"]["XAUUSD"] = "XAUUSDm"
        store.save(document)
        self.assertEqual(store.load()["mappings"]["XAUUSD"], "XAUUSDm")

    def test_local_store_atomic_round_trip(self):
        import tempfile
        from pathlib import Path

        directory = tempfile.mkdtemp()
        store = data.SymbolMapStore(path=Path(directory) / "map.json")
        document = store.load()
        self.assertEqual(document["mappings"], {})
        document["mappings"]["XAUUSD"] = "XAUUSDm"
        document["event_risk_blocked"]["XAUUSD"] = True
        store.save(document)
        reloaded = store.load()
        self.assertEqual(reloaded["mappings"]["XAUUSD"], "XAUUSDm")
        self.assertTrue(reloaded["event_risk_blocked"]["XAUUSD"])


class QuantizeTests(unittest.TestCase):
    def test_quantize_4_rounds_half_even(self):
        self.assertEqual(data.quantize_4("1.00005"), Decimal("1.0000"))
        self.assertEqual(data.quantize_4("1.00015"), Decimal("1.0002"))


if __name__ == "__main__":
    unittest.main()
