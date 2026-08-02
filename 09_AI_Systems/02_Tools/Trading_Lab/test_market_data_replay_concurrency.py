"""Regression/acceptance tests for TRL-R2-011 Market Data Fabric and Replay
V0 cross-process locking (contract Section 25 category G/I). Exercises
``market_data_replay_journal._CrossProcessFileLock`` /
``MarketDataReplayJournalWriter.acquire_mutation_lock`` using real, separate
worker processes launched via ``subprocess`` -- a plain in-process
``threading.Lock`` could not catch a missing cross-process critical
section, so these tests deliberately do not simulate concurrency with
sequential objects in one process. Synchronization between workers uses
readiness-marker files polled with a bounded timeout, never a fixed sleep
guess -- mirroring ``test_mt5_execution_concurrency.py`` exactly.

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

import mdr_test_support as support

APP_DIRECTORY = support.APP_DIRECTORY
READY_POLL_INTERVAL_SECONDS = 0.01
READY_TIMEOUT_SECONDS = 30.0

_IMPORT_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app import market_data_replay_journal as mdj
from trading_lab_app import market_data_replay_service as mdrsvc
from trading_lab_app import market_data_replay_storage as mds

class FakeMode:
    current_mode = "RESEARCH"
    def has_capability(self, cap):
        return cap == "market_data_research"

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])

journal = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=TEMP / "journal.json"))
storage = mds.LocalDatasetStorage(root=TEMP / "datasets")
service = mdrsvc.MarketDataReplayService(mode_service=FakeMode(), journal=journal, storage=storage)

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

error = None
dataset_id = None
try:
    manifest = service.import_market_data(str(TEMP / "shared.csv"), "SYNTHETIC_FIXTURE", "race-ref")
    dataset_id = manifest["dataset_id"]
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)

result = {{"worker_id": WORKER_ID, "dataset_id": dataset_id, "error": error}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result), encoding="utf-8")
'''

_INVALID_IMPORT_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app import market_data_replay_journal as mdj
from trading_lab_app import market_data_replay_service as mdrsvc
from trading_lab_app import market_data_replay_storage as mds

class FakeMode:
    current_mode = "RESEARCH"
    def has_capability(self, cap):
        return cap == "market_data_research"

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])

journal = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=TEMP / "journal.json"))
storage = mds.LocalDatasetStorage(root=TEMP / "datasets")
service = mdrsvc.MarketDataReplayService(mode_service=FakeMode(), journal=journal, storage=storage)

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

error = None
reason_code = None
try:
    service.import_market_data(str(TEMP / "invalid.csv"), "SYNTHETIC_FIXTURE", "race-ref")
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)
    reason_code = getattr(exc, "reason_code", None)

result = {{"worker_id": WORKER_ID, "error": error, "reason_code": reason_code}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result), encoding="utf-8")
'''

_SESSION_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app import market_data_replay_journal as mdj
from trading_lab_app import market_data_replay_service as mdrsvc
from trading_lab_app import market_data_replay_storage as mds

class FakeMode:
    current_mode = "RESEARCH"
    def has_capability(self, cap):
        return cap == "market_data_research"

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])

with open(TEMP / "shared_state.json", encoding="utf-8") as handle:
    shared = json.load(handle)

journal = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=TEMP / "journal.json"))
storage = mds.LocalDatasetStorage(root=TEMP / "datasets")
service = mdrsvc.MarketDataReplayService(mode_service=FakeMode(), journal=journal, storage=storage)

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

error = None
replay_session_id = None
try:
    session = service.create_replay_session(shared["dataset_id"], 0, shared["bar_count"] - 1, 1)
    replay_session_id = session["replay_session_id"]
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)

result = {{"worker_id": WORKER_ID, "replay_session_id": replay_session_id, "error": error}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result), encoding="utf-8")
'''

_REPLAY_NEXT_WORKER_SOURCE = r'''
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app import market_data_replay_journal as mdj
from trading_lab_app import market_data_replay_service as mdrsvc
from trading_lab_app import market_data_replay_storage as mds

class FakeMode:
    current_mode = "RESEARCH"
    def has_capability(self, cap):
        return cap == "market_data_research"

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])

with open(TEMP / "shared_state.json", encoding="utf-8") as handle:
    shared = json.load(handle)

journal = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=TEMP / "journal.json"))
storage = mds.LocalDatasetStorage(root=TEMP / "datasets")
service = mdrsvc.MarketDataReplayService(mode_service=FakeMode(), journal=journal, storage=storage)

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

error = None
current_index = None
try:
    projection = service.replay_next(shared["replay_session_id"])
    current_index = projection["current_index"]
except Exception as exc:
    error = "{{}}: {{}}".format(type(exc).__name__, exc)

result = {{"worker_id": WORKER_ID, "current_index": current_index, "error": error}}
(TEMP / ("result-%s.json" % WORKER_ID)).write_text(json.dumps(result), encoding="utf-8")
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


class ConcurrentImportTests(unittest.TestCase):
    def test_two_processes_racing_identical_import_converge_on_one_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "shared.csv").write_bytes(support.build_csv_bytes(bar_count=6))
            results = _run_two_workers(_IMPORT_WORKER_SOURCE, temp_dir)

        self.assertIsNone(results[1]["error"])
        self.assertIsNone(results[2]["error"])
        self.assertEqual(results[1]["dataset_id"], results[2]["dataset_id"])

    def test_journal_has_exactly_one_imported_and_one_reused_event_after_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "shared.csv").write_bytes(support.build_csv_bytes(bar_count=6))
            _run_two_workers(_IMPORT_WORKER_SOURCE, temp_dir)
            with open(temp_dir / "journal.json", encoding="utf-8") as handle:
                document = json.load(handle)
        events = document["journal"]["events"]
        imported = [e for e in events if e["event_type"] == "MARKET_DATASET_IMPORTED"]
        reused = [e for e in events if e["event_type"] == "MARKET_DATASET_REUSED"]
        self.assertEqual(len(imported), 1)
        self.assertEqual(len(reused), 1)

    def test_journal_is_valid_hash_chain_after_import_race(self):
        from trading_lab_app import market_data_replay_journal as mdj
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "shared.csv").write_bytes(support.build_csv_bytes(bar_count=6))
            _run_two_workers(_IMPORT_WORKER_SOURCE, temp_dir)
            writer = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=temp_dir / "journal.json"))
        self.assertEqual(writer.startup_diagnostic_code, "OK")

    def test_exactly_one_dataset_storage_file_after_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "shared.csv").write_bytes(support.build_csv_bytes(bar_count=6))
            _run_two_workers(_IMPORT_WORKER_SOURCE, temp_dir)
            files = list((temp_dir / "datasets").glob("*.json"))
        self.assertEqual(len(files), 1)

    def test_no_lock_file_remains_after_import_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "shared.csv").write_bytes(support.build_csv_bytes(bar_count=6))
            _run_two_workers(_IMPORT_WORKER_SOURCE, temp_dir)
            lock_files = list(temp_dir.glob("*.lock"))
        self.assertEqual(lock_files, [])


class ConcurrentInvalidImportTests(unittest.TestCase):
    """Founder-review correction, Section 6 item 3: two genuinely separate
    OS processes racing an identical *invalid* import must each still
    record their own governed rejection under the authoritative lock --
    no lost event, no malformed hash chain, no leftover lock file."""

    def test_two_processes_racing_invalid_import_both_record_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "invalid.csv").write_bytes((support.mdd.CSV_HEADER + "\nnot,a,valid,row\n").encode("utf-8"))
            results = _run_two_workers(_INVALID_IMPORT_WORKER_SOURCE, temp_dir)
        self.assertIsNotNone(results[1]["error"])
        self.assertIsNotNone(results[2]["error"])
        self.assertEqual(results[1]["reason_code"], "MARKET_DATA_CSV_SHAPE_INVALID")
        self.assertEqual(results[2]["reason_code"], "MARKET_DATA_CSV_SHAPE_INVALID")

    def test_journal_has_exactly_two_rejected_events_no_lost_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "invalid.csv").write_bytes((support.mdd.CSV_HEADER + "\nnot,a,valid,row\n").encode("utf-8"))
            _run_two_workers(_INVALID_IMPORT_WORKER_SOURCE, temp_dir)
            with open(temp_dir / "journal.json", encoding="utf-8") as handle:
                document = json.load(handle)
        events = document["journal"]["events"]
        rejected = [e for e in events if e["event_type"] == "MARKET_DATASET_REJECTED"]
        self.assertEqual(len(rejected), 2)
        sequence_numbers = sorted(e["sequence_number"] for e in rejected)
        self.assertEqual(sequence_numbers, [1, 2])

    def test_journal_is_valid_hash_chain_after_invalid_import_race(self):
        from trading_lab_app import market_data_replay_journal as mdj
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "invalid.csv").write_bytes((support.mdd.CSV_HEADER + "\nnot,a,valid,row\n").encode("utf-8"))
            _run_two_workers(_INVALID_IMPORT_WORKER_SOURCE, temp_dir)
            writer = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=temp_dir / "journal.json"))
        self.assertEqual(writer.startup_diagnostic_code, "OK")

    def test_no_lock_file_remains_after_invalid_import_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "invalid.csv").write_bytes((support.mdd.CSV_HEADER + "\nnot,a,valid,row\n").encode("utf-8"))
            _run_two_workers(_INVALID_IMPORT_WORKER_SOURCE, temp_dir)
            lock_files = list(temp_dir.glob("*.lock"))
        self.assertEqual(lock_files, [])

    def test_no_dataset_storage_file_created_by_invalid_import_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            (temp_dir / "invalid.csv").write_bytes((support.mdd.CSV_HEADER + "\nnot,a,valid,row\n").encode("utf-8"))
            _run_two_workers(_INVALID_IMPORT_WORKER_SOURCE, temp_dir)
            dataset_dir = temp_dir / "datasets"
            files = list(dataset_dir.glob("*.json")) if dataset_dir.exists() else []
        self.assertEqual(files, [])


class ConcurrentReplaySessionTests(unittest.TestCase):
    def _seed_dataset(self, temp_dir):
        from trading_lab_app import market_data_replay_journal as mdj
        from trading_lab_app import market_data_replay_service as mdrsvc
        from trading_lab_app import market_data_replay_storage as mds

        class FakeMode:
            current_mode = "RESEARCH"

            def has_capability(self, cap):
                return cap == "market_data_research"

        csv_path = temp_dir / "shared.csv"
        csv_path.write_bytes(support.build_csv_bytes(bar_count=6))
        journal = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=temp_dir / "journal.json"))
        storage = mds.LocalDatasetStorage(root=temp_dir / "datasets")
        service = mdrsvc.MarketDataReplayService(mode_service=FakeMode(), journal=journal, storage=storage)
        manifest = service.import_market_data(str(csv_path), "SYNTHETIC_FIXTURE", "race-ref")
        with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
            json.dump({"dataset_id": manifest["dataset_id"], "bar_count": manifest["bar_count"]}, handle)
        return manifest

    def test_two_processes_racing_session_creation_converge_on_one_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            self._seed_dataset(temp_dir)
            results = _run_two_workers(_SESSION_WORKER_SOURCE, temp_dir)
        self.assertIsNone(results[1]["error"])
        self.assertIsNone(results[2]["error"])
        self.assertEqual(results[1]["replay_session_id"], results[2]["replay_session_id"])

    def test_journal_has_exactly_one_created_and_one_reused_session_event(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            self._seed_dataset(temp_dir)
            _run_two_workers(_SESSION_WORKER_SOURCE, temp_dir)
            with open(temp_dir / "journal.json", encoding="utf-8") as handle:
                document = json.load(handle)
        events = document["journal"]["events"]
        created = [e for e in events if e["event_type"] == "REPLAY_SESSION_CREATED"]
        reused = [e for e in events if e["event_type"] == "REPLAY_SESSION_REUSED"]
        self.assertEqual(len(created), 1)
        self.assertEqual(len(reused), 1)


class ConcurrentReplayNextTests(unittest.TestCase):
    def _seed_session(self, temp_dir):
        from trading_lab_app import market_data_replay_journal as mdj
        from trading_lab_app import market_data_replay_service as mdrsvc
        from trading_lab_app import market_data_replay_storage as mds

        class FakeMode:
            current_mode = "RESEARCH"

            def has_capability(self, cap):
                return cap == "market_data_research"

        csv_path = temp_dir / "shared.csv"
        csv_path.write_bytes(support.build_csv_bytes(bar_count=10))
        journal = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=temp_dir / "journal.json"))
        storage = mds.LocalDatasetStorage(root=temp_dir / "datasets")
        service = mdrsvc.MarketDataReplayService(mode_service=FakeMode(), journal=journal, storage=storage)
        manifest = service.import_market_data(str(csv_path), "SYNTHETIC_FIXTURE", "race-ref")
        session = service.create_replay_session(manifest["dataset_id"], 0, manifest["bar_count"] - 1, 1)
        with open(temp_dir / "shared_state.json", "w", encoding="utf-8") as handle:
            json.dump({"replay_session_id": session["replay_session_id"]}, handle)
        return session

    def test_two_processes_racing_replay_next_no_duplicate_step(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            self._seed_session(temp_dir)
            results = _run_two_workers(_REPLAY_NEXT_WORKER_SOURCE, temp_dir)
            with open(temp_dir / "journal.json", encoding="utf-8") as handle:
                document = json.load(handle)

        self.assertIsNone(results[1]["error"])
        self.assertIsNone(results[2]["error"])
        events = document["journal"]["events"]
        steps = [e for e in events if e["event_type"] == "REPLAY_STEP_RECORDED"]
        snapshots = [e for e in events if e["event_type"] == "REPLAY_SNAPSHOT_RECORDED"]
        self.assertEqual(len(steps), 2)
        self.assertEqual(len(snapshots), 2)
        sequence_numbers = sorted(step["payload"]["step"]["sequence_number"] for step in steps)
        self.assertEqual(sequence_numbers, [1, 2])
        current_indexes = sorted({results[1]["current_index"], results[2]["current_index"]})
        self.assertEqual(current_indexes, [0, 1])

    def test_no_lock_file_remains_after_replay_next_race(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            self._seed_session(temp_dir)
            _run_two_workers(_REPLAY_NEXT_WORKER_SOURCE, temp_dir)
            lock_files = list(temp_dir.glob("*.lock"))
        self.assertEqual(lock_files, [])


if __name__ == "__main__":
    unittest.main()
