"""Deterministic, read-only loading for the packaged local strategy vault."""

import hashlib
import json
import math
from pathlib import Path


CATALOG_DIRECTORY = Path(__file__).resolve().parent / "strategy_catalog"
EXECUTABLE_FILENAME = "SMA-001.1.0.0.json"
BACKLOG_FILENAME = "research_backlog.json"
ALLOWED_FILENAMES = (EXECUTABLE_FILENAME, BACKLOG_FILENAME)
CATALOG_PATH_PREFIX = "trading_lab_app/strategy_catalog/"
MAX_FILE_BYTES = 131072
MAX_JSON_DEPTH = 12
MAX_JSON_NODES = 4096
MAX_INTEGER_BITS = 512
MAX_FLOAT_MAGNITUDE = 1e150

# Filled from the reviewed, normalized packaged catalog. These are intentionally
# code-owned trust anchors rather than values stored beside their own definitions.
PACKAGED_NORMALIZED_FILE_DIGESTS = {
    EXECUTABLE_FILENAME: "a34e6be5fb95c6523139839837218846c6f2be93f5d29fbc0551ac2c5dfde95a",
    BACKLOG_FILENAME: "34c88a6502feb52aaf9187dd7f6ea76b95d23b2fab9d47a1debd450b6a5fcbfd",
}
PACKAGED_CANONICAL_DIGESTS = {
    EXECUTABLE_FILENAME: "3cc2c876ad7c11d2244f9f71ab9a62cdc7f8baac0f5d3964173faa4d9e7e4878",
    BACKLOG_FILENAME: "5029263efdb47563852ba93733f6d84a2cb4c757d32e57a29a604b952ec75a63",
}
PACKAGED_BUNDLE_DIGEST = "62a549288ab65fd543f7550416c96f01d65a3ecf3f128aa7b31b2de1ddc21d7b"


class VaultFailure(Exception):
    """A stable internal signal carrying a public fail-closed reason code."""

    def __init__(self, reason_code):
        super().__init__(reason_code)
        self.reason_code = reason_code


def normalize_newlines(raw_bytes):
    """Normalize CRLF and bare CR bytes to LF, matching Release 1 principles."""
    if type(raw_bytes) is not bytes:
        raise TypeError("raw_bytes must be exact bytes")
    return raw_bytes.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def canonical_json_bytes(value):
    """Return deterministic UTF-8 JSON with a single terminal LF."""
    text = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return (text + "\n").encode("utf-8")


def sha256_hex(data):
    if type(data) is not bytes:
        raise TypeError("data must be exact bytes")
    return hashlib.sha256(data).hexdigest()


def _bounded_json_shape(value):
    nodes = 0
    stack = [(value, 1)]
    while stack:
        item, depth = stack.pop()
        nodes += 1
        if nodes > MAX_JSON_NODES or depth > MAX_JSON_DEPTH:
            raise VaultFailure("REGISTRY_SCHEMA_INVALID")
        if type(item) is dict:
            stack.extend((key, depth + 1) for key in item)
            stack.extend((child, depth + 1) for child in item.values())
        elif type(item) is list:
            stack.extend((child, depth + 1) for child in item)
        elif type(item) is int and item.bit_length() > MAX_INTEGER_BITS:
            raise VaultFailure("REGISTRY_SCHEMA_INVALID")
        elif type(item) is float and (not math.isfinite(item) or abs(item) > MAX_FLOAT_MAGNITUDE):
            raise VaultFailure("REGISTRY_SCHEMA_INVALID")
        elif type(item) not in (str, int, float, bool, type(None)):
            raise VaultFailure("REGISTRY_SCHEMA_INVALID")


def _object_without_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate JSON object field")
        value[key] = item
    return value


def _read_json_file(path):
    try:
        raw = path.read_bytes()
    except FileNotFoundError as error:
        raise VaultFailure("REGISTRY_FILE_MISSING") from error
    except OSError as error:
        raise VaultFailure("REGISTRY_FILE_MISSING") from error
    if len(raw) > MAX_FILE_BYTES:
        raise VaultFailure("REGISTRY_SCHEMA_INVALID")
    normalized = normalize_newlines(raw)
    try:
        text = normalized.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise VaultFailure("REGISTRY_INVALID_UTF8") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicate_keys,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (json.JSONDecodeError, ValueError) as error:
        raise VaultFailure("REGISTRY_INVALID_JSON") from error
    _bounded_json_shape(value)
    return value, normalized


def _bundle_digest(entries):
    digest = hashlib.sha256()
    digest.update(b"TRL-STRATEGY-VAULT-BUNDLE-V1\n")
    for entry in entries:
        path_bytes = entry["path"].encode("utf-8")
        content = entry["normalized_bytes"]
        digest.update(b"PATH\0")
        digest.update(str(len(path_bytes)).encode("ascii"))
        digest.update(b"\0")
        digest.update(path_bytes)
        digest.update(b"\0LENGTH\0")
        digest.update(str(len(content)).encode("ascii"))
        digest.update(b"\0CONTENT\0")
        digest.update(content)
        digest.update(b"\0END\n")
    return digest.hexdigest()


def inspect_catalog():
    """Load only the exact catalog allowlist and return data plus provenance."""
    catalog_directory = CATALOG_DIRECTORY
    try:
        paths = sorted(catalog_directory.iterdir(), key=lambda path: path.name)
    except (FileNotFoundError, OSError) as error:
        raise VaultFailure("REGISTRY_FILE_MISSING") from error
    names = [path.name for path in paths]
    missing = sorted(set(ALLOWED_FILENAMES) - set(names))
    if missing:
        raise VaultFailure("REGISTRY_FILE_MISSING")
    unexpected = sorted(set(names) - set(ALLOWED_FILENAMES))
    if any(not path.is_file() or path.is_symlink() for path in paths):
        unexpected.append("UNSAFE_CATALOG_PATH")
    if unexpected:
        raise VaultFailure("REGISTRY_UNEXPECTED_FILE")

    loaded = {}
    entries = []
    for filename in ALLOWED_FILENAMES:
        value, normalized = _read_json_file(catalog_directory / filename)
        canonical_digest = sha256_hex(canonical_json_bytes(value))
        normalized_digest = sha256_hex(normalized)
        if canonical_digest != PACKAGED_CANONICAL_DIGESTS[filename]:
            raise VaultFailure("REGISTRY_IDENTITY_MISMATCH")
        if normalized_digest != PACKAGED_NORMALIZED_FILE_DIGESTS[filename]:
            raise VaultFailure("REGISTRY_IDENTITY_MISMATCH")
        loaded[filename] = value
        entries.append({
            "path": CATALOG_PATH_PREFIX + filename,
            "byte_length": len(normalized),
            "normalized_sha256": normalized_digest,
            "canonical_json_sha256": canonical_digest,
            "normalized_bytes": normalized,
        })
    entries.sort(key=lambda entry: entry["path"])
    bundle_digest = _bundle_digest(entries)
    if bundle_digest != PACKAGED_BUNDLE_DIGEST:
        raise VaultFailure("REGISTRY_BUNDLE_DIGEST_MISMATCH")
    public_manifest = []
    for entry in entries:
        public_manifest.append({
            "path": entry["path"],
            "byte_length": entry["byte_length"],
            "normalized_sha256": entry["normalized_sha256"],
            "canonical_json_sha256": entry["canonical_json_sha256"],
        })
    return {
        "documents": loaded,
        "manifest": public_manifest,
        "bundle_digest": bundle_digest,
    }


__all__ = (
    "ALLOWED_FILENAMES",
    "BACKLOG_FILENAME",
    "CATALOG_DIRECTORY",
    "EXECUTABLE_FILENAME",
    "MAX_FILE_BYTES",
    "MAX_JSON_DEPTH",
    "MAX_JSON_NODES",
    "PACKAGED_BUNDLE_DIGEST",
    "PACKAGED_CANONICAL_DIGESTS",
    "PACKAGED_NORMALIZED_FILE_DIGESTS",
    "VaultFailure",
    "canonical_json_bytes",
    "inspect_catalog",
    "normalize_newlines",
    "sha256_hex",
)
