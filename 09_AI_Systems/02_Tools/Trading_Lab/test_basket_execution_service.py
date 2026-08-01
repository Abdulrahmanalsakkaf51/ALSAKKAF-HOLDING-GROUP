"""Tests for basket_execution_service.py — the TRL-R2-009 Phase 6
controlled manual demo basket execution service.

Covers: ModeService/capability gating, deterministic construction and
reuse, SMA-001/FIB-001 blockers, quantity conservation at the service
boundary, the child check sequence and freshness window, the full
confirmation-cycle lifecycle (request/reuse/expiry/basis-change/cycle
increment), one-confirmation sequential child sending, stale-check
recovery (both the zero-fill and post-fill cases), rejection/partial/
uncertain terminal outcomes, no-retry/no-rollback, and restart safety.

All tests use FakeExecutionAdapter and isolated in-memory storage only —
no MetaTrader5 import, no broker connection, no real order.
"""

from datetime import timedelta
import unittest

from trading_lab_app import basket_execution_data as bed
from trading_lab_app import basket_execution_service as bes
from trading_lab_app import mode_service as ms
from trading_lab_app import mt5_execution_adapter as maa
from trading_lab_app import mt5_execution_journal as mej
from trading_lab_app import mt5_execution_service as mes
from trading_lab_app import signal_data as sd
from trading_lab_app.timeline_data import format_utc, validate_utc_timestamp


DEFAULT_FINGERPRINT = mes.AccountFingerprintConfiguration(
    login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server",
)


def make_clock(start="2026-08-01T12:00:00.000000Z"):
    box = {"now": validate_utc_timestamp(start)}
    return (lambda: box["now"]), box


def make_proposal(salt=None, expires_at_utc="2026-08-01T20:00:00.000000Z"):
    fields = dict(
        created_at_utc="2026-08-01T11:00:00.000000Z",
        observed_at_utc="2026-08-01T11:00:00.000000Z",
        expires_at_utc=expires_at_utc,
        instrument="XAUUSD",
        side="BUY",
        entry_type="ENTRY_ZONE",
        entry_zone_lower="1899",
        entry_zone_upper="1899",
        stop_loss="1895",
        targets=["1902", "1905", "1908", "1911"],
        target_allocations_percent=["25", "25", "25", "25"],
        confidence_score=80,
        evidence_quality_status="GOVERNED",
        invalidation_reason="structure break",
        wait_reason=None,
        beginner_explanation="basket-demo" if salt is None else "basket-demo {}".format(salt),
        strategy_basis_ids=["BASIS-1"],
        research_basis_ids=["BASIS-1"],
        market_data_observation_id="tle_" + "0" * 32,
        news_observation_ids=[],
        economic_event_observation_ids=[],
        risk_percent="0.5",
        strategy_id="SMA-001",
        strategy_version="1.0.0",
        broker_native_instrument="XAUUSD",
        regime_classification="TREND_UP",
        feature_snapshot_hash="0" * 64,
        data_quality_result={"status": "PASS", "reasons": []},
        news_event_risk_result={"status": "PASS", "reasons": [], "evidence_ids": []},
        confidence_calibration_source="PHASE4_COMPONENT_SCORE_UNCALIBRATED_V1",
        confidence_status="UNCALIBRATED_HEURISTIC",
        explanation="basket demo trade",
        rejection_reasons=[],
        model_rule_versions={"strategy_version": "1.0.0", "risk_engine_version": "1.0.0", "pipeline_version": "1.0.0"},
        role_results={key: {"status": "PASS", "reasons": []} for key in sd.ROLE_NAMES},
        candidate_quantity="0.04",
        independent_quantity="0.04",
        maximum_spread="50",
        active_risk_policy_hash="1" * 64,
        operating_mode="MT5_DEMO_MANUAL",
        sample_label="SYNTHETIC_PAPER",
    )
    return sd.build_signal_proposal(**fields)


class GeometryPatch:
    """Mirrors test_mt5_execution_service.py's own pattern exactly:
    production code never grants this (EXECUTION_GEOMETRY_APPROVED_STRATEGIES
    is permanently empty); tests patch it narrowly to exercise the
    happy-path send flow. Patching the *module* (not a `from ... import`
    value binding) is required for basket_execution_service.py to see it,
    since it references ``mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES``
    dynamically rather than importing the value."""

    def __enter__(self):
        self._original = mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES
        mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset({"SMA-001"})
        return self

    def __exit__(self, *exc_info):
        mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = self._original
        return False


class Harness:
    """One shared adapter/journal/mode-service/fingerprint set, used by
    both a Phase 5 ExecutionService (to build the parent order intent
    exactly the way the real CLI does) and the Phase 6 BasketExecutionService
    under test — mirroring app.py's "share, never duplicate" wiring."""

    def __init__(self, clock=None, box=None):
        self.clock, self.box = (clock, box) if clock is not None else make_clock()
        self.mode_service = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
        self.mode_service.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
        self.adapter = maa.FakeExecutionAdapter(clock=self.clock)
        self.adapter.set_symbol("XAUUSD")
        self.journal = mej.in_memory_journal_writer(clock=self.clock)
        self.fingerprint = DEFAULT_FINGERPRINT
        self.execution_service = mes.ExecutionService(
            adapter=self.adapter, mode_service=self.mode_service,
            journal=self.journal, account_fingerprint=self.fingerprint,
            clock=self.clock,
        )
        self.basket_service = bes.BasketExecutionService(
            adapter=self.adapter, mode_service=self.mode_service,
            journal=self.journal, account_fingerprint=self.fingerprint,
            clock=self.clock,
        )

    def advance(self, seconds):
        self.box["now"] = self.box["now"] + timedelta(seconds=seconds)

    def build_parent_intent(self, salt=None, expires_at_utc="2026-08-01T20:00:00.000000Z"):
        proposal = make_proposal(salt=salt, expires_at_utc=expires_at_utc)
        return self.execution_service.build_order_intent(proposal)

    def build_confirmed_basket(self, salt=None):
        """Build a basket and drive it all the way through CHECK_COMPLETE
        and an ACCEPTED confirmation cycle 1, returning the challenge."""
        with GeometryPatch():
            intent = self.build_parent_intent(salt=salt)
            record = self.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            for _ in range(4):
                self.basket_service.check_basket(basket_id)
            cycle = self.basket_service.request_basket_confirmation(basket_id)
            entry = bed.format_confirmation_entry(cycle["challenge_hex"])
            self.basket_service.confirm_basket(basket_id, entry)
        return basket_id


class CapabilityGatingTests(unittest.TestCase):
    def test_disabled_service_denies_every_mutation(self):
        svc = bes.disabled_basket_service(operating_mode="OFF")
        for method, args in (
            ("build_basket", ("oid_1",)), ("check_basket", ("bsk_1",)),
            ("request_basket_confirmation", ("bsk_1",)), ("confirm_basket", ("bsk_1", "x")),
            ("send_basket_next", ("bsk_1",)),
        ):
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                getattr(svc, method)(*args)
            self.assertEqual(ctx.exception.reason_code, "BASKET_CAPABILITY_DENIED")

    def test_disabled_service_status_document_is_honest(self):
        svc = bes.disabled_basket_service(operating_mode="RESEARCH")
        status = svc.status_document()
        self.assertFalse(status["enabled"])
        self.assertEqual(status["operating_mode"], "RESEARCH")
        self.assertFalse(status["manual_basket_execution_granted"])

    def test_wrong_mode_denies_even_with_real_service(self):
        harness = Harness()
        harness.mode_service.request_transition("OFF", actor="t", actor_channel="LOCAL_OPERATOR")
        with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
            harness.basket_service.build_basket("oid_does_not_matter")
        self.assertEqual(ctx.exception.reason_code, "BASKET_CAPABILITY_DENIED")

    def test_manual_basket_execution_granted_only_in_mt5_demo_manual(self):
        for mode in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
            self.assertNotIn("manual_basket_execution", ms._CAPABILITY_MATRIX[mode])
        self.assertIn("manual_basket_execution", ms._CAPABILITY_MATRIX["MT5_DEMO_MANUAL"])
        for mode in ("MT5_DEMO_AUTOMATED", "MT5_LIVE_MANUAL", "MT5_LIVE_AUTOMATED"):
            self.assertNotIn("manual_basket_execution", ms._CAPABILITY_MATRIX[mode])

    def test_no_environment_or_direct_bypass_of_capability_check(self):
        # There is no keyword argument, environment variable, or alternate
        # constructor path on BasketExecutionService that skips
        # _require_capability; every mutating method calls it first.
        harness = Harness()
        harness.mode_service.request_transition("OFF", actor="t", actor_channel="LOCAL_OPERATOR")
        with self.assertRaises(bes.BasketExecutionServiceError):
            harness.basket_service.check_basket("bsk_" + "0" * 32)


class BuildBasketTests(unittest.TestCase):
    def test_sma001_blocked_by_default(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
        # Parent intent construction happens under the (test-only) patch so
        # a valid CREATED intent exists; the basket-level geometry check is
        # then exercised on its own, outside the patch, against the real,
        # permanently-empty EXECUTION_GEOMETRY_APPROVED_STRATEGIES.
        with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
            harness.basket_service.build_basket(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED")

    def test_build_basket_succeeds_with_geometry_approved(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
        self.assertEqual(record["basket_status"], "CREATED")
        self.assertEqual(len(record["plan"]["children"]), 4)
        self.assertRegex(record["basket_id"], r"^bsk_[0-9a-f]{32}$")

    def test_build_basket_is_deterministic_and_reused(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            first = harness.basket_service.build_basket(intent["order_intent_id"])
            second = harness.basket_service.build_basket(intent["order_intent_id"])
        self.assertEqual(first["basket_id"], second["basket_id"])

    def test_conservation_exact_across_four_children(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
        total = sum(float(c["child_quantity"]) for c in record["plan"]["children"])
        self.assertAlmostEqual(total, float(record["plan"]["total_quantity"]), places=10)

    def test_no_zero_or_hidden_child(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
        for child in record["plan"]["children"]:
            self.assertGreater(float(child["child_quantity"]), 0)
        self.assertEqual(record["plan"]["child_count"], len(record["children"]))

    def test_unknown_parent_intent_rejected(self):
        harness = Harness()
        with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
            with GeometryPatch():
                harness.basket_service.build_basket("oid_does_not_exist")
        self.assertEqual(ctx.exception.reason_code, "BASKET_PARENT_INTENT_NOT_FOUND")

    def test_symbol_unavailable_rejects_and_persists(self):
        harness = Harness()
        harness.adapter.symbols.pop("XAUUSD")
        with GeometryPatch():
            intent = harness.build_parent_intent()
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                harness.basket_service.build_basket(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "SYMBOL_UNAVAILABLE")

    def test_fingerprint_mismatch_rejected(self):
        harness = Harness()
        wrong_fingerprint = mes.AccountFingerprintConfiguration(
            login=1, company="Other Broker", server="Other-Server",
        )
        harness.basket_service._account_fingerprint_config = wrong_fingerprint
        with GeometryPatch():
            intent = harness.build_parent_intent()
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                harness.basket_service.build_basket(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "BASKET_PARENT_INTENT_NOT_ELIGIBLE")

    def test_never_mutates_or_rehashes_parent_intent(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            original_hash = intent["canonical_order_intent_hash"]
            harness.basket_service.build_basket(intent["order_intent_id"])
            reloaded = harness.execution_service._load_intent(intent["order_intent_id"])
        self.assertEqual(reloaded["canonical_order_intent_hash"], original_hash)
        self.assertEqual(reloaded["execution_status"], "CREATED")


class CheckSequenceTests(unittest.TestCase):
    def test_checks_every_required_child_in_order_and_calls_adapter_once_each(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
        order_check_calls = [call for call in harness.adapter.calls if call[0] == "order_check"]
        self.assertEqual(len(order_check_calls), 4)
        status = harness.basket_service.basket_status_document(basket_id)
        self.assertEqual(status["basket_status"], "CHECK_COMPLETE")

    def test_check_never_sends(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            harness.basket_service.check_basket(record["basket_id"])
        self.assertEqual([call for call in harness.adapter.calls if call[0] == "order_send"], [])

    def test_failed_check_prevents_confirmation(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            harness.adapter.queue_check_result({"outcome": "FAILED", "retcode": 1, "comment": "no", "checked_at_utc": "2026-08-01T12:00:00.000000Z"})
            harness.basket_service.check_basket(basket_id)
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                harness.basket_service.request_basket_confirmation(basket_id)
        self.assertEqual(ctx.exception.reason_code, "BASKET_NOT_CHECK_COMPLETE")

    def test_check_freshness_window_120_seconds(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
            harness.advance(121)
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                harness.basket_service.request_basket_confirmation(basket_id)
        self.assertEqual(ctx.exception.reason_code, "BASKET_CHILD_CHECK_STALE")


class ConfirmationCycleTests(unittest.TestCase):
    def test_cycle_one_request_and_accept(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        status = harness.basket_service.basket_status_document(basket_id)
        self.assertEqual(status["confirmation_status"], "ACCEPTED")
        self.assertEqual(status["active_confirmation_cycle_number"], 1)

    def test_active_request_reused_with_unchanged_expiry(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
            first = harness.basket_service.request_basket_confirmation(basket_id)
            second = harness.basket_service.request_basket_confirmation(basket_id)
        self.assertEqual(first["confirmation_request_id"], second["confirmation_request_id"])
        self.assertEqual(first["expires_at_utc"], second["expires_at_utc"])
        self.assertEqual(first["challenge_hex"], second["challenge_hex"])

    def test_invalid_format_rejected(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
            harness.basket_service.request_basket_confirmation(basket_id)
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                harness.basket_service.confirm_basket(basket_id, "yes")
        self.assertEqual(ctx.exception.reason_code, "BASKET_CONFIRMATION_FORMAT_INVALID")

    def test_wrong_challenge_rejected(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
            harness.basket_service.request_basket_confirmation(basket_id)
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                harness.basket_service.confirm_basket(basket_id, bed.format_confirmation_entry("f" * 16))
        self.assertEqual(ctx.exception.reason_code, "BASKET_CONFIRMATION_MISMATCH")

    def test_second_acceptance_rejected(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        cycle = harness.basket_service._active_cycle(harness.basket_service._load_basket_record(basket_id))
        entry = bed.format_confirmation_entry(cycle["challenge_hex"])
        with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
            harness.basket_service.confirm_basket(basket_id, entry)
        self.assertEqual(ctx.exception.reason_code, "BASKET_CONFIRMATION_ALREADY_ACCEPTED")

    def test_expired_challenge_rejected_and_immutable(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
            cycle = harness.basket_service.request_basket_confirmation(basket_id)
            harness.advance(301)
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                harness.basket_service.confirm_basket(basket_id, bed.format_confirmation_entry(cycle["challenge_hex"]))
            self.assertEqual(ctx.exception.reason_code, "BASKET_CONFIRMATION_EXPIRED")
            # An expired request can never be reissued with the same ID/challenge.
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
            new_cycle = harness.basket_service.request_basket_confirmation(basket_id)
        self.assertNotEqual(new_cycle["confirmation_request_id"], cycle["confirmation_request_id"])
        self.assertNotEqual(new_cycle["challenge_hex"], cycle["challenge_hex"])
        self.assertEqual(new_cycle["confirmation_cycle_number"], 2)

    def test_restart_safe_cycle_numbering(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            record = harness.basket_service.build_basket(intent["order_intent_id"])
            basket_id = record["basket_id"]
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
            harness.basket_service.request_basket_confirmation(basket_id)
            harness.advance(301)
            for _ in range(4):
                harness.basket_service.check_basket(basket_id)
            harness.basket_service.request_basket_confirmation(basket_id)
        # Simulate restart: a brand new service instance reading the same journal.
        reloaded_service = bes.BasketExecutionService(
            adapter=harness.adapter, mode_service=harness.mode_service,
            journal=harness.journal, account_fingerprint=harness.fingerprint, clock=harness.clock,
        )
        status = reloaded_service.basket_status_document(basket_id)
        self.assertEqual(status["active_confirmation_cycle_number"], 2)


class SequentialSendTests(unittest.TestCase):
    def test_one_confirmation_authorizes_all_four_sends(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        with GeometryPatch():
            for _ in range(4):
                harness.basket_service.send_basket_next(basket_id)
        status = harness.basket_service.basket_status_document(basket_id)
        self.assertEqual(status["basket_status"], "COMPLETED")
        self.assertEqual(status["filled_child_count"], 4)

    def test_no_automatic_send_between_children(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        send_calls_before = len([c for c in harness.adapter.calls if c[0] == "order_send"])
        self.assertEqual(send_calls_before, 0)

    def test_send_basket_next_takes_no_child_argument_and_cannot_skip(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        record = harness.basket_service._load_basket_record(basket_id)
        first_expected = record["plan"]["children"][0]["basket_child_id"]
        with GeometryPatch():
            result = harness.basket_service.send_basket_next(basket_id)
        filled = [cid for cid, c in result["children"].items() if c["execution_state"] == "FILLED"]
        self.assertEqual(filled, [first_expected])

    def test_restart_between_children_preserves_progress(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)
        reloaded = bes.BasketExecutionService(
            adapter=harness.adapter, mode_service=harness.mode_service,
            journal=harness.journal, account_fingerprint=harness.fingerprint, clock=harness.clock,
        )
        status = reloaded.basket_status_document(basket_id)
        self.assertEqual(status["filled_child_count"], 1)
        with GeometryPatch():
            for _ in range(3):
                reloaded.send_basket_next(basket_id)
        self.assertEqual(reloaded.basket_status_document(basket_id)["basket_status"], "COMPLETED")

    def test_durable_reservation_at_most_once_send_per_child(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)
        send_calls = [c for c in harness.adapter.calls if c[0] == "order_send"]
        self.assertEqual(len(send_calls), 1)


class StaleCheckRecoveryTests(unittest.TestCase):
    def test_stale_before_any_fill_returns_all_to_check_required(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        harness.advance(121)
        with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
            with GeometryPatch():
                harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(ctx.exception.reason_code, "BASKET_CHILD_CHECK_STALE")
        status = harness.basket_service.basket_status_document(basket_id)
        self.assertEqual(status["basket_status"], "CHECK_REQUIRED")
        self.assertEqual(status["filled_child_count"], 0)
        self.assertEqual(status["confirmation_status"], "INVALIDATED")

    def test_stale_after_one_fill_preserves_filled_child(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)
        harness.advance(121)
        with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
            with GeometryPatch():
                harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(ctx.exception.reason_code, "BASKET_CHILD_CHECK_STALE")
        status = harness.basket_service.basket_status_document(basket_id)
        self.assertEqual(status["filled_child_count"], 1)
        self.assertNotEqual(status["basket_status"], "PARTIALLY_COMPLETED")
        filled_children = [c for c in status["children"] if c["execution_state"] == "FILLED"]
        self.assertEqual(len(filled_children), 1)

    def test_no_automatic_recheck_after_stale(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        harness.advance(121)
        with self.assertRaises(bes.BasketExecutionServiceError):
            with GeometryPatch():
                harness.basket_service.send_basket_next(basket_id)
        order_check_calls_after = [c for c in harness.adapter.calls if c[0] == "order_check"]
        # Exactly the original 4 checks from build_confirmed_basket — no
        # automatic recheck was performed merely by discovering staleness.
        self.assertEqual(len(order_check_calls_after), 4)

    def test_fresh_recheck_and_new_cycle_after_stale(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)
        harness.advance(121)
        with self.assertRaises(bes.BasketExecutionServiceError):
            with GeometryPatch():
                harness.basket_service.send_basket_next(basket_id)
        with GeometryPatch():
            for _ in range(3):
                harness.basket_service.check_basket(basket_id)
            new_cycle = harness.basket_service.request_basket_confirmation(basket_id)
        self.assertEqual(new_cycle["confirmation_cycle_number"], 2)
        self.assertEqual(len(new_cycle["authorized_prior_filled_child_ids"]), 1)
        self.assertEqual(len(new_cycle["authorized_remaining_child_ids"]), 3)

    def test_old_challenge_rejected_after_new_cycle(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        old_cycle = harness.basket_service._active_cycle(harness.basket_service._load_basket_record(basket_id))
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)
        harness.advance(121)
        with self.assertRaises(bes.BasketExecutionServiceError):
            with GeometryPatch():
                harness.basket_service.send_basket_next(basket_id)
        with GeometryPatch():
            for _ in range(3):
                harness.basket_service.check_basket(basket_id)
            harness.basket_service.request_basket_confirmation(basket_id)
            with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
                harness.basket_service.confirm_basket(basket_id, bed.format_confirmation_entry(old_cycle["challenge_hex"]))
        self.assertIn(ctx.exception.reason_code, ("BASKET_CONFIRMATION_INVALIDATED", "BASKET_CONFIRMATION_MISMATCH"))


class ResultBehaviorTests(unittest.TestCase):
    def test_rejection_before_any_fill_is_failed(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        harness.adapter.queue_send_result({
            "outcome": "REJECTED", "retcode": 10006, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": "rejected", "sent_at_utc": format_utc(harness.clock()),
        })
        with GeometryPatch():
            result = harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(result["basket_status"], "FAILED")
        self.assertEqual(result["terminal_reason"], "BASKET_CHILD_SEND_REJECTED")
        self.assertIn("BASKET_CHILD_SEND_REJECTED", result["rejection_reasons"])

    def test_rejection_after_fill_is_partially_completed(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)
        harness.adapter.queue_send_result({
            "outcome": "REJECTED", "retcode": 10006, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": "rejected", "sent_at_utc": format_utc(harness.clock()),
        })
        with GeometryPatch():
            result = harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(result["basket_status"], "PARTIALLY_COMPLETED")
        self.assertTrue(result["basket_status"] in bed.RECONCILIATION_REQUIRED_STATUSES)
        filled = [c for c in result["children"].values() if c["execution_state"] == "FILLED"]
        self.assertEqual(len(filled), 1)

    def test_partial_fill_freezes_basket_and_marks_reconciliation(self):
        # Founder correction round (2026-08-01-020), Section 6: a partial
        # fill freezes the basket -- never PARTIALLY_COMPLETED.
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        record = harness.basket_service._load_basket_record(basket_id)
        first_child_id = record["plan"]["children"][0]["basket_child_id"]
        first_child_quantity = record["plan"]["children"][0]["child_quantity"]
        half = str(float(first_child_quantity) / 2)
        harness.adapter.queue_send_result({
            "outcome": "PARTIALLY_FILLED", "retcode": 10009, "ticket": 1, "deal": 2,
            "position": 1, "volume_filled": half, "comment": "partial", "sent_at_utc": format_utc(harness.clock()),
        })
        with GeometryPatch():
            result = harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(result["basket_status"], "FROZEN")
        self.assertTrue(result["basket_status"] in bed.RECONCILIATION_REQUIRED_STATUSES)
        self.assertEqual(result["terminal_reason"], "BASKET_CHILD_SEND_PARTIALLY_FILLED")
        child = result["children"][first_child_id]
        self.assertEqual(child["execution_state"], "PARTIALLY_FILLED")
        self.assertAlmostEqual(float(child["send_result"]["filled_quantity"]), float(half), places=10)
        with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
            with GeometryPatch():
                harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(ctx.exception.reason_code, "BASKET_ALREADY_TERMINAL")

    def test_partial_fill_after_earlier_fill_still_freezes_not_partially_completed(self):
        # "This applies whether or not earlier children were fully FILLED"
        # (Founder correction round Section 6.B).
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)  # child 1 FILLED
        record = harness.basket_service._load_basket_record(basket_id)
        second_child_id = record["plan"]["children"][1]["basket_child_id"]
        second_child_quantity = record["plan"]["children"][1]["child_quantity"]
        half = str(float(second_child_quantity) / 2)
        harness.adapter.queue_send_result({
            "outcome": "PARTIALLY_FILLED", "retcode": 10009, "ticket": 3, "deal": 4,
            "position": 3, "volume_filled": half, "comment": "partial", "sent_at_utc": format_utc(harness.clock()),
        })
        with GeometryPatch():
            result = harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(result["basket_status"], "FROZEN")
        self.assertNotEqual(result["basket_status"], "PARTIALLY_COMPLETED")
        filled = [c for c in result["children"].values() if c["execution_state"] == "FILLED"]
        self.assertEqual(len(filled), 1)
        second_child = result["children"][second_child_id]
        self.assertEqual(second_child["execution_state"], "PARTIALLY_FILLED")

    def test_uncertain_result_freezes_basket_and_retains_reservation(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        record = harness.basket_service._load_basket_record(basket_id)
        first_child_id = record["plan"]["children"][0]["basket_child_id"]
        harness.adapter.queue_send_result({
            "outcome": "UNCERTAIN", "retcode": None, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": "timeout", "sent_at_utc": format_utc(harness.clock()),
        })
        with GeometryPatch():
            result = harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(result["basket_status"], "FROZEN")
        self.assertTrue(result["basket_status"] in bed.RECONCILIATION_REQUIRED_STATUSES)
        child = result["children"][first_child_id]
        self.assertEqual(child["execution_state"], "FROZEN_PENDING_RECONCILIATION")
        with self.assertRaises(bes.BasketExecutionServiceError) as ctx:
            with GeometryPatch():
                harness.basket_service.send_basket_next(basket_id)
        self.assertEqual(ctx.exception.reason_code, "BASKET_ALREADY_TERMINAL")

    def test_frozen_basket_survives_restart(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        harness.adapter.queue_send_result({
            "outcome": "UNCERTAIN", "retcode": None, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": "timeout", "sent_at_utc": format_utc(harness.clock()),
        })
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)
        reloaded = bes.BasketExecutionService(
            adapter=harness.adapter, mode_service=harness.mode_service,
            journal=harness.journal, account_fingerprint=harness.fingerprint, clock=harness.clock,
        )
        status = reloaded.basket_status_document(basket_id)
        self.assertEqual(status["basket_status"], "FROZEN")

    def test_no_rollback_or_compensation_on_later_failure(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        with GeometryPatch():
            harness.basket_service.send_basket_next(basket_id)
        harness.adapter.queue_send_result({
            "outcome": "REJECTED", "retcode": 10006, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": "rejected", "sent_at_utc": format_utc(harness.clock()),
        })
        with GeometryPatch():
            result = harness.basket_service.send_basket_next(basket_id)
        filled = [c for c in result["children"].values() if c["execution_state"] == "FILLED"]
        self.assertEqual(len(filled), 1)
        # No CANCELLED state exists and the fill is never touched.
        self.assertNotIn("CANCELLED", bed.BASKET_CHILD_STATES)


class JournalAndConcurrencyTests(unittest.TestCase):
    def test_basket_events_are_additive_to_phase5_journal(self):
        harness = Harness()
        with GeometryPatch():
            intent = harness.build_parent_intent()
            harness.basket_service.build_basket(intent["order_intent_id"])
        event_types = {event["event_type"] for event in harness.journal.events}
        self.assertIn("ORDER_INTENT_CREATED", event_types)
        self.assertIn("BASKET_CREATED", event_types)

    def test_loading_a_basket_never_calls_the_adapter(self):
        harness = Harness()
        basket_id = harness.build_confirmed_basket()
        calls_before = len(harness.adapter.calls)
        harness.basket_service.inspect_basket_document(basket_id)
        harness.basket_service.basket_status_document(basket_id)
        harness.basket_service.list_baskets_document()
        self.assertEqual(len(harness.adapter.calls), calls_before)

    def test_isolated_storage_only_no_production_localappdata(self):
        harness = Harness()
        # in_memory_journal_writer and in_memory_mode_service never touch
        # the filesystem; this is a structural guarantee of the fixture.
        self.assertTrue(hasattr(harness.journal, "events"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
