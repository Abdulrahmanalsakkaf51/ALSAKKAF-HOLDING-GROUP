"""Offline deterministic contract tests for TRL-R2-005."""

from copy import deepcopy
from decimal import Decimal
import http.client
import io
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest import mock


BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from trading_lab_app import server  # noqa: E402
from trading_lab_app.paper_data import (  # noqa: E402
    INSTRUMENT_METADATA_SCHEMA,
    MARKET_OBSERVATION_SCHEMA,
    PAPER_ONLY_STATUS,
    PaperConfiguration,
    PaperValidationError,
    build_proposal,
    canonical_decimal,
    validate_proposal,
)
from trading_lab_app.paper_service import (  # noqa: E402
    ForwardPaperService,
    PaperEngineError,
    disabled_service,
    run_synthetic_demonstration,
)
from trading_lab_app.paper_store import (  # noqa: E402
    InMemoryPaperStore,
    LocalPaperStore,
    PaperStorageValidationError,
    storage_document,
)
from trading_lab_app.timeline_data import (  # noqa: E402
    EVENT_CATEGORIES,
    MarketTimeline,
    TimelineValidationError,
    validate_utc_timestamp,
)


SESSION = "2026-01-01T09:00:00.000000Z"


def timestamp(minute, second=0):
    return "2026-01-01T09:{:02d}:{:02d}.000000Z".format(minute, second)


def metadata(instrument="XAUUSD"):
    return {
        "schema_version": INSTRUMENT_METADATA_SCHEMA,
        "instrument": instrument,
        "tick_size": "0.1",
        "tick_value": "1",
        "contract_size": "100",
        "quantity_step": "0.01",
        "minimum_quantity": "0.01",
        "maximum_quantity": "100",
        "quote_currency": "USD",
    }


def quote(bid, ask, at_utc, instrument="XAUUSD", metadata_value=None):
    spread = Decimal(str(ask)) - Decimal(str(bid))
    return {
        "schema_version": MARKET_OBSERVATION_SCHEMA,
        "observation_kind": "QUOTE",
        "bid": str(bid),
        "ask": str(ask),
        "open_bid": None,
        "high_bid": None,
        "low_bid": None,
        "close_bid": None,
        "open_ask": None,
        "high_ask": None,
        "low_ask": None,
        "close_ask": None,
        "spread": canonical_decimal(spread),
        "instrument_metadata": metadata_value or metadata(instrument),
        "metadata_observed_at_utc": at_utc,
    }


def bar(open_bid, high_bid, low_bid, close_bid, at_utc, instrument="XAUUSD"):
    spread = Decimal("0.2")
    add = lambda value: canonical_decimal(Decimal(str(value)) + spread)
    return {
        "schema_version": MARKET_OBSERVATION_SCHEMA,
        "observation_kind": "BAR",
        "bid": str(close_bid),
        "ask": add(close_bid),
        "open_bid": str(open_bid),
        "high_bid": str(high_bid),
        "low_bid": str(low_bid),
        "close_bid": str(close_bid),
        "open_ask": add(open_bid),
        "high_ask": add(high_bid),
        "low_ask": add(low_bid),
        "close_ask": add(close_bid),
        "spread": "0.2",
        "instrument_metadata": metadata(instrument),
        "metadata_observed_at_utc": at_utc,
    }


def make_service(configuration=None, store=None):
    return ForwardPaperService(
        store=store or InMemoryPaperStore(),
        configuration=configuration,
        session_started_at_utc=SESSION,
    )


def observe(service, at_utc, bid="99.9", ask="100.1", instrument="XAUUSD"):
    return service.append_market_observation(
        instrument, at_utc, at_utc, quote(bid, ask, at_utc, instrument)
    )["market_event"]


def proposal(evidence_id, created, side="BUY", risk="0.5", instrument="XAUUSD"):
    if side == "WAIT":
        values = {
            "entry_type": "WAIT",
            "entry_zone_lower": None,
            "entry_zone_upper": None,
            "stop_loss": None,
            "targets": None,
            "target_allocations_percent": None,
            "wait_reason": "Wait for a later governed observation.",
            "risk_percent": "0",
        }
    elif side == "BUY":
        values = {
            "entry_type": "ENTRY_ZONE",
            "entry_zone_lower": "100",
            "entry_zone_upper": "101",
            "stop_loss": "98",
            "targets": ["102", "103", "104", "105"],
            "target_allocations_percent": ["25", "25", "25", "25"],
            "wait_reason": None,
            "risk_percent": risk,
        }
    else:
        values = {
            "entry_type": "ENTRY_ZONE",
            "entry_zone_lower": "109",
            "entry_zone_upper": "110",
            "stop_loss": "112",
            "targets": ["108", "107", "106", "105"],
            "target_allocations_percent": ["25", "25", "25", "25"],
            "wait_reason": None,
            "risk_percent": risk,
        }
    return build_proposal(
        created_at_utc=created,
        observed_at_utc=created,
        expires_at_utc=timestamp(59),
        instrument=instrument,
        side=side,
        confidence_score=50,
        evidence_quality_status="GOVERNED",
        invalidation_reason="The governed paper setup is no longer valid.",
        beginner_explanation="A bounded synthetic paper contract for offline testing.",
        strategy_basis_ids=["TRL-R2-005.TEST"],
        research_basis_ids=["SYNTHETIC.TEST"],
        market_data_observation_id=evidence_id,
        news_observation_ids=[],
        economic_event_observation_ids=[],
        **values
    )


class TimelineContractTests(unittest.TestCase):
    def append_one(self, timeline=None, observed=timestamp(0, 1), payload=None):
        active = timeline or MarketTimeline()
        return active, active.append(
            "MARKET_OBSERVATION",
            "XAUUSD",
            observed,
            observed,
            "SYNTHETIC.TEST",
            payload or {"price": "100.1"},
        )

    def test_governed_categories_and_schema(self):
        # 12 categories as of TRL-R2-006 (Phase 4): the original 11 plus
        # SIGNAL_PIPELINE_STEP for the governed signal-intelligence pipeline.
        self.assertEqual(len(EVENT_CATEGORIES), 12)
        self.assertIn("SIGNAL_PIPELINE_STEP", EVENT_CATEGORIES)
        timeline, event = self.append_one()
        self.assertEqual(event["schema_version"], "TRL_TIMELINE_EVENT.v1")
        self.assertEqual(timeline.to_document()["schema_version"], "TRL_MARKET_TIMELINE.v1")
        with self.assertRaises(TimelineValidationError):
            timeline.append("UNKNOWN", None, timestamp(0, 2), timestamp(0, 2), "TEST", {})

    def test_strict_utc_timestamp(self):
        self.assertEqual(validate_utc_timestamp(timestamp(1)).tzname(), "UTC")
        for invalid in (
            "2026-01-01T09:01:00Z",
            "2026-01-01T13:01:00.000000+04:00",
            "2026-01-01 09:01:00.000000Z",
            "2026-02-30T09:01:00.000000Z",
        ):
            with self.assertRaises(TimelineValidationError):
                validate_utc_timestamp(invalid)

    def test_exact_numeric_policy_rejects_boolean_float_nan_and_infinity(self):
        for value in (True, 1.5, float("nan"), float("inf")):
            with self.assertRaises(TimelineValidationError):
                canonical_decimal(value)
        timeline = MarketTimeline()
        with self.assertRaises(TimelineValidationError):
            self.append_one(timeline, payload={"price": 1.5})

    def test_payload_and_container_bounds(self):
        with self.assertRaises(TimelineValidationError):
            self.append_one(payload={"text": "x" * 2049})
        with self.assertRaises(TimelineValidationError):
            self.append_one(payload={"items": list(range(129))})

    def test_stable_event_id_and_hash_chain(self):
        first, event_a = self.append_one()
        second, event_b = self.append_one()
        self.assertEqual(event_a["timeline_event_id"], event_b["timeline_event_id"])
        next_event = first.append(
            "PAPER_SESSION_EVENT", None, timestamp(0, 2), timestamp(0, 2),
            "SYNTHETIC.TEST", {"event_type": "CHECKPOINT"},
        )
        self.assertEqual(next_event["previous_event_hash"], event_a["current_event_hash"])
        self.assertNotEqual(next_event["current_event_hash"], event_a["current_event_hash"])
        self.assertEqual(second.to_document()["event_count"], 1)

    def test_corruption_and_hash_mismatch_fail_closed(self):
        timeline, _ = self.append_one()
        document = timeline.to_document()
        document["events"][0]["payload"]["price"] = "999"
        with self.assertRaises(TimelineValidationError):
            MarketTimeline.from_document(document)

    def test_truncation_and_reordering_fail_closed(self):
        timeline, _ = self.append_one()
        timeline.append(
            "PAPER_SESSION_EVENT", None, timestamp(0, 2), timestamp(0, 2),
            "SYNTHETIC.TEST", {"event_type": "CHECKPOINT"},
        )
        truncated = timeline.to_document()
        truncated["events"].pop()
        with self.assertRaises(TimelineValidationError):
            MarketTimeline.from_document(truncated)
        reordered = timeline.to_document()
        reordered["events"].reverse()
        with self.assertRaises(TimelineValidationError):
            MarketTimeline.from_document(reordered)

    def test_backdated_observation_is_rejected(self):
        timeline, _ = self.append_one(observed=timestamp(1))
        with self.assertRaises(TimelineValidationError):
            timeline.append(
                "PAPER_SESSION_EVENT", None, timestamp(0), timestamp(0),
                "SYNTHETIC.TEST", {"event_type": "BACKDATED"},
            )


class ProposalContractTests(unittest.TestCase):
    def evidence(self):
        service = make_service()
        event = observe(service, timestamp(0, 1))
        return service, event["timeline_event_id"]

    def test_buy_and_sell_ordering(self):
        _service, evidence_id = self.evidence()
        self.assertEqual(proposal(evidence_id, timestamp(0, 2), "BUY")["side"], "BUY")
        sell = proposal(evidence_id, timestamp(0, 2), "SELL")
        self.assertEqual(sell["targets"], ["108", "107", "106", "105"])
        invalid = deepcopy(sell)
        invalid["targets"] = ["108", "109", "106", "105"]
        with self.assertRaises(PaperValidationError):
            validate_proposal(invalid)

    def test_wait_has_reason_and_no_executable_fields(self):
        service, evidence_id = self.evidence()
        wait = proposal(evidence_id, timestamp(0, 2), "WAIT")
        self.assertEqual(service.submit_proposal(wait)["status"], "WAIT")
        self.assertEqual(service.account_document()["open_position_count"], 0)
        invalid = deepcopy(wait)
        invalid["entry_zone_lower"] = "100"
        with self.assertRaises(PaperValidationError):
            validate_proposal(invalid)

    def test_stable_proposal_id_and_confidence_semantics(self):
        _service, evidence_id = self.evidence()
        first = proposal(evidence_id, timestamp(0, 2))
        second = proposal(evidence_id, timestamp(0, 2))
        self.assertEqual(first["proposal_id"], second["proposal_id"])
        invalid = deepcopy(first)
        invalid["confidence_score"] = True
        with self.assertRaises(PaperValidationError):
            validate_proposal(invalid)

    def test_prohibited_performance_claim_fails(self):
        _service, evidence_id = self.evidence()
        invalid = deepcopy(proposal(evidence_id, timestamp(0, 2)))
        invalid["beginner_explanation"] = "Guaranteed profit from this setup."
        with self.assertRaises(PaperValidationError):
            validate_proposal(invalid)

    def test_missing_or_future_market_evidence_fails_closed(self):
        service, evidence_id = self.evidence()
        missing = deepcopy(proposal(evidence_id, timestamp(0, 2)))
        missing["market_data_observation_id"] = "tle_" + "1" * 32
        missing["proposal_id"] = "pp_" + "1" * 32
        with self.assertRaises(PaperEngineError):
            service.submit_proposal(missing)
        future_service = make_service()
        future_event = observe(future_service, timestamp(0, 2))
        future = build_proposal(
            created_at_utc=timestamp(0, 1),
            observed_at_utc=timestamp(0, 3),
            expires_at_utc=timestamp(59),
            instrument="XAUUSD",
            side="BUY",
            entry_type="ENTRY_ZONE",
            entry_zone_lower="100",
            entry_zone_upper="101",
            stop_loss="98",
            targets=["102", "103", "104", "105"],
            target_allocations_percent=["25", "25", "25", "25"],
            confidence_score=50,
            evidence_quality_status="GOVERNED",
            invalidation_reason="The governed paper setup is no longer valid.",
            wait_reason=None,
            beginner_explanation="A bounded synthetic paper contract for offline testing.",
            strategy_basis_ids=["TRL-R2-005.TEST"],
            research_basis_ids=["SYNTHETIC.TEST"],
            market_data_observation_id=future_event["timeline_event_id"],
            news_observation_ids=[],
            economic_event_observation_ids=[],
            risk_percent="0.5",
        )
        with self.assertRaisesRegex(PaperEngineError, "future"):
            future_service.submit_proposal(future)


class StorageRecoveryTests(unittest.TestCase):
    def test_in_memory_serialization_restart(self):
        store = InMemoryPaperStore()
        service = make_service(store=store)
        observe(service, timestamp(0, 1))
        before = service.timeline_document()
        restarted = ForwardPaperService(store=store)
        self.assertEqual(restarted.timeline_document(), before)

    def test_atomic_local_persistence_uses_fsync_and_replace(self):
        timeline = MarketTimeline()
        timeline.append(
            "PAPER_SESSION_EVENT", None, SESSION, SESSION, "SYNTHETIC.TEST",
            {"event_type": "SESSION_STARTED", "session_started_at_utc": SESSION},
        )
        document = storage_document(PaperConfiguration().document(), timeline)
        store = LocalPaperStore(Path(tempfile.gettempdir()) / "not-created" / "paper.json")

        class MemoryTemporary(io.BytesIO):
            name = str(Path(tempfile.gettempdir()) / "not-created" / ".paper-unique.tmp")

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def fileno(self):
                return 7

        handle = MemoryTemporary()
        with mock.patch("pathlib.Path.mkdir"), mock.patch(
            "trading_lab_app.paper_store.tempfile.NamedTemporaryFile",
            return_value=handle,
        ), mock.patch("trading_lab_app.paper_store.os.fsync") as fsync, mock.patch(
            "trading_lab_app.paper_store.os.replace"
        ) as replace:
            store.save(document)
        self.assertTrue(handle.getvalue().endswith(b"\n"))
        fsync.assert_called_once_with(7)
        replace.assert_called_once()
        self.assertEqual(store.trusted_snapshot, document)

    def test_atomic_replace_failure_retains_trusted_snapshot_and_cleans_exact_temp(self):
        timeline = MarketTimeline()
        document = storage_document(PaperConfiguration().document(), timeline)
        store = LocalPaperStore(Path(tempfile.gettempdir()) / "not-created" / "paper.json")
        store._trusted_snapshot = deepcopy(document)

        class MemoryTemporary(io.BytesIO):
            name = str(Path(tempfile.gettempdir()) / "not-created" / ".paper-exact.tmp")

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def fileno(self):
                return 8

        handle = MemoryTemporary()
        with mock.patch("pathlib.Path.mkdir"), mock.patch(
            "trading_lab_app.paper_store.tempfile.NamedTemporaryFile",
            return_value=handle,
        ), mock.patch("trading_lab_app.paper_store.os.fsync"), mock.patch(
            "trading_lab_app.paper_store.os.replace", side_effect=OSError
        ), mock.patch("pathlib.Path.unlink") as unlink, self.assertRaises(RuntimeError):
            store.save(document)
        unlink.assert_called_once_with()
        self.assertEqual(store.trusted_snapshot, document)

    def test_persistence_failure_keeps_valid_in_memory_projection(self):
        store = InMemoryPaperStore()
        service = make_service(store=store)
        initial_count = service.timeline_document()["event_count"]
        store.fail_writes = True
        observe(service, timestamp(0, 1))
        self.assertEqual(service.timeline_document()["event_count"], initial_count + 1)
        health = service.health_document()
        self.assertEqual(health["persistence_status"], "WRITE_FAILED_IN_MEMORY_VALID")
        self.assertEqual(health["persistence_failure_count"], 1)

    def test_invalid_storage_does_not_silently_replace_trusted_snapshot(self):
        store = InMemoryPaperStore()
        service = make_service(store=store)
        trusted = store.trusted_snapshot
        invalid = deepcopy(trusted)
        invalid["timeline"]["event_count"] += 1
        store.replace_raw_for_test(invalid)
        restarted = ForwardPaperService(store=store)
        self.assertFalse(restarted.health_document()["operational"])
        self.assertEqual(restarted.health_document()["startup_diagnostic_code"], "INVALID_PAPER_STORAGE")
        self.assertEqual(store.trusted_snapshot, trusted)

    def test_repeated_shutdown_is_safe(self):
        service = make_service()
        self.assertTrue(service.shutdown())
        self.assertTrue(service.shutdown())


class ForwardFillAndAccountingTests(unittest.TestCase):
    def prepared_buy(self, configuration=None):
        service = make_service(configuration)
        evidence = observe(service, timestamp(0, 1))
        result = service.submit_proposal(
            proposal(evidence["timeline_event_id"], timestamp(0, 2), "BUY")
        )
        return service, result

    def test_forward_only_and_same_observation_cannot_fill(self):
        service, result = self.prepared_buy()
        self.assertEqual(result["status"], "PENDING")
        self.assertEqual(service.account_document()["open_position_count"], 0)
        later = observe(service, timestamp(0, 3), "100.4", "100.6")
        self.assertNotEqual(
            service.positions_document()["positions"][0]["entry_market_observation_id"],
            result["proposal_event"]["payload"]["proposal"]["market_data_observation_id"],
        )
        self.assertEqual(later["append_sequence"], 4)

    def test_buy_uses_ask_with_explicit_spread_and_slippage(self):
        service, _ = self.prepared_buy()
        observe(service, timestamp(0, 3), "100.4", "100.6")
        position = service.positions_document()["positions"][0]
        self.assertEqual(position["entry_side"], "ASK")
        self.assertEqual(position["entry_basis_price"], "100.6")
        self.assertEqual(position["entry_price"], "100.7")
        self.assertEqual(position["entry_spread"], "0.2")
        self.assertGreater(Decimal(position["entry_slippage_amount"]), 0)

    def test_late_observed_preproposal_price_cannot_retroactively_fill(self):
        service, _ = self.prepared_buy()
        occurred = "2026-01-01T09:00:01.500000Z"
        observed = timestamp(0, 3)
        result = service.append_market_observation(
            "XAUUSD", occurred, observed, quote("100.4", "100.6", observed)
        )
        self.assertEqual(result["status"], "ACCEPTED")
        self.assertNotIn("PAPER_ENTRY", [item["event_category"] for item in result["actions"]])
        self.assertEqual(service.account_document()["open_position_count"], 0)

    def test_sell_uses_bid_and_short_profit_accounting(self):
        service = make_service()
        evidence = observe(service, timestamp(0, 1), "110", "110.2")
        service.submit_proposal(
            proposal(evidence["timeline_event_id"], timestamp(0, 2), "SELL")
        )
        observe(service, timestamp(0, 3), "109.5", "109.7")
        position = service.positions_document()["positions"][0]
        self.assertEqual(position["entry_side"], "BID")
        self.assertEqual(position["entry_price"], "109.4")
        for minute, low in ((1, "107.7"), (2, "106.7"), (3, "105.7"), (4, "104.7")):
            at = timestamp(minute)
            service.append_market_observation(
                "XAUUSD", at, at, bar("109", "109.2", low, str(109 - minute), at)
            )
        account = service.account_document()
        self.assertEqual(account["completed_paper_trade_count"], 1)
        self.assertGreater(Decimal(account["realized_pnl"]), 0)

    def test_expired_proposal_cannot_fill(self):
        service, _ = self.prepared_buy()
        at = "2026-01-01T10:00:01.000000Z"
        result = service.append_market_observation(
            "XAUUSD", at, at, quote("100.4", "100.6", at)
        )
        self.assertNotIn("PAPER_ENTRY", [item["event_category"] for item in result["actions"]])
        self.assertIn("PROPOSAL_EXPIRED", [
            event["payload"].get("event_type")
            for event in service.timeline_document()["events"]
            if event["event_category"] == "PAPER_SESSION_EVENT"
        ])

    def test_stale_observation_cannot_fill(self):
        service, _ = self.prepared_buy()
        occurred = timestamp(0, 3)
        observed = timestamp(10, 3)
        payload = quote("100.4", "100.6", observed)
        result = service.append_market_observation(
            "XAUUSD", occurred, observed, payload
        )
        self.assertEqual(result["status"], "STALE_REJECTED")
        self.assertEqual(service.account_document()["open_position_count"], 0)

    def test_missing_spread_or_contract_fails_closed(self):
        service = make_service()
        payload = quote("99.9", "100.1", timestamp(0, 1))
        del payload["spread"]
        with self.assertRaises(PaperEngineError):
            service.append_market_observation(
                "XAUUSD", timestamp(0, 1), timestamp(0, 1), payload
            )
        payload = quote("99.9", "100.1", timestamp(0, 1))
        del payload["instrument_metadata"]["tick_value"]
        with self.assertRaises(PaperEngineError):
            service.append_market_observation(
                "XAUUSD", timestamp(0, 1), timestamp(0, 1), payload
            )

    def test_stop_first_ambiguity_and_tp1_tp2_partial_accounting(self):
        result = run_synthetic_demonstration()
        self.assertEqual(result["ambiguous_stop_first_count"], 1)
        self.assertEqual(
            result["ambiguous_resolution"],
            "CONSERVATIVE_STOP_FIRST_UNKNOWN_INTRABAR_ORDER",
        )
        self.assertEqual(result["event_category_counts"]["PAPER_TP"], 6)
        self.assertEqual(result["event_category_counts"]["PAPER_STOP"], 1)

    def test_completed_tp1_through_tp4_and_restart_demo(self):
        first = run_synthetic_demonstration()
        second = run_synthetic_demonstration()
        self.assertEqual(first, second)
        self.assertEqual(first["label"], "SYNTHETIC DEMONSTRATION — NOT LIVE MARKET DATA")
        self.assertEqual(first["sell_proposal_status"], "FILLED")
        self.assertEqual(first["account"]["completed_paper_trade_count"], 2)
        self.assertTrue(first["restart_reconstruction_exact"])
        self.assertTrue(first["account"]["synthetic_demonstration_values"])

    def test_zero_quantity_target_does_not_block_later_targets(self):
        coarse_metadata = metadata("XAUUSD")
        coarse_metadata["quantity_step"] = "1"
        coarse_metadata["minimum_quantity"] = "1"
        service = make_service()
        evidence = service.append_market_observation(
            "XAUUSD",
            timestamp(0, 1),
            timestamp(0, 1),
            quote("99.9", "100.1", timestamp(0, 1), metadata_value=coarse_metadata),
        )["market_event"]
        service.submit_proposal(
            proposal(evidence["timeline_event_id"], timestamp(0, 2), "BUY", risk="0.05")
        )
        service.append_market_observation(
            "XAUUSD",
            timestamp(0, 3),
            timestamp(0, 3),
            quote("100.4", "100.6", timestamp(0, 3), metadata_value=coarse_metadata),
        )
        position = service.positions_document()["positions"][0]
        self.assertEqual(position["initial_quantity"], "1")
        result = service.append_market_observation(
            "XAUUSD",
            timestamp(0, 4),
            timestamp(0, 4),
            quote("105.5", "105.7", timestamp(0, 4), metadata_value=coarse_metadata),
        )
        tp_events = [
            item for item in result["actions"] if item["event_category"] == "PAPER_TP"
        ]
        self.assertEqual(
            [item["payload"]["target_number"] for item in tp_events], [1, 2, 3, 4]
        )
        self.assertEqual([item["payload"]["quantity"] for item in tp_events], ["0", "0", "0", "1"])
        account = service.account_document()
        self.assertEqual(account["open_position_count"], 0)
        self.assertEqual(account["completed_paper_trade_count"], 1)

    def test_fees_slippage_and_risk_sizing_are_explicit_and_bounded(self):
        service, _ = self.prepared_buy()
        observe(service, timestamp(0, 3), "100.4", "100.6")
        position = service.positions_document()["positions"][0]
        self.assertGreater(Decimal(position["entry_fee"]), 0)
        self.assertGreater(Decimal(position["entry_slippage_amount"]), 0)
        limit = Decimal(service.account_document()["marked_equity"]) * Decimal("0.005")
        self.assertLessEqual(Decimal(position["initial_risk_amount"]), limit + Decimal("1"))

    def test_one_position_per_instrument_is_risk_rejected(self):
        service, _ = self.prepared_buy()
        fill = observe(service, timestamp(0, 3), "100.4", "100.6")
        second = proposal(fill["timeline_event_id"], timestamp(0, 4), "BUY")
        result = service.submit_proposal(second)
        self.assertEqual(result["status"], "REJECTED")
        self.assertEqual(result["reason_code"], "ONE_OPEN_POSITION_PER_INSTRUMENT")
        self.assertEqual(service.account_document()["open_position_count"], 1)


class RiskHaltTests(unittest.TestCase):
    def stopped_service(self, configuration):
        service = make_service(configuration)
        evidence = observe(service, timestamp(0, 1))
        service.submit_proposal(proposal(evidence["timeline_event_id"], timestamp(0, 2)))
        observe(service, timestamp(0, 3), "100.4", "100.6")
        at = timestamp(1)
        service.append_market_observation(
            "XAUUSD", at, at, bar("100", "101", "97", "98", at)
        )
        return service

    def test_hard_risk_configuration_limits(self):
        with self.assertRaises(PaperValidationError):
            PaperConfiguration(maximum_risk_percent=Decimal("1.1"))
        with self.assertRaises(PaperValidationError):
            PaperConfiguration(maximum_daily_loss_percent=Decimal("2.1"))
        with self.assertRaises(PaperValidationError):
            PaperConfiguration(maximum_drawdown_percent=Decimal("5.1"))
        configuration = PaperConfiguration(
            default_risk_percent=Decimal("0.4"),
            maximum_risk_percent=Decimal("0.4"),
        )
        service = make_service(configuration)
        evidence = observe(service, timestamp(0, 1))
        result = service.submit_proposal(
            proposal(evidence["timeline_event_id"], timestamp(0, 2), risk="0.5")
        )
        self.assertEqual(result["reason_code"], "PROPOSAL_RISK_EXCEEDS_GOVERNED_MAXIMUM")

    def test_daily_loss_halt_is_sticky(self):
        configuration = PaperConfiguration(
            maximum_daily_loss_percent=Decimal("0.1"),
            maximum_drawdown_percent=Decimal("5"),
        )
        service = self.stopped_service(configuration)
        health = service.health_document()
        self.assertTrue(health["risk_halt"])
        self.assertEqual(health["risk_halt_reason"], "MAXIMUM_DAILY_PAPER_LOSS")
        observe(service, timestamp(2), "100", "100.2")
        self.assertTrue(service.health_document()["risk_halt"])

    def test_drawdown_halt(self):
        configuration = PaperConfiguration(
            maximum_daily_loss_percent=Decimal("2"),
            maximum_drawdown_percent=Decimal("0.1"),
        )
        service = self.stopped_service(configuration)
        self.assertEqual(
            service.health_document()["risk_halt_reason"],
            "MAXIMUM_PAPER_ACCOUNT_DRAWDOWN",
        )

    def test_no_risk_increase_after_loss(self):
        service = self.stopped_service(PaperConfiguration())
        evidence = observe(service, timestamp(2), "100", "100.2")
        increased = proposal(evidence["timeline_event_id"], timestamp(2, 1), risk="1")
        result = service.submit_proposal(increased)
        self.assertEqual(result["reason_code"], "RISK_INCREASE_AFTER_LOSS_FORBIDDEN")


class ApiUiAndNegativeSurfaceTests(unittest.TestCase):
    def test_disabled_mode_constructs_no_storage(self):
        paper = disabled_service()
        self.assertIsNone(paper.store)
        self.assertFalse(paper.health_document()["storage_constructed"])
        self.assertEqual(paper.timeline_document()["event_count"], 0)

    def test_api_schemas_and_read_only_method_host_protections(self):
        paper = make_service()
        httpd = server.create_server(0, paper_service=paper)
        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()
        try:
            connection = http.client.HTTPConnection(
                "127.0.0.1", httpd.server_address[1], timeout=3
            )
            for path in server.PAPER_API_ROUTES:
                connection.request("GET", path, headers={"Host": "127.0.0.1"})
                response = connection.getresponse()
                document = json.loads(response.read().decode("utf-8"))
                self.assertEqual(response.status, 200)
                self.assertTrue(document["schema_version"].startswith("TRL_"))
            connection.request("HEAD", "/api/paper-account", headers={"Host": "127.0.0.1"})
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.read(), b"")
            connection.request("POST", "/api/paper-account", headers={"Host": "127.0.0.1"})
            response = connection.getresponse()
            response.read()
            self.assertEqual(response.status, 405)
            self.assertEqual(response.getheader("Allow"), "GET, HEAD")
            connection.request("GET", "/api/paper-health", headers={"Host": "example.invalid"})
            response = connection.getresponse()
            self.assertEqual(response.status, 421)
            response.read()
            connection.close()
        finally:
            httpd.shutdown()
            httpd.server_close()
            thread.join(timeout=3)
        self.assertFalse(thread.is_alive())
        self.assertEqual(httpd.active_request_count(), 0)

    def test_dashboard_is_beginner_friendly_and_never_displays_proposals(self):
        html = (BASE / "trading_lab_app" / "static" / "index.html").read_text(
            encoding="utf-8"
        )
        javascript = (BASE / "trading_lab_app" / "static" / "app.js").read_text(
            encoding="utf-8"
        )
        self.assertIn("PAPER ONLY", html)
        self.assertIn("No active paper proposal yet", html)
        self.assertIn("Expert timeline and recovery details", html)
        self.assertNotIn("renderPaperProposal", javascript)
        self.assertNotIn("fake live profit", (html + javascript).casefold())

    def test_no_mt5_trade_or_order_method_was_added(self):
        source = (BASE / "trading_lab_app" / "mt5_connector.py").read_text(
            encoding="utf-8"
        ).casefold()
        for method in ("order_send", "order_check", "trade_action_deal"):
            self.assertNotIn(method, source)

    def test_fixture_contains_no_external_or_account_information(self):
        fixture = (BASE / "trading_lab_app" / "synthetic_paper_demonstration.json").read_text(
            encoding="utf-8"
        )
        self.assertIn("SYNTHETIC DEMONSTRATION — NOT LIVE MARKET DATA", fixture)
        for forbidden in ("https://", "account_number", "credential", "publisher_body"):
            self.assertNotIn(forbidden, fixture.casefold())


if __name__ == "__main__":
    unittest.main(verbosity=2)
