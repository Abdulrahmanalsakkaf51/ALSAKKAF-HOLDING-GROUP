"""Authoritative TRL-R2-011 Market Data Fabric and Replay V0 service (TRL
CORTEX DATA FABRIC V0).

Implements TRL_R2_011_MARKET_DATA_FABRIC_REPLAY_V0_CONTRACT.md Sections
14-19. This is the single place import atomicity/reuse and replay-session
projection decisions are made; the CLI and the read-only HTTP layer never
re-derive validation or projection logic -- they call this service and
render its result. ``ModeService`` remains the sole authority for
*capability* (``market_data_research``); this service is the sole authority
for Market Data Fabric *record correctness and replay projection*.

Never imports MetaTrader5, never connects to a broker, never calls an
external API or AI model, never writes to the Phase 5/6 execution journal
or the R2-010 Market Intelligence journal, never creates R2-010 evidence or
an Opportunity Card, never creates an execution artifact.
"""

from copy import deepcopy
from datetime import datetime, timezone
import os
import stat

from . import market_data_replay_data as mdd
from .timeline_data import format_utc, validate_utc_timestamp


CAPABILITY = "market_data_research"

DEFAULT_PAGE_LIMIT = 100
MAX_PAGE_LIMIT = 1000
DEFAULT_JOURNAL_TAIL = 100
MAX_JOURNAL_TAIL = 1000

# Service-level operational reason codes, distinct from the governed
# Section 24.1 reason codes in ``market_data_replay_data`` (which every
# ``MarketDataServiceError`` raised from a data-module validation failure
# reuses directly instead) -- exactly mirroring
# ``market_intelligence_service.SERVICE_REASON_CODES``.
SERVICE_REASON_CODES = (
    "MARKET_DATA_INPUT_PATH_INVALID",
    "MARKET_DATA_DATASET_NOT_FOUND",
    "MARKET_DATA_REPLAY_SESSION_NOT_FOUND",
    "MARKET_DATA_REPLAY_SNAPSHOT_NOT_FOUND",
    "MARKET_DATA_PAGINATION_INVALID",
    "MARKET_DATA_MUTATION_LOCK_UNAVAILABLE",
)


class MarketDataServiceError(RuntimeError):
    """Wraps a governed or service-level reason code for callers that want
    it without a traceback."""

    def __init__(self, reason_code, message=None):
        self.reason_code = reason_code
        super().__init__(message or reason_code)


# ---------------------------------------------------------------------
# Input-file safety (Section 7.1)
# ---------------------------------------------------------------------

def load_csv_input_bytes(path):
    """Enforce every Section 7.1 input-safety rule and return the raw
    bytes. Never returns or persists the absolute path itself."""
    if not isinstance(path, str) or not path:
        raise MarketDataServiceError("MARKET_DATA_INPUT_PATH_INVALID", "a single local path is required")
    if "://" in path:
        raise MarketDataServiceError("MARKET_DATA_INPUT_PATH_INVALID", "a URL is not an accepted input")
    if path.startswith("\\\\") or path.startswith("//"):
        raise MarketDataServiceError("MARKET_DATA_INPUT_PATH_INVALID", "a network/UNC path is not an accepted input")
    try:
        file_stat = os.lstat(path)
    except OSError as error:
        raise MarketDataServiceError("MARKET_DATA_INPUT_PATH_INVALID", "input path could not be accessed") from error
    if stat.S_ISLNK(file_stat.st_mode):
        raise MarketDataServiceError("MARKET_DATA_INPUT_PATH_INVALID", "a symlink/reparse point is not an accepted input")
    if not stat.S_ISREG(file_stat.st_mode):
        raise MarketDataServiceError("MARKET_DATA_INPUT_PATH_INVALID", "input must be a regular file")
    if file_stat.st_size > mdd.MAX_CSV_BYTES:
        raise MarketDataServiceError("MARKET_DATA_INPUT_FILE_TOO_LARGE", "input exceeds the 33554432-byte bound")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(mdd.MAX_CSV_BYTES + 1)
    except OSError as error:
        raise MarketDataServiceError("MARKET_DATA_INPUT_PATH_INVALID", "input could not be read") from error
    if len(raw) > mdd.MAX_CSV_BYTES:
        raise MarketDataServiceError("MARKET_DATA_INPUT_FILE_TOO_LARGE", "input exceeds the 33554432-byte bound")
    return raw


# ---------------------------------------------------------------------
# Pagination (Section 19)
# ---------------------------------------------------------------------

def _validate_pagination(offset, limit, default_limit=DEFAULT_PAGE_LIMIT, max_limit=MAX_PAGE_LIMIT):
    if offset is None:
        offset = 0
    if limit is None:
        limit = default_limit
    if isinstance(offset, bool) or not isinstance(offset, int) or offset < 0:
        raise MarketDataServiceError("MARKET_DATA_PAGINATION_INVALID", "offset must be a non-negative integer")
    if isinstance(limit, bool) or not isinstance(limit, int) or not (1 <= limit <= max_limit):
        raise MarketDataServiceError("MARKET_DATA_PAGINATION_INVALID", "limit must be an integer from 1 through {}".format(max_limit))
    return offset, limit


def _paginate(items, offset, limit):
    total = len(items)
    page = items[offset:offset + limit]
    return page, total, (offset + len(page)) < total


# ---------------------------------------------------------------------
# Disabled (capability-denied-by-mode) service -- mirrors
# ``market_intelligence_service.DisabledMarketIntelligenceService`` exactly:
# read-only documents remain callable and honest (``enabled: False``,
# empty collections) rather than raising; every mutation fails closed.
# ---------------------------------------------------------------------

class DisabledMarketDataReplayService:
    enabled = False

    def __init__(self, operating_mode="OFF"):
        self.operating_mode = operating_mode

    def status_document(self):
        return {
            "schema_version": "TRL_MARKET_DATA_FABRIC_STATUS.v1",
            "enabled": False,
            "operating_mode": self.operating_mode,
            "market_data_research_granted": False,
            "research_only": True,
            "local_data_only": True,
            "live_data_disabled": True,
            "execution_disabled": True,
            "dataset_count": 0,
            "replay_session_count": 0,
            "journal_integrity": "OK",
            "message": "TRL CORTEX DATA FABRIC V0 is disabled in the {} operating mode.".format(self.operating_mode),
        }

    def list_market_datasets_document(self, offset=None, limit=None):
        offset, limit = _validate_pagination(offset, limit)
        return {"schema_version": "TRL_MARKET_DATASET_LIST.v1", "enabled": False, "offset": offset, "limit": limit, "returned_count": 0, "total_count": 0, "has_more": False, "datasets": []}

    def inspect_market_dataset_document(self, dataset_id, offset=None, limit=None):
        return {"found": False, "reason_code": "MARKET_DATA_DATASET_NOT_FOUND"}

    def list_replay_sessions_document(self, offset=None, limit=None):
        offset, limit = _validate_pagination(offset, limit)
        return {"schema_version": "TRL_REPLAY_SESSION_LIST.v1", "enabled": False, "offset": offset, "limit": limit, "returned_count": 0, "total_count": 0, "has_more": False, "replay_sessions": []}

    def inspect_replay_session_document(self, replay_session_id):
        return {"found": False, "reason_code": "MARKET_DATA_REPLAY_SESSION_NOT_FOUND"}

    def inspect_replay_snapshot_document(self, replay_session_id):
        return {"found": False, "reason_code": "MARKET_DATA_REPLAY_SNAPSHOT_NOT_FOUND"}

    def journal_document(self, tail=None):
        return {"schema_version": "TRL_MARKET_DATA_REPLAY_JOURNAL_VIEW.v1", "enabled": False, "event_count": 0, "events": []}

    def market_datasets_http_document(self, offset=None, limit=None):
        return self.list_market_datasets_document(offset, limit)

    def market_dataset_http_document(self, dataset_id, offset=None, limit=None):
        return self.inspect_market_dataset_document(dataset_id, offset, limit)

    def replay_sessions_http_document(self, offset=None, limit=None):
        return self.list_replay_sessions_document(offset, limit)

    def replay_session_http_document(self, replay_session_id):
        return self.inspect_replay_session_document(replay_session_id)

    def replay_snapshot_http_document(self, replay_session_id):
        return self.inspect_replay_snapshot_document(replay_session_id)

    def _deny(self):
        raise MarketDataServiceError("MARKET_DATA_CAPABILITY_DENIED", "market_data_research is disabled in this operating mode")

    def import_market_data(self, csv_path, source_classification, source_reference):
        self._deny()

    def create_replay_session(self, dataset_id, start_index, end_index, step_size):
        self._deny()

    def replay_next(self, replay_session_id):
        self._deny()

    def cancel_replay_session(self, replay_session_id):
        self._deny()

    def shutdown(self):
        return True


def disabled_service(operating_mode="OFF"):
    return DisabledMarketDataReplayService(operating_mode)


# ---------------------------------------------------------------------
# Real service
# ---------------------------------------------------------------------

class MarketDataReplayService:
    enabled = True

    def __init__(self, mode_service=None, journal=None, storage=None, clock=None):
        self._mode_service = mode_service
        from .market_data_replay_journal import in_memory_mdr_journal_writer
        self._journal = journal if journal is not None else in_memory_mdr_journal_writer()
        from .market_data_replay_storage import LocalDatasetStorage
        self._storage = storage if storage is not None else LocalDatasetStorage()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _now(self):
        return format_utc(self._clock())

    def _require_capability(self):
        if self._mode_service is None or not self._mode_service.has_capability(CAPABILITY):
            raise MarketDataServiceError("MARKET_DATA_CAPABILITY_DENIED", "market_data_research is not granted in the current mode")

    # -- journal read helpers -------------------------------------------

    def _events_of_type(self, event_type):
        return [event for event in self._journal.events if event["event_type"] == event_type]

    def _dataset_summaries(self):
        """One entry per unique authoritative dataset_id, sourced from its
        original MARKET_DATASET_IMPORTED event (Section 12: a
        MARKET_DATASET_REUSED event never introduces a new listable
        dataset)."""
        summaries = {}
        for event in self._events_of_type("MARKET_DATASET_IMPORTED"):
            payload = event["payload"]
            summary = dict(payload)
            summary["imported_at_utc"] = event["occurred_at_utc"]
            summaries[payload["dataset_id"]] = summary
        return summaries

    def _dataset_summary(self, dataset_id):
        return self._dataset_summaries().get(dataset_id)

    def _integrity_failure_recorded(self, dataset_id):
        return any(
            event["payload"].get("dataset_id") == dataset_id
            for event in self._events_of_type("JOURNAL_INTEGRITY_FAILURE")
        )

    def _load_dataset_envelope(self, dataset_id, canonical_dataset_hash):
        """Load and fully revalidate the storage envelope for an
        authoritative dataset. On any structural failure (Section 18.3
        Case B), records exactly one bounded JOURNAL_INTEGRITY_FAILURE
        event under the mutation lock (idempotent -- never a duplicate)
        and returns ``None``."""
        try:
            envelope = self._storage.load(dataset_id)
        except Exception:
            envelope = None
        if envelope is None or envelope["canonical_dataset_hash"] != canonical_dataset_hash:
            with self._journal.acquire_mutation_lock():
                if not self._integrity_failure_recorded(dataset_id):
                    self._journal.append(
                        "JOURNAL_INTEGRITY_FAILURE",
                        {
                            "dataset_id": dataset_id,
                            "canonical_dataset_hash": canonical_dataset_hash,
                            "reason_code": "MARKET_DATA_STORAGE_INTEGRITY_FAILURE",
                        },
                        occurred_at_utc=self._now(),
                    )
            return None
        return envelope

    # -- replay projection reconstruction (Section 14.3, 15) -------------

    def _session_base_event(self, replay_session_id):
        for event in self._events_of_type("REPLAY_SESSION_CREATED"):
            if event["payload"]["session"]["replay_session_id"] == replay_session_id:
                return event
        return None

    def _reconstruct_projection(self, replay_session_id):
        """Return a dict describing the current derived projection for one
        replay session, or ``None`` if it does not exist. ``status`` is one
        of READY/RUNNING/COMPLETED/CANCELLED/CORRUPTED (Section 14.3)."""
        base_event = self._session_base_event(replay_session_id)
        if base_event is None:
            return None
        session = base_event["payload"]["session"]

        steps = []
        for event in self._events_of_type("REPLAY_STEP_RECORDED"):
            step = event["payload"]["step"]
            if step["replay_session_id"] == replay_session_id:
                steps.append(step)
        snapshots = []
        for event in self._events_of_type("REPLAY_SNAPSHOT_RECORDED"):
            snapshot = event["payload"]["snapshot"]
            if snapshot["replay_session_id"] == replay_session_id:
                snapshots.append(snapshot)

        corrupted = False
        for index, step in enumerate(steps, start=1):
            if step["sequence_number"] != index:
                corrupted = True
            if step["canonical_replay_session_hash"] != session["canonical_replay_session_hash"]:
                corrupted = True
        if len(snapshots) != len(steps):
            corrupted = True
        for step, snapshot in zip(steps, snapshots):
            if snapshot["replay_step_id"] != step["replay_step_id"]:
                corrupted = True

        cancelled_events = [
            event for event in self._events_of_type("REPLAY_SESSION_CANCELLED")
            if event["payload"]["replay_session_id"] == replay_session_id
        ]
        completed_events = [
            event for event in self._events_of_type("REPLAY_SESSION_COMPLETED")
            if event["payload"]["replay_session_id"] == replay_session_id
        ]

        if corrupted:
            status = "CORRUPTED"
        elif completed_events:
            status = "COMPLETED"
        elif cancelled_events:
            status = "CANCELLED"
        elif steps:
            status = "RUNNING"
        else:
            status = "READY"

        current_index = steps[-1]["to_index"] if steps else None
        latest_snapshot = snapshots[-1] if snapshots else None

        return {
            "session": session,
            "status": status,
            "steps": steps,
            "snapshots": snapshots,
            "current_index": current_index,
            "latest_snapshot": latest_snapshot,
            "created_at_utc": base_event["occurred_at_utc"],
        }

    def _projection_document(self, projection):
        session = projection["session"]
        return {
            "schema_version": "TRL_REPLAY_SESSION_PROJECTION.v1",
            "replay_session_id": session["replay_session_id"],
            "canonical_replay_session_hash": session["canonical_replay_session_hash"],
            "dataset_id": session["dataset_id"],
            "canonical_dataset_hash": session["canonical_dataset_hash"],
            "start_index": session["start_index"],
            "end_index": session["end_index"],
            "step_size": session["step_size"],
            "created_at_utc": projection["created_at_utc"],
            "status": projection["status"],
            "step_count": len(projection["steps"]),
            "current_index": projection["current_index"],
            "latest_snapshot": projection["latest_snapshot"],
        }

    # -- read-only documents (Section 19, 21, 22) ------------------------

    def status_document(self):
        mode = self._mode_service.current_mode if self._mode_service else "OFF"
        granted = bool(self._mode_service and self._mode_service.has_capability(CAPABILITY))
        return {
            "schema_version": "TRL_MARKET_DATA_FABRIC_STATUS.v1",
            "enabled": True,
            "operating_mode": mode,
            "market_data_research_granted": granted,
            "research_only": True,
            "local_data_only": True,
            "live_data_disabled": True,
            "execution_disabled": True,
            "dataset_count": len(self._dataset_summaries()),
            "replay_session_count": len(self._events_of_type("REPLAY_SESSION_CREATED")),
            "journal_integrity": self._journal.startup_diagnostic_code,
            "message": "TRL CORTEX DATA FABRIC V0 research-only local market data and deterministic replay. No live data. No broker history. No execution authority.",
        }

    def list_market_datasets_document(self, offset=None, limit=None):
        offset, limit = _validate_pagination(offset, limit)
        summaries = list(self._dataset_summaries().values())
        summaries.sort(key=lambda item: item["dataset_id"])
        summaries.sort(key=lambda item: item["imported_at_utc"], reverse=True)
        page, total, has_more = _paginate(summaries, offset, limit)
        return {
            "schema_version": "TRL_MARKET_DATASET_LIST.v1", "enabled": True,
            "offset": offset, "limit": limit, "returned_count": len(page),
            "total_count": total, "has_more": has_more, "datasets": page,
        }

    def inspect_market_dataset_document(self, dataset_id, offset=None, limit=None):
        offset, limit = _validate_pagination(offset, limit)
        summary = self._dataset_summary(dataset_id)
        if summary is None:
            return {"found": False, "reason_code": "MARKET_DATA_DATASET_NOT_FOUND"}
        envelope = self._load_dataset_envelope(dataset_id, summary["canonical_dataset_hash"])
        if envelope is None:
            return {"found": True, "status": "CORRUPTED", "dataset": summary, "reason_code": "MARKET_DATA_STORAGE_INTEGRITY_FAILURE"}
        manifest = envelope["manifest"]
        refs = manifest["ordered_bar_refs"]
        page, total, has_more = _paginate(refs, offset, limit)
        return {
            "found": True, "status": "OK", "dataset": summary,
            "instrument": manifest["instrument"], "timeframe": manifest["timeframe"],
            "source_classification": manifest["source_classification"],
            "source_reference": manifest["source_reference"],
            "gap_count": manifest["gap_count"], "largest_gap_intervals": manifest["largest_gap_intervals"],
            "total_bar_count": total, "offset": offset, "limit": limit,
            "returned_count": len(page), "has_more": has_more, "ordered_bar_refs": page,
        }

    def list_replay_sessions_document(self, offset=None, limit=None):
        offset, limit = _validate_pagination(offset, limit)
        documents = []
        for event in self._events_of_type("REPLAY_SESSION_CREATED"):
            session = event["payload"]["session"]
            projection = self._reconstruct_projection(session["replay_session_id"])
            documents.append(self._projection_document(projection))
        documents.sort(key=lambda item: item["replay_session_id"])
        documents.sort(key=lambda item: item["created_at_utc"], reverse=True)
        page, total, has_more = _paginate(documents, offset, limit)
        return {
            "schema_version": "TRL_REPLAY_SESSION_LIST.v1", "enabled": True,
            "offset": offset, "limit": limit, "returned_count": len(page),
            "total_count": total, "has_more": has_more, "replay_sessions": page,
        }

    def inspect_replay_session_document(self, replay_session_id):
        projection = self._reconstruct_projection(replay_session_id)
        if projection is None:
            return {"found": False, "reason_code": "MARKET_DATA_REPLAY_SESSION_NOT_FOUND"}
        return {"found": True, "replay_session": self._projection_document(projection)}

    def inspect_replay_snapshot_document(self, replay_session_id):
        projection = self._reconstruct_projection(replay_session_id)
        if projection is None or projection["latest_snapshot"] is None:
            return {"found": False, "reason_code": "MARKET_DATA_REPLAY_SNAPSHOT_NOT_FOUND"}
        return {"found": True, "status": projection["status"], "snapshot": projection["latest_snapshot"]}

    def journal_document(self, tail=None):
        if tail is None:
            tail = DEFAULT_JOURNAL_TAIL
        if isinstance(tail, bool) or not isinstance(tail, int) or not (1 <= tail <= MAX_JOURNAL_TAIL):
            raise MarketDataServiceError("MARKET_DATA_PAGINATION_INVALID", "tail must be an integer from 1 through {}".format(MAX_JOURNAL_TAIL))
        events = self._journal.events
        page = events[-tail:]
        return {
            "schema_version": "TRL_MARKET_DATA_REPLAY_JOURNAL_VIEW.v1", "enabled": True,
            "event_count": len(page), "total_event_count": len(events), "events": page,
        }

    def market_datasets_http_document(self, offset=None, limit=None):
        return self.list_market_datasets_document(offset, limit)

    def market_dataset_http_document(self, dataset_id, offset=None, limit=None):
        return self.inspect_market_dataset_document(dataset_id, offset, limit)

    def replay_sessions_http_document(self, offset=None, limit=None):
        return self.list_replay_sessions_document(offset, limit)

    def replay_session_http_document(self, replay_session_id):
        return self.inspect_replay_session_document(replay_session_id)

    def replay_snapshot_http_document(self, replay_session_id):
        return self.inspect_replay_snapshot_document(replay_session_id)

    # -- mutations (Section 17.2, 20 -- capability-gated) -----------------

    def _append_rejection(self, reason_code, source_classification, source_reference, detail=None):
        """Append exactly one bounded ``MARKET_DATASET_REJECTED`` event.
        Callers must already hold the mutation lock and must already have
        reloaded the journal (Section 17.2 steps 9-10) -- this method never
        acquires a lock itself, so it can never be an unlocked fallback."""
        payload = {
            "reason_code": reason_code,
            "source_classification": source_classification if source_classification in mdd.SOURCE_CLASSIFICATIONS else None,
            "source_reference": (source_reference or "")[:256],
        }
        if detail:
            payload["detail"] = detail[:256]
        self._journal.append("MARKET_DATASET_REJECTED", payload, occurred_at_utc=self._now())

    def _fail_if_journal_corrupted(self):
        """Section 18.3 Case A, checked fresh -- immediately after lock
        acquisition, which has already reloaded the journal from the
        durable store (``_ReloadingLock``) -- never from a value cached
        before the lock was acquired."""
        if self._journal.startup_diagnostic_code != "OK":
            raise MarketDataServiceError("MARKET_DATA_JOURNAL_CORRUPTED", "the market data replay journal failed integrity validation")

    def import_market_data(self, csv_path, source_classification, source_reference):
        # Section 4: a denied capability must not acquire the mutation lock
        # or touch the journal at all.
        self._require_capability()

        # Section 3 step 1: determine the primary governed input-rejection
        # reason, if any, WITHOUT mutating journal or storage state. Every
        # branch below is pure validation/construction over already-safe,
        # already-read local input.
        reason_code = None
        detail = None
        bars = None
        provisional_manifest = None
        if source_classification not in mdd.SOURCE_CLASSIFICATIONS:
            reason_code, detail = mdd.SCHEMA_FAIL, "source_classification is not governed"
        if reason_code is None:
            try:
                mdd.validate_source_reference(source_reference)
            except mdd.MarketDataValidationError as error:
                reason_code, detail = error.reason_code, str(error)
        raw_bytes = None
        if reason_code is None:
            try:
                raw_bytes = load_csv_input_bytes(csv_path)
            except MarketDataServiceError as error:
                reason_code, detail = error.reason_code, str(error)
        if reason_code is None:
            try:
                rows, expected_interval_seconds, gap_count, largest_gap_intervals = mdd.parse_csv_rows(raw_bytes)
            except mdd.MarketDataValidationError as error:
                reason_code, detail = error.reason_code, str(error)
        if reason_code is None:
            try:
                bars = [mdd.build_bar_record(row, source_classification) for row in rows]
                provisional_manifest = mdd.build_dataset_manifest_record(
                    bars, source_classification, source_reference, expected_interval_seconds,
                    gap_count, largest_gap_intervals, imported_at_utc=self._now(),
                )
            except mdd.MarketDataValidationError as error:
                reason_code, detail = error.reason_code, str(error)

        from .market_data_replay_journal import MarketDataReplayJournalLockTimeout
        try:
            with self._journal.acquire_mutation_lock():
                # Section 5.B: corruption always takes precedence over any
                # pending input-rejection reason -- never hidden behind it.
                self._fail_if_journal_corrupted()

                if reason_code is not None:
                    # Section 3 steps 2-9 / Section 5.C: construct the
                    # bounded rejection payload and append exactly one
                    # event now that the lock is held and the journal has
                    # been reloaded. A journal-capacity failure here (event
                    # too large / journal full) takes precedence over the
                    # original input-rejection reason and appends nothing
                    # (the journal's own append_batch is already atomic).
                    try:
                        self._append_rejection(reason_code, source_classification, source_reference, detail)
                    except mdd.MarketDataValidationError as append_error:
                        raise MarketDataServiceError(append_error.reason_code, str(append_error))
                    raise MarketDataServiceError(reason_code, detail)

                dataset_id = provisional_manifest["dataset_id"]
                canonical_dataset_hash = provisional_manifest["canonical_dataset_hash"]
                existing = self._dataset_summary(dataset_id)
                if existing is not None and existing["canonical_dataset_hash"] == canonical_dataset_hash:
                    envelope = self._storage.load(dataset_id)
                    if envelope is None or envelope["canonical_dataset_hash"] != canonical_dataset_hash:
                        raise MarketDataServiceError("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "the existing accepted dataset envelope failed revalidation")
                    self._journal.append(
                        "MARKET_DATASET_REUSED",
                        {
                            "dataset_id": dataset_id, "canonical_dataset_hash": canonical_dataset_hash,
                            "reuse_reason": "IDENTICAL_BARS_AND_SOURCE_REFERENCE",
                            "source_classification": source_classification,
                            "source_reference": source_reference[:256],
                        },
                        occurred_at_utc=self._now(),
                    )
                    return envelope["manifest"]

                from . import market_data_replay_storage as mdstorage
                envelope = mdd.build_storage_envelope(provisional_manifest, bars)
                if not self._storage.exists(dataset_id):
                    saved = self._storage.save_new(dataset_id, envelope)
                else:
                    saved = self._storage.load(dataset_id)
                    if saved is None or saved["canonical_dataset_hash"] != canonical_dataset_hash:
                        raise MarketDataServiceError("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "an orphan storage file failed revalidation during import")
                encoded = mdstorage.encode_envelope(saved)
                import hashlib
                storage_hash = hashlib.sha256(encoded).hexdigest()
                manifest = saved["manifest"]
                self._journal.append(
                    "MARKET_DATASET_IMPORTED",
                    {
                        "dataset_id": manifest["dataset_id"], "canonical_dataset_hash": manifest["canonical_dataset_hash"],
                        "instrument": manifest["instrument"], "timeframe": manifest["timeframe"],
                        "source_classification": manifest["source_classification"],
                        "source_reference": manifest["source_reference"],
                        "bar_count": manifest["bar_count"],
                        "first_observed_at_utc": manifest["first_observed_at_utc"],
                        "last_observed_at_utc": manifest["last_observed_at_utc"],
                        "gap_count": manifest["gap_count"], "largest_gap_intervals": manifest["largest_gap_intervals"],
                        "storage_envelope_size": len(encoded), "storage_envelope_hash": storage_hash,
                    },
                    occurred_at_utc=manifest["imported_at_utc"],
                )
                return manifest
        except MarketDataReplayJournalLockTimeout as error:
            # Section 5.A: append nothing (the lock was never acquired, so
            # the ``with`` body above never ran); return the exact governed
            # lock-timeout code. The original pending rejection reason, if
            # any, is preserved only as non-authoritative diagnostic text
            # in the message -- never as a second reason_code or a new
            # alias.
            if reason_code is not None:
                raise MarketDataServiceError(
                    "MARKET_DATA_JOURNAL_LOCK_TIMEOUT",
                    "the mutation lock was not available in time while attempting to record a rejection (pending reason: {})".format(reason_code),
                )
            raise MarketDataServiceError("MARKET_DATA_JOURNAL_LOCK_TIMEOUT", str(error))

    def create_replay_session(self, dataset_id, start_index, end_index, step_size):
        self._require_capability()
        # A pre-lock read of cached diagnostic state only (never a
        # mutation): without this, a corrupted journal's dataset lookup
        # below would return "not found" instead of surfacing the real,
        # more actionable corruption state. The authoritative check still
        # happens fresh, after lock acquisition and reload, below.
        self._fail_if_journal_corrupted()
        summary = self._dataset_summary(dataset_id)
        if summary is None:
            raise MarketDataServiceError("MARKET_DATA_DATASET_NOT_FOUND")
        try:
            mdd.validate_replay_bounds(summary["bar_count"], start_index, end_index, step_size)
        except mdd.MarketDataValidationError as error:
            raise MarketDataServiceError(error.reason_code, str(error))
        steps = mdd.projected_step_count(start_index, end_index, step_size)
        if steps > mdd.MAX_PROJECTED_REPLAY_STEPS:
            raise MarketDataServiceError("MARKET_DATA_REPLAY_PROJECTED_STEP_LIMIT_EXCEEDED")

        from .market_data_replay_journal import MarketDataReplayJournalLockTimeout
        try:
            with self._journal.acquire_mutation_lock():
                self._fail_if_journal_corrupted()
                session_preview = mdd.build_replay_session_record(
                    dataset_id, summary["canonical_dataset_hash"], start_index, end_index, step_size, self._now(),
                )
                replay_session_id = session_preview["replay_session_id"]
                existing_base = self._session_base_event(replay_session_id)
                if existing_base is not None:
                    projection = self._reconstruct_projection(replay_session_id)
                    if projection["status"] == "CORRUPTED":
                        raise MarketDataServiceError("MARKET_DATA_REPLAY_SESSION_CORRUPTED")
                    if projection["status"] == "READY":
                        self._journal.append(
                            "REPLAY_SESSION_REUSED",
                            {"replay_session_id": replay_session_id, "canonical_replay_session_hash": session_preview["canonical_replay_session_hash"]},
                            occurred_at_utc=self._now(),
                        )
                        projection = self._reconstruct_projection(replay_session_id)
                    return self._projection_document(projection)

                self._journal.append(
                    "REPLAY_SESSION_CREATED",
                    {"session": session_preview},
                    occurred_at_utc=session_preview["created_at_utc"],
                )
                return self._projection_document(self._reconstruct_projection(replay_session_id))
        except MarketDataReplayJournalLockTimeout as error:
            raise MarketDataServiceError("MARKET_DATA_JOURNAL_LOCK_TIMEOUT", str(error))

    def replay_next(self, replay_session_id):
        self._require_capability()
        from .market_data_replay_journal import MarketDataReplayJournalLockTimeout
        try:
            with self._journal.acquire_mutation_lock():
                self._fail_if_journal_corrupted()
                projection = self._reconstruct_projection(replay_session_id)
                if projection is None:
                    raise MarketDataServiceError("MARKET_DATA_REPLAY_SESSION_NOT_FOUND")
                status = projection["status"]
                if status == "CORRUPTED":
                    raise MarketDataServiceError("MARKET_DATA_REPLAY_SESSION_CORRUPTED")
                if status == "CANCELLED":
                    raise MarketDataServiceError("MARKET_DATA_REPLAY_ALREADY_CANCELLED")
                if status == "COMPLETED":
                    # Section 15.1: "no new step is created, no duplicate
                    # event is appended, and a governed completed result is
                    # returned instead" -- the exact governed reason code
                    # names this specific non-error, already-completed
                    # short-circuit explicitly, distinguishing it from the
                    # step that itself just reached completion.
                    document = self._projection_document(projection)
                    document["reason_code"] = "MARKET_DATA_REPLAY_ALREADY_COMPLETED"
                    return document

                session = projection["session"]
                envelope = self._load_dataset_envelope(session["dataset_id"], session["canonical_dataset_hash"])
                if envelope is None:
                    raise MarketDataServiceError("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "the dataset backing this replay session failed revalidation")
                bars = envelope["ordered_bars"]

                from_index = 0 if status == "READY" else projection["current_index"] + 1
                to_index = min(from_index + session["step_size"] - 1, session["end_index"])
                sequence_number = len(projection["steps"]) + 1
                ordered_bar_refs = [mdd.bar_ref(bar) for bar in bars[from_index:to_index + 1]]
                status_after = "COMPLETED" if to_index == session["end_index"] else "RUNNING"
                now = self._now()

                step = mdd.build_replay_step_record(
                    replay_session_id, session["canonical_replay_session_hash"], sequence_number,
                    from_index, to_index, ordered_bar_refs, status_after, now,
                )
                window_start = max(session["start_index"], to_index - mdd.MAX_REPLAY_WINDOW_BARS + 1)
                window_refs = [mdd.bar_ref(bar) for bar in bars[window_start:to_index + 1]]
                current_bar = bars[to_index]
                snapshot = mdd.build_replay_snapshot_record(
                    replay_session_id, session["canonical_replay_session_hash"],
                    step["replay_step_id"], step["canonical_replay_step_hash"],
                    session["dataset_id"], session["canonical_dataset_hash"],
                    to_index, current_bar["bar_id"], current_bar["canonical_bar_hash"],
                    window_start, to_index, window_refs, now,
                )
                batch = [
                    ("REPLAY_STEP_RECORDED", {"step": step}),
                    ("REPLAY_SNAPSHOT_RECORDED", {"snapshot": snapshot}),
                ]
                if status_after == "COMPLETED":
                    batch.append(("REPLAY_SESSION_COMPLETED", {
                        "replay_session_id": replay_session_id,
                        "canonical_replay_session_hash": session["canonical_replay_session_hash"],
                    }))
                self._journal.append_batch(batch, occurred_at_utc=now)
                return self._projection_document(self._reconstruct_projection(replay_session_id))
        except MarketDataReplayJournalLockTimeout as error:
            raise MarketDataServiceError("MARKET_DATA_JOURNAL_LOCK_TIMEOUT", str(error))

    def cancel_replay_session(self, replay_session_id):
        self._require_capability()
        from .market_data_replay_journal import MarketDataReplayJournalLockTimeout
        try:
            with self._journal.acquire_mutation_lock():
                self._fail_if_journal_corrupted()
                projection = self._reconstruct_projection(replay_session_id)
                if projection is None:
                    raise MarketDataServiceError("MARKET_DATA_REPLAY_SESSION_NOT_FOUND")
                status = projection["status"]
                if status == "CORRUPTED":
                    raise MarketDataServiceError("MARKET_DATA_REPLAY_SESSION_CORRUPTED")
                if status in ("CANCELLED", "COMPLETED"):
                    return self._projection_document(projection)
                self._journal.append(
                    "REPLAY_SESSION_CANCELLED",
                    {
                        "replay_session_id": replay_session_id,
                        "canonical_replay_session_hash": projection["session"]["canonical_replay_session_hash"],
                    },
                    occurred_at_utc=self._now(),
                )
                return self._projection_document(self._reconstruct_projection(replay_session_id))
        except MarketDataReplayJournalLockTimeout as error:
            raise MarketDataServiceError("MARKET_DATA_JOURNAL_LOCK_TIMEOUT", str(error))

    def shutdown(self):
        return True


__all__ = (
    "CAPABILITY",
    "DEFAULT_PAGE_LIMIT", "MAX_PAGE_LIMIT", "DEFAULT_JOURNAL_TAIL", "MAX_JOURNAL_TAIL",
    "SERVICE_REASON_CODES", "MarketDataServiceError",
    "load_csv_input_bytes",
    "DisabledMarketDataReplayService", "disabled_service",
    "MarketDataReplayService",
)
