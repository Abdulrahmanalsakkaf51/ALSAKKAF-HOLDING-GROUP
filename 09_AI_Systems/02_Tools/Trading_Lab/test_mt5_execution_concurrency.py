"""Regression tests for the Phase 5 cross-process locking correction.

A Founder-review manual rehearsal found that ``build_order_intent`` and
``confirm_and_send`` had no cross-process mutual exclusion around their
"search the durable journal, then decide, then persist" critical sections
-- two genuinely separate OS processes racing against the same initially
empty durable journal each independently created a distinct order intent
for the identical governed proposal, with one silently lost from disk.
This file exercises the fix (``mt5_execution_journal._CrossProcessFileLock``
/ ``ExecutionJournalWriter.acquire_creation_lock``) using real, separate
worker processes launched via ``subprocess`` -- a plain in-process
``threading.Lock`` could not have caught the original defect, so these
tests deliberately do not simulate concurrency with sequential objects in
one process. Synchronization between workers uses readiness-marker files
polled with a bounded timeout, never a fixed sleep guess.

All storage is isolated under a per-test ``tempfile.mkdtemp()`` directory;
nothing here touches real ``LOCALAPPDATA`` or a real broker.
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

# Named fixture helper (test-maintenance only, no Phase 5 behavior change):
# every proposal fixture in this file must remain unexpired at the moment
# it reaches build_order_intent's real-wall-clock expiry check. There is no
# controlled-clock seam here -- every worker below is a genuinely separate
# OS process launched via subprocess, so an in-process fake clock could not
# be shared with it even if one existed. One durable, far-future timestamp,
# referenced consistently from this single named constant, replaces the
# scattered hardcoded "2026-08-01T13:00:00.000000Z" values that were valid
# when this file was written but have since passed real wall-clock time.
FIXTURE_PROPOSAL_EXPIRES_AT_UTC = "2035-08-01T13:00:00.000000Z"

_CREATE_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app import mode_service as ms
from trading_lab_app import mt5_execution_adapter as maa
from trading_lab_app import mt5_execution_journal as mej
from trading_lab_app import mt5_execution_service as mes
from trading_lab_app import signal_data as sd

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])
mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset({{"SMA-001"}})

proposal = sd.build_signal_proposal(
    created_at_utc="2026-08-01T11:00:00.000000Z",
    observed_at_utc="2026-08-01T11:00:00.000000Z",
    expires_at_utc={expires_at_utc!r},
    instrument="XAUUSD", side="BUY", entry_type="ENTRY_ZONE",
    entry_zone_lower="1899", entry_zone_upper="1899", stop_loss="1895",
    targets=["1902", "1905", "1908", "1911"], target_allocations_percent=["25", "25", "25", "25"],
    confidence_score=80, evidence_quality_status="GOVERNED", invalidation_reason="structure break",
    wait_reason=None, beginner_explanation="regression-worker",
    strategy_basis_ids=["BASIS-1"], research_basis_ids=["BASIS-1"],
    market_data_observation_id="tle_" + "0" * 32, news_observation_ids=[], economic_event_observation_ids=[],
    risk_percent="0.5", strategy_id="SMA-001", strategy_version="1.0.0", broker_native_instrument="XAUUSD",
    regime_classification="TREND_UP", feature_snapshot_hash="0" * 64,
    data_quality_result={{"status": "PASS", "reasons": []}},
    news_event_risk_result={{"status": "PASS", "reasons": [], "evidence_ids": []}},
    confidence_calibration_source="PHASE4_COMPONENT_SCORE_UNCALIBRATED_V1", confidence_status="UNCALIBRATED_HEURISTIC",
    explanation="regression-worker fixture", rejection_reasons=[],
    model_rule_versions={{"strategy_version": "1.0.0", "risk_engine_version": "1.0.0", "pipeline_version": "1.0.0"}},
    role_results={{key: {{"status": "PASS", "reasons": []}} for key in sd.ROLE_NAMES}},
    candidate_quantity="0.01", independent_quantity="0.01", maximum_spread="50",
    active_risk_policy_hash="1" * 64, operating_mode="MT5_DEMO_MANUAL", sample_label="SYNTHETIC_PAPER",
)

mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
mode_svc.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
adapter = maa.FakeExecutionAdapter()
adapter.set_symbol("XAUUSD")
adapter.account.update({{"login": 900100100, "company": "Fake Demo Broker Ltd", "server": "FakeDemo-Server"}})
fingerprint = mes.AccountFingerprintConfiguration(login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server")

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=TEMP / "journal.json"))
svc = mes.ExecutionService(adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint)

error = None
intent = None
try:
    intent = svc.build_order_intent(proposal)
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)

result = {{
    "worker_id": WORKER_ID,
    "order_intent_id": intent["order_intent_id"] if intent else None,
    "error": error,
    "adapter_calls": len(adapter.calls),
}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result), encoding="utf-8")
'''

_SEND_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app import mode_service as ms
from trading_lab_app import mt5_execution_adapter as maa
from trading_lab_app import mt5_execution_journal as mej
from trading_lab_app import mt5_execution_service as mes

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

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=TEMP / "journal.json"))
svc = mes.ExecutionService(adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint)

error = None
send_outcome = None
try:
    result = svc.confirm_and_send(shared["order_intent_id"], shared["challenge_code"], actor_channel="LOCAL_OPERATOR")
    send_outcome = result["send_result"]["outcome"]
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)

result_doc = {{
    "worker_id": WORKER_ID,
    "send_outcome": send_outcome,
    "error": error,
    "adapter_order_send_calls": len([c for c in adapter.calls if c[0] == "order_send"]),
}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result_doc), encoding="utf-8")
'''


def _wait_for(path, timeout=READY_TIMEOUT_SECONDS):
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() >= deadline:
            raise TimeoutError("timed out waiting for {}".format(path))
        time.sleep(READY_POLL_INTERVAL_SECONDS)


def _run_two_workers(source_template, temp_dir, extra_setup=None):
    worker_path = temp_dir / "worker.py"
    worker_path.write_text(
        source_template.format(
            app_dir=str(APP_DIRECTORY),
            expires_at_utc=FIXTURE_PROPOSAL_EXPIRES_AT_UTC,
        ),
        encoding="utf-8",
    )
    if extra_setup is not None:
        extra_setup(temp_dir)

    procs = [
        subprocess.Popen([sys.executable, "-B", str(worker_path), str(worker_id), str(temp_dir)])
        for worker_id in (1, 2)
    ]
    # Deterministic synchronization: wait for BOTH workers to signal they
    # have finished setup and are blocked polling for "go" before firing
    # the starting gun -- never a fixed sleep guess.
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


class ConcurrentFirstCreationTests(unittest.TestCase):
    def test_two_processes_racing_build_order_intent_converge_on_one_intent(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            results = _run_two_workers(_CREATE_WORKER_SOURCE, temp_dir)

        self.assertIsNone(results[1]["error"])
        self.assertIsNone(results[2]["error"])
        self.assertEqual(results[1]["order_intent_id"], results[2]["order_intent_id"])
        self.assertEqual(results[1]["adapter_calls"], 0)
        self.assertEqual(results[2]["adapter_calls"], 0)

    def test_journal_has_exactly_one_created_event_after_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            _run_two_workers(_CREATE_WORKER_SOURCE, temp_dir)
            with open(temp_dir / "journal.json", encoding="utf-8") as handle:
                document = json.load(handle)
        events = document["journal"]["events"]
        created = [e for e in events if e["event_type"] == "ORDER_INTENT_CREATED"]
        reused = [e for e in events if e["event_type"] == "ORDER_INTENT_REUSED"]
        self.assertEqual(len(created), 1)
        self.assertEqual(len(reused), 1)
        self.assertEqual(
            created[0]["payload"]["intent"]["order_intent_id"],
            reused[0]["payload"]["intent"]["order_intent_id"],
        )

    def test_journal_is_valid_hash_chain_after_race(self):
        import trading_lab_app.mt5_execution_journal as mej
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            _run_two_workers(_CREATE_WORKER_SOURCE, temp_dir)
            writer = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=temp_dir / "journal.json"))
        self.assertEqual(writer.startup_diagnostic_code, "OK")

    def test_no_lock_file_remains_after_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            _run_two_workers(_CREATE_WORKER_SOURCE, temp_dir)
            lock_files = list(temp_dir.glob("*.lock"))
        self.assertEqual(lock_files, [])


class ConcurrentSendTests(unittest.TestCase):
    def _prepare_confirmed_intent(self, temp_dir):
        """Single-process setup (not racy): build, check, and request
        confirmation for one intent, sharing the durable journal path the
        two racing worker processes will use afterward."""
        import trading_lab_app.mode_service as ms
        import trading_lab_app.mt5_execution_adapter as maa
        import trading_lab_app.mt5_execution_journal as mej
        import trading_lab_app.mt5_execution_service as mes
        import trading_lab_app.signal_data as sd

        original_geometry = mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES
        self.addCleanup(setattr, mes, "EXECUTION_GEOMETRY_APPROVED_STRATEGIES", original_geometry)
        mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset({"SMA-001"})
        proposal = sd.build_signal_proposal(
            created_at_utc="2026-08-01T11:00:00.000000Z",
            observed_at_utc="2026-08-01T11:00:00.000000Z",
            expires_at_utc=FIXTURE_PROPOSAL_EXPIRES_AT_UTC,
            instrument="XAUUSD", side="BUY", entry_type="ENTRY_ZONE",
            entry_zone_lower="1899", entry_zone_upper="1899", stop_loss="1895",
            targets=["1902", "1905", "1908", "1911"], target_allocations_percent=["25", "25", "25", "25"],
            confidence_score=80, evidence_quality_status="GOVERNED", invalidation_reason="structure break",
            wait_reason=None, beginner_explanation="send-race-setup",
            strategy_basis_ids=["BASIS-1"], research_basis_ids=["BASIS-1"],
            market_data_observation_id="tle_" + "0" * 32, news_observation_ids=[], economic_event_observation_ids=[],
            risk_percent="0.5", strategy_id="SMA-001", strategy_version="1.0.0", broker_native_instrument="XAUUSD",
            regime_classification="TREND_UP", feature_snapshot_hash="0" * 64,
            data_quality_result={"status": "PASS", "reasons": []},
            news_event_risk_result={"status": "PASS", "reasons": [], "evidence_ids": []},
            confidence_calibration_source="PHASE4_COMPONENT_SCORE_UNCALIBRATED_V1", confidence_status="UNCALIBRATED_HEURISTIC",
            explanation="send-race-setup fixture", rejection_reasons=[],
            model_rule_versions={"strategy_version": "1.0.0", "risk_engine_version": "1.0.0", "pipeline_version": "1.0.0"},
            role_results={key: {"status": "PASS", "reasons": []} for key in sd.ROLE_NAMES},
            candidate_quantity="0.01", independent_quantity="0.01", maximum_spread="50",
            active_risk_policy_hash="1" * 64, operating_mode="MT5_DEMO_MANUAL", sample_label="SYNTHETIC_PAPER",
        )
        mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
        mode_svc.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
        adapter = maa.FakeExecutionAdapter()
        adapter.set_symbol("XAUUSD")
        adapter.account.update({"login": 900100100, "company": "Fake Demo Broker Ltd", "server": "FakeDemo-Server"})
        fingerprint = mes.AccountFingerprintConfiguration(login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server")
        journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=temp_dir / "journal.json"))
        svc = mes.ExecutionService(adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint)

        intent = svc.build_order_intent(proposal)
        svc.order_check(intent["order_intent_id"])
        challenge = svc.request_confirmation(intent["order_intent_id"])
        with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
            json.dump({
                "order_intent_id": intent["order_intent_id"],
                "challenge_code": challenge["challenge_code"],
            }, handle)
        return intent["order_intent_id"]

    def test_two_processes_racing_confirm_and_send_send_at_most_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            self._prepare_confirmed_intent(temp_dir)
            results = _run_two_workers(_SEND_WORKER_SOURCE, temp_dir)

        successes = [r for r in results.values() if r["error"] is None and r["send_outcome"] == "FILLED"]
        failures = [r for r in results.values() if r["error"] is not None]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        total_adapter_send_calls = sum(r["adapter_order_send_calls"] for r in results.values())
        self.assertEqual(total_adapter_send_calls, 1)
        # MANUAL_CONFIRMATION_ACCEPTED is always persisted (under the same
        # lock) immediately before ORDER_SEND_REQUESTED, so a racing loser
        # that reloads after the winner releases the lock deterministically
        # sees the confirmation already consumed -- it never reaches the
        # separate DUPLICATE_SEND_BLOCKED check.
        self.assertIn("CONFIRMATION_ALREADY_CONSUMED", failures[0]["error"])

    def test_journal_has_exactly_one_send_reservation_after_race(self):
        import trading_lab_app.mt5_execution_journal as mej
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            self._prepare_confirmed_intent(temp_dir)
            _run_two_workers(_SEND_WORKER_SOURCE, temp_dir)
            with open(temp_dir / "journal.json", encoding="utf-8") as handle:
                document = json.load(handle)
        events = document["journal"]["events"]
        requested = [e for e in events if e["event_type"] == "ORDER_SEND_REQUESTED"]
        results_events = [e for e in events if e["event_type"] == "ORDER_SEND_RESULT"]
        self.assertEqual(len(requested), 1)
        self.assertEqual(len(results_events), 1)
        writer = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=temp_dir / "journal.json"))
        self.assertEqual(writer.startup_diagnostic_code, "OK")

    def test_restart_after_race_still_blocks_further_submission(self):
        import trading_lab_app.mode_service as ms
        import trading_lab_app.mt5_execution_adapter as maa
        import trading_lab_app.mt5_execution_journal as mej
        import trading_lab_app.mt5_execution_service as mes

        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            self._prepare_confirmed_intent(temp_dir)
            _run_two_workers(_SEND_WORKER_SOURCE, temp_dir)

            with open(temp_dir / "shared_state.json", encoding="utf-8") as handle:
                shared = json.load(handle)

            mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
            mode_svc.request_transition("MT5_DEMO_MANUAL", actor="t", actor_channel="LOCAL_OPERATOR")
            adapter = maa.FakeExecutionAdapter()
            adapter.set_symbol("XAUUSD")
            adapter.account.update({"login": 900100100, "company": "Fake Demo Broker Ltd", "server": "FakeDemo-Server"})
            fingerprint = mes.AccountFingerprintConfiguration(login=900100100, company="Fake Demo Broker Ltd", server="FakeDemo-Server")
            journal = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=temp_dir / "journal.json"))
            svc = mes.ExecutionService(adapter=adapter, mode_service=mode_svc, journal=journal, account_fingerprint=fingerprint)

            with self.assertRaises(mes.ExecutionServiceError) as ctx:
                svc.confirm_and_send(shared["order_intent_id"], shared["challenge_code"], actor_channel="LOCAL_OPERATOR")
            self.assertIn(ctx.exception.reason_code, ("DUPLICATE_SEND_BLOCKED", "CONFIRMATION_ALREADY_CONSUMED", "INTENT_ALREADY_TERMINAL"))
            self.assertEqual(len([c for c in adapter.calls if c[0] == "order_send"]), 0)


if __name__ == "__main__":
    unittest.main()
