"""Bounded local JSON cache for governed title/link and schedule metadata."""

import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import tempfile

from . import news_data, news_sources


CACHE_SCHEMA_VERSION = "TRL-OFFICIAL-NEWS-CACHE-1.0"
CACHE_DIRECTORY_NAME = "official_news"
CACHE_FILE_NAME = "cache-v1.json"
MAX_CACHE_RECORDS = 1000
MAX_CACHE_BYTES = 5 * 1024 * 1024
MAX_RETENTION_DAYS = 30
MAX_FUTURE_TOLERANCE = timedelta(minutes=5)
_FINGERPRINT = re.compile(r"^[0-9a-f]{64}$")


class CacheError(OSError):
    def __init__(self, reason_code):
        super().__init__(reason_code)
        self.reason_code = reason_code


def _reject_nonfinite(value):
    raise CacheError("NEWS_CACHE_INVALID")


def _reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CacheError("NEWS_CACHE_INVALID")
        result[key] = value
    return result


def decode_cache_bytes(raw):
    """Decode strict cache JSON, including rejection of nonfinite constants."""
    try:
        if type(raw) is not bytes or len(raw) > MAX_CACHE_BYTES:
            raise CacheError("NEWS_CACHE_INVALID")
        text = raw.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_reject_duplicate_keys,
            parse_constant=_reject_nonfinite,
        )
    except CacheError:
        raise
    except (
        OSError, UnicodeError, TypeError, ValueError, OverflowError,
        RecursionError, json.JSONDecodeError,
    ) as error:
        raise CacheError("NEWS_CACHE_INVALID") from error


def deterministic_bytes(value, reason_code="NEWS_CACHE_INVALID"):
    try:
        return (json.dumps(
            value, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ) + "\n").encode("utf-8")
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as error:
        raise CacheError(reason_code) from error


class InMemoryCacheStorage:
    """Injected test storage; it never touches LOCALAPPDATA."""

    def __init__(self, initial=None, fail_load=False, fail_write=False):
        self.value = copy.deepcopy(initial)
        self.fail_load = fail_load
        self.fail_write = fail_write
        self.write_attempt_count = 0
        self.write_count = 0

    def load(self):
        if self.fail_load:
            raise CacheError("NEWS_CACHE_INVALID")
        return copy.deepcopy(self.value)

    def write(self, value):
        self.write_attempt_count += 1
        if self.fail_write:
            raise CacheError("NEWS_CACHE_WRITE_FAILED")
        self.value = copy.deepcopy(value)
        self.write_count += 1


class FileCacheStorage:
    """Atomic cache storage at the one fixed production location."""

    def __init__(self, path):
        self.path = Path(path)

    def load(self):
        try:
            if not self.path.exists():
                return None
            if self.path.stat().st_size > MAX_CACHE_BYTES:
                raise CacheError("NEWS_CACHE_INVALID")
            raw = self.path.read_bytes()
            if len(raw) > MAX_CACHE_BYTES:
                raise CacheError("NEWS_CACHE_INVALID")
            return decode_cache_bytes(raw)
        except CacheError:
            raise
        except (OSError, UnicodeError, TypeError, ValueError, json.JSONDecodeError) as error:
            raise CacheError("NEWS_CACHE_INVALID") from error

    def write(self, value):
        body = deterministic_bytes(value, "NEWS_CACHE_WRITE_FAILED")
        if len(body) > MAX_CACHE_BYTES:
            raise CacheError("NEWS_CACHE_WRITE_FAILED")
        descriptor = None
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temporary_name = tempfile.mkstemp(
                prefix="." + self.path.name + ".",
                suffix=".tmp",
                dir=str(self.path.parent),
            )
            temporary = Path(temporary_name)
            handle = os.fdopen(descriptor, "wb")
            descriptor = None
            with handle:
                handle.write(body)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            temporary = None
        except (OSError, TypeError, ValueError) as error:
            raise CacheError("NEWS_CACHE_WRITE_FAILED") from error
        finally:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            try:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            except OSError:
                pass


def production_storage(environment=None):
    values = os.environ if environment is None else environment
    base = values.get("LOCALAPPDATA")
    if not base:
        raise CacheError("NEWS_CACHE_INVALID")
    return FileCacheStorage(
        Path(base) / "ALSAKKAF_TRL" / CACHE_DIRECTORY_NAME / CACHE_FILE_NAME
    )


def empty_document(saved_timestamp_utc):
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "saved_timestamp_utc": saved_timestamp_utc,
        "records": [],
    }


def _parsed_utc(value):
    try:
        canonical = news_data.canonical_cached_timestamp(value)
        parsed = datetime.fromisoformat(canonical[:-1] + "+00:00")
    except (AttributeError, TypeError, ValueError, news_data.NewsValidationError) as error:
        raise CacheError("NEWS_CACHE_INVALID") from error
    if parsed.tzinfo is None:
        raise CacheError("NEWS_CACHE_INVALID")
    return parsed.astimezone(timezone.utc)


def _validate_document(document, now, registry, enforce_bounds=True):
    try:
        source_map = news_sources.validated_source_map(registry)
    except news_sources.SourceRegistryError as error:
        raise CacheError("NEWS_CACHE_INVALID") from error
    if type(now) is not datetime or now.tzinfo is None:
        raise CacheError("NEWS_CACHE_INVALID")
    now_utc = now.astimezone(timezone.utc)
    if document is None:
        return empty_document(news_data.utc_timestamp(now))
    if type(document) is not dict or set(document) != {
        "schema_version", "saved_timestamp_utc", "records",
    }:
        raise CacheError("NEWS_CACHE_INVALID")
    if document["schema_version"] != CACHE_SCHEMA_VERSION:
        raise CacheError("NEWS_CACHE_INVALID")
    saved = _parsed_utc(document["saved_timestamp_utc"])
    if saved > now_utc + MAX_FUTURE_TOLERANCE:
        raise CacheError("NEWS_CACHE_INVALID")
    records = document["records"]
    if type(records) is not list or (enforce_bounds and len(records) > MAX_CACHE_RECORDS):
        raise CacheError("NEWS_CACHE_INVALID")
    seen = set()
    cutoff = now_utc - timedelta(days=MAX_RETENTION_DAYS)
    accepted = []
    validated_all = []
    for wrapper in records:
        if type(wrapper) is not dict or set(wrapper) != {
            "kind", "identity", "fingerprint", "first_seen_timestamp_utc",
            "last_seen_timestamp_utc", "record",
        }:
            raise CacheError("NEWS_CACHE_INVALID")
        if type(wrapper["kind"]) is not str or wrapper["kind"] not in {"news", "event"}:
            raise CacheError("NEWS_CACHE_INVALID")
        identity = wrapper["identity"]
        fingerprint = wrapper["fingerprint"]
        if (
            type(identity) is not str or not identity or len(identity) > 100
            or type(fingerprint) is not str
            or _FINGERPRINT.fullmatch(fingerprint) is None
            or (wrapper["kind"], identity) in seen
        ):
            raise CacheError("NEWS_CACHE_INVALID")
        seen.add((wrapper["kind"], identity))
        first_seen = _parsed_utc(wrapper["first_seen_timestamp_utc"])
        last_seen = _parsed_utc(wrapper["last_seen_timestamp_utc"])
        if (
            first_seen > last_seen
            or last_seen > now_utc + MAX_FUTURE_TOLERANCE
            or last_seen > saved
        ):
            raise CacheError("NEWS_CACHE_INVALID")
        record = wrapper["record"]
        id_field = "news_id" if wrapper["kind"] == "news" else "event_id"
        if type(record) is not dict:
            raise CacheError("NEWS_CACHE_INVALID")
        source_id = record.get("source_id")
        if type(source_id) is not str or source_id not in source_map:
            raise CacheError("NEWS_CACHE_INVALID")
        try:
            validated_record = news_data.validate_cached_record(
                wrapper["kind"], record, source_map[source_id]
            )
        except news_data.NewsValidationError as error:
            raise CacheError("NEWS_CACHE_INVALID") from error
        retrieved = _parsed_utc(validated_record["retrieved_timestamp_utc"])
        published_value = validated_record["published_timestamp_utc"]
        published = _parsed_utc(published_value) if published_value is not None else None
        if (
            validated_record[id_field] != identity
            or retrieved != last_seen
            or retrieved > now_utc + MAX_FUTURE_TOLERANCE
            or (published is not None and published > now_utc + MAX_FUTURE_TOLERANCE)
            or (published is not None and published > retrieved + MAX_FUTURE_TOLERANCE)
            or news_data.observation_fingerprint(validated_record) != fingerprint
        ):
            raise CacheError("NEWS_CACHE_INVALID")
        accepted_wrapper = copy.deepcopy(wrapper)
        accepted_wrapper["record"] = validated_record
        validated_all.append(accepted_wrapper)
        if last_seen >= cutoff:
            accepted.append(accepted_wrapper)
    if enforce_bounds:
        bounded = empty_document(document["saved_timestamp_utc"])
        bounded["records"] = validated_all
        if len(deterministic_bytes(bounded)) > MAX_CACHE_BYTES:
            raise CacheError("NEWS_CACHE_INVALID")
    result = empty_document(document["saved_timestamp_utc"])
    result["records"] = accepted
    return result


def validate_document(document, now, registry, enforce_bounds=True):
    try:
        return _validate_document(
            document, now, registry, enforce_bounds=enforce_bounds
        )
    except CacheError:
        raise
    except (TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as error:
        raise CacheError("NEWS_CACHE_INVALID") from error


def prune_document(document, now, registry):
    candidate = copy.deepcopy(document)
    if type(candidate) is dict and "saved_timestamp_utc" in candidate:
        candidate["saved_timestamp_utc"] = news_data.utc_timestamp(now)
    validated = validate_document(
        candidate, now, registry, enforce_bounds=False
    )
    cutoff = now.astimezone(timezone.utc) - timedelta(days=MAX_RETENTION_DAYS)
    records = [
        wrapper for wrapper in validated["records"]
        if _parsed_utc(wrapper["last_seen_timestamp_utc"]) >= cutoff
    ]
    records.sort(key=lambda wrapper: (
        wrapper["last_seen_timestamp_utc"], wrapper["kind"], wrapper["identity"]
    ))
    if len(records) > MAX_CACHE_RECORDS:
        records = records[-MAX_CACHE_RECORDS:]
    result = empty_document(news_data.utc_timestamp(now))
    result["records"] = records
    while records and len(deterministic_bytes(result)) > MAX_CACHE_BYTES:
        records.pop(0)
    if len(deterministic_bytes(result)) > MAX_CACHE_BYTES:
        raise CacheError("NEWS_CACHE_WRITE_FAILED")
    return result
