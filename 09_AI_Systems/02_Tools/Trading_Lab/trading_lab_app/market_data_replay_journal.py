"""Durable, append-only, hash-chained Market Data and Replay journal
(TRL-R2-011, Section 18). ``TRL_MARKET_DATA_REPLAY_JOURNAL.v1``, embedded in
a ``TRL_MARKET_DATA_REPLAY_STORE.v1`` storage document -- structurally
parallel to ``market_intelligence_journal.py``'s
``MarketIntelligenceJournalWriter`` / ``LocalMarketIntelligenceJournalStore``
pair (itself parallel to ``mt5_execution_journal.py``'s), but a wholly
separate journal file and schema family. This module never reads, writes,
or references the Phase 5/6 execution journal or the R2-010 Market
Intelligence journal in any way. Loading this journal never imports data,
advances replay, accesses a network, connects to a broker, constructs an
adapter, creates evidence, generates a signal, or generates an order -- it
is pure, validated replay of already-persisted events.
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

from . import market_data_replay_data as mdd
from .timeline_data import (
    deterministic_json_text,
    format_utc,
    sha256_text,
    validate_utc_timestamp,
)


JOURNAL_STORE_SCHEMA = "TRL_MARKET_DATA_REPLAY_STORE.v1"
JOURNAL_STORE_ID = "trl-market-data-replay-journal-local-store-v1"
JOURNAL_SCHEMA = "TRL_MARKET_DATA_REPLAY_JOURNAL.v1"
JOURNAL_EVENT_SCHEMA = "TRL_MARKET_DATA_REPLAY_JOURNAL_EVENT.v1"

MAX_JOURNAL_EVENTS = 100000
MAX_JOURNAL_BYTES = 268435456
MAX_EVENT_BYTES = 262144

LOCK_ACQUIRE_TIMEOUT_SECONDS = 10.0
LOCK_POLL_INTERVAL_SECONDS = 0.02
LOCK_STALE_SECONDS = 60.0
GENESIS_HASH = "0" * 64

# Section 18.1's closed, ten-member event vocabulary.
EVENT_TYPES = (
    "MARKET_DATASET_IMPORTED",
    "MARKET_DATASET_REUSED",
    "MARKET_DATASET_REJECTED",
    "REPLAY_SESSION_CREATED",
    "REPLAY_SESSION_REUSED",
    "REPLAY_STEP_RECORDED",
    "REPLAY_SNAPSHOT_RECORDED",
    "REPLAY_SESSION_COMPLETED",
    "REPLAY_SESSION_CANCELLED",
    "JOURNAL_INTEGRITY_FAILURE",
)


class MarketDataReplayJournalValidationError(ValueError):
    """A stable, non-secret Market Data Fabric journal validation failure."""


class MarketDataReplayJournalStorageError(RuntimeError):
    """Controlled storage failure with no path or exception-detail disclosure."""


class MarketDataReplayJournalStorageValidationError(MarketDataReplayJournalStorageError):
    """Invalid persisted content; callers must fail closed (Section 18.3 Case A)."""


class MarketDataReplayJournalLockTimeout(MarketDataReplayJournalStorageError):
    """The replay mutation lock could not be acquired in time. Callers must
    fail closed (never proceed unlocked, Section 18.1)."""


class _CrossProcessFileLock:
    """Bounded-wait, cross-process mutual-exclusion lock backed by atomic
    exclusive file creation -- duplicated (not imported) from the Phase 5/6
    and R2-010 journal modules so this module has zero dependency on
    either."""

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
                    raise MarketDataReplayJournalLockTimeout(
                        "market data replay journal mutation lock was not available in time"
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
    """In-process equivalent used by ``InMemoryMarketDataReplayJournalStore``."""

    _shared_lock = threading.Lock()

    def __enter__(self):
        acquired = self._shared_lock.acquire(timeout=LOCK_ACQUIRE_TIMEOUT_SECONDS)
        if not acquired:
            raise MarketDataReplayJournalLockTimeout(
                "market data replay journal mutation lock was not available in time"
            )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._shared_lock.release()
        return False


def _require_exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise MarketDataReplayJournalValidationError("{} has an invalid field set".format(label))


def _event_without_current_hash(event):
    return {key: value for key, value in event.items() if key != "current_event_hash"}


def _validate_event(event, previous_event=None, seen_ids=None):
    expected = (
        "schema_version", "event_id", "event_type", "occurred_at_utc",
        "sequence_number", "payload", "payload_sha256",
        "previous_event_hash", "current_event_hash",
    )
    _require_exact_keys(event, expected, "market data replay journal event")
    if event["schema_version"] != JOURNAL_EVENT_SCHEMA:
        raise MarketDataReplayJournalValidationError("market data replay journal event schema is unsupported")
    if event["event_type"] not in EVENT_TYPES:
        raise MarketDataReplayJournalValidationError("market data replay journal event type is not governed")
    occurred = validate_utc_timestamp(event["occurred_at_utc"], "occurred_at_utc")
    if previous_event is not None:
        prior_occurred = validate_utc_timestamp(previous_event["occurred_at_utc"])
        if occurred < prior_occurred:
            raise MarketDataReplayJournalValidationError("market data replay journal event was backdated")
    sequence = event["sequence_number"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise MarketDataReplayJournalValidationError("sequence_number must be a positive integer")
    expected_sequence = 1 if previous_event is None else previous_event["sequence_number"] + 1
    if sequence != expected_sequence:
        raise MarketDataReplayJournalValidationError("sequence_number is not contiguous")
    payload_text = deterministic_json_text(event["payload"])
    payload_hash = sha256_text(payload_text)
    if event["payload_sha256"] != payload_hash:
        raise MarketDataReplayJournalValidationError("journal payload hash mismatch")
    previous_hash = GENESIS_HASH if previous_event is None else previous_event["current_event_hash"]
    if event["previous_event_hash"] != previous_hash:
        raise MarketDataReplayJournalValidationError("journal previous-event hash mismatch")
    stable_fields = {
        "schema_version": JOURNAL_EVENT_SCHEMA,
        "event_type": event["event_type"],
        "occurred_at_utc": event["occurred_at_utc"],
        "sequence_number": sequence,
        "payload_sha256": payload_hash,
    }
    expected_id = "mde_" + sha256_text(deterministic_json_text(stable_fields))[:32]
    if event["event_id"] != expected_id:
        raise MarketDataReplayJournalValidationError("journal event ID mismatch")
    expected_current = sha256_text(deterministic_json_text(_event_without_current_hash(event)))
    if event["current_event_hash"] != expected_current:
        raise MarketDataReplayJournalValidationError("journal current-event hash mismatch")
    if seen_ids is not None and event["event_id"] in seen_ids:
        raise MarketDataReplayJournalValidationError("duplicate journal event ID")
    encoded_size = len((deterministic_json_text(event) + "\n").encode("utf-8"))
    if encoded_size > MAX_EVENT_BYTES:
        raise MarketDataReplayJournalValidationError("journal event exceeds the encoded-size bound")
    return deepcopy(event)


class MarketDataReplayJournal:
    """An in-memory validated hash chain of Market Data Fabric audit events."""

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
            raise MarketDataReplayJournalValidationError("journal event count exceeds the bound")
        encoded = deterministic_json_text(self.to_document()).encode("utf-8")
        if len(encoded) > MAX_JOURNAL_BYTES:
            raise MarketDataReplayJournalValidationError("journal exceeds the byte bound")

    def _next_event(self, event_type, occurred_at_utc, payload, sequence_number, previous_hash):
        payload_text = deterministic_json_text(payload)
        payload_hash = sha256_text(payload_text)
        stable_fields = {
            "schema_version": JOURNAL_EVENT_SCHEMA,
            "event_type": event_type,
            "occurred_at_utc": occurred_at_utc,
            "sequence_number": sequence_number,
            "payload_sha256": payload_hash,
        }
        event_id = "mde_" + sha256_text(deterministic_json_text(stable_fields))[:32]
        event = dict(stable_fields)
        event.update({
            "event_id": event_id,
            "payload": payload,
            "previous_event_hash": previous_hash,
        })
        event["current_event_hash"] = sha256_text(
            deterministic_json_text(_event_without_current_hash(event))
        )
        return event

    def append(self, event_type, occurred_at_utc, payload):
        """Append exactly one event. Raises
        ``mdd.MarketDataValidationError('MARKET_DATA_JOURNAL_EVENT_TOO_LARGE'
        | 'MARKET_DATA_JOURNAL_FULL')`` for the two closed bound
        violations, or ``MarketDataReplayJournalValidationError`` for any
        other structural problem."""
        return self.append_batch([(event_type, occurred_at_utc, payload)])[0]

    def append_batch(self, entries):
        """Append every ``(event_type, occurred_at_utc, payload)`` tuple as
        one atomic unit: either every event becomes visible, or none do
        (Section 15.2 -- no partially visible batch)."""
        if not entries:
            raise MarketDataReplayJournalValidationError("an event batch must contain at least one event")
        snapshot = list(self._events)
        try:
            sequence = len(self._events) + 1
            previous_hash = self.tail_hash
            appended = []
            for event_type, occurred_at_utc, payload in entries:
                if event_type not in EVENT_TYPES:
                    raise MarketDataReplayJournalValidationError("market data replay journal event type is not governed")
                validate_utc_timestamp(occurred_at_utc, "occurred_at_utc")
                if self._events:
                    prior = validate_utc_timestamp(self._events[-1]["occurred_at_utc"])
                    if validate_utc_timestamp(occurred_at_utc) < prior:
                        raise MarketDataReplayJournalValidationError("market data replay journal event was backdated")
                event = self._next_event(event_type, occurred_at_utc, payload, sequence, previous_hash)
                encoded_size = len((deterministic_json_text(event) + "\n").encode("utf-8"))
                if encoded_size > MAX_EVENT_BYTES:
                    raise mdd.MarketDataValidationError(
                        "MARKET_DATA_JOURNAL_EVENT_TOO_LARGE",
                        "journal event exceeds the encoded-size bound",
                    )
                if any(item["event_id"] == event["event_id"] for item in self._events):
                    raise MarketDataReplayJournalValidationError("duplicate journal event ID")
                clean = _validate_event(
                    event, self._events[-1] if self._events else None,
                    {item["event_id"] for item in self._events},
                )
                self._events.append(clean)
                appended.append(clean)
                sequence += 1
                previous_hash = clean["current_event_hash"]
            try:
                self._validate_bounds()
            except MarketDataReplayJournalValidationError as error:
                raise mdd.MarketDataValidationError(
                    "MARKET_DATA_JOURNAL_FULL",
                    "journal event count or byte bound reached",
                ) from error
        except Exception:
            self._events = snapshot
            raise
        return [deepcopy(event) for event in appended]

    def to_document(self):
        return {
            "schema_version": JOURNAL_SCHEMA,
            "event_count": len(self._events),
            "tail_event_hash": self.tail_hash,
            "events": deepcopy(self._events),
        }

    @classmethod
    def from_document(cls, document):
        expected = ("schema_version", "event_count", "tail_event_hash", "events")
        _require_exact_keys(document, expected, "market data replay journal")
        if document["schema_version"] != JOURNAL_SCHEMA:
            raise MarketDataReplayJournalValidationError("market data replay journal schema is unsupported")
        count = document["event_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise MarketDataReplayJournalValidationError("market data replay journal event count is invalid")
        if not isinstance(document["events"], list) or count != len(document["events"]):
            raise MarketDataReplayJournalValidationError("market data replay journal is truncated or count-mismatched")
        journal = cls(document["events"])
        if document["tail_event_hash"] != journal.tail_hash:
            raise MarketDataReplayJournalValidationError("market data replay journal tail hash mismatch")
        return journal


def validate_storage_document(document):
    expected = {"schema_version", "storage_id", "session_started_at_utc", "journal"}
    if not isinstance(document, dict) or set(document) != expected:
        raise MarketDataReplayJournalStorageValidationError("market data replay journal storage has an invalid field set")
    if document["schema_version"] != JOURNAL_STORE_SCHEMA:
        raise MarketDataReplayJournalStorageValidationError("market data replay journal storage schema is unsupported")
    if document["storage_id"] != JOURNAL_STORE_ID:
        raise MarketDataReplayJournalStorageValidationError("market data replay journal storage identity is invalid")
    try:
        validate_utc_timestamp(document["session_started_at_utc"])
        journal = MarketDataReplayJournal.from_document(document["journal"])
    except MarketDataReplayJournalValidationError as error:
        raise MarketDataReplayJournalStorageValidationError(str(error)) from error
    clean = {
        "schema_version": JOURNAL_STORE_SCHEMA,
        "storage_id": JOURNAL_STORE_ID,
        "session_started_at_utc": document["session_started_at_utc"],
        "journal": journal.to_document(),
    }
    if len((deterministic_json_text(clean) + "\n").encode("utf-8")) > MAX_JOURNAL_BYTES:
        raise MarketDataReplayJournalStorageValidationError("market data replay journal storage exceeds the byte bound")
    return clean


def storage_document(session_started_at_utc, journal):
    if not isinstance(journal, MarketDataReplayJournal):
        raise MarketDataReplayJournalStorageValidationError("market data replay journal storage requires a validated journal")
    return validate_storage_document({
        "schema_version": JOURNAL_STORE_SCHEMA,
        "storage_id": JOURNAL_STORE_ID,
        "session_started_at_utc": session_started_at_utc,
        "journal": journal.to_document(),
    })


def _reject_constant(_value):
    raise MarketDataReplayJournalStorageValidationError("market data replay journal storage contains a non-finite number")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MarketDataReplayJournalStorageValidationError("market data replay journal storage contains a duplicate object key")
        result[key] = value
    return result


def _parse_document(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_JOURNAL_BYTES:
        raise MarketDataReplayJournalStorageValidationError("market data replay journal storage exceeds the byte bound")
    try:
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise MarketDataReplayJournalStorageValidationError("market data replay journal storage is not strict UTF-8 JSON") from error
    return validate_storage_document(document)


class InMemoryMarketDataReplayJournalStore:
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
            raise MarketDataReplayJournalStorageError("market data replay journal storage atomic write failed")
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
    return root / "ALSAKKAF" / "TradingLab" / "market-data-fabric-v0" / "market-data-replay-journal-v1.json"


class LocalMarketDataReplayJournalStore:
    """Atomic single-document storage, mirroring the mode/execution/R2-010
    journal stores."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_journal_store_path()

    def load(self):
        if not self.path.exists():
            return None
        try:
            raw = self.path.read_bytes()
            return _parse_document(raw)
        except MarketDataReplayJournalStorageValidationError:
            raise
        except OSError as error:
            raise MarketDataReplayJournalStorageError("market data replay journal storage read failed") from error

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
            raise MarketDataReplayJournalStorageError("market data replay journal storage atomic write failed") from error
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
    durable store into the writer's in-memory journal before yielding
    (Section 15.1 steps 1-2 / Section 18.1 "reload after lock
    acquisition")."""

    def __init__(self, writer):
        self._writer = writer
        self._inner = writer.store.lock()

    def __enter__(self):
        self._inner.__enter__()
        self._writer._load()
        return self._writer

    def __exit__(self, exc_type, exc_value, traceback):
        return self._inner.__exit__(exc_type, exc_value, traceback)


class MarketDataReplayJournalWriter:
    """The single authoritative append path: loads on construction,
    validates, and persists atomically on every append/append_batch. A
    corrupted store fails closed at construction rather than silently
    starting empty (Section 18.3 Case A)."""

    def __init__(self, store=None, session_started_at_utc=None, clock=None):
        self.store = store if store is not None else LocalMarketDataReplayJournalStore()
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
        except MarketDataReplayJournalStorageValidationError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_INVALID"
            self._journal = MarketDataReplayJournal()
            return
        except MarketDataReplayJournalStorageError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_READ_FAILED"
            self._journal = MarketDataReplayJournal()
            return
        if loaded is None:
            self._journal = MarketDataReplayJournal()
            return
        try:
            self._journal = MarketDataReplayJournal.from_document(loaded["journal"])
        except MarketDataReplayJournalValidationError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_INVALID"
            self._journal = MarketDataReplayJournal()

    @property
    def events(self):
        return self._journal.events

    def acquire_mutation_lock(self):
        """The cross-process replay mutation lock (Section 15.1 step 1,
        Section 17.2 step 9). Reloads from the durable store immediately
        after acquiring the lock."""
        return _ReloadingLock(self)

    def append(self, event_type, payload, occurred_at_utc=None):
        occurred = occurred_at_utc or format_utc(self._clock())
        event = self._journal.append(event_type, occurred, payload)
        self._persist()
        return event

    def append_batch(self, entries, occurred_at_utc=None):
        occurred = occurred_at_utc or format_utc(self._clock())
        normalized = [
            (event_type, occurred, payload) for event_type, payload in entries
        ]
        events = self._journal.append_batch(normalized)
        self._persist()
        return events

    def _persist(self):
        document = storage_document(self._session_started_at_utc, self._journal)
        try:
            self.store.save(document)
        except MarketDataReplayJournalStorageError:
            self.persistence_status = "WRITE_FAILED_IN_MEMORY_VALID"
            self.persistence_failure_count += 1
        else:
            self.persistence_status = "OK"

    def to_document(self):
        return {
            "schema_version": "TRL_MARKET_DATA_REPLAY_JOURNAL_VIEW.v1",
            "startup_diagnostic_code": self.startup_diagnostic_code,
            "persistence_status": self.persistence_status,
            "persistence_failure_count": self.persistence_failure_count,
            "journal": self._journal.to_document(),
        }

    def shutdown(self):
        if self._shutdown:
            return True
        self._shutdown = True
        return self.store.shutdown()


def in_memory_mdr_journal_writer(session_started_at_utc=None, clock=None):
    return MarketDataReplayJournalWriter(
        store=InMemoryMarketDataReplayJournalStore(), session_started_at_utc=session_started_at_utc, clock=clock,
    )


__all__ = (
    "EVENT_TYPES",
    "MAX_JOURNAL_EVENTS", "MAX_JOURNAL_BYTES", "MAX_EVENT_BYTES",
    "LOCK_ACQUIRE_TIMEOUT_SECONDS", "LOCK_POLL_INTERVAL_SECONDS",
    "MarketDataReplayJournal",
    "MarketDataReplayJournalLockTimeout",
    "MarketDataReplayJournalStorageError",
    "MarketDataReplayJournalStorageValidationError",
    "MarketDataReplayJournalValidationError",
    "MarketDataReplayJournalWriter",
    "InMemoryMarketDataReplayJournalStore",
    "LocalMarketDataReplayJournalStore",
    "default_journal_store_path",
    "in_memory_mdr_journal_writer",
    "storage_document",
    "validate_storage_document",
)
