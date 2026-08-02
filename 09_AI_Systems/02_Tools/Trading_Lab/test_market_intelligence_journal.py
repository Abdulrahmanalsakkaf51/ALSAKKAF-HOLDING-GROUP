"""Tests for market_intelligence_journal.py — TRL-R2-010's append-only,
hash-chained Market Intelligence journal, wholly separate from the Phase
5/6 execution journal.
"""

import tempfile
import unittest
from pathlib import Path

from trading_lab_app import market_intelligence_journal as mij


class JournalWriterTests(unittest.TestCase):
    def test_append_only_growth(self):
        writer = mij.in_memory_mi_journal_writer()
        writer.append("MI_SNAPSHOT_RECORDED", {"snapshot_id": "mkt_" + "a" * 32})
        writer.append("MI_OPPORTUNITY_CREATED", {"opportunity": {"opportunity_id": "opp_" + "b" * 32}})
        self.assertEqual(len(writer.events), 2)
        self.assertEqual(writer.events[0]["append_sequence"], 1)
        self.assertEqual(writer.events[1]["append_sequence"], 2)

    def test_survives_restart_via_shared_store(self):
        store = mij.InMemoryMarketIntelligenceJournalStore()
        writer1 = mij.MarketIntelligenceJournalWriter(store=store)
        writer1.append("MI_SNAPSHOT_RECORDED", {})
        writer2 = mij.MarketIntelligenceJournalWriter(store=store)
        self.assertGreaterEqual(len(writer2.events), 1)

    def test_loading_never_references_an_adapter_or_network_call(self):
        store = mij.InMemoryMarketIntelligenceJournalStore()
        writer1 = mij.MarketIntelligenceJournalWriter(store=store)
        writer1.append("MI_OPPORTUNITY_CREATED", {"opportunity": {"opportunity_id": "opp_" + "a" * 32}})
        writer2 = mij.MarketIntelligenceJournalWriter(store=store)
        self.assertFalse(hasattr(writer2, "_adapter"))
        self.assertFalse(any(attribute.endswith("adapter") for attribute in vars(writer2)))

    def test_diagnostic_ok_by_default(self):
        writer = mij.in_memory_mi_journal_writer()
        self.assertEqual(writer.startup_diagnostic_code, "OK")

    def test_event_type_must_be_governed(self):
        writer = mij.in_memory_mi_journal_writer()
        with self.assertRaises(mij.MarketIntelligenceJournalValidationError):
            writer.append("MI_UNKNOWN_EVENT", {})

    def test_governed_event_vocabulary_matches_contract_section_17_1(self):
        expected = {
            "MI_SNAPSHOT_RECORDED", "MI_OPPORTUNITY_CREATED", "MI_OPPORTUNITY_REUSED",
            "MI_EVIDENCE_RECORDED", "MI_DECISION_RECORDED", "MI_LATTICE_CREATED",
            "MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED", "MI_BASKET_PREVIEW_CREATED",
            "MI_TELEMETRY_RECORDED", "MI_RECORD_REJECTED", "MI_JOURNAL_INTEGRITY_FAILURE",
        }
        self.assertTrue(expected.issubset(set(mij.EVENT_TYPES)))

    def test_large_explanation_field_is_not_silently_truncated(self):
        writer = mij.in_memory_mi_journal_writer()
        long_text = "x" * 1000
        writer.append("MI_EVIDENCE_RECORDED", {"evidence": [{"explanation": long_text}]})
        self.assertEqual(len(writer.events[0]["payload"]["evidence"][0]["explanation"]), 1000)


class HashChainValidationTests(unittest.TestCase):
    def _corrupted(self, mutate):
        store = mij.InMemoryMarketIntelligenceJournalStore()
        writer = mij.MarketIntelligenceJournalWriter(store=store)
        writer.append("MI_SNAPSHOT_RECORDED", {"snapshot_id": "mkt_" + "a" * 32})
        raw = store.load()
        mutate(raw)
        store.replace_raw_for_test(raw)
        return mij.MarketIntelligenceJournalWriter(store=store)

    def test_broken_previous_hash_fails_closed(self):
        def mutate(raw):
            raw["journal"]["events"][0]["previous_event_hash"] = "1" * 64
        writer = self._corrupted(mutate)
        self.assertEqual(writer.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")
        self.assertEqual(writer.events, [])

    def test_modified_payload_fails_closed(self):
        def mutate(raw):
            raw["journal"]["events"][0]["payload"]["snapshot_id"] = "TAMPERED"
        writer = self._corrupted(mutate)
        self.assertEqual(writer.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")
        self.assertEqual(writer.events, [])

    def test_duplicate_object_key_in_raw_storage_fails_closed(self):
        store = mij.InMemoryMarketIntelligenceJournalStore()
        writer = mij.MarketIntelligenceJournalWriter(store=store)
        writer.append("MI_SNAPSHOT_RECORDED", {})
        raw_bytes = b'{"a": 1, "a": 2}'
        with self.assertRaises(mij.MarketIntelligenceJournalStorageValidationError):
            mij._parse_document(raw_bytes)


class LocalFileStoreTests(unittest.TestCase):
    def test_atomic_round_trip_and_no_lock_file_remains(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mi-journal.json"
            store = mij.LocalMarketIntelligenceJournalStore(path=path)
            writer = mij.MarketIntelligenceJournalWriter(store=store)
            writer.append("MI_SNAPSHOT_RECORDED", {"snapshot_id": "mkt_" + "a" * 32})
            self.assertTrue(path.exists())
            reloaded = mij.MarketIntelligenceJournalWriter(store=mij.LocalMarketIntelligenceJournalStore(path=path))
            self.assertEqual(len(reloaded.events), 1)
            lock_path = path.with_suffix(path.suffix + ".lock")
            self.assertFalse(lock_path.exists())

    def test_cross_process_lock_timeout_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mi-journal.json"
            store = mij.LocalMarketIntelligenceJournalStore(path=path)
            holder = store.lock()
            holder.acquire()
            try:
                waiter = store.lock()
                original_timeout = mij.LOCK_ACQUIRE_TIMEOUT_SECONDS
                mij.LOCK_ACQUIRE_TIMEOUT_SECONDS = 0.05
                try:
                    with self.assertRaises(mij.MarketIntelligenceJournalLockTimeout):
                        waiter.acquire()
                finally:
                    mij.LOCK_ACQUIRE_TIMEOUT_SECONDS = original_timeout
            finally:
                holder.release()

    def test_default_journal_path_is_separate_from_execution_journal(self):
        from trading_lab_app import mt5_execution_journal as mej
        mi_path = mij.default_journal_store_path()
        exec_path = mej.default_journal_store_path()
        self.assertNotEqual(mi_path, exec_path)


if __name__ == "__main__":
    unittest.main()
