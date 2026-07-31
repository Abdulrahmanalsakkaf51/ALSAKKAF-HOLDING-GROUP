"""Bounded local persistence for the signal-intelligence evidence/audit
timeline (TRL-R2-006). Mirrors ``paper_store.py``'s atomic
temp-file-plus-``os.replace`` design and validation strictness exactly,
scoped to its own storage document and default path so it never reads or
writes the R2-005 paper store."""

from copy import deepcopy
from decimal import Decimal
import json
import os
from pathlib import Path
import tempfile

from .timeline_data import (
    MAX_TIMELINE_BYTES,
    MarketTimeline,
    TimelineValidationError,
    deterministic_json_text,
    sanitize_payload,
)


SIGNAL_STORE_SCHEMA = "TRL_SIGNAL_INTELLIGENCE_STORE.v1"
SIGNAL_STORE_ID = "trl-signal-intelligence-local-store-v1"
MAX_STORE_BYTES = MAX_TIMELINE_BYTES + 64 * 1024


class SignalStorageError(RuntimeError):
    """Controlled storage failure with no path or exception-detail disclosure."""


class SignalStorageValidationError(SignalStorageError):
    """Invalid persisted content; callers must fail closed."""


def _reject_constant(_value):
    raise SignalStorageValidationError("signal storage contains a non-finite number")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise SignalStorageValidationError("signal storage contains a duplicate object key")
        result[key] = value
    return result


def _parse_document(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_STORE_BYTES:
        raise SignalStorageValidationError("signal storage exceeds the byte bound")
    try:
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(
            text,
            parse_float=Decimal,
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SignalStorageValidationError("signal storage is not strict UTF-8 JSON") from error
    return validate_storage_document(document)


def validate_storage_document(document):
    expected = {"schema_version", "storage_id", "settings", "timeline"}
    if not isinstance(document, dict) or set(document) != expected:
        raise SignalStorageValidationError("signal storage has an invalid field set")
    if document["schema_version"] != SIGNAL_STORE_SCHEMA:
        raise SignalStorageValidationError("signal storage schema is unsupported")
    if document["storage_id"] != SIGNAL_STORE_ID:
        raise SignalStorageValidationError("signal storage identity is invalid")
    try:
        settings = sanitize_payload(document["settings"])
        timeline = MarketTimeline.from_document(document["timeline"])
    except TimelineValidationError as error:
        raise SignalStorageValidationError(str(error)) from error
    clean = {
        "schema_version": SIGNAL_STORE_SCHEMA,
        "storage_id": SIGNAL_STORE_ID,
        "settings": settings,
        "timeline": timeline.to_document(),
    }
    if len((deterministic_json_text(clean) + "\n").encode("utf-8")) > MAX_STORE_BYTES:
        raise SignalStorageValidationError("signal storage exceeds the byte bound")
    return clean


def storage_document(settings, timeline):
    if not isinstance(timeline, MarketTimeline):
        raise SignalStorageValidationError("signal storage requires a validated timeline")
    return validate_storage_document({
        "schema_version": SIGNAL_STORE_SCHEMA,
        "storage_id": SIGNAL_STORE_ID,
        "settings": deepcopy(settings),
        "timeline": timeline.to_document(),
    })


class InMemorySignalStore:
    """Exact serialization round-trip storage used by deterministic tests
    and as the safe default for every mode (no filesystem access unless a
    caller explicitly wires in ``LocalSignalStore``)."""

    def __init__(self, initial_document=None):
        self._document = None
        self.fail_writes = False
        self.save_count = 0
        if initial_document is not None:
            clean = validate_storage_document(initial_document)
            self._document = deepcopy(clean)

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
            raise SignalStorageError("signal storage atomic write failed")
        self._document = deepcopy(clean)
        self.save_count += 1

    def replace_raw_for_test(self, raw):
        if isinstance(raw, bytes):
            self._document = json.loads(raw.decode("utf-8"))
        else:
            self._document = deepcopy(raw)

    def shutdown(self):
        return True


def default_signal_store_path():
    local_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return root / "ALSAKKAF" / "TradingLab" / "signal-intelligence-timeline-v1.json"


class LocalSignalStore:
    """Atomic single-document storage, mirroring ``LocalPaperStore``."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_signal_store_path()

    def load(self):
        if not self.path.exists():
            return None
        try:
            raw = self.path.read_bytes()
            return _parse_document(raw)
        except SignalStorageValidationError:
            raise
        except OSError as error:
            raise SignalStorageError("signal storage read failed") from error

    def save(self, document):
        clean = validate_storage_document(document)
        raw = (deterministic_json_text(clean) + "\n").encode("utf-8")
        temporary_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=".{}-".format(self.path.name),
                suffix=".tmp",
                dir=str(self.path.parent),
                delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(temporary_path), str(self.path))
            temporary_path = None
        except OSError as error:
            raise SignalStorageError("signal storage atomic write failed") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass

    def shutdown(self):
        return True


__all__ = (
    "InMemorySignalStore",
    "LocalSignalStore",
    "SIGNAL_STORE_SCHEMA",
    "SignalStorageError",
    "SignalStorageValidationError",
    "default_signal_store_path",
    "storage_document",
    "validate_storage_document",
)
