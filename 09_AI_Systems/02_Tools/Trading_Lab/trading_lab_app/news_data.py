"""Strict governed schemas and deterministic identities for official metadata."""

import hashlib
import html
from html.parser import HTMLParser
import json
import math
import re
import unicodedata
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import unquote_to_bytes, urlsplit, urlunsplit

from . import news_sources


NEWS_ITEM_SCHEMA = "TRL-OFFICIAL-NEWS-ITEM-1.3"
ECONOMIC_EVENT_SCHEMA = "TRL-OFFICIAL-ECONOMIC-EVENT-1.3"
NEWS_COLLECTION_SCHEMA = "TRL-OFFICIAL-NEWS-COLLECTION-1.2"
EVENT_COLLECTION_SCHEMA = "TRL-OFFICIAL-ECONOMIC-EVENT-COLLECTION-1.3"
CONTENT_RETENTION_STATUS = "TITLE_LINK_METADATA_ONLY; FULL_TEXT_NOT_RETAINED"
SOURCE_NOT_PROVIDED = "SOURCE_NOT_PROVIDED"
MAX_TEXT_LENGTH = 500
MAX_TITLE_INPUT_LENGTH = 4096
MAX_TITLE_CANONICALIZATION_PASSES = 8
MAX_URL_LENGTH = 2048
MAX_QUERY_LENGTH = 1024
MAX_QUERY_PARAMETERS = 32
MAX_LIMITATIONS = 32
MAX_REVISION_NUMBER = 2_147_483_647
MAX_ABSOLUTE_SOURCE_NUMBER = 10 ** 100
EVENT_OCCURRENCE_IDENTITY_BASIS = "EVENT_SERIES_SCHEDULED_TIMESTAMP_PRECISION"
EVENT_OCCURRENCE_IDENTITY_LIMITATION = (
    "SOURCE_OCCURRENCE_ID_NOT_PROVIDED: a changed scheduled date is treated as "
    "a new occurrence; reschedule continuity cannot be reliably inferred."
)
BLOCKED_TITLE_CONTAINERS = frozenset((
    "script", "style", "template", "noscript", "form", "iframe", "object",
))
DISCARDED_VOID_TITLE_ELEMENTS = frozenset((
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link",
    "meta", "param", "source", "track", "wbr",
))
NEWS_RECORD_FIELDS = frozenset((
    "schema_version", "news_id", "source_id", "publisher", "title",
    "source_url", "source_url_availability_status", "source_url_reason_code",
    "identity_basis", "identity_ambiguity_reason", "published_timestamp_utc",
    "retrieved_timestamp_utc", "country_or_region", "currency_tags",
    "source_category", "revision_number", "data_quality_status",
    "content_retention_status", "limitations",
))
EVENT_RECORD_FIELDS = frozenset((
    "schema_version", "event_id", "event_series_id",
    "event_series_identity_basis", "event_occurrence_identity_basis",
    "event_occurrence_identity_limitation", "source_id", "publisher", "event_name",
    "scheduled_timestamp_utc", "scheduled_time_precision",
    "published_timestamp_utc", "retrieved_timestamp_utc", "country_or_region",
    "currency_tags", "event_category", "actual", "forecast", "previous",
    "importance", "missing_value_reasons", "revision_number", "source_url",
    "source_url_availability_status", "source_url_reason_code",
    "data_quality_status", "limitations",
))
FALLBACK_LINK_REASONS = frozenset((
    "SOURCE_ITEM_LINK_NOT_PROVIDED", "SOURCE_ITEM_LINK_MALFORMED",
    "SOURCE_ITEM_LINK_HTTPS_REQUIRED", "SOURCE_ITEM_LINK_CREDENTIALS_REJECTED",
    "SOURCE_ITEM_LINK_UNSAFE_PORT", "SOURCE_ITEM_LINK_FRAGMENT_REJECTED",
    "SOURCE_ITEM_LINK_HOST_NOT_GOVERNED", "SOURCE_ITEM_LINK_QUERY_MALFORMED",
    "SOURCE_ITEM_LINK_QUERY_TOO_LARGE",
    "SOURCE_ITEM_LINK_QUERY_TOO_MANY_PARAMETERS",
))
_RFC3339_TIMESTAMP = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?(?:Z|[+-]\d{2}:\d{2})$"
)
_RFC2822_TIMESTAMP = re.compile(
    r"^(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun), \d{1,2} "
    r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) "
    r"\d{4} \d{2}:\d{2}:\d{2} (?:GMT|UTC|[+-]\d{4})$"
)
_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TITLE_TAG_COMPONENTS = re.compile(r"[.:]")
_RESIDUAL_BLOCKED_TITLE_MARKUP = re.compile(
    r"<\s*/?\s*(?:[A-Za-z0-9_-]+[.:])*(?:"
    + "|".join(sorted(BLOCKED_TITLE_CONTAINERS))
    + r")(?:[.:][A-Za-z0-9_-]+)*(?=[\s/>]|$)",
    re.IGNORECASE,
)
_MALFORMED_BLOCKED_TITLE_MARKUP = re.compile(
    r"<\s*/?\s*(?:[A-Za-z0-9_-]+[.:])*(?:"
    + "|".join(sorted(BLOCKED_TITLE_CONTAINERS))
    + r")(?:[.:][A-Za-z0-9_-]+)*[^A-Za-z0-9_.:\s/>-]",
    re.IGNORECASE,
)


class NewsValidationError(ValueError):
    """Governed source metadata failed strict validation."""

    def __init__(self, reason_code):
        super().__init__(reason_code)
        self.reason_code = reason_code


class _UnsafeTitleMarkup(ValueError):
    pass


def title_tag_has_governed_component(tag, governed_names):
    """Match blocked/void names across case, namespace, and dotted tokens."""
    if type(tag) is not str or not tag:
        return False
    components = tuple(
        component for component in _TITLE_TAG_COMPONENTS.split(tag.lower())
        if component
    )
    return any(component in governed_names for component in components)


class _TitleExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.blocked_tags = []

    def handle_starttag(self, tag, attrs):
        normalized = tag.lower()
        if title_tag_has_governed_component(normalized, BLOCKED_TITLE_CONTAINERS):
            self.blocked_tags.append(normalized)
        elif title_tag_has_governed_component(
            normalized, DISCARDED_VOID_TITLE_ELEMENTS
        ):
            return

    def handle_endtag(self, tag):
        normalized = tag.lower()
        if title_tag_has_governed_component(
            normalized, DISCARDED_VOID_TITLE_ELEMENTS
        ):
            raise _UnsafeTitleMarkup("void title element has a closing tag")
        if title_tag_has_governed_component(normalized, BLOCKED_TITLE_CONTAINERS):
            if not self.blocked_tags or self.blocked_tags[-1] != normalized:
                raise _UnsafeTitleMarkup("mismatched blocked title element")
            self.blocked_tags.pop()

    def handle_startendtag(self, tag, attrs):
        normalized = tag.lower()
        if (
            title_tag_has_governed_component(
                normalized, BLOCKED_TITLE_CONTAINERS
            )
            or title_tag_has_governed_component(
                normalized, DISCARDED_VOID_TITLE_ELEMENTS
            )
        ):
            return

    def handle_data(self, data):
        if not self.blocked_tags:
            self.parts.append(data)

    def validated_parts(self):
        if self.blocked_tags:
            raise _UnsafeTitleMarkup("unclosed blocked title element")
        return list(self.parts)


def _title_unicode_is_safe(value):
    for character in value:
        category = unicodedata.category(character)
        if category in {"Cc", "Cf"} and character not in {"\t", "\n", "\r"}:
            return False
    return True


def canonical_title(value):
    """Return one bounded, deterministic, idempotent metadata title."""
    if type(value) is not str or not value or len(value) > MAX_TITLE_INPUT_LENGTH:
        raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    current = value
    for _iteration in range(MAX_TITLE_CANONICALIZATION_PASSES):
        if len(current) > MAX_TITLE_INPUT_LENGTH or not _title_unicode_is_safe(current):
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        if _MALFORMED_BLOCKED_TITLE_MARKUP.search(current):
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        parser = _TitleExtractor()
        try:
            parser.feed(current)
            parser.close()
            decoded = html.unescape(" ".join(parser.validated_parts()))
        except Exception as error:
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID") from error
        if not _title_unicode_is_safe(decoded):
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        cleaned = " ".join(decoded.split())
        if not cleaned or len(cleaned) > MAX_TEXT_LENGTH:
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
        if cleaned == current:
            if _RESIDUAL_BLOCKED_TITLE_MARKUP.search(cleaned):
                raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
            return cleaned
        current = cleaned
    raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")


def _strict_string(value, maximum, allow_empty=False):
    if type(value) is not str or len(value) > maximum or (not allow_empty and not value):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeError as error:
        raise NewsValidationError("NEWS_CACHE_INVALID") from error
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    return value


def canonical_cached_timestamp(value, optional=False):
    """Require the canonical UTC representation emitted by this application."""
    if optional and value is None:
        return None
    _strict_string(value, 100)
    try:
        normalized = parse_source_timestamp(value)
    except NewsValidationError as error:
        raise NewsValidationError("NEWS_CACHE_INVALID") from error
    if normalized != value or not value.endswith("Z"):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    return normalized


def _strict_string_list(value, maximum_items, maximum_length):
    if type(value) is not list or len(value) > maximum_items:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    return [_strict_string(item, maximum_length) for item in value]


def _validate_revision(value):
    if type(value) is not int or not 1 <= value <= MAX_REVISION_NUMBER:
        raise NewsValidationError("NEWS_CACHE_INVALID")


def _validate_optional_source_value(value):
    if value is None:
        return None
    if type(value) is str:
        return _strict_string(value, MAX_TEXT_LENGTH, allow_empty=True)
    if type(value) is int:
        if abs(value) > MAX_ABSOLUTE_SOURCE_NUMBER:
            raise NewsValidationError("NEWS_CACHE_INVALID")
        return value
    if type(value) is float:
        if not math.isfinite(value) or abs(value) > MAX_ABSOLUTE_SOURCE_NUMBER:
            raise NewsValidationError("NEWS_CACHE_INVALID")
        return value
    raise NewsValidationError("NEWS_CACHE_INVALID")


def _validate_cached_link(record, source):
    url = _strict_string(record["source_url"], MAX_URL_LENGTH)
    status = _strict_string(record["source_url_availability_status"], 100)
    reason = _strict_string(record["source_url_reason_code"], 100)
    if status == "GOVERNED_ITEM_LINK_AVAILABLE":
        canonical, expected_status, expected_reason = governed_official_url(url, source)
        if (
            canonical != url
            or expected_status != status
            or expected_reason != reason
        ):
            raise NewsValidationError("NEWS_CACHE_INVALID")
    elif status == "SOURCE_ENDPOINT_FALLBACK":
        if url != source["exact_endpoint"] or reason not in FALLBACK_LINK_REASONS:
            raise NewsValidationError("NEWS_CACHE_INVALID")
    else:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    return status, reason


def _validate_source_metadata(record, source, category_field):
    if (
        record["source_id"] != source["source_id"]
        or record["publisher"] != source["publisher"]
        or record["country_or_region"] != source["country_or_region"]
        or record["currency_tags"] != source["currency_tags"]
        or record[category_field] != source["source_category"]
    ):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _strict_string(record["source_id"], 100)
    _strict_string(record["publisher"], MAX_TEXT_LENGTH)
    _strict_string(record["country_or_region"], 100)
    _strict_string(record[category_field], 100)
    _strict_string_list(record["currency_tags"], 16, 20)


def _validate_news_cache_record(record, source):
    if type(record) is not dict or set(record) != NEWS_RECORD_FIELDS:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    if type(record["schema_version"]) is not str or record["schema_version"] != NEWS_ITEM_SCHEMA:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _validate_source_metadata(record, source, "source_category")
    title = _strict_string(record["title"], MAX_TEXT_LENGTH)
    try:
        canonical = canonical_title(title)
    except NewsValidationError as error:
        raise NewsValidationError("NEWS_CACHE_INVALID") from error
    if canonical != title:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    published = canonical_cached_timestamp(
        record["published_timestamp_utc"], optional=True
    )
    canonical_cached_timestamp(record["retrieved_timestamp_utc"])
    _validate_revision(record["revision_number"])
    status, reason = _validate_cached_link(record, source)
    ambiguity = record["identity_ambiguity_reason"]
    if status == "GOVERNED_ITEM_LINK_AVAILABLE":
        expected_basis = "GOVERNED_ITEM_URL"
        expected_ambiguity = None
        identity_values = (source["source_id"], record["source_url"])
    else:
        identity_values = (
            source["source_id"], status, title, published or SOURCE_NOT_PROVIDED,
        )
        if published is None:
            expected_basis = "SOURCE_FALLBACK_TITLE_ONLY"
            expected_ambiguity = "SOURCE_IDENTITY_AMBIGUOUS_WITHOUT_LINK_OR_TIMESTAMP"
        else:
            expected_basis = "SOURCE_FALLBACK_TITLE_PUBLISHED_TIMESTAMP"
            expected_ambiguity = None
    if (
        record["identity_basis"] != expected_basis
        or ambiguity != expected_ambiguity
        or record["news_id"] != stable_identifier("NEWS", identity_values)
    ):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _strict_string(record["news_id"], 100)
    _strict_string(record["identity_basis"], 100)
    if ambiguity is not None:
        _strict_string(ambiguity, 100)
    expected_quality = (
        "SOURCE_METADATA_VALID" if published else "SOURCE_TIMESTAMP_NOT_PROVIDED"
    )
    if (
        record["data_quality_status"] != expected_quality
        or record["content_retention_status"] != CONTENT_RETENTION_STATUS
    ):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _strict_string(record["data_quality_status"], 100)
    _strict_string(record["content_retention_status"], MAX_TEXT_LENGTH)
    expected_limitations = list(source["limitations"])
    if status == "SOURCE_ENDPOINT_FALLBACK":
        expected_limitations.append(reason)
    if expected_ambiguity is not None:
        expected_limitations.append(expected_ambiguity)
    if record["limitations"] != expected_limitations:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _strict_string_list(record["limitations"], MAX_LIMITATIONS, MAX_TEXT_LENGTH)


def _validate_event_cache_record(record, source):
    if type(record) is not dict or set(record) != EVENT_RECORD_FIELDS:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    if type(record["schema_version"]) is not str or record["schema_version"] != ECONOMIC_EVENT_SCHEMA:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _validate_source_metadata(record, source, "event_category")
    name = _strict_string(record["event_name"], MAX_TEXT_LENGTH)
    try:
        canonical = canonical_title(name)
    except NewsValidationError as error:
        raise NewsValidationError("NEWS_CACHE_INVALID") from error
    if canonical != name:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    scheduled = canonical_cached_timestamp(record["scheduled_timestamp_utc"])
    published = canonical_cached_timestamp(
        record["published_timestamp_utc"], optional=True
    )
    canonical_cached_timestamp(record["retrieved_timestamp_utc"])
    precision = record["scheduled_time_precision"]
    if type(precision) is not str or precision not in {"DATE_ONLY", "TIMESTAMP"}:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    if precision == "DATE_ONLY" and not scheduled.endswith("T00:00:00Z"):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _validate_revision(record["revision_number"])
    status, reason = _validate_cached_link(record, source)
    expected_series_basis = (
        "GOVERNED_ITEM_URL"
        if status == "GOVERNED_ITEM_LINK_AVAILABLE"
        else "SOURCE_ENDPOINT_FALLBACK"
    )
    series_identity_material = (
        record["source_url"]
        if status == "GOVERNED_ITEM_LINK_AVAILABLE"
        else status
    )
    expected_series_id = stable_identifier(
        "EVENT-SERIES",
        (source["source_id"], name, expected_series_basis, series_identity_material),
    )
    expected_identity = stable_identifier(
        "EVENT", (expected_series_id, scheduled, precision)
    )
    if (
        record["event_series_id"] != expected_series_id
        or record["event_series_identity_basis"] != expected_series_basis
        or record["event_occurrence_identity_basis"]
        != EVENT_OCCURRENCE_IDENTITY_BASIS
        or record["event_occurrence_identity_limitation"]
        != EVENT_OCCURRENCE_IDENTITY_LIMITATION
        or record["event_id"] != expected_identity
    ):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _strict_string(record["event_id"], 100)
    _strict_string(record["event_series_id"], 100)
    _strict_string(record["event_series_identity_basis"], 100)
    _strict_string(record["event_occurrence_identity_basis"], 100)
    _strict_string(record["event_occurrence_identity_limitation"], MAX_TEXT_LENGTH)
    reasons = record["missing_value_reasons"]
    value_fields = ("actual", "forecast", "previous", "importance")
    if (
        type(reasons) is not dict
        or set(reasons) != set(value_fields)
        or any(type(key) is not str for key in reasons)
    ):
        raise NewsValidationError("NEWS_CACHE_INVALID")
    for field in value_fields:
        value = _validate_optional_source_value(record[field])
        expected_reason = SOURCE_NOT_PROVIDED if value is None else None
        if reasons[field] != expected_reason:
            raise NewsValidationError("NEWS_CACHE_INVALID")
        if expected_reason is not None:
            _strict_string(reasons[field], 100)
    expected_quality = (
        "SOURCE_DATE_ONLY" if precision == "DATE_ONLY" else "SOURCE_TIMESTAMP_VALID"
    )
    if record["data_quality_status"] != expected_quality:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _strict_string(record["data_quality_status"], 100)
    expected_limitations = list(source["limitations"])
    if status == "SOURCE_ENDPOINT_FALLBACK":
        expected_limitations.append(reason)
    if precision == "DATE_ONLY":
        expected_limitations.append(
            "SOURCE_DATE_ONLY: normalized midnight UTC is a date marker, not an official release time."
        )
    expected_limitations.append(EVENT_OCCURRENCE_IDENTITY_LIMITATION)
    if record["limitations"] != expected_limitations:
        raise NewsValidationError("NEWS_CACHE_INVALID")
    _strict_string_list(record["limitations"], MAX_LIMITATIONS, MAX_TEXT_LENGTH)


def validate_cached_record(kind, record, source):
    """Validate one untrusted cached source-content record without mutation."""
    try:
        news_sources.validated_endpoint_parts(source)
        if kind == "news":
            _validate_news_cache_record(record, source)
        elif kind == "event":
            _validate_event_cache_record(record, source)
        else:
            raise NewsValidationError("NEWS_CACHE_INVALID")
        return json.loads(json.dumps(
            record, ensure_ascii=False, allow_nan=False, sort_keys=True,
            separators=(",", ":"),
        ))
    except NewsValidationError:
        raise
    except (KeyError, TypeError, ValueError, UnicodeError, OverflowError, RecursionError) as error:
        raise NewsValidationError("NEWS_CACHE_INVALID") from error


def utc_timestamp(value):
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    normalized = value.astimezone(timezone.utc)
    text = normalized.isoformat(timespec="microseconds")[:-6]
    text = text.rstrip("0").rstrip(".")
    return text + "Z"


def parse_source_timestamp(value):
    if type(value) is not str or not value or len(value) > 100:
        raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    if _RFC3339_TIMESTAMP.fullmatch(value):
        try:
            if value.endswith("Z"):
                parsed = datetime.fromisoformat(value[:-1] + "+00:00")
            else:
                parsed = datetime.fromisoformat(value)
        except ValueError as error:
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID") from error
    elif _RFC2822_TIMESTAMP.fullmatch(value):
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID") from error
        if parsed.tzinfo is None:
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    else:
        raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    return utc_timestamp(parsed)


def parse_schedule_timestamp(value):
    """Return normalized UTC, quality, and a date-only marker."""
    if type(value) is not str or len(value) > 100:
        raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    if _DATE_ONLY.fullmatch(value) is None:
        return parse_source_timestamp(value), "SOURCE_TIMESTAMP_VALID", False
    try:
        parsed_date = date.fromisoformat(value)
    except ValueError as error:
        raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID") from error
    normalized = datetime(
        parsed_date.year, parsed_date.month, parsed_date.day, tzinfo=timezone.utc
    )
    return utc_timestamp(normalized), "SOURCE_DATE_ONLY", True


def _unsafe_url_characters(value):
    return "\\" in value or any(
        unicodedata.category(character) in {"Cc", "Cf"}
        for character in value
    )


def _decoded_url_component_is_safe(value):
    try:
        decoded = unquote_to_bytes(value).decode("utf-8", errors="strict")
    except UnicodeError:
        return False
    return not _unsafe_url_characters(decoded)


def governed_official_url(value, source):
    """Return a safe URL plus explicit item-link availability and reason."""
    try:
        news_sources.validated_endpoint_parts(source)
    except news_sources.SourceRegistryError as error:
        raise NewsValidationError("NEWS_PROVIDER_CHANGED") from error
    fallback = source["exact_endpoint"]
    if not news_sources.endpoint_is_allowlisted(source, fallback):
        raise NewsValidationError("NEWS_PROVIDER_CHANGED")
    if value is None or value == "":
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_NOT_PROVIDED"
    if type(value) is not str or not value or len(value) > 2048:
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_MALFORMED"
    if (
        value != value.strip()
        or _unsafe_url_characters(value)
        or any(character.isspace() for character in value)
    ):
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_MALFORMED"
    if re.search(r"%(?![0-9A-Fa-f]{2})", value):
        reason = (
            "SOURCE_ITEM_LINK_QUERY_MALFORMED"
            if "?" in value else "SOURCE_ITEM_LINK_MALFORMED"
        )
        return fallback, "SOURCE_ENDPOINT_FALLBACK", reason
    try:
        parts = urlsplit(value)
        port = parts.port
    except ValueError:
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_MALFORMED"
    if parts.scheme != "https":
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_HTTPS_REQUIRED"
    if parts.username is not None or parts.password is not None:
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_CREDENTIALS_REJECTED"
    if port is not None:
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_UNSAFE_PORT"
    if parts.fragment:
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_FRAGMENT_REJECTED"
    hostname = parts.hostname
    if not news_sources.item_link_host_is_allowlisted(source, hostname):
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_HOST_NOT_GOVERNED"
    path = parts.path or "/"
    if not _decoded_url_component_is_safe(path):
        return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_MALFORMED"
    query = parts.query
    if "?" in value:
        if not query:
            return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_QUERY_MALFORMED"
        try:
            encoded_query = query.encode("utf-8", errors="strict")
        except UnicodeError:
            return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_QUERY_MALFORMED"
        if not _decoded_url_component_is_safe(query):
            return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_QUERY_MALFORMED"
        if len(query) > MAX_QUERY_LENGTH or len(encoded_query) > MAX_QUERY_LENGTH:
            return fallback, "SOURCE_ENDPOINT_FALLBACK", "SOURCE_ITEM_LINK_QUERY_TOO_LARGE"
        if query.count("&") + 1 > MAX_QUERY_PARAMETERS:
            return (
                fallback,
                "SOURCE_ENDPOINT_FALLBACK",
                "SOURCE_ITEM_LINK_QUERY_TOO_MANY_PARAMETERS",
            )
    canonical = urlunsplit(("https", hostname, path, query, ""))
    return canonical, "GOVERNED_ITEM_LINK_AVAILABLE", "SOURCE_ITEM_LINK_HOST_GOVERNED"


def canonical_official_url(value, source):
    """Compatibility helper returning only the safely governed URL."""
    return governed_official_url(value, source)[0]


def stable_identifier(prefix, values):
    encoded = json.dumps(
        list(values), ensure_ascii=False, allow_nan=False, separators=(",", ":")
    ).encode("utf-8")
    return "{}-{}".format(prefix, hashlib.sha256(encoded).hexdigest()[:24].upper())


def news_item(source, title, source_url, published_timestamp_utc, retrieved_timestamp_utc):
    title = canonical_title(title)
    published_timestamp_utc = (
        parse_source_timestamp(published_timestamp_utc)
        if published_timestamp_utc is not None else None
    )
    retrieved_timestamp_utc = parse_source_timestamp(retrieved_timestamp_utc)
    canonical_url, link_status, link_reason = governed_official_url(source_url, source)
    if link_status == "GOVERNED_ITEM_LINK_AVAILABLE":
        identity_values = (source["source_id"], canonical_url)
        identity_basis = "GOVERNED_ITEM_URL"
        identity_ambiguity_reason = None
    else:
        identity_values = (
            source["source_id"], link_status, title,
            published_timestamp_utc or SOURCE_NOT_PROVIDED,
        )
        if published_timestamp_utc:
            identity_basis = "SOURCE_FALLBACK_TITLE_PUBLISHED_TIMESTAMP"
            identity_ambiguity_reason = None
        else:
            identity_basis = "SOURCE_FALLBACK_TITLE_ONLY"
            identity_ambiguity_reason = "SOURCE_IDENTITY_AMBIGUOUS_WITHOUT_LINK_OR_TIMESTAMP"
    identity = stable_identifier("NEWS", identity_values)
    quality = "SOURCE_METADATA_VALID" if published_timestamp_utc else "SOURCE_TIMESTAMP_NOT_PROVIDED"
    limitations = list(source["limitations"])
    if link_status != "GOVERNED_ITEM_LINK_AVAILABLE":
        limitations.append(link_reason)
    if identity_ambiguity_reason is not None:
        limitations.append(identity_ambiguity_reason)
    return {
        "schema_version": NEWS_ITEM_SCHEMA,
        "news_id": identity,
        "source_id": source["source_id"],
        "publisher": source["publisher"],
        "title": title,
        "source_url": canonical_url,
        "source_url_availability_status": link_status,
        "source_url_reason_code": link_reason,
        "identity_basis": identity_basis,
        "identity_ambiguity_reason": identity_ambiguity_reason,
        "published_timestamp_utc": published_timestamp_utc,
        "retrieved_timestamp_utc": retrieved_timestamp_utc,
        "country_or_region": source["country_or_region"],
        "currency_tags": list(source["currency_tags"]),
        "source_category": source["source_category"],
        "revision_number": 1,
        "data_quality_status": quality,
        "content_retention_status": CONTENT_RETENTION_STATUS,
        "limitations": limitations,
    }


def economic_event(
    source, event_name, scheduled_value, published_value,
    retrieved_timestamp_utc, source_url, supplied_values=None,
):
    event_name = canonical_title(event_name)
    scheduled, quality, date_only = parse_schedule_timestamp(scheduled_value)
    published = parse_source_timestamp(published_value) if published_value else None
    retrieved_timestamp_utc = parse_source_timestamp(retrieved_timestamp_utc)
    canonical_url, link_status, link_reason = governed_official_url(source_url, source)
    precision = "DATE_ONLY" if date_only else "TIMESTAMP"
    series_basis = (
        "GOVERNED_ITEM_URL"
        if link_status == "GOVERNED_ITEM_LINK_AVAILABLE"
        else "SOURCE_ENDPOINT_FALLBACK"
    )
    series_identity_material = (
        canonical_url
        if link_status == "GOVERNED_ITEM_LINK_AVAILABLE"
        else link_status
    )
    series_identity = stable_identifier(
        "EVENT-SERIES",
        (source["source_id"], event_name, series_basis, series_identity_material),
    )
    identity = stable_identifier("EVENT", (series_identity, scheduled, precision))
    supplied = supplied_values if supplied_values is not None else {}
    if type(supplied) is not dict or not set(supplied).issubset({
        "actual", "forecast", "previous", "importance",
    }):
        raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID")
    values = {}
    reasons = {}
    for field in ("actual", "forecast", "previous", "importance"):
        value = supplied.get(field)
        try:
            values[field] = _validate_optional_source_value(value)
        except NewsValidationError as error:
            raise NewsValidationError("NEWS_SOURCE_SCHEMA_INVALID") from error
        reasons[field] = None if value is not None else SOURCE_NOT_PROVIDED
    limitations = list(source["limitations"])
    if link_status != "GOVERNED_ITEM_LINK_AVAILABLE":
        limitations.append(link_reason)
    if date_only:
        limitations.append(
            "SOURCE_DATE_ONLY: normalized midnight UTC is a date marker, not an official release time."
        )
    limitations.append(EVENT_OCCURRENCE_IDENTITY_LIMITATION)
    return {
        "schema_version": ECONOMIC_EVENT_SCHEMA,
        "event_id": identity,
        "event_series_id": series_identity,
        "event_series_identity_basis": series_basis,
        "event_occurrence_identity_basis": EVENT_OCCURRENCE_IDENTITY_BASIS,
        "event_occurrence_identity_limitation": EVENT_OCCURRENCE_IDENTITY_LIMITATION,
        "source_id": source["source_id"],
        "publisher": source["publisher"],
        "event_name": event_name,
        "scheduled_timestamp_utc": scheduled,
        "scheduled_time_precision": precision,
        "published_timestamp_utc": published,
        "retrieved_timestamp_utc": retrieved_timestamp_utc,
        "country_or_region": source["country_or_region"],
        "currency_tags": list(source["currency_tags"]),
        "event_category": source["source_category"],
        "actual": values["actual"],
        "forecast": values["forecast"],
        "previous": values["previous"],
        "importance": values["importance"],
        "missing_value_reasons": reasons,
        "revision_number": 1,
        "source_url": canonical_url,
        "source_url_availability_status": link_status,
        "source_url_reason_code": link_reason,
        "data_quality_status": quality,
        "limitations": limitations,
    }


def observation_fingerprint(record):
    excluded = {
        "retrieved_timestamp_utc", "revision_number",
        "operational_freshness_status", "latest_source_status",
        "latest_source_failure_reason", "latest_source_attempt_timestamp_utc",
        "last_successfully_observed_timestamp_utc",
    }
    value = {key: record[key] for key in sorted(record) if key not in excluded}
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")).hexdigest()
