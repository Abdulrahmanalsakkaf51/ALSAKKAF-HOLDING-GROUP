"""Tests for TRL-R2-011 Market Data Fabric and Replay V0 -- service module
(``market_data_replay_service.py``). Covers contract Section 25 categories
D (dataset reuse), F (replay behavior for every status), H (pagination),
I (capability), and the import-atomicity sequence (Section 17.2).
"""

import tempfile
import unittest

import mdr_test_support as support
from trading_lab_app import market_data_replay_data as mdd
from trading_lab_app import market_data_replay_journal as mdj
from trading_lab_app import market_data_replay_service as svc


class _SpyJournal:
    """Wraps a real journal writer, recording the exact call order of
    ``acquire_mutation_lock``/``append``/``append_batch`` -- used to prove
    directly that no append ever happens before a lock acquisition."""

    def __init__(self, inner):
        self._inner = inner
        self.call_order = []

    @property
    def startup_diagnostic_code(self):
        return self._inner.startup_diagnostic_code

    @property
    def events(self):
        return self._inner.events

    def acquire_mutation_lock(self):
        self.call_order.append("acquire_mutation_lock")
        return self._inner.acquire_mutation_lock()

    def append(self, event_type, payload, occurred_at_utc=None):
        self.call_order.append(("append", event_type))
        return self._inner.append(event_type, payload, occurred_at_utc=occurred_at_utc)

    def append_batch(self, entries, occurred_at_utc=None):
        self.call_order.append(("append_batch", [entry[0] for entry in entries]))
        return self._inner.append_batch(entries, occurred_at_utc=occurred_at_utc)


class LockedRejectionTests(unittest.TestCase):
    """Founder-review correction: every ``MARKET_DATASET_REJECTED`` append
    must occur under the authoritative mutation lock, after a fresh reload,
    exactly like every other journal mutation -- never as an unlocked
    fallback. Section 3-6 of the correction instructions."""

    def _bad_csv_path(self):
        import os
        raw = (mdd.CSV_HEADER + "\nnot,a,valid,row\n").encode("utf-8")
        handle = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        handle.write(raw)
        handle.close()
        self.addCleanup(os.unlink, handle.name)
        return handle.name

    def test_rejection_append_happens_only_after_lock_acquired(self):
        writer = mdj.in_memory_mdr_journal_writer()
        spy = _SpyJournal(writer)
        service = support.build_service(journal=spy)
        with self.assertRaises(svc.MarketDataServiceError):
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
        append_calls = [entry for entry in spy.call_order if entry != "acquire_mutation_lock"]
        self.assertEqual(len(append_calls), 1)
        self.assertEqual(append_calls[0], ("append", "MARKET_DATASET_REJECTED"))
        # The lock acquisition must precede the append in the recorded order.
        self.assertLess(
            spy.call_order.index("acquire_mutation_lock"),
            spy.call_order.index(("append", "MARKET_DATASET_REJECTED")),
        )

    def test_no_rejection_event_appended_before_lock_in_a_fresh_service(self):
        writer = mdj.in_memory_mdr_journal_writer()
        service = support.build_service(journal=writer)
        self.assertEqual(len(writer.events), 0)
        with self.assertRaises(svc.MarketDataServiceError):
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
        # Exactly one event exists, and it is the rejection itself -- proving
        # no earlier, premature append occurred.
        self.assertEqual(len(writer.events), 1)
        self.assertEqual(writer.events[0]["event_type"], "MARKET_DATASET_REJECTED")

    def test_journal_reloaded_after_lock_acquisition_before_rejection_append(self):
        store = mdj.InMemoryMarketDataReplayJournalStore()
        service_writer = mdj.MarketDataReplayJournalWriter(store=store)
        # A different writer instance, sharing the same durable store,
        # persists one event AFTER service_writer's own construction --
        # simulating another process's concurrent write. service_writer's
        # in-memory view is now stale relative to the store.
        other_writer = mdj.MarketDataReplayJournalWriter(store=store)
        other_writer.append(
            "MARKET_DATASET_REJECTED",
            {"reason_code": "MARKET_DATA_CSV_SHAPE_INVALID", "source_classification": None, "source_reference": "prior"},
            occurred_at_utc="2020-01-01T00:00:00.000000Z",
        )
        self.assertEqual(len(service_writer.events), 0)  # confirmed stale

        service = support.build_service(journal=service_writer)
        with self.assertRaises(svc.MarketDataServiceError):
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")

        # If the journal were not reloaded after lock acquisition, this
        # append would have been built from the stale (empty) in-memory
        # view and would have silently overwritten -- losing -- the other
        # writer's already-durable event.
        final_reader = mdj.MarketDataReplayJournalWriter(store=store)
        self.assertEqual(final_reader.startup_diagnostic_code, "OK")
        self.assertEqual(len(final_reader.events), 2)
        self.assertEqual(final_reader.events[0]["payload"]["source_reference"], "prior")
        self.assertEqual(final_reader.events[1]["event_type"], "MARKET_DATASET_REJECTED")

    def test_capability_denied_import_performs_no_journal_mutation(self):
        writer = mdj.in_memory_mdr_journal_writer()
        service = support.build_service(mode_service=support.denied_mode_service(), journal=writer)
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_CAPABILITY_DENIED")
        self.assertEqual(len(writer.events), 0)

    def test_capability_denied_import_leaves_store_byte_identical(self):
        store = mdj.InMemoryMarketDataReplayJournalStore()
        writer = mdj.MarketDataReplayJournalWriter(store=store)
        before = store.load()
        service = support.build_service(mode_service=support.denied_mode_service(), journal=writer)
        with self.assertRaises(svc.MarketDataServiceError):
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
        after = store.load()
        self.assertEqual(before, after)

    def test_rejection_path_lock_timeout_appends_nothing(self):
        writer = mdj.in_memory_mdr_journal_writer()
        service = support.build_service(journal=writer)
        holder = writer.acquire_mutation_lock()
        holder.__enter__()
        try:
            original_timeout = mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS
            mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS = 0.2
            try:
                with self.assertRaises(svc.MarketDataServiceError) as ctx:
                    service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
                self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_LOCK_TIMEOUT")
            finally:
                mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS = original_timeout
        finally:
            holder.__exit__(None, None, None)
        self.assertEqual(len(writer.events), 0)

    def test_rejection_against_corrupted_journal_appends_nothing(self):
        store = mdj.InMemoryMarketDataReplayJournalStore()
        store.replace_raw_for_test(b'{"not": "a valid journal store"}')
        writer = mdj.MarketDataReplayJournalWriter(store=store)
        self.assertEqual(writer.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")
        service = support.build_service(journal=writer)
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_CORRUPTED")
        self.assertEqual(len(writer.events), 0)

    def test_rejection_when_journal_full_appends_nothing(self):
        writer = mdj.in_memory_mdr_journal_writer()
        original = mdj.MAX_JOURNAL_EVENTS
        mdj.MAX_JOURNAL_EVENTS = 0
        try:
            service = support.build_service(journal=writer)
            with self.assertRaises(svc.MarketDataServiceError) as ctx:
                service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
            self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_FULL")
            self.assertEqual(len(writer.events), 0)
        finally:
            mdj.MAX_JOURNAL_EVENTS = original

    def test_rejection_event_exceeding_encoded_limit_fails_before_mutation(self):
        writer = mdj.in_memory_mdr_journal_writer()
        original = mdj.MAX_EVENT_BYTES
        mdj.MAX_EVENT_BYTES = 8
        try:
            service = support.build_service(journal=writer)
            with self.assertRaises(svc.MarketDataServiceError) as ctx:
                service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
            self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_EVENT_TOO_LARGE")
            self.assertEqual(len(writer.events), 0)
        finally:
            mdj.MAX_EVENT_BYTES = original

    def test_successful_rejection_produces_exactly_one_append_and_persist(self):
        store = mdj.InMemoryMarketDataReplayJournalStore()
        writer = mdj.MarketDataReplayJournalWriter(store=store)
        service = support.build_service(journal=writer)
        with self.assertRaises(svc.MarketDataServiceError):
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
        self.assertEqual(len(writer.events), 1)
        self.assertEqual(store.save_count, 1)
        reloaded = mdj.MarketDataReplayJournalWriter(store=store)
        self.assertEqual(reloaded.startup_diagnostic_code, "OK")
        self.assertEqual(len(reloaded.events), 1)

    def test_no_storage_envelope_or_manifest_created_by_rejected_import(self):
        from trading_lab_app import market_data_replay_storage as mds_module
        storage = mds_module.InMemoryDatasetStorage()
        service = support.build_service(storage=storage)
        with self.assertRaises(svc.MarketDataServiceError):
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
        self.assertEqual(storage._documents, {})
        self.assertEqual(service.list_market_datasets_document()["total_count"], 0)

    def test_retry_after_lock_timeout_derives_from_last_valid_state(self):
        writer = mdj.in_memory_mdr_journal_writer()
        service = support.build_service(journal=writer)
        holder = writer.acquire_mutation_lock()
        holder.__enter__()
        try:
            original_timeout = mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS
            mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS = 0.2
            try:
                with self.assertRaises(svc.MarketDataServiceError):
                    service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
            finally:
                mdj.LOCK_ACQUIRE_TIMEOUT_SECONDS = original_timeout
        finally:
            holder.__exit__(None, None, None)
        self.assertEqual(len(writer.events), 0)
        # Retry, now that the lock is free -- derives cleanly from the
        # still-empty, still-valid journal; exactly one event results, no
        # malformed or duplicate entry.
        with self.assertRaises(svc.MarketDataServiceError):
            service.import_market_data(self._bad_csv_path(), "SYNTHETIC_FIXTURE", "ref")
        self.assertEqual(len(writer.events), 1)
        self.assertEqual(writer.events[0]["sequence_number"], 1)


class JournalCorruptionTests(unittest.TestCase):
    def _corrupted_service(self):
        store = mdj.InMemoryMarketDataReplayJournalStore()
        store.replace_raw_for_test(b'{"not": "a valid journal store"}')
        journal = mdj.MarketDataReplayJournalWriter(store=store)
        self.assertEqual(journal.startup_diagnostic_code, "JOURNAL_STORAGE_INVALID")
        return support.build_service(journal=journal)

    def test_import_fails_closed_with_exact_governed_code(self):
        service = self._corrupted_service()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            support.import_synthetic_dataset(service)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_CORRUPTED")

    def test_replay_next_fails_closed_with_exact_governed_code(self):
        service = self._corrupted_service()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.replay_next("rps_" + "0" * 32)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_CORRUPTED")

    def test_create_replay_session_fails_closed_with_exact_governed_code(self):
        service = self._corrupted_service()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.create_replay_session("mds_" + "0" * 32, 0, 1, 1)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_CORRUPTED")

    def test_cancel_replay_session_fails_closed_with_exact_governed_code(self):
        service = self._corrupted_service()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.cancel_replay_session("rps_" + "0" * 32)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_CORRUPTED")

    def test_read_only_status_remains_available_when_journal_corrupted(self):
        service = self._corrupted_service()
        document = service.status_document()
        self.assertEqual(document["journal_integrity"], "JOURNAL_STORAGE_INVALID")


class _LockTimeoutJournal:
    """A minimal journal stub whose mutation lock always times out --
    deterministically exercises every service mutation's
    ``MarketDataReplayJournalLockTimeout`` -> ``MARKET_DATA_JOURNAL_LOCK_TIMEOUT``
    conversion without needing a genuine cross-process race. Optionally
    pre-seeded with events so read-before-lock lookups (e.g.
    ``create_replay_session``'s dataset-existence check) succeed and the
    lock itself is what fails."""

    startup_diagnostic_code = "OK"

    def __init__(self, events=None):
        self._events = events or []

    @property
    def events(self):
        return list(self._events)

    def acquire_mutation_lock(self):
        raise mdj.MarketDataReplayJournalLockTimeout("forced for test")


class LockTimeoutConversionTests(unittest.TestCase):
    def _service(self, events=None):
        return support.build_service(journal=_LockTimeoutJournal(events))

    def test_import_converts_lock_timeout_to_exact_governed_code(self):
        service = self._service()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            support.import_synthetic_dataset(service)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_LOCK_TIMEOUT")

    def test_create_replay_session_converts_lock_timeout(self):
        seeded_event = {
            "event_type": "MARKET_DATASET_IMPORTED",
            "payload": {
                "dataset_id": "mds_" + "1" * 32, "canonical_dataset_hash": "1" * 64,
                "instrument": "XAUUSD", "timeframe": "M5", "source_classification": "SYNTHETIC_FIXTURE",
                "source_reference": "seed", "bar_count": 6,
                "first_observed_at_utc": "2026-01-01T00:00:00.000000Z",
                "last_observed_at_utc": "2026-01-01T00:00:00.000000Z",
                "gap_count": 0, "largest_gap_intervals": 0,
                "storage_envelope_size": 1, "storage_envelope_hash": "0" * 64,
            },
            "occurred_at_utc": "2026-01-01T00:00:00.000000Z",
        }
        service = self._service(events=[seeded_event])
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.create_replay_session("mds_" + "1" * 32, 0, 1, 1)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_LOCK_TIMEOUT")

    def test_replay_next_converts_lock_timeout(self):
        service = self._service()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.replay_next("rps_" + "0" * 32)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_LOCK_TIMEOUT")

    def test_cancel_replay_session_converts_lock_timeout(self):
        service = self._service()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.cancel_replay_session("rps_" + "0" * 32)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_JOURNAL_LOCK_TIMEOUT")


class StorageIntegrityFailureCaseBTests(unittest.TestCase):
    """Section 18.3 Case B: the journal itself remains valid, but a
    referenced dataset storage envelope fails its own revalidation."""

    def test_corrupted_storage_records_one_bounded_integrity_failure_event(self):
        service = support.build_service()
        manifest = support.import_synthetic_dataset(service)
        dataset_id = manifest["dataset_id"]
        # Corrupt the backing storage envelope in place (simulating
        # on-disk tampering) while the journal's own acceptance event
        # remains untouched and valid.
        service._storage._documents[dataset_id] = b'{"bogus": true}'

        document = service.inspect_market_dataset_document(dataset_id)
        self.assertEqual(document["status"], "CORRUPTED")
        self.assertEqual(document["reason_code"], "MARKET_DATA_STORAGE_INTEGRITY_FAILURE")

        events = service.journal_document(tail=100)["events"]
        failures = [e for e in events if e["event_type"] == "JOURNAL_INTEGRITY_FAILURE"]
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["payload"]["reason_code"], "MARKET_DATA_STORAGE_INTEGRITY_FAILURE")
        self.assertEqual(failures[0]["payload"]["dataset_id"], dataset_id)
        # No physical path is ever included in the bounded failure payload.
        self.assertNotIn("path", "".join(failures[0]["payload"].keys()).lower())

    def test_no_duplicate_integrity_failure_event_on_repeated_access(self):
        service = support.build_service()
        manifest = support.import_synthetic_dataset(service)
        dataset_id = manifest["dataset_id"]
        service._storage._documents[dataset_id] = b'{"bogus": true}'

        service.inspect_market_dataset_document(dataset_id)
        service.inspect_market_dataset_document(dataset_id)
        service.inspect_market_dataset_document(dataset_id)

        events = service.journal_document(tail=100)["events"]
        failures = [e for e in events if e["event_type"] == "JOURNAL_INTEGRITY_FAILURE"]
        self.assertEqual(len(failures), 1)

    def test_storage_not_rewritten_automatically(self):
        service = support.build_service()
        manifest = support.import_synthetic_dataset(service)
        dataset_id = manifest["dataset_id"]
        corrupted_raw = b'{"bogus": true}'
        service._storage._documents[dataset_id] = corrupted_raw
        service.inspect_market_dataset_document(dataset_id)
        self.assertEqual(service._storage._documents[dataset_id], corrupted_raw)


class ReplaySessionCorruptionTests(unittest.TestCase):
    """Section 14.3's per-session ``CORRUPTED`` projection (distinct from
    whole-journal Case A) -- forced by appending a step whose
    ``canonical_replay_session_hash`` does not match its own session, the
    exact example the contract names."""

    def _corrupted_session(self):
        service = support.build_service()
        manifest = support.import_synthetic_dataset(service, source_reference="corruption-ref")
        session = service.create_replay_session(manifest["dataset_id"], 0, manifest["bar_count"] - 1, 1)
        sid = session["replay_session_id"]
        now = service._now()
        tampered_step = {
            "schema_version": "TRL_REPLAY_STEP.v1",
            "replay_step_id": "rst_" + "9" * 32,
            "replay_session_id": sid,
            "canonical_replay_session_hash": "9" * 64,  # deliberately wrong
            "sequence_number": 1,
            "from_index": 0, "to_index": 0,
            "ordered_bar_refs": [["bar_" + "0" * 32, "0" * 64]],
            "status_after": "RUNNING",
            "occurred_at_utc": now,
            "canonical_replay_step_hash": "8" * 64,
        }
        service._journal.append("REPLAY_STEP_RECORDED", {"step": tampered_step}, occurred_at_utc=now)
        return service, manifest, sid

    def test_inspect_reports_corrupted_status(self):
        service, _manifest, sid = self._corrupted_session()
        document = service.inspect_replay_session_document(sid)
        self.assertEqual(document["replay_session"]["status"], "CORRUPTED")

    def test_replay_next_fails_closed_with_exact_governed_code(self):
        service, _manifest, sid = self._corrupted_session()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.replay_next(sid)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_REPLAY_SESSION_CORRUPTED")

    def test_cancel_fails_closed_with_exact_governed_code(self):
        service, _manifest, sid = self._corrupted_session()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.cancel_replay_session(sid)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_REPLAY_SESSION_CORRUPTED")

    def test_create_replay_session_refuses_identical_identity_reuse(self):
        service, manifest, sid = self._corrupted_session()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.create_replay_session(manifest["dataset_id"], 0, manifest["bar_count"] - 1, 1)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_REPLAY_SESSION_CORRUPTED")


class ImportAtomicityTests(unittest.TestCase):
    def test_import_creates_manifest_and_envelope(self):
        service = support.build_service()
        manifest = support.import_synthetic_dataset(service)
        self.assertEqual(manifest["import_status"], "ACCEPTED")
        self.assertTrue(mdd.DATASET_ID_PATTERN.fullmatch(manifest["dataset_id"]))

    def test_identical_import_reuses_dataset(self):
        service = support.build_service()
        raw = support.build_csv_bytes()
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as handle:
            handle.write(raw)
            path = handle.name
        try:
            first = service.import_market_data(path, "SYNTHETIC_FIXTURE", "same-ref")
            second = service.import_market_data(path, "SYNTHETIC_FIXTURE", "same-ref")
        finally:
            import os
            os.unlink(path)
        self.assertEqual(first["dataset_id"], second["dataset_id"])
        self.assertEqual(first["canonical_dataset_hash"], second["canonical_dataset_hash"])
        journal_events = service.journal_document(tail=100)["events"]
        imported = [e for e in journal_events if e["event_type"] == "MARKET_DATASET_IMPORTED"]
        reused = [e for e in journal_events if e["event_type"] == "MARKET_DATASET_REUSED"]
        self.assertEqual(len(imported), 1)
        self.assertEqual(len(reused), 1)

    def test_different_source_reference_creates_distinct_manifest(self):
        service = support.build_service()
        raw = support.build_csv_bytes()
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as handle:
            handle.write(raw)
            path = handle.name
        try:
            first = service.import_market_data(path, "SYNTHETIC_FIXTURE", "ref-a")
            second = service.import_market_data(path, "SYNTHETIC_FIXTURE", "ref-b")
        finally:
            import os
            os.unlink(path)
        self.assertNotEqual(first["dataset_id"], second["dataset_id"])

    def test_rejected_import_produces_no_manifest(self):
        service = support.build_service()
        raw = (mdd.CSV_HEADER + "\nbad,row\n").encode("utf-8")
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as handle:
            handle.write(raw)
            path = handle.name
        try:
            with self.assertRaises(svc.MarketDataServiceError):
                service.import_market_data(path, "SYNTHETIC_FIXTURE", "bad-ref")
        finally:
            import os
            os.unlink(path)
        self.assertEqual(service.status_document()["dataset_count"], 0)
        events = service.journal_document(tail=100)["events"]
        self.assertEqual(len([e for e in events if e["event_type"] == "MARKET_DATASET_REJECTED"]), 1)

    def test_all_or_nothing_no_partial_bar_set(self):
        service = support.build_service()
        raw = support.build_csv_bytes(bar_count=3) + b"XAUUSD,M5,not-a-timestamp,1900,1901,1899,1900,0,1\n"
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as handle:
            handle.write(raw)
            path = handle.name
        try:
            with self.assertRaises(svc.MarketDataServiceError):
                service.import_market_data(path, "SYNTHETIC_FIXTURE", "partial-ref")
        finally:
            import os
            os.unlink(path)
        self.assertEqual(service.list_market_datasets_document()["total_count"], 0)


class CapabilityGatingTests(unittest.TestCase):
    def test_import_denied_without_capability(self):
        service = support.build_service(mode_service=support.denied_mode_service())
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            support.import_synthetic_dataset(service)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_CAPABILITY_DENIED")

    def test_read_only_status_available_when_denied(self):
        service = support.build_service(mode_service=support.denied_mode_service())
        document = service.status_document()
        self.assertFalse(document["market_data_research_granted"])

    def test_disabled_service_read_only_operations_available(self):
        disabled = svc.disabled_service(operating_mode="OFF")
        self.assertFalse(disabled.status_document()["enabled"])
        self.assertEqual(disabled.list_market_datasets_document()["total_count"], 0)
        with self.assertRaises(svc.MarketDataServiceError):
            disabled.import_market_data("x.csv", "SYNTHETIC_FIXTURE", "ref")


class ReplaySessionLifecycleTests(unittest.TestCase):
    def _service_with_dataset(self, bar_count=6):
        service = support.build_service()
        raw = support.build_csv_bytes(bar_count=bar_count)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as handle:
            handle.write(raw)
            path = handle.name
        manifest = service.import_market_data(path, "SYNTHETIC_FIXTURE", "replay-ref")
        import os
        os.unlink(path)
        return service, manifest

    def test_ready_status_on_creation(self):
        service, manifest = self._service_with_dataset()
        session = service.create_replay_session(manifest["dataset_id"], 0, 5, 2)
        self.assertEqual(session["status"], "READY")

    def test_ready_reuse_returns_same_session_and_appends_reused_event(self):
        service, manifest = self._service_with_dataset()
        first = service.create_replay_session(manifest["dataset_id"], 0, 5, 2)
        second = service.create_replay_session(manifest["dataset_id"], 0, 5, 2)
        self.assertEqual(first["replay_session_id"], second["replay_session_id"])
        events = service.journal_document(tail=100)["events"]
        self.assertEqual(len([e for e in events if e["event_type"] == "REPLAY_SESSION_CREATED"]), 1)
        self.assertEqual(len([e for e in events if e["event_type"] == "REPLAY_SESSION_REUSED"]), 1)

    def test_running_reuse_returns_current_projection_without_duplicating_steps(self):
        service, manifest = self._service_with_dataset()
        session = service.create_replay_session(manifest["dataset_id"], 0, 5, 2)
        service.replay_next(session["replay_session_id"])
        reused = service.create_replay_session(manifest["dataset_id"], 0, 5, 2)
        self.assertEqual(reused["status"], "RUNNING")
        self.assertEqual(reused["step_count"], 1)

    def test_exact_first_middle_final_partial_step(self):
        service, manifest = self._service_with_dataset(bar_count=5)
        session = service.create_replay_session(manifest["dataset_id"], 0, 4, 2)
        sid = session["replay_session_id"]
        first = service.replay_next(sid)
        self.assertEqual(first["current_index"], 1)
        self.assertEqual(first["status"], "RUNNING")
        middle = service.replay_next(sid)
        self.assertEqual(middle["current_index"], 3)
        self.assertEqual(middle["status"], "RUNNING")
        final = service.replay_next(sid)
        self.assertEqual(final["current_index"], 4)
        self.assertEqual(final["status"], "COMPLETED")

    def test_no_step_after_completion(self):
        service, manifest = self._service_with_dataset(bar_count=3)
        session = service.create_replay_session(manifest["dataset_id"], 0, 2, 3)
        sid = session["replay_session_id"]
        completed = service.replay_next(sid)
        self.assertEqual(completed["status"], "COMPLETED")
        self.assertNotIn("reason_code", completed)
        again = service.replay_next(sid)
        self.assertEqual(again["step_count"], completed["step_count"])
        self.assertEqual(again["reason_code"], "MARKET_DATA_REPLAY_ALREADY_COMPLETED")
        events = service.journal_document(tail=100)["events"]
        self.assertEqual(len([e for e in events if e["event_type"] == "REPLAY_STEP_RECORDED"]), 1)

    def test_completed_reuse_returns_existing_completed_session(self):
        service, manifest = self._service_with_dataset(bar_count=3)
        session = service.create_replay_session(manifest["dataset_id"], 0, 2, 3)
        service.replay_next(session["replay_session_id"])
        reused = service.create_replay_session(manifest["dataset_id"], 0, 2, 3)
        self.assertEqual(reused["status"], "COMPLETED")

    def test_cancellation_of_ready_session(self):
        service, manifest = self._service_with_dataset()
        session = service.create_replay_session(manifest["dataset_id"], 0, 5, 2)
        cancelled = service.cancel_replay_session(session["replay_session_id"])
        self.assertEqual(cancelled["status"], "CANCELLED")

    def test_cancellation_idempotent(self):
        service, manifest = self._service_with_dataset()
        session = service.create_replay_session(manifest["dataset_id"], 0, 5, 2)
        sid = session["replay_session_id"]
        service.cancel_replay_session(sid)
        events_before = len(service.journal_document(tail=100)["events"])
        service.cancel_replay_session(sid)
        events_after = len(service.journal_document(tail=100)["events"])
        self.assertEqual(events_before, events_after)

    def test_cancelling_completed_session_appends_no_event(self):
        service, manifest = self._service_with_dataset(bar_count=3)
        session = service.create_replay_session(manifest["dataset_id"], 0, 2, 3)
        service.replay_next(session["replay_session_id"])
        events_before = len(service.journal_document(tail=100)["events"])
        result = service.cancel_replay_session(session["replay_session_id"])
        events_after = len(service.journal_document(tail=100)["events"])
        self.assertEqual(result["status"], "COMPLETED")
        self.assertEqual(events_before, events_after)

    def test_replay_next_after_cancellation_rejected(self):
        service, manifest = self._service_with_dataset()
        session = service.create_replay_session(manifest["dataset_id"], 0, 5, 2)
        service.cancel_replay_session(session["replay_session_id"])
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.replay_next(session["replay_session_id"])
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_REPLAY_ALREADY_CANCELLED")

    def test_snapshot_window_capped_at_100_and_no_future_bar(self):
        service, manifest = self._service_with_dataset(bar_count=6)
        session = service.create_replay_session(manifest["dataset_id"], 0, 5, 6)
        result = service.replay_next(session["replay_session_id"])
        snapshot = result["latest_snapshot"]
        self.assertLessEqual(len(snapshot["ordered_window_bar_refs"]), mdd.MAX_REPLAY_WINDOW_BARS)
        self.assertEqual(snapshot["window_end_index"], snapshot["current_index"])
        self.assertTrue(snapshot["non_live"])
        self.assertTrue(snapshot["non_executable"])

    def test_projected_step_limit_exceeded_rejected(self):
        # A real >10000-bar CSV fixture would be excessive for a unit test;
        # this exercises the service-level projected-step-count gate
        # directly against a synthetic large dataset summary journaled the
        # same compact way MARKET_DATASET_IMPORTED always is (Section
        # 18.2), without constructing 10001 real canonical bars.
        service = support.build_service()
        service._journal.append(
            "MARKET_DATASET_IMPORTED",
            {
                "dataset_id": "mds_" + "9" * 32, "canonical_dataset_hash": "9" * 64,
                "instrument": "XAUUSD", "timeframe": "M5", "source_classification": "SYNTHETIC_FIXTURE",
                "source_reference": "large-ref", "bar_count": 20000,
                "first_observed_at_utc": "2026-01-01T00:00:00.000000Z",
                "last_observed_at_utc": "2026-01-01T00:00:00.000000Z",
                "gap_count": 0, "largest_gap_intervals": 0,
                "storage_envelope_size": 1, "storage_envelope_hash": "0" * 64,
            },
            occurred_at_utc="2026-01-01T00:00:00.000000Z",
        )
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.create_replay_session("mds_" + "9" * 32, 0, 19999, 1)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_REPLAY_PROJECTED_STEP_LIMIT_EXCEEDED")

    def test_replay_bounds_invalid_rejected(self):
        service, manifest = self._service_with_dataset(bar_count=6)
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.create_replay_session(manifest["dataset_id"], 3, 1, 1)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_REPLAY_BOUNDS_INVALID")

    def test_dataset_not_found_rejected(self):
        service, _manifest = self._service_with_dataset()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.create_replay_session("mds_" + "0" * 32, 0, 1, 1)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_DATASET_NOT_FOUND")

    def test_replay_session_not_found_rejected(self):
        service, _manifest = self._service_with_dataset()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.replay_next("rps_" + "0" * 32)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_REPLAY_SESSION_NOT_FOUND")


class PaginationTests(unittest.TestCase):
    def test_dataset_listing_paginates(self):
        service = support.build_service()
        for index in range(3):
            support.import_synthetic_dataset(service, source_reference="ref-{}".format(index))
        page = service.list_market_datasets_document(offset=0, limit=2)
        self.assertEqual(page["returned_count"], 2)
        self.assertEqual(page["total_count"], 3)
        self.assertTrue(page["has_more"])

    def test_invalid_pagination_rejected(self):
        service = support.build_service()
        with self.assertRaises(svc.MarketDataServiceError) as ctx:
            service.list_market_datasets_document(offset=-1, limit=10)
        self.assertEqual(ctx.exception.reason_code, "MARKET_DATA_PAGINATION_INVALID")
        with self.assertRaises(svc.MarketDataServiceError):
            service.list_market_datasets_document(offset=0, limit=svc.MAX_PAGE_LIMIT + 1)

    def test_dataset_bar_reference_pagination_reports_fields(self):
        service = support.build_service()
        manifest = support.import_synthetic_dataset(service)
        document = service.inspect_market_dataset_document(manifest["dataset_id"], offset=1, limit=2)
        self.assertEqual(document["offset"], 1)
        self.assertEqual(document["limit"], 2)
        self.assertIn("total_bar_count", document)
        self.assertIn("has_more", document)

    def test_journal_tail_bounded(self):
        service = support.build_service()
        for index in range(5):
            service._journal.append("MARKET_DATASET_REJECTED", {"i": index}, occurred_at_utc="2026-01-01T00:00:0{}.000000Z".format(index))
        document = service.journal_document(tail=2)
        self.assertEqual(document["event_count"], 2)
        with self.assertRaises(svc.MarketDataServiceError):
            service.journal_document(tail=svc.MAX_JOURNAL_TAIL + 1)


if __name__ == "__main__":
    unittest.main()
