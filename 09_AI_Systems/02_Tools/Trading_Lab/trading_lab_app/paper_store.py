"""Bounded local persistence for the forward paper timeline."""

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


PAPER_STORE_SCHEMA = "TRL_FORWARD_PAPER_STORE.v1"
PAPER_STORE_ID = "trl-forward-paper-local-store-v1"
MAX_STORE_BYTES = MAX_TIMELINE_BYTES + 64 * 1024


class PaperStorageError(RuntimeError):
    """Controlled storage failure with no path or exception-detail disclosure."""


class PaperStorageValidationError(PaperStorageError):
    """Invalid persisted content; callers must fail closed."""


def _reject_constant(_value):
    raise PaperStorageValidationError("paper storage contains a non-finite number")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise PaperStorageValidationError("paper storage contains a duplicate object key")
        result[key] = value
    return result


def _parse_document(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_STORE_BYTES:
        raise PaperStorageValidationError("paper storage exceeds the byte bound")
    try:
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(
            text,
            parse_float=Decimal,
            parse_constant=_reject_constant,
            object_pairs_hook=_unique_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise PaperStorageValidationError("paper storage is not strict UTF-8 JSON") from error
    return validate_storage_document(document)


def validate_storage_document(document):
    expected = {"schema_version", "storage_id", "settings", "timeline"}
    if not isinstance(document, dict) or set(document) != expected:
        raise PaperStorageValidationError("paper storage has an invalid field set")
    if document["schema_version"] != PAPER_STORE_SCHEMA:
        raise PaperStorageValidationError("paper storage schema is unsupported")
    if document["storage_id"] != PAPER_STORE_ID:
        raise PaperStorageValidationError("paper storage identity is invalid")
    try:
        settings = sanitize_payload(document["settings"])
        timeline = MarketTimeline.from_document(document["timeline"])
    except TimelineValidationError as error:
        raise PaperStorageValidationError(str(error)) from error
    clean = {
        "schema_version": PAPER_STORE_SCHEMA,
        "storage_id": PAPER_STORE_ID,
        "settings": settings,
        "timeline": timeline.to_document(),
    }
    if len((deterministic_json_text(clean) + "\n").encode("utf-8")) > MAX_STORE_BYTES:
        raise PaperStorageValidationError("paper storage exceeds the byte bound")
    return clean


def storage_document(settings, timeline):
    if not isinstance(timeline, MarketTimeline):
        raise PaperStorageValidationError("paper storage requires a validated timeline")
    return validate_storage_document({
        "schema_version": PAPER_STORE_SCHEMA,
        "storage_id": PAPER_STORE_ID,
        "settings": deepcopy(settings),
        "timeline": timeline.to_document(),
    })


class InMemoryPaperStore:
    """Exact serialization round-trip storage used by deterministic tests."""

    def __init__(self, initial_document=None):
        self._document = None
        self._trusted_snapshot = None
        self.fail_writes = False
        self.save_count = 0
        if initial_document is not None:
            clean = validate_storage_document(initial_document)
            self._document = deepcopy(clean)
            self._trusted_snapshot = deepcopy(clean)

    @property
    def trusted_snapshot(self):
        return deepcopy(self._trusted_snapshot)

    def load(self):
        if self._document is None:
            return None
        raw = (deterministic_json_text(self._document) + "\n").encode("utf-8")
        clean = _parse_document(raw)
        self._trusted_snapshot = deepcopy(clean)
        return deepcopy(clean)

    def save(self, document):
        clean = validate_storage_document(document)
        raw = (deterministic_json_text(clean) + "\n").encode("utf-8")
        clean = _parse_document(raw)
        if self.fail_writes:
            raise PaperStorageError("paper storage atomic write failed")
        self._document = deepcopy(clean)
        self._trusted_snapshot = deepcopy(clean)
        self.save_count += 1

    def replace_raw_for_test(self, raw):
        """Install controlled invalid content without production filesystem effects."""
        if isinstance(raw, bytes):
            self._document = json.loads(raw.decode("utf-8"))
        else:
            self._document = deepcopy(raw)

    def shutdown(self):
        return True


def default_paper_store_path():
    """Return an isolated application-data path; never create it here."""
    local_data = os.environ.get("LOCALAPPDATA")
    if local_data:
        root = Path(local_data)
    else:
        root = Path.home() / "AppData" / "Local"
    return root / "ALSAKKAF" / "TradingLab" / "forward-paper-timeline-v1.json"


class LocalPaperStore:
    """Atomic single-document storage with trusted-snapshot retention."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_paper_store_path()
        self._trusted_snapshot = None
        self._shutdown = False

    @property
    def trusted_snapshot(self):
        return deepcopy(self._trusted_snapshot)

    def load(self):
        if not self.path.exists():
            return None
        try:
            raw = self.path.read_bytes()
            clean = _parse_document(raw)
        except PaperStorageValidationError:
            raise
        except OSError as error:
            raise PaperStorageError("paper storage read failed") from error
        self._trusted_snapshot = deepcopy(clean)
        return deepcopy(clean)

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
            raise PaperStorageError("paper storage atomic write failed") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass
        self._trusted_snapshot = deepcopy(clean)

    def shutdown(self):
        self._shutdown = True
        return True
