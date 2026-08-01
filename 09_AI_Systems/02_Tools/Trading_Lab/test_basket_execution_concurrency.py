"""True separate-process concurrency regression tests for the Phase 6
(TRL-R2-009) basket execution service.

Mirrors test_mt5_execution_concurrency.py's exact house style: real,
separate OS worker processes launched via subprocess (never threads, never
sequential in-process calls, never a mocked lock), synchronized with
readiness-marker files polled with a bounded timeout, never a fixed sleep
guess. A plain in-process threading.Lock could not catch a genuine
cross-process race, so these tests deliberately do not simulate
concurrency with sequential objects in one process.

All storage is isolated under a per-test tempfile.mkdtemp() directory;
nothing here touches real LOCALAPPDATA or a real broker. Every worker uses
FakeExecutionAdapter only.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

APP_DIRECTORY = Path(__file__).resolve().parent
READY_POLL_INTERVAL_SECONDS = 0.01
READY_TIMEOUT_SECONDS = 30.0
FIXTURE_PROPOSAL_EXPIRES_AT_UTC = "2035-08-01T13:00:00.000000Z"

_BASKET_CREATE_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app import mode_service as ms
from trading_lab_app import mt5_execution_adapter as maa
from trading_lab_app import mt5_execution_journal as mej
from trading_lab_app import mt5_execution_service as mes
from trading_lab_app import basket_execution_service as bes

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])
mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset({{"SMA-001"}})

with open(TEMP / "shared_state.json", encoding="utf-8") as handle:
    shared = json.load(handle)

mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
mode_svc.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
adapter = maa.FakeExecutionAdapter()
adapter.set_symbol("XAUUSD")
adapter.account.update({{"login": 900100100, "company": "Fake Demo Broker Ltd", "server": "FakeDemo-Server"}})
fingerprint = mes.AccountFingerprintConfiguration(login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server")
journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=TEMP / "journal.json"))
basket_svc = bes.BasketExecutionService(
    adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint,
)

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

error = None
basket_id = None
try:
    record = basket_svc.build_basket(shared["order_intent_id"])
    basket_id = record["basket_id"]
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)

result = {{
    "worker_id": WORKER_ID,
    "basket_id": basket_id,
    "error": error,
    "order_check_calls": len([c for c in adapter.calls if c[0] == "order_check"]),
    "order_send_calls": len([c for c in adapter.calls if c[0] == "order_send"]),
}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result), encoding="utf-8")
'''

_BASKET_SEND_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app import mode_service as ms
from trading_lab_app import mt5_execution_adapter as maa
from trading_lab_app import mt5_execution_journal as mej
from trading_lab_app import mt5_execution_service as mes
from trading_lab_app import basket_execution_service as bes

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])

with open(TEMP / "shared_state.json", encoding="utf-8") as handle:
    shared = json.load(handle)

mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
mode_svc.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
adapter = maa.FakeExecutionAdapter()
adapter.set_symbol("XAUUSD")
adapter.account.update({{"login": 900100100, "company": "Fake Demo Broker Ltd", "server": "FakeDemo-Server"}})
fingerprint = mes.AccountFingerprintConfiguration(login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server")
journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=TEMP / "journal.json"))
basket_svc = bes.BasketExecutionService(
    adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint,
)

# Test-only cross-process observation: in-memory call counters on `adapter`
# exist only inside this one worker process and are invisible to the test
# harness or the other worker, so each order_send call is independently
# marked with its own uniquely-named file in the isolated temp directory
# instead. Never held under the journal lock -- the marker is written
# exactly where the real call happens, outside any lock.
_original_order_send = adapter.order_send
def _observed_order_send(request):
    marker_name = "order-send-call-%s-%s.marker" % (WORKER_ID, time.monotonic_ns())
    (TEMP / marker_name).write_text("1", encoding="utf-8")
    return _original_order_send(request)
adapter.order_send = _observed_order_send

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

error = None
reason_code = None
try:
    basket_svc.send_basket_next(shared["basket_id"])
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)
    reason_code = getattr(exc, "reason_code", None)

result_doc = {{
    "worker_id": WORKER_ID,
    "error": error,
    "reason_code": reason_code,
}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result_doc), encoding="utf-8")
'''


def _wait_for(path, timeout=READY_TIMEOUT_SECONDS):
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("timed out waiting for {}".format(path))
        time.sleep(READY_POLL_INTERVAL_SECONDS)


def _run_two_workers(source_template, temp_dir):
    worker_path = temp_dir / "worker.py"
    worker_path.write_text(source_template.format(app_dir=str(APP_DIRECTORY)), encoding="utf-8")

    procs = [
        subprocess.Popen([sys.executable, "-B", str(worker_path), str(worker_id), str(temp_dir)])
        for worker_id in (1, 2)
    ]
    _wait_for(temp_dir / "ready-1")
    _wait_for(temp_dir / "ready-2")
    (temp_dir / "go.signal").write_text("1", encoding="utf-8")

    for proc in procs:
        proc.wait(timeout=30)

    results = {}
    for worker_id in (1, 2):
        with open(temp_dir / "result-{}.json".format(worker_id), encoding="utf-8") as handle:
            results[worker_id] = json.load(handle)
    return results


def _build_geometry_approved_parent_intent(temp_dir):
    """Single-process, non-racy setup: build one valid, geometry-approved
    parent order intent, sharing the durable journal path the racing
    worker processes will use afterward. Returns order_intent_id."""
    import trading_lab_app.mode_service as ms
    import trading_lab_app.mt5_execution_adapter as maa
    import trading_lab_app.mt5_execution_journal as mej
    import trading_lab_app.mt5_execution_service as mes
    import trading_lab_app.signal_data as sd

    original_geometry = mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES
    try:
        mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset({"SMA-001"})
        proposal = sd.build_signal_proposal(
            created_at_utc="2026-08-01T11:00:00.000000Z",
            observed_at_utc="2026-08-01T11:00:00.000000Z",
            expires_at_utc=FIXTURE_PROPOSAL_EXPIRES_AT_UTC,
            instrument="XAUUSD", side="BUY", entry_type="ENTRY_ZONE",
            entry_zone_lower="1899", entry_zone_upper="1899", stop_loss="1895",
            targets=["1902", "1905", "1908", "1911"], target_allocations_percent=["25", "25", "25", "25"],
            confidence_score=80, evidence_quality_status="GOVERNED", invalidation_reason="structure break",
            wait_reason=None, beginner_explanation="basket-concurrency-setup",
            strategy_basis_ids=["BASIS-1"], research_basis_ids=["BASIS-1"],
            market_data_observation_id="tle_" + "0" * 32, news_observation_ids=[], economic_event_observation_ids=[],
            risk_percent="0.5", strategy_id="SMA-001", strategy_version="1.0.0", broker_native_instrument="XAUUSD",
            regime_classification="TREND_UP", feature_snapshot_hash="0" * 64,
            data_quality_result={"status": "PASS", "reasons": []},
            news_event_risk_result={"status": "PASS", "reasons": [], "evidence_ids": []},
            confidence_calibration_source="PHASE4_COMPONENT_SCORE_UNCALIBRATED_V1", confidence_status="UNCALIBRATED_HEURISTIC",
            explanation="basket-concurrency-setup fixture", rejection_reasons=[],
            model_rule_versions={"strategy_version": "1.0.0", "risk_engine_version": "1.0.0", "pipeline_version": "1.0.0"},
            role_results={key: {"status": "PASS", "reasons": []} for key in sd.ROLE_NAMES},
            candidate_quantity="0.04", independent_quantity="0.04", maximum_spread="50",
            active_risk_policy_hash="1" * 64, operating_mode="MT5_DEMO_MANUAL", sample_label="SYNTHETIC_PAPER",
        )
        mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
        mode_svc.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
        adapter = maa.FakeExecutionAdapter()
        adapter.set_symbol("XAUUSD")
        fingerprint = mes.AccountFingerprintConfiguration(login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server")
        journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=temp_dir / "journal.json"))
        svc = mes.ExecutionService(adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint)
        intent = svc.build_order_intent(proposal)
        return intent["order_intent_id"]
    finally:
        mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = original_geometry


def _build_confirmed_basket(temp_dir):
    """Single-process, non-racy setup: build a basket, check all 4
    children, request and accept a confirmation cycle. Returns basket_id."""
    import trading_lab_app.mode_service as ms
    import trading_lab_app.mt5_execution_adapter as maa
    import trading_lab_app.mt5_execution_journal as mej
    import trading_lab_app.mt5_execution_service as mes
    import trading_lab_app.basket_execution_data as bed
    import trading_lab_app.basket_execution_service as bes

    order_intent_id = _build_geometry_approved_parent_intent(temp_dir)
    original_geometry = mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES
    try:
        mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset({"SMA-001"})
        mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
        mode_svc.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
        adapter = maa.FakeExecutionAdapter()
        adapter.set_symbol("XAUUSD")
        fingerprint = mes.AccountFingerprintConfiguration(login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server")
        journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=temp_dir / "journal.json"))
        basket_svc = bes.BasketExecutionService(adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint)

        record = basket_svc.build_basket(order_intent_id)
        basket_id = record["basket_id"]
        for _ in range(4):
            basket_svc.check_basket(basket_id)
        cycle = basket_svc.request_basket_confirmation(basket_id)
        basket_svc.confirm_basket(basket_id, bed.format_confirmation_entry(cycle["challenge_hex"]))
        return basket_id
    finally:
        mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = original_geometry


class ConcurrentBasketCreationTests(unittest.TestCase):
    def test_two_processes_racing_build_basket_converge_on_one_basket(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            order_intent_id = _build_geometry_approved_parent_intent(temp_dir)
            with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
                json.dump({"order_intent_id": order_intent_id}, handle)
            results = _run_two_workers(_BASKET_CREATE_WORKER_SOURCE, temp_dir)

        self.assertIsNone(results[1]["error"])
        self.assertIsNone(results[2]["error"])
        self.assertIsNotNone(results[1]["basket_id"])
        self.assertEqual(results[1]["basket_id"], results[2]["basket_id"])
        # Neither worker's own adapter ever reaches order_check/order_send
        # merely from build_basket -- basket construction never checks or
        # sends a child.
        self.assertEqual(results[1]["order_check_calls"], 0)
        self.assertEqual(results[2]["order_check_calls"], 0)
        self.assertEqual(results[1]["order_send_calls"], 0)
        self.assertEqual(results[2]["order_send_calls"], 0)

    def test_journal_has_exactly_one_authoritative_basket_created_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            order_intent_id = _build_geometry_approved_parent_intent(temp_dir)
            with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
                json.dump({"order_intent_id": order_intent_id}, handle)
            _run_two_workers(_BASKET_CREATE_WORKER_SOURCE, temp_dir)
            with open(temp_dir / "journal.json", encoding="utf-8") as handle:
                document = json.load(handle)
        events = document["journal"]["events"]
        created = [e for e in events if e["event_type"] == "BASKET_CREATED"]
        reused = [e for e in events if e["event_type"] == "BASKET_REUSED"]
        self.assertEqual(len(created), 1)
        self.assertEqual(len(reused), 1)
        self.assertEqual(
            created[0]["payload"]["basket_record"]["basket_id"],
            reused[0]["payload"]["basket_record"]["basket_id"],
        )

    def test_journal_is_valid_hash_chain_after_basket_creation_race(self):
        import trading_lab_app.mt5_execution_journal as mej
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            order_intent_id = _build_geometry_approved_parent_intent(temp_dir)
            with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
                json.dump({"order_intent_id": order_intent_id}, handle)
            _run_two_workers(_BASKET_CREATE_WORKER_SOURCE, temp_dir)
            writer = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=temp_dir / "journal.json"))
        self.assertEqual(writer.startup_diagnostic_code, "OK")

    def test_no_lock_file_remains_after_basket_creation_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            order_intent_id = _build_geometry_approved_parent_intent(temp_dir)
            with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
                json.dump({"order_intent_id": order_intent_id}, handle)
            _run_two_workers(_BASKET_CREATE_WORKER_SOURCE, temp_dir)
            lock_files = list(temp_dir.glob("*.lock"))
        self.assertEqual(lock_files, [])


class ConcurrentChildSendTests(unittest.TestCase):
    def test_two_processes_racing_send_basket_next_send_at_most_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            basket_id = _build_confirmed_basket(temp_dir)
            with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
                json.dump({"basket_id": basket_id}, handle)
            results = _run_two_workers(_BASKET_SEND_WORKER_SOURCE, temp_dir)
            marker_files = list(temp_dir.glob("order-send-call-*.marker"))

        successes = [r for r in results.values() if r["error"] is None]
        failures = [r for r in results.values() if r["error"] is not None]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        # Exactly one process ever reached the adapter's order_send method
        # -- proven by an independent, per-call marker file, not an
        # in-memory counter (which cannot be shared across processes).
        self.assertEqual(len(marker_files), 1)
        self.assertEqual(failures[0]["reason_code"], "BASKET_CHILD_SEND_ALREADY_RESERVED")

    def test_journal_has_exactly_one_send_reservation_after_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            basket_id = _build_confirmed_basket(temp_dir)
            with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
                json.dump({"basket_id": basket_id}, handle)
            _run_two_workers(_BASKET_SEND_WORKER_SOURCE, temp_dir)
            with open(temp_dir / "journal.json", encoding="utf-8") as handle:
                document = json.load(handle)
        events = document["journal"]["events"]
        reserved = [e for e in events if e["event_type"] == "BASKET_CHILD_SEND_RESERVED"]
        results_events = [e for e in events if e["event_type"] == "BASKET_CHILD_SEND_RESULT"]
        self.assertEqual(len(reserved), 1)
        self.assertEqual(len(results_events), 1)

    def test_child_is_not_resent_after_restart_following_race(self):
        import trading_lab_app.mode_service as ms
        import trading_lab_app.mt5_execution_adapter as maa
        import trading_lab_app.mt5_execution_journal as mej
        import trading_lab_app.mt5_execution_service as mes
        import trading_lab_app.basket_execution_service as bes

        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            basket_id = _build_confirmed_basket(temp_dir)
            with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
                json.dump({"basket_id": basket_id}, handle)
            _run_two_workers(_BASKET_SEND_WORKER_SOURCE, temp_dir)
            markers_after_race = len(list(temp_dir.glob("order-send-call-*.marker")))
            self.assertEqual(markers_after_race, 1)

            # Restart: a brand-new process-equivalent service instance
            # (fresh adapter, fresh in-memory mode service, same durable
            # journal) reconstructed after the race completed.
            original_geometry = mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES
            mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset({"SMA-001"})
            self.addCleanup(setattr, mes, "EXECUTION_GEOMETRY_APPROVED_STRATEGIES", original_geometry)

            mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
            mode_svc.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
            adapter = maa.FakeExecutionAdapter()
            adapter.set_symbol("XAUUSD")
            fingerprint = mes.AccountFingerprintConfiguration(login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server")
            journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=temp_dir / "journal.json"))
            basket_svc = bes.BasketExecutionService(adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint)

            # Merely loading/inspecting after restart must never call the
            # adapter or resend anything.
            status = basket_svc.basket_status_document(basket_id)
            self.assertEqual(status["filled_child_count"], 1)
            self.assertEqual(len([c for c in adapter.calls if c[0] == "order_send"]), 0)

            # Sending the next (second) child from this fresh instance must
            # not touch the first (already-won) child again.
            won_child_id = [c["basket_child_id"] for c in status["children"] if c["execution_state"] == "FILLED"][0]
            basket_svc.send_basket_next(basket_id)
            status_after = basket_svc.basket_status_document(basket_id)
            won_child_after = [c for c in status_after["children"] if c["basket_child_id"] == won_child_id][0]
            self.assertEqual(won_child_after["execution_state"], "FILLED")
            self.assertEqual(status_after["filled_child_count"], 2)

    def test_no_lock_file_remains_after_send_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            basket_id = _build_confirmed_basket(temp_dir)
            with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
                json.dump({"basket_id": basket_id}, handle)
            _run_two_workers(_BASKET_SEND_WORKER_SOURCE, temp_dir)
            lock_files = list(temp_dir.glob("*.lock"))
        self.assertEqual(lock_files, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
