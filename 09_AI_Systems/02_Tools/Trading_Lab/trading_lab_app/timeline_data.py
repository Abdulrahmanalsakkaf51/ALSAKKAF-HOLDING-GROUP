"""Deterministic append-only causal timeline for local paper research."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
import re


TIMELINE_SCHEMA = "TRL_MARKET_TIMELINE.v1"
TIMELINE_EVENT_SCHEMA = "TRL_TIMELINE_EVENT.v1"
TIMELINE_ID = "trl-market-timeline-v1"
GENESIS_HASH = "0" * 64

EVENT_CATEGORIES = (
    "MARKET_OBSERVATION",
    "OFFICIAL_NEWS_OBSERVATION",
    "ECONOMIC_EVENT_OBSERVATION",
    "PAPER_PROPOSAL",
    "PAPER_ENTRY",
    "PAPER_MARK",
    "PAPER_TP",
    "PAPER_STOP",
    "PAPER_EXIT",
    "PAPER_RISK_REJECTION",
    "PAPER_SESSION_EVENT",
    # Added in Phase 4 (TRL-R2-006): one append-only audit event per
    # governed signal-pipeline role outcome (pass or BLOCKED), so a
    # BLOCKED signal proposal is fully auditable after the fact.
    "SIGNAL_PIPELINE_STEP",
)

MAX_TIMELINE_EVENTS = 5000
MAX_TIMELINE_BYTES = 4 * 1024 * 1024
MAX_PAYLOAD_BYTES = 24 * 1024
MAX_STRING_LENGTH = 2048
MAX_SOURCE_LENGTH = 256
MAX_CONTAINER_ITEMS = 128
MAX_PAYLOAD_DEPTH = 7
MAX_INTEGER_ABS = 10 ** 18

_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")
_INSTRUMENT_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,31}$")
_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_HASH_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_EVENT_ID_PATTERN = re.compile(r"^tle_[0-9a-f]{32}$")


class TimelineValidationError(ValueError):
    """A stable, non-secret timeline validation failure."""


def deterministic_json_text(value):
    """Return the sole canonical JSON representation used for identities."""
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def sha256_text(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def format_utc(value):
    """Format an aware UTC datetime in the timeline's strict RFC3339 form."""
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise TimelineValidationError("timestamp must be an aware datetime")
    utc_value = value.astimezone(timezone.utc)
    return utc_value.strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def validate_utc_timestamp(value, field="timestamp"):
    if not isinstance(value, str) or not _UTC_PATTERN.fullmatch(value):
        raise TimelineValidationError(
            "{} must be strict RFC3339 UTC with six fractional digits".format(field)
        )
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError as error:
        raise TimelineValidationError("{} is not a real UTC timestamp".format(field)) from error
    return parsed.replace(tzinfo=timezone.utc)


def canonical_decimal(value, field="number", positive=False, allow_zero=True):
    """Validate an exact number and return a bounded canonical decimal string."""
    if isinstance(value, bool) or isinstance(value, float):
        raise TimelineValidationError("{} must be an exact decimal, not boolean/float".format(field))
    if not isinstance(value, (str, int, Decimal)):
        raise TimelineValidationError("{} must be an exact decimal".format(field))
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as error:
        raise TimelineValidationError("{} must be a valid decimal".format(field)) from error
    if not number.is_finite():
        raise TimelineValidationError("{} must be finite".format(field))
    if abs(number) > Decimal(MAX_INTEGER_ABS):
        raise TimelineValidationError("{} exceeds the numeric bound".format(field))
    if positive and (number < 0 or (number == 0 and not allow_zero)):
        qualifier = "positive" if not allow_zero else "non-negative"
        raise TimelineValidationError("{} must be {}".format(field, qualifier))
    rendered = format(number, "f")
    if "." in rendered:
        rendered = rendered.rstrip("0").rstrip(".")
    if rendered in ("", "-0"):
        rendered = "0"
    if len(rendered) > 80:
        raise TimelineValidationError("{} exceeds the numeric text bound".format(field))
    return rendered


def decimal_value(value, field="number"):
    return Decimal(canonical_decimal(value, field=field))


def validate_instrument(value, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not _INSTRUMENT_PATTERN.fullmatch(value):
        raise TimelineValidationError("instrument must be a bounded canonical symbol")
    return value


def _validate_string(value, field, maximum=MAX_STRING_LENGTH):
    if not isinstance(value, str) or not value or len(value) > maximum:
        raise TimelineValidationError("{} must be a non-empty bounded string".format(field))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise TimelineValidationError("{} contains a control character".format(field))
    return value


def sanitize_payload(value, depth=0):
    """Validate and copy a JSON-shaped payload using exact numeric policy."""
    if depth > MAX_PAYLOAD_DEPTH:
        raise TimelineValidationError("payload nesting exceeds the bound")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        if abs(value) > MAX_INTEGER_ABS:
            raise TimelineValidationError("payload integer exceeds the bound")
        return value
    if isinstance(value, Decimal):
        return canonical_decimal(value, "payload decimal")
    if isinstance(value, float):
        raise TimelineValidationError("payload floats are forbidden; use exact decimals")
    if isinstance(value, str):
        return _validate_string(value, "payload string")
    if isinstance(value, list):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise TimelineValidationError("payload list exceeds the item bound")
        return [sanitize_payload(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > MAX_CONTAINER_ITEMS:
            raise TimelineValidationError("payload object exceeds the item bound")
        clean = {}
        for key, item in value.items():
            if not isinstance(key, str) or not _KEY_PATTERN.fullmatch(key):
                raise TimelineValidationError("payload object key is not canonical")
            clean[key] = sanitize_payload(item, depth + 1)
        return clean
    raise TimelineValidationError("payload contains an unsupported type")


def _require_exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise TimelineValidationError("{} has an invalid field set".format(label))


def _event_without_current_hash(event):
    return {key: value for key, value in event.items() if key != "current_event_hash"}


def validate_timeline_event(event, previous_event=None, seen_ids=None):
    expected = (
        "schema_version",
        "timeline_event_id",
        "event_category",
        "instrument",
        "occurred_at_utc",
        "first_observed_at_utc",
        "append_sequence",
        "governed_source_basis",
        "payload",
        "payload_sha256",
        "previous_event_hash",
        "current_event_hash",
    )
    _require_exact_keys(event, expected, "timeline event")
    if event["schema_version"] != TIMELINE_EVENT_SCHEMA:
        raise TimelineValidationError("timeline event schema is unsupported")
    event_id = event["timeline_event_id"]
    if not isinstance(event_id, str) or not _EVENT_ID_PATTERN.fullmatch(event_id):
        raise TimelineValidationError("timeline event ID is invalid")
    if seen_ids is not None and event_id in seen_ids:
        raise TimelineValidationError("duplicate timeline event ID")
    category = event["event_category"]
    if category not in EVENT_CATEGORIES:
        raise TimelineValidationError("timeline event category is not governed")
    instrument = validate_instrument(event["instrument"], nullable=True)
    occurred = validate_utc_timestamp(event["occurred_at_utc"], "occurred_at_utc")
    observed = validate_utc_timestamp(
        event["first_observed_at_utc"], "first_observed_at_utc"
    )
    if occurred > observed:
        raise TimelineValidationError("event occurrence cannot follow first observation")
    sequence = event["append_sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise TimelineValidationError("append sequence must be a positive integer")
    source = _validate_string(
        event["governed_source_basis"], "governed source/basis", MAX_SOURCE_LENGTH
    )
    clean_payload = sanitize_payload(event["payload"])
    payload_text = deterministic_json_text(clean_payload)
    if len(payload_text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise TimelineValidationError("timeline payload exceeds the byte bound")
    payload_hash = sha256_text(payload_text)
    if event["payload_sha256"] != payload_hash:
        raise TimelineValidationError("timeline payload hash mismatch")
    previous_hash = GENESIS_HASH if previous_event is None else previous_event["current_event_hash"]
    expected_sequence = 1 if previous_event is None else previous_event["append_sequence"] + 1
    if sequence != expected_sequence:
        raise TimelineValidationError("timeline append sequence is not contiguous")
    if event["previous_event_hash"] != previous_hash:
        raise TimelineValidationError("timeline previous-event hash mismatch")
    if previous_event is not None:
        prior_observed = validate_utc_timestamp(previous_event["first_observed_at_utc"])
        if observed < prior_observed:
            raise TimelineValidationError("timeline observation was backdated")
    stable_fields = {
        "schema_version": TIMELINE_EVENT_SCHEMA,
        "event_category": category,
        "instrument": instrument,
        "occurred_at_utc": event["occurred_at_utc"],
        "first_observed_at_utc": event["first_observed_at_utc"],
        "governed_source_basis": source,
        "payload_sha256": payload_hash,
    }
    expected_id = "tle_" + sha256_text(deterministic_json_text(stable_fields))[:32]
    if event_id != expected_id:
        raise TimelineValidationError("timeline event ID mismatch")
    expected_current = sha256_text(deterministic_json_text(_event_without_current_hash(event)))
    if event["current_event_hash"] != expected_current:
        raise TimelineValidationError("timeline current-event hash mismatch")
    if not _HASH_PATTERN.fullmatch(event["current_event_hash"]):
        raise TimelineValidationError("timeline current-event hash is invalid")
    return deepcopy(event)


class MarketTimeline:
    """An in-memory validated hash chain with deterministic documents."""

    def __init__(self, events=None):
        self._events = []
        if events:
            seen_ids = set()
            previous = None
            for candidate in events:
                clean = validate_timeline_event(candidate, previous, seen_ids)
                self._events.append(clean)
                seen_ids.add(clean["timeline_event_id"])
                previous = clean
        self._validate_bounds()

    @property
    def events(self):
        return deepcopy(self._events)

    @property
    def tail_hash(self):
        return self._events[-1]["current_event_hash"] if self._events else GENESIS_HASH

    def _validate_bounds(self):
        if len(self._events) > MAX_TIMELINE_EVENTS:
            raise TimelineValidationError("timeline event count exceeds the bound")
        encoded = deterministic_json_text(self.to_document()).encode("utf-8")
        if len(encoded) > MAX_TIMELINE_BYTES:
            raise TimelineValidationError("timeline document exceeds the byte bound")

    def append(
        self,
        category,
        instrument,
        occurred_at_utc,
        first_observed_at_utc,
        governed_source_basis,
        payload,
    ):
        if category not in EVENT_CATEGORIES:
            raise TimelineValidationError("timeline event category is not governed")
        instrument = validate_instrument(instrument, nullable=True)
        validate_utc_timestamp(occurred_at_utc, "occurred_at_utc")
        observed = validate_utc_timestamp(first_observed_at_utc, "first_observed_at_utc")
        if validate_utc_timestamp(occurred_at_utc) > observed:
            raise TimelineValidationError("event occurrence cannot follow first observation")
        if self._events:
            prior = validate_utc_timestamp(self._events[-1]["first_observed_at_utc"])
            if observed < prior:
                raise TimelineValidationError("timeline observation was backdated")
        source = _validate_string(
            governed_source_basis, "governed source/basis", MAX_SOURCE_LENGTH
        )
        clean_payload = sanitize_payload(payload)
        payload_text = deterministic_json_text(clean_payload)
        if len(payload_text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise TimelineValidationError("timeline payload exceeds the byte bound")
        payload_hash = sha256_text(payload_text)
        stable_fields = {
            "schema_version": TIMELINE_EVENT_SCHEMA,
            "event_category": category,
            "instrument": instrument,
            "occurred_at_utc": occurred_at_utc,
            "first_observed_at_utc": first_observed_at_utc,
            "governed_source_basis": source,
            "payload_sha256": payload_hash,
        }
        event_id = "tle_" + sha256_text(deterministic_json_text(stable_fields))[:32]
        if any(item["timeline_event_id"] == event_id for item in self._events):
            raise TimelineValidationError("duplicate timeline event ID")
        event = dict(stable_fields)
        event.update({
            "timeline_event_id": event_id,
            "append_sequence": len(self._events) + 1,
            "payload": clean_payload,
            "previous_event_hash": self.tail_hash,
        })
        event["current_event_hash"] = sha256_text(
            deterministic_json_text(_event_without_current_hash(event))
        )
        clean = validate_timeline_event(
            event,
            self._events[-1] if self._events else None,
            {item["timeline_event_id"] for item in self._events},
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
            "schema_version": TIMELINE_SCHEMA,
            "timeline_id": TIMELINE_ID,
            "event_count": len(self._events),
            "tail_event_hash": self.tail_hash,
            "events": deepcopy(self._events),
        }

    @classmethod
    def from_document(cls, document):
        expected = (
            "schema_version",
            "timeline_id",
            "event_count",
            "tail_event_hash",
            "events",
        )
        _require_exact_keys(document, expected, "timeline document")
        if document["schema_version"] != TIMELINE_SCHEMA:
            raise TimelineValidationError("timeline schema is unsupported")
        if document["timeline_id"] != TIMELINE_ID:
            raise TimelineValidationError("timeline identity is invalid")
        count = document["event_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise TimelineValidationError("timeline event count is invalid")
        if not isinstance(document["events"], list) or count != len(document["events"]):
            raise TimelineValidationError("timeline is truncated or count-mismatched")
        timeline = cls(document["events"])
        if document["tail_event_hash"] != timeline.tail_hash:
            raise TimelineValidationError("timeline tail hash mismatch")
        return timeline
