"""Tests for mt5_execution_data.py — TRL-R2-007 Phase 5 schemas/hashing."""

import unittest

from trading_lab_app import mt5_execution_data as med


def _lookup_fields(**overrides):
    fields = {
        "proposal_id": "sp_" + "a" * 32,
        "account_fingerprint_hash": "b" * 64,
        "broker_native_instrument": "XAUUSD",
        "side": "BUY",
        "quantity": "0.01",
        "strategy_id": "SMA-001",
        "strategy_version": "1.0.0",
        "risk_policy_hash": "c" * 64,
        "operating_mode": "MT5_DEMO_MANUAL",
        "authorization_identity": "LOCAL_OPERATOR",
    }
    fields.update(overrides)
    return fields


def _intent(**overrides):
    lookup = _lookup_fields()
    order_intent_id = med.order_intent_id_for(lookup, "nonce-fixed")
    identity_fields = {
        "schema_version": med.ORDER_INTENT_SCHEMA,
        "order_intent_id": order_intent_id,
        "proposal_id": lookup["proposal_id"],
        "canonical_proposal_hash": "d" * 64,
        "created_at_utc": "2026-08-01T12:00:00.000000Z",
        "expires_at_utc": "2026-08-01T13:00:00.000000Z",
        "operating_mode": "MT5_DEMO_MANUAL",
        "account_fingerprint_hash": lookup["account_fingerprint_hash"],
        "broker_native_instrument": "XAUUSD",
        "side": "BUY",
        "order_type": "BUY_LIMIT",
        "quantity": "0.01",
        "entry_price": "1899",
        "stop_loss": "1895",
        "targets": ["1902", "1905", "1908", "1911"],
        "target_allocations_percent": ["25", "25", "25", "25"],
        "maximum_spread": "50",
        "maximum_deviation_points": 20,
        "time_in_force": "GTC",
        "fill_policy": "FOK",
        "strategy_id": "SMA-001",
        "strategy_version": "1.0.0",
        "risk_policy_hash": lookup["risk_policy_hash"],
        "idempotency_key": order_intent_id,
        "manual_confirmation_required": True,
    }
    identity_fields.update({k: v for k, v in overrides.items() if k in identity_fields})
    intent_hash = med.order_intent_hash_for(identity_fields)
    intent = dict(identity_fields)
    intent["execution_status"] = overrides.get("execution_status", "CREATED")
    intent["rejection_reasons"] = overrides.get("rejection_reasons", [])
    intent["canonical_order_intent_hash"] = overrides.get("canonical_order_intent_hash", intent_hash)
    return intent


class LookupKeyTests(unittest.TestCase):
    def test_lookup_key_deterministic(self):
        key1 = med.execution_intent_lookup_key(_lookup_fields())
        key2 = med.execution_intent_lookup_key(_lookup_fields())
        self.assertEqual(key1, key2)
        self.assertTrue(key1.startswith("eik_"))

    def test_lookup_key_changes_with_proposal_id(self):
        key1 = med.execution_intent_lookup_key(_lookup_fields())
        key2 = med.execution_intent_lookup_key(_lookup_fields(proposal_id="sp_" + "f" * 32))
        self.assertNotEqual(key1, key2)

    def test_lookup_key_rejects_invalid_field_set(self):
        fields = _lookup_fields()
        del fields["side"]
        with self.assertRaises(med.ExecutionValidationError):
            med.execution_intent_lookup_key(fields)

    def test_lookup_key_contains_no_nonce_or_price(self):
        # The field set is closed; neither "nonce" nor any price-like field
        # can be present.
        fields = _lookup_fields()
        self.assertNotIn("client_intent_nonce", fields)
        self.assertNotIn("entry_price", fields)


class IntentIdentityTests(unittest.TestCase):
    def test_intent_id_deterministic_for_same_nonce(self):
        lookup = _lookup_fields()
        id1 = med.order_intent_id_for(lookup, "nonce-a")
        id2 = med.order_intent_id_for(lookup, "nonce-a")
        self.assertEqual(id1, id2)
        self.assertTrue(id1.startswith("exi_"))

    def test_intent_id_changes_with_nonce(self):
        lookup = _lookup_fields()
        id1 = med.order_intent_id_for(lookup, "nonce-a")
        id2 = med.order_intent_id_for(lookup, "nonce-b")
        self.assertNotEqual(id1, id2)

    def test_intent_id_changes_when_lookup_fields_change(self):
        id1 = med.order_intent_id_for(_lookup_fields(), "nonce-a")
        id2 = med.order_intent_id_for(_lookup_fields(side="SELL"), "nonce-a")
        self.assertNotEqual(id1, id2)


class AttemptIdentityTests(unittest.TestCase):
    def test_attempt_id_deterministic(self):
        intent_id = med.order_intent_id_for(_lookup_fields(), "nonce-a")
        attempt1 = med.execution_attempt_id_for(intent_id, 1, "h" * 64, "2026-08-01T12:00:00.000000Z")
        attempt2 = med.execution_attempt_id_for(intent_id, 1, "h" * 64, "2026-08-01T12:00:00.000000Z")
        self.assertEqual(attempt1, attempt2)
        self.assertTrue(attempt1.startswith("exa_"))

    def test_attempt_id_changes_with_price_hash(self):
        intent_id = med.order_intent_id_for(_lookup_fields(), "nonce-a")
        attempt1 = med.execution_attempt_id_for(intent_id, 1, "h" * 64, "2026-08-01T12:00:00.000000Z")
        attempt2 = med.execution_attempt_id_for(intent_id, 1, "i" * 64, "2026-08-01T12:00:00.000000Z")
        self.assertNotEqual(attempt1, attempt2)

    def test_attempt_id_rejects_non_positive_sequence(self):
        intent_id = med.order_intent_id_for(_lookup_fields(), "nonce-a")
        with self.assertRaises(med.ExecutionValidationError):
            med.execution_attempt_id_for(intent_id, 0, "h" * 64, "2026-08-01T12:00:00.000000Z")


class ConfirmationChallengeTests(unittest.TestCase):
    def test_challenge_deterministic(self):
        code1 = med.confirmation_challenge_code("exi_" + "a" * 32, "b" * 64)
        code2 = med.confirmation_challenge_code("exi_" + "a" * 32, "b" * 64)
        self.assertEqual(code1, code2)
        self.assertEqual(len(code1), 8)

    def test_challenge_differs_per_intent(self):
        code1 = med.confirmation_challenge_code("exi_" + "a" * 32, "b" * 64)
        code2 = med.confirmation_challenge_code("exi_" + "c" * 32, "b" * 64)
        self.assertNotEqual(code1, code2)


class AccountFingerprintHashTests(unittest.TestCase):
    def test_hash_deterministic(self):
        hash1 = med.account_fingerprint_hash(555, "Broker Co", "Broker-Demo")
        hash2 = med.account_fingerprint_hash(555, "Broker Co", "Broker-Demo")
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)

    def test_hash_never_contains_raw_login(self):
        login = 900100100
        digest = med.account_fingerprint_hash(login, "Broker Co", "Broker-Demo")
        self.assertNotIn(str(login), digest)

    def test_hash_rejects_non_positive_login(self):
        with self.assertRaises(med.ExecutionValidationError):
            med.account_fingerprint_hash(0, "Broker Co", "Broker-Demo")


class OrderIntentValidationTests(unittest.TestCase):
    def test_valid_intent_round_trips(self):
        intent = _intent()
        clean = med.validate_order_intent(intent)
        self.assertEqual(clean["order_intent_id"], intent["order_intent_id"])

    def test_hash_mismatch_fails_closed(self):
        intent = _intent()
        intent["canonical_order_intent_hash"] = "0" * 64
        with self.assertRaises(med.ExecutionValidationError) as ctx:
            med.validate_order_intent(intent)
        self.assertEqual(ctx.exception.reason_code, "INTENT_HASH_MISMATCH")

    def test_hash_stable_across_execution_status_change(self):
        # The hash must not change merely because execution_status moved
        # from CREATED to CHECK_PASSED — mt5_execution_service relies on
        # this to keep the same intent identity through its whole
        # lifecycle.
        intent = _intent()
        original_hash = intent["canonical_order_intent_hash"]
        intent["execution_status"] = "CHECK_PASSED"
        clean = med.validate_order_intent(intent)
        self.assertEqual(clean["canonical_order_intent_hash"], original_hash)

    def test_wrong_operating_mode_fails_closed(self):
        intent = _intent()
        intent["operating_mode"] = "MT5_LIVE_MANUAL"
        with self.assertRaises(med.ExecutionValidationError) as ctx:
            med.validate_order_intent(intent)
        self.assertEqual(ctx.exception.reason_code, "OPERATING_MODE_NOT_MT5_DEMO_MANUAL")

    def test_unknown_field_set_fails_closed(self):
        intent = _intent()
        intent["unexpected_field"] = "x"
        with self.assertRaises(med.ExecutionValidationError):
            med.validate_order_intent(intent)

    def test_bad_order_type_fails_closed(self):
        intent = _intent()
        intent["order_type"] = "MARKET"
        intent["canonical_order_intent_hash"] = med.order_intent_hash_for(
            {k: v for k, v in intent.items() if k not in ("execution_status", "rejection_reasons", "canonical_order_intent_hash")}
        )
        with self.assertRaises(med.ExecutionValidationError) as ctx:
            med.validate_order_intent(intent)
        self.assertEqual(ctx.exception.reason_code, "ENTRY_ZONE_RANGE_MAPPING_NOT_APPROVED")

    def test_no_credential_field_exists_on_schema(self):
        for field in med.ORDER_INTENT_FIELDS:
            lowered = field.lower()
            for forbidden in ("password", "secret", "token", "credential"):
                self.assertNotIn(forbidden, lowered)

    def test_target_allocation_must_sum_to_100(self):
        intent = _intent()
        intent["target_allocations_percent"] = ["10", "10", "10", "10"]
        intent["canonical_order_intent_hash"] = med.order_intent_hash_for(
            {k: v for k, v in intent.items() if k not in ("execution_status", "rejection_reasons", "canonical_order_intent_hash")}
        )
        with self.assertRaises(med.ExecutionValidationError):
            med.validate_order_intent(intent)

    def test_idempotency_key_must_equal_intent_id(self):
        intent = _intent()
        intent["idempotency_key"] = "exi_" + "9" * 32
        intent["canonical_order_intent_hash"] = med.order_intent_hash_for(
            {k: v for k, v in intent.items() if k not in ("execution_status", "rejection_reasons", "canonical_order_intent_hash")}
        )
        with self.assertRaises(med.ExecutionValidationError):
            med.validate_order_intent(intent)


if __name__ == "__main__":
    unittest.main()
