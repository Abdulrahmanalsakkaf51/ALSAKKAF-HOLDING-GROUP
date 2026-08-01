"""Lock-safety tests for mt5_execution_journal.py's cross-process/in-process
locking primitives (added during the Founder concurrency-race correction).

All storage is isolated under per-test ``tempfile.mkdtemp()`` directories;
nothing here touches real LOCALAPPDATA.
"""

from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest import mock

from trading_lab_app import mt5_execution_journal as mej


class CrossProcessFileLockTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.lock_path = Path(self._tmp.name) / "journal.json.lock"

    def test_acquire_and_release_normal(self):
        lock = mej._CrossProcessFileLock(self.lock_path)
        with lock:
            self.assertTrue(self.lock_path.exists())
        self.assertFalse(self.lock_path.exists())

    def test_lock_released_after_exception(self):
        lock = mej._CrossProcessFileLock(self.lock_path)
        with self.assertRaises(ValueError):
            with lock:
                self.assertTrue(self.lock_path.exists())
                raise ValueError("simulated failure inside critical section")
        self.assertFalse(self.lock_path.exists())

    def test_second_lock_blocks_while_first_held(self):
        lock1 = mej._CrossProcessFileLock(self.lock_path)
        lock1.acquire()
        try:
            lock2 = mej._CrossProcessFileLock(self.lock_path)
            with self.assertRaises(mej.ExecutionJournalLockTimeout):
                lock2.acquire(timeout=0.2)
        finally:
            lock1.release()

    def test_timeout_fails_closed_no_lock_file_created_by_loser(self):
        lock1 = mej._CrossProcessFileLock(self.lock_path)
        lock1.acquire()
        try:
            lock2 = mej._CrossProcessFileLock(self.lock_path)
            with self.assertRaises(mej.ExecutionJournalLockTimeout):
                lock2.acquire(timeout=0.2)
            # The original holder's lock file must be untouched by the
            # losing acquire attempt.
            self.assertTrue(self.lock_path.exists())
            self.assertEqual(self.lock_path.read_bytes(), lock1._token)
        finally:
            lock1.release()

    def _abandon(self, lock):
        """Simulate a genuinely crashed/killed owning process: its lock
        file survives (nothing ran its cleanup) but the OS has already
        reclaimed its open handle, exactly as happens on real process
        termination on both Windows and POSIX. (On Windows in particular,
        a file cannot be unlinked while any handle to it — even one held
        by the *same* process — remains open, so accurately simulating
        "crashed" here means actually closing the handle, not merely
        leaving this test process holding it open.)"""
        import os
        os.close(lock._fd)
        lock._fd = None
        stale_time = time.time() - (mej.LOCK_STALE_SECONDS + 5)
        os.utime(self.lock_path, (stale_time, stale_time))

    def test_stale_lock_is_broken_and_reacquired(self):
        lock1 = mej._CrossProcessFileLock(self.lock_path)
        lock1.acquire()
        self._abandon(lock1)

        lock2 = mej._CrossProcessFileLock(self.lock_path)
        lock2.acquire(timeout=2.0)
        try:
            self.assertTrue(self.lock_path.exists())
            self.assertEqual(self.lock_path.read_bytes(), lock2._token)
        finally:
            lock2.release()

    def test_late_release_from_stale_owner_does_not_delete_new_owners_lock(self):
        # This is the exact bug class the Founder review flagged: an
        # original holder whose lock was broken as stale and re-acquired
        # by someone else must not blindly delete the new owner's lock
        # when it finally calls release().
        lock1 = mej._CrossProcessFileLock(self.lock_path)
        lock1.acquire()
        self._abandon(lock1)

        lock2 = mej._CrossProcessFileLock(self.lock_path)
        lock2.acquire(timeout=2.0)  # breaks lock1's stale file, acquires its own

        # lock1 (the original, now-stale owner) finally gets around to
        # releasing what it still believes is its own lock.
        lock1.release()

        # lock2's lock must still be intact and still owned by lock2.
        self.assertTrue(self.lock_path.exists())
        self.assertEqual(self.lock_path.read_bytes(), lock2._token)
        lock2.release()
        self.assertFalse(self.lock_path.exists())

    def test_no_lock_file_persists_after_clean_completion(self):
        with mej._CrossProcessFileLock(self.lock_path):
            pass
        self.assertFalse(self.lock_path.exists())


class InMemoryThreadLockTests(unittest.TestCase):
    def test_serializes_concurrent_threads(self):
        order = []
        lock_events = threading.Event()

        def worker(label):
            with mej._ThreadLock():
                order.append("{}-enter".format(label))
                time.sleep(0.05)
                order.append("{}-exit".format(label))

        t1 = threading.Thread(target=worker, args=("A",))
        t2 = threading.Thread(target=worker, args=("B",))
        t1.start()
        time.sleep(0.01)  # ensure t1 acquires first, deterministically
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        # Each thread's enter/exit pair must not interleave with the other's.
        self.assertEqual(order[0][2:], "enter")
        self.assertEqual(order[1][2:], "exit")
        self.assertEqual(order[0][0], order[1][0])

    def test_timeout_fails_closed(self):
        acquired_first = threading.Event()
        release_first = threading.Event()

        def holder():
            with mej._ThreadLock():
                acquired_first.set()
                release_first.wait(timeout=5)

        thread = threading.Thread(target=holder)
        thread.start()
        acquired_first.wait(timeout=5)
        try:
            with mock.patch.object(mej, "LOCK_ACQUIRE_TIMEOUT_SECONDS", 0.2):
                with self.assertRaises(mej.ExecutionJournalLockTimeout):
                    with mej._ThreadLock():
                        pass
        finally:
            release_first.set()
            thread.join(timeout=5)


class JournalWriterLockIntegrationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.journal_path = Path(self._tmp.name) / "journal.json"

    def test_reload_occurs_after_lock_acquisition(self):
        """A writer constructed before another writer persisted an event
        must see that event once it enters the locked section — proving
        the lock's reload-from-disk step, not a stale in-memory snapshot."""
        writer_a = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=self.journal_path))
        self.assertEqual(len(writer_a.events), 0)

        writer_b = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=self.journal_path))
        writer_b.append("ADAPTER_UNAVAILABLE", {"reason_code": "MT5_DEPENDENCY_MISSING"})

        # writer_a's in-memory snapshot is still stale (still 0 events) --
        # until it enters the locked section, which must reload first.
        self.assertEqual(len(writer_a.events), 0)
        with writer_a.acquire_creation_lock() as reloaded:
            self.assertEqual(len(reloaded.events), 1)

    def test_corrupted_journal_after_lock_acquisition_fails_closed(self):
        writer = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=self.journal_path))
        writer.append("ADAPTER_UNAVAILABLE", {"reason_code": "MT5_DEPENDENCY_MISSING"})

        # Corrupt the file directly on disk (simulating tampering/damage
        # between this writer's construction and its next locked access).
        import json
        with open(self.journal_path, encoding="utf-8") as handle:
            document = json.load(handle)
        document["journal"]["events"][0]["previous_event_hash"] = "f" * 64
        with open(self.journal_path, "w", encoding="utf-8") as handle:
            json.dump(document, handle)

        with writer.acquire_creation_lock() as reloaded:
            self.assertEqual(reloaded.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")
            self.assertEqual(len(reloaded.events), 0)

    def test_lock_files_removed_after_clean_completion(self):
        writer = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=self.journal_path))
        with writer.acquire_creation_lock():
            pass
        lock_files = list(Path(self._tmp.name).glob("*.lock"))
        self.assertEqual(lock_files, [])

    def test_in_memory_store_uses_thread_lock_not_file_lock(self):
        writer = mej.in_memory_journal_writer()
        with writer.acquire_creation_lock() as reloaded:
            self.assertEqual(len(reloaded.events), 0)
        lock_files = list(Path(self._tmp.name).glob("*.lock"))
        self.assertEqual(lock_files, [])

    def test_lock_timeout_fails_closed_without_any_write(self):
        holder = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=self.journal_path))
        cm = holder.acquire_creation_lock()
        cm.__enter__()
        try:
            waiter = mej.ExecutionJournalWriter(store=mej.LocalExecutionJournalStore(path=self.journal_path))
            with mock.patch.object(mej, "LOCK_ACQUIRE_TIMEOUT_SECONDS", 0.2):
                with self.assertRaises(mej.ExecutionJournalLockTimeout):
                    with waiter.acquire_creation_lock():
                        pass
            # No event was appended by the timed-out waiter.
            self.assertEqual(len(waiter.events), 0)
        finally:
            cm.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
