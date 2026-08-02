"""True separate-process concurrency regression tests for the TRL-R2-010
Market Intelligence V0 service.

Mirrors test_basket_execution_concurrency.py's exact house style: real,
separate OS worker processes launched via subprocess (never threads, never
sequential in-process calls, never a mocked lock), synchronized with
readiness-marker files polled with a bounded timeout, never a fixed sleep
guess. All storage is isolated under a per-test tempfile.mkdtemp()
directory; nothing here touches real LOCALAPPDATA.
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

_ANALYZE_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})
sys.path.insert(0, {trading_lab_dir!r})

from trading_lab_app import mode_service as ms
from trading_lab_app import market_intelligence_service as svc
from trading_lab_app.market_intelligence_journal import MarketIntelligenceJournalWriter, LocalMarketIntelligenceJournalStore

import mi_test_support as support

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])

mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
mode_svc.request_transition("RESEARCH", actor="t", actor_channel="LOCAL_OPERATOR")
journal = MarketIntelligenceJournalWriter(store=LocalMarketIntelligenceJournalStore(path=TEMP / "mi-journal.json"))
service = svc.MarketIntelligenceService(mode_service=mode_svc, journal=journal)

envelope_path = support.write_temp_json(support.analysis_envelope(), directory=str(TEMP))

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

error = None
opportunity_id = None
decision_status = None
try:
    result = service.analyze_market_snapshot(envelope_path)
    opportunity_id = result["opportunity"]["opportunity_id"]
    decision_status = result["decision"]["final_status"]
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)

result_doc = {{"worker_id": WORKER_ID, "opportunity_id": opportunity_id, "decision_status": decision_status, "error": error}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result_doc), encoding="utf-8")
'''

_PREVIEW_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})
sys.path.insert(0, {trading_lab_dir!r})

from trading_lab_app import mode_service as ms
from trading_lab_app import market_intelligence_service as svc
from trading_lab_app.market_intelligence_journal import MarketIntelligenceJournalWriter, LocalMarketIntelligenceJournalStore

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])

with open(TEMP / "shared_state.json", encoding="utf-8") as handle:
    shared = json.load(handle)

mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
mode_svc.request_transition("RESEARCH", actor="t", actor_channel="LOCAL_OPERATOR")
journal = MarketIntelligenceJournalWriter(store=LocalMarketIntelligenceJournalStore(path=TEMP / "mi-journal.json"))
service = svc.MarketIntelligenceService(mode_service=mode_svc, journal=journal)

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

error = None
preview_id = None
try:
    preview = service.preview_opportunity_basket(shared["opportunity_id"])
    preview_id = preview["preview_id"]
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)

result_doc = {{"worker_id": WORKER_ID, "preview_id": preview_id, "error": error}}
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
    worker_path.write_text(
        source_template.format(app_dir=str(APP_DIRECTORY), trading_lab_dir=str(APP_DIRECTORY)),
        encoding="utf-8",
    )
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


class TrueCrossProcessOpportunityCreationTests(unittest.TestCase):
    def test_two_processes_racing_analyze_produce_one_created_one_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            results = _run_two_workers(_ANALYZE_WORKER_SOURCE, temp_dir)
            self.assertIsNone(results[1]["error"], results[1])
            self.assertIsNone(results[2]["error"], results[2])
            self.assertEqual(results[1]["opportunity_id"], results[2]["opportunity_id"])
            self.assertEqual(results[1]["decision_status"], results[2]["decision_status"])

            from trading_lab_app.market_intelligence_journal import MarketIntelligenceJournalWriter, LocalMarketIntelligenceJournalStore
            journal = MarketIntelligenceJournalWriter(store=LocalMarketIntelligenceJournalStore(path=temp_dir / "mi-journal.json"))
            created = [event for event in journal.events if event["event_type"] == "MI_OPPORTUNITY_CREATED"]
            reused = [event for event in journal.events if event["event_type"] == "MI_OPPORTUNITY_REUSED"]
            self.assertEqual(len(created), 1)
            self.assertEqual(len(reused), 1)

            lock_path = (temp_dir / "mi-journal.json").with_suffix(".json.lock")
            self.assertFalse(lock_path.exists())


class TrueCrossProcessPreviewCreationTests(unittest.TestCase):
    def test_two_processes_racing_preview_produce_exactly_one_preview(self):
        with tempfile.TemporaryDirectory() as directory:
            temp_dir = Path(directory)
            import trading_lab_app.mode_service as ms
            import trading_lab_app.market_intelligence_service as svc
            from trading_lab_app.market_intelligence_journal import MarketIntelligenceJournalWriter, LocalMarketIntelligenceJournalStore
            import mi_test_support as support

            mode_svc = ms.in_memory_mode_service(subsystem_builder=lambda m: None)
            mode_svc.request_transition("RESEARCH", actor="t", actor_channel="LOCAL_OPERATOR")
            journal = MarketIntelligenceJournalWriter(store=LocalMarketIntelligenceJournalStore(path=temp_dir / "mi-journal.json"))
            service = svc.MarketIntelligenceService(mode_service=mode_svc, journal=journal)
            path = support.write_temp_json(support.analysis_envelope(), directory=str(temp_dir))
            result = service.analyze_market_snapshot(path)
            self.assertEqual(result["decision"]["final_status"], "TRADE_CANDIDATE")
            (temp_dir / "shared_state.json").write_text(
                json.dumps({"opportunity_id": result["opportunity"]["opportunity_id"]}), encoding="utf-8",
            )

            results = _run_two_workers(_PREVIEW_WORKER_SOURCE, temp_dir)
            self.assertIsNone(results[1]["error"], results[1])
            self.assertIsNone(results[2]["error"], results[2])
            self.assertEqual(results[1]["preview_id"], results[2]["preview_id"])

            journal2 = MarketIntelligenceJournalWriter(store=LocalMarketIntelligenceJournalStore(path=temp_dir / "mi-journal.json"))
            created = [event for event in journal2.events if event["event_type"] == "MI_BASKET_PREVIEW_CREATED"]
            self.assertEqual(len(created), 1)
            lock_path = (temp_dir / "mi-journal.json").with_suffix(".json.lock")
            self.assertFalse(lock_path.exists())


if __name__ == "__main__":
    unittest.main()
