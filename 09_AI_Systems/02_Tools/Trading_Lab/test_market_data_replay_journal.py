"""Tests for TRL-R2-011 Market Data Fabric and Replay V0 -- journal module
(``market_data_replay_journal.py``). Covers contract Section 25 category F
(closed events, compact payloads, size/count bounds, hash chain, strict
schema, atomic persistence/batches, corruption fail-closed, lock timeout,
owner-token safety, no unlocked fallback, restart-safe projection).
"""

import tempfile
import threading
import unittest
from pathlib import Path

import mdr_test_support as support
from trading_lab_app import market_data_replay_data as mdd
from trading_lab_app import market_data_replay_journal as mdj


class InMemoryJournalTests(unittest.TestCase):
    def test_append_and_reload(self):
        writer = mdj.in_memory_mdr_journal_writer()
        writer.append("MARKET_DATASET_IMPORTED", {"dataset_id": "mds_" + "0" * 32}, occurred_at_utc="2026-01-01T00:00:00.000000Z")
        reloaded = mdj.MarketDataReplayJournalWriter(store=writer.store)
        self.assertEqual(reloaded.startup_diagnostic_code, "OK")
        self.assertEqual(len(reloaded.events), 1)

    def test_closed_event_vocabulary_enforced(self):
        journal = mdj.MarketDataReplayJournal()
        with self.assertRaises(mdj.MarketDataReplayJournalValidationError):
            journal.append("NOT_A_GOVERNED_EVENT", "2026-01-01T00:00:00.000000Z", {})

    def test_all_ten_event_types_governed(self):
        self.assertEqual(len(mdj.EVENT_TYPES), 10)
        for event_type in mdj.EVENT_TYPES:
            journal = mdj.MarketDataReplayJournal()
            journal.append(event_type, "2026-01-01T00:00:00.000000Z", {"k": "v"})

    def test_sequence_numbers_contiguous(self):
        writer = mdj.in_memory_mdr_journal_writer()
        for index in range(3):
            writer.append("MARKET_DATASET_REJECTED", {"i": index}, occurred_at_utc="2026-01-01T00:00:0{}.000000Z".format(index))
        sequences = [event["sequence_number"] for event in writer.events]
        self.assertEqual(sequences, [1, 2, 3])

    def test_hash_chain_links_consecutive_events(self):
        writer = mdj.in_memory_mdr_journal_writer()
        writer.append("MARKET_DATASET_REJECTED", {}, occurred_at_utc="2026-01-01T00:00:00.000000Z")
        writer.append("MARKET_DATASET_REJECTED", {}, occurred_at_utc="2026-01-01T00:00:01.000000Z")
        events = writer.events
        self.assertEqual(events[0]["previous_event_hash"], mdj.GENESIS_HASH)
        self.assertEqual(events[1]["previous_event_hash"], events[0]["current_event_hash"])

    def test_atomic_batch_all_or_nothing(self):
        writer = mdj.in_memory_mdr_journal_writer()
        events = writer.append_batch(
            [("REPLAY_STEP_RECORDED", {"a": 1}), ("REPLAY_SNAPSHOT_RECORDED", {"b": 2})],
            occurred_at_utc="2026-01-01T00:00:00.000000Z",
        )
        self.assertEqual(len(events), 2)
        self.assertEqual([e["event_type"] for e in events], ["REPLAY_STEP_RECORDED", "REPLAY_SNAPSHOT_RECORDED"])
        self.assertEqual(events[0]["sequence_number"] + 1, events[1]["sequence_number"])

    def test_batch_failure_leaves_journal_unchanged(self):
        writer = mdj.in_memory_mdr_journal_writer()
        writer.append("MARKET_DATASET_REJECTED", {}, occurred_at_utc="2026-01-01T00:00:00.000000Z")
        before = len(writer.events)
        with self.assertRaises(mdj.MarketDataReplayJournalValidationError):
            writer.append_batch(
                [("REPLAY_STEP_RECORDED", {}), ("NOT_GOVERNED", {})],
                occurred_at_utc="2026-01-01T00:00:01.000000Z",
            )
        self.assertEqual(len(writer.events), before)

    def test_event_count_bound_enforced(self):
        journal = mdj.MarketDataReplayJournal()
        original = mdj.MAX_JOURNAL_EVENTS
        mdj.MAX_JOURNAL_EVENTS = 2
        try:
            journal.append("MARKET_DATASET_REJECTED", "2026-01-01T00:00:00.000000Z", {})
            journal.append("MARKET_DATASET_REJECTED", "2026-01-01T00:00:01.000000Z", {})
            with self.assertRaises(mdd.MarketDataValidationError) as ctx:
                journal.append("MARKET_DATASET_REJECTED", "2026-01-01T00:00:02.000000Z", {})
            self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_FULL")
            self.assertEqual(len(journal.events), 2)
        finally:
            mdj.MAX_JOURNAL_EVENTS = original

    def test_event_too_large_rejected(self):
        journal = mdj.MarketDataReplayJournal()
        huge_payload = {"blob": "x" * (mdj.MAX_EVENT_BYTES)}
        with self.assertRaises(mdd.MarketDataValidationError) as ctx:
            journal.append("MARKET_DATASET_REJECTED", "2026-01-01T00:00:00.000000Z", huge_payload)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_EVENT_TOO_LARGE")

    def test_duplicate_key_rejected_on_load(self):
        store = mdj.InMemoryMarketDataReplayJournalStore()
        store.replace_raw_for_test(b'{"a": 1, "a": 2}')
        with self.assertRaises(mdj.MarketDataReplayJournalStorageValidationError):
            store.load()

    def test_corrupted_journal_fails_closed_at_startup(self):
        store = mdj.InMemoryMarketDataReplayJournalStore()
        store.replace_raw_for_test(b'{"not": "a valid journal store"}')
        writer = mdj.MarketDataReplayJournalWriter(store=store)
        self.assertEqual(writer.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")

    def test_no_duplicate_event_id_within_journal(self):
        journal = mdj.MarketDataReplayJournal()
        journal.append("MARKET_DATASET_REJECTED", "2026-01-01T00:00:00.000000Z", {"x": 1})
        events = journal.events
        with self.assertRaises(mdj.MarketDataReplayJournalValidationError):
            mdj.MarketDataReplayJournal(events + events)


class LocalJournalStoreTests(unittest.TestCase):
    def test_persists_across_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.json"
            writer = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=path))
            writer.append("MARKET_DATASET_REJECTED", {"x": 1}, occurred_at_utc="2026-01-01T00:00:00.000000Z")
            reloaded = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=path))
            self.assertEqual(reloaded.startup_diagnostic_code, "OK")
            self.assertEqual(len(reloaded.events), 1)

    def test_atomic_write_leaves_no_temp_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.json"
            writer = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=path))
            writer.append("MARKET_DATASET_REJECTED", {}, occurred_at_utc="2026-01-01T00:00:00.000000Z")
            leftovers = [p for p in Path(tmp).iterdir() if p.suffix == ".tmp"]
            self.assertEqual(leftovers, [])

    def test_no_lock_file_remains_after_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.json"
            writer = mdj.MarketDataReplayJournalWriter(store=mdj.LocalMarketDataReplayJournalStore(path=path))
            with writer.acquire_mutation_lock():
                writer.append("MARKET_DATASET_REJECTED", {}, occurred_at_utc="2026-01-01T00:00:00.000000Z")
            lock_files = list(Path(tmp).glob("*.lock"))
            self.assertEqual(lock_files, [])

    def test_lock_timeout_when_already_held(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.json"
            lock_path = path.with_suffix(path.suffix + ".lock")
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            lock_path.write_bytes(b"held-by-someone-else")
            store = mdj.LocalMarketDataReplayJournalStore(path=path)
            lock = store.lock()
            with self.assertRaises(mdj.MarketDataReplayJournalLockTimeout):
                lock.acquire(timeout=0.1)

    def test_owner_token_mismatch_cannot_remove_another_holders_lock(self):
        """Founder-review correction, Section 6 item 10: a lock instance
        must never delete a lock file it does not itself own (by exact
        owner-token match) -- proven directly by acquiring a real lock,
        forging a foreign token into the same lock file mid-hold, then
        confirming ``release()`` leaves that foreign-owned file in place."""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.json"
            lock_path = path.with_suffix(path.suffix + ".lock")
            store = mdj.LocalMarketDataReplayJournalStore(path=path)
            lock = store.lock()
            lock.acquire()
            # Simulate a stale-lock recovery race: another process's token
            # now occupies the exact same lock file.
            lock_path.write_bytes(b"a-different-owner-token")
            lock.release()
            self.assertTrue(lock_path.exists())
            self.assertEqual(lock_path.read_bytes(), b"a-different-owner-token")


class ThreadLockContentionTests(unittest.TestCase):
    def test_second_thread_blocked_lock_times_out(self):
        writer = mdj.in_memory_mdr_journal_writer()
        holder = writer.acquire_mutation_lock()
        holder.__enter__()
        try:
            second = mdj.MarketDataReplayJournalWriter(store=writer.store)
            with self.assertRaises(mdj.MarketDataReplayJournalLockTimeout):
                lock2 = second.acquire_mutation_lock()
                # The in-memory store's lock is a shared class-level thread
                # lock, so a second attempt from the same process blocks
                # until the bounded timeout, exactly like the cross-process
                # file lock.
                orig_timeout = mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS
                mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS = 0.2
                try:
                    lock2.__enter__()
                finally:
                    mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS = orig_timeout
        finally:
            holder.__exit__(None, None, None)


if __name__ == "__main__":
    unittest.main()
