"""Governed data contracts for TRL-R2-010 Market Intelligence V0 (TRL CORTEX V0).

Implements TRL_R2_010_MARKET_INTELLIGENCE_V0_CONTRACT.md Sections 6-13, 18-19.
Pure data/validation/computation module: no I/O, no MetaTrader5 import, no
adapter, no journal, no ModeService call. Research-only, non-executable,
deterministic. Every score/ranking computation uses ``Decimal`` with
``ROUND_HALF_EVEN`` — never binary float.

Two accelerated-V0 implementation decisions not literally spelled out by the
contract's field tables (recorded here, and in
TRL_R2_010_MARKET_INTELLIGENCE_V0_EVIDENCE.md, as explicit engineering
judgment calls within the Section 21 "tonight-ready" boundary):

1. Decision steps 1-6 (schema validation, instrument/timeframe allowlist,
   evidence completeness/duplication/expiry) are evaluated as pre-flight
   admission gates by the service BEFORE any governed record is
   constructed — a failure produces an ``MI_RECORD_REJECTED`` journal event
   with the exact reason code and no persisted Opportunity Card, rather
   than a persisted BLOCKED Opportunity Card. This keeps
   ``TRL_OPPORTUNITY_CARD.v1.evidence_ids`` always exactly-eleven and
   non-expired (its own Section 6.3 invariant) and keeps the
   ``ordered_evidence_refs`` opportunity-ID input (Section 8.3) always
   well-formed. Steps 7-23 (``evaluate_decision`` below) are the real,
   fully auditable decision engine, always operating over a validly
   constructed opportunity.
2. The Section 7.1 envelope does not list a source for
   ``TRL_OPPORTUNITY_CARD.v1``'s ``market_regime``/``entry_concept``/
   ``invalidation_concept``/``stop_concept``/``ordered_target_concepts``
   fields (Section 6.3). This module accepts them as additional required
   closed top-level envelope fields (operator-authored plain language,
   never automatically generated from evidence) — a minimal, closed,
   auditable extension, not a silent default.
"""

from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re

from .timeline_data import (
    TimelineValidationError,
    canonical_decimal,
    decimal_value,
    deterministic_json_text,
    sha256_text,
    validate_utc_timestamp,
)


# ---------------------------------------------------------------------
# Schema versions and identity domains
# ---------------------------------------------------------------------

SNAPSHOT_SCHEMA = "TRL_MARKET_SNAPSHOT.v1"
EVIDENCE_SCHEMA = "TRL_EVIDENCE_ITEM.v1"
OPPORTUNITY_SCHEMA = "TRL_OPPORTUNITY_CARD.v1"
VIRTUAL_OPPORTUNITY_SCHEMA = "TRL_VIRTUAL_OPPORTUNITY.v1"
DECISION_SCHEMA = "TRL_OPPORTUNITY_DECISION.v1"
TELEMETRY_SCHEMA = "TRL_LEARNING_TELEMETRY.v1"
PREVIEW_SCHEMA = "TRL_MARKET_INTELLIGENCE_BASKET_PREVIEW.v1"
ANALYSIS_INPUT_SCHEMA = "TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1"

SNAPSHOT_ID_DOMAIN = "TRL-MARKET-SNAPSHOT-ID.v1"
EVIDENCE_ID_DOMAIN = "TRL-EVIDENCE-ID.v1"
OPPORTUNITY_ID_DOMAIN = "TRL-OPPORTUNITY-ID.v1"
VIRTUAL_OPPORTUNITY_ID_DOMAIN = "TRL-VIRTUAL-OPPORTUNITY-ID.v1"
DECISION_ID_DOMAIN = "TRL-OPPORTUNITY-DECISION-ID.v1"
TELEMETRY_ID_DOMAIN = "TRL-LEARNING-TELEMETRY-ID.v1"
PREVIEW_ID_DOMAIN = "TRL-BASKET-PREVIEW-ID.v1"

INSTRUMENTS = ("XAUUSD", "NAS100", "EURUSD", "GBPUSD", "USDJPY")
TIMEFRAMES = ("M5", "M15", "H1", "H4", "D1")
SIDES = ("BUY", "SELL")
SESSIONS = ("ASIA", "LONDON", "NEW_YORK", "OVERLAP", "OFF_HOURS")
DATA_SOURCE_CLASSIFICATIONS = (
    "COMMITTED_FIXTURE", "ISOLATED_TEST_FIXTURE", "LOCAL_USER_SUPPLIED", "HISTORICAL_REPLAY",
)
DATA_QUALITY_STATUSES = ("SUFFICIENT", "DEGRADED", "INSUFFICIENT")
EVENT_RISK_CLASSIFICATIONS = ("NONE", "LOW", "MEDIUM", "HIGH")
EVIDENCE_DIRECTIONS = ("SUPPORTS", "OPPOSES", "NEUTRAL")
EVIDENCE_SOURCE_CLASSIFICATIONS = ("SYNTHETIC_FIXTURE", "LOCAL_USER_INPUT")
MARKET_REGIMES = (
    "TRENDING", "RANGING", "VOLATILE_EXPANSION", "VOLATILE_CONTRACTION", "UNCLASSIFIED",
)
DECISION_STATUSES = ("TRADE_CANDIDATE", "WAIT", "REJECT", "BLOCKED", "EXPIRED")
VIRTUAL_STATES = (
    "WATCHING", "ACTIVATED", "INVALIDATED", "EXPIRED", "REJECTED", "SELECTED_FOR_PREVIEW",
)
CALIBRATION_BUCKETS = (
    "HIGH_CONFIDENCE", "MEDIUM_CONFIDENCE", "LOW_CONFIDENCE", "UNCALIBRATED",
)
OUTCOME_CLASSIFICATIONS = (
    "TRUE_POSITIVE", "FALSE_POSITIVE", "TRUE_NEGATIVE", "FALSE_NEGATIVE", "INDETERMINATE",
)
MISSING_DATA_STATUSES = ("COMPLETE", "PARTIAL", "UNAVAILABLE")
TELEMETRY_ORIGINAL_STATUSES = ("TRADE_CANDIDATE", "WAIT", "REJECT", "BLOCKED")

EXECUTION_HANDOFF_STATUS = "EXECUTION_HANDOFF_NOT_APPROVED"

EVIDENCE_CATEGORIES = (
    "MARKET_STRUCTURE", "TREND", "MOMENTUM", "VOLATILITY", "LIQUIDITY_AND_SPREAD",
    "MULTI_TIMEFRAME_ALIGNMENT", "EVENT_RISK", "EXECUTION_COST", "RISK_EXPOSURE",
    "CONTRADICTING_EVIDENCE", "DATA_QUALITY",
)
DIRECTIONAL_EVIDENCE_CATEGORIES = (
    "MARKET_STRUCTURE", "TREND", "MOMENTUM", "MULTI_TIMEFRAME_ALIGNMENT", "CONTRADICTING_EVIDENCE",
)
SEVERITY_CATEGORIES = ("EVENT_RISK", "EXECUTION_COST", "RISK_EXPOSURE", "DATA_QUALITY")

LATTICE_MIN_SIZE = 1
LATTICE_MAX_SIZE = 6
MAX_SELECTED_FOR_PREVIEW = 1
MIN_TARGET_COUNT = 2
MAX_TARGET_COUNT = 4
MAX_TEXT_LENGTH = 256

DATA_QUALITY_MIN = Decimal("0.6000")
TRADE_CANDIDATE_SUPPORT_MIN = Decimal("0.6500")
TRADE_CANDIDATE_CONTRADICTION_MAX = Decimal("0.3500")
REJECT_CONTRADICTION_MIN = Decimal("0.6000")
TRADE_CANDIDATE_UNCERTAINTY_MAX = Decimal("0.4000")
TRADE_CANDIDATE_COST_MAX = Decimal("0.3000")
REJECT_COST_MIN = Decimal("0.7000")
HARD_EVENT_RISK_BLOCK_MIN = Decimal("0.9000")
HARD_RISK_EXPOSURE_BLOCK_MIN = Decimal("0.9000")
WAIT_EVENT_RISK_MIN = Decimal("0.6000")
WAIT_RISK_EXPOSURE_MIN = Decimal("0.6000")

REASON_CODES = (
    "MARKET_INTELLIGENCE_SCHEMA_VALIDATION_FAILED",
    "MARKET_INTELLIGENCE_INSTRUMENT_NOT_ALLOWED",
    "MARKET_INTELLIGENCE_TIMEFRAME_NOT_ALLOWED",
    "MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_MISSING",
    "MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_DUPLICATED",
    "MARKET_INTELLIGENCE_EVIDENCE_EXPIRED",
    "MARKET_INTELLIGENCE_OPPORTUNITY_EXPIRED",
    "MARKET_INTELLIGENCE_DATA_QUALITY_BELOW_MINIMUM",
    "MARKET_INTELLIGENCE_HARD_EVENT_RISK_BLOCK",
    "MARKET_INTELLIGENCE_HARD_RISK_EXPOSURE_BLOCK",
    "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED",
    "STRATEGY_PARAMETERS_NOT_APPROVED",
    "MARKET_INTELLIGENCE_INVALIDATION_ALREADY_OCCURRED",
    "MARKET_INTELLIGENCE_STRUCTURALLY_INCONSISTENT",
    "MARKET_INTELLIGENCE_CONTRADICTION_REJECTED",
    "MARKET_INTELLIGENCE_TRANSACTION_COST_DESTROYS_EDGE",
    "MARKET_INTELLIGENCE_TRIGGER_NOT_ACTIVE",
    "MARKET_INTELLIGENCE_EVENT_RISK_WAIT",
    "MARKET_INTELLIGENCE_RISK_EXPOSURE_WAIT",
    "MARKET_INTELLIGENCE_UNCERTAINTY_ABOVE_THRESHOLD",
    "MARKET_INTELLIGENCE_SUPPORT_BELOW_THRESHOLD",
    "MARKET_INTELLIGENCE_CONTRADICTION_ABOVE_THRESHOLD",
    "MARKET_INTELLIGENCE_TRANSACTION_COST_MARGINAL",
    "MARKET_INTELLIGENCE_ALL_GATES_PASSED",
    "MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE",
)

SCHEMA_FAIL = "MARKET_INTELLIGENCE_SCHEMA_VALIDATION_FAILED"


class MarketIntelligenceValidationError(ValueError):
    """A stable, non-secret Market Intelligence validation failure."""

    def __init__(self, reason_code, message=None):
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code {!r} is not governed".format(reason_code))
        self.reason_code = reason_code
        super().__init__(message or reason_code)


def _fail(reason_code, message=None):
    raise MarketIntelligenceValidationError(reason_code, message)


# ---------------------------------------------------------------------
# Field-level primitives
# ---------------------------------------------------------------------

def _bounded_text(value, field, maximum, allow_empty=False, reason_code=SCHEMA_FAIL):
    if not isinstance(value, str):
        _fail(reason_code, "{} must be a string".format(field))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail(reason_code, "{} contains a control character".format(field))
    if not allow_empty and not value.strip():
        _fail(reason_code, "{} must not be empty".format(field))
    if len(value) > maximum:
        _fail(reason_code, "{} exceeds the maximum length".format(field))
    return value


def _price(value, field, reason_code=SCHEMA_FAIL):
    try:
        return canonical_decimal(value, field, positive=True, allow_zero=False)
    except TimelineValidationError as error:
        _fail(reason_code, str(error))


def _nonneg_price(value, field, reason_code=SCHEMA_FAIL):
    try:
        return canonical_decimal(value, field, positive=True, allow_zero=True)
    except TimelineValidationError as error:
        _fail(reason_code, str(error))


def _bool(value, field, reason_code=SCHEMA_FAIL):
    if not isinstance(value, bool):
        _fail(reason_code, "{} must be a strict boolean".format(field))
    return value


def _score_input(value, field, reason_code=SCHEMA_FAIL):
    """Validate a [0.0000, 1.0000] exact decimal input at up to 4 dp."""
    if isinstance(value, bool) or isinstance(value, float):
        _fail(reason_code, "{} must be an exact decimal, not boolean/float".format(field))
    if not isinstance(value, (str, int, Decimal)):
        _fail(reason_code, "{} must be an exact decimal".format(field))
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        _fail(reason_code, "{} must be a valid decimal".format(field))
        return None
    if not number.is_finite():
        _fail(reason_code, "{} must be finite".format(field))
    if number < 0 or number > 1:
        _fail(reason_code, "{} must be within [0.0000, 1.0000]".format(field))
    exponent = number.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -4:
        _fail(reason_code, "{} must have at most 4 decimal places".format(field))
    return number.quantize(Decimal("0.0001"))


def quantize_4(value):
    """quantize_4(value) = Decimal(value).quantize(Decimal("0.0001"), ROUND_HALF_EVEN)."""
    if isinstance(value, bool):
        raise MarketIntelligenceValidationError(SCHEMA_FAIL, "cannot quantize a boolean")
    if isinstance(value, float):
        raise MarketIntelligenceValidationError(SCHEMA_FAIL, "cannot quantize a binary float")
    try:
        number = value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise MarketIntelligenceValidationError(SCHEMA_FAIL, "value is not a valid decimal")
    if not number.is_finite():
        raise MarketIntelligenceValidationError(SCHEMA_FAIL, "value must be finite")
    quantized = number.quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
    if quantized == 0:
        quantized = Decimal("0.0000")
    return quantized


def score_text(value):
    """Return the fixed four-decimal canonical string form of a quantized score."""
    quantized = quantize_4(value)
    if not (Decimal("0.0000") <= quantized <= Decimal("1.0000")):
        raise MarketIntelligenceValidationError(SCHEMA_FAIL, "score is out of bounds")
    return format(quantized, "f")


_SCORE_TEXT_PATTERN = re.compile(r"^[01]\.\d{4}$")


def _score_field(value, field, reason_code=SCHEMA_FAIL):
    if not isinstance(value, str) or not _SCORE_TEXT_PATTERN.fullmatch(value):
        _fail(reason_code, "{} must be a fixed four-decimal score string".format(field))
    number = Decimal(value)
    if number < 0 or number > 1:
        _fail(reason_code, "{} must be within [0.0000, 1.0000]".format(field))
    return value


def _identity_material(fields, expected_keys, reason_code=SCHEMA_FAIL):
    if set(fields) != set(expected_keys):
        _fail(reason_code, "identity input has an invalid field set")
    return deterministic_json_text(fields)


def _decimal_text(value):
    return format(value, "f")


# ---------------------------------------------------------------------
# TRL_MARKET_SNAPSHOT.v1 (Section 6.1) and its transport-input shape
# ---------------------------------------------------------------------

SNAPSHOT_INPUT_FIELDS = (
    "instrument", "timeframe", "observed_at_utc", "open", "high", "low", "close",
    "spread", "volatility_measure", "volatility_method", "session",
    "data_source_classification", "data_quality_status", "event_risk_classification",
)

SNAPSHOT_FIELDS = ("schema_version", "snapshot_id") + SNAPSHOT_INPUT_FIELDS + (
    "canonical_snapshot_hash",
)

_TOKEN_PATTERN = re.compile(r"^[A-Z0-9]{2,16}$")


def validate_snapshot_input(value):
    """Structural validation of the embedded ``snapshot`` object (Section 7.1).

    Deliberately does NOT enforce instrument/timeframe allowlist membership
    (see module docstring, decision 1) — callers must separately call
    ``check_instrument_and_timeframe`` as a distinct pre-flight gate.
    """
    if not isinstance(value, dict) or set(value) != set(SNAPSHOT_INPUT_FIELDS):
        _fail(SCHEMA_FAIL, "snapshot has an invalid field set")
    instrument = _bounded_text(value["instrument"], "instrument", 16)
    if not _TOKEN_PATTERN.fullmatch(instrument):
        _fail(SCHEMA_FAIL, "instrument must be a bounded uppercase alphanumeric token")
    timeframe = _bounded_text(value["timeframe"], "timeframe", 8)
    if not _TOKEN_PATTERN.fullmatch(timeframe):
        _fail(SCHEMA_FAIL, "timeframe must be a bounded uppercase alphanumeric token")
    observed_at = value["observed_at_utc"]
    validate_utc_timestamp(observed_at, "observed_at_utc")
    open_ = _price(value["open"], "open")
    high = _price(value["high"], "high")
    low = _price(value["low"], "low")
    close = _price(value["close"], "close")
    if not (decimal_value(low) <= decimal_value(open_) <= decimal_value(high)):
        _fail(SCHEMA_FAIL, "open must be within [low, high]")
    if not (decimal_value(low) <= decimal_value(close) <= decimal_value(high)):
        _fail(SCHEMA_FAIL, "close must be within [low, high]")
    spread = _nonneg_price(value["spread"], "spread")
    volatility_measure = _nonneg_price(value["volatility_measure"], "volatility_measure")
    volatility_method = _bounded_text(value["volatility_method"], "volatility_method", 128)
    session = value["session"]
    if session not in SESSIONS:
        _fail(SCHEMA_FAIL, "session is not governed")
    data_source_classification = value["data_source_classification"]
    if data_source_classification not in DATA_SOURCE_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "data_source_classification is not governed")
    data_quality_status = value["data_quality_status"]
    if data_quality_status not in DATA_QUALITY_STATUSES:
        _fail(SCHEMA_FAIL, "data_quality_status is not governed")
    event_risk_classification = value["event_risk_classification"]
    if event_risk_classification is not None and event_risk_classification not in EVENT_RISK_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "event_risk_classification is not governed")
    return {
        "instrument": instrument, "timeframe": timeframe, "observed_at_utc": observed_at,
        "open": open_, "high": high, "low": low, "close": close, "spread": spread,
        "volatility_measure": volatility_measure, "volatility_method": volatility_method,
        "session": session, "data_source_classification": data_source_classification,
        "data_quality_status": data_quality_status,
        "event_risk_classification": event_risk_classification,
    }


def check_instrument_and_timeframe(instrument, timeframe):
    """Decision-engine steps 2/3 (Section 10.4), evaluated as a pre-flight
    gate (module docstring decision 1). No alias is ever guessed."""
    if instrument not in INSTRUMENTS:
        _fail("MARKET_INTELLIGENCE_INSTRUMENT_NOT_ALLOWED")
    if timeframe not in TIMEFRAMES:
        _fail("MARKET_INTELLIGENCE_TIMEFRAME_NOT_ALLOWED")


def snapshot_id_for(fields):
    expected = SNAPSHOT_INPUT_FIELDS
    material = _identity_material(fields, expected)
    return "mkt_" + sha256_text(SNAPSHOT_ID_DOMAIN + "\n" + material)[:32]


def canonical_snapshot_hash_for(fields_with_id):
    expected = SNAPSHOT_INPUT_FIELDS + ("snapshot_id",)
    if set(fields_with_id) != set(expected):
        _fail(SCHEMA_FAIL, "snapshot hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields_with_id))


def build_snapshot_record(validated_input):
    snapshot_id = snapshot_id_for(validated_input)
    hash_fields = dict(validated_input)
    hash_fields["snapshot_id"] = snapshot_id
    canonical_hash = canonical_snapshot_hash_for(hash_fields)
    record = {"schema_version": SNAPSHOT_SCHEMA, "snapshot_id": snapshot_id}
    record.update(validated_input)
    record["canonical_snapshot_hash"] = canonical_hash
    return validate_snapshot_record(record)


def snapshot_mid_price(record):
    return quantize_4(
        (decimal_value(record["high"]) + decimal_value(record["low"])) / Decimal("2")
    )


def validate_snapshot_record(record):
    if not isinstance(record, dict) or set(record) != set(SNAPSHOT_FIELDS):
        _fail(SCHEMA_FAIL, "snapshot record has an invalid field set")
    if record["schema_version"] != SNAPSHOT_SCHEMA:
        _fail(SCHEMA_FAIL, "snapshot schema is unsupported")
    if not re.fullmatch(r"mkt_[0-9a-f]{32}", record["snapshot_id"] or ""):
        _fail(SCHEMA_FAIL, "snapshot_id is invalid")
    validated_input = validate_snapshot_input(
        {key: record[key] for key in SNAPSHOT_INPUT_FIELDS}
    )
    hash_fields = dict(validated_input)
    hash_fields["snapshot_id"] = record["snapshot_id"]
    expected_hash = canonical_snapshot_hash_for(hash_fields)
    if record["canonical_snapshot_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_snapshot_hash does not match canonical content")
    clean = {"schema_version": SNAPSHOT_SCHEMA, "snapshot_id": record["snapshot_id"]}
    clean.update(validated_input)
    clean["canonical_snapshot_hash"] = record["canonical_snapshot_hash"]
    return clean


# ---------------------------------------------------------------------
# TRL_EVIDENCE_ITEM.v1 (Section 6.2) and its transport-input shape
# ---------------------------------------------------------------------

EVIDENCE_INPUT_FIELDS = (
    "category", "evidence_direction", "normalized_strength", "confidence",
    "source_classification", "source_reference", "observed_at_utc",
    "expires_at_utc", "explanation",
)

EVIDENCE_FIELDS = (
    "schema_version", "evidence_id", "snapshot_id", "canonical_snapshot_hash",
    "proposed_side", "category", "evidence_direction", "normalized_strength",
    "confidence", "source_classification", "source_reference", "observed_at_utc",
    "expires_at_utc", "explanation", "canonical_evidence_hash",
)


def validate_evidence_input(value):
    if not isinstance(value, dict) or set(value) != set(EVIDENCE_INPUT_FIELDS):
        _fail(SCHEMA_FAIL, "evidence input has an invalid field set")
    category = value["category"]
    if category not in EVIDENCE_CATEGORIES:
        _fail(SCHEMA_FAIL, "category is not governed")
    direction = value["evidence_direction"]
    if direction not in EVIDENCE_DIRECTIONS:
        _fail(SCHEMA_FAIL, "evidence_direction is not governed")
    normalized_strength = _score_input(value["normalized_strength"], "normalized_strength")
    confidence = _score_input(value["confidence"], "confidence")
    source_classification = value["source_classification"]
    if source_classification not in EVIDENCE_SOURCE_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "source_classification is not governed")
    source_reference = _bounded_text(value["source_reference"], "source_reference", 256)
    observed_at = value["observed_at_utc"]
    observed_dt = validate_utc_timestamp(observed_at, "observed_at_utc")
    expires_at = value["expires_at_utc"]
    expires_dt = validate_utc_timestamp(expires_at, "expires_at_utc")
    if expires_dt <= observed_dt:
        _fail(SCHEMA_FAIL, "expires_at_utc must be strictly after observed_at_utc")
    explanation = _bounded_text(value["explanation"], "explanation", 1000)
    return {
        "category": category, "evidence_direction": direction,
        "normalized_strength": normalized_strength, "confidence": confidence,
        "source_classification": source_classification, "source_reference": source_reference,
        "observed_at_utc": observed_at, "expires_at_utc": expires_at, "explanation": explanation,
    }


def check_evidence_completeness(evidence_inputs, created_at_dt):
    """Decision-engine steps 4/5/6 (Section 10.4), evaluated as a pre-flight
    gate (module docstring decision 1). ``evidence_inputs`` is the ordered
    list of already-``validate_evidence_input``-cleaned dicts. Returns a
    ``{category: item}`` mapping covering exactly the eleven categories."""
    by_category = {}
    for item in evidence_inputs:
        by_category.setdefault(item["category"], []).append(item)
    for category in EVIDENCE_CATEGORIES:
        if category not in by_category:
            _fail("MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_MISSING")
    for category in EVIDENCE_CATEGORIES:
        if len(by_category[category]) > 1:
            _fail("MARKET_INTELLIGENCE_EVIDENCE_CATEGORY_DUPLICATED")
    for category in EVIDENCE_CATEGORIES:
        item = by_category[category][0]
        expires_dt = validate_utc_timestamp(item["expires_at_utc"])
        if expires_dt <= created_at_dt:
            _fail("MARKET_INTELLIGENCE_EVIDENCE_EXPIRED")
    return {category: by_category[category][0] for category in EVIDENCE_CATEGORIES}


def evidence_id_for(fields):
    expected = (
        "snapshot_id", "proposed_side", "category", "evidence_direction",
        "normalized_strength", "confidence", "source_classification",
        "source_reference", "observed_at_utc", "expires_at_utc",
    )
    material = _identity_material(fields, expected)
    return "evd_" + sha256_text(EVIDENCE_ID_DOMAIN + "\n" + material)[:32]


def canonical_evidence_hash_for(fields_without_hash):
    expected = (
        "schema_version", "evidence_id", "snapshot_id", "canonical_snapshot_hash",
        "proposed_side", "category", "evidence_direction", "normalized_strength",
        "confidence", "source_classification", "source_reference", "observed_at_utc",
        "expires_at_utc", "explanation",
    )
    if set(fields_without_hash) != set(expected):
        _fail(SCHEMA_FAIL, "evidence hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields_without_hash))


def build_evidence_record(snapshot_id, canonical_snapshot_hash, proposed_side, validated_input):
    identity_fields = {
        "snapshot_id": snapshot_id, "proposed_side": proposed_side,
        "category": validated_input["category"],
        "evidence_direction": validated_input["evidence_direction"],
        "normalized_strength": _decimal_text(validated_input["normalized_strength"]),
        "confidence": _decimal_text(validated_input["confidence"]),
        "source_classification": validated_input["source_classification"],
        "source_reference": validated_input["source_reference"],
        "observed_at_utc": validated_input["observed_at_utc"],
        "expires_at_utc": validated_input["expires_at_utc"],
    }
    evidence_id = evidence_id_for(identity_fields)
    record_without_hash = {
        "schema_version": EVIDENCE_SCHEMA, "evidence_id": evidence_id,
        "snapshot_id": snapshot_id, "canonical_snapshot_hash": canonical_snapshot_hash,
        "proposed_side": proposed_side, "category": validated_input["category"],
        "evidence_direction": validated_input["evidence_direction"],
        "normalized_strength": _decimal_text(validated_input["normalized_strength"]),
        "confidence": _decimal_text(validated_input["confidence"]),
        "source_classification": validated_input["source_classification"],
        "source_reference": validated_input["source_reference"],
        "observed_at_utc": validated_input["observed_at_utc"],
        "expires_at_utc": validated_input["expires_at_utc"],
        "explanation": validated_input["explanation"],
    }
    record = dict(record_without_hash)
    record["canonical_evidence_hash"] = canonical_evidence_hash_for(record_without_hash)
    return validate_evidence_record(record)


def validate_evidence_record(record):
    if not isinstance(record, dict) or set(record) != set(EVIDENCE_FIELDS):
        _fail(SCHEMA_FAIL, "evidence record has an invalid field set")
    if record["schema_version"] != EVIDENCE_SCHEMA:
        _fail(SCHEMA_FAIL, "evidence schema is unsupported")
    if not re.fullmatch(r"evd_[0-9a-f]{32}", record["evidence_id"] or ""):
        _fail(SCHEMA_FAIL, "evidence_id is invalid")
    if not re.fullmatch(r"mkt_[0-9a-f]{32}", record["snapshot_id"] or ""):
        _fail(SCHEMA_FAIL, "snapshot_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_snapshot_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_snapshot_hash is invalid")
    if record["proposed_side"] not in SIDES:
        _fail(SCHEMA_FAIL, "proposed_side is not governed")
    if record["category"] not in EVIDENCE_CATEGORIES:
        _fail(SCHEMA_FAIL, "category is not governed")
    if record["evidence_direction"] not in EVIDENCE_DIRECTIONS:
        _fail(SCHEMA_FAIL, "evidence_direction is not governed")
    _score_field(record["normalized_strength"], "normalized_strength")
    _score_field(record["confidence"], "confidence")
    if record["source_classification"] not in EVIDENCE_SOURCE_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "source_classification is not governed")
    _bounded_text(record["source_reference"], "source_reference", 256)
    validate_utc_timestamp(record["observed_at_utc"], "observed_at_utc")
    validate_utc_timestamp(record["expires_at_utc"], "expires_at_utc")
    _bounded_text(record["explanation"], "explanation", 1000)
    expected_hash = canonical_evidence_hash_for(
        {key: value for key, value in record.items() if key != "canonical_evidence_hash"}
    )
    if record["canonical_evidence_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_evidence_hash does not match canonical content")
    return dict(record)


def effective_evidence_score(item):
    """effective_evidence_score(item) = quantize_4(normalized_strength * confidence)."""
    strength = Decimal(item["normalized_strength"])
    confidence = Decimal(item["confidence"])
    return quantize_4(strength * confidence)


# ---------------------------------------------------------------------
# Score aggregation (Section 10.2)
# ---------------------------------------------------------------------

def compute_scores(evidence_by_category):
    """Return the seven canonical opportunity scores as fixed four-decimal
    strings, computed strictly via ``Decimal`` with a single final
    ``quantize_4`` per aggregate (never repeated intermediate rounding)."""
    supporting_sum = Decimal("0")
    opposing_sum = Decimal("0")
    for category in DIRECTIONAL_EVIDENCE_CATEGORIES:
        item = evidence_by_category[category]
        effective = effective_evidence_score(item)
        if item["evidence_direction"] == "SUPPORTS":
            supporting_sum += effective
        elif item["evidence_direction"] == "OPPOSES":
            opposing_sum += effective
    supporting_score = quantize_4(supporting_sum / Decimal("5"))
    contradiction_score = quantize_4(opposing_sum / Decimal("5"))

    uncertainty_sum = Decimal("0")
    for category in EVIDENCE_CATEGORIES:
        confidence = Decimal(evidence_by_category[category]["confidence"])
        uncertainty_sum += Decimal("1.0000") - confidence
    uncertainty_score = quantize_4(uncertainty_sum / Decimal("11"))

    data_quality_score = effective_evidence_score(evidence_by_category["DATA_QUALITY"])
    estimated_cost_score = effective_evidence_score(evidence_by_category["EXECUTION_COST"])
    event_risk_score = effective_evidence_score(evidence_by_category["EVENT_RISK"])
    risk_exposure_score = effective_evidence_score(evidence_by_category["RISK_EXPOSURE"])

    return {
        "supporting_score": format(supporting_score, "f"),
        "contradiction_score": format(contradiction_score, "f"),
        "uncertainty_score": format(uncertainty_score, "f"),
        "data_quality_score": format(data_quality_score, "f"),
        "estimated_cost_score": format(estimated_cost_score, "f"),
        "event_risk_score": format(event_risk_score, "f"),
        "risk_exposure_score": format(risk_exposure_score, "f"),
    }


def partition_evidence_by_direction(evidence_by_category):
    """Return (supporting_evidence_ids, opposing_evidence_ids), restricted
    to the five directional categories (Section 6.5)."""
    supporting, opposing = [], []
    for category in DIRECTIONAL_EVIDENCE_CATEGORIES:
        item = evidence_by_category[category]
        if item["evidence_direction"] == "SUPPORTS":
            supporting.append(item["evidence_id"])
        elif item["evidence_direction"] == "OPPOSES":
            opposing.append(item["evidence_id"])
    return supporting, opposing


# ---------------------------------------------------------------------
# TRL_OPPORTUNITY_CARD.v1 (Section 6.3)
# ---------------------------------------------------------------------

# Accelerated-V0 extension (module docstring decision 2): required
# additional closed top-level envelope fields supplying the concept text
# and market regime Section 7.1 does not otherwise source.
OPPORTUNITY_CONCEPT_INPUT_FIELDS = (
    "market_regime", "entry_concept", "invalidation_concept", "stop_concept",
    "ordered_target_concepts",
)

OPPORTUNITY_FIELDS = (
    "schema_version", "opportunity_id", "snapshot_id", "canonical_snapshot_hash",
    "instrument", "timeframe", "proposed_side", "market_regime", "strategy_id",
    "strategy_version", "entry_concept", "invalidation_concept", "stop_concept",
    "ordered_target_concepts", "evidence_ids", "activation_satisfied", "invalidation_satisfied",
    "supporting_score", "contradiction_score", "uncertainty_score", "data_quality_score",
    "estimated_cost_score", "event_risk_score", "risk_exposure_score",
    "decision_status", "decision_reason_codes", "created_at_utc", "expiry_utc",
    "canonical_opportunity_hash",
)

_OPPORTUNITY_IDENTITY_KEYS = (
    "snapshot_id", "proposed_side", "market_regime", "strategy_id", "strategy_version",
    "entry_concept", "invalidation_concept", "stop_concept", "ordered_target_concepts",
    "activation_satisfied", "invalidation_satisfied", "ordered_evidence_refs",
)

_OPPORTUNITY_HASH_SCORE_KEYS = (
    "supporting_score", "contradiction_score", "uncertainty_score", "data_quality_score",
    "estimated_cost_score", "event_risk_score", "risk_exposure_score",
)


def validate_opportunity_concept_input(value):
    if not isinstance(value, dict) or set(value) != set(OPPORTUNITY_CONCEPT_INPUT_FIELDS):
        _fail(SCHEMA_FAIL, "opportunity concept input has an invalid field set")
    market_regime = value["market_regime"]
    if market_regime not in MARKET_REGIMES:
        _fail(SCHEMA_FAIL, "market_regime is not governed")
    entry_concept = _bounded_text(value["entry_concept"], "entry_concept", MAX_TEXT_LENGTH)
    invalidation_concept = _bounded_text(
        value["invalidation_concept"], "invalidation_concept", MAX_TEXT_LENGTH,
    )
    stop_concept = _bounded_text(value["stop_concept"], "stop_concept", MAX_TEXT_LENGTH)
    targets = value["ordered_target_concepts"]
    if not isinstance(targets, list) or not (MIN_TARGET_COUNT <= len(targets) <= MAX_TARGET_COUNT):
        _fail(SCHEMA_FAIL, "ordered_target_concepts must contain 2 to 4 items")
    clean_targets = [
        _bounded_text(item, "ordered_target_concepts[{}]".format(index), MAX_TEXT_LENGTH)
        for index, item in enumerate(targets)
    ]
    return {
        "market_regime": market_regime, "entry_concept": entry_concept,
        "invalidation_concept": invalidation_concept, "stop_concept": stop_concept,
        "ordered_target_concepts": clean_targets,
    }


def opportunity_id_for(fields):
    material = _identity_material(fields, _OPPORTUNITY_IDENTITY_KEYS)
    return "opp_" + sha256_text(OPPORTUNITY_ID_DOMAIN + "\n" + material)[:32]


def canonical_opportunity_hash_for(fields_without_hash):
    expected = _OPPORTUNITY_IDENTITY_KEYS + ("opportunity_id",) + _OPPORTUNITY_HASH_SCORE_KEYS
    if set(fields_without_hash) != set(expected):
        _fail(SCHEMA_FAIL, "opportunity hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields_without_hash))


def build_opportunity_record(
    *, snapshot_record, proposed_side, strategy_id, strategy_version,
    concept_input, evidence_by_category, activation_satisfied, invalidation_satisfied,
    created_at_utc, expiry_utc,
):
    ordered_evidence_refs = [
        [evidence_by_category[category]["evidence_id"], evidence_by_category[category]["canonical_evidence_hash"]]
        for category in EVIDENCE_CATEGORIES
    ]
    identity_fields = {
        "snapshot_id": snapshot_record["snapshot_id"], "proposed_side": proposed_side,
        "market_regime": concept_input["market_regime"], "strategy_id": strategy_id,
        "strategy_version": strategy_version, "entry_concept": concept_input["entry_concept"],
        "invalidation_concept": concept_input["invalidation_concept"],
        "stop_concept": concept_input["stop_concept"],
        "ordered_target_concepts": concept_input["ordered_target_concepts"],
        "activation_satisfied": activation_satisfied,
        "invalidation_satisfied": invalidation_satisfied,
        "ordered_evidence_refs": ordered_evidence_refs,
    }
    opportunity_id = opportunity_id_for(identity_fields)
    scores = compute_scores(evidence_by_category)
    hash_fields = dict(identity_fields)
    hash_fields["opportunity_id"] = opportunity_id
    hash_fields.update(scores)
    canonical_hash = canonical_opportunity_hash_for(hash_fields)
    record = {
        "schema_version": OPPORTUNITY_SCHEMA, "opportunity_id": opportunity_id,
        "snapshot_id": snapshot_record["snapshot_id"],
        "canonical_snapshot_hash": snapshot_record["canonical_snapshot_hash"],
        "instrument": snapshot_record["instrument"], "timeframe": snapshot_record["timeframe"],
        "proposed_side": proposed_side, "market_regime": concept_input["market_regime"],
        "strategy_id": strategy_id, "strategy_version": strategy_version,
        "entry_concept": concept_input["entry_concept"],
        "invalidation_concept": concept_input["invalidation_concept"],
        "stop_concept": concept_input["stop_concept"],
        "ordered_target_concepts": concept_input["ordered_target_concepts"],
        "evidence_ids": [evidence_by_category[category]["evidence_id"] for category in EVIDENCE_CATEGORIES],
        "activation_satisfied": activation_satisfied,
        "invalidation_satisfied": invalidation_satisfied,
        "decision_status": "WAIT",
        "decision_reason_codes": [],
        "created_at_utc": created_at_utc,
        "expiry_utc": expiry_utc,
        "canonical_opportunity_hash": canonical_hash,
    }
    record.update(scores)
    return validate_opportunity_record(record)


def validate_opportunity_record(record):
    if not isinstance(record, dict) or set(record) != set(OPPORTUNITY_FIELDS):
        _fail(SCHEMA_FAIL, "opportunity record has an invalid field set")
    if record["schema_version"] != OPPORTUNITY_SCHEMA:
        _fail(SCHEMA_FAIL, "opportunity schema is unsupported")
    if not re.fullmatch(r"opp_[0-9a-f]{32}", record["opportunity_id"] or ""):
        _fail(SCHEMA_FAIL, "opportunity_id is invalid")
    if not re.fullmatch(r"mkt_[0-9a-f]{32}", record["snapshot_id"] or ""):
        _fail(SCHEMA_FAIL, "snapshot_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_snapshot_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_snapshot_hash is invalid")
    _bounded_text(record["instrument"], "instrument", 16)
    _bounded_text(record["timeframe"], "timeframe", 8)
    if record["proposed_side"] not in SIDES:
        _fail(SCHEMA_FAIL, "proposed_side is not governed")
    if record["market_regime"] not in MARKET_REGIMES:
        _fail(SCHEMA_FAIL, "market_regime is not governed")
    _bounded_text(record["strategy_id"], "strategy_id", MAX_TEXT_LENGTH)
    _bounded_text(record["strategy_version"], "strategy_version", MAX_TEXT_LENGTH)
    _bounded_text(record["entry_concept"], "entry_concept", MAX_TEXT_LENGTH)
    _bounded_text(record["invalidation_concept"], "invalidation_concept", MAX_TEXT_LENGTH)
    _bounded_text(record["stop_concept"], "stop_concept", MAX_TEXT_LENGTH)
    targets = record["ordered_target_concepts"]
    if not isinstance(targets, list) or not (MIN_TARGET_COUNT <= len(targets) <= MAX_TARGET_COUNT):
        _fail(SCHEMA_FAIL, "ordered_target_concepts must contain 2 to 4 items")
    for index, item in enumerate(targets):
        _bounded_text(item, "ordered_target_concepts[{}]".format(index), MAX_TEXT_LENGTH)
    evidence_ids = record["evidence_ids"]
    if not isinstance(evidence_ids, list) or len(evidence_ids) != len(EVIDENCE_CATEGORIES):
        _fail(SCHEMA_FAIL, "evidence_ids must contain exactly eleven entries")
    for evidence_id in evidence_ids:
        if not re.fullmatch(r"evd_[0-9a-f]{32}", evidence_id or ""):
            _fail(SCHEMA_FAIL, "evidence_ids contains an invalid entry")
    activation_satisfied = _bool(record["activation_satisfied"], "activation_satisfied")
    invalidation_satisfied = _bool(record["invalidation_satisfied"], "invalidation_satisfied")
    for key in _OPPORTUNITY_HASH_SCORE_KEYS:
        _score_field(record[key], key)
    if record["decision_status"] not in DECISION_STATUSES:
        _fail(SCHEMA_FAIL, "decision_status is not governed")
    reason_codes = record["decision_reason_codes"]
    if not isinstance(reason_codes, list) or len(reason_codes) > 32:
        _fail(SCHEMA_FAIL, "decision_reason_codes must be a bounded list")
    for code in reason_codes:
        if code not in REASON_CODES:
            _fail(SCHEMA_FAIL, "decision_reason_codes contains an ungoverned code")
    validate_utc_timestamp(record["created_at_utc"], "created_at_utc")
    expiry_dt = validate_utc_timestamp(record["expiry_utc"], "expiry_utc")
    created_dt = validate_utc_timestamp(record["created_at_utc"])
    if expiry_dt <= created_dt:
        _fail(SCHEMA_FAIL, "expiry_utc must be strictly after created_at_utc")

    ordered_evidence_refs = None  # recomputed by caller when hashing; not stored directly
    identity_fields = {
        "snapshot_id": record["snapshot_id"], "proposed_side": record["proposed_side"],
        "market_regime": record["market_regime"], "strategy_id": record["strategy_id"],
        "strategy_version": record["strategy_version"], "entry_concept": record["entry_concept"],
        "invalidation_concept": record["invalidation_concept"], "stop_concept": record["stop_concept"],
        "ordered_target_concepts": record["ordered_target_concepts"],
        "activation_satisfied": activation_satisfied, "invalidation_satisfied": invalidation_satisfied,
        "ordered_evidence_refs": record.get("_ordered_evidence_refs"),
    }
    del ordered_evidence_refs
    # ordered_evidence_refs is not a stored field on the record itself (it is
    # a hash-input intermediate the caller supplied only at construction
    # time); a stored record is re-validated for shape/type/enum here, and
    # its canonical_opportunity_hash is trusted as constructed rather than
    # blindly recomputed, since ordered_evidence_refs would require a
    # journal lookup this pure data function does not have access to. The
    # service layer independently re-verifies the hash immediately after
    # ``build_opportunity_record`` returns (same call, same process), which
    # is where genuine tamper-evidence is enforced end-to-end.
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_opportunity_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_opportunity_hash is invalid")
    return dict(record)


# ---------------------------------------------------------------------
# Virtual-candidate input (Section 11.1) and TRL_VIRTUAL_OPPORTUNITY.v1 (6.4)
# ---------------------------------------------------------------------

VIRTUAL_CANDIDATE_INPUT_FIELDS = (
    "entry_trigger", "stop_price", "target_prices", "target_allocations",
    "hypothetical_total_quantity", "activation_satisfied", "invalidation_satisfied",
    "expires_at_utc",
)

VIRTUAL_OPPORTUNITY_FIELDS = (
    "schema_version", "virtual_opportunity_id", "opportunity_id", "canonical_opportunity_hash",
    "rank", "hypothetical_entry_trigger", "stop", "ordered_targets",
    "expected_reward_risk_ratio", "estimated_transaction_cost", "activation_condition",
    "invalidation_condition", "state", "expiry_utc", "non_executable",
    "canonical_virtual_opportunity_hash",
)


def _allocation_decimal(value, field):
    if isinstance(value, bool) or isinstance(value, float):
        _fail(SCHEMA_FAIL, "{} must be an exact decimal, not boolean/float".format(field))
    if not isinstance(value, (str, int, Decimal)):
        _fail(SCHEMA_FAIL, "{} must be an exact decimal".format(field))
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        _fail(SCHEMA_FAIL, "{} must be a valid decimal".format(field))
        return None
    if not number.is_finite() or number <= 0:
        _fail(SCHEMA_FAIL, "{} must be a finite positive decimal".format(field))
    exponent = number.as_tuple().exponent
    if isinstance(exponent, int) and exponent < -4:
        _fail(SCHEMA_FAIL, "{} must have at most 4 decimal places".format(field))
    return number.quantize(Decimal("0.0001"))


def validate_virtual_candidate_input(value):
    if not isinstance(value, dict) or set(value) != set(VIRTUAL_CANDIDATE_INPUT_FIELDS):
        _fail(SCHEMA_FAIL, "virtual candidate input has an invalid field set")
    entry_trigger = _price(value["entry_trigger"], "entry_trigger")
    stop_price = _price(value["stop_price"], "stop_price")
    targets = value["target_prices"]
    if not isinstance(targets, list) or not (MIN_TARGET_COUNT <= len(targets) <= MAX_TARGET_COUNT):
        _fail(SCHEMA_FAIL, "target_prices must contain 2 to 4 items")
    clean_targets = [_price(item, "target_prices[{}]".format(index)) for index, item in enumerate(targets)]
    allocations = value["target_allocations"]
    if not isinstance(allocations, list) or len(allocations) != len(clean_targets):
        _fail(SCHEMA_FAIL, "target_allocations must align one-to-one with target_prices")
    clean_allocations = [
        _allocation_decimal(item, "target_allocations[{}]".format(index))
        for index, item in enumerate(allocations)
    ]
    if sum(clean_allocations, Decimal("0")) != Decimal("100.0000"):
        _fail(SCHEMA_FAIL, "target_allocations must sum to exactly 100.0000")
    quantity = value["hypothetical_total_quantity"]
    clean_quantity = None
    if quantity is not None:
        clean_quantity = _price(quantity, "hypothetical_total_quantity")
    activation_satisfied = _bool(value["activation_satisfied"], "activation_satisfied")
    invalidation_satisfied = _bool(value["invalidation_satisfied"], "invalidation_satisfied")
    expires_at = value["expires_at_utc"]
    validate_utc_timestamp(expires_at, "expires_at_utc")
    return {
        "entry_trigger": entry_trigger, "stop_price": stop_price,
        "target_prices": clean_targets,
        "target_allocations": [_decimal_text(item) for item in clean_allocations],
        "hypothetical_total_quantity": clean_quantity,
        "activation_satisfied": activation_satisfied,
        "invalidation_satisfied": invalidation_satisfied, "expires_at_utc": expires_at,
    }


def candidate_geometry_valid(side, entry_trigger, stop_price, target_prices):
    """Section 11.1 BUY/SELL geometry rules."""
    entry = decimal_value(entry_trigger)
    stop = decimal_value(stop_price)
    targets = [decimal_value(item) for item in target_prices]
    if side == "BUY":
        if not (stop < entry):
            return False
        if not all(target > entry for target in targets):
            return False
        return all(targets[index] < targets[index + 1] for index in range(len(targets) - 1))
    if side == "SELL":
        if not (stop > entry):
            return False
        if not all(target < entry for target in targets):
            return False
        return all(targets[index] > targets[index + 1] for index in range(len(targets) - 1))
    return False


def compute_reward_risk(entry_trigger, stop_price, target_prices, target_allocations, mid_price):
    """``mid_price`` must be a ``Decimal`` (see ``snapshot_mid_price``)."""
    entry = decimal_value(entry_trigger)
    stop = decimal_value(stop_price)
    risk_distance = abs(entry - stop)
    if risk_distance == 0:
        reward_risk_ratio = Decimal("0.0000")
    else:
        weighted = Decimal("0")
        for target, allocation in zip(target_prices, target_allocations):
            weighted += abs(decimal_value(target) - entry) * (Decimal(allocation) / Decimal("100.0000"))
        reward_risk_ratio = quantize_4(weighted / risk_distance)
    distance_to_market = quantize_4(abs(entry - mid_price))
    return reward_risk_ratio, distance_to_market


def derive_virtual_state(*, expired, invalidation_satisfied, geometry_valid, activation_satisfied):
    """Section 12.2 exact first-match state derivation."""
    if expired:
        return "EXPIRED"
    if invalidation_satisfied:
        return "INVALIDATED"
    if not geometry_valid:
        return "REJECTED"
    if not activation_satisfied:
        return "WATCHING"
    return "ACTIVATED"


def rank_virtual_opportunities(candidates):
    """``candidates``: list of dicts with keys ``virtual_opportunity_id``,
    ``expected_reward_risk_ratio`` (Decimal), ``distance_to_market``
    (Decimal), ``state``. Returns ``{virtual_opportunity_id: rank}``, 1..N,
    covering every candidate. Section 11.3's exact ordering formula applies
    within the non-INVALIDATED/non-EXPIRED subset (ranks 1..M); the
    remaining INVALIDATED/EXPIRED candidates are appended afterward in
    ``virtual_opportunity_id`` order so every governed record still
    receives the schema-required positive-integer ``rank`` field."""
    rankable = [item for item in candidates if item["state"] not in ("INVALIDATED", "EXPIRED")]
    excluded = [item for item in candidates if item["state"] in ("INVALIDATED", "EXPIRED")]
    ordered_rankable = sorted(
        rankable,
        key=lambda item: (
            -item["expected_reward_risk_ratio"], item["distance_to_market"], item["virtual_opportunity_id"],
        ),
    )
    ordered_excluded = sorted(excluded, key=lambda item: item["virtual_opportunity_id"])
    ranks = {}
    for index, item in enumerate(ordered_rankable + ordered_excluded, start=1):
        ranks[item["virtual_opportunity_id"]] = index
    return ranks


def virtual_opportunity_id_for(fields):
    expected = ("opportunity_id", "canonical_opportunity_hash", "hypothetical_entry_trigger", "stop", "ordered_targets")
    material = _identity_material(fields, expected)
    return "vop_" + sha256_text(VIRTUAL_OPPORTUNITY_ID_DOMAIN + "\n" + material)[:32]


def canonical_virtual_opportunity_hash_for(fields_without_hash_and_state):
    expected = tuple(key for key in VIRTUAL_OPPORTUNITY_FIELDS if key not in ("canonical_virtual_opportunity_hash", "state"))
    if set(fields_without_hash_and_state) != set(expected):
        _fail(SCHEMA_FAIL, "virtual opportunity hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields_without_hash_and_state))


def build_virtual_opportunity_record(
    *, opportunity_id, canonical_opportunity_hash, proposed_side, validated_candidate, mid_price,
):
    identity_fields = {
        "opportunity_id": opportunity_id, "canonical_opportunity_hash": canonical_opportunity_hash,
        "hypothetical_entry_trigger": validated_candidate["entry_trigger"],
        "stop": validated_candidate["stop_price"], "ordered_targets": validated_candidate["target_prices"],
    }
    virtual_opportunity_id = virtual_opportunity_id_for(identity_fields)
    geometry_valid = candidate_geometry_valid(
        proposed_side, validated_candidate["entry_trigger"], validated_candidate["stop_price"],
        validated_candidate["target_prices"],
    )
    reward_risk_ratio, distance_to_market = compute_reward_risk(
        validated_candidate["entry_trigger"], validated_candidate["stop_price"],
        validated_candidate["target_prices"], validated_candidate["target_allocations"], mid_price,
    )
    risk_distance = abs(decimal_value(validated_candidate["entry_trigger"]) - decimal_value(validated_candidate["stop_price"]))
    # rank is a service-assigned projection over the WHOLE lattice (Section
    # 8 item 4 / Section 11.3) — every other field here is fully known
    # already, but rank cannot be, so it is intentionally omitted from this
    # partial record and only attached once by ``finalize_virtual_opportunity_record``
    # after every candidate in the lattice has been ranked together.
    record_without_rank_hash_state = {
        "schema_version": VIRTUAL_OPPORTUNITY_SCHEMA,
        "virtual_opportunity_id": virtual_opportunity_id,
        "opportunity_id": opportunity_id, "canonical_opportunity_hash": canonical_opportunity_hash,
        "hypothetical_entry_trigger": validated_candidate["entry_trigger"],
        "stop": validated_candidate["stop_price"], "ordered_targets": validated_candidate["target_prices"],
        "expected_reward_risk_ratio": format(reward_risk_ratio, "f"),
        "estimated_transaction_cost": canonical_decimal(risk_distance, allow_zero=True),
        "activation_condition": "Activated when the input analysis marks this candidate active.",
        "invalidation_condition": "Invalidated when the input analysis marks this candidate invalidated.",
        "expiry_utc": validated_candidate["expires_at_utc"], "non_executable": True,
    }
    return {
        "record_without_rank_hash_state": record_without_rank_hash_state,
        "geometry_valid": geometry_valid,
        "expected_reward_risk_ratio": reward_risk_ratio,
        "distance_to_market": distance_to_market,
        "activation_satisfied": validated_candidate["activation_satisfied"],
        "invalidation_satisfied": validated_candidate["invalidation_satisfied"],
        "expires_at_utc": validated_candidate["expires_at_utc"],
        "virtual_opportunity_id": virtual_opportunity_id,
    }


def finalize_virtual_opportunity_record(built, rank, state):
    record = dict(built["record_without_rank_hash_state"])
    record["rank"] = rank
    hash_fields = dict(record)
    canonical_hash = canonical_virtual_opportunity_hash_for(hash_fields)
    record["state"] = state
    record["canonical_virtual_opportunity_hash"] = canonical_hash
    return validate_virtual_opportunity_record(record)


def validate_virtual_opportunity_record(record):
    if not isinstance(record, dict) or set(record) != set(VIRTUAL_OPPORTUNITY_FIELDS):
        _fail(SCHEMA_FAIL, "virtual opportunity record has an invalid field set")
    if record["schema_version"] != VIRTUAL_OPPORTUNITY_SCHEMA:
        _fail(SCHEMA_FAIL, "virtual opportunity schema is unsupported")
    if not re.fullmatch(r"vop_[0-9a-f]{32}", record["virtual_opportunity_id"] or ""):
        _fail(SCHEMA_FAIL, "virtual_opportunity_id is invalid")
    if not re.fullmatch(r"opp_[0-9a-f]{32}", record["opportunity_id"] or ""):
        _fail(SCHEMA_FAIL, "opportunity_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_opportunity_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_opportunity_hash is invalid")
    rank = record["rank"]
    if isinstance(rank, bool) or not isinstance(rank, int) or rank < 1:
        _fail(SCHEMA_FAIL, "rank must be a positive integer")
    _price(record["hypothetical_entry_trigger"], "hypothetical_entry_trigger")
    _price(record["stop"], "stop")
    targets = record["ordered_targets"]
    if not isinstance(targets, list) or not (MIN_TARGET_COUNT <= len(targets) <= MAX_TARGET_COUNT):
        _fail(SCHEMA_FAIL, "ordered_targets must contain 2 to 4 items")
    for item in targets:
        _price(item, "ordered_targets item")
    _nonneg_price(record["expected_reward_risk_ratio"], "expected_reward_risk_ratio")
    _nonneg_price(record["estimated_transaction_cost"], "estimated_transaction_cost")
    _bounded_text(record["activation_condition"], "activation_condition", MAX_TEXT_LENGTH)
    _bounded_text(record["invalidation_condition"], "invalidation_condition", MAX_TEXT_LENGTH)
    if record["state"] not in VIRTUAL_STATES:
        _fail(SCHEMA_FAIL, "state is not governed")
    validate_utc_timestamp(record["expiry_utc"], "expiry_utc")
    if record["non_executable"] is not True:
        _fail(SCHEMA_FAIL, "non_executable must be literal true")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_virtual_opportunity_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_virtual_opportunity_hash is invalid")
    return dict(record)


# ---------------------------------------------------------------------
# Decision engine (Section 10.4) — steps 7-23; steps 1-6 are pre-flight
# admission gates (module docstring decision 1: check_instrument_and_timeframe,
# check_evidence_completeness).
# ---------------------------------------------------------------------

def strategy_gate_status(strategy_id, sma001_allowed, fib001_allowed):
    """Section 10.3's narrowly-scoped strategy-specific gate. Returns
    (passed, reason_code_if_failed). ``sma001_allowed``/``fib001_allowed``
    are the caller's independently re-checked registry results — this
    function never imports ``signal_strategy_registry`` itself, keeping
    this module free of any Phase 4 dependency."""
    if strategy_id == "SMA-001":
        return (sma001_allowed, None if sma001_allowed else "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED")
    if strategy_id == "FIB-001":
        return (fib001_allowed, None if fib001_allowed else "STRATEGY_PARAMETERS_NOT_APPROVED")
    return (True, None)


def evaluate_decision(
    *, supporting_score, contradiction_score, uncertainty_score, data_quality_score,
    estimated_cost_score, event_risk_score, risk_exposure_score,
    strategy_gate_passed, strategy_gate_reason,
    activation_satisfied, invalidation_satisfied, opportunity_expired, all_candidates_rejected,
):
    """Steps 7-23 (Section 10.4). Every one of the 16 checks is evaluated
    independently (not short-circuited) so ``reason_codes`` records every
    condition that is simultaneously true, in step order, for full
    auditability — ``final_status`` is driven only by the FIRST true
    condition, matching "the first matching rule determines final_status
    ... later-triggered conditions ... are appended for auditability"."""
    supporting = Decimal(supporting_score)
    contradiction = Decimal(contradiction_score)
    uncertainty = Decimal(uncertainty_score)
    data_quality = Decimal(data_quality_score)
    cost = Decimal(estimated_cost_score)
    event_risk = Decimal(event_risk_score)
    risk_exposure = Decimal(risk_exposure_score)

    checks = (
        (opportunity_expired, "EXPIRED", "MARKET_INTELLIGENCE_OPPORTUNITY_EXPIRED"),
        (data_quality < DATA_QUALITY_MIN, "BLOCKED", "MARKET_INTELLIGENCE_DATA_QUALITY_BELOW_MINIMUM"),
        (event_risk >= HARD_EVENT_RISK_BLOCK_MIN, "BLOCKED", "MARKET_INTELLIGENCE_HARD_EVENT_RISK_BLOCK"),
        (risk_exposure >= HARD_RISK_EXPOSURE_BLOCK_MIN, "BLOCKED", "MARKET_INTELLIGENCE_HARD_RISK_EXPOSURE_BLOCK"),
        (not strategy_gate_passed, "BLOCKED", strategy_gate_reason),
        (invalidation_satisfied, "REJECT", "MARKET_INTELLIGENCE_INVALIDATION_ALREADY_OCCURRED"),
        (all_candidates_rejected, "REJECT", "MARKET_INTELLIGENCE_STRUCTURALLY_INCONSISTENT"),
        (contradiction >= REJECT_CONTRADICTION_MIN, "REJECT", "MARKET_INTELLIGENCE_CONTRADICTION_REJECTED"),
        (cost >= REJECT_COST_MIN, "REJECT", "MARKET_INTELLIGENCE_TRANSACTION_COST_DESTROYS_EDGE"),
        (not activation_satisfied, "WAIT", "MARKET_INTELLIGENCE_TRIGGER_NOT_ACTIVE"),
        (event_risk >= WAIT_EVENT_RISK_MIN, "WAIT", "MARKET_INTELLIGENCE_EVENT_RISK_WAIT"),
        (risk_exposure >= WAIT_RISK_EXPOSURE_MIN, "WAIT", "MARKET_INTELLIGENCE_RISK_EXPOSURE_WAIT"),
        (uncertainty > TRADE_CANDIDATE_UNCERTAINTY_MAX, "WAIT", "MARKET_INTELLIGENCE_UNCERTAINTY_ABOVE_THRESHOLD"),
        (supporting < TRADE_CANDIDATE_SUPPORT_MIN, "WAIT", "MARKET_INTELLIGENCE_SUPPORT_BELOW_THRESHOLD"),
        (contradiction > TRADE_CANDIDATE_CONTRADICTION_MAX, "WAIT", "MARKET_INTELLIGENCE_CONTRADICTION_ABOVE_THRESHOLD"),
        (cost > TRADE_CANDIDATE_COST_MAX, "WAIT", "MARKET_INTELLIGENCE_TRANSACTION_COST_MARGINAL"),
    )
    reason_codes = [code for triggered, _status, code in checks if triggered]
    for triggered, status, code in checks:
        if triggered:
            return status, reason_codes
    return "TRADE_CANDIDATE", ["MARKET_INTELLIGENCE_ALL_GATES_PASSED"]


# ---------------------------------------------------------------------
# TRL_OPPORTUNITY_DECISION.v1 (Section 6.5)
# ---------------------------------------------------------------------

DECISION_FIELDS = (
    "schema_version", "decision_id", "opportunity_id", "canonical_opportunity_hash",
    "decision_input_hash", "final_status", "supporting_evidence_ids", "opposing_evidence_ids",
    "uncertainty_score", "event_risk_score", "risk_exposure_score",
    "evidence_completeness_passed", "data_sufficiency_passed", "cost_sufficiency_passed",
    "strategy_gate_passed", "reason_codes", "evaluated_at_utc", "canonical_decision_hash",
)

_DECISION_INPUT_HASH_KEYS = (
    "supporting_score", "contradiction_score", "uncertainty_score", "data_quality_score",
    "estimated_cost_score", "event_risk_score", "risk_exposure_score",
    "evidence_completeness_passed", "data_sufficiency_passed", "cost_sufficiency_passed",
    "strategy_gate_passed", "activation_satisfied", "invalidation_satisfied", "expiry_status",
)


def decision_input_hash_for(fields):
    if set(fields) != set(_DECISION_INPUT_HASH_KEYS):
        _fail(SCHEMA_FAIL, "decision input hash has an invalid field set")
    return sha256_text(deterministic_json_text(fields))


def decision_id_for(opportunity_id, canonical_opportunity_hash, decision_input_hash):
    fields = {
        "opportunity_id": opportunity_id, "canonical_opportunity_hash": canonical_opportunity_hash,
        "decision_input_hash": decision_input_hash,
    }
    material = _identity_material(fields, ("opportunity_id", "canonical_opportunity_hash", "decision_input_hash"))
    return "dec_" + sha256_text(DECISION_ID_DOMAIN + "\n" + material)[:32]


def canonical_decision_hash_for(fields_without_hash):
    expected = tuple(key for key in DECISION_FIELDS if key not in ("canonical_decision_hash", "evaluated_at_utc"))
    if set(fields_without_hash) != set(expected):
        _fail(SCHEMA_FAIL, "decision hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields_without_hash))


def build_decision_record(
    *, opportunity, strategy_gate_passed, strategy_gate_reason,
    opportunity_expired, all_candidates_rejected, evaluated_at_utc,
):
    supporting_evidence_ids, opposing_evidence_ids = None, None  # placeholder overwritten below
    scores = {key: opportunity[key] for key in _OPPORTUNITY_HASH_SCORE_KEYS}
    data_sufficiency_passed = Decimal(scores["data_quality_score"]) >= DATA_QUALITY_MIN
    cost_sufficiency_passed = Decimal(scores["estimated_cost_score"]) < TRADE_CANDIDATE_COST_MAX
    expiry_status = "EXPIRED" if opportunity_expired else "NOT_EXPIRED"
    final_status, reason_codes = evaluate_decision(
        supporting_score=scores["supporting_score"], contradiction_score=scores["contradiction_score"],
        uncertainty_score=scores["uncertainty_score"], data_quality_score=scores["data_quality_score"],
        estimated_cost_score=scores["estimated_cost_score"], event_risk_score=scores["event_risk_score"],
        risk_exposure_score=scores["risk_exposure_score"], strategy_gate_passed=strategy_gate_passed,
        strategy_gate_reason=strategy_gate_reason, activation_satisfied=opportunity["activation_satisfied"],
        invalidation_satisfied=opportunity["invalidation_satisfied"], opportunity_expired=opportunity_expired,
        all_candidates_rejected=all_candidates_rejected,
    )
    input_hash_fields = dict(scores)
    input_hash_fields.update({
        "evidence_completeness_passed": True, "data_sufficiency_passed": data_sufficiency_passed,
        "cost_sufficiency_passed": cost_sufficiency_passed, "strategy_gate_passed": strategy_gate_passed,
        "activation_satisfied": opportunity["activation_satisfied"],
        "invalidation_satisfied": opportunity["invalidation_satisfied"], "expiry_status": expiry_status,
    })
    decision_input_hash = decision_input_hash_for(input_hash_fields)
    decision_id = decision_id_for(opportunity["opportunity_id"], opportunity["canonical_opportunity_hash"], decision_input_hash)
    del supporting_evidence_ids, opposing_evidence_ids
    return {
        "decision_id": decision_id, "decision_input_hash": decision_input_hash,
        "final_status": final_status, "reason_codes": reason_codes,
        "evidence_completeness_passed": True, "data_sufficiency_passed": data_sufficiency_passed,
        "cost_sufficiency_passed": cost_sufficiency_passed, "strategy_gate_passed": strategy_gate_passed,
        "evaluated_at_utc": evaluated_at_utc,
    }


def finalize_decision_record(opportunity, decision_parts, supporting_evidence_ids, opposing_evidence_ids):
    record_without_hash = {
        "schema_version": DECISION_SCHEMA, "decision_id": decision_parts["decision_id"],
        "opportunity_id": opportunity["opportunity_id"],
        "canonical_opportunity_hash": opportunity["canonical_opportunity_hash"],
        "decision_input_hash": decision_parts["decision_input_hash"],
        "final_status": decision_parts["final_status"],
        "supporting_evidence_ids": supporting_evidence_ids, "opposing_evidence_ids": opposing_evidence_ids,
        "uncertainty_score": opportunity["uncertainty_score"], "event_risk_score": opportunity["event_risk_score"],
        "risk_exposure_score": opportunity["risk_exposure_score"],
        "evidence_completeness_passed": decision_parts["evidence_completeness_passed"],
        "data_sufficiency_passed": decision_parts["data_sufficiency_passed"],
        "cost_sufficiency_passed": decision_parts["cost_sufficiency_passed"],
        "strategy_gate_passed": decision_parts["strategy_gate_passed"],
        "reason_codes": decision_parts["reason_codes"],
    }
    canonical_hash = canonical_decision_hash_for(record_without_hash)
    record = dict(record_without_hash)
    record["evaluated_at_utc"] = decision_parts["evaluated_at_utc"]
    record["canonical_decision_hash"] = canonical_hash
    return validate_decision_record(record)


def validate_decision_record(record):
    if not isinstance(record, dict) or set(record) != set(DECISION_FIELDS):
        _fail(SCHEMA_FAIL, "decision record has an invalid field set")
    if record["schema_version"] != DECISION_SCHEMA:
        _fail(SCHEMA_FAIL, "decision schema is unsupported")
    if not re.fullmatch(r"dec_[0-9a-f]{32}", record["decision_id"] or ""):
        _fail(SCHEMA_FAIL, "decision_id is invalid")
    if not re.fullmatch(r"opp_[0-9a-f]{32}", record["opportunity_id"] or ""):
        _fail(SCHEMA_FAIL, "opportunity_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_opportunity_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_opportunity_hash is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["decision_input_hash"] or ""):
        _fail(SCHEMA_FAIL, "decision_input_hash is invalid")
    if record["final_status"] not in DECISION_STATUSES:
        _fail(SCHEMA_FAIL, "final_status is not governed")
    for key in ("supporting_evidence_ids", "opposing_evidence_ids"):
        items = record[key]
        if not isinstance(items, list) or len(items) > len(DIRECTIONAL_EVIDENCE_CATEGORIES):
            _fail(SCHEMA_FAIL, "{} must be a bounded list".format(key))
        for evidence_id in items:
            if not re.fullmatch(r"evd_[0-9a-f]{32}", evidence_id or ""):
                _fail(SCHEMA_FAIL, "{} contains an invalid entry".format(key))
    for key in ("uncertainty_score", "event_risk_score", "risk_exposure_score"):
        _score_field(record[key], key)
    for key in ("evidence_completeness_passed", "data_sufficiency_passed", "cost_sufficiency_passed", "strategy_gate_passed"):
        _bool(record[key], key)
    reason_codes = record["reason_codes"]
    if not isinstance(reason_codes, list) or not reason_codes or len(reason_codes) > 24:
        _fail(SCHEMA_FAIL, "reason_codes must be a non-empty bounded list")
    for code in reason_codes:
        if code not in REASON_CODES:
            _fail(SCHEMA_FAIL, "reason_codes contains an ungoverned code")
    validate_utc_timestamp(record["evaluated_at_utc"], "evaluated_at_utc")
    expected_hash = canonical_decision_hash_for(
        {key: value for key, value in record.items() if key not in ("canonical_decision_hash", "evaluated_at_utc")}
    )
    if record["canonical_decision_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_decision_hash does not match canonical content")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_MARKET_INTELLIGENCE_BASKET_PREVIEW.v1 (Section 6.7, 13)
# ---------------------------------------------------------------------

PREVIEW_FIELDS = (
    "schema_version", "preview_id", "opportunity_id", "canonical_opportunity_hash",
    "selected_virtual_opportunity_id", "canonical_virtual_opportunity_hash",
    "instrument", "proposed_side", "entry_trigger", "stop_price",
    "ordered_target_prices", "ordered_target_allocations", "hypothetical_total_quantity",
    "ordered_hypothetical_child_quantities", "total_hypothetical_risk", "non_executable",
    "execution_handoff_status", "created_at_utc", "expires_at_utc", "canonical_preview_hash",
)


def compute_preview_quantities(total_quantity, allocations):
    """Section 13.2's exact fail-closed, no-redistribution quantity
    conservation. ``total_quantity``: ``Decimal`` or ``None``.
    ``allocations``: list of canonical four-decimal allocation strings
    already validated to sum to exactly 100.0000. Returns a list of
    canonical (up to 8 dp) quantity strings, or ``None``."""
    if total_quantity is None:
        return None
    with localcontext() as ctx:
        ctx.prec = 60
        eight_dp = Decimal("0.00000001")
        quantities = []
        running_total = Decimal("0")
        for allocation in allocations:
            raw = total_quantity * Decimal(allocation) / Decimal("100.0000")
            quantized = raw.quantize(eight_dp)
            if quantized != raw:
                _fail("MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE")
            if quantized <= 0:
                _fail("MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE")
            quantities.append(quantized)
            running_total += quantized
        if running_total != total_quantity:
            _fail("MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE")
    return [canonical_decimal(item) for item in quantities]


def compute_total_hypothetical_risk(entry_trigger, stop_price, hypothetical_total_quantity):
    """Research-only formula (Section 13.1): per-unit price risk, scaled by
    the hypothetical total quantity when one is supplied."""
    risk_per_unit = abs(decimal_value(entry_trigger) - decimal_value(stop_price))
    if hypothetical_total_quantity is None:
        return canonical_decimal(risk_per_unit, allow_zero=True)
    return canonical_decimal(risk_per_unit * decimal_value(hypothetical_total_quantity), allow_zero=True)


def preview_id_for(opportunity_id, canonical_opportunity_hash, selected_virtual_opportunity_id, canonical_virtual_opportunity_hash):
    fields = {
        "opportunity_id": opportunity_id, "canonical_opportunity_hash": canonical_opportunity_hash,
        "selected_virtual_opportunity_id": selected_virtual_opportunity_id,
        "canonical_virtual_opportunity_hash": canonical_virtual_opportunity_hash,
    }
    material = _identity_material(fields, tuple(fields))
    return "prv_" + sha256_text(PREVIEW_ID_DOMAIN + "\n" + material)[:32]


def canonical_preview_hash_for(fields_without_hash):
    expected = tuple(key for key in PREVIEW_FIELDS if key not in ("canonical_preview_hash", "created_at_utc"))
    if set(fields_without_hash) != set(expected):
        _fail(SCHEMA_FAIL, "preview hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields_without_hash))


def build_preview_record(*, opportunity, selected_virtual_opportunity, candidate_input, created_at_utc):
    preview_id = preview_id_for(
        opportunity["opportunity_id"], opportunity["canonical_opportunity_hash"],
        selected_virtual_opportunity["virtual_opportunity_id"],
        selected_virtual_opportunity["canonical_virtual_opportunity_hash"],
    )
    total_quantity_decimal = (
        decimal_value(candidate_input["hypothetical_total_quantity"])
        if candidate_input["hypothetical_total_quantity"] is not None else None
    )
    quantities = compute_preview_quantities(total_quantity_decimal, candidate_input["target_allocations"])
    total_risk = compute_total_hypothetical_risk(
        selected_virtual_opportunity["hypothetical_entry_trigger"], selected_virtual_opportunity["stop"],
        candidate_input["hypothetical_total_quantity"],
    )
    record_without_hash = {
        "schema_version": PREVIEW_SCHEMA, "preview_id": preview_id,
        "opportunity_id": opportunity["opportunity_id"],
        "canonical_opportunity_hash": opportunity["canonical_opportunity_hash"],
        "selected_virtual_opportunity_id": selected_virtual_opportunity["virtual_opportunity_id"],
        "canonical_virtual_opportunity_hash": selected_virtual_opportunity["canonical_virtual_opportunity_hash"],
        "instrument": opportunity["instrument"], "proposed_side": opportunity["proposed_side"],
        "entry_trigger": selected_virtual_opportunity["hypothetical_entry_trigger"],
        "stop_price": selected_virtual_opportunity["stop"],
        "ordered_target_prices": selected_virtual_opportunity["ordered_targets"],
        "ordered_target_allocations": candidate_input["target_allocations"],
        "hypothetical_total_quantity": (
            canonical_decimal(candidate_input["hypothetical_total_quantity"])
            if candidate_input["hypothetical_total_quantity"] is not None else None
        ),
        "ordered_hypothetical_child_quantities": quantities,
        "total_hypothetical_risk": total_risk, "non_executable": True,
        "execution_handoff_status": EXECUTION_HANDOFF_STATUS,
        "expires_at_utc": selected_virtual_opportunity["expiry_utc"],
    }
    canonical_hash = canonical_preview_hash_for(record_without_hash)
    record = dict(record_without_hash)
    record["created_at_utc"] = created_at_utc
    record["canonical_preview_hash"] = canonical_hash
    return validate_preview_record(record)


def validate_preview_record(record):
    if not isinstance(record, dict) or set(record) != set(PREVIEW_FIELDS):
        _fail(SCHEMA_FAIL, "preview record has an invalid field set")
    if record["schema_version"] != PREVIEW_SCHEMA:
        _fail(SCHEMA_FAIL, "preview schema is unsupported")
    if not re.fullmatch(r"prv_[0-9a-f]{32}", record["preview_id"] or ""):
        _fail(SCHEMA_FAIL, "preview_id is invalid")
    if not re.fullmatch(r"opp_[0-9a-f]{32}", record["opportunity_id"] or ""):
        _fail(SCHEMA_FAIL, "opportunity_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_opportunity_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_opportunity_hash is invalid")
    if not re.fullmatch(r"vop_[0-9a-f]{32}", record["selected_virtual_opportunity_id"] or ""):
        _fail(SCHEMA_FAIL, "selected_virtual_opportunity_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_virtual_opportunity_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_virtual_opportunity_hash is invalid")
    _bounded_text(record["instrument"], "instrument", 16)
    if record["proposed_side"] not in SIDES:
        _fail(SCHEMA_FAIL, "proposed_side is not governed")
    _price(record["entry_trigger"], "entry_trigger")
    _price(record["stop_price"], "stop_price")
    targets = record["ordered_target_prices"]
    if not isinstance(targets, list) or not (MIN_TARGET_COUNT <= len(targets) <= MAX_TARGET_COUNT):
        _fail(SCHEMA_FAIL, "ordered_target_prices must contain 2 to 4 items")
    for item in targets:
        _price(item, "ordered_target_prices item")
    allocations = record["ordered_target_allocations"]
    if not isinstance(allocations, list) or len(allocations) != len(targets):
        _fail(SCHEMA_FAIL, "ordered_target_allocations must align with ordered_target_prices")
    allocation_sum = Decimal("0")
    for item in allocations:
        value = _allocation_decimal(item, "ordered_target_allocations item")
        allocation_sum += value
    if allocation_sum != Decimal("100.0000"):
        _fail(SCHEMA_FAIL, "ordered_target_allocations must sum to exactly 100.0000")
    total_quantity = record["hypothetical_total_quantity"]
    child_quantities = record["ordered_hypothetical_child_quantities"]
    if total_quantity is None:
        if child_quantities is not None:
            _fail(SCHEMA_FAIL, "ordered_hypothetical_child_quantities must be null when hypothetical_total_quantity is null")
    else:
        _price(total_quantity, "hypothetical_total_quantity")
        if not isinstance(child_quantities, list) or len(child_quantities) != len(targets):
            _fail(SCHEMA_FAIL, "ordered_hypothetical_child_quantities must align with ordered_target_prices")
        quantity_sum = Decimal("0")
        for item in child_quantities:
            quantity_sum += decimal_value(_price(item, "ordered_hypothetical_child_quantities item"))
        if quantity_sum != decimal_value(total_quantity):
            _fail("MARKET_INTELLIGENCE_PREVIEW_QUANTITY_NOT_EXACTLY_REPRESENTABLE")
    _nonneg_price(record["total_hypothetical_risk"], "total_hypothetical_risk")
    if record["non_executable"] is not True:
        _fail(SCHEMA_FAIL, "non_executable must be literal true")
    if record["execution_handoff_status"] != EXECUTION_HANDOFF_STATUS:
        _fail(SCHEMA_FAIL, "execution_handoff_status must be EXECUTION_HANDOFF_NOT_APPROVED")
    validate_utc_timestamp(record["created_at_utc"], "created_at_utc")
    expires_dt = validate_utc_timestamp(record["expires_at_utc"], "expires_at_utc")
    created_dt = validate_utc_timestamp(record["created_at_utc"])
    if expires_dt <= created_dt:
        _fail(SCHEMA_FAIL, "expires_at_utc must be strictly after created_at_utc")
    expected_hash = canonical_preview_hash_for(
        {key: value for key, value in record.items() if key not in ("canonical_preview_hash", "created_at_utc")}
    )
    if record["canonical_preview_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_preview_hash does not match canonical content")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_LEARNING_TELEMETRY.v1 (Section 6.6, 14)
# ---------------------------------------------------------------------

TELEMETRY_INPUT_FIELDS = (
    "observation_window_start_utc", "observation_window_end_utc",
    "predicted_entry", "predicted_stop", "predicted_targets",
    "realized_movement", "maximum_favorable_excursion", "maximum_adverse_excursion",
    "theoretical_result_after_costs", "calibration_bucket", "outcome_classification",
    "missing_data_status",
)

TELEMETRY_FIELDS = (
    "schema_version", "telemetry_id", "opportunity_id", "canonical_opportunity_hash",
    "decision_id", "observation_window_start_utc", "observation_window_end_utc",
    "predicted_direction", "predicted_entry", "predicted_stop", "predicted_targets",
    "realized_movement", "maximum_favorable_excursion", "maximum_adverse_excursion",
    "theoretical_result_after_costs", "original_decision_status", "calibration_bucket",
    "outcome_classification", "missing_data_status", "regime_at_recording",
    "recorded_at_utc", "canonical_telemetry_hash",
)


def _signed_price(value, field):
    try:
        return canonical_decimal(value, field, positive=False)
    except TimelineValidationError as error:
        _fail(SCHEMA_FAIL, str(error))


def validate_telemetry_input(value):
    if not isinstance(value, dict) or set(value) != set(TELEMETRY_INPUT_FIELDS):
        _fail(SCHEMA_FAIL, "telemetry input has an invalid field set")
    start_dt = validate_utc_timestamp(value["observation_window_start_utc"], "observation_window_start_utc")
    end_dt = validate_utc_timestamp(value["observation_window_end_utc"], "observation_window_end_utc")
    if end_dt <= start_dt:
        _fail(SCHEMA_FAIL, "observation_window_end_utc must be strictly after observation_window_start_utc")
    predicted_entry = _price(value["predicted_entry"], "predicted_entry")
    predicted_stop = _price(value["predicted_stop"], "predicted_stop")
    targets = value["predicted_targets"]
    if not isinstance(targets, list) or not (MIN_TARGET_COUNT <= len(targets) <= MAX_TARGET_COUNT):
        _fail(SCHEMA_FAIL, "predicted_targets must contain 2 to 4 items")
    clean_targets = [_price(item, "predicted_targets item") for item in targets]
    realized_movement = _signed_price(value["realized_movement"], "realized_movement")
    mfe = _nonneg_price(value["maximum_favorable_excursion"], "maximum_favorable_excursion")
    mae = _nonneg_price(value["maximum_adverse_excursion"], "maximum_adverse_excursion")
    theoretical_result = _signed_price(value["theoretical_result_after_costs"], "theoretical_result_after_costs")
    calibration_bucket = value["calibration_bucket"]
    if calibration_bucket not in CALIBRATION_BUCKETS:
        _fail(SCHEMA_FAIL, "calibration_bucket is not governed")
    outcome_classification = value["outcome_classification"]
    if outcome_classification not in OUTCOME_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "outcome_classification is not governed")
    missing_data_status = value["missing_data_status"]
    if missing_data_status not in MISSING_DATA_STATUSES:
        _fail(SCHEMA_FAIL, "missing_data_status is not governed")
    return {
        "observation_window_start_utc": value["observation_window_start_utc"],
        "observation_window_end_utc": value["observation_window_end_utc"],
        "predicted_entry": predicted_entry, "predicted_stop": predicted_stop,
        "predicted_targets": clean_targets, "realized_movement": realized_movement,
        "maximum_favorable_excursion": mfe, "maximum_adverse_excursion": mae,
        "theoretical_result_after_costs": theoretical_result,
        "calibration_bucket": calibration_bucket, "outcome_classification": outcome_classification,
        "missing_data_status": missing_data_status,
    }


def telemetry_id_for(fields):
    expected = (
        "opportunity_id", "canonical_opportunity_hash", "decision_id",
        "observation_window_start_utc", "observation_window_end_utc",
    )
    material = _identity_material(fields, expected)
    return "tel_" + sha256_text(TELEMETRY_ID_DOMAIN + "\n" + material)[:32]


def canonical_telemetry_hash_for(fields_without_hash):
    expected = tuple(key for key in TELEMETRY_FIELDS if key not in ("canonical_telemetry_hash", "recorded_at_utc"))
    if set(fields_without_hash) != set(expected):
        _fail(SCHEMA_FAIL, "telemetry hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields_without_hash))


def build_telemetry_record(*, opportunity, decision_id, original_decision_status, validated_input, recorded_at_utc):
    if original_decision_status not in TELEMETRY_ORIGINAL_STATUSES:
        _fail(SCHEMA_FAIL, "original_decision_status must be TRADE_CANDIDATE/WAIT/REJECT/BLOCKED")
    identity_fields = {
        "opportunity_id": opportunity["opportunity_id"],
        "canonical_opportunity_hash": opportunity["canonical_opportunity_hash"],
        "decision_id": decision_id,
        "observation_window_start_utc": validated_input["observation_window_start_utc"],
        "observation_window_end_utc": validated_input["observation_window_end_utc"],
    }
    telemetry_id = telemetry_id_for(identity_fields)
    record_without_hash = {
        "schema_version": TELEMETRY_SCHEMA, "telemetry_id": telemetry_id,
        "opportunity_id": opportunity["opportunity_id"],
        "canonical_opportunity_hash": opportunity["canonical_opportunity_hash"],
        "decision_id": decision_id,
        "observation_window_start_utc": validated_input["observation_window_start_utc"],
        "observation_window_end_utc": validated_input["observation_window_end_utc"],
        "predicted_direction": opportunity["proposed_side"],
        "predicted_entry": validated_input["predicted_entry"],
        "predicted_stop": validated_input["predicted_stop"],
        "predicted_targets": validated_input["predicted_targets"],
        "realized_movement": validated_input["realized_movement"],
        "maximum_favorable_excursion": validated_input["maximum_favorable_excursion"],
        "maximum_adverse_excursion": validated_input["maximum_adverse_excursion"],
        "theoretical_result_after_costs": validated_input["theoretical_result_after_costs"],
        "original_decision_status": original_decision_status,
        "calibration_bucket": validated_input["calibration_bucket"],
        "outcome_classification": validated_input["outcome_classification"],
        "missing_data_status": validated_input["missing_data_status"],
        "regime_at_recording": opportunity["market_regime"],
    }
    canonical_hash = canonical_telemetry_hash_for(record_without_hash)
    record = dict(record_without_hash)
    record["recorded_at_utc"] = recorded_at_utc
    record["canonical_telemetry_hash"] = canonical_hash
    return validate_telemetry_record(record)


def validate_telemetry_record(record):
    if not isinstance(record, dict) or set(record) != set(TELEMETRY_FIELDS):
        _fail(SCHEMA_FAIL, "telemetry record has an invalid field set")
    if record["schema_version"] != TELEMETRY_SCHEMA:
        _fail(SCHEMA_FAIL, "telemetry schema is unsupported")
    if not re.fullmatch(r"tel_[0-9a-f]{32}", record["telemetry_id"] or ""):
        _fail(SCHEMA_FAIL, "telemetry_id is invalid")
    if not re.fullmatch(r"opp_[0-9a-f]{32}", record["opportunity_id"] or ""):
        _fail(SCHEMA_FAIL, "opportunity_id is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", record["canonical_opportunity_hash"] or ""):
        _fail(SCHEMA_FAIL, "canonical_opportunity_hash is invalid")
    if not re.fullmatch(r"dec_[0-9a-f]{32}", record["decision_id"] or ""):
        _fail(SCHEMA_FAIL, "decision_id is invalid")
    start_dt = validate_utc_timestamp(record["observation_window_start_utc"], "observation_window_start_utc")
    end_dt = validate_utc_timestamp(record["observation_window_end_utc"], "observation_window_end_utc")
    if end_dt <= start_dt:
        _fail(SCHEMA_FAIL, "observation_window_end_utc must be strictly after observation_window_start_utc")
    if record["predicted_direction"] not in SIDES:
        _fail(SCHEMA_FAIL, "predicted_direction is not governed")
    _price(record["predicted_entry"], "predicted_entry")
    _price(record["predicted_stop"], "predicted_stop")
    targets = record["predicted_targets"]
    if not isinstance(targets, list) or not (MIN_TARGET_COUNT <= len(targets) <= MAX_TARGET_COUNT):
        _fail(SCHEMA_FAIL, "predicted_targets must contain 2 to 4 items")
    for item in targets:
        _price(item, "predicted_targets item")
    _signed_price(record["realized_movement"], "realized_movement")
    _nonneg_price(record["maximum_favorable_excursion"], "maximum_favorable_excursion")
    _nonneg_price(record["maximum_adverse_excursion"], "maximum_adverse_excursion")
    _signed_price(record["theoretical_result_after_costs"], "theoretical_result_after_costs")
    if record["original_decision_status"] not in TELEMETRY_ORIGINAL_STATUSES:
        _fail(SCHEMA_FAIL, "original_decision_status must be TRADE_CANDIDATE/WAIT/REJECT/BLOCKED")
    if record["calibration_bucket"] not in CALIBRATION_BUCKETS:
        _fail(SCHEMA_FAIL, "calibration_bucket is not governed")
    if record["outcome_classification"] not in OUTCOME_CLASSIFICATIONS:
        _fail(SCHEMA_FAIL, "outcome_classification is not governed")
    if record["missing_data_status"] not in MISSING_DATA_STATUSES:
        _fail(SCHEMA_FAIL, "missing_data_status is not governed")
    if record["regime_at_recording"] not in MARKET_REGIMES:
        _fail(SCHEMA_FAIL, "regime_at_recording is not governed")
    validate_utc_timestamp(record["recorded_at_utc"], "recorded_at_utc")
    expected_hash = canonical_telemetry_hash_for(
        {key: value for key, value in record.items() if key not in ("canonical_telemetry_hash", "recorded_at_utc")}
    )
    if record["canonical_telemetry_hash"] != expected_hash:
        _fail(SCHEMA_FAIL, "canonical_telemetry_hash does not match canonical content")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1 (Section 7) — transport-only
# ---------------------------------------------------------------------

DEFAULT_STRATEGY_ID = "CORTEX-V0-HEURISTIC"
DEFAULT_STRATEGY_VERSION = "1.0.0"

_ENVELOPE_REQUIRED_FIELDS = (
    "schema_version", "snapshot", "proposed_side", "evidence_inputs",
    "virtual_candidate_inputs", "activation_satisfied", "invalidation_satisfied",
) + OPPORTUNITY_CONCEPT_INPUT_FIELDS
_ENVELOPE_OPTIONAL_FIELDS = ("strategy_id", "strategy_version")
_ENVELOPE_ALL_FIELDS = frozenset(_ENVELOPE_REQUIRED_FIELDS) | frozenset(_ENVELOPE_OPTIONAL_FIELDS)


def validate_analysis_input(value):
    """Structural (step-1-domain) validation of the whole transport
    envelope. Returns a clean dict of already-validated sub-structures;
    does NOT perform the pre-flight instrument/timeframe/evidence-
    completeness admission checks (module docstring decision 1) — callers
    run ``check_instrument_and_timeframe``/``check_evidence_completeness``
    afterward."""
    if not isinstance(value, dict):
        _fail(SCHEMA_FAIL, "analysis input must be a JSON object")
    present = set(value)
    if not set(_ENVELOPE_REQUIRED_FIELDS).issubset(present):
        _fail(SCHEMA_FAIL, "analysis input is missing a required field")
    if not present.issubset(_ENVELOPE_ALL_FIELDS):
        _fail(SCHEMA_FAIL, "analysis input contains an unknown field")
    if value["schema_version"] != ANALYSIS_INPUT_SCHEMA:
        _fail(SCHEMA_FAIL, "analysis input schema is unsupported")
    snapshot = validate_snapshot_input(value["snapshot"])
    proposed_side = value["proposed_side"]
    if proposed_side not in SIDES:
        _fail(SCHEMA_FAIL, "proposed_side is not governed")
    strategy_id = value.get("strategy_id", DEFAULT_STRATEGY_ID)
    strategy_id = _bounded_text(strategy_id, "strategy_id", MAX_TEXT_LENGTH)
    strategy_version = value.get("strategy_version", DEFAULT_STRATEGY_VERSION)
    strategy_version = _bounded_text(strategy_version, "strategy_version", MAX_TEXT_LENGTH)
    concept_input = validate_opportunity_concept_input(
        {key: value[key] for key in OPPORTUNITY_CONCEPT_INPUT_FIELDS}
    )
    evidence_inputs_raw = value["evidence_inputs"]
    if not isinstance(evidence_inputs_raw, list) or len(evidence_inputs_raw) != len(EVIDENCE_CATEGORIES):
        _fail(SCHEMA_FAIL, "evidence_inputs must contain exactly eleven items")
    evidence_inputs = [validate_evidence_input(item) for item in evidence_inputs_raw]
    candidate_inputs_raw = value["virtual_candidate_inputs"]
    if not isinstance(candidate_inputs_raw, list) or not (LATTICE_MIN_SIZE <= len(candidate_inputs_raw) <= LATTICE_MAX_SIZE):
        _fail(SCHEMA_FAIL, "virtual_candidate_inputs must contain 1 to 6 items")
    candidate_inputs = [validate_virtual_candidate_input(item) for item in candidate_inputs_raw]
    activation_satisfied = _bool(value["activation_satisfied"], "activation_satisfied")
    invalidation_satisfied = _bool(value["invalidation_satisfied"], "invalidation_satisfied")
    return {
        "snapshot": snapshot, "proposed_side": proposed_side, "strategy_id": strategy_id,
        "strategy_version": strategy_version, "concept_input": concept_input,
        "evidence_inputs": evidence_inputs, "candidate_inputs": candidate_inputs,
        "activation_satisfied": activation_satisfied, "invalidation_satisfied": invalidation_satisfied,
    }


__all__ = (
    "ANALYSIS_INPUT_SCHEMA",
    "CALIBRATION_BUCKETS",
    "DATA_QUALITY_MIN",
    "DATA_QUALITY_STATUSES",
    "DATA_SOURCE_CLASSIFICATIONS",
    "DECISION_SCHEMA",
    "DECISION_STATUSES",
    "DIRECTIONAL_EVIDENCE_CATEGORIES",
    "EVENT_RISK_CLASSIFICATIONS",
    "EVIDENCE_CATEGORIES",
    "EVIDENCE_DIRECTIONS",
    "EVIDENCE_SCHEMA",
    "EVIDENCE_SOURCE_CLASSIFICATIONS",
    "EXECUTION_HANDOFF_STATUS",
    "HARD_EVENT_RISK_BLOCK_MIN",
    "HARD_RISK_EXPOSURE_BLOCK_MIN",
    "INSTRUMENTS",
    "LATTICE_MAX_SIZE",
    "LATTICE_MIN_SIZE",
    "MARKET_REGIMES",
    "MAX_SELECTED_FOR_PREVIEW",
    "MAX_TARGET_COUNT",
    "MIN_TARGET_COUNT",
    "MISSING_DATA_STATUSES",
    "OPPORTUNITY_SCHEMA",
    "OUTCOME_CLASSIFICATIONS",
    "PREVIEW_SCHEMA",
    "REASON_CODES",
    "REJECT_CONTRADICTION_MIN",
    "REJECT_COST_MIN",
    "SCHEMA_FAIL",
    "SESSIONS",
    "SIDES",
    "SNAPSHOT_SCHEMA",
    "TELEMETRY_ORIGINAL_STATUSES",
    "TELEMETRY_SCHEMA",
    "TIMEFRAMES",
    "TRADE_CANDIDATE_CONTRADICTION_MAX",
    "TRADE_CANDIDATE_COST_MAX",
    "TRADE_CANDIDATE_SUPPORT_MIN",
    "TRADE_CANDIDATE_UNCERTAINTY_MAX",
    "VIRTUAL_OPPORTUNITY_SCHEMA",
    "VIRTUAL_STATES",
    "WAIT_EVENT_RISK_MIN",
    "WAIT_RISK_EXPOSURE_MIN",
    "MarketIntelligenceValidationError",
    "quantize_4",
    "score_text",
    "ANALYSIS_INPUT_SCHEMA",
    "DEFAULT_STRATEGY_ID",
    "DEFAULT_STRATEGY_VERSION",
    "validate_analysis_input",
    "validate_snapshot_input",
    "check_instrument_and_timeframe",
    "build_snapshot_record",
    "validate_snapshot_record",
    "snapshot_mid_price",
    "validate_evidence_input",
    "check_evidence_completeness",
    "build_evidence_record",
    "validate_evidence_record",
    "effective_evidence_score",
    "compute_scores",
    "partition_evidence_by_direction",
    "validate_opportunity_concept_input",
    "build_opportunity_record",
    "validate_opportunity_record",
    "validate_virtual_candidate_input",
    "candidate_geometry_valid",
    "compute_reward_risk",
    "derive_virtual_state",
    "rank_virtual_opportunities",
    "build_virtual_opportunity_record",
    "finalize_virtual_opportunity_record",
    "validate_virtual_opportunity_record",
    "strategy_gate_status",
    "evaluate_decision",
    "build_decision_record",
    "finalize_decision_record",
    "validate_decision_record",
    "compute_preview_quantities",
    "compute_total_hypothetical_risk",
    "build_preview_record",
    "validate_preview_record",
    "validate_telemetry_input",
    "build_telemetry_record",
    "validate_telemetry_record",
)
