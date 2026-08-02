"""Tests for market_intelligence_data.py — TRL-R2-010 Market Intelligence
V0 (TRL CORTEX V0) schemas, identities, scoring, decision engine, and
lattice/preview geometry. Pure data-layer tests: no journal, no
ModeService, no I/O.
"""

from decimal import Decimal
import unittest

from trading_lab_app import market_intelligence_data as mid
from trading_lab_app.timeline_data import validate_utc_timestamp

import mi_test_support as support


class SnapshotSchemaTests(unittest.TestCase):
    def test_valid_snapshot_round_trips(self):
        clean = mid.validate_snapshot_input(support.snapshot_input())
        record = mid.build_snapshot_record(clean)
        self.assertTrue(record["snapshot_id"].startswith("mkt_"))
        self.assertEqual(len(record["snapshot_id"]), 36)
        revalidated = mid.validate_snapshot_record(record)
        self.assertEqual(revalidated, record)

    def test_unknown_field_rejected(self):
        payload = support.snapshot_input()
        payload["unexpected"] = "x"
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_snapshot_input(payload)

    def test_missing_field_rejected(self):
        payload = support.snapshot_input()
        del payload["session"]
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_snapshot_input(payload)

    def test_wrong_type_rejected(self):
        payload = support.snapshot_input(open=2400.0)
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_snapshot_input(payload)

    def test_boolean_rejected_as_number(self):
        payload = support.snapshot_input(spread=True)
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_snapshot_input(payload)

    def test_non_finite_rejected(self):
        payload = support.snapshot_input(volatility_measure="Infinity")
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_snapshot_input(payload)

    def test_ungoverned_session_rejected(self):
        payload = support.snapshot_input(session="TOKYO")
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_snapshot_input(payload)

    def test_open_outside_low_high_rejected(self):
        payload = support.snapshot_input(open="2500.00")
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_snapshot_input(payload)

    def test_snapshot_id_deterministic_across_calls(self):
        clean = mid.validate_snapshot_input(support.snapshot_input())
        first = mid.snapshot_id_for(clean)
        second = mid.snapshot_id_for(dict(clean))
        self.assertEqual(first, second)

    def test_snapshot_mid_price(self):
        record = mid.build_snapshot_record(mid.validate_snapshot_input(support.snapshot_input()))
        self.assertEqual(mid.snapshot_mid_price(record), Decimal("2402.5000"))


class InstrumentTimeframeAllowlistTests(unittest.TestCase):
    def test_canonical_instruments_and_timeframes(self):
        self.assertEqual(mid.INSTRUMENTS, ("XAUUSD", "NAS100", "EURUSD", "GBPUSD", "USDJPY"))
        self.assertEqual(mid.TIMEFRAMES, ("M5", "M15", "H1", "H4", "D1"))
        for instrument in mid.INSTRUMENTS:
            for timeframe in mid.TIMEFRAMES:
                mid.check_instrument_and_timeframe(instrument, timeframe)

    def test_unsupported_instrument_alias_fails_closed(self):
        with self.assertRaises(mid.MarketIntelligenceValidationError) as ctx:
            mid.check_instrument_and_timeframe("GOLD", "H1")
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INSTRUMENT_NOT_ALLOWED")

    def test_no_silent_normalization_of_alias(self):
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.check_instrument_and_timeframe("XAU/USD", "H1")

    def test_unsupported_timeframe_fails_closed(self):
        with self.assertRaises(mid.MarketIntelligenceValidationError) as ctx:
            mid.check_instrument_and_timeframe("XAUUSD", "M1")
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_TIMEFRAME_NOT_ALLOWED")


class EvidenceSchemaTests(unittest.TestCase):
    def _snapshot(self):
        return mid.build_snapshot_record(mid.validate_snapshot_input(support.snapshot_input()))

    def test_evidence_round_trips_and_has_no_opportunity_id_field(self):
        snapshot = self._snapshot()
        clean = mid.validate_evidence_input(support.evidence_input("MARKET_STRUCTURE", "SUPPORTS", "0.9000", "0.9000"))
        record = mid.build_evidence_record(snapshot["snapshot_id"], snapshot["canonical_snapshot_hash"], "BUY", clean)
        self.assertNotIn("opportunity_id", record)
        self.assertEqual(set(record), set(mid.EVIDENCE_FIELDS))
        self.assertEqual(mid.validate_evidence_record(record), record)

    def test_evidence_id_deterministic_and_no_nonce(self):
        snapshot = self._snapshot()
        clean = mid.validate_evidence_input(support.evidence_input("TREND", "SUPPORTS", "0.9000", "0.9000"))
        first = mid.build_evidence_record(snapshot["snapshot_id"], snapshot["canonical_snapshot_hash"], "BUY", clean)
        second = mid.build_evidence_record(snapshot["snapshot_id"], snapshot["canonical_snapshot_hash"], "BUY", dict(clean))
        self.assertEqual(first["evidence_id"], second["evidence_id"])
        self.assertEqual(first["canonical_evidence_hash"], second["canonical_evidence_hash"])

    def test_expires_before_observed_rejected(self):
        payload = support.evidence_input("TREND", "SUPPORTS", "0.9000", "0.9000", expires="2020-01-01T00:00:00.000000Z")
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_evidence_input(payload)

    def test_strength_out_of_bounds_rejected(self):
        payload = support.evidence_input("TREND", "SUPPORTS", "1.5000", "0.9000")
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_evidence_input(payload)

    def test_strength_boolean_rejected(self):
        payload = support.evidence_input("TREND", "SUPPORTS", True, "0.9000")
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_evidence_input(payload)

    def test_more_than_four_decimal_places_rejected(self):
        payload = support.evidence_input("TREND", "SUPPORTS", "0.90001", "0.9000")
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_evidence_input(payload)

    def test_ungoverned_category_rejected(self):
        payload = support.evidence_input("UNKNOWN_CATEGORY", "SUPPORTS", "0.9000", "0.9000")
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_evidence_input(payload)

    def test_hash_tamper_detected(self):
        snapshot = self._snapshot()
        clean = mid.validate_evidence_input(support.evidence_input("TREND", "SUPPORTS", "0.9000", "0.9000"))
        record = mid.build_evidence_record(snapshot["snapshot_id"], snapshot["canonical_snapshot_hash"], "BUY", clean)
        tampered = dict(record)
        tampered["normalized_strength"] = "0.1000"
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_evidence_record(tampered)


class EvidenceCompletenessTests(unittest.TestCase):
    def _now(self):
        return validate_utc_timestamp("2026-08-01T12:00:00.000000Z")

    def test_exactly_one_per_category_passes(self):
        inputs = [mid.validate_evidence_input(item) for item in support.strong_evidence_inputs()]
        by_category = mid.check_evidence_completeness(inputs, self._now())
        self.assertEqual(set(by_category), set(mid.EVIDENCE_CATEGORIES))

    def test_missing_category_fails_closed(self):
        inputs = [mid.validate_evidence_input(item) for item in support.strong_evidence_inputs()[:-1]]
        with self.assertRaises(mid.MarketIntelligenceValidationError) as ctx:
            mid.check_evidence_completeness(inputs, self._now())
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_MISSING")

    def test_duplicate_category_fails_closed(self):
        raw = support.strong_evidence_inputs()
        raw.append(dict(raw[0]))  # all eleven categories still present, plus one duplicate
        inputs = [mid.validate_evidence_input(item) for item in raw]
        with self.assertRaises(mid.MarketIntelligenceValidationError) as ctx:
            mid.check_evidence_completeness(inputs, self._now())
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_DUPLICATED")

    def test_individually_expired_fails_closed_distinct_reason(self):
        raw = support.strong_evidence_inputs()
        raw[0] = support.evidence_input("MARKET_STRUCTURE", "SUPPORTS", "0.9000", "0.9000", expires="2026-08-01T11:00:00.000000Z")
        inputs = [mid.validate_evidence_input(item) for item in raw]
        with self.assertRaises(mid.MarketIntelligenceValidationError) as ctx:
            mid.check_evidence_completeness(inputs, self._now())
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_EVIDENCE_EXPIRED")


class ScoringTests(unittest.TestCase):
    def _evidence_by_category(self, overrides=None):
        snapshot = mid.build_snapshot_record(mid.validate_snapshot_input(support.snapshot_input()))
        raw = support.strong_evidence_inputs()
        if overrides:
            by_cat = {item["category"]: item for item in raw}
            by_cat.update(overrides)
            raw = list(by_cat.values())
        inputs = [mid.validate_evidence_input(item) for item in raw]
        by_category = mid.check_evidence_completeness(inputs, validate_utc_timestamp("2026-08-01T12:00:00.000000Z"))
        return {
            category: mid.build_evidence_record(snapshot["snapshot_id"], snapshot["canonical_snapshot_hash"], "BUY", item)
            for category, item in by_category.items()
        }

    def test_effective_evidence_score_formula(self):
        item = {"normalized_strength": "0.9000", "confidence": "0.9500"}
        self.assertEqual(mid.effective_evidence_score(item), Decimal("0.8550"))

    def test_round_half_even_quantize(self):
        # 0.12345 -> banker's rounding at the 4th decimal (5 rounds to even digit 4)
        self.assertEqual(mid.quantize_4("0.12345"), Decimal("0.1234"))
        self.assertEqual(mid.quantize_4("0.12355"), Decimal("0.1236"))

    def test_negative_zero_canonicalizes_to_zero(self):
        self.assertEqual(mid.quantize_4(Decimal("-0.00001")), Decimal("0.0000"))

    def test_supporting_score_fixed_denominator_five(self):
        evidence = self._evidence_by_category()
        scores = mid.compute_scores(evidence)
        # three directional SUPPORTS at 0.9000*0.9500=0.8550 each (MARKET_STRUCTURE/TREND/MOMENTUM),
        # MULTI_TIMEFRAME_ALIGNMENT also SUPPORTS at 0.8550 -> sum 3.42 / 5 = 0.6840
        self.assertEqual(scores["supporting_score"], "0.6840")

    def test_contradiction_score_denominator_unaffected_by_neutral_items(self):
        evidence = self._evidence_by_category()
        scores = mid.compute_scores(evidence)
        self.assertEqual(scores["contradiction_score"], "0.0000")

    def test_uncertainty_score_denominator_eleven(self):
        evidence = self._evidence_by_category()
        scores = mid.compute_scores(evidence)
        confidences = [Decimal(item["confidence"]) for item in evidence.values()]
        expected = mid.quantize_4(sum((Decimal("1.0000") - c for c in confidences), Decimal("0")) / Decimal("11"))
        self.assertEqual(scores["uncertainty_score"], format(expected, "f"))

    def test_severity_categories_never_mixed_into_support_or_contradiction(self):
        evidence = self._evidence_by_category(overrides={
            "EVENT_RISK": support.evidence_input("EVENT_RISK", "SUPPORTS", "0.9999", "0.9999"),
        })
        scores = mid.compute_scores(evidence)
        # EVENT_RISK is not one of the five directional categories, so
        # marking it SUPPORTS must not move supporting_score at all.
        self.assertEqual(scores["supporting_score"], "0.6840")

    def test_partition_evidence_by_direction_restricted_to_five_categories(self):
        evidence = self._evidence_by_category()
        supporting, opposing = mid.partition_evidence_by_direction(evidence)
        self.assertEqual(len(supporting), 4)
        self.assertEqual(opposing, [])


class OpportunitySchemaTests(unittest.TestCase):
    def _opportunity(self):
        snapshot = mid.build_snapshot_record(mid.validate_snapshot_input(support.snapshot_input()))
        inputs = [mid.validate_evidence_input(item) for item in support.strong_evidence_inputs()]
        by_category = mid.check_evidence_completeness(inputs, validate_utc_timestamp("2026-08-01T12:00:00.000000Z"))
        evidence = {
            category: mid.build_evidence_record(snapshot["snapshot_id"], snapshot["canonical_snapshot_hash"], "BUY", item)
            for category, item in by_category.items()
        }
        concept = mid.validate_opportunity_concept_input({
            "market_regime": "TRENDING", "entry_concept": "buy dip", "invalidation_concept": "break structure",
            "stop_concept": "below swing low", "ordered_target_concepts": ["t1", "t2", "t3"],
        })
        return mid.build_opportunity_record(
            snapshot_record=snapshot, proposed_side="BUY", strategy_id="CORTEX-V0-HEURISTIC",
            strategy_version="1.0.0", concept_input=concept, evidence_by_category=evidence,
            activation_satisfied=True, invalidation_satisfied=False,
            created_at_utc="2026-08-01T12:00:00.000000Z", expiry_utc="2026-08-02T12:00:00.000000Z",
        ), evidence

    def test_opportunity_round_trips(self):
        opportunity, _evidence = self._opportunity()
        self.assertTrue(opportunity["opportunity_id"].startswith("opp_"))
        self.assertEqual(len(opportunity["evidence_ids"]), 11)
        revalidated = mid.validate_opportunity_record(opportunity)
        self.assertEqual(revalidated["opportunity_id"], opportunity["opportunity_id"])

    def test_opportunity_id_excludes_created_at_and_decision_fields(self):
        opportunity, evidence = self._opportunity()
        concept = mid.validate_opportunity_concept_input({
            "market_regime": "TRENDING", "entry_concept": "buy dip", "invalidation_concept": "break structure",
            "stop_concept": "below swing low", "ordered_target_concepts": ["t1", "t2", "t3"],
        })
        snapshot = mid.build_snapshot_record(mid.validate_snapshot_input(support.snapshot_input()))
        other = mid.build_opportunity_record(
            snapshot_record=snapshot, proposed_side="BUY", strategy_id="CORTEX-V0-HEURISTIC",
            strategy_version="1.0.0", concept_input=concept, evidence_by_category=evidence,
            activation_satisfied=True, invalidation_satisfied=False,
            created_at_utc="2030-01-01T00:00:00.000000Z", expiry_utc="2030-01-02T00:00:00.000000Z",
        )
        self.assertEqual(opportunity["opportunity_id"], other["opportunity_id"])
        self.assertEqual(opportunity["canonical_opportunity_hash"], other["canonical_opportunity_hash"])

    def test_ordered_target_concepts_bounds(self):
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_opportunity_concept_input({
                "market_regime": "TRENDING", "entry_concept": "e", "invalidation_concept": "i",
                "stop_concept": "s", "ordered_target_concepts": ["only-one"],
            })


class VirtualCandidateGeometryTests(unittest.TestCase):
    def test_buy_geometry_valid(self):
        self.assertTrue(mid.candidate_geometry_valid("BUY", "2401.00", "2396.00", ["2410.00", "2415.00"]))

    def test_buy_geometry_stop_above_entry_invalid(self):
        self.assertFalse(mid.candidate_geometry_valid("BUY", "2401.00", "2405.00", ["2410.00", "2415.00"]))

    def test_buy_geometry_target_not_increasing_invalid(self):
        self.assertFalse(mid.candidate_geometry_valid("BUY", "2401.00", "2396.00", ["2415.00", "2410.00"]))

    def test_sell_geometry_valid(self):
        self.assertTrue(mid.candidate_geometry_valid("SELL", "2401.00", "2406.00", ["2395.00", "2390.00"]))

    def test_sell_geometry_stop_below_entry_invalid(self):
        self.assertFalse(mid.candidate_geometry_valid("SELL", "2401.00", "2396.00", ["2395.00", "2390.00"]))

    def test_sell_geometry_target_not_decreasing_invalid(self):
        self.assertFalse(mid.candidate_geometry_valid("SELL", "2401.00", "2406.00", ["2390.00", "2395.00"]))

    def test_allocation_sum_must_be_exactly_100(self):
        payload = support.candidate_input(target_allocations=["40.0000", "30.0000", "29.9999"])
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_virtual_candidate_input(payload)

    def test_target_count_bounds(self):
        payload = support.candidate_input(target_prices=["2410.00"], target_allocations=["100.0000"])
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.validate_virtual_candidate_input(payload)

    def test_reward_risk_and_distance_to_market(self):
        candidate = mid.validate_virtual_candidate_input(support.candidate_input())
        rr, dist = mid.compute_reward_risk(
            candidate["entry_trigger"], candidate["stop_price"], candidate["target_prices"],
            candidate["target_allocations"], Decimal("2402.5000"),
        )
        self.assertEqual(rr, Decimal("2.7000"))
        self.assertEqual(dist, Decimal("1.5000"))


class VirtualOpportunityStateAndRankingTests(unittest.TestCase):
    def test_state_derivation_order(self):
        self.assertEqual(mid.derive_virtual_state(expired=True, invalidation_satisfied=True, geometry_valid=False, activation_satisfied=False), "EXPIRED")
        self.assertEqual(mid.derive_virtual_state(expired=False, invalidation_satisfied=True, geometry_valid=False, activation_satisfied=False), "INVALIDATED")
        self.assertEqual(mid.derive_virtual_state(expired=False, invalidation_satisfied=False, geometry_valid=False, activation_satisfied=True), "REJECTED")
        self.assertEqual(mid.derive_virtual_state(expired=False, invalidation_satisfied=False, geometry_valid=True, activation_satisfied=False), "WATCHING")
        self.assertEqual(mid.derive_virtual_state(expired=False, invalidation_satisfied=False, geometry_valid=True, activation_satisfied=True), "ACTIVATED")

    def test_ranking_three_tier_ordering(self):
        candidates = [
            {"virtual_opportunity_id": "vop_b", "expected_reward_risk_ratio": Decimal("2.0000"), "distance_to_market": Decimal("1.0000"), "state": "ACTIVATED"},
            {"virtual_opportunity_id": "vop_a", "expected_reward_risk_ratio": Decimal("2.0000"), "distance_to_market": Decimal("1.0000"), "state": "ACTIVATED"},
            {"virtual_opportunity_id": "vop_c", "expected_reward_risk_ratio": Decimal("3.0000"), "distance_to_market": Decimal("5.0000"), "state": "ACTIVATED"},
            {"virtual_opportunity_id": "vop_d", "expected_reward_risk_ratio": Decimal("2.0000"), "distance_to_market": Decimal("0.5000"), "state": "ACTIVATED"},
        ]
        ranks = mid.rank_virtual_opportunities(candidates)
        # highest reward/risk wins (vop_c), then lowest distance among ties
        # (vop_d before vop_a/vop_b), then ascending ID as the final tie-break.
        self.assertEqual(ranks["vop_c"], 1)
        self.assertEqual(ranks["vop_d"], 2)
        self.assertEqual(ranks["vop_a"], 3)
        self.assertEqual(ranks["vop_b"], 4)

    def test_invalidated_and_expired_excluded_from_primary_ranking_but_still_ranked(self):
        candidates = [
            {"virtual_opportunity_id": "vop_a", "expected_reward_risk_ratio": Decimal("5.0000"), "distance_to_market": Decimal("0.1000"), "state": "INVALIDATED"},
            {"virtual_opportunity_id": "vop_b", "expected_reward_risk_ratio": Decimal("1.0000"), "distance_to_market": Decimal("1.0000"), "state": "ACTIVATED"},
        ]
        ranks = mid.rank_virtual_opportunities(candidates)
        self.assertEqual(ranks["vop_b"], 1)
        self.assertEqual(ranks["vop_a"], 2)

    def test_virtual_opportunity_id_does_not_depend_on_rank(self):
        opportunity_id, hash_ = "opp_" + "a" * 32, "b" * 64
        candidate = mid.validate_virtual_candidate_input(support.candidate_input())
        built = mid.build_virtual_opportunity_record(
            opportunity_id=opportunity_id, canonical_opportunity_hash=hash_,
            proposed_side="BUY", validated_candidate=candidate, mid_price=Decimal("2402.5000"),
        )
        low_rank = mid.finalize_virtual_opportunity_record(built, 1, "ACTIVATED")
        high_rank = mid.finalize_virtual_opportunity_record(built, 6, "ACTIVATED")
        self.assertEqual(low_rank["virtual_opportunity_id"], high_rank["virtual_opportunity_id"])
        self.assertNotEqual(low_rank["canonical_virtual_opportunity_hash"], high_rank["canonical_virtual_opportunity_hash"])

    def test_non_executable_always_true(self):
        opportunity_id, hash_ = "opp_" + "a" * 32, "b" * 64
        candidate = mid.validate_virtual_candidate_input(support.candidate_input())
        built = mid.build_virtual_opportunity_record(
            opportunity_id=opportunity_id, canonical_opportunity_hash=hash_,
            proposed_side="BUY", validated_candidate=candidate, mid_price=Decimal("2402.5000"),
        )
        record = mid.finalize_virtual_opportunity_record(built, 1, "ACTIVATED")
        self.assertIs(record["non_executable"], True)


class DecisionEngineTests(unittest.TestCase):
    def _base_scores(self):
        return {
            "supporting_score": "0.7000", "contradiction_score": "0.1000", "uncertainty_score": "0.1000",
            "data_quality_score": "0.9000", "estimated_cost_score": "0.1000",
            "event_risk_score": "0.1000", "risk_exposure_score": "0.1000",
        }

    def _evaluate(self, **overrides):
        scores = self._base_scores()
        scores.update({key: overrides.pop(key) for key in list(overrides) if key in scores})
        kwargs = {
            "strategy_gate_passed": True, "strategy_gate_reason": None,
            "activation_satisfied": True, "invalidation_satisfied": False,
            "opportunity_expired": False, "all_candidates_rejected": False,
        }
        kwargs.update(overrides)
        return mid.evaluate_decision(**scores, **kwargs)

    def test_trade_candidate_all_gates_pass(self):
        status, reasons = self._evaluate()
        self.assertEqual(status, "TRADE_CANDIDATE")
        self.assertEqual(reasons, ["MARKET_INTELLIGENCE_ALL_GATES_PASSED"])

    def test_expired_status(self):
        status, reasons = self._evaluate(opportunity_expired=True)
        self.assertEqual(status, "EXPIRED")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_OPPORTUNITY_EXPIRED")

    def test_blocked_data_quality_below_minimum(self):
        status, reasons = self._evaluate(data_quality_score="0.5000")
        self.assertEqual(status, "BLOCKED")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_DATA_QUALITY_BELOW_MINIMUM")

    def test_blocked_hard_event_risk(self):
        status, reasons = self._evaluate(event_risk_score="0.9500")
        self.assertEqual(status, "BLOCKED")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_HARD_EVENT_RISK_BLOCK")

    def test_blocked_hard_risk_exposure(self):
        status, reasons = self._evaluate(risk_exposure_score="0.9500")
        self.assertEqual(status, "BLOCKED")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_HARD_RISK_EXPOSURE_BLOCK")

    def test_blocked_strategy_gate_sma(self):
        status, reason = mid.strategy_gate_status("SMA-001", False, True)
        self.assertFalse(status)
        self.assertEqual(reason, "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED")
        outcome, reasons = self._evaluate(strategy_gate_passed=False, strategy_gate_reason=reason)
        self.assertEqual(outcome, "BLOCKED")
        self.assertEqual(reasons[0], "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED")

    def test_blocked_strategy_gate_fib(self):
        status, reason = mid.strategy_gate_status("FIB-001", True, False)
        self.assertFalse(status)
        self.assertEqual(reason, "STRATEGY_PARAMETERS_NOT_APPROVED")

    def test_generic_cortex_not_globally_blocked(self):
        status, _reason = mid.strategy_gate_status("CORTEX-V0-HEURISTIC", False, False)
        self.assertTrue(status)

    def test_reject_invalidation_already_occurred(self):
        status, reasons = self._evaluate(invalidation_satisfied=True)
        self.assertEqual(status, "REJECT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_INVALIDATION_ALREADY_OCCURRED")

    def test_reject_structurally_inconsistent(self):
        status, reasons = self._evaluate(all_candidates_rejected=True)
        self.assertEqual(status, "REJECT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_STRUCTURALLY_INCONSISTENT")

    def test_reject_contradiction(self):
        status, reasons = self._evaluate(contradiction_score="0.6500")
        self.assertEqual(status, "REJECT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_CONTRADICTION_REJECTED")

    def test_reject_transaction_cost_destroys_edge(self):
        status, reasons = self._evaluate(estimated_cost_score="0.8000")
        self.assertEqual(status, "REJECT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_TRANSACTION_COST_DESTROYS_EDGE")

    def test_wait_trigger_not_active(self):
        status, reasons = self._evaluate(activation_satisfied=False)
        self.assertEqual(status, "WAIT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_TRIGGER_NOT_ACTIVE")

    def test_wait_event_risk(self):
        status, reasons = self._evaluate(event_risk_score="0.6500")
        self.assertEqual(status, "WAIT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_EVENT_RISK_WAIT")

    def test_wait_risk_exposure(self):
        status, reasons = self._evaluate(risk_exposure_score="0.6500")
        self.assertEqual(status, "WAIT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_RISK_EXPOSURE_WAIT")

    def test_wait_uncertainty_above_threshold(self):
        status, reasons = self._evaluate(uncertainty_score="0.5000")
        self.assertEqual(status, "WAIT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_UNCERTAINTY_ABOVE_THRESHOLD")

    def test_wait_support_below_threshold(self):
        status, reasons = self._evaluate(supporting_score="0.5000")
        self.assertEqual(status, "WAIT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_SUPPORT_BELOW_THRESHOLD")

    def test_wait_contradiction_above_threshold(self):
        status, reasons = self._evaluate(contradiction_score="0.4000")
        self.assertEqual(status, "WAIT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_CONTRADICTION_ABOVE_THRESHOLD")

    def test_wait_transaction_cost_marginal(self):
        status, reasons = self._evaluate(estimated_cost_score="0.3500")
        self.assertEqual(status, "WAIT")
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_TRANSACTION_COST_MARGINAL")

    def test_intelligence_scoring_not_validated_never_blocks_classification(self):
        # There is no code path in evaluate_decision that references
        # INTELLIGENCE_SCORING_NOT_VALIDATED at all — it is a display/
        # promotion blocker only (Section 19.4), never a decision gate.
        status, reasons = self._evaluate()
        self.assertNotIn("INTELLIGENCE_SCORING_NOT_VALIDATED", reasons)
        self.assertEqual(status, "TRADE_CANDIDATE")

    def test_full_reason_code_audit_list_records_every_true_condition(self):
        status, reasons = self._evaluate(event_risk_score="0.6500", risk_exposure_score="0.6500")
        self.assertEqual(status, "WAIT")
        self.assertIn("MARKET_INTELLIGENCE_EVENT_RISK_WAIT", reasons)
        self.assertIn("MARKET_INTELLIGENCE_RISK_EXPOSURE_WAIT", reasons)
        self.assertEqual(reasons[0], "MARKET_INTELLIGENCE_EVENT_RISK_WAIT")


class PreviewQuantityConservationTests(unittest.TestCase):
    def test_exact_conservation(self):
        quantities = mid.compute_preview_quantities(Decimal("1.00000000"), ["40.0000", "30.0000", "30.0000"])
        self.assertEqual(quantities, ["0.4", "0.3", "0.3"])

    def test_null_quantity_produces_null_children(self):
        self.assertIsNone(mid.compute_preview_quantities(None, ["40.0000", "30.0000", "30.0000"]))

    def test_not_exactly_representable_fails_closed(self):
        with self.assertRaises(mid.MarketIntelligenceValidationError) as ctx:
            mid.compute_preview_quantities(Decimal("1.23456789"), ["11.1111", "11.1111", "77.7778"])
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE")

    def test_no_zero_child(self):
        with self.assertRaises(mid.MarketIntelligenceValidationError):
            mid.compute_preview_quantities(Decimal("0.00000000"), ["50.0000", "50.0000"])

    def test_preview_record_execution_handoff_blocker_always_present(self):
        opportunity = {"opportunity_id": "opp_" + "a" * 32, "canonical_opportunity_hash": "b" * 64, "instrument": "XAUUSD", "proposed_side": "BUY"}
        candidate = mid.validate_virtual_candidate_input(support.candidate_input())
        built = mid.build_virtual_opportunity_record(
            opportunity_id=opportunity["opportunity_id"], canonical_opportunity_hash=opportunity["canonical_opportunity_hash"],
            proposed_side="BUY", validated_candidate=candidate, mid_price=Decimal("2402.5000"),
        )
        vop = mid.finalize_virtual_opportunity_record(built, 1, "SELECTED_FOR_PREVIEW")
        preview = mid.build_preview_record(
            opportunity=opportunity, selected_virtual_opportunity=vop, candidate_input=candidate,
            created_at_utc="2026-08-01T12:00:00.000000Z",
        )
        self.assertEqual(preview["execution_handoff_status"], "EXECUTION_HANDOFF_NOT_APPROVED")
        self.assertIs(preview["non_executable"], True)
        self.assertEqual(len(preview["ordered_target_prices"]), 3)


if __name__ == "__main__":
    unittest.main()
