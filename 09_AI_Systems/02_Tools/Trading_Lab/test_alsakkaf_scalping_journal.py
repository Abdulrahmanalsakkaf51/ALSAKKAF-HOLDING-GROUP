"""Tests for alsakkaf_scalping_journal.py (TRL-R2-012 contract Section 15)."""

import unittest

from trading_lab_app import alsakkaf_scalping_journal as journal


class JournalAppendTests(unittest.TestCase):
    def test_append_and_hash_chain(self):
        writer = journal.in_memory_journal_writer()
        event_one = writer.append("SCALPING_STATE_CHANGED", {"from_state": "OFF", "to_state": "ANALYZE_ONLY"})
        event_two = writer.append("SCALPING_STATE_CHANGED", {"from_state": "ANALYZE_ONLY", "to_state": "OFF"})
        self.assertEqual(event_two["previous_event_hash"], event_one["current_event_hash"])
        self.assertEqual(event_one["append_sequence"], 1)
        self.assertEqual(event_two["append_sequence"], 2)

    def test_unknown_event_type_rejected(self):
        writer = journal.in_memory_journal_writer()
        with self.assertRaises(journal.ScalpingJournalValidationError):
            writer.append("NOT_A_GOVERNED_EVENT", {})

    def test_governed_event_vocabulary_is_stable(self):
        expected = {
            "SCALPING_STATE_CHANGED", "SYMBOL_MAPPING_SAVED", "PROFILE_CONFIGURED",
            "ANALYSIS_COMPLETED", "DECISION_RECORDED", "CYCLE_CREATED",
            "ORDER_PLAN_CREATED", "ORDER_CHECK_RECORDED", "ORDER_SEND_RECORDED",
            "ORDER_RESULT_UNCERTAIN", "PENDING_ORDER_CANCELLED", "POSITION_OPENED",
            "POSITION_UPDATED", "POSITION_PARTIALLY_CLOSED", "POSITION_CLOSED",
            "CYCLE_COMPLETED", "CYCLE_BLOCKED", "DAILY_LIMIT_REACHED",
            "EMERGENCY_STOP_ACTIVATED", "EMERGENCY_STOP_RESET",
            "JOURNAL_INTEGRITY_FAILURE", "SERVICE_STOPPED",
        }
        self.assertEqual(set(journal.EVENT_TYPES), expected)

    def test_events_property_returns_deep_copy(self):
        writer = journal.in_memory_journal_writer()
        writer.append("SCALPING_STATE_CHANGED", {"from_state": "OFF", "to_state": "PAUSED"})
        events = writer.events
        events[0]["payload"]["from_state"] = "TAMPERED"
        self.assertNotEqual(writer.events[0]["payload"]["from_state"], "TAMPERED")


class StorageRoundTripTests(unittest.TestCase):
    def test_local_store_atomic_round_trip(self):
        import tempfile
        from pathlib import Path

        directory = tempfile.mkdtemp()
        path = Path(directory) / "journal.json"
        writer = journal.ScalpingJournalWriter(store=journal.LocalScalpingJournalStore(path=path))
        writer.append("SCALPING_STATE_CHANGED", {"from_state": "OFF", "to_state": "ANALYZE_ONLY"})
        reloaded = journal.ScalpingJournalWriter(store=journal.LocalScalpingJournalStore(path=path))
        self.assertEqual(len(reloaded.events), 1)
        self.assertEqual(reloaded.startup_diagnostic_code, "OK")

    def test_corrupted_storage_fails_closed(self):
        store = journal.InMemoryScalpingJournalStore()
        store.replace_raw_for_test = lambda raw: None  # not used; corrupt via direct document injection below
        writer = journal.ScalpingJournalWriter(store=store)
        writer.append("SCALPING_STATE_CHANGED", {"from_state": "OFF", "to_state": "ANALYZE_ONLY"})
        # Directly corrupt the stored document's hash chain.
        corrupted = store._document
        corrupted["journal"]["tail_event_hash"] = "0" * 64
        reloaded = journal.ScalpingJournalWriter(store=store)
        self.assertEqual(reloaded.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")
        self.assertEqual(reloaded.events, [])


class BoundedLimitsTests(unittest.TestCase):
    def test_oversized_payload_string_is_truncated_not_rejected(self):
        writer = journal.in_memory_journal_writer()
        huge_text = "x" * 10000
        event = writer.append("SCALPING_STATE_CHANGED", {"from_state": "OFF", "to_state": huge_text})
        self.assertLessEqual(len(event["payload"]["to_state"]), journal.MAX_TEXT_LENGTH)

    def test_payload_too_large_overall_fails_closed(self):
        writer = journal.in_memory_journal_writer()
        payload = {"field_%d" % i: "x" * 500 for i in range(200)}
        with self.assertRaises(journal.ScalpingJournalValidationError):
            writer.append("SCALPING_STATE_CHANGED", payload)


class LockTimeoutTests(unittest.TestCase):
    def test_lock_timeout_error_is_a_storage_error(self):
        self.assertTrue(issubclass(journal.ScalpingJournalLockTimeout, journal.ScalpingJournalStorageError))


if __name__ == "__main__":
    unittest.main()
