"""Governed data contracts for the TRL-R2-007 MT5 execution adapter (Phase 5).

Phase 5 scope only: the ``MT5_DEMO_MANUAL`` single-order, non-basket,
non-automated slice of TRL_R2_007_MT5_EXECUTION_CONTRACT.md. Basket
children, live modes, arming tokens and automatic reconciliation are
out of scope for this checkpoint (see TRL_FULL_VISION_MASTER_PROGRAM.md
Phase 6/9/10) and are deliberately absent from every schema below.

No field here is ever populated by a generative/LLM component and no
value here is trusted from a proposal without independent
re-validation (Section "EXECUTION INPUT CONTRACT" of the Phase 5
kickoff). This module is pure data/validation: no I/O, no MetaTrader5
import, no adapter, no journal.
"""

from decimal import Decimal
import re

from .timeline_data import (
    TimelineValidationError,
    canonical_decimal,
    decimal_value,
    deterministic_json_text,
    sha256_text,
    validate_instrument,
    validate_utc_timestamp,
)


ORDER_INTENT_SCHEMA = "TRL_MT5_ORDER_INTENT.v1"
CONFIRMATION_SCHEMA = "TRL_MT5_MANUAL_CONFIRMATION.v1"
CHECK_RESULT_SCHEMA = "TRL_MT5_ORDER_CHECK_RESULT.v1"
SEND_RESULT_SCHEMA = "TRL_MT5_ORDER_SEND_RESULT.v1"

# The single operating mode Phase 5 admits. Live modes and automated modes
# are never reachable from this module.
PHASE5_OPERATING_MODE = "MT5_DEMO_MANUAL"

SIDES = ("BUY", "SELL")
# The one narrow, unambiguous order-type mapping Phase 5 supports (see
# module docstring in mt5_execution_service.py "_resolve_entry_order" for
# the full rationale). Any proposal whose entry zone is a genuine range, or
# whose exact collapsed price has already been crossed by the market, fails
# closed rather than inventing a broader mapping.
ORDER_TYPES = ("BUY_LIMIT", "SELL_LIMIT")
TIME_IN_FORCE_VALUES = ("GTC",)
FILL_POLICIES = ("FOK", "IOC", "RETURN")

INTENT_STATES = (
    "CREATED",
    "CHECK_PASSED",
    "AWAITING_CONFIRMATION",
    "FILLED",
    "PARTIALLY_FILLED",
    "REJECTED",
    "CANCELLED",
    "FROZEN_PENDING_RECONCILIATION",
)
TERMINAL_INTENT_STATES = (
    "FILLED", "PARTIALLY_FILLED", "REJECTED", "CANCELLED",
    "FROZEN_PENDING_RECONCILIATION",
)

CHECK_OUTCOMES = ("PASSED", "FAILED", "MALFORMED")
SEND_OUTCOMES = ("FILLED", "PARTIALLY_FILLED", "REJECTED", "UNCERTAIN", "MALFORMED")

# The closed reason-code vocabulary for every fail-closed outcome this
# adapter can produce. Every rejection anywhere in Phase 5 uses exactly one
# of these; nothing free-text ever substitutes for a reason code.
EXECUTION_REASON_CODES = (
    "PROPOSAL_SCHEMA_INVALID",
    "PROPOSAL_HASH_MISMATCH",
    "PROPOSAL_NOT_EXECUTABLE_SIDE",
    "PROPOSAL_BLOCKED",
    "PROPOSAL_HOLD",
    "PROPOSAL_WAIT",
    "PROPOSAL_EXPIRED",
    "STRATEGY_NOT_REGISTERED",
    "STRATEGY_DISABLED",
    "STRATEGY_PARAMETERS_NOT_APPROVED",
    "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED",
    "STRATEGY_VERSION_MISMATCH",
    "RISK_POLICY_HASH_MISMATCH",
    "ROLE_QUANTITY_MISMATCH",
    "ENTRY_ZONE_RANGE_MAPPING_NOT_APPROVED",
    "ENTRY_PRICE_ALREADY_CROSSED_MAPPING_NOT_APPROVED",
    "OPERATING_MODE_NOT_MT5_DEMO_MANUAL",
    "CAPABILITY_DENIED",
    "INSTRUMENT_NOT_ALLOWLISTED",
    "MT5_DEPENDENCY_MISSING",
    "TERMINAL_UNAVAILABLE",
    "TERMINAL_PATH_MISMATCH",
    "TERMINAL_TRADE_NOT_ALLOWED",
    "ACCOUNT_UNAVAILABLE",
    "ACCOUNT_FINGERPRINT_MISMATCH",
    "ACCOUNT_MODE_MISMATCH",
    "ACCOUNT_TRADE_NOT_ALLOWED",
    "SYMBOL_UNAVAILABLE",
    "SYMBOL_NOT_TRADEABLE",
    "SYMBOL_MAPPING_MISMATCH",
    "SYMBOL_METADATA_STALE",
    "TICK_UNAVAILABLE",
    "TICK_STALE",
    "INVALID_BID_ASK",
    "SPREAD_EXCEEDS_LIMIT",
    "INVALID_QUANTITY",
    "QUANTITY_STEP_MISMATCH",
    "INVALID_STOP",
    "STOP_LEVEL_VIOLATION",
    "FREEZE_LEVEL_VIOLATION",
    "MARKET_SESSION_CLOSED",
    "FILLING_MODE_UNAVAILABLE",
    "INTENT_NOT_FOUND",
    "INTENT_EXPIRED",
    "INTENT_ALREADY_TERMINAL",
    "INTENT_HASH_MISMATCH",
    "ORDER_CHECK_NOT_YET_PERFORMED",
    "ORDER_CHECK_FAILED",
    "ORDER_CHECK_STALE",
    "CONFIRMATION_REQUIRED",
    "CONFIRMATION_MISMATCH",
    "CONFIRMATION_WRONG_INTENT",
    "CONFIRMATION_EXPIRED",
    "CONFIRMATION_ALREADY_CONSUMED",
    "CONFIRMATION_CHANNEL_NOT_LOCAL",
    "DUPLICATE_SEND_BLOCKED",
    "UNCERTAIN_RESULT_BLOCKED",
    "BROKER_RESPONSE_MALFORMED",
    "BROKER_RESULT_MISMATCH",
    "LOOKUP_STORE_INTEGRITY_UNCERTAIN",
    "JOURNAL_UNAVAILABLE",
    "EXECUTION_LOCK_UNAVAILABLE",
    "ADAPTER_DISABLED",
)

MAX_TEXT_LENGTH = 256
MAX_COMMENT_LENGTH = 64

_HASH64_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_INTENT_ID_PATTERN = re.compile(r"^exi_[0-9a-f]{32}$")
_ATTEMPT_ID_PATTERN = re.compile(r"^exa_[0-9a-f]{32}$")
_STRATEGY_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-[A-Z0-9]+$")
_SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")


class ExecutionValidationError(ValueError):
    """A controlled, non-secret Phase 5 execution validation failure."""

    def __init__(self, reason_code, message=None):
        if reason_code not in EXECUTION_REASON_CODES:
            raise ValueError("reason_code {!r} is not governed".format(reason_code))
        self.reason_code = reason_code
        super().__init__(message or reason_code)


def _fail(reason_code, message=None):
    raise ExecutionValidationError(reason_code, message)


def _bounded_text(value, field, maximum=MAX_TEXT_LENGTH, allow_empty=False, reason_code="BROKER_RESPONSE_MALFORMED"):
    if value is None and allow_empty:
        return ""
    if not isinstance(value, str):
        _fail(reason_code, "{} must be a string".format(field))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail(reason_code, "{} contains a control character".format(field))
    if not allow_empty and not value:
        _fail(reason_code, "{} must not be empty".format(field))
    return value[:maximum]


def _price(value, field, reason_code="BROKER_RESPONSE_MALFORMED", nullable=False):
    if value is None and nullable:
        return None
    try:
        return canonical_decimal(value, field, positive=True, allow_zero=False)
    except TimelineValidationError as error:
        _fail(reason_code, str(error))


def account_fingerprint_hash(login, company, server):
    """sha256 of the account's login, company and server values joined —
    Section 12: the raw login/company/server never appear in identity
    material, only this hash does."""
    if isinstance(login, bool) or not isinstance(login, int) or login <= 0:
        _fail("ACCOUNT_UNAVAILABLE", "account login must be a positive integer")
    company = _bounded_text(company, "account company", reason_code="ACCOUNT_UNAVAILABLE")
    server = _bounded_text(server, "account server", reason_code="ACCOUNT_UNAVAILABLE")
    material = "\n".join((str(login), company, server))
    return sha256_text(material)


def execution_intent_lookup_key(fields):
    """TRL_EXECUTION_INTENT_LOOKUP_KEY.v1 (Phase 5 slice — no basket/live
    fields). Deterministic and reproducible from the proposal and its
    authorized context alone; contains no nonce and no price."""
    expected = (
        "proposal_id", "account_fingerprint_hash", "broker_native_instrument",
        "side", "quantity", "strategy_id", "strategy_version",
        "risk_policy_hash", "operating_mode", "authorization_identity",
    )
    if set(fields) != set(expected):
        _fail("PROPOSAL_SCHEMA_INVALID", "execution intent lookup key has an invalid field set")
    return "eik_" + sha256_text(deterministic_json_text(fields))[:32]


def order_intent_id_for(lookup_key_fields, client_intent_nonce):
    material = dict(lookup_key_fields)
    material["client_intent_nonce"] = _bounded_text(
        client_intent_nonce, "client_intent_nonce", reason_code="PROPOSAL_SCHEMA_INVALID"
    )
    return "exi_" + sha256_text(deterministic_json_text(material))[:32]


def execution_attempt_id_for(order_intent_id, attempt_sequence, broker_request_hash, request_timestamp_utc):
    if not _INTENT_ID_PATTERN.fullmatch(order_intent_id):
        _fail("INTENT_NOT_FOUND", "order_intent_id is invalid")
    if isinstance(attempt_sequence, bool) or not isinstance(attempt_sequence, int) or attempt_sequence < 1:
        _fail("PROPOSAL_SCHEMA_INVALID", "attempt_sequence must be a positive integer")
    validate_utc_timestamp(request_timestamp_utc, "request_timestamp_utc")
    material = {
        "order_intent_id": order_intent_id,
        "attempt_sequence": attempt_sequence,
        "broker_request_hash": broker_request_hash,
        "request_timestamp_utc": request_timestamp_utc,
    }
    return "exa_" + sha256_text(deterministic_json_text(material))[:32]


def confirmation_challenge_code(order_intent_id, canonical_order_intent_hash):
    """A short, bounded, non-guessable-by-accident challenge fragment the
    local operator must retype exactly — never a vague 'yes'/'confirm'."""
    return sha256_text(order_intent_id + ":" + canonical_order_intent_hash)[:8]


ORDER_INTENT_FIELDS = (
    "schema_version",
    "order_intent_id",
    "proposal_id",
    "canonical_proposal_hash",
    "created_at_utc",
    "expires_at_utc",
    "operating_mode",
    "account_fingerprint_hash",
    "broker_native_instrument",
    "side",
    "order_type",
    "quantity",
    "entry_price",
    "stop_loss",
    "targets",
    "target_allocations_percent",
    "maximum_spread",
    "maximum_deviation_points",
    "time_in_force",
    "fill_policy",
    "strategy_id",
    "strategy_version",
    "risk_policy_hash",
    "idempotency_key",
    "manual_confirmation_required",
    "execution_status",
    "rejection_reasons",
    "canonical_order_intent_hash",
)


def _identity_fields(intent):
    return {
        key: value for key, value in intent.items()
        if key not in ("execution_status", "rejection_reasons", "canonical_order_intent_hash")
    }


def order_intent_hash_for(intent_without_hash):
    return sha256_text(deterministic_json_text(intent_without_hash))


def validate_order_intent(intent):
    """Validate a full TRL_MT5_ORDER_INTENT.v1 document; return a clean copy."""
    if not isinstance(intent, dict) or set(intent) != set(ORDER_INTENT_FIELDS):
        _fail("PROPOSAL_SCHEMA_INVALID", "order intent has an invalid field set")
    if intent["schema_version"] != ORDER_INTENT_SCHEMA:
        _fail("PROPOSAL_SCHEMA_INVALID", "order intent schema is unsupported")
    if not _INTENT_ID_PATTERN.fullmatch(intent["order_intent_id"]):
        _fail("PROPOSAL_SCHEMA_INVALID", "order_intent_id is invalid")
    if not re.fullmatch(r"^sp_[0-9a-f]{32}$", intent["proposal_id"] or ""):
        _fail("PROPOSAL_SCHEMA_INVALID", "proposal_id is invalid")
    if not _HASH64_PATTERN.fullmatch(intent["canonical_proposal_hash"] or ""):
        _fail("PROPOSAL_SCHEMA_INVALID", "canonical_proposal_hash is invalid")
    validate_utc_timestamp(intent["created_at_utc"], "created_at_utc")
    validate_utc_timestamp(intent["expires_at_utc"], "expires_at_utc")
    if intent["operating_mode"] != PHASE5_OPERATING_MODE:
        _fail("OPERATING_MODE_NOT_MT5_DEMO_MANUAL", "order intent operating_mode is not governed for Phase 5")
    if not _HASH64_PATTERN.fullmatch(intent["account_fingerprint_hash"] or ""):
        _fail("ACCOUNT_UNAVAILABLE", "account_fingerprint_hash is invalid")
    try:
        validate_instrument(intent["broker_native_instrument"])
    except TimelineValidationError as error:
        _fail("SYMBOL_UNAVAILABLE", str(error))
    if intent["side"] not in SIDES:
        _fail("PROPOSAL_NOT_EXECUTABLE_SIDE", "order intent side is not governed")
    if intent["order_type"] not in ORDER_TYPES:
        _fail("ENTRY_ZONE_RANGE_MAPPING_NOT_APPROVED", "order intent order_type is not governed")
    quantity = decimal_value(_price(intent["quantity"], "quantity"))
    if quantity <= 0:
        _fail("INVALID_QUANTITY", "quantity must be positive")
    _price(intent["entry_price"], "entry_price")
    _price(intent["stop_loss"], "stop_loss")
    targets = intent["targets"]
    if not isinstance(targets, list) or not 1 <= len(targets) <= 4:
        _fail("PROPOSAL_SCHEMA_INVALID", "targets must be a list of 1 through 4 prices")
    for target in targets:
        _price(target, "target")
    allocations = intent["target_allocations_percent"]
    if not isinstance(allocations, list) or len(allocations) != len(targets):
        _fail("PROPOSAL_SCHEMA_INVALID", "target_allocations_percent must match targets length")
    allocation_sum = Decimal("0")
    for allocation in allocations:
        value = decimal_value(canonical_decimal(allocation, "target allocation", positive=True, allow_zero=False))
        allocation_sum += value
    if allocation_sum != Decimal("100"):
        _fail("PROPOSAL_SCHEMA_INVALID", "target_allocations_percent must sum to exactly 100")
    _price(intent["maximum_spread"], "maximum_spread")
    deviation = intent["maximum_deviation_points"]
    if isinstance(deviation, bool) or not isinstance(deviation, int) or not 0 < deviation <= 1000:
        _fail("PROPOSAL_SCHEMA_INVALID", "maximum_deviation_points is outside its governed range")
    if intent["time_in_force"] not in TIME_IN_FORCE_VALUES:
        _fail("PROPOSAL_SCHEMA_INVALID", "time_in_force is not governed")
    if intent["fill_policy"] not in FILL_POLICIES:
        _fail("FILLING_MODE_UNAVAILABLE", "fill_policy is not governed")
    if not _STRATEGY_ID_PATTERN.fullmatch(intent["strategy_id"] or ""):
        _fail("STRATEGY_NOT_REGISTERED", "strategy_id is invalid")
    if not _SEMVER_PATTERN.fullmatch(intent["strategy_version"] or ""):
        _fail("STRATEGY_VERSION_MISMATCH", "strategy_version is invalid")
    if not _HASH64_PATTERN.fullmatch(intent["risk_policy_hash"] or ""):
        _fail("RISK_POLICY_HASH_MISMATCH", "risk_policy_hash is invalid")
    if intent["idempotency_key"] != intent["order_intent_id"]:
        _fail("PROPOSAL_SCHEMA_INVALID", "idempotency_key must equal order_intent_id in Phase 5")
    if intent["manual_confirmation_required"] is not True:
        _fail("PROPOSAL_SCHEMA_INVALID", "manual_confirmation_required must always be true in Phase 5")
    if intent["execution_status"] not in INTENT_STATES:
        _fail("PROPOSAL_SCHEMA_INVALID", "execution_status is not governed")
    reasons = intent["rejection_reasons"]
    if not isinstance(reasons, list) or len(reasons) > 16:
        _fail("PROPOSAL_SCHEMA_INVALID", "rejection_reasons must be a bounded list")
    for reason in reasons:
        if reason not in EXECUTION_REASON_CODES:
            _fail("PROPOSAL_SCHEMA_INVALID", "rejection_reasons contains an ungoverned code")
    expected_hash = order_intent_hash_for(_identity_fields(intent))
    if intent["canonical_order_intent_hash"] != expected_hash:
        _fail("INTENT_HASH_MISMATCH", "canonical_order_intent_hash does not match canonical content")
    return dict(intent)


__all__ = (
    "CHECK_OUTCOMES",
    "CHECK_RESULT_SCHEMA",
    "CONFIRMATION_SCHEMA",
    "EXECUTION_REASON_CODES",
    "FILL_POLICIES",
    "INTENT_STATES",
    "ORDER_INTENT_FIELDS",
    "ORDER_INTENT_SCHEMA",
    "ORDER_TYPES",
    "PHASE5_OPERATING_MODE",
    "SEND_OUTCOMES",
    "SEND_RESULT_SCHEMA",
    "SIDES",
    "TERMINAL_INTENT_STATES",
    "TIME_IN_FORCE_VALUES",
    "ExecutionValidationError",
    "account_fingerprint_hash",
    "confirmation_challenge_code",
    "execution_attempt_id_for",
    "execution_intent_lookup_key",
    "order_intent_hash_for",
    "order_intent_id_for",
    "validate_order_intent",
)
