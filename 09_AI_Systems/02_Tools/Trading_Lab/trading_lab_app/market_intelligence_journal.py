"""Durable, append-only, hash-chained Market Intelligence journal
(TRL-R2-010, Section 17). Structurally parallel to
``mt5_execution_journal.py``'s ``ExecutionJournalWriter`` /
``LocalExecutionJournalStore`` pair, but a wholly separate journal file and
schema family — this module never reads, writes, or references the Phase
5/6 execution journal (TRL_MT5_EXECUTION_JOURNAL.v1) in any way. Loading
this journal never makes an external call, never runs analysis, never
constructs an adapter, and never takes a market or execution action — it is
pure, validated replay.
"""

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import tempfile
import threading
import time

from .timeline_data import (
    deterministic_json_text,
    format_utc,
    sha256_text,
    validate_utc_timestamp,
)


JOURNAL_STORE_SCHEMA = "TRL_MARKET_INTELLIGENCE_JOURNAL_STORE.v1"
JOURNAL_STORE_ID = "trl-market-intelligence-journal-local-store-v1"
JOURNAL_EVENT_SCHEMA = "TRL_MARKET_INTELLIGENCE_JOURNAL_EVENT.v1"
MAX_JOURNAL_EVENTS = 20000
MAX_JOURNAL_BYTES = 16 * 1024 * 1024
# Bounded well above the largest single governed-record field this
# checkpoint stores (TRL_EVIDENCE_ITEM.v1.explanation, up to 1000 Unicode
# code points) so a payload string is never silently truncated in a way
# that would desynchronize a journaled record from its own
# canonical_*_hash (computed against the untruncated value).
MAX_PAYLOAD_BYTES = 128 * 1024
MAX_TEXT_LENGTH = 4096

LOCK_ACQUIRE_TIMEOUT_SECONDS = 10.0
LOCK_POLL_INTERVAL_SECONDS = 0.02
LOCK_STALE_SECONDS = 60.0
GENESIS_HASH = "0" * 64

# Section 17.1's closed, additive-to-nothing event vocabulary — this is a
# brand-new journal, not an extension of the Phase 5/6 execution journal.
EVENT_TYPES = (
    "MI_SNAPSHOT_RECORDED",
    "MI_OPPORTUNITY_CREATED",
    "MI_OPPORTUNITY_REUSED",
    "MI_EVIDENCE_RECORDED",
    "MI_DECISION_RECORDED",
    "MI_LATTICE_CREATED",
    "MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED",
    "MI_BASKET_PREVIEW_CREATED",
    "MI_TELEMETRY_RECORDED",
    "MI_RECORD_REJECTED",
    "MI_JOURNAL_INTEGRITY_FAILURE",
    "SERVICE_STOPPED",
)


class MarketIntelligenceJournalValidationError(ValueError):
    """A stable, non-secret Market Intelligence journal validation failure."""


class MarketIntelligenceJournalStorageError(RuntimeError):
    """Controlled storage failure with no path or exception-detail disclosure."""


class MarketIntelligenceJournalStorageValidationError(MarketIntelligenceJournalStorageError):
    """Invalid persisted content; callers must fail closed."""


class MarketIntelligenceJournalLockTimeout(MarketIntelligenceJournalStorageError):
    """The creation critical-section lock could not be acquired in time.
    Callers must fail closed (never proceed unlocked)."""


class _CrossProcessFileLock:
    """Bounded-wait, cross-process mutual-exclusion lock backed by atomic
    exclusive file creation — identical design to
    ``mt5_execution_journal._CrossProcessFileLock``, duplicated here rather
    than imported so this module has zero dependency on the Phase 5/6
    journal module."""

    def __init__(self, lock_path):
        self._lock_path = Path(lock_path)
        self._fd = None
        self._token = "{}:{}".format(os.getpid(), secrets.token_hex(8)).encode("ascii")

    def acquire(self, timeout=None):
        if timeout is None:
            timeout = LOCK_ACQUIRE_TIMEOUT_SECONDS
        deadline = time.monotonic() + timeout
        while True:
            try:
                self._lock_path.parent.mkdir(parents=True, exist_ok=True)
                self._fd = os.open(str(self._lock_path), os.O_CREAT | os.O_EXCL | os.O_RDWR)
                os.write(self._fd, self._token)
                os.fsync(self._fd)
                return
            except FileExistsError:
                self._break_if_stale()
                if time.monotonic() >= deadline:
                    raise MarketIntelligenceJournalLockTimeout(
                        "market intelligence journal creation lock was not available in time"
                    )
                time.sleep(LOCK_POLL_INTERVAL_SECONDS)

    def _break_if_stale(self):
        try:
            age = time.time() - self._lock_path.stat().st_mtime
        except OSError:
            return
        if age <= LOCK_STALE_SECONDS:
            return
        try:
            self._lock_path.unlink()
        except OSError:
            pass

    def _current_owner_token(self):
        try:
            return self._lock_path.read_bytes()
        except OSError:
            return None

    def release(self):
        if self._fd is not None:
            try:
                os.close(self._fd)
            except OSError:
                pass
            self._fd = None
        if self._current_owner_token() != self._token:
            return
        try:
            self._lock_path.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.release()
        return False


class _ThreadLock:
    """In-process equivalent used by ``InMemoryMarketIntelligenceJournalStore``."""

    _shared_lock = threading.Lock()

    def __enter__(self):
        acquired = self._shared_lock.acquire(timeout=LOCK_ACQUIRE_TIMEOUT_SECONDS)
        if not acquired:
            raise MarketIntelligenceJournalLockTimeout(
                "market intelligence journal creation lock was not available in time"
            )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._shared_lock.release()
        return False


def _bounded_text(value, field_name, maximum=MAX_TEXT_LENGTH, allow_empty=False):
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise MarketIntelligenceJournalValidationError("{} must be a string".format(field_name))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise MarketIntelligenceJournalValidationError("{} contains a control character".format(field_name))
    if not allow_empty and not value:
        raise MarketIntelligenceJournalValidationError("{} must not be empty".format(field_name))
    return value[:maximum]


def _sanitize_payload_value(value, depth=0):
    if depth > 8:
        raise MarketIntelligenceJournalValidationError("journal payload nesting exceeds the bound")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return _bounded_text(value, "payload string", allow_empty=True)
    if isinstance(value, (list, tuple)):
        if len(value) > 256:
            raise MarketIntelligenceJournalValidationError("journal payload list exceeds the item bound")
        return [_sanitize_payload_value(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > 128:
            raise MarketIntelligenceJournalValidationError("journal payload object exceeds the item bound")
        clean = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 64:
                raise MarketIntelligenceJournalValidationError("journal payload key is not canonical")
            clean[key] = _sanitize_payload_value(item, depth + 1)
        return clean
    raise MarketIntelligenceJournalValidationError("journal payload contains an unsupported type")


def _require_exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise MarketIntelligenceJournalValidationError("{} has an invalid field set".format(label))


def _event_without_current_hash(event):
    return {key: value for key, value in event.items() if key != "current_event_hash"}


def _validate_event(event, previous_event=None, seen_ids=None):
    expected = (
        "schema_version", "event_id", "event_type", "occurred_at_utc",
        "append_sequence", "payload", "payload_sha256",
        "previous_event_hash", "current_event_hash",
    )
    _require_exact_keys(event, expected, "market intelligence journal event")
    if event["schema_version"] != JOURNAL_EVENT_SCHEMA:
        raise MarketIntelligenceJournalValidationError("market intelligence journal event schema is unsupported")
    if event["event_type"] not in EVENT_TYPES:
        raise MarketIntelligenceJournalValidationError("market intelligence journal event type is not governed")
    occurred = validate_utc_timestamp(event["occurred_at_utc"], "occurred_at_utc")
    if previous_event is not None:
        prior_occurred = validate_utc_timestamp(previous_event["occurred_at_utc"])
        if occurred < prior_occurred:
            raise MarketIntelligenceJournalValidationError("market intelligence journal event was backdated")
    sequence = event["append_sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise MarketIntelligenceJournalValidationError("append sequence must be a positive integer")
    expected_sequence = 1 if previous_event is None else previous_event["append_sequence"] + 1
    if sequence != expected_sequence:
        raise MarketIntelligenceJournalValidationError("append sequence is not contiguous")
    clean_payload = _sanitize_payload_value(event["payload"])
    payload_text = deterministic_json_text(clean_payload)
    if len(payload_text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise MarketIntelligenceJournalValidationError("journal payload exceeds the byte bound")
    payload_hash = sha256_text(payload_text)
    if event["payload_sha256"] != payload_hash:
        raise MarketIntelligenceJournalValidationError("journal payload hash mismatch")
    previous_hash = GENESIS_HASH if previous_event is None else previous_event["current_event_hash"]
    if event["previous_event_hash"] != previous_hash:
        raise MarketIntelligenceJournalValidationError("journal previous-event hash mismatch")
    stable_fields = {
        "schema_version": JOURNAL_EVENT_SCHEMA,
        "event_type": event["event_type"],
        "occurred_at_utc": event["occurred_at_utc"],
        "payload_sha256": payload_hash,
    }
    expected_id = "mie_" + sha256_text(deterministic_json_text(stable_fields))[:32]
    if event["event_id"] != expected_id:
        raise MarketIntelligenceJournalValidationError("journal event ID mismatch")
    expected_current = sha256_text(deterministic_json_text(_event_without_current_hash(event)))
    if event["current_event_hash"] != expected_current:
        raise MarketIntelligenceJournalValidationError("journal current-event hash mismatch")
    if seen_ids is not None and event["event_id"] in seen_ids:
        raise MarketIntelligenceJournalValidationError("duplicate journal event ID")
    clean_event = deepcopy(event)
    clean_event["payload"] = clean_payload
    return clean_event


class MarketIntelligenceJournal:
    """An in-memory validated hash chain of Market Intelligence audit events."""

    def __init__(self, events=None):
        self._events = []
        if events:
            seen_ids = set()
            previous = None
            for candidate in events:
                clean = _validate_event(candidate, previous, seen_ids)
                self._events.append(clean)
                seen_ids.add(clean["event_id"])
                previous = clean
        self._validate_bounds()

    @property
    def events(self):
        return deepcopy(self._events)

    @property
    def tail_hash(self):
        return self._events[-1]["current_event_hash"] if self._events else GENESIS_HASH

    def _validate_bounds(self):
        if len(self._events) > MAX_JOURNAL_EVENTS:
            raise MarketIntelligenceJournalValidationError("journal event count exceeds the bound")
        encoded = deterministic_json_text(self.to_document()).encode("utf-8")
        if len(encoded) > MAX_JOURNAL_BYTES:
            raise MarketIntelligenceJournalValidationError("journal exceeds the byte bound")

    def append(self, event_type, occurred_at_utc, payload):
        if event_type not in EVENT_TYPES:
            raise MarketIntelligenceJournalValidationError("market intelligence journal event type is not governed")
        validate_utc_timestamp(occurred_at_utc, "occurred_at_utc")
        if self._events:
            prior = validate_utc_timestamp(self._events[-1]["occurred_at_utc"])
            if validate_utc_timestamp(occurred_at_utc) < prior:
                raise MarketIntelligenceJournalValidationError("market intelligence journal event was backdated")
        clean_payload = _sanitize_payload_value(payload)
        payload_text = deterministic_json_text(clean_payload)
        if len(payload_text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise MarketIntelligenceJournalValidationError("journal payload exceeds the byte bound")
        payload_hash = sha256_text(payload_text)
        stable_fields = {
            "schema_version": JOURNAL_EVENT_SCHEMA,
            "event_type": event_type,
            "occurred_at_utc": occurred_at_utc,
            "payload_sha256": payload_hash,
        }
        event_id = "mie_" + sha256_text(deterministic_json_text(stable_fields))[:32]
        if any(item["event_id"] == event_id for item in self._events):
            raise MarketIntelligenceJournalValidationError("duplicate journal event ID")
        event = dict(stable_fields)
        event.update({
            "event_id": event_id,
            "append_sequence": len(self._events) + 1,
            "payload": clean_payload,
            "previous_event_hash": self.tail_hash,
        })
        event["current_event_hash"] = sha256_text(
            deterministic_json_text(_event_without_current_hash(event))
        )
        clean = _validate_event(
            event, self._events[-1] if self._events else None,
            {item["event_id"] for item in self._events},
        )
        self._events.append(clean)
        try:
            self._validate_bounds()
        except Exception:
            self._events.pop()
            raise
        return deepcopy(clean)

    def to_document(self):
        return {
            "schema_version": "TRL_MARKET_INTELLIGENCE_JOURNAL.v1",
            "event_count": len(self._events),
            "tail_event_hash": self.tail_hash,
            "events": deepcopy(self._events),
        }

    @classmethod
    def from_document(cls, document):
        expected = ("schema_version", "event_count", "tail_event_hash", "events")
        _require_exact_keys(document, expected, "market intelligence journal")
        if document["schema_version"] != "TRL_MARKET_INTELLIGENCE_JOURNAL.v1":
            raise MarketIntelligenceJournalValidationError("market intelligence journal schema is unsupported")
        count = document["event_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise MarketIntelligenceJournalValidationError("market intelligence journal event count is invalid")
        if not isinstance(document["events"], list) or count != len(document["events"]):
            raise MarketIntelligenceJournalValidationError("market intelligence journal is truncated or count-mismatched")
        journal = cls(document["events"])
        if document["tail_event_hash"] != journal.tail_hash:
            raise MarketIntelligenceJournalValidationError("market intelligence journal tail hash mismatch")
        return journal


def validate_storage_document(document):
    expected = {"schema_version", "storage_id", "session_started_at_utc", "journal"}
    if not isinstance(document, dict) or set(document) != expected:
        raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage has an invalid field set")
    if document["schema_version"] != JOURNAL_STORE_SCHEMA:
        raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage schema is unsupported")
    if document["storage_id"] != JOURNAL_STORE_ID:
        raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage identity is invalid")
    try:
        validate_utc_timestamp(document["session_started_at_utc"])
        journal = MarketIntelligenceJournal.from_document(document["journal"])
    except MarketIntelligenceJournalValidationError as error:
        raise MarketIntelligenceJournalStorageValidationError(str(error)) from error
    clean = {
        "schema_version": JOURNAL_STORE_SCHEMA,
        "storage_id": JOURNAL_STORE_ID,
        "session_started_at_utc": document["session_started_at_utc"],
        "journal": journal.to_document(),
    }
    if len((deterministic_json_text(clean) + "\n").encode("utf-8")) > MAX_JOURNAL_BYTES:
        raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage exceeds the byte bound")
    return clean


def storage_document(session_started_at_utc, journal):
    if not isinstance(journal, MarketIntelligenceJournal):
        raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage requires a validated journal")
    return validate_storage_document({
        "schema_version": JOURNAL_STORE_SCHEMA,
        "storage_id": JOURNAL_STORE_ID,
        "session_started_at_utc": session_started_at_utc,
        "journal": journal.to_document(),
    })


def _reject_constant(_value):
    raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage contains a non-finite number")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage contains a duplicate object key")
        result[key] = value
    return result


def _parse_document(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_JOURNAL_BYTES:
        raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage exceeds the byte bound")
    try:
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MarketIntelligenceJournalStorageValidationError("market intelligence journal storage is not strict UTF-8 JSON") from error
    return validate_storage_document(document)


class InMemoryMarketIntelligenceJournalStore:
    """Exact serialization round-trip storage used by deterministic tests."""

    def __init__(self, initial_document=None):
        self._document = None
        self.fail_writes = False
        self.save_count = 0
        if initial_document is not None:
            self._document = deepcopy(validate_storage_document(initial_document))

    def load(self):
        if self._document is None:
            return None
        raw = (deterministic_json_text(self._document) + "\n").encode("utf-8")
        return _parse_document(raw)

    def save(self, document):
        clean = validate_storage_document(document)
        raw = (deterministic_json_text(clean) + "\n").encode("utf-8")
        clean = _parse_document(raw)
        if self.fail_writes:
            raise MarketIntelligenceJournalStorageError("market intelligence journal storage atomic write failed")
        self._document = deepcopy(clean)
        self.save_count += 1

    def replace_raw_for_test(self, raw):
        if isinstance(raw, bytes):
            self._document = json.loads(raw.decode("utf-8"))
        else:
            self._document = deepcopy(raw)

    def lock(self):
        return _ThreadLock()

    def shutdown(self):
        return True


def default_journal_store_path():
    """Return an isolated application-data path; never create it here."""
    local_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return root / "ALSAKKAF" / "TradingLab" / "market-intelligence-journal-v1.json"


class LocalMarketIntelligenceJournalStore:
    """Atomic single-document storage, mirroring the mode/execution stores."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_journal_store_path()

    def load(self):
        if not self.path.exists():
            return None
        try:
            raw = self.path.read_bytes()
            return _parse_document(raw)
        except MarketIntelligenceJournalStorageValidationError:
            raise
        except OSError as error:
            raise MarketIntelligenceJournalStorageError("market intelligence journal storage read failed") from error

    def save(self, document):
        clean = validate_storage_document(document)
        raw = (deterministic_json_text(clean) + "\n").encode("utf-8")
        temporary_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".{}-".format(self.path.name), suffix=".tmp",
                dir=str(self.path.parent), delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(temporary_path), str(self.path))
            temporary_path = None
        except OSError as error:
            raise MarketIntelligenceJournalStorageError("market intelligence journal storage atomic write failed") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass

    def lock(self):
        return _CrossProcessFileLock(self.path.with_suffix(self.path.suffix + ".lock"))

    def shutdown(self):
        return True


class _ReloadingLock:
    """Wraps a store-level lock: on entry, acquires it and re-reads the
    durable store into the writer's in-memory journal before yielding."""

    def __init__(self, writer):
        self._writer = writer
        self._inner = writer.store.lock()

    def __enter__(self):
        self._inner.__enter__()
        self._writer._load()
        return self._writer

    def __exit__(self, exc_type, exc_value, traceback):
        return self._inner.__exit__(exc_type, exc_value, traceback)


class MarketIntelligenceJournalWriter:
    """The single authoritative append path: loads on construction,
    validates, and persists atomically on every append. A corrupted store
    fails closed at construction rather than silently starting empty."""

    def __init__(self, store=None, session_started_at_utc=None, clock=None):
        self.store = store if store is not None else LocalMarketIntelligenceJournalStore()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._session_started_at_utc = session_started_at_utc or format_utc(self._clock())
        self.startup_diagnostic_code = "OK"
        self.persistence_status = "OK"
        self.persistence_failure_count = 0
        self._shutdown = False
        self._load()

    def _load(self):
        try:
            loaded = self.store.load()
        except MarketIntelligenceJournalStorageValidationError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_INVALID"
            self._journal = MarketIntelligenceJournal()
            return
        except MarketIntelligenceJournalStorageError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_READ_FAILED"
            self._journal = MarketIntelligenceJournal()
            return
        if loaded is None:
            self._journal = MarketIntelligenceJournal()
            return
        try:
            self._journal = MarketIntelligenceJournal.from_document(loaded["journal"])
        except MarketIntelligenceJournalValidationError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_INVALID"
            self._journal = MarketIntelligenceJournal()

    @property
    def events(self):
        return self._journal.events

    def acquire_creation_lock(self):
        """A cross-process critical section for "search the durable store,
        then decide, then persist" sequences (opportunity/decision reuse,
        Section 22). Reloads from the durable store immediately after
        acquiring the lock."""
        return _ReloadingLock(self)

    def append(self, event_type, payload, occurred_at_utc=None):
        occurred = occurred_at_utc or format_utc(self._clock())
        event = self._journal.append(event_type, occurred, payload)
        document = storage_document(self._session_started_at_utc, self._journal)
        try:
            self.store.save(document)
        except MarketIntelligenceJournalStorageError:
            self.persistence_status = "WRITE_FAILED_IN_MEMORY_VALID"
            self.persistence_failure_count += 1
        else:
            self.persistence_status = "OK"
        return event

    def to_document(self):
        return {
            "schema_version": "TRL_MARKET_INTELLIGENCE_JOURNAL_VIEW.v1",
            "startup_diagnostic_code": self.startup_diagnostic_code,
            "persistence_status": self.persistence_status,
            "persistence_failure_count": self.persistence_failure_count,
            "journal": self._journal.to_document(),
        }

    def shutdown(self):
        if self._shutdown:
            return True
        self.append("SERVICE_STOPPED", {})
        self._shutdown = True
        return self.store.shutdown()


def in_memory_mi_journal_writer(session_started_at_utc=None, clock=None):
    return MarketIntelligenceJournalWriter(
        store=InMemoryMarketIntelligenceJournalStore(), session_started_at_utc=session_started_at_utc, clock=clock,
    )


__all__ = (
    "EVENT_TYPES",
    "MarketIntelligenceJournal",
    "MarketIntelligenceJournalLockTimeout",
    "MarketIntelligenceJournalStorageError",
    "MarketIntelligenceJournalStorageValidationError",
    "MarketIntelligenceJournalValidationError",
    "MarketIntelligenceJournalWriter",
    "InMemoryMarketIntelligenceJournalStore",
    "LocalMarketIntelligenceJournalStore",
    "default_journal_store_path",
    "in_memory_mi_journal_writer",
    "storage_document",
    "validate_storage_document",
)
