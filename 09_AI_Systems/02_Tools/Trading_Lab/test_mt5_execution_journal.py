"""Tests for mt5_execution_journal.py — append-only hash-chained journal."""

import unittest

from trading_lab_app import mt5_execution_journal as mej


class ExecutionJournalWriterTests(unittest.TestCase):
    def test_append_only_growth(self):
        writer = mej.in_memory_journal_writer()
        writer.append("ADAPTER_UNAVAILABLE", {"reason_code": "MT5_DEPENDENCY_MISSING"})
        writer.append("CONNECTION_ATTEMPTED", {})
        self.assertEqual(len(writer.events), 2)
        self.assertEqual(writer.events[0]["append_sequence"], 1)
        self.assertEqual(writer.events[1]["append_sequence"], 2)

    def test_survives_restart_via_shared_store(self):
        store = mej.InMemoryExecutionJournalStore()
        writer1 = mej.ExecutionJournalWriter(store=store)
        writer1.append("SERVICE_STOPPED", {})
        writer2 = mej.ExecutionJournalWriter(store=store)
        self.assertGreaterEqual(len(writer2.events), 1)

    def test_loading_never_calls_any_adapter(self):
        # The journal module has no adapter reference at all — loading
        # cannot call order_check/order_send by construction. This test
        # documents that invariant explicitly.
        store = mej.InMemoryExecutionJournalStore()
        writer1 = mej.ExecutionJournalWriter(store=store)
        writer1.append("PROPOSAL_ACCEPTED", {"proposal_id": "sp_" + "a" * 32})
        writer2 = mej.ExecutionJournalWriter(store=store)
        self.assertFalse(hasattr(writer2, "_adapter"))

    def test_diagnostic_ok_by_default(self):
        writer = mej.in_memory_journal_writer()
        self.assertEqual(writer.startup_diagnostic_code, "OK")


class HashChainValidationTests(unittest.TestCase):
    def _corrupted(self, mutate):
        store = mej.InMemoryExecutionJournalStore()
        writer = mej.ExecutionJournalWriter(store=store)
        writer.append("ADAPTER_UNAVAILABLE", {"reason_code": "MT5_DEPENDENCY_MISSING"})
        raw = store.load()
        mutate(raw)
        store.replace_raw_for_test(raw)
        return mej.ExecutionJournalWriter(store=store)

    def test_broken_previous_hash_fails_closed(self):
        def mutate(raw):
            raw["journal"]["events"][0]["previous_event_hash"] = "1" * 64
        writer = self._corrupted(mutate)
        self.assertEqual(writer.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")
        self.assertEqual(writer.events, [])

    def test_modified_payload_fails_closed(self):
        def mutate(raw):
            raw["journal"]["events"][0]["payload"]["reason_code"] = "TAMPERED"
        writer = self._corrupted(mutate)
        self.assertEqual(writer.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")

    def test_broken_sequence_fails_closed(self):
        def mutate(raw):
            raw["journal"]["events"][0]["append_sequence"] = 5
        writer = self._corrupted(mutate)
        self.assertEqual(writer.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")

    def test_duplicate_event_id_rejected(self):
        writer = mej.ExecutionJournal()
        writer.append("ADAPTER_UNAVAILABLE", "2026-08-01T12:00:00.000000Z", {"reason_code": "MT5_DEPENDENCY_MISSING"})
        events = writer.events
        duplicate = dict(events[0])
        with self.assertRaises(mej.ExecutionJournalValidationError):
            mej.ExecutionJournal(events + [duplicate])

    def test_backdated_event_rejected(self):
        journal = mej.ExecutionJournal()
        journal.append("ADAPTER_UNAVAILABLE", "2026-08-01T12:00:00.000000Z", {"reason_code": "MT5_DEPENDENCY_MISSING"})
        with self.assertRaises(mej.ExecutionJournalValidationError):
            journal.append("CONNECTION_ATTEMPTED", "2026-08-01T11:00:00.000000Z", {})

    def test_corrupted_journal_cannot_trigger_an_action(self):
        # Loading a corrupted journal only ever resets to empty and sets a
        # diagnostic code — it never raises an exception that could be
        # mistaken for a retryable action, and it never mutates the store.
        def mutate(raw):
            raw["journal"]["tail_event_hash"] = "f" * 64
        writer = self._corrupted(mutate)
        self.assertEqual(writer.events, [])
        self.assertEqual(writer.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")

    def test_governed_event_type_required(self):
        journal = mej.ExecutionJournal()
        with self.assertRaises(mej.ExecutionJournalValidationError):
            journal.append("NOT_A_REAL_EVENT_TYPE", "2026-08-01T12:00:00.000000Z", {})


class BoundsTests(unittest.TestCase):
    def test_oversized_payload_rejected(self):
        # Individual strings are bounded (truncated) to MAX_TEXT_LENGTH, so
        # exceeding the payload byte bound requires many bounded strings,
        # not one giant one.
        journal = mej.ExecutionJournal()
        with self.assertRaises(mej.ExecutionJournalValidationError):
            journal.append(
                "PROPOSAL_ACCEPTED", "2026-08-01T12:00:00.000000Z",
                {"items": ["x" * mej.MAX_TEXT_LENGTH] * 100},
            )

    def test_isolated_storage_only(self):
        # Tests must never touch real LOCALAPPDATA.
        writer = mej.in_memory_journal_writer()
        self.assertIsInstance(writer.store, mej.InMemoryExecutionJournalStore)


if __name__ == "__main__":
    unittest.main()
