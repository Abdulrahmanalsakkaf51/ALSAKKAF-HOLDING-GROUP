"""Durable, append-only, hash-chained execution journal (TRL-R2-007, Phase 5).

Structurally parallel to ``mode_service.py``'s ``ModeTransitionLog`` /
``LocalModeStateStore`` pair, and to ``paper_store.py`` for R2-005. Loading
this journal never makes an adapter call, never retries an action, and
never generates a proposal — it is pure, validated replay.
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


JOURNAL_STORE_SCHEMA = "TRL_MT5_EXECUTION_JOURNAL_STORE.v1"
JOURNAL_STORE_ID = "trl-mt5-execution-journal-local-store-v1"
JOURNAL_EVENT_SCHEMA = "TRL_MT5_EXECUTION_JOURNAL_EVENT.v1"
MAX_JOURNAL_EVENTS = 20000
MAX_JOURNAL_BYTES = 4 * 1024 * 1024
MAX_PAYLOAD_BYTES = 16 * 1024
MAX_TEXT_LENGTH = 512

# Bounds for the cross-process creation/send lock (see _CrossProcessFileLock
# below). A concurrent caller waits up to LOCK_ACQUIRE_TIMEOUT_SECONDS for
# the lock; a lock file older than LOCK_STALE_SECONDS is treated as
# abandoned (its owning process crashed while holding it) and is broken
# rather than causing every future caller to fail closed forever.
LOCK_ACQUIRE_TIMEOUT_SECONDS = 10.0
LOCK_POLL_INTERVAL_SECONDS = 0.02
LOCK_STALE_SECONDS = 60.0
GENESIS_HASH = "0" * 64

EVENT_TYPES = (
    "ADAPTER_UNAVAILABLE",
    "CONNECTION_ATTEMPTED",
    "FINGERPRINT_ACCEPTED",
    "FINGERPRINT_REJECTED",
    "PROPOSAL_ACCEPTED",
    "PROPOSAL_REJECTED",
    "ORDER_INTENT_CREATED",
    "ORDER_INTENT_REUSED",
    "ORDER_CHECK_REQUESTED",
    "ORDER_CHECK_RESULT",
    "MANUAL_CONFIRMATION_REQUESTED",
    "MANUAL_CONFIRMATION_REJECTED",
    "MANUAL_CONFIRMATION_ACCEPTED",
    "ORDER_SEND_REQUESTED",
    "ORDER_SEND_RESULT",
    "UNCERTAIN_RESULT",
    "DUPLICATE_BLOCKED",
    "EXPIRY_BLOCKED",
    "SERVICE_STOPPED",
    # TRL-R2-009 (Phase 6) basket event types — additive only. Every rule
    # above (schema, hash chain, bounds, atomic persistence) applies to
    # these unchanged; see TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md
    # Section 16.
    "BASKET_REJECTED",
    "BASKET_BLOCKED",
    "BASKET_CREATED",
    "BASKET_REUSED",
    "BASKET_CHILD_CREATED",
    "BASKET_CHILD_CHECK_REQUESTED",
    "BASKET_CHILD_CHECK_RESULT",
    "BASKET_CHILD_CHECK_STALE",
    "BASKET_RECHECK_REQUIRED",
    "BASKET_CONFIRMATION_REQUESTED",
    "BASKET_CONFIRMATION_REQUEST_REUSED",
    "BASKET_CONFIRMATION_REJECTED",
    "BASKET_CONFIRMATION_ACCEPTED",
    "BASKET_CONFIRMATION_EXPIRED",
    "BASKET_CONFIRMATION_INVALIDATED",
    "BASKET_CHILD_SEND_RESERVED",
    "BASKET_CHILD_SEND_RESULT",
    "BASKET_CHILD_PARTIAL",
    "BASKET_CHILD_UNCERTAIN",
    "BASKET_PARTIALLY_COMPLETED",
    "BASKET_FAILED",
    "BASKET_FROZEN",
    "BASKET_RECONCILIATION_REQUIRED",
    "BASKET_COMPLETED",
    "BASKET_DUPLICATE_BLOCKED",
    "BASKET_EXPIRED",
)


class ExecutionJournalValidationError(ValueError):
    """A stable, non-secret execution journal validation failure."""


class ExecutionJournalStorageError(RuntimeError):
    """Controlled storage failure with no path or exception-detail disclosure."""


class ExecutionJournalStorageValidationError(ExecutionJournalStorageError):
    """Invalid persisted content; callers must fail closed."""


class ExecutionJournalLockTimeout(ExecutionJournalStorageError):
    """The creation/send critical-section lock could not be acquired in
    time. Callers must fail closed (never proceed unlocked) rather than
    silently reintroducing the exact race this lock exists to prevent."""


class _CrossProcessFileLock:
    """A bounded-wait, cross-process mutual-exclusion lock backed by
    atomic exclusive file creation (``O_CREAT | O_EXCL``), which is atomic
    on both POSIX and Windows. Guards the "search the durable store, then
    decide, then persist" critical sections in ``mt5_execution_service.py``
    (order-intent creation and order-send duplicate-checking) — a plain
    ``threading.Lock`` only protects against concurrent threads in one
    process, not the separate OS processes the CLI-driven workflow
    actually produces (each CLI command is its own process).

    Stale-lock recovery (``_break_if_stale``) is designed around a
    genuinely crashed/killed owner, not a merely slow-but-alive one: on
    Windows, a file cannot be unlinked while any handle to it remains
    open, even one held by the same process that is trying to unlink it —
    so an owner whose process is still alive (its handle still open)
    cannot actually have its lock stolen by a stale-timeout break; only a
    truly terminated owner's file (whose OS-level handle was reclaimed on
    exit) can be. That is the intended, correct behavior."""

    def __init__(self, lock_path):
        self._lock_path = Path(lock_path)
        self._fd = None
        # A token unique to this specific acquisition (process ID is not
        # enough on its own: a PID can be reused after a process exits).
        # Written into the lock file's content and re-checked before
        # release, so a holder can never delete a lock some *other* owner
        # has since acquired after breaking this holder's own stale lock —
        # see release() below.
        self._token = "{}:{}".format(os.getpid(), secrets.token_hex(8)).encode("ascii")

    def acquire(self, timeout=None):
        # Looked up from the module global at call time (rather than bound
        # as a default-argument value at definition time) so tests can
        # monkeypatch LOCK_ACQUIRE_TIMEOUT_SECONDS for fast, deterministic
        # timeout coverage without waiting out the real production bound.
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
                    raise ExecutionJournalLockTimeout(
                        "execution journal creation/send lock was not available in time"
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
        # Only remove the lock file if it still contains THIS acquisition's
        # own token. If it does not, this holder's lock was already broken
        # as stale and re-acquired by a different owner while this holder
        # was still working — unlinking would delete that other owner's
        # live lock and let two callers both believe they hold it
        # simultaneously, exactly the bug this check exists to prevent.
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
    """In-process equivalent used by ``InMemoryExecutionJournalStore`` —
    sufficient there because an in-memory store can never actually be
    shared across separate OS processes in the first place."""

    _shared_lock = threading.Lock()

    def __enter__(self):
        acquired = self._shared_lock.acquire(timeout=LOCK_ACQUIRE_TIMEOUT_SECONDS)
        if not acquired:
            raise ExecutionJournalLockTimeout(
                "execution journal creation/send lock was not available in time"
            )
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._shared_lock.release()
        return False


def _stable_id(prefix, *parts):
    material = "\n".join(str(part) for part in parts)
    return prefix + sha256_text(material)[:32]


def _bounded_text(value, field_name, maximum=MAX_TEXT_LENGTH, allow_empty=False):
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ExecutionJournalValidationError("{} must be a string".format(field_name))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ExecutionJournalValidationError("{} contains a control character".format(field_name))
    if not allow_empty and not value:
        raise ExecutionJournalValidationError("{} must not be empty".format(field_name))
    return value[:maximum]


def _sanitize_payload_value(value, depth=0):
    if depth > 6:
        raise ExecutionJournalValidationError("journal payload nesting exceeds the bound")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return _bounded_text(value, "payload string", allow_empty=True)
    if isinstance(value, (list, tuple)):
        if len(value) > 256:
            raise ExecutionJournalValidationError("journal payload list exceeds the item bound")
        return [_sanitize_payload_value(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > 128:
            raise ExecutionJournalValidationError("journal payload object exceeds the item bound")
        clean = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 64:
                raise ExecutionJournalValidationError("journal payload key is not canonical")
            clean[key] = _sanitize_payload_value(item, depth + 1)
        return clean
    raise ExecutionJournalValidationError("journal payload contains an unsupported type")


def _require_exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ExecutionJournalValidationError("{} has an invalid field set".format(label))


def _event_without_current_hash(event):
    return {key: value for key, value in event.items() if key != "current_event_hash"}


def _validate_event(event, previous_event=None, seen_ids=None):
    expected = (
        "schema_version", "event_id", "event_type", "occurred_at_utc",
        "append_sequence", "payload", "payload_sha256",
        "previous_event_hash", "current_event_hash",
    )
    _require_exact_keys(event, expected, "execution journal event")
    if event["schema_version"] != JOURNAL_EVENT_SCHEMA:
        raise ExecutionJournalValidationError("execution journal event schema is unsupported")
    if event["event_type"] not in EVENT_TYPES:
        raise ExecutionJournalValidationError("execution journal event type is not governed")
    occurred = validate_utc_timestamp(event["occurred_at_utc"], "occurred_at_utc")
    if previous_event is not None:
        prior_occurred = validate_utc_timestamp(previous_event["occurred_at_utc"])
        if occurred < prior_occurred:
            raise ExecutionJournalValidationError("execution journal event was backdated")
    sequence = event["append_sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise ExecutionJournalValidationError("append sequence must be a positive integer")
    expected_sequence = 1 if previous_event is None else previous_event["append_sequence"] + 1
    if sequence != expected_sequence:
        raise ExecutionJournalValidationError("append sequence is not contiguous")
    clean_payload = _sanitize_payload_value(event["payload"])
    payload_text = deterministic_json_text(clean_payload)
    if len(payload_text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ExecutionJournalValidationError("journal payload exceeds the byte bound")
    payload_hash = sha256_text(payload_text)
    if event["payload_sha256"] != payload_hash:
        raise ExecutionJournalValidationError("journal payload hash mismatch")
    previous_hash = GENESIS_HASH if previous_event is None else previous_event["current_event_hash"]
    if event["previous_event_hash"] != previous_hash:
        raise ExecutionJournalValidationError("journal previous-event hash mismatch")
    stable_fields = {
        "schema_version": JOURNAL_EVENT_SCHEMA,
        "event_type": event["event_type"],
        "occurred_at_utc": event["occurred_at_utc"],
        "payload_sha256": payload_hash,
    }
    expected_id = "mje_" + sha256_text(deterministic_json_text(stable_fields))[:32]
    if event["event_id"] != expected_id:
        raise ExecutionJournalValidationError("journal event ID mismatch")
    expected_current = sha256_text(deterministic_json_text(_event_without_current_hash(event)))
    if event["current_event_hash"] != expected_current:
        raise ExecutionJournalValidationError("journal current-event hash mismatch")
    if seen_ids is not None and event["event_id"] in seen_ids:
        raise ExecutionJournalValidationError("duplicate journal event ID")
    clean_event = deepcopy(event)
    clean_event["payload"] = clean_payload
    return clean_event


class ExecutionJournal:
    """An in-memory validated hash chain of execution audit events."""

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
            raise ExecutionJournalValidationError("journal event count exceeds the bound")
        encoded = deterministic_json_text(self.to_document()).encode("utf-8")
        if len(encoded) > MAX_JOURNAL_BYTES:
            raise ExecutionJournalValidationError("journal exceeds the byte bound")

    def append(self, event_type, occurred_at_utc, payload):
        if event_type not in EVENT_TYPES:
            raise ExecutionJournalValidationError("execution journal event type is not governed")
        validate_utc_timestamp(occurred_at_utc, "occurred_at_utc")
        if self._events:
            prior = validate_utc_timestamp(self._events[-1]["occurred_at_utc"])
            if validate_utc_timestamp(occurred_at_utc) < prior:
                raise ExecutionJournalValidationError("execution journal event was backdated")
        clean_payload = _sanitize_payload_value(payload)
        payload_text = deterministic_json_text(clean_payload)
        if len(payload_text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise ExecutionJournalValidationError("journal payload exceeds the byte bound")
        payload_hash = sha256_text(payload_text)
        stable_fields = {
            "schema_version": JOURNAL_EVENT_SCHEMA,
            "event_type": event_type,
            "occurred_at_utc": occurred_at_utc,
            "payload_sha256": payload_hash,
        }
        event_id = "mje_" + sha256_text(deterministic_json_text(stable_fields))[:32]
        if any(item["event_id"] == event_id for item in self._events):
            raise ExecutionJournalValidationError("duplicate journal event ID")
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
            "schema_version": "TRL_MT5_EXECUTION_JOURNAL.v1",
            "event_count": len(self._events),
            "tail_event_hash": self.tail_hash,
            "events": deepcopy(self._events),
        }

    @classmethod
    def from_document(cls, document):
        expected = ("schema_version", "event_count", "tail_event_hash", "events")
        _require_exact_keys(document, expected, "execution journal")
        if document["schema_version"] != "TRL_MT5_EXECUTION_JOURNAL.v1":
            raise ExecutionJournalValidationError("execution journal schema is unsupported")
        count = document["event_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ExecutionJournalValidationError("execution journal event count is invalid")
        if not isinstance(document["events"], list) or count != len(document["events"]):
            raise ExecutionJournalValidationError("execution journal is truncated or count-mismatched")
        journal = cls(document["events"])
        if document["tail_event_hash"] != journal.tail_hash:
            raise ExecutionJournalValidationError("execution journal tail hash mismatch")
        return journal


def validate_storage_document(document):
    expected = {"schema_version", "storage_id", "session_started_at_utc", "journal"}
    if not isinstance(document, dict) or set(document) != expected:
        raise ExecutionJournalStorageValidationError("execution journal storage has an invalid field set")
    if document["schema_version"] != JOURNAL_STORE_SCHEMA:
        raise ExecutionJournalStorageValidationError("execution journal storage schema is unsupported")
    if document["storage_id"] != JOURNAL_STORE_ID:
        raise ExecutionJournalStorageValidationError("execution journal storage identity is invalid")
    try:
        validate_utc_timestamp(document["session_started_at_utc"])
        journal = ExecutionJournal.from_document(document["journal"])
    except ExecutionJournalValidationError as error:
        raise ExecutionJournalStorageValidationError(str(error)) from error
    clean = {
        "schema_version": JOURNAL_STORE_SCHEMA,
        "storage_id": JOURNAL_STORE_ID,
        "session_started_at_utc": document["session_started_at_utc"],
        "journal": journal.to_document(),
    }
    if len((deterministic_json_text(clean) + "\n").encode("utf-8")) > MAX_JOURNAL_BYTES:
        raise ExecutionJournalStorageValidationError("execution journal storage exceeds the byte bound")
    return clean


def storage_document(session_started_at_utc, journal):
    if not isinstance(journal, ExecutionJournal):
        raise ExecutionJournalStorageValidationError("execution journal storage requires a validated journal")
    return validate_storage_document({
        "schema_version": JOURNAL_STORE_SCHEMA,
        "storage_id": JOURNAL_STORE_ID,
        "session_started_at_utc": session_started_at_utc,
        "journal": journal.to_document(),
    })


def _reject_constant(_value):
    raise ExecutionJournalStorageValidationError("execution journal storage contains a non-finite number")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ExecutionJournalStorageValidationError("execution journal storage contains a duplicate object key")
        result[key] = value
    return result


def _parse_document(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_JOURNAL_BYTES:
        raise ExecutionJournalStorageValidationError("execution journal storage exceeds the byte bound")
    try:
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ExecutionJournalStorageValidationError("execution journal storage is not strict UTF-8 JSON") from error
    return validate_storage_document(document)


class InMemoryExecutionJournalStore:
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
            raise ExecutionJournalStorageError("execution journal storage atomic write failed")
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
    return root / "ALSAKKAF" / "TradingLab" / "mt5-execution-journal-v1.json"


class LocalExecutionJournalStore:
    """Atomic single-document storage, mirroring the mode store's design."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_journal_store_path()

    def load(self):
        if not self.path.exists():
            return None
        try:
            raw = self.path.read_bytes()
            return _parse_document(raw)
        except ExecutionJournalStorageValidationError:
            raise
        except OSError as error:
            raise ExecutionJournalStorageError("execution journal storage read failed") from error

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
            raise ExecutionJournalStorageError("execution journal storage atomic write failed") from error
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
    durable store into the writer's in-memory journal before yielding, so
    the caller's search sees the freshest persisted state; on exit,
    releases the underlying lock unconditionally."""

    def __init__(self, writer):
        self._writer = writer
        self._inner = writer.store.lock()

    def __enter__(self):
        self._inner.__enter__()
        self._writer._load()
        return self._writer

    def __exit__(self, exc_type, exc_value, traceback):
        return self._inner.__exit__(exc_type, exc_value, traceback)


class ExecutionJournalWriter:
    """The single authoritative append path: loads on construction,
    validates, and persists atomically on every append. A corrupted store
    fails closed at construction rather than silently starting empty."""

    def __init__(self, store=None, session_started_at_utc=None, clock=None):
        self.store = store if store is not None else LocalExecutionJournalStore()
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
        except ExecutionJournalStorageValidationError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_INVALID"
            self._journal = ExecutionJournal()
            return
        except ExecutionJournalStorageError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_READ_FAILED"
            self._journal = ExecutionJournal()
            return
        if loaded is None:
            self._journal = ExecutionJournal()
            return
        try:
            self._journal = ExecutionJournal.from_document(loaded["journal"])
        except ExecutionJournalValidationError:
            self.startup_diagnostic_code = "JOURNAL_STORAGE_INVALID"
            self._journal = ExecutionJournal()

    @property
    def events(self):
        return self._journal.events

    def acquire_creation_lock(self):
        """A cross-process critical section for the "search the durable
        store, then decide, then persist" sequences in
        ``mt5_execution_service.py`` (order-intent lookup-before-create,
        order-send duplicate-checking). Reloads from the durable store
        immediately after acquiring the lock, so ``self.events`` reflects
        the latest state any other process may have persisted while this
        caller was waiting — a stale in-memory snapshot loaded only at
        construction time would otherwise defeat the lock entirely."""
        return _ReloadingLock(self)

    def append(self, event_type, payload, occurred_at_utc=None):
        occurred = occurred_at_utc or format_utc(self._clock())
        event = self._journal.append(event_type, occurred, payload)
        document = storage_document(self._session_started_at_utc, self._journal)
        try:
            self.store.save(document)
        except ExecutionJournalStorageError:
            self.persistence_status = "WRITE_FAILED_IN_MEMORY_VALID"
            self.persistence_failure_count += 1
        else:
            self.persistence_status = "OK"
        return event

    def to_document(self):
        return {
            "schema_version": "TRL_MT5_EXECUTION_JOURNAL_VIEW.v1",
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


def in_memory_journal_writer(session_started_at_utc=None, clock=None):
    return ExecutionJournalWriter(
        store=InMemoryExecutionJournalStore(), session_started_at_utc=session_started_at_utc, clock=clock,
    )


__all__ = (
    "EVENT_TYPES",
    "ExecutionJournal",
    "ExecutionJournalLockTimeout",
    "ExecutionJournalStorageError",
    "ExecutionJournalStorageValidationError",
    "ExecutionJournalValidationError",
    "ExecutionJournalWriter",
    "InMemoryExecutionJournalStore",
    "LocalExecutionJournalStore",
    "default_journal_store_path",
    "in_memory_journal_writer",
    "storage_document",
    "validate_storage_document",
)
