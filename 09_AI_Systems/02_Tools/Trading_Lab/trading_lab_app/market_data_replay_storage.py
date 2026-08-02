"""Immutable, content-addressed local dataset storage for TRL-R2-011 Market
Data Fabric and Replay V0 (Section 10.6, 17.1). Persists one complete
``TRL_MARKET_DATASET_STORAGE_ENVELOPE.v1`` per accepted dataset, filename
derived only from the safe ``dataset_id`` -- never from a source CSV
filename or path. Structurally parallel to
``market_intelligence_journal.LocalMarketIntelligenceJournalStore``'s atomic
temp-file-plus-``os.replace`` write and strict duplicate-key-rejecting
reload, but one file per dataset rather than one shared document, and a
dedicated storage root wholly separate from every journal file in this
repository. The physical storage path is internal configuration and is
never returned by any method here as part of a governed record -- only
``load``/``save`` accept/return the envelope dict itself.

No filesystem-path is ever exposed as governed data: every load fully
revalidates the strict UTF-8 / strict JSON / duplicate-key / exact-field /
identity / hash / correspondence / size rules of Section 10.6 requirement
15 before returning an envelope. Storage files are immutable after
successful acceptance; this module never rewrites an existing final file in
place -- ``save_new`` refuses if the destination already exists.
"""

from decimal import Decimal
import json
import os
from pathlib import Path
import tempfile

from . import market_data_replay_data as mdd


class DatasetStorageError(RuntimeError):
    """Controlled storage failure with no path or exception-detail disclosure."""


def _reject_constant(_value):
    raise DatasetStorageError("dataset storage envelope contains a non-finite numeric constant")


def _unique_object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DatasetStorageError("dataset storage envelope contains a duplicate object key")
        result[key] = value
    return result


def _parse_envelope_bytes(raw):
    if not isinstance(raw, bytes) or len(raw) > mdd.MAX_STORAGE_ENVELOPE_BYTES:
        raise mdd.MarketDataValidationError(
            "MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE",
            "dataset storage envelope exceeds the 268435456-byte bound",
        )
    try:
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_unique_object_pairs)
    except (UnicodeDecodeError, json.JSONDecodeError, DatasetStorageError) as error:
        raise mdd.MarketDataValidationError(
            "MARKET_DATA_STORAGE_INTEGRITY_FAILURE",
            "dataset storage envelope is not strict UTF-8 JSON",
        ) from error
    try:
        return mdd.validate_storage_envelope(document)
    except mdd.MarketDataValidationError as error:
        # Every Section 10.6 requirement-15 revalidation failure on a
        # *stored* envelope is reported under the one governed storage
        # reason code -- never the CSV-import-context codes
        # ``validate_dataset_manifest_record``/``validate_bar_record``
        # raise internally when reused here for schema-shape checking, and
        # never MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE (already raised
        # directly above, before any parse is attempted).
        raise mdd.MarketDataValidationError(
            "MARKET_DATA_STORAGE_INTEGRITY_FAILURE",
            "dataset storage envelope failed revalidation: {}".format(error),
        ) from error


def encode_envelope(envelope):
    """Canonical, deterministic, lossless-decimal JSON bytes for one
    envelope. Numbers are already canonical decimal *text* fields on every
    governed record (Section 8), so ``json.dumps`` never round-trips a
    price through binary float."""
    text = json.dumps(
        envelope, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"), default=_json_default,
    )
    encoded = (text + "\n").encode("utf-8")
    if len(encoded) > mdd.MAX_STORAGE_ENVELOPE_BYTES:
        raise mdd.MarketDataValidationError(
            "MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE",
            "dataset storage envelope exceeds the 268435456-byte bound",
        )
    return encoded


def _json_default(value):
    if isinstance(value, Decimal):
        raise DatasetStorageError("a raw Decimal must never reach envelope encoding directly")
    raise TypeError("object of type {} is not JSON serializable".format(type(value).__name__))


def default_dataset_storage_root():
    """Return an isolated application-data directory; never create it here."""
    local_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return root / "ALSAKKAF" / "TradingLab" / "market-data-fabric-v0" / "datasets"


class LocalDatasetStorage:
    """Atomic, content-addressed, per-dataset local file storage."""

    def __init__(self, root=None):
        self.root = Path(root) if root is not None else default_dataset_storage_root()

    def _path_for(self, dataset_id):
        if not mdd.DATASET_ID_PATTERN.fullmatch(dataset_id or ""):
            raise DatasetStorageError("dataset_id is not a safe identity")
        return self.root / (dataset_id + ".json")

    def exists(self, dataset_id):
        return self._path_for(dataset_id).exists()

    def load(self, dataset_id):
        """Return the fully revalidated envelope, or ``None`` if no
        physical file exists for this dataset_id. Raises
        ``MarketDataValidationError('MARKET_DATA_STORAGE_INTEGRITY_FAILURE'
        or 'MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE')`` on any structural
        failure -- callers must fail closed and never adopt an invalid or
        oversized file."""
        path = self._path_for(dataset_id)
        if not path.exists():
            return None
        try:
            raw = path.read_bytes()
        except OSError as error:
            raise DatasetStorageError("dataset storage read failed") from error
        envelope = _parse_envelope_bytes(raw)
        if envelope["dataset_id"] != dataset_id:
            raise mdd.MarketDataValidationError(
                "MARKET_DATA_STORAGE_INTEGRITY_FAILURE",
                "dataset storage envelope dataset_id does not match its own filename",
            )
        return envelope

    def save_new(self, dataset_id, envelope):
        """Write the envelope exactly once. Storage files are immutable
        after successful acceptance (Section 10.6 requirement 14): this
        refuses to overwrite an already-existing final file."""
        if envelope["dataset_id"] != dataset_id:
            raise DatasetStorageError("envelope dataset_id does not match the requested dataset_id")
        clean = mdd.validate_storage_envelope(envelope)
        encoded = encode_envelope(clean)
        path = self._path_for(dataset_id)
        if path.exists():
            raise DatasetStorageError("a dataset storage file already exists for this dataset_id")
        temporary_path = None
        try:
            self.root.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".{}-".format(path.name), suffix=".tmp",
                dir=str(self.root), delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(temporary_path), str(path))
            temporary_path = None
        except OSError as error:
            raise DatasetStorageError("dataset storage atomic write failed") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass
        return self.load(dataset_id)


class InMemoryDatasetStorage:
    """Exact serialization round-trip storage used by deterministic tests."""

    def __init__(self):
        self._documents = {}
        self.fail_writes = False

    def exists(self, dataset_id):
        return dataset_id in self._documents

    def load(self, dataset_id):
        raw = self._documents.get(dataset_id)
        if raw is None:
            return None
        return _parse_envelope_bytes(raw)

    def save_new(self, dataset_id, envelope):
        if envelope["dataset_id"] != dataset_id:
            raise DatasetStorageError("envelope dataset_id does not match the requested dataset_id")
        clean = mdd.validate_storage_envelope(envelope)
        encoded = encode_envelope(clean)
        if dataset_id in self._documents:
            raise DatasetStorageError("a dataset storage file already exists for this dataset_id")
        if self.fail_writes:
            raise DatasetStorageError("dataset storage atomic write failed")
        self._documents[dataset_id] = encoded
        return self.load(dataset_id)

    def replace_raw_for_test(self, dataset_id, raw):
        self._documents[dataset_id] = raw


__all__ = (
    "DatasetStorageError",
    "encode_envelope",
    "default_dataset_storage_root",
    "LocalDatasetStorage",
    "InMemoryDatasetStorage",
)
