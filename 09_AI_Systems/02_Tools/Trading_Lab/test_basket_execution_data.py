"""Tests for basket_execution_data.py — the TRL-R2-009 Phase 6 schemas,
deterministic identities, and quantity/allocation conservation.

Pure data-layer tests: no adapter, no journal, no ModeService, no I/O.
"""

import copy
import hashlib
import unittest

from trading_lab_app import basket_execution_data as bed
from trading_lab_app import mt5_execution_data as med


def _hash64(seed):
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def make_plan_children():
    return [
        {"child_index": 0, "basket_child_id": "bc_" + "a" * 16, "target_price": "1902.00", "target_allocation_percent": "25", "child_quantity": "0.0025"},
        {"child_index": 1, "basket_child_id": "bc_" + "b" * 16, "target_price": "1905.00", "target_allocation_percent": "25", "child_quantity": "0.0025"},
        {"child_index": 2, "basket_child_id": "bc_" + "c" * 16, "target_price": "1908.00", "target_allocation_percent": "25", "child_quantity": "0.0025"},
        {"child_index": 3, "basket_child_id": "bc_" + "d" * 16, "target_price": "1911.00", "target_allocation_percent": "25", "child_quantity": "0.0025"},
    ]


def make_plan_without_hash():
    return {
        "schema_version": bed.BASKET_PLAN_SCHEMA,
        "basket_id": "bsk_" + "0" * 32,
        "basket_lookup_key": "blk_" + "0" * 32,
        "parent_proposal_id": "prop_" + "1" * 16,
        "canonical_parent_proposal_hash": _hash64("1"),
        "parent_order_intent_id": "oid_" + "2" * 16,
        "canonical_parent_order_intent_hash": _hash64("2"),
        "account_fingerprint_hash": _hash64("3"),
        "broker_native_instrument": "XAUUSD",
        "side": "BUY",
        "order_type": "BUY_LIMIT",
        "entry_price": "1899.00",
        "stop_loss": "1895.00",
        "total_quantity": "0.01",
        "approved_aggregate_risk_id": "agg_" + "4" * 32,
        "child_count": 4,
        "children": make_plan_children(),
        "strategy_id": "SMA-001",
        "strategy_version": "1.0.0",
        "risk_policy_hash": _hash64("5"),
        "operating_mode": "MT5_DEMO_MANUAL",
        "created_at_utc": "2026-08-01T12:00:00.000000Z",
        "expires_at_utc": "2026-08-01T13:00:00.000000Z",
    }


def make_plan():
    without_hash = make_plan_without_hash()
    plan_hash = bed.canonical_basket_plan_hash_for(without_hash)
    plan = dict(without_hash)
    plan["canonical_basket_plan_hash"] = plan_hash
    return plan


class IdentityDeterminismTests(unittest.TestCase):
    def test_basket_lookup_key_deterministic_and_no_nonce(self):
        fields = {
            "parent_order_intent_id": "oid_1", "canonical_parent_order_intent_hash": _hash64("a"),
            "account_fingerprint_hash": _hash64("b"), "broker_native_instrument": "XAUUSD", "side": "BUY",
            "strategy_id": "SMA-001", "strategy_version": "1.0.0", "risk_policy_hash": _hash64("c"),
            "operating_mode": "MT5_DEMO_MANUAL", "authorization_identity": "LOCAL_OPERATOR",
            "child_count": 4, "target_set_hash": bed.target_set_hash(["1902", "1905"], ["50", "50"]),
        }
        key1 = bed.basket_lookup_key(fields)
        key2 = bed.basket_lookup_key(dict(fields))
        self.assertEqual(key1, key2)
        self.assertRegex(key1, r"^blk_[0-9a-f]{32}$")

    def test_basket_lookup_key_rejects_wrong_field_set(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.basket_lookup_key({"parent_order_intent_id": "x"})

    def test_basket_id_deterministic_from_lookup_key(self):
        lookup_key = "blk_" + "a" * 32
        self.assertEqual(bed.basket_id_for(lookup_key), bed.basket_id_for(lookup_key))
        self.assertRegex(bed.basket_id_for(lookup_key), r"^bsk_[0-9a-f]{32}$")

    def test_basket_id_rejects_malformed_lookup_key(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.basket_id_for("not-a-lookup-key")

    def test_basket_child_id_deterministic(self):
        key = bed.basket_child_lookup_key({
            "basket_id": "bsk_" + "0" * 32,
            "parent_proposal_id": "sp_" + "1" * 16, "canonical_parent_proposal_hash": _hash64("p"),
            "parent_order_intent_id": "exi_" + "2" * 16, "canonical_parent_order_intent_hash": _hash64("o"),
            "child_index": 0, "target_price": "1902", "target_allocation_percent": "25",
            "child_quantity": "0.0025", "account_fingerprint_hash": _hash64("f"),
            "broker_native_instrument": "XAUUSD", "side": "BUY", "order_type": "BUY_LIMIT",
            "entry_price": "1899", "stop_loss": "1895", "strategy_id": "SMA-001",
            "strategy_version": "1.0.0", "risk_policy_hash": _hash64("g"),
            "operating_mode": "MT5_DEMO_MANUAL", "expires_at_utc": "2026-08-01T13:00:00.000000Z",
        })
        self.assertEqual(bed.basket_child_id_for(key), bed.basket_child_id_for(key))
        self.assertRegex(bed.basket_child_id_for(key), r"^bc_[0-9a-f]{16}$")

    def test_basket_child_lookup_key_never_uses_canonical_basket_plan_hash(self):
        # Founder correction round (2026-08-01-020): a plan hash can never
        # be an input to the child IDs that are themselves part of that
        # same plan hash. Passing the old, now-circular field name must
        # fail closed as an invalid field set, not silently succeed.
        with self.assertRaises(bed.BasketValidationError):
            bed.basket_child_lookup_key({
                "basket_id": "bsk_" + "0" * 32, "canonical_basket_plan_hash": "bsk_" + "0" * 32,
                "child_index": 0, "target_price": "1902", "target_allocation_percent": "25",
                "child_quantity": "0.0025", "account_fingerprint_hash": _hash64("f"),
                "broker_native_instrument": "XAUUSD", "side": "BUY", "order_type": "BUY_LIMIT",
                "entry_price": "1899", "stop_loss": "1895", "strategy_id": "SMA-001",
                "strategy_version": "1.0.0", "risk_policy_hash": _hash64("g"),
                "operating_mode": "MT5_DEMO_MANUAL", "expires_at_utc": "2026-08-01T13:00:00.000000Z",
            })

    def test_different_child_index_yields_different_child_id(self):
        base_fields = {
            "basket_id": "bsk_" + "0" * 32,
            "parent_proposal_id": "sp_" + "1" * 16, "canonical_parent_proposal_hash": _hash64("p"),
            "parent_order_intent_id": "exi_" + "2" * 16, "canonical_parent_order_intent_hash": _hash64("o"),
            "target_price": "1902", "target_allocation_percent": "25",
            "child_quantity": "0.0025", "account_fingerprint_hash": _hash64("f"),
            "broker_native_instrument": "XAUUSD", "side": "BUY", "order_type": "BUY_LIMIT",
            "entry_price": "1899", "stop_loss": "1895", "strategy_id": "SMA-001",
            "strategy_version": "1.0.0", "risk_policy_hash": _hash64("g"),
            "operating_mode": "MT5_DEMO_MANUAL", "expires_at_utc": "2026-08-01T13:00:00.000000Z",
        }
        key0 = bed.basket_child_lookup_key({**base_fields, "child_index": 0})
        key1 = bed.basket_child_lookup_key({**base_fields, "child_index": 1})
        self.assertNotEqual(bed.basket_child_id_for(key0), bed.basket_child_id_for(key1))

    def test_check_result_id_deterministic(self):
        id1 = bed.check_result_id_for("bsk_" + "0" * 32, "bc_" + "a" * 16, _hash64("x"), "2026-08-01T12:00:00.000000Z")
        id2 = bed.check_result_id_for("bsk_" + "0" * 32, "bc_" + "a" * 16, _hash64("x"), "2026-08-01T12:00:00.000000Z")
        self.assertEqual(id1, id2)
        self.assertRegex(id1, r"^bcr_[0-9a-f]{16}$")

    def test_confirmation_request_id_unique_per_cycle_number(self):
        basis_hash = _hash64("h")
        id_cycle_1 = bed.confirmation_request_id_for("bsk_" + "0" * 32, _hash64("p"), basis_hash, 1, "2026-08-01T12:00:00.000000Z", "2026-08-01T12:05:00.000000Z")
        id_cycle_2 = bed.confirmation_request_id_for("bsk_" + "0" * 32, _hash64("p"), basis_hash, 2, "2026-08-01T12:00:00.000000Z", "2026-08-01T12:05:00.000000Z")
        self.assertNotEqual(id_cycle_1, id_cycle_2)
        self.assertRegex(id_cycle_1, r"^creq_[0-9a-f]{32}$")

    def test_challenge_hex_unique_per_request_id(self):
        challenge_1 = bed.challenge_hex_for("creq_" + "1" * 32, "bsk_" + "0" * 32, _hash64("p"), _hash64("b"))
        challenge_2 = bed.challenge_hex_for("creq_" + "2" * 32, "bsk_" + "0" * 32, _hash64("p"), _hash64("b"))
        self.assertNotEqual(challenge_1, challenge_2)
        self.assertRegex(challenge_1, r"^[0-9a-f]{16}$")

    def test_no_credential_or_secret_field_in_any_identity_material(self):
        # None of the identity functions accept or hash anything resembling
        # a broker credential; this is a structural check that the field
        # sets they validate never include such a name.
        for fields in (bed.BASKET_PLAN_FIELDS, bed.BASKET_CHILD_INTENT_FIELDS, bed.BASKET_CONFIRMATION_FIELDS):
            for name in fields:
                lowered = name.lower()
                self.assertNotIn("password", lowered)
                self.assertNotIn("secret", lowered)
                self.assertNotIn("api_key", lowered)


class ConfirmationEntryParsingTests(unittest.TestCase):
    def test_exact_format_accepted(self):
        self.assertEqual(bed.parse_confirmation_entry("CONFIRM-BASKET " + "a" * 16), "a" * 16)

    def test_bare_confirm_rejected(self):
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.parse_confirmation_entry("yes")
        self.assertEqual(ctx.exception.reason_code, "BASKET_CONFIRMATION_FORMAT_INVALID")

    def test_wrong_case_rejected(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.parse_confirmation_entry("confirm-basket " + "a" * 16)

    def test_extra_token_rejected(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.parse_confirmation_entry("CONFIRM-BASKET " + "a" * 16 + " extra")

    def test_non_ascii_rejected(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.parse_confirmation_entry("CONFIRM-BASKET " + "a" * 15 + "é")

    def test_wrong_length_hex_rejected(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.parse_confirmation_entry("CONFIRM-BASKET " + "a" * 17)

    def test_uppercase_hex_rejected(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.parse_confirmation_entry("CONFIRM-BASKET " + "A" * 16)

    def test_round_trip_format_then_parse(self):
        challenge = "0123456789abcdef"
        self.assertEqual(bed.parse_confirmation_entry(bed.format_confirmation_entry(challenge)), challenge)


class ConservationTests(unittest.TestCase):
    def test_exact_even_split_conserves_quantity(self):
        quantities = bed.compute_child_quantities("0.04", ["25", "25", "25", "25"], "0.01", "100", "0.01")
        self.assertEqual(quantities, ["0.01", "0.01", "0.01", "0.01"])

    def test_uneven_allocation_still_conserves_exactly(self):
        quantities = bed.compute_child_quantities("0.10", ["50", "30", "20"], "0.01", "100", "0.01")
        self.assertEqual([str(q) for q in quantities], ["0.05", "0.03", "0.02"])
        total = sum(float(q) for q in quantities)
        self.assertAlmostEqual(total, 0.10, places=8)

    def test_allocation_sum_must_be_exactly_100(self):
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.compute_child_quantities("1", ["30", "30", "30"], "0.01", "100", "0.01")
        self.assertEqual(ctx.exception.reason_code, "BASKET_ALLOCATION_SUM_INVALID")

    def test_unresolvable_step_fails_closed_not_rounded(self):
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.compute_child_quantities("0.01", ["50", "50"], "0.01", "100", "0.01")
        self.assertEqual(ctx.exception.reason_code, "BASKET_QUANTITY_CONSERVATION_UNRESOLVABLE")

    def test_below_minimum_volume_fails_closed(self):
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.compute_child_quantities("0.01", ["25", "25", "25", "25"], "0.01", "100", "0.0025")
        self.assertEqual(ctx.exception.reason_code, "BASKET_CHILD_QUANTITY_BELOW_MINIMUM")

    def test_above_maximum_volume_fails_closed(self):
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.compute_child_quantities("400", ["50", "50"], "0.01", "100", "0.01")
        self.assertEqual(ctx.exception.reason_code, "BASKET_CHILD_QUANTITY_ABOVE_MAXIMUM")

    def test_empty_allocations_rejected(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.compute_child_quantities("0.04", [], "0.01", "100", "0.01")

    def test_zero_allocation_rejected(self):
        with self.assertRaises(bed.BasketValidationError):
            bed.compute_child_quantities("0.04", ["0", "100"], "0.01", "100", "0.01")


class BasketPlanValidationTests(unittest.TestCase):
    def test_valid_plan_round_trips(self):
        plan = make_plan()
        validated = bed.validate_basket_plan(plan)
        self.assertEqual(validated["basket_id"], plan["basket_id"])

    def test_unsupported_schema_version_rejected(self):
        plan = make_plan()
        plan["schema_version"] = "TRL_BASKET_PLAN.v0"
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_plan(plan)
        self.assertEqual(ctx.exception.reason_code, "BASKET_SCHEMA_VERSION_UNSUPPORTED")

    def test_child_count_out_of_bounds_rejected(self):
        plan = make_plan()
        plan["child_count"] = 1
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_plan(plan)
        self.assertEqual(ctx.exception.reason_code, "BASKET_CHILD_COUNT_INVALID")

    def test_hidden_child_detected(self):
        plan = make_plan()
        plan["children"] = plan["children"][:3]
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_plan(plan)
        self.assertEqual(ctx.exception.reason_code, "BASKET_HIDDEN_CHILD_DETECTED")

    def test_duplicate_target_price_rejected(self):
        plan = make_plan()
        plan["children"][1]["target_price"] = plan["children"][0]["target_price"]
        plan_hash = bed.canonical_basket_plan_hash_for(bed._plan_identity_fields(plan))
        plan["canonical_basket_plan_hash"] = plan_hash
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_plan(plan)
        self.assertEqual(ctx.exception.reason_code, "BASKET_TARGET_NOT_UNIQUE")

    def test_tampered_plan_hash_detected(self):
        plan = make_plan()
        plan["canonical_basket_plan_hash"] = _hash64("tampered")
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_plan(plan)
        self.assertEqual(ctx.exception.reason_code, "BASKET_HASH_MISMATCH")

    def test_wrong_operating_mode_rejected(self):
        plan = make_plan_without_hash()
        plan["operating_mode"] = "MT5_LIVE_MANUAL"
        plan["canonical_basket_plan_hash"] = bed.canonical_basket_plan_hash_for(plan)
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_plan(plan)
        self.assertEqual(ctx.exception.reason_code, "BASKET_CAPABILITY_DENIED")

    def test_out_of_order_child_index_rejected(self):
        plan = make_plan_without_hash()
        plan["children"][0]["child_index"] = 3
        plan["canonical_basket_plan_hash"] = bed.canonical_basket_plan_hash_for(plan)
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_plan(plan)
        self.assertEqual(ctx.exception.reason_code, "BASKET_TARGET_ORDER_INVALID")

    def test_never_touches_phase5_order_intent_schema(self):
        # basket_execution_data.py must not define, import as its own, or
        # reinterpret TRL_MT5_ORDER_INTENT.v1 (Section 1.1).
        self.assertNotEqual(bed.BASKET_PLAN_SCHEMA, med.ORDER_INTENT_SCHEMA)
        self.assertFalse(hasattr(bed, "ORDER_INTENT_SCHEMA"))
        self.assertFalse(hasattr(bed, "validate_order_intent"))


class BasketChildIntentValidationTests(unittest.TestCase):
    def make_child(self):
        child_without_hash = {
            "schema_version": bed.BASKET_CHILD_INTENT_SCHEMA,
            "basket_id": "bsk_" + "0" * 32,
            "canonical_basket_plan_hash_at_creation": _hash64("p"),
            "basket_child_id": "bc_" + "a" * 16,
            "child_index": 0,
            "parent_order_intent_id": "oid_" + "1" * 16,
            "account_fingerprint_hash": _hash64("f"),
            "broker_native_instrument": "XAUUSD",
            "side": "BUY",
            "order_type": "BUY_LIMIT",
            "entry_price": "1899.00",
            "stop_loss": "1895.00",
            "strategy_id": "SMA-001",
            "strategy_version": "1.0.0",
            "risk_policy_hash": _hash64("r"),
            "operating_mode": "MT5_DEMO_MANUAL",
            "expires_at_utc": "2026-08-01T13:00:00.000000Z",
            "target_price": "1902.00",
            "target_allocation_percent": "25",
            "child_quantity": "0.0025",
            "idempotency_key": "bc_" + "a" * 16,
        }
        child = dict(child_without_hash)
        child["canonical_basket_child_hash"] = bed.canonical_basket_child_hash_for(child_without_hash)
        return child

    def test_valid_child_round_trips(self):
        child = self.make_child()
        validated = bed.validate_basket_child_intent(child)
        self.assertEqual(validated["basket_child_id"], child["basket_child_id"])

    def test_idempotency_key_must_equal_basket_child_id(self):
        child = self.make_child()
        child["idempotency_key"] = "bc_" + "z" * 16
        child["canonical_basket_child_hash"] = bed.canonical_basket_child_hash_for(bed._child_identity_fields(child))
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_child_intent(child)
        self.assertEqual(ctx.exception.reason_code, "BASKET_SCHEMA_INVALID")

    def test_tampered_child_hash_detected(self):
        child = self.make_child()
        child["canonical_basket_child_hash"] = _hash64("tampered")
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_child_intent(child)
        self.assertEqual(ctx.exception.reason_code, "BASKET_HASH_MISMATCH")

    def test_non_finite_price_rejected(self):
        child = self.make_child()
        child["target_price"] = "nan"
        child["canonical_basket_child_hash"] = bed.canonical_basket_child_hash_for(bed._child_identity_fields(child))
        with self.assertRaises(bed.BasketValidationError):
            bed.validate_basket_child_intent(child)


class BasketConfirmationValidationTests(unittest.TestCase):
    def make_confirmation(self):
        without_hash = {
            "schema_version": bed.BASKET_CONFIRMATION_SCHEMA,
            "confirmation_request_id": "creq_" + "1" * 32,
            "confirmation_cycle_number": 1,
            "basket_id": "bsk_" + "0" * 32,
            "canonical_basket_plan_hash": _hash64("p"),
            "confirmation_basis_hash": _hash64("b"),
            "account_fingerprint_hash": _hash64("f"),
            "authorized_prior_filled_child_ids": [],
            "authorized_remaining_child_ids": ["bc_" + "a" * 16, "bc_" + "b" * 16],
            "authorized_start_child_id": "bc_" + "a" * 16,
            "ordered_required_check_ids": ["bcr_" + "1" * 16, "bcr_" + "2" * 16],
            "ordered_required_check_hashes": [_hash64("x"), _hash64("y")],
            "challenge_derivation_version": bed.CONFIRM_CHALLENGE_DOMAIN,
            "challenge_hex": "a" * 16,
            "requested_at_utc": "2026-08-01T12:00:00.000000Z",
            "expires_at_utc": "2026-08-01T12:05:00.000000Z",
            "status": "REQUESTED",
            "accepted_at_utc": None,
            "expired_at_utc": None,
            "invalidated_at_utc": None,
            "invalidation_reason": None,
        }
        record = dict(without_hash)
        record["canonical_confirmation_request_hash"] = bed.canonical_confirmation_request_hash_for(
            bed._confirmation_identity_fields(without_hash)
        )
        return record

    def test_valid_confirmation_round_trips(self):
        record = self.make_confirmation()
        validated = bed.validate_basket_confirmation(record)
        self.assertEqual(validated["confirmation_request_id"], record["confirmation_request_id"])

    def test_authorized_start_must_be_member_of_remaining(self):
        record = self.make_confirmation()
        record["authorized_start_child_id"] = "bc_" + "z" * 16
        record["canonical_confirmation_request_hash"] = bed.canonical_confirmation_request_hash_for(
            bed._confirmation_identity_fields(record)
        )
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_confirmation(record)
        self.assertEqual(ctx.exception.reason_code, "BASKET_SCHEMA_INVALID")

    def test_check_ids_must_align_with_remaining(self):
        record = self.make_confirmation()
        record["ordered_required_check_ids"] = ["bcr_" + "1" * 16]
        record["ordered_required_check_hashes"] = [_hash64("x")]
        record["canonical_confirmation_request_hash"] = bed.canonical_confirmation_request_hash_for(
            bed._confirmation_identity_fields(record)
        )
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_confirmation(record)
        self.assertEqual(ctx.exception.reason_code, "BASKET_SCHEMA_INVALID")

    def test_invalid_status_rejected(self):
        record = self.make_confirmation()
        record["status"] = "PENDING"
        record["canonical_confirmation_request_hash"] = bed.canonical_confirmation_request_hash_for(
            bed._confirmation_identity_fields(record)
        )
        with self.assertRaises(bed.BasketValidationError):
            bed.validate_basket_confirmation(record)

    def test_tampered_request_hash_detected(self):
        record = self.make_confirmation()
        record["canonical_confirmation_request_hash"] = _hash64("tampered")
        with self.assertRaises(bed.BasketValidationError) as ctx:
            bed.validate_basket_confirmation(record)
        self.assertEqual(ctx.exception.reason_code, "BASKET_HASH_MISMATCH")


class VocabularyClosureTests(unittest.TestCase):
    def test_basket_statuses_partition_into_terminal_and_nonterminal(self):
        self.assertEqual(
            set(bed.BASKET_STATUSES),
            set(bed.TERMINAL_BASKET_STATUSES) | set(bed.NONTERMINAL_BASKET_STATUSES),
        )
        self.assertEqual(set(bed.TERMINAL_BASKET_STATUSES) & set(bed.NONTERMINAL_BASKET_STATUSES), set())

    def test_child_states_partition_into_terminal_and_nonterminal(self):
        self.assertEqual(
            set(bed.BASKET_CHILD_STATES),
            set(bed.TERMINAL_BASKET_CHILD_STATES) | set(bed.NONTERMINAL_BASKET_CHILD_STATES),
        )
        self.assertEqual(set(bed.TERMINAL_BASKET_CHILD_STATES) & set(bed.NONTERMINAL_BASKET_CHILD_STATES), set())

    def test_no_cancelled_child_state_exists(self):
        self.assertNotIn("CANCELLED", bed.BASKET_CHILD_STATES)

    def test_no_child_level_awaiting_confirmation_state(self):
        self.assertNotIn("AWAITING_CONFIRMATION", bed.BASKET_CHILD_STATES)

    def test_reason_codes_are_unique(self):
        self.assertEqual(len(bed.BASKET_REASON_CODES), len(set(bed.BASKET_REASON_CODES)))

    def test_reason_codes_include_send_stage_rejection_and_partial_codes(self):
        self.assertIn("BASKET_CHILD_SEND_REJECTED", bed.BASKET_REASON_CODES)
        self.assertIn("BASKET_CHILD_SEND_PARTIALLY_FILLED", bed.BASKET_REASON_CODES)

    def test_min_max_child_count_matches_contract(self):
        self.assertEqual(bed.MIN_CHILD_COUNT, 2)
        self.assertEqual(bed.MAX_CHILD_COUNT, 4)


if __name__ == "__main__":
    unittest.main(verbosity=2)
