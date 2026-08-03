"""Real separate-process concurrency tests for ALSAKKAF SCALPING
(TRL-R2-012 contract Section 15 -- cross-process owner-token locking).

Exercises ``alsakkaf_scalping_journal._CrossProcessFileLock`` /
``ScalpingJournalWriter.acquire_mutation_lock`` using real, separate
worker processes launched via ``subprocess`` -- a plain in-process
``threading.Lock`` could not catch a missing cross-process critical
section. Synchronization between workers uses readiness-marker files
polled with a bounded timeout, never a fixed sleep guess, mirroring
``test_market_data_replay_concurrency.py`` exactly.
"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

APP_DIRECTORY = str(Path(__file__).resolve().parent)
READY_POLL_INTERVAL_SECONDS = 0.01
READY_TIMEOUT_SECONDS = 30.0

_WORKER_SOURCE = r'''
import sys
import time
from pathlib import Path

sys.path.insert(0, {app_dir!r})

from trading_lab_app.alsakkaf_scalping_journal import LocalScalpingJournalStore, ScalpingJournalWriter

WORKER_ID = sys.argv[1]
TEMP = Path(sys.argv[2])

writer = ScalpingJournalWriter(store=LocalScalpingJournalStore(path=TEMP / "journal.json"))

(TEMP / ("ready-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
go_path = TEMP / "go.signal"
while not go_path.exists():
    time.sleep(0.0005)

with writer.acquire_mutation_lock() as locked_writer:
    locked_writer.append("SCALPING_STATE_CHANGED", {{"from_state": "OFF", "to_state": "ANALYZE_ONLY"}})

(TEMP / ("done-%s" % WORKER_ID)).write_text("1", encoding="utf-8")
'''


def _wait_for(paths, timeout=READY_TIMEOUT_SECONDS):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if all(path.exists() for path in paths):
            return True
        time.sleep(READY_POLL_INTERVAL_SECONDS)
    return False


class JournalLockConcurrencyTests(unittest.TestCase):
    def test_two_processes_racing_to_append_never_corrupt_the_chain(self):
        temp_directory = Path(tempfile.mkdtemp())
        worker_script = temp_directory / "worker.py"
        worker_script.write_text(_WORKER_SOURCE.format(app_dir=APP_DIRECTORY), encoding="utf-8")

        processes = []
        ready_paths = []
        for worker_id in ("a", "b"):
            ready_path = temp_directory / ("ready-%s" % worker_id)
            ready_paths.append(ready_path)
            process = subprocess.Popen(
                [sys.executable, "-B", "-W", "error", str(worker_script), worker_id, str(temp_directory)],
            )
            processes.append(process)

        try:
            self.assertTrue(_wait_for(ready_paths), "workers did not become ready in time")
            (temp_directory / "go.signal").write_text("1", encoding="utf-8")
            for process in processes:
                self.assertEqual(process.wait(timeout=READY_TIMEOUT_SECONDS), 0)
            done_paths = [temp_directory / ("done-%s" % worker_id) for worker_id in ("a", "b")]
            self.assertTrue(_wait_for(done_paths))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()

        from trading_lab_app.alsakkaf_scalping_journal import LocalScalpingJournalStore, ScalpingJournalWriter

        final_writer = ScalpingJournalWriter(store=LocalScalpingJournalStore(path=temp_directory / "journal.json"))
        self.assertEqual(final_writer.startup_diagnostic_code, "OK")
        events = [event for event in final_writer.events if event["event_type"] == "SCALPING_STATE_CHANGED"]
        self.assertEqual(len(events), 2)
        sequences = [event["append_sequence"] for event in events]
        self.assertEqual(sorted(sequences), [1, 2])


if __name__ == "__main__":
    unittest.main()
