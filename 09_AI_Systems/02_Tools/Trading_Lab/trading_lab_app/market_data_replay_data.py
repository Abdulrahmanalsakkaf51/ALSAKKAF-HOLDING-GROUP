"""Governed data contracts for TRL-R2-011 Market Data Fabric and Replay V0
(TRL CORTEX DATA FABRIC V0).

Implements TRL_R2_011_MARKET_DATA_FABRIC_REPLAY_V0_CONTRACT.md Sections 6-16.
Pure data/validation/computation module: no filesystem I/O, no network, no
MetaTrader5 import, no journal, no ModeService call, no clock. CSV *bytes*
are handed in already read by the service layer (mirroring
``market_intelligence_service.load_analysis_input_bytes`` /
``market_intelligence_data.validate_snapshot_input`` splitting file-safety
I/O from pure structural validation). ``Decimal`` is authoritative for every
price/spread value; binary float is never used for validation, identity, or
comparison (Section 8).

Two V0 implementation decisions not spelled out verbatim by the contract's
closed reason-code table (Section 24.1), recorded here and in
``TRL_R2_011_MARKET_DATA_FABRIC_REPLAY_V0_EVIDENCE.md`` as explicit,
disclosed engineering judgment calls, exactly the way
``market_intelligence_data``'s own module docstring records its two V0
decisions:

1. The reason-code table has no dedicated code for an instrument/timeframe
   allowlist violation, a cross-row mixed-instrument/timeframe file, or a
   bar-invariant violation (``open<=0``, ``high<low``, etc. -- Section 9
   rules 1-2 and 5-15). Every one of these is a structural/domain violation
   of "this file does not describe one valid uniform bar series," so this
   module reuses ``MARKET_DATA_CSV_SHAPE_INVALID`` for allowlist/mixed-file
   violations and ``MARKET_DATA_DECIMAL_GRAMMAR_INVALID`` for OHLC/spread
   invariant violations (both already-governed codes whose fields are
   exactly the ones a rule 5-15 violation is judged against), rather than
   inventing an unlisted alias.
2. Canonical JSON/hashing reuses this repository's established Phase
   5/6/6A pattern (``timeline_data.deterministic_json_text`` +
   ``timeline_data.sha256_text``, the same functions
   ``market_intelligence_data.py`` and every journal module already use for
   every governed identity), not ``trading_lab_core.canonical.canonical_json``
   -- that heavier canonicalizer exists for the unrelated Release-1
   reproducibility engine and is never imported by any governed R2-0XX
   schema module. Both encoders are stable, sorted-key, allow_nan=False
   JSON text; this module follows the encoder the schema-identity precedent
   actually uses.
"""

from datetime import datetime, timezone
from decimal import Decimal
import re

from .timeline_data import (
    deterministic_json_text,
    sha256_text,
)


# ---------------------------------------------------------------------
# Schema versions and identity domains (Section 10, 11)
# ---------------------------------------------------------------------

BAR_SCHEMA = "TRL_MARKET_BAR.v1"
DATASET_MANIFEST_SCHEMA = "TRL_MARKET_DATASET_MANIFEST.v1"
REPLAY_SESSION_SCHEMA = "TRL_REPLAY_SESSION.v1"
REPLAY_STEP_SCHEMA = "TRL_REPLAY_STEP.v1"
REPLAY_SNAPSHOT_SCHEMA = "TRL_REPLAY_SNAPSHOT.v1"
STORAGE_ENVELOPE_SCHEMA = "TRL_MARKET_DATASET_STORAGE_ENVELOPE.v1"

BAR_ID_DOMAIN = "TRL-MARKET-BAR-ID.v1"
DATASET_ID_DOMAIN = "TRL-MARKET-DATASET-ID.v1"
REPLAY_SESSION_ID_DOMAIN = "TRL-REPLAY-SESSION-ID.v1"
REPLAY_STEP_ID_DOMAIN = "TRL-REPLAY-STEP-ID.v1"
REPLAY_SNAPSHOT_ID_DOMAIN = "TRL-REPLAY-SNAPSHOT-ID.v1"

# ---------------------------------------------------------------------
# Canonical allowlists (Section 6 -- reused verbatim from R2-010)
# ---------------------------------------------------------------------

INSTRUMENTS = ("XAUUSD", "NAS100", "EURUSD", "GBPUSD", "USDJPY")
TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1")
SOURCE_CLASSIFICATIONS = ("SYNTHETIC_FIXTURE", "LOCAL_HISTORICAL_FILE")
IMPORT_STATUSES = ("ACCEPTED",)
REPLAY_STEP_STATUSES = ("RUNNING", "COMPLETED")

TIMEFRAME_SECONDS = {
    "M5": 300,
    "M15": 900,
    "H1": 3600,
    "H4": 14400,
    "D1": 86400,
}

# ---------------------------------------------------------------------
# Exact V0 resource limits (Section 7.1, 18.1)
# ---------------------------------------------------------------------

MAX_CSV_BYTES = 33554432
MIN_DATA_ROWS = 2
MAX_DATA_ROWS = 250000
MAX_PHYSICAL_LINE_BYTES = 1024
MAX_FIELD_CODEPOINTS = 128
MAX_SOURCE_REFERENCE_CODEPOINTS = 256
MAX_STORAGE_ENVELOPE_BYTES = 268435456

STEP_SIZE_MIN = 1
STEP_SIZE_MAX = 1000
MAX_PROJECTED_REPLAY_STEPS = 10000
MAX_REPLAY_WINDOW_BARS = 100

CSV_HEADER = (
    "instrument,timeframe,observed_at_utc,open,high,low,close,spread,tick_volume"
)
CSV_FIELDS = (
    "instrument", "timeframe", "observed_at_utc", "open", "high", "low",
    "close", "spread", "tick_volume",
)

BAR_ID_PATTERN = re.compile(r"^bar_[0-9a-f]{32}$")
DATASET_ID_PATTERN = re.compile(r"^mds_[0-9a-f]{32}$")
REPLAY_SESSION_ID_PATTERN = re.compile(r"^rps_[0-9a-f]{32}$")
REPLAY_STEP_ID_PATTERN = re.compile(r"^rst_[0-9a-f]{32}$")
REPLAY_SNAPSHOT_ID_PATTERN = re.compile(r"^rsn_[0-9a-f]{32}$")

_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z$")
_DECIMAL_PATTERN = re.compile(r"^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$")
_TICK_VOLUME_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)$")
MAX_TICK_VOLUME = 9223372036854775807

REASON_CODES = (
    "MARKET_DATA_INPUT_FILE_TOO_LARGE",
    "MARKET_DATA_CSV_LINE_TOO_LONG",
    "MARKET_DATA_CSV_FIELD_TOO_LONG",
    "MARKET_DATA_CSV_SHAPE_INVALID",
    "MARKET_DATA_TIMESTAMP_INVALID",
    "MARKET_DATA_DECIMAL_GRAMMAR_INVALID",
    "MARKET_DATA_DECIMAL_DIGIT_LIMIT_EXCEEDED",
    "MARKET_DATA_DECIMAL_SCALE_EXCEEDED",
    "MARKET_DATA_TICK_VOLUME_OUT_OF_RANGE",
    "MARKET_DATA_DUPLICATE_TIMESTAMP",
    "MARKET_DATA_TIMESTAMP_OUT_OF_ORDER",
    "MARKET_DATA_IRREGULAR_INTERVAL",
    "MARKET_DATA_STORAGE_ENVELOPE_TOO_LARGE",
    "MARKET_DATA_STORAGE_INTEGRITY_FAILURE",
    "MARKET_DATA_JOURNAL_EVENT_TOO_LARGE",
    "MARKET_DATA_JOURNAL_FULL",
    "MARKET_DATA_JOURNAL_LOCK_TIMEOUT",
    "MARKET_DATA_JOURNAL_CORRUPTED",
    "MARKET_DATA_REPLAY_BOUNDS_INVALID",
    "MARKET_DATA_REPLAY_PROJECTED_STEP_LIMIT_EXCEEDED",
    "MARKET_DATA_REPLAY_ALREADY_COMPLETED",
    "MARKET_DATA_REPLAY_ALREADY_CANCELLED",
    "MARKET_DATA_REPLAY_SESSION_CORRUPTED",
    "MARKET_DATA_CAPABILITY_DENIED",
    "EXTERNAL_MARKET_DATA_FEED_NOT_APPROVED",
    "BROKER_HISTORY_IMPORT_NOT_APPROVED",
    "AUTOMATIC_EVIDENCE_GENERATION_NOT_APPROVED",
    "REPLAY_TO_INTELLIGENCE_HANDOFF_NOT_APPROVED",
    "REPLAY_TO_EXECUTION_HANDOFF_NOT_APPROVED",
)

SCHEMA_FAIL = "MARKET_DATA_CSV_SHAPE_INVALID"


class MarketDataValidationError(ValueError):
    """A stable, non-secret Market Data Fabric validation failure."""

    def __init__(self, reason_code, message=None):
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code {!r} is not governed".format(reason_code))
        self.reason_code = reason_code
        super().__init__(message or reason_code)


def _fail(reason_code, message=None):
    raise MarketDataValidationError(reason_code, message)


def _require_exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        _fail(SCHEMA_FAIL, "{} has an invalid field set".format(label))


def _identity_material(fields, expected_keys):
    if set(fields) != set(expected_keys):
        _fail(SCHEMA_FAIL, "identity input has an invalid field set")
    return deterministic_json_text(fields)


def _identity_for(prefix, domain, fields, expected_keys):
    material = _identity_material(fields, expected_keys)
    return prefix + sha256_text(domain + "\n" + material)[:32]


def _hash_for(fields_with_id, expected_keys):
    if set(fields_with_id) != set(expected_keys):
        _fail(SCHEMA_FAIL, "hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields_with_id))


# ---------------------------------------------------------------------
# Timestamp grammar (Section 7.2)
# ---------------------------------------------------------------------

def validate_market_timestamp(value, field="observed_at_utc"):
    if not isinstance(value, str) or not _UTC_PATTERN.fullmatch(value):
        _fail("MARKET_DATA_TIMESTAMP_INVALID", "{} must be strict RFC3339 UTC with six fractional digits".format(field))
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
    except ValueError:
        _fail("MARKET_DATA_TIMESTAMP_INVALID", "{} is not a real UTC timestamp".format(field))
        return None
    rendered = parsed.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    if rendered != value:
        _fail("MARKET_DATA_TIMESTAMP_INVALID", "{} does not round-trip canonically".format(field))
    return parsed.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------
# Exact Decimal grammar (Section 7.3) and tick_volume grammar (Section 7.4)
# ---------------------------------------------------------------------

def parse_market_decimal(text, field, positive, allow_zero=True):
    """Validate the exact CSV decimal grammar and return a canonical
    lossless decimal text (Section 7.3): no rounding, only canonical
    trailing-fractional-zero removal and negative-zero canonicalization."""
    if not isinstance(text, str):
        _fail("MARKET_DATA_DECIMAL_GRAMMAR_INVALID", "{} must be a string".format(field))
    if not _DECIMAL_PATTERN.fullmatch(text):
        _fail("MARKET_DATA_DECIMAL_GRAMMAR_INVALID", "{} does not match the exact decimal grammar".format(field))
    sign = "-" if text.startswith("-") else ""
    unsigned = text[1:] if sign else text
    if "." in unsigned:
        integer_part, fractional_part = unsigned.split(".", 1)
    else:
        integer_part, fractional_part = unsigned, ""
    total_digits = len(integer_part) + len(fractional_part)
    if total_digits > 24:
        _fail("MARKET_DATA_DECIMAL_DIGIT_LIMIT_EXCEEDED", "{} exceeds the 24 total-digit bound".format(field))
    if len(fractional_part) > 12:
        _fail("MARKET_DATA_DECIMAL_SCALE_EXCEEDED", "{} exceeds the 12 fractional-digit bound".format(field))
    value = Decimal(text)
    if value == 0:
        canonical = "0"
    else:
        canonical_fraction = fractional_part.rstrip("0")
        if canonical_fraction:
            canonical = "{}{}.{}".format(sign, integer_part, canonical_fraction)
        else:
            canonical = "{}{}".format(sign, integer_part)
    canonical_value = Decimal(canonical)
    if positive and (canonical_value < 0 or (canonical_value == 0 and not allow_zero)):
        qualifier = "positive" if not allow_zero else "non-negative"
        _fail("MARKET_DATA_DECIMAL_GRAMMAR_INVALID", "{} must be {}".format(field, qualifier))
    return canonical


def decimal_value(text):
    return Decimal(text)


def parse_tick_volume(text, field="tick_volume"):
    if not isinstance(text, str) or not _TICK_VOLUME_PATTERN.fullmatch(text):
        _fail("MARKET_DATA_TICK_VOLUME_OUT_OF_RANGE", "{} does not match the exact tick-volume grammar".format(field))
    value = int(text)
    if value > MAX_TICK_VOLUME:
        _fail("MARKET_DATA_TICK_VOLUME_OUT_OF_RANGE", "{} exceeds the maximum tick-volume range".format(field))
    return value


# ---------------------------------------------------------------------
# Strict CSV parsing (Section 7.1)
# ---------------------------------------------------------------------

def _split_physical_lines(raw_bytes):
    """Split into physical lines: LF or CRLF only; a bare CR not
    immediately followed by LF is an embedded/invalid line terminator."""
    search_from = 0
    while True:
        index = raw_bytes.find(b"\r", search_from)
        if index == -1:
            break
        if index + 1 >= len(raw_bytes) or raw_bytes[index + 1:index + 2] != b"\n":
            _fail("MARKET_DATA_CSV_SHAPE_INVALID", "an embedded or bare CR was found outside a CRLF line terminator")
        search_from = index + 2
    normalized = raw_bytes.replace(b"\r\n", b"\n")
    lines = normalized.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def _parse_csv_row(line_text, expected_field_count):
    """Manual, single-physical-line CSV field splitter with standard
    double-quote escaping. A physical line always maps to exactly one row
    because embedded CR/LF inside any field is already rejected at the
    byte level (``_split_physical_lines``), so a quoted field can never
    legitimately span more than one physical line."""
    fields = []
    index = 0
    length = len(line_text)
    while True:
        if index < length and line_text[index] == '"':
            index += 1
            characters = []
            closed = False
            while index < length:
                character = line_text[index]
                if character == '"':
                    if index + 1 < length and line_text[index + 1] == '"':
                        characters.append('"')
                        index += 2
                        continue
                    index += 1
                    closed = True
                    break
                characters.append(character)
                index += 1
            if not closed:
                _fail("MARKET_DATA_CSV_SHAPE_INVALID", "an unterminated quoted field was found")
            if index < length and line_text[index] not in (",",):
                _fail("MARKET_DATA_CSV_SHAPE_INVALID", "unexpected content after a closing quote")
            fields.append("".join(characters))
        else:
            start = index
            while index < length and line_text[index] != ",":
                index += 1
            fields.append(line_text[start:index])
        if index < length and line_text[index] == ",":
            index += 1
            continue
        break
    if len(fields) != expected_field_count:
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "row does not contain exactly {} fields".format(expected_field_count))
    return fields


def parse_csv_rows(raw_bytes):
    """Strictly parse and validate CSV bytes into an ordered list of
    canonical field dicts (Sections 7, 9, 13). Returns
    ``(rows, expected_interval_seconds, gap_count, largest_gap_intervals)``.
    Raises on the first invalid row -- no partial result is ever returned
    (Section 9's "a single invalid row fails the entire import")."""
    if not isinstance(raw_bytes, bytes):
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "CSV input must be raw bytes")
    if len(raw_bytes) > MAX_CSV_BYTES:
        _fail("MARKET_DATA_INPUT_FILE_TOO_LARGE", "CSV input exceeds the 33554432-byte bound")
    if raw_bytes.startswith(b"\xef\xbb\xbf"):
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "a byte-order mark is not accepted")
    if b"\x00" in raw_bytes:
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "a NUL byte is not accepted")
    lines = _split_physical_lines(raw_bytes)
    if not lines:
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "the CSV input is empty")
    for line in lines:
        if len(line) > MAX_PHYSICAL_LINE_BYTES:
            _fail("MARKET_DATA_CSV_LINE_TOO_LONG", "a physical CSV line exceeds the 1024-byte bound")
    try:
        text_lines = [line.decode("utf-8", errors="strict") for line in lines]
    except UnicodeDecodeError:
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "CSV input is not strict UTF-8")
        return None
    if text_lines[0] != CSV_HEADER:
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "the exact required CSV header was not found")
    data_lines = text_lines[1:]
    if len(data_lines) < MIN_DATA_ROWS:
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "the CSV input has fewer than the minimum required data rows")
    if len(data_lines) > MAX_DATA_ROWS:
        _fail("MARKET_DATA_CSV_SHAPE_INVALID", "the CSV input exceeds the maximum permitted data rows")

    rows = []
    instrument = None
    timeframe = None
    expected_interval_seconds = None
    previous_dt = None
    gap_count = 0
    largest_gap_intervals = 0

    for line_number, line_text in enumerate(data_lines, start=2):
        if line_text == "":
            _fail("MARKET_DATA_CSV_SHAPE_INVALID", "line {}: a blank data row is not accepted".format(line_number))
        raw_fields = _parse_csv_row(line_text, len(CSV_FIELDS))
        for value in raw_fields:
            if len(value) > MAX_FIELD_CODEPOINTS:
                _fail("MARKET_DATA_CSV_FIELD_TOO_LONG", "line {}: a parsed field exceeds the 128-code-point bound".format(line_number))
            if value != value.strip():
                _fail("MARKET_DATA_CSV_SHAPE_INVALID", "line {}: a field contains untrimmed leading or trailing whitespace".format(line_number))
        row = dict(zip(CSV_FIELDS, raw_fields))

        row_instrument = row["instrument"]
        row_timeframe = row["timeframe"]
        if row_instrument not in INSTRUMENTS:
            _fail("MARKET_DATA_CSV_SHAPE_INVALID", "line {}: instrument is not allowlisted".format(line_number))
        if row_timeframe not in TIMEFRAMES:
            _fail("MARKET_DATA_CSV_SHAPE_INVALID", "line {}: timeframe is not allowlisted".format(line_number))
        if instrument is None:
            instrument = row_instrument
            timeframe = row_timeframe
            expected_interval_seconds = TIMEFRAME_SECONDS[timeframe]
        elif row_instrument != instrument or row_timeframe != timeframe:
            _fail("MARKET_DATA_CSV_SHAPE_INVALID", "line {}: a single dataset must use one instrument and one timeframe".format(line_number))

        observed_dt = validate_market_timestamp(row["observed_at_utc"], "observed_at_utc")

        open_text = parse_market_decimal(row["open"], "open", positive=True, allow_zero=False)
        high_text = parse_market_decimal(row["high"], "high", positive=True, allow_zero=False)
        low_text = parse_market_decimal(row["low"], "low", positive=True, allow_zero=False)
        close_text = parse_market_decimal(row["close"], "close", positive=True, allow_zero=False)
        spread_text = parse_market_decimal(row["spread"], "spread", positive=True, allow_zero=True)
        tick_volume = parse_tick_volume(row["tick_volume"])

        open_v, high_v, low_v, close_v = (
            decimal_value(open_text), decimal_value(high_text),
            decimal_value(low_text), decimal_value(close_text),
        )
        if not (high_v >= open_v and high_v >= close_v and high_v >= low_v
                and low_v <= open_v and low_v <= close_v):
            _fail("MARKET_DATA_DECIMAL_GRAMMAR_INVALID", "line {}: high/low/open/close invariants are violated".format(line_number))

        if previous_dt is not None:
            if observed_dt == previous_dt:
                _fail("MARKET_DATA_DUPLICATE_TIMESTAMP", "line {}: duplicate observed_at_utc".format(line_number))
            if observed_dt < previous_dt:
                _fail("MARKET_DATA_TIMESTAMP_OUT_OF_ORDER", "line {}: observed_at_utc is out of order".format(line_number))
            delta = observed_dt - previous_dt
            delta_seconds = delta.days * 86400 + delta.seconds
            if delta.microseconds != 0 or delta_seconds % expected_interval_seconds != 0:
                _fail("MARKET_DATA_IRREGULAR_INTERVAL", "line {}: interval is not an exact multiple of the timeframe interval".format(line_number))
            multiple = delta_seconds // expected_interval_seconds
            if multiple > 1:
                missing_intervals = multiple - 1
                gap_count += 1
                largest_gap_intervals = max(largest_gap_intervals, missing_intervals)

        rows.append({
            "instrument": row_instrument,
            "timeframe": row_timeframe,
            "observed_at_utc": row["observed_at_utc"],
            "open": open_text, "high": high_text, "low": low_text, "close": close_text,
            "spread": spread_text, "tick_volume": tick_volume,
        })
        previous_dt = observed_dt

    return rows, expected_interval_seconds, gap_count, largest_gap_intervals


# ---------------------------------------------------------------------
# TRL_MARKET_BAR.v1 (Section 10.1, 11.1)
# ---------------------------------------------------------------------

BAR_ID_FIELDS = (
    "instrument", "timeframe", "observed_at_utc", "open", "high", "low",
    "close", "spread", "tick_volume", "source_classification",
)
BAR_HASH_FIELDS = ("schema_version", "bar_id") + BAR_ID_FIELDS
BAR_FIELDS = BAR_HASH_FIELDS + ("canonical_bar_hash",)


def build_bar_record(row, source_classification):
    if source_classification not in SOURCE_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "source_classification is not governed")
    identity_fields = dict(row)
    identity_fields["source_classification"] = source_classification
    bar_id = _identity_for("bar_", BAR_ID_DOMAIN, identity_fields, BAR_ID_FIELDS)
    hash_fields = dict(identity_fields)
    hash_fields["schema_version"] = BAR_SCHEMA
    hash_fields["bar_id"] = bar_id
    canonical_hash = _hash_for(hash_fields, BAR_HASH_FIELDS)
    record = {"schema_version": BAR_SCHEMA, "bar_id": bar_id}
    record.update(identity_fields)
    record["canonical_bar_hash"] = canonical_hash
    return validate_bar_record(record)


def validate_bar_record(record):
    _require_exact_keys(record, BAR_FIELDS, "market bar")
    if record["schema_version"] != BAR_SCHEMA:
        _fail(SCHEMA_FAIL, "bar schema is unsupported")
    if not BAR_ID_PATTERN.fullmatch(record["bar_id"] or ""):
        _fail(SCHEMA_FAIL, "bar_id is invalid")
    if record["instrument"] not in INSTRUMENTS:
        _fail(SCHEMA_FAIL, "instrument is not allowlisted")
    if record["timeframe"] not in TIMEFRAMES:
        _fail(SCHEMA_FAIL, "timeframe is not allowlisted")
    validate_market_timestamp(record["observed_at_utc"], "observed_at_utc")
    open_text = parse_market_decimal(record["open"], "open", positive=True, allow_zero=False)
    high_text = parse_market_decimal(record["high"], "high", positive=True, allow_zero=False)
    low_text = parse_market_decimal(record["low"], "low", positive=True, allow_zero=False)
    close_text = parse_market_decimal(record["close"], "close", positive=True, allow_zero=False)
    spread_text = parse_market_decimal(record["spread"], "spread", positive=True, allow_zero=True)
    if (open_text, high_text, low_text, close_text, spread_text) != (
        record["open"], record["high"], record["low"], record["close"], record["spread"],
    ):
        _fail(SCHEMA_FAIL, "a price/spread field is not in canonical decimal form")
    if not isinstance(record["tick_volume"], int) or isinstance(record["tick_volume"], bool):
        _fail(SCHEMA_FAIL, "tick_volume must be a strict integer")
    if not (0 <= record["tick_volume"] <= MAX_TICK_VOLUME):
        _fail("MARKET_DATA_TICK_VOLUME_OUT_OF_RANGE", "tick_volume is out of range")
    if record["source_classification"] not in SOURCE_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "source_classification is not governed")
    identity_fields = {key: record[key] for key in BAR_ID_FIELDS}
    expected_id = _identity_for("bar_", BAR_ID_DOMAIN, identity_fields, BAR_ID_FIELDS)
    if record["bar_id"] != expected_id:
        _fail(SCHEMA_FAIL, "bar_id does not match canonical identity content")
    hash_fields = dict(identity_fields)
    hash_fields["schema_version"] = BAR_SCHEMA
    hash_fields["bar_id"] = record["bar_id"]
    expected_hash = _hash_for(hash_fields, BAR_HASH_FIELDS)
    if record["canonical_bar_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_bar_hash does not match canonical content")
    return dict(record)


def bar_ref(bar_record):
    return [bar_record["bar_id"], bar_record["canonical_bar_hash"]]


# ---------------------------------------------------------------------
# TRL_MARKET_DATASET_MANIFEST.v1 (Section 10.2, 11.2)
# ---------------------------------------------------------------------

DATASET_ID_FIELDS = (
    "instrument", "timeframe", "source_classification", "source_reference",
    "ordered_bar_refs", "expected_interval_seconds", "gap_count", "largest_gap_intervals",
)
DATASET_HASH_FIELDS = (
    "schema_version", "dataset_id", "instrument", "timeframe", "source_classification",
    "source_reference", "bar_count", "first_observed_at_utc", "last_observed_at_utc",
    "ordered_bar_refs", "expected_interval_seconds", "gap_count", "largest_gap_intervals",
    "duplicate_timestamp_count", "out_of_order_count", "import_status",
)
DATASET_FIELDS = DATASET_HASH_FIELDS + ("imported_at_utc",)


def validate_source_reference(value):
    if not isinstance(value, str) or not value:
        _fail(SCHEMA_FAIL, "source_reference must be a non-empty string")
    if len(value) > MAX_SOURCE_REFERENCE_CODEPOINTS:
        _fail(SCHEMA_FAIL, "source_reference exceeds the 256-code-point bound")
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail(SCHEMA_FAIL, "source_reference contains a control character")
    if "://" in value or value.startswith("\\\\") or value.startswith("//"):
        _fail(SCHEMA_FAIL, "source_reference must not contain a URL or network path")
    return value


def build_dataset_manifest_record(
    bars, source_classification, source_reference, expected_interval_seconds,
    gap_count, largest_gap_intervals, imported_at_utc,
):
    if not bars:
        _fail(SCHEMA_FAIL, "a dataset manifest requires at least one bar")
    if not (MIN_DATA_ROWS <= len(bars) <= MAX_DATA_ROWS):
        _fail(SCHEMA_FAIL, "bar_count is out of the governed range")
    validate_source_reference(source_reference)
    if source_classification not in SOURCE_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "source_classification is not governed")
    instrument = bars[0]["instrument"]
    timeframe = bars[0]["timeframe"]
    ordered_bar_refs = [bar_ref(bar) for bar in bars]
    identity_fields = {
        "instrument": instrument, "timeframe": timeframe,
        "source_classification": source_classification, "source_reference": source_reference,
        "ordered_bar_refs": ordered_bar_refs,
        "expected_interval_seconds": expected_interval_seconds,
        "gap_count": gap_count, "largest_gap_intervals": largest_gap_intervals,
    }
    dataset_id = _identity_for("mds_", DATASET_ID_DOMAIN, identity_fields, DATASET_ID_FIELDS)
    hash_fields = {
        "schema_version": DATASET_MANIFEST_SCHEMA, "dataset_id": dataset_id,
        "instrument": instrument, "timeframe": timeframe,
        "source_classification": source_classification, "source_reference": source_reference,
        "bar_count": len(bars),
        "first_observed_at_utc": bars[0]["observed_at_utc"],
        "last_observed_at_utc": bars[-1]["observed_at_utc"],
        "ordered_bar_refs": ordered_bar_refs,
        "expected_interval_seconds": expected_interval_seconds,
        "gap_count": gap_count, "largest_gap_intervals": largest_gap_intervals,
        "duplicate_timestamp_count": 0, "out_of_order_count": 0,
        "import_status": "ACCEPTED",
    }
    canonical_dataset_hash = _hash_for(hash_fields, DATASET_HASH_FIELDS)
    record = dict(hash_fields)
    record["canonical_dataset_hash"] = canonical_dataset_hash
    record["imported_at_utc"] = imported_at_utc
    return validate_dataset_manifest_record(record)


def validate_dataset_manifest_record(record):
    expected = DATASET_FIELDS + ("canonical_dataset_hash",)
    _require_exact_keys(record, expected, "dataset manifest")
    if record["schema_version"] != DATASET_MANIFEST_SCHEMA:
        _fail(SCHEMA_FAIL, "dataset manifest schema is unsupported")
    if not DATASET_ID_PATTERN.fullmatch(record["dataset_id"] or ""):
        _fail(SCHEMA_FAIL, "dataset_id is invalid")
    if record["instrument"] not in INSTRUMENTS:
        _fail(SCHEMA_FAIL, "instrument is not allowlisted")
    if record["timeframe"] not in TIMEFRAMES:
        _fail(SCHEMA_FAIL, "timeframe is not allowlisted")
    if record["source_classification"] not in SOURCE_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "source_classification is not governed")
    validate_source_reference(record["source_reference"])
    if (not isinstance(record["bar_count"], int) or isinstance(record["bar_count"], bool)
            or not (MIN_DATA_ROWS <= record["bar_count"] <= MAX_DATA_ROWS)):
        _fail(SCHEMA_FAIL, "bar_count is out of the governed range")
    validate_market_timestamp(record["first_observed_at_utc"], "first_observed_at_utc")
    validate_market_timestamp(record["last_observed_at_utc"], "last_observed_at_utc")
    if not isinstance(record["ordered_bar_refs"], list) or len(record["ordered_bar_refs"]) != record["bar_count"]:
        _fail(SCHEMA_FAIL, "ordered_bar_refs does not match bar_count")
    for entry in record["ordered_bar_refs"]:
        if (not isinstance(entry, list) or len(entry) != 2
                or not BAR_ID_PATTERN.fullmatch(entry[0] or "")
                or not isinstance(entry[1], str) or not re.fullmatch(r"[0-9a-f]{64}", entry[1] or "")):
            _fail(SCHEMA_FAIL, "ordered_bar_refs contains an invalid entry")
    if record["expected_interval_seconds"] != TIMEFRAME_SECONDS[record["timeframe"]]:
        _fail(SCHEMA_FAIL, "expected_interval_seconds does not match the timeframe")
    if (not isinstance(record["gap_count"], int) or isinstance(record["gap_count"], bool)
            or record["gap_count"] < 0):
        _fail(SCHEMA_FAIL, "gap_count must be a non-negative integer")
    if (not isinstance(record["largest_gap_intervals"], int) or isinstance(record["largest_gap_intervals"], bool)
            or record["largest_gap_intervals"] < 0):
        _fail(SCHEMA_FAIL, "largest_gap_intervals must be a non-negative integer")
    if (record["gap_count"] == 0) != (record["largest_gap_intervals"] == 0):
        _fail(SCHEMA_FAIL, "gap_count and largest_gap_intervals are inconsistent")
    if record["duplicate_timestamp_count"] != 0 or record["out_of_order_count"] != 0:
        _fail(SCHEMA_FAIL, "an accepted manifest must have zero duplicate/out-of-order counts")
    if record["import_status"] != "ACCEPTED":
        _fail(SCHEMA_FAIL, "import_status must be ACCEPTED")
    validate_market_timestamp(record["imported_at_utc"], "imported_at_utc")
    identity_fields = {key: record[key] for key in DATASET_ID_FIELDS}
    expected_id = _identity_for("mds_", DATASET_ID_DOMAIN, identity_fields, DATASET_ID_FIELDS)
    if record["dataset_id"] != expected_id:
        _fail(SCHEMA_FAIL, "dataset_id does not match canonical identity content")
    hash_fields = {key: record[key] for key in DATASET_HASH_FIELDS}
    expected_hash = _hash_for(hash_fields, DATASET_HASH_FIELDS)
    if record["canonical_dataset_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_dataset_hash does not match canonical content")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_REPLAY_SESSION.v1 (Section 10.3, 11.3, 14.1)
# ---------------------------------------------------------------------

REPLAY_SESSION_ID_FIELDS = ("dataset_id", "canonical_dataset_hash", "start_index", "end_index", "step_size")
REPLAY_SESSION_HASH_FIELDS = ("schema_version", "replay_session_id") + REPLAY_SESSION_ID_FIELDS
REPLAY_SESSION_FIELDS = REPLAY_SESSION_HASH_FIELDS + ("created_at_utc", "canonical_replay_session_hash")


def _strict_nonneg_int(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def validate_replay_bounds(bar_count, start_index, end_index, step_size):
    if not _strict_nonneg_int(start_index) or start_index < 0:
        _fail("MARKET_DATA_REPLAY_BOUNDS_INVALID", "start_index must be a non-negative integer")
    if not _strict_nonneg_int(end_index) or end_index > bar_count - 1:
        _fail("MARKET_DATA_REPLAY_BOUNDS_INVALID", "end_index must not exceed dataset.bar_count - 1")
    if start_index > end_index:
        _fail("MARKET_DATA_REPLAY_BOUNDS_INVALID", "start_index must not exceed end_index")
    if not isinstance(step_size, int) or isinstance(step_size, bool) or not (STEP_SIZE_MIN <= step_size <= STEP_SIZE_MAX):
        _fail("MARKET_DATA_REPLAY_BOUNDS_INVALID", "step_size must be an integer from 1 through 1000")


def projected_step_count(start_index, end_index, step_size):
    return -(-(end_index - start_index + 1) // step_size)


def build_replay_session_record(dataset_id, canonical_dataset_hash, start_index, end_index, step_size, created_at_utc):
    identity_fields = {
        "dataset_id": dataset_id, "canonical_dataset_hash": canonical_dataset_hash,
        "start_index": start_index, "end_index": end_index, "step_size": step_size,
    }
    replay_session_id = _identity_for("rps_", REPLAY_SESSION_ID_DOMAIN, identity_fields, REPLAY_SESSION_ID_FIELDS)
    hash_fields = dict(identity_fields)
    hash_fields["schema_version"] = REPLAY_SESSION_SCHEMA
    hash_fields["replay_session_id"] = replay_session_id
    canonical_hash = _hash_for(hash_fields, REPLAY_SESSION_HASH_FIELDS)
    record = dict(hash_fields)
    record["created_at_utc"] = created_at_utc
    record["canonical_replay_session_hash"] = canonical_hash
    return validate_replay_session_record(record)


def validate_replay_session_record(record):
    _require_exact_keys(record, REPLAY_SESSION_FIELDS, "replay session")
    if record["schema_version"] != REPLAY_SESSION_SCHEMA:
        _fail(SCHEMA_FAIL, "replay session schema is unsupported")
    if not REPLAY_SESSION_ID_PATTERN.fullmatch(record["replay_session_id"] or ""):
        _fail(SCHEMA_FAIL, "replay_session_id is invalid")
    if not DATASET_ID_PATTERN.fullmatch(record["dataset_id"] or ""):
        _fail(SCHEMA_FAIL, "dataset_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_dataset_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_dataset_hash is invalid")
    if not _strict_nonneg_int(record["start_index"]) or not _strict_nonneg_int(record["end_index"]):
        _fail(SCHEMA_FAIL, "start_index/end_index must be non-negative integers")
    if record["start_index"] > record["end_index"]:
        _fail(SCHEMA_FAIL, "start_index must not exceed end_index")
    if (not isinstance(record["step_size"], int) or isinstance(record["step_size"], bool)
            or not (STEP_SIZE_MIN <= record["step_size"] <= STEP_SIZE_MAX)):
        _fail(SCHEMA_FAIL, "step_size must be an integer from 1 through 1000")
    validate_market_timestamp(record["created_at_utc"], "created_at_utc")
    identity_fields = {key: record[key] for key in REPLAY_SESSION_ID_FIELDS}
    expected_id = _identity_for("rps_", REPLAY_SESSION_ID_DOMAIN, identity_fields, REPLAY_SESSION_ID_FIELDS)
    if record["replay_session_id"] != expected_id:
        _fail(SCHEMA_FAIL, "replay_session_id does not match canonical identity content")
    hash_fields = {key: record[key] for key in REPLAY_SESSION_HASH_FIELDS}
    expected_hash = _hash_for(hash_fields, REPLAY_SESSION_HASH_FIELDS)
    if record["canonical_replay_session_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_replay_session_hash does not match canonical content")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_REPLAY_STEP.v1 (Section 10.4, 11.4, 15)
# ---------------------------------------------------------------------

REPLAY_STEP_ID_FIELDS = (
    "replay_session_id", "canonical_replay_session_hash", "sequence_number",
    "from_index", "to_index", "ordered_bar_refs", "status_after",
)
REPLAY_STEP_HASH_FIELDS = ("schema_version", "replay_step_id") + REPLAY_STEP_ID_FIELDS
REPLAY_STEP_FIELDS = REPLAY_STEP_HASH_FIELDS + ("occurred_at_utc", "canonical_replay_step_hash")


def build_replay_step_record(
    replay_session_id, canonical_replay_session_hash, sequence_number,
    from_index, to_index, ordered_bar_refs, status_after, occurred_at_utc,
):
    identity_fields = {
        "replay_session_id": replay_session_id,
        "canonical_replay_session_hash": canonical_replay_session_hash,
        "sequence_number": sequence_number, "from_index": from_index, "to_index": to_index,
        "ordered_bar_refs": ordered_bar_refs, "status_after": status_after,
    }
    replay_step_id = _identity_for("rst_", REPLAY_STEP_ID_DOMAIN, identity_fields, REPLAY_STEP_ID_FIELDS)
    hash_fields = dict(identity_fields)
    hash_fields["schema_version"] = REPLAY_STEP_SCHEMA
    hash_fields["replay_step_id"] = replay_step_id
    canonical_hash = _hash_for(hash_fields, REPLAY_STEP_HASH_FIELDS)
    record = dict(hash_fields)
    record["occurred_at_utc"] = occurred_at_utc
    record["canonical_replay_step_hash"] = canonical_hash
    return validate_replay_step_record(record)


def validate_replay_step_record(record):
    _require_exact_keys(record, REPLAY_STEP_FIELDS, "replay step")
    if record["schema_version"] != REPLAY_STEP_SCHEMA:
        _fail(SCHEMA_FAIL, "replay step schema is unsupported")
    if not REPLAY_STEP_ID_PATTERN.fullmatch(record["replay_step_id"] or ""):
        _fail(SCHEMA_FAIL, "replay_step_id is invalid")
    if not REPLAY_SESSION_ID_PATTERN.fullmatch(record["replay_session_id"] or ""):
        _fail(SCHEMA_FAIL, "replay_session_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_replay_session_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_replay_session_hash is invalid")
    if not isinstance(record["sequence_number"], int) or isinstance(record["sequence_number"], bool) or record["sequence_number"] < 1:
        _fail(SCHEMA_FAIL, "sequence_number must be a positive integer")
    if not _strict_nonneg_int(record["from_index"]) or not _strict_nonneg_int(record["to_index"]):
        _fail(SCHEMA_FAIL, "from_index/to_index must be non-negative integers")
    if record["from_index"] > record["to_index"]:
        _fail(SCHEMA_FAIL, "from_index must not exceed to_index")
    if not isinstance(record["ordered_bar_refs"], list) or not record["ordered_bar_refs"]:
        _fail(SCHEMA_FAIL, "ordered_bar_refs must be a non-empty list")
    if len(record["ordered_bar_refs"]) != (record["to_index"] - record["from_index"] + 1):
        _fail(SCHEMA_FAIL, "ordered_bar_refs length does not match from_index/to_index")
    if record["status_after"] not in REPLAY_STEP_STATUSES:
        _fail(SCHEMA_FAIL, "status_after is not governed")
    validate_market_timestamp(record["occurred_at_utc"], "occurred_at_utc")
    identity_fields = {key: record[key] for key in REPLAY_STEP_ID_FIELDS}
    expected_id = _identity_for("rst_", REPLAY_STEP_ID_DOMAIN, identity_fields, REPLAY_STEP_ID_FIELDS)
    if record["replay_step_id"] != expected_id:
        _fail(SCHEMA_FAIL, "replay_step_id does not match canonical identity content")
    hash_fields = {key: record[key] for key in REPLAY_STEP_HASH_FIELDS}
    expected_hash = _hash_for(hash_fields, REPLAY_STEP_HASH_FIELDS)
    if record["canonical_replay_step_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_replay_step_hash does not match canonical content")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_REPLAY_SNAPSHOT.v1 (Section 10.5, 11.5, 16)
# ---------------------------------------------------------------------

REPLAY_SNAPSHOT_ID_FIELDS = (
    "replay_session_id", "canonical_replay_session_hash", "replay_step_id",
    "canonical_replay_step_hash", "dataset_id", "canonical_dataset_hash",
    "current_index", "current_bar_id", "canonical_current_bar_hash",
    "window_start_index", "window_end_index", "ordered_window_bar_refs",
    "non_live", "non_executable",
)
REPLAY_SNAPSHOT_HASH_FIELDS = ("schema_version", "replay_snapshot_id") + REPLAY_SNAPSHOT_ID_FIELDS
REPLAY_SNAPSHOT_FIELDS = REPLAY_SNAPSHOT_HASH_FIELDS + ("created_at_utc", "canonical_replay_snapshot_hash")


def build_replay_snapshot_record(
    replay_session_id, canonical_replay_session_hash, replay_step_id, canonical_replay_step_hash,
    dataset_id, canonical_dataset_hash, current_index, current_bar_id, canonical_current_bar_hash,
    window_start_index, window_end_index, ordered_window_bar_refs, created_at_utc,
):
    identity_fields = {
        "replay_session_id": replay_session_id,
        "canonical_replay_session_hash": canonical_replay_session_hash,
        "replay_step_id": replay_step_id, "canonical_replay_step_hash": canonical_replay_step_hash,
        "dataset_id": dataset_id, "canonical_dataset_hash": canonical_dataset_hash,
        "current_index": current_index, "current_bar_id": current_bar_id,
        "canonical_current_bar_hash": canonical_current_bar_hash,
        "window_start_index": window_start_index, "window_end_index": window_end_index,
        "ordered_window_bar_refs": ordered_window_bar_refs,
        "non_live": True, "non_executable": True,
    }
    replay_snapshot_id = _identity_for("rsn_", REPLAY_SNAPSHOT_ID_DOMAIN, identity_fields, REPLAY_SNAPSHOT_ID_FIELDS)
    hash_fields = dict(identity_fields)
    hash_fields["schema_version"] = REPLAY_SNAPSHOT_SCHEMA
    hash_fields["replay_snapshot_id"] = replay_snapshot_id
    canonical_hash = _hash_for(hash_fields, REPLAY_SNAPSHOT_HASH_FIELDS)
    record = dict(hash_fields)
    record["created_at_utc"] = created_at_utc
    record["canonical_replay_snapshot_hash"] = canonical_hash
    return validate_replay_snapshot_record(record)


def validate_replay_snapshot_record(record):
    _require_exact_keys(record, REPLAY_SNAPSHOT_FIELDS, "replay snapshot")
    if record["schema_version"] != REPLAY_SNAPSHOT_SCHEMA:
        _fail(SCHEMA_FAIL, "replay snapshot schema is unsupported")
    if not REPLAY_SNAPSHOT_ID_PATTERN.fullmatch(record["replay_snapshot_id"] or ""):
        _fail(SCHEMA_FAIL, "replay_snapshot_id is invalid")
    if not REPLAY_SESSION_ID_PATTERN.fullmatch(record["replay_session_id"] or ""):
        _fail(SCHEMA_FAIL, "replay_session_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_replay_session_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_replay_session_hash is invalid")
    if not REPLAY_STEP_ID_PATTERN.fullmatch(record["replay_step_id"] or ""):
        _fail(SCHEMA_FAIL, "replay_step_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_replay_step_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_replay_step_hash is invalid")
    if not DATASET_ID_PATTERN.fullmatch(record["dataset_id"] or ""):
        _fail(SCHEMA_FAIL, "dataset_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_dataset_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_dataset_hash is invalid")
    if not _strict_nonneg_int(record["current_index"]):
        _fail(SCHEMA_FAIL, "current_index must be a non-negative integer")
    if not BAR_ID_PATTERN.fullmatch(record["current_bar_id"] or ""):
        _fail(SCHEMA_FAIL, "current_bar_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_current_bar_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_current_bar_hash is invalid")
    if not _strict_nonneg_int(record["window_start_index"]) or not _strict_nonneg_int(record["window_end_index"]):
        _fail(SCHEMA_FAIL, "window_start_index/window_end_index must be non-negative integers")
    if record["window_end_index"] != record["current_index"]:
        _fail(SCHEMA_FAIL, "window_end_index must equal current_index")
    if record["window_start_index"] > record["window_end_index"]:
        _fail(SCHEMA_FAIL, "window_start_index must not exceed window_end_index")
    window_size = record["window_end_index"] - record["window_start_index"] + 1
    if window_size > MAX_REPLAY_WINDOW_BARS:
        _fail(SCHEMA_FAIL, "replay window exceeds the 100-bar maximum")
    if not isinstance(record["ordered_window_bar_refs"], list) or len(record["ordered_window_bar_refs"]) != window_size:
        _fail(SCHEMA_FAIL, "ordered_window_bar_refs does not match the window size")
    for entry in record["ordered_window_bar_refs"]:
        if (not isinstance(entry, list) or len(entry) != 2
                or not BAR_ID_PATTERN.fullmatch(entry[0] or "")
                or not re.fullmatch(r"[0-9a-f]{64}", entry[1] or "")):
            _fail(SCHEMA_FAIL, "ordered_window_bar_refs contains an invalid entry")
    if record["non_live"] is not True or record["non_executable"] is not True:
        _fail(SCHEMA_FAIL, "non_live and non_executable must always be true")
    validate_market_timestamp(record["created_at_utc"], "created_at_utc")
    identity_fields = {key: record[key] for key in REPLAY_SNAPSHOT_ID_FIELDS}
    expected_id = _identity_for("rsn_", REPLAY_SNAPSHOT_ID_DOMAIN, identity_fields, REPLAY_SNAPSHOT_ID_FIELDS)
    if record["replay_snapshot_id"] != expected_id:
        _fail(SCHEMA_FAIL, "replay_snapshot_id does not match canonical identity content")
    hash_fields = {key: record[key] for key in REPLAY_SNAPSHOT_HASH_FIELDS}
    expected_hash = _hash_for(hash_fields, REPLAY_SNAPSHOT_HASH_FIELDS)
    if record["canonical_replay_snapshot_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_replay_snapshot_hash does not match canonical content")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_MARKET_DATASET_STORAGE_ENVELOPE.v1 (Section 10.6) -- non-governed
# storage-only container; schema validated here, persisted by
# market_data_replay_storage.py.
# ---------------------------------------------------------------------

STORAGE_ENVELOPE_FIELDS = ("schema_version", "dataset_id", "canonical_dataset_hash", "manifest", "ordered_bars")


def build_storage_envelope(manifest, bars):
    if manifest["bar_count"] != len(bars):
        _fail(SCHEMA_FAIL, "manifest.bar_count does not match the supplied bar set")
    for entry, bar in zip(manifest["ordered_bar_refs"], bars):
        if entry != bar_ref(bar):
            _fail(SCHEMA_FAIL, "ordered_bar_refs does not match the supplied bar order")
    envelope = {
        "schema_version": STORAGE_ENVELOPE_SCHEMA,
        "dataset_id": manifest["dataset_id"],
        "canonical_dataset_hash": manifest["canonical_dataset_hash"],
        "manifest": manifest,
        "ordered_bars": bars,
    }
    return validate_storage_envelope(envelope)


def validate_storage_envelope(envelope):
    _require_exact_keys(envelope, STORAGE_ENVELOPE_FIELDS, "dataset storage envelope")
    if envelope["schema_version"] != STORAGE_ENVELOPE_SCHEMA:
        _fail("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "storage envelope schema is unsupported")
    manifest = validate_dataset_manifest_record(envelope["manifest"])
    if envelope["dataset_id"] != manifest["dataset_id"]:
        _fail("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "envelope dataset_id does not match manifest.dataset_id")
    if envelope["canonical_dataset_hash"] != manifest["canonical_dataset_hash"]:
        _fail("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "envelope canonical_dataset_hash does not match manifest.canonical_dataset_hash")
    if not isinstance(envelope["ordered_bars"], list) or len(envelope["ordered_bars"]) != manifest["bar_count"]:
        _fail("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "ordered_bars length does not match manifest.bar_count")
    ordered_bars = []
    for bar_record, ref in zip(envelope["ordered_bars"], manifest["ordered_bar_refs"]):
        clean_bar = validate_bar_record(bar_record)
        if bar_ref(clean_bar) != ref:
            _fail("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "ordered_bars does not match manifest.ordered_bar_refs")
        if (clean_bar["instrument"] != manifest["instrument"]
                or clean_bar["timeframe"] != manifest["timeframe"]
                or clean_bar["source_classification"] != manifest["source_classification"]):
            _fail("MARKET_DATA_STORAGE_INTEGRITY_FAILURE", "a bar is inconsistent with the manifest instrument/timeframe/source")
        ordered_bars.append(clean_bar)
    return {
        "schema_version": STORAGE_ENVELOPE_SCHEMA,
        "dataset_id": envelope["dataset_id"],
        "canonical_dataset_hash": envelope["canonical_dataset_hash"],
        "manifest": manifest,
        "ordered_bars": ordered_bars,
    }


__all__ = (
    "BAR_SCHEMA", "DATASET_MANIFEST_SCHEMA", "REPLAY_SESSION_SCHEMA", "REPLAY_STEP_SCHEMA",
    "REPLAY_SNAPSHOT_SCHEMA", "STORAGE_ENVELOPE_SCHEMA",
    "INSTRUMENTS", "TIMEFRAMES", "SOURCE_CLASSIFICATIONS", "TIMEFRAME_SECONDS",
    "MAX_CSV_BYTES", "MIN_DATA_ROWS", "MAX_DATA_ROWS", "MAX_PHYSICAL_LINE_BYTES",
    "MAX_FIELD_CODEPOINTS", "MAX_SOURCE_REFERENCE_CODEPOINTS", "MAX_STORAGE_ENVELOPE_BYTES",
    "STEP_SIZE_MIN", "STEP_SIZE_MAX", "MAX_PROJECTED_REPLAY_STEPS", "MAX_REPLAY_WINDOW_BARS",
    "CSV_HEADER", "CSV_FIELDS",
    "BAR_ID_PATTERN", "DATASET_ID_PATTERN", "REPLAY_SESSION_ID_PATTERN",
    "REPLAY_STEP_ID_PATTERN", "REPLAY_SNAPSHOT_ID_PATTERN",
    "REASON_CODES", "SCHEMA_FAIL", "MarketDataValidationError",
    "validate_market_timestamp", "parse_market_decimal", "decimal_value", "parse_tick_volume",
    "parse_csv_rows",
    "build_bar_record", "validate_bar_record", "bar_ref",
    "validate_source_reference", "build_dataset_manifest_record", "validate_dataset_manifest_record",
    "validate_replay_bounds", "projected_step_count",
    "build_replay_session_record", "validate_replay_session_record",
    "build_replay_step_record", "validate_replay_step_record",
    "build_replay_snapshot_record", "validate_replay_snapshot_record",
    "build_storage_envelope", "validate_storage_envelope",
)
