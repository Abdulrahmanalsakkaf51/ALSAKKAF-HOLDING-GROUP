"""Tests for mt5_execution_service.py — the TRL-R2-007 Phase 5 authority.

Covers the Phase 5 kickoff prompt's testing-requirements list: mode
gating, proposal revalidation chain, SMA/FIB blockers, order-intent
determinism, order_check, manual confirmation, order_send, idempotency/
duplicate protection, uncertain-result handling, and journal integrity.
All tests use the fake adapter and isolated in-memory storage only.
"""

from datetime import datetime, timezone
import unittest

from trading_lab_app import mode_service as ms
from trading_lab_app import mt5_execution_adapter as maa
from trading_lab_app import mt5_execution_data as med
from trading_lab_app import mt5_execution_journal as mej
from trading_lab_app import mt5_execution_service as mes
from trading_lab_app import signal_data as sd


DEFAULT_FINGERPRINT = mes.AccountFingerprintConfiguration(
    login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server",
)


def make_clock(start="2026-08-01T12:00:00.000000Z"):
    box = {"now": ms.validate_utc_timestamp(start) if hasattr(ms, "validate_utc_timestamp") else None}
    from trading_lab_app.timeline_data import validate_utc_timestamp
    box["now"] = validate_utc_timestamp(start)
    return lambda: box["now"], box


def make_proposal(
    strategy_id="SMA-001",
    strategy_version="1.0.0",
    side="BUY",
    expires_at_utc="2026-08-01T13:00:00.000000Z",
    entry_lower="1899",
    entry_upper="1899",
    candidate_quantity="0.01",
    independent_quantity="0.01",
    risk_policy_hash="1" * 64,
    instrument="XAUUSD",
    maximum_spread="50",
    salt=None,
):
    fields = dict(
        created_at_utc="2026-08-01T11:00:00.000000Z",
        observed_at_utc="2026-08-01T11:00:00.000000Z",
        expires_at_utc=expires_at_utc,
        instrument=instrument,
        side=side,
        entry_type="ENTRY_ZONE",
        entry_zone_lower=entry_lower,
        entry_zone_upper=entry_upper,
        stop_loss="1895",
        targets=["1902", "1905", "1908", "1911"],
        target_allocations_percent=["25", "25", "25", "25"],
        confidence_score=80,
        evidence_quality_status="GOVERNED",
        invalidation_reason="structure break",
        wait_reason=None,
        beginner_explanation="demo" if salt is None else "demo {}".format(salt),
        strategy_basis_ids=["BASIS-1"],
        research_basis_ids=["BASIS-1"],
        market_data_observation_id="tle_" + "0" * 32,
        news_observation_ids=[],
        economic_event_observation_ids=[],
        risk_percent="0.5",
        strategy_id=strategy_id,
        strategy_version=strategy_version,
        broker_native_instrument=instrument,
        regime_classification="TREND_UP",
        feature_snapshot_hash="0" * 64,
        data_quality_result={"status": "PASS", "reasons": []},
        news_event_risk_result={"status": "PASS", "reasons": [], "evidence_ids": []},
        confidence_calibration_source="PHASE4_COMPONENT_SCORE_UNCALIBRATED_V1",
        confidence_status="UNCALIBRATED_HEURISTIC",
        explanation="demo trade",
        rejection_reasons=[],
        model_rule_versions={"strategy_version": "1.0.0", "risk_engine_version": "1.0.0", "pipeline_version": "1.0.0"},
        role_results={key: {"status": "PASS", "reasons": []} for key in sd.ROLE_NAMES},
        candidate_quantity=candidate_quantity,
        independent_quantity=independent_quantity,
        maximum_spread=maximum_spread,
        active_risk_policy_hash=risk_policy_hash,
        operating_mode="MT5_DEMO_MANUAL",
        sample_label="SYNTHETIC_PAPER",
    )
    return sd.build_signal_proposal(**fields)


def make_wait_proposal():
    return sd.build_signal_proposal(
        schema_version=None,
        created_at_utc="2026-08-01T11:00:00.000000Z",
        observed_at_utc="2026-08-01T11:00:00.000000Z",
        expires_at_utc="2026-08-01T13:00:00.000000Z",
        instrument="XAUUSD",
        side="WAIT",
        entry_type="WAIT",
        entry_zone_lower=None,
        entry_zone_upper=None,
        stop_loss=None,
        targets=None,
        target_allocations_percent=None,
        confidence_score=50,
        evidence_quality_status="GOVERNED",
        invalidation_reason="none",
        wait_reason="insufficient bar history",
        beginner_explanation="demo",
        strategy_basis_ids=["BASIS-1"],
        research_basis_ids=["BASIS-1"],
        market_data_observation_id="tle_" + "0" * 32,
        news_observation_ids=[],
        economic_event_observation_ids=[],
        risk_percent="0",
        strategy_id="SMA-001",
        strategy_version="1.0.0",
        broker_native_instrument="XAUUSD",
        regime_classification="TREND_UP",
        feature_snapshot_hash="0" * 64,
        data_quality_result={"status": "PASS", "reasons": []},
        news_event_risk_result={"status": "PASS", "reasons": [], "evidence_ids": []},
        confidence_calibration_source="PHASE4_COMPONENT_SCORE_UNCALIBRATED_V1",
        confidence_status="UNCALIBRATED_HEURISTIC",
        explanation="demo wait",
        rejection_reasons=[],
        model_rule_versions={"strategy_version": "1.0.0", "risk_engine_version": "1.0.0", "pipeline_version": "1.0.0"},
        role_results={key: {"status": "PASS", "reasons": []} for key in sd.ROLE_NAMES},
        candidate_quantity=None,
        independent_quantity=None,
        maximum_spread="50",
        active_risk_policy_hash="1" * 64,
        operating_mode="MT5_DEMO_MANUAL",
        sample_label="SYNTHETIC_PAPER",
    )


def make_blocked_proposal():
    proposal = make_wait_proposal()
    identity = {k: v for k, v in proposal.items() if k not in ("proposal_id", "canonical_proposal_hash")}
    identity["side"] = "BLOCKED"
    identity["rejection_reasons"] = ["NO_STRATEGY_SIGNAL"]
    proposal_id, digest = sd.signal_proposal_id_for(identity)
    identity["proposal_id"] = proposal_id
    identity["canonical_proposal_hash"] = digest
    return sd.validate_signal_proposal(identity)


class Harness:
    """Builds an isolated ExecutionService wired to a fake adapter, a
    real (in-memory) mode service, and a controllable clock, with SMA-001
    execution geometry temporarily allowlisted for test purposes only —
    production code never grants this (EXECUTION_GEOMETRY_APPROVED_STRATEGIES
    is empty; see mt5_execution_service.py)."""

    def __init__(self, allow_geometry=True):
        self.clock, self.clock_box = make_clock()
        self.mode = ms.in_memory_mode_service(subsystem_builder=lambda _mode: None)
        self.mode.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
        self.store = mej.InMemoryExecutionJournalStore()
        self.journal = mej.ExecutionJournalWriter(store=self.store, clock=self.clock)
        self.adapter = maa.FakeExecutionAdapter(clock=self.clock)
        self.adapter.set_symbol("XAUUSD")
        self.fingerprint = DEFAULT_FINGERPRINT
        self.service = mes.ExecutionService(
            adapter=self.adapter, mode_service=self.mode, journal=self.journal,
            account_fingerprint=self.fingerprint, clock=self.clock,
        )
        self._original_geometry = mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES
        if allow_geometry:
            mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset({"SMA-001"})

    def restore(self):
        mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = self._original_geometry

    def advance(self, seconds):
        from datetime import timedelta
        self.clock_box["now"] = self.clock_box["now"] + timedelta(seconds=seconds)

    def restart(self):
        journal2 = mej.ExecutionJournalWriter(store=self.store, clock=self.clock)
        return mes.ExecutionService(
            adapter=self.adapter, mode_service=self.mode, journal=journal2,
            account_fingerprint=self.fingerprint, clock=self.clock,
        )


class HarnessTestCase(unittest.TestCase):
    def setUp(self):
        self.harness = Harness()
        self.addCleanup(self.harness.restore)

    def build_intent(self, **kwargs):
        proposal = make_proposal(**kwargs)
        return self.harness.service.build_order_intent(proposal)


class ModeGatingTests(unittest.TestCase):
    def test_off_does_not_construct_real_adapter_via_app_helper(self):
        from trading_lab_app import app
        adapter = app._execution_adapter_for_mode("OFF")
        self.assertIsInstance(adapter, maa.DisabledExecutionAdapter)

    def test_research_does_not_construct_real_adapter(self):
        from trading_lab_app import app
        adapter = app._execution_adapter_for_mode("RESEARCH")
        self.assertIsInstance(adapter, maa.DisabledExecutionAdapter)

    def test_synthetic_paper_does_not_construct_real_adapter(self):
        from trading_lab_app import app
        adapter = app._execution_adapter_for_mode("SYNTHETIC_PAPER")
        self.assertIsInstance(adapter, maa.DisabledExecutionAdapter)

    def test_only_mt5_demo_manual_constructs_real_adapter(self):
        from trading_lab_app import app
        adapter = app._execution_adapter_for_mode("MT5_DEMO_MANUAL")
        self.assertIsInstance(adapter, maa.RealMT5ExecutionAdapter)

    def test_unauthorized_modes_fail_closed(self):
        from trading_lab_app import app
        for mode in ("MT5_DEMO_AUTOMATED", "MT5_LIVE_MANUAL", "MT5_LIVE_AUTOMATED"):
            with self.assertRaises(app.ModeSubsystemConfigurationError):
                app._execution_adapter_for_mode(mode)

    def test_disabled_service_denies_every_mutation(self):
        service = mes.disabled_service()
        for method, args in (
            ("build_order_intent", ({},)),
            ("order_check", ("exi_x",)),
            ("request_confirmation", ("exi_x",)),
            ("confirm_and_send", ("exi_x", "code")),
        ):
            with self.assertRaises(mes.ExecutionServiceError):
                getattr(service, method)(*args)

    def test_capability_denied_without_mode_service(self):
        service = mes.ExecutionService(adapter=maa.fake_adapter())
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            service.build_order_intent({})
        self.assertEqual(ctx.exception.reason_code, "CAPABILITY_DENIED")

    def test_capability_denied_in_research_mode(self):
        mode = ms.in_memory_mode_service(subsystem_builder=lambda _m: None)
        mode.request_transition("RESEARCH", actor="t", actor_channel="LOCAL_OPERATOR")
        service = mes.ExecutionService(adapter=maa.fake_adapter(), mode_service=mode)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            service.build_order_intent({})
        self.assertEqual(ctx.exception.reason_code, "CAPABILITY_DENIED")

    def test_http_cannot_initiate_a_broker_action(self):
        # No mutating route exists for check/confirm/send at all —
        # server.py's EXECUTION_API_ROUTES is GET-only, and
        # test_mt5_execution_http.py exercises that HTTP surface directly
        # (including the global 405 for POST/PUT/PATCH/DELETE). This test
        # documents the CLI-only design at the module level: confirm_and_send
        # rejects any non-local actor_channel outright.
        service = mes.ExecutionService(adapter=maa.fake_adapter())
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            service.confirm_and_send("exi_" + "0" * 32, "code", actor_channel="HTTP")
        self.assertEqual(ctx.exception.reason_code, "CONFIRMATION_CHANNEL_NOT_LOCAL")


class SmaFibBlockerTests(unittest.TestCase):
    def test_sma001_blocked_by_execution_geometry_allowlist(self):
        harness = Harness(allow_geometry=False)
        proposal = make_proposal(strategy_id="SMA-001")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED")

    def test_fib001_blocked_by_registry_approval_pending(self):
        harness = Harness(allow_geometry=False)
        proposal = make_proposal(strategy_id="FIB-001", strategy_version="0.0.0")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "STRATEGY_PARAMETERS_NOT_APPROVED")

    def test_blockers_prevent_reaching_the_adapter(self):
        harness = Harness(allow_geometry=False)
        proposal = make_proposal(strategy_id="SMA-001")
        try:
            harness.service.build_order_intent(proposal)
        except mes.ExecutionServiceError:
            pass
        self.assertEqual(harness.adapter.calls, [])


class ProposalRevalidationTests(HarnessTestCase):
    def test_schema_invalid_fails_before_adapter_call(self):
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent({"not": "a proposal"})
        self.assertEqual(ctx.exception.reason_code, "PROPOSAL_SCHEMA_INVALID")
        self.assertEqual(self.harness.adapter.calls, [])

    def test_hash_mismatch_fails_before_adapter_call(self):
        proposal = make_proposal()
        tampered = dict(proposal)
        tampered["canonical_proposal_hash"] = "0" * 64
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(tampered)
        self.assertEqual(ctx.exception.reason_code, "PROPOSAL_HASH_MISMATCH")

    def test_expired_proposal_fails_before_adapter_call(self):
        proposal = make_proposal(expires_at_utc="2026-08-01T11:30:00.000000Z")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "PROPOSAL_EXPIRED")

    def test_blocked_proposal_fails_before_adapter_call(self):
        proposal = make_blocked_proposal()
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "PROPOSAL_BLOCKED")

    def test_wait_proposal_fails_before_adapter_call(self):
        proposal = make_wait_proposal()
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "PROPOSAL_WAIT")

    def test_strategy_version_mismatch_prevents_adapter_call(self):
        proposal = make_proposal(strategy_version="9.9.9")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "STRATEGY_VERSION_MISMATCH")

    def test_risk_policy_hash_mismatch_prevents_adapter_call(self):
        self.harness.service.expected_risk_policy_hash = "9" * 64
        proposal = make_proposal(risk_policy_hash="1" * 64)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "RISK_POLICY_HASH_MISMATCH")

    def test_role_quantity_mismatch_prevents_adapter_call(self):
        proposal = make_proposal(candidate_quantity="0.01", independent_quantity="0.02")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "ROLE_QUANTITY_MISMATCH")

    def test_entry_zone_range_not_approved(self):
        proposal = make_proposal(entry_lower="1898", entry_upper="1899")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "ENTRY_ZONE_RANGE_MAPPING_NOT_APPROVED")

    def test_unconfigured_account_fingerprint_is_external_blocker(self):
        self.harness.service.account_fingerprint = mes.unconfigured_account_fingerprint()
        proposal = make_proposal()
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "ACCOUNT_UNAVAILABLE")

    def test_instrument_not_allowlisted(self):
        proposal = make_proposal(instrument="EURUSD")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "INSTRUMENT_NOT_ALLOWLISTED")

    def test_journal_integrity_uncertain_fails_closed(self):
        self.harness.journal.startup_diagnostic_code = "JOURNAL_STORAGE_INVALID"
        proposal = make_proposal()
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.build_order_intent(proposal)
        self.assertEqual(ctx.exception.reason_code, "LOOKUP_STORE_INTEGRITY_UNCERTAIN")


class TwoFreshJournalIdentityTests(unittest.TestCase):
    """Formalizes the Founder-review two-fresh-journal experiment: per
    TRL_R2_007_MT5_EXECUTION_CONTRACT.md Section 5.1/5.3, the lookup key is
    the contract's sole no-nonce, cross-store-deterministic identity; the
    nonce-salted order_intent_id/canonical_order_intent_hash/idempotency_key
    are explicitly NOT claimed to be deterministic across two genuinely
    independent journals that have never seen each other's data -- only
    within one continuous durable store, via lookup-before-create reuse."""

    def setUp(self):
        self.harness_a = Harness()
        self.addCleanup(self.harness_a.restore)
        self.harness_b = Harness()
        self.addCleanup(self.harness_b.restore)

    def test_lookup_key_and_proposal_identity_are_equal_across_journals(self):
        proposal = make_proposal(salt="two-journal")
        intent_a = self.harness_a.service.build_order_intent(proposal)
        intent_b = self.harness_b.service.build_order_intent(proposal)

        lookup_a = [e for e in self.harness_a.journal.events if e["event_type"] == "ORDER_INTENT_CREATED"][0]["payload"]["lookup_key"]
        lookup_b = [e for e in self.harness_b.journal.events if e["event_type"] == "ORDER_INTENT_CREATED"][0]["payload"]["lookup_key"]

        self.assertEqual(intent_a["proposal_id"], intent_b["proposal_id"])
        self.assertEqual(intent_a["canonical_proposal_hash"], intent_b["canonical_proposal_hash"])
        self.assertEqual(lookup_a, lookup_b)
        immutable_fields = (
            "broker_native_instrument", "side", "order_type", "quantity",
            "entry_price", "stop_loss", "targets", "target_allocations_percent",
        )
        for field in immutable_fields:
            self.assertEqual(intent_a[field], intent_b[field])

    def test_nonce_salted_identity_differs_across_genuinely_independent_journals(self):
        # This is the contract's actual, intended design (Section 5.3): the
        # nonce is fixed only once persisted in ONE continuous store; two
        # journals that have never seen each other's data each perform a
        # genuine first creation and legitimately mint different nonces.
        proposal = make_proposal(salt="two-journal-nonce")
        intent_a = self.harness_a.service.build_order_intent(proposal)
        intent_b = self.harness_b.service.build_order_intent(proposal)

        self.assertNotEqual(intent_a["order_intent_id"], intent_b["order_intent_id"])
        self.assertNotEqual(intent_a["canonical_order_intent_hash"], intent_b["canonical_order_intent_hash"])
        self.assertNotEqual(intent_a["idempotency_key"], intent_b["idempotency_key"])

    def test_recomputed_lookup_key_matches_both_journals_independently(self):
        proposal = make_proposal(salt="two-journal-recompute")
        intent_a = self.harness_a.service.build_order_intent(proposal)
        intent_b = self.harness_b.service.build_order_intent(proposal)
        recomputed = med.execution_intent_lookup_key({
            "proposal_id": intent_a["proposal_id"],
            "account_fingerprint_hash": intent_a["account_fingerprint_hash"],
            "broker_native_instrument": intent_a["broker_native_instrument"],
            "side": intent_a["side"],
            "quantity": intent_a["quantity"],
            "strategy_id": intent_a["strategy_id"],
            "strategy_version": intent_a["strategy_version"],
            "risk_policy_hash": intent_a["risk_policy_hash"],
            "operating_mode": intent_a["operating_mode"],
            "authorization_identity": "LOCAL_OPERATOR",
        })
        lookup_a = [e for e in self.harness_a.journal.events if e["event_type"] == "ORDER_INTENT_CREATED"][0]["payload"]["lookup_key"]
        lookup_b = [e for e in self.harness_b.journal.events if e["event_type"] == "ORDER_INTENT_CREATED"][0]["payload"]["lookup_key"]
        self.assertEqual(recomputed, lookup_a)
        self.assertEqual(recomputed, lookup_b)

    def test_lookup_before_create_within_one_journal_reuses_not_recreates(self):
        # Contrasted directly against the cross-journal test above: within
        # ONE continuous store, a second build for the identical proposal
        # must resolve to the SAME nonce-salted identity, never a new one.
        proposal = make_proposal(salt="single-journal-reuse")
        first = self.harness_a.service.build_order_intent(proposal)
        second = self.harness_a.service.build_order_intent(proposal)
        self.assertEqual(first["order_intent_id"], second["order_intent_id"])
        self.assertEqual(first["canonical_order_intent_hash"], second["canonical_order_intent_hash"])


class OrderIntentDeterminismTests(HarnessTestCase):
    def test_same_proposal_produces_same_intent_id(self):
        proposal = make_proposal()
        intent1 = self.harness.service.build_order_intent(proposal)
        intent2 = self.harness.service.build_order_intent(proposal)
        self.assertEqual(intent1["order_intent_id"], intent2["order_intent_id"])

    def test_changed_proposal_changes_intent_identity(self):
        proposal1 = make_proposal(salt="a")
        proposal2 = make_proposal(salt="b")
        intent1 = self.harness.service.build_order_intent(proposal1)
        intent2 = self.harness.service.build_order_intent(proposal2)
        self.assertNotEqual(intent1["order_intent_id"], intent2["order_intent_id"])

    def test_intent_contains_no_credential_like_field(self):
        intent = self.build_intent()
        for key, value in intent.items():
            if isinstance(value, str):
                for forbidden in ("password", "secret_key", "token"):
                    self.assertNotIn(forbidden, value.lower())

    def test_lookup_before_create_reuses_existing_intent(self):
        proposal = make_proposal()
        first = self.harness.service.build_order_intent(proposal)
        second = self.harness.service.build_order_intent(proposal)
        self.assertEqual(first["order_intent_id"], second["order_intent_id"])
        reused_events = [e for e in self.harness.journal.events if e["event_type"] == "ORDER_INTENT_REUSED"]
        self.assertEqual(len(reused_events), 1)

    def test_repeated_submission_after_order_check_reuses_intent(self):
        intent = self.build_intent()
        self.harness.service.order_check(intent["order_intent_id"])
        again = self.harness.service.build_order_intent(make_proposal())
        self.assertEqual(again["order_intent_id"], intent["order_intent_id"])
        self.assertEqual(self.adapter_calls_count("order_check"), 1)

    def adapter_calls_count(self, operation):
        return len([c for c in self.harness.adapter.calls if c[0] == operation])

    def test_crash_after_persistence_recovers_created_intent(self):
        proposal = make_proposal()
        intent = self.harness.service.build_order_intent(proposal)
        # Simulate a process restart before any order_check happened.
        restarted = self.harness.restart()
        recovered = restarted.build_order_intent(proposal)
        self.assertEqual(recovered["order_intent_id"], intent["order_intent_id"])
        self.assertEqual(recovered["execution_status"], "CREATED")


class OrderCheckTests(HarnessTestCase):
    def test_check_calls_adapter_exactly_once(self):
        intent = self.build_intent()
        self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(self.count("order_check"), 1)

    def count(self, operation):
        return len([c for c in self.harness.adapter.calls if c[0] == operation])

    def test_check_never_calls_send(self):
        intent = self.build_intent()
        self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(self.count("order_send"), 0)

    def test_successful_check_does_not_auto_send(self):
        intent = self.build_intent()
        result = self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(result["intent"]["execution_status"], "CHECK_PASSED")
        self.assertEqual(self.count("order_send"), 0)

    def test_failed_check_prevents_send(self):
        intent = self.build_intent()
        self.harness.adapter.queue_check_result({"outcome": "FAILED", "retcode": 10006, "comment": "x", "checked_at_utc": "t"})
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "ORDER_CHECK_FAILED")
        with self.assertRaises(mes.ExecutionServiceError):
            self.harness.service.request_confirmation(intent["order_intent_id"])

    def test_malformed_check_response_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.queue_check_result({"not": "a valid result"})
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "BROKER_RESPONSE_MALFORMED")

    def test_stale_tick_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", tick_time_utc="2020-01-01T00:00:00.000000Z")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "TICK_STALE")

    def test_invalid_bid_ask_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", bid="1900.30", ask="1900.20")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "INVALID_BID_ASK")

    def test_excess_spread_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", bid="1899.00", ask="1905.00")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "SPREAD_EXCEEDS_LIMIT")

    def test_invalid_quantity_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", volume_minimum="1", volume_maximum="10")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "INVALID_QUANTITY")

    def test_quantity_step_mismatch_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", volume_minimum="0.005", volume_maximum="10", volume_step="0.02")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "QUANTITY_STEP_MISMATCH")

    def test_stop_level_violation_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", stops_level=10000)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "STOP_LEVEL_VIOLATION")

    def test_freeze_level_violation_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", stops_level=0, freeze_level=10000)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "FREEZE_LEVEL_VIOLATION")

    def test_symbol_unavailable_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.symbols.pop("XAUUSD")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "SYMBOL_UNAVAILABLE")

    def test_symbol_not_tradeable_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", tradeable=False, reason_code="SYMBOL_NOT_TRADEABLE")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "SYMBOL_NOT_TRADEABLE")

    def test_account_fingerprint_mismatch_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.account["login"] = 1
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "ACCOUNT_FINGERPRINT_MISMATCH")

    def test_live_account_rejected_in_demo_only_mode(self):
        intent = self.build_intent()
        self.harness.adapter.account["trade_mode"] = maa.ACCOUNT_TRADE_MODE_NAMES and 2
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "ACCOUNT_MODE_MISMATCH")

    def test_account_unavailable_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.account["available"] = False
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "ACCOUNT_UNAVAILABLE")

    def test_terminal_unavailable_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.terminal["connected"] = False
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "TERMINAL_UNAVAILABLE")

    def test_mt5_dependency_missing_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.dependency["available"] = False
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "MT5_DEPENDENCY_MISSING")

    def test_filling_mode_unavailable_fails_closed(self):
        intent = self.build_intent()
        self.harness.adapter.set_symbol("XAUUSD", filling_modes=("IOC",))
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "FILLING_MODE_UNAVAILABLE")

    def test_intent_expired_fails_before_adapter_call(self):
        intent = self.build_intent()
        self.harness.advance(3700)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "INTENT_EXPIRED")

    def test_intent_not_found(self):
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.order_check("exi_" + "9" * 32)
        self.assertEqual(ctx.exception.reason_code, "INTENT_NOT_FOUND")


class ManualConfirmationTests(HarnessTestCase):
    def _checked_intent(self):
        intent = self.build_intent()
        self.harness.service.order_check(intent["order_intent_id"])
        return intent

    def test_confirmation_required_before_send(self):
        intent = self._checked_intent()
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent["order_intent_id"], "anything")
        self.assertEqual(ctx.exception.reason_code, "CONFIRMATION_REQUIRED")

    def test_wrong_confirmation_rejected(self):
        intent = self._checked_intent()
        self.harness.service.request_confirmation(intent["order_intent_id"])
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent["order_intent_id"], "WRONGCODE")
        self.assertEqual(ctx.exception.reason_code, "CONFIRMATION_MISMATCH")

    def test_confirmation_for_another_intent_rejected(self):
        intent1 = self._checked_intent()
        challenge1 = self.harness.service.request_confirmation(intent1["order_intent_id"])
        intent2 = self.build_intent(salt="other")
        self.harness.service.order_check(intent2["order_intent_id"])
        self.harness.service.request_confirmation(intent2["order_intent_id"])
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent2["order_intent_id"], challenge1["challenge_code"])
        self.assertEqual(ctx.exception.reason_code, "CONFIRMATION_WRONG_INTENT")

    def test_expired_confirmation_rejected(self):
        intent = self._checked_intent()
        challenge = self.harness.service.request_confirmation(intent["order_intent_id"])
        self.harness.advance(mes.CONFIRMATION_LIFETIME_SECONDS + 1)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent["order_intent_id"], challenge["challenge_code"])
        self.assertEqual(ctx.exception.reason_code, "CONFIRMATION_EXPIRED")

    def test_reused_confirmation_rejected(self):
        intent = self._checked_intent()
        challenge = self.harness.service.request_confirmation(intent["order_intent_id"])
        self.harness.service.confirm_and_send(intent["order_intent_id"], challenge["challenge_code"])
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent["order_intent_id"], challenge["challenge_code"])
        self.assertEqual(ctx.exception.reason_code, "CONFIRMATION_ALREADY_CONSUMED")

    def test_confirmation_cannot_come_from_non_local_channel(self):
        intent = self._checked_intent()
        challenge = self.harness.service.request_confirmation(intent["order_intent_id"])
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(
                intent["order_intent_id"], challenge["challenge_code"], actor_channel="HTTP",
            )
        self.assertEqual(ctx.exception.reason_code, "CONFIRMATION_CHANNEL_NOT_LOCAL")

    def test_confirmation_requires_check_passed_first(self):
        intent = self.build_intent()
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.request_confirmation(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "ORDER_CHECK_NOT_YET_PERFORMED")

    def test_stale_check_blocks_confirmation(self):
        intent = self._checked_intent()
        self.harness.advance(mes.CHECK_FRESHNESS_SECONDS + 1)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.request_confirmation(intent["order_intent_id"])
        self.assertEqual(ctx.exception.reason_code, "ORDER_CHECK_STALE")


class OrderSendTests(HarnessTestCase):
    def _confirmed(self):
        intent = self.build_intent()
        self.harness.service.order_check(intent["order_intent_id"])
        challenge = self.harness.service.request_confirmation(intent["order_intent_id"])
        return intent, challenge["challenge_code"]

    def count(self, operation):
        return len([c for c in self.harness.adapter.calls if c[0] == operation])

    def test_send_calls_adapter_at_most_once(self):
        intent, code = self._confirmed()
        self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(self.count("order_send"), 1)

    def test_successful_send_fills(self):
        intent, code = self._confirmed()
        result = self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(result["intent"]["execution_status"], "FILLED")

    def test_duplicate_send_blocked(self):
        intent, code = self._confirmed()
        self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(ctx.exception.reason_code, "CONFIRMATION_ALREADY_CONSUMED")
        self.assertEqual(self.count("order_send"), 1)

    def test_duplicate_send_remains_blocked_after_restart(self):
        intent, code = self._confirmed()
        self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        restarted = self.harness.restart()
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            restarted.confirm_and_send(intent["order_intent_id"], code)
        self.assertIn(ctx.exception.reason_code, ("CONFIRMATION_ALREADY_CONSUMED", "INTENT_ALREADY_TERMINAL"))
        self.assertEqual(self.count("order_send"), 1)

    def test_unknown_result_prevents_retry(self):
        intent, code = self._confirmed()
        self.harness.adapter.queue_send_result({"outcome": "UNCERTAIN", "comment": "timeout"})
        result = self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(result["intent"]["execution_status"], "FROZEN_PENDING_RECONCILIATION")
        # No automatic retry: a further attempt is blocked without ever
        # calling order_send again.
        with self.assertRaises(mes.ExecutionServiceError):
            self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(self.count("order_send"), 1)

    def test_timeout_prevents_automatic_retry(self):
        intent, code = self._confirmed()
        self.harness.adapter.queue_send_result({"outcome": "MALFORMED", "comment": "timeout"})
        self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(self.count("order_send"), 1)

    def test_broker_rejection_persisted_accurately(self):
        intent, code = self._confirmed()
        self.harness.adapter.queue_send_result({"outcome": "REJECTED", "comment": "no money", "retcode": 10019})
        result = self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(result["intent"]["execution_status"], "REJECTED")

    def test_broker_success_normalized_accurately(self):
        intent, code = self._confirmed()
        result = self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(result["send_result"]["ticket"], 555001)

    def test_broker_result_volume_mismatch_fails_closed(self):
        intent, code = self._confirmed()
        self.harness.adapter.queue_send_result({
            "outcome": "FILLED", "retcode": 10009, "ticket": 1, "deal": 2,
            "position": 1, "volume_filled": "99.0", "comment": "x", "sent_at_utc": "t",
        })
        result = self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(result["intent"]["execution_status"], "FROZEN_PENDING_RECONCILIATION")

    def test_broker_result_missing_volume_fails_closed(self):
        intent, code = self._confirmed()
        self.harness.adapter.queue_send_result({
            "outcome": "FILLED", "retcode": 10009, "ticket": 1, "deal": 2,
            "position": 1, "volume_filled": None, "comment": "x", "sent_at_utc": "t",
        })
        result = self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(result["intent"]["execution_status"], "FROZEN_PENDING_RECONCILIATION")

    def test_expired_proposal_blocks_send(self):
        # A short-lived proposal that expires well within the (longer)
        # confirmation window, so PROPOSAL_EXPIRED is reached specifically
        # rather than CONFIRMATION_EXPIRED firing first.
        proposal = make_proposal(expires_at_utc="2026-08-01T12:00:30.000000Z")
        intent = self.harness.service.build_order_intent(proposal)
        self.harness.service.order_check(intent["order_intent_id"])
        challenge = self.harness.service.request_confirmation(intent["order_intent_id"])
        self.harness.advance(60)
        self.assertLess(60, mes.CONFIRMATION_LIFETIME_SECONDS)
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent["order_intent_id"], challenge["challenge_code"])
        self.assertEqual(ctx.exception.reason_code, "PROPOSAL_EXPIRED")

    def test_account_fingerprint_changed_before_send_blocks(self):
        intent, code = self._confirmed()
        self.harness.adapter.account["login"] = 1
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(ctx.exception.reason_code, "ACCOUNT_FINGERPRINT_MISMATCH")

    def test_excess_spread_before_send_blocks(self):
        intent, code = self._confirmed()
        self.harness.adapter.set_symbol("XAUUSD", bid="1899.00", ask="1905.00")
        with self.assertRaises(mes.ExecutionServiceError) as ctx:
            self.harness.service.confirm_and_send(intent["order_intent_id"], code)
        self.assertEqual(ctx.exception.reason_code, "SPREAD_EXCEEDS_LIMIT")


class SecretHandlingTests(HarnessTestCase):
    def test_journal_never_contains_login_number(self):
        intent, code = self.build_and_send()
        for event in self.harness.journal.events:
            self.assertNotIn(str(self.harness.fingerprint.login), str(event))

    def build_and_send(self):
        intent = self.build_intent()
        self.harness.service.order_check(intent["order_intent_id"])
        challenge = self.harness.service.request_confirmation(intent["order_intent_id"])
        self.harness.service.confirm_and_send(intent["order_intent_id"], challenge["challenge_code"])
        return intent, challenge["challenge_code"]

    def test_account_status_document_redacts_login(self):
        document = self.harness.service.account_status_document()
        self.assertNotIn("login", document)
        self.assertIn("login_redacted", document)

    def test_no_password_field_anywhere_in_status_documents(self):
        for document in (
            self.harness.service.status_document(),
            self.harness.service.account_status_document(),
            self.harness.service.terminal_status_document(),
            self.harness.service.journal_document(),
        ):
            self.assertNotIn("password", str(document).lower())


if __name__ == "__main__":
    unittest.main()
