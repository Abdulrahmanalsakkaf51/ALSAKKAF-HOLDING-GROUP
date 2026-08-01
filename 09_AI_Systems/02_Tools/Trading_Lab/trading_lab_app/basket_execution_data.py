"""Governed data contracts for the TRL-R2-009 controlled basket execution
checkpoint (Phase 6).

Pure data/validation module: no I/O, no MetaTrader5 import, no adapter, no
journal. Every schema here is its own independently versioned type, wholly
separate from Phase 5's ``TRL_MT5_ORDER_INTENT.v1`` — see
TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md Section 1.1. This module
adds no field to, and calls no identity function of, ``mt5_execution_data``.
No field here is ever populated by a generative/LLM component and no value
here is trusted from a proposal or parent intent without independent
re-validation by the caller (``basket_execution_service``).
"""

from decimal import Decimal
import re

from .timeline_data import (
    TimelineValidationError,
    canonical_decimal,
    decimal_value,
    deterministic_json_text,
    sha256_text,
    validate_utc_timestamp,
)


BASKET_PLAN_SCHEMA = "TRL_BASKET_PLAN.v1"
BASKET_CHILD_INTENT_SCHEMA = "TRL_BASKET_CHILD_INTENT.v1"
BASKET_CHECK_RESULT_SCHEMA = "TRL_BASKET_CHECK_RESULT.v1"
BASKET_CONFIRMATION_SCHEMA = "TRL_BASKET_CONFIRMATION.v1"
BASKET_CHILD_EXECUTION_RESULT_SCHEMA = "TRL_BASKET_CHILD_EXECUTION_RESULT.v1"
BASKET_STATUS_SCHEMA = "TRL_BASKET_STATUS.v1"

CONFIRM_REQUEST_DOMAIN = "TRL-BASKET-CONFIRM-REQUEST.v1"
CONFIRM_CHALLENGE_DOMAIN = "TRL-BASKET-CONFIRM.v1"
BASKET_ID_DOMAIN = "TRL-BASKET-ID.v1"
BASKET_CHILD_LOOKUP_DOMAIN = "TRL-BASKET-CHILD-LOOKUP.v1"
BASKET_CHILD_ID_DOMAIN = "TRL-BASKET-CHILD-ID.v1"
BASKET_CHECK_DOMAIN = "TRL-BASKET-CHECK.v1"

# The single operating mode Phase 6 ever admits, mirroring
# mt5_execution_data.PHASE5_OPERATING_MODE without importing or aliasing it.
BASKET_OPERATING_MODE = "MT5_DEMO_MANUAL"

MIN_CHILD_COUNT = 2
MAX_CHILD_COUNT = 4

SIDES = ("BUY", "SELL")
ORDER_TYPES = ("BUY_LIMIT", "SELL_LIMIT")

CHECK_OUTCOMES = ("PASSED", "FAILED", "MALFORMED")
SEND_OUTCOMES = ("FILLED", "PARTIALLY_FILLED", "REJECTED", "UNCERTAIN", "MALFORMED")

CONFIRMATION_STATUSES = ("REQUESTED", "ACCEPTED", "INVALIDATED", "EXPIRED")

BASKET_STATUSES = (
    "CREATED", "CHECK_REQUIRED", "CHECKING", "CHECK_COMPLETE",
    "AWAITING_CONFIRMATION", "CONFIRMED", "SENDING",
    "COMPLETED", "FAILED", "PARTIALLY_COMPLETED", "REJECTED", "BLOCKED",
    "FROZEN", "EXPIRED",
)
NONTERMINAL_BASKET_STATUSES = (
    "CREATED", "CHECK_REQUIRED", "CHECKING", "CHECK_COMPLETE",
    "AWAITING_CONFIRMATION", "CONFIRMED", "SENDING",
)
TERMINAL_BASKET_STATUSES = (
    "COMPLETED", "FAILED", "PARTIALLY_COMPLETED", "REJECTED", "BLOCKED", "FROZEN", "EXPIRED",
)
RECONCILIATION_REQUIRED_STATUSES = ("PARTIALLY_COMPLETED", "FROZEN")

BASKET_CHILD_STATES = (
    "CREATED", "CHECK_REQUIRED", "CHECKING", "CHECK_PASSED", "SEND_RESERVED",
    "FILLED", "PARTIALLY_FILLED", "REJECTED", "FROZEN_PENDING_RECONCILIATION",
    "EXPIRED", "BLOCKED",
)
TERMINAL_BASKET_CHILD_STATES = (
    "FILLED", "PARTIALLY_FILLED", "REJECTED", "FROZEN_PENDING_RECONCILIATION", "EXPIRED", "BLOCKED",
)
NONTERMINAL_BASKET_CHILD_STATES = (
    "CREATED", "CHECK_REQUIRED", "CHECKING", "CHECK_PASSED", "SEND_RESERVED",
)

# The closed, additive reason-code vocabulary for every fail-closed basket
# outcome (Section 15). Every basket-layer rejection uses exactly one of
# these; nothing free-text ever substitutes for a reason code.
BASKET_REASON_CODES = (
    "BASKET_SCHEMA_INVALID",
    "BASKET_SCHEMA_VERSION_UNSUPPORTED",
    "PARENT_SCHEMA_VERSION_UNSUPPORTED",
    "BASKET_BACKWARD_COMPATIBILITY_FAILURE",
    "BASKET_CHILD_COUNT_INVALID",
    "BASKET_PARENT_INTENT_NOT_FOUND",
    "BASKET_PARENT_INTENT_NOT_ELIGIBLE",
    "BASKET_PARENT_PROPOSAL_HASH_MISMATCH",
    "BASKET_PARENT_INTENT_HASH_MISMATCH",
    "BASKET_PARENT_EXPIRED",
    "BASKET_TARGET_COUNT_MISMATCH",
    "BASKET_TARGET_ORDER_INVALID",
    "BASKET_TARGET_NOT_UNIQUE",
    "BASKET_ALLOCATION_SUM_INVALID",
    "BASKET_QUANTITY_CONSERVATION_UNRESOLVABLE",
    "BASKET_CHILD_QUANTITY_ZERO",
    "BASKET_CHILD_QUANTITY_BELOW_MINIMUM",
    "BASKET_CHILD_QUANTITY_ABOVE_MAXIMUM",
    "BASKET_CHILD_STEP_MISMATCH",
    "BASKET_ORDER_TYPE_MISMATCH",
    "BASKET_ECONOMIC_MEANING_CHANGED",
    "BASKET_HIDDEN_CHILD_DETECTED",
    "BASKET_HASH_MISMATCH",
    "BASKET_JOURNAL_INTEGRITY_UNCERTAIN",
    "BASKET_NOT_FOUND",
    "BASKET_ALREADY_TERMINAL",
    "BASKET_EXPIRED",
    "BASKET_CAPABILITY_DENIED",
    "BASKET_NOT_CHECK_COMPLETE",
    "BASKET_CHECK_FAILED",
    "BASKET_CHILD_CHECK_FAILED",
    "BASKET_CHILD_CHECK_STALE",
    "BASKET_RECHECK_REQUIRED",
    "BASKET_CHILD_ALREADY_FILLED",
    "BASKET_CHILD_SEND_REJECTED",
    "BASKET_CHILD_SEND_PARTIALLY_FILLED",
    "BASKET_CONFIRMATION_FORMAT_INVALID",
    "BASKET_CONFIRMATION_MISMATCH",
    "BASKET_CONFIRMATION_WRONG_REQUEST",
    "BASKET_CONFIRMATION_EXPIRED",
    "BASKET_CONFIRMATION_ALREADY_ACCEPTED",
    "BASKET_CONFIRMATION_UNAVAILABLE",
    "BASKET_CONFIRMATION_INVALIDATED",
    "BASKET_CONFIRMATION_BASIS_CHANGED",
    "BASKET_CONFIRMATION_REQUEST_REUSED",
    "BASKET_CONFIRMATION_CHANNEL_NOT_LOCAL",
    "BASKET_DUPLICATE_BLOCKED",
    "BASKET_CHILD_SEND_ALREADY_RESERVED",
    "BASKET_CHILD_NOT_NEXT_ELIGIBLE",
    "BASKET_CHILD_ALREADY_TERMINAL",
    "BASKET_CHILD_UNCERTAIN_RESULT_BLOCKED",
    "BASKET_FROZEN",
    "BASKET_RECONCILIATION_REQUIRED",
    "BASKET_EXECUTION_LOCK_UNAVAILABLE",
)

MAX_TEXT_LENGTH = 256
_BASKET_ID_PATTERN = re.compile(r"^bsk_[0-9a-f]{32}$")
_BASKET_LOOKUP_KEY_PATTERN = re.compile(r"^blk_[0-9a-f]{32}$")
_BASKET_CHILD_ID_PATTERN = re.compile(r"^bc_[0-9a-f]{16}$")
_CHECK_RESULT_ID_PATTERN = re.compile(r"^bcr_[0-9a-f]{16}$")
_CONFIRMATION_REQUEST_ID_PATTERN = re.compile(r"^creq_[0-9a-f]{32}$")
_HASH64_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_HASH16_PATTERN = re.compile(r"^[0-9a-f]{16}$")
_CONFIRM_BASKET_ENTRY_PATTERN = re.compile(r"^CONFIRM-BASKET [0-9a-f]{16}$")


class BasketValidationError(ValueError):
    """A controlled, non-secret Phase 6 basket validation failure."""

    def __init__(self, reason_code, message=None):
        if reason_code not in BASKET_REASON_CODES:
            raise ValueError("reason_code {!r} is not governed".format(reason_code))
        self.reason_code = reason_code
        super().__init__(message or reason_code)


def _fail(reason_code, message=None):
    raise BasketValidationError(reason_code, message)


def _bounded_text(value, field, maximum=MAX_TEXT_LENGTH, allow_empty=False, reason_code="BASKET_SCHEMA_INVALID"):
    if value is None and allow_empty:
        return ""
    if not isinstance(value, str):
        _fail(reason_code, "{} must be a string".format(field))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail(reason_code, "{} contains a control character".format(field))
    if not allow_empty and not value:
        _fail(reason_code, "{} must not be empty".format(field))
    return value[:maximum]


def _price(value, field, reason_code="BASKET_SCHEMA_INVALID", nullable=False):
    if value is None and nullable:
        return None
    try:
        return canonical_decimal(value, field, positive=True, allow_zero=False)
    except TimelineValidationError as error:
        _fail(reason_code, str(error))


def _positive_int(value, field, reason_code="BASKET_SCHEMA_INVALID"):
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        _fail(reason_code, "{} must be a positive integer".format(field))
    return value


def _bounded_id_list(value, field, pattern, reason_code="BASKET_SCHEMA_INVALID", max_items=MAX_CHILD_COUNT):
    if not isinstance(value, list) or len(value) > max_items:
        _fail(reason_code, "{} must be a bounded list".format(field))
    for item in value:
        if not isinstance(item, str) or not pattern.fullmatch(item):
            _fail(reason_code, "{} contains an invalid identity".format(field))
    return list(value)


# ---------------------------------------------------------------------
# Deterministic identities (Section 17)
# ---------------------------------------------------------------------

def target_set_hash(targets, target_allocations_percent):
    return sha256_text(deterministic_json_text([targets, target_allocations_percent]))


def basket_lookup_key(fields):
    expected = (
        "parent_order_intent_id", "canonical_parent_order_intent_hash",
        "account_fingerprint_hash", "broker_native_instrument", "side",
        "strategy_id", "strategy_version", "risk_policy_hash",
        "operating_mode", "authorization_identity", "child_count", "target_set_hash",
    )
    if set(fields) != set(expected):
        _fail("BASKET_SCHEMA_INVALID", "basket lookup key has an invalid field set")
    return "blk_" + sha256_text(deterministic_json_text(fields))[:32]


def basket_id_for(lookup_key):
    if not _BASKET_LOOKUP_KEY_PATTERN.fullmatch(lookup_key or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_lookup_key is invalid")
    return "bsk_" + sha256_text(BASKET_ID_DOMAIN + "\n" + lookup_key)[:32]


def approved_aggregate_risk_id_for(basket_id):
    return "agg_" + sha256_text(basket_id)[:32]


def basket_child_lookup_key(fields):
    """Founder-approved non-circular formula (Founder correction round,
    entry 2026-08-01-020): the child identity input is exactly the
    immutable parent-context and per-child economic fields already known
    before the basket plan is assembled — it never includes
    canonical_basket_plan_hash, which is itself computed FROM the ordered
    child IDs this function produces. basket_id stands in for "which
    basket" without needing the plan to exist first (basket_id is itself a
    pure function of the same governed parent/lookup context); every other
    field here anchors the child to its exact immutable parent proposal
    and parent order intent instead."""
    expected = (
        "basket_id", "parent_proposal_id", "canonical_parent_proposal_hash",
        "parent_order_intent_id", "canonical_parent_order_intent_hash",
        "account_fingerprint_hash", "child_index", "target_price",
        "target_allocation_percent", "child_quantity", "broker_native_instrument",
        "side", "order_type", "entry_price", "stop_loss", "strategy_id",
        "strategy_version", "risk_policy_hash", "operating_mode", "expires_at_utc",
    )
    if set(fields) != set(expected):
        _fail("BASKET_SCHEMA_INVALID", "basket child lookup key has an invalid field set")
    return "bclk_" + sha256_text(BASKET_CHILD_LOOKUP_DOMAIN + "\n" + deterministic_json_text(fields))[:32]


def basket_child_id_for(child_lookup_key):
    return "bc_" + sha256_text(BASKET_CHILD_ID_DOMAIN + "\n" + child_lookup_key)[:16]


def check_result_id_for(basket_id, basket_child_id, canonical_basket_child_hash_at_check, checked_at_utc):
    material = "\n".join((
        BASKET_CHECK_DOMAIN, basket_id, basket_child_id,
        canonical_basket_child_hash_at_check, checked_at_utc,
    ))
    return "bcr_" + sha256_text(material)[:16]


def canonical_basket_check_hash_for(fields):
    expected = (
        "basket_id", "basket_child_id", "canonical_basket_child_hash_at_check",
        "checked_at_utc", "check_outcome",
    )
    if set(fields) != set(expected):
        _fail("BASKET_SCHEMA_INVALID", "check-hash input has an invalid field set")
    return sha256_text(deterministic_json_text(fields))


def confirmation_basis_hash_for(fields):
    expected = (
        "basket_id", "canonical_basket_plan_hash", "account_fingerprint_hash",
        "authorized_prior_filled_child_ids", "authorized_remaining_child_ids",
        "authorized_start_child_id", "ordered_required_check_ids",
        "ordered_required_check_hashes", "operating_mode",
        "confirmation_lifetime_seconds",
    )
    if set(fields) != set(expected):
        _fail("BASKET_SCHEMA_INVALID", "confirmation basis has an invalid field set")
    return sha256_text(deterministic_json_text(fields))


def confirmation_request_id_for(
    basket_id, canonical_basket_plan_hash, confirmation_basis_hash,
    confirmation_cycle_number, requested_at_utc, expires_at_utc,
):
    material = "\n".join((
        CONFIRM_REQUEST_DOMAIN, basket_id, canonical_basket_plan_hash,
        confirmation_basis_hash, str(confirmation_cycle_number),
        requested_at_utc, expires_at_utc,
    ))
    return "creq_" + sha256_text(material)[:32]


def challenge_hex_for(confirmation_request_id, basket_id, canonical_basket_plan_hash, confirmation_basis_hash):
    material = "\n".join((
        CONFIRM_CHALLENGE_DOMAIN, confirmation_request_id, basket_id,
        canonical_basket_plan_hash, confirmation_basis_hash,
    ))
    return sha256_text(material)[:16]


def parse_confirmation_entry(text):
    """Parse the exact ``CONFIRM-BASKET <16-hex>`` local operator syntax
    (Section 13.2). Returns the extracted lowercase 16-hex challenge on
    success; fails closed with BASKET_CONFIRMATION_FORMAT_INVALID on any
    deviation — a bare 'yes'/'confirm'/'proceed', a missing/altered prefix,
    wrong case, extra tokens, or non-ASCII content."""
    if not isinstance(text, str) or not text.isascii():
        _fail("BASKET_CONFIRMATION_FORMAT_INVALID", "confirmation entry must be an ASCII string")
    if not _CONFIRM_BASKET_ENTRY_PATTERN.fullmatch(text):
        _fail("BASKET_CONFIRMATION_FORMAT_INVALID", "confirmation entry does not match CONFIRM-BASKET <16-hex>")
    return text[len("CONFIRM-BASKET "):]


def format_confirmation_entry(challenge_hex):
    return "CONFIRM-BASKET " + challenge_hex


# ---------------------------------------------------------------------
# Quantity and allocation conservation (Section 21)
# ---------------------------------------------------------------------

def compute_child_quantities(total_quantity, allocations, volume_min, volume_max, volume_step):
    """Zero-tolerance exact conservation: returns the ordered list of
    canonical-decimal-string child quantities, or fails the entire basket
    closed with the exact Section-21 reason code. No rounding is ever
    performed."""
    total = decimal_value(_price(total_quantity, "total_quantity"))
    step = decimal_value(_price(volume_step, "volume_step"))
    vmin = decimal_value(_price(volume_min, "volume_min"))
    vmax = decimal_value(_price(volume_max, "volume_max"))
    if not allocations:
        _fail("BASKET_SCHEMA_INVALID", "allocations must not be empty")

    allocation_sum = Decimal("0")
    quantities = []
    for allocation in allocations:
        pct = decimal_value(_price(allocation, "target_allocation_percent"))
        allocation_sum += pct
        raw = total * pct / Decimal("100")
        if raw <= 0:
            _fail("BASKET_CHILD_QUANTITY_ZERO")
        remainder = raw % step
        if remainder != 0:
            _fail("BASKET_QUANTITY_CONSERVATION_UNRESOLVABLE")
        if raw < vmin:
            _fail("BASKET_CHILD_QUANTITY_BELOW_MINIMUM")
        if raw > vmax:
            _fail("BASKET_CHILD_QUANTITY_ABOVE_MAXIMUM")
        quantities.append(canonical_decimal(raw))
    if allocation_sum != Decimal("100"):
        _fail("BASKET_ALLOCATION_SUM_INVALID")
    aggregate = sum((decimal_value(quantity) for quantity in quantities), Decimal("0"))
    if aggregate != total:
        _fail("BASKET_QUANTITY_CONSERVATION_UNRESOLVABLE")
    return quantities


# ---------------------------------------------------------------------
# TRL_BASKET_PLAN.v1 (Section 9)
# ---------------------------------------------------------------------

CHILD_PLAN_DESCRIPTOR_FIELDS = (
    "child_index", "basket_child_id", "target_price",
    "target_allocation_percent", "child_quantity",
)

BASKET_PLAN_FIELDS = (
    "schema_version", "basket_id", "basket_lookup_key", "parent_proposal_id",
    "canonical_parent_proposal_hash", "parent_order_intent_id",
    "canonical_parent_order_intent_hash", "account_fingerprint_hash",
    "broker_native_instrument", "side", "order_type", "entry_price", "stop_loss",
    "total_quantity", "approved_aggregate_risk_id", "child_count", "children",
    "strategy_id", "strategy_version", "risk_policy_hash", "operating_mode",
    "created_at_utc", "expires_at_utc", "canonical_basket_plan_hash",
)


def _plan_identity_fields(plan):
    return {key: value for key, value in plan.items() if key != "canonical_basket_plan_hash"}


def canonical_basket_plan_hash_for(plan_without_hash):
    return sha256_text(deterministic_json_text(plan_without_hash))


def _validate_child_descriptor(descriptor, expected_index):
    if not isinstance(descriptor, dict) or set(descriptor) != set(CHILD_PLAN_DESCRIPTOR_FIELDS):
        _fail("BASKET_SCHEMA_INVALID", "child descriptor has an invalid field set")
    if descriptor["child_index"] != expected_index:
        _fail("BASKET_TARGET_ORDER_INVALID", "child_index is out of order")
    if not _BASKET_CHILD_ID_PATTERN.fullmatch(descriptor["basket_child_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_child_id is invalid")
    _price(descriptor["target_price"], "target_price")
    _price(descriptor["target_allocation_percent"], "target_allocation_percent")
    _price(descriptor["child_quantity"], "child_quantity")
    return dict(descriptor)


def validate_basket_plan(plan):
    """Validate a full TRL_BASKET_PLAN.v1 document; return a clean copy."""
    if not isinstance(plan, dict) or set(plan) != set(BASKET_PLAN_FIELDS):
        _fail("BASKET_SCHEMA_INVALID", "basket plan has an invalid field set")
    if plan["schema_version"] != BASKET_PLAN_SCHEMA:
        _fail("BASKET_SCHEMA_VERSION_UNSUPPORTED", "basket plan schema is unsupported")
    if not _BASKET_ID_PATTERN.fullmatch(plan["basket_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_id is invalid")
    if not _BASKET_LOOKUP_KEY_PATTERN.fullmatch(plan["basket_lookup_key"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_lookup_key is invalid")
    _bounded_text(plan["parent_proposal_id"], "parent_proposal_id")
    if not _HASH64_PATTERN.fullmatch(plan["canonical_parent_proposal_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "canonical_parent_proposal_hash is invalid")
    _bounded_text(plan["parent_order_intent_id"], "parent_order_intent_id")
    if not _HASH64_PATTERN.fullmatch(plan["canonical_parent_order_intent_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "canonical_parent_order_intent_hash is invalid")
    if not _HASH64_PATTERN.fullmatch(plan["account_fingerprint_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "account_fingerprint_hash is invalid")
    _bounded_text(plan["broker_native_instrument"], "broker_native_instrument")
    if plan["side"] not in SIDES:
        _fail("BASKET_SCHEMA_INVALID", "side is not governed")
    if plan["order_type"] not in ORDER_TYPES:
        _fail("BASKET_ORDER_TYPE_MISMATCH", "order_type is not governed")
    _price(plan["entry_price"], "entry_price")
    _price(plan["stop_loss"], "stop_loss")
    _price(plan["total_quantity"], "total_quantity")
    if not plan["approved_aggregate_risk_id"] or not plan["approved_aggregate_risk_id"].startswith("agg_"):
        _fail("BASKET_SCHEMA_INVALID", "approved_aggregate_risk_id is invalid")
    child_count = plan["child_count"]
    if isinstance(child_count, bool) or not isinstance(child_count, int) or not (MIN_CHILD_COUNT <= child_count <= MAX_CHILD_COUNT):
        _fail("BASKET_CHILD_COUNT_INVALID", "child_count must be between 2 and 4")
    children = plan["children"]
    if not isinstance(children, list) or len(children) != child_count:
        _fail("BASKET_HIDDEN_CHILD_DETECTED", "children length does not match child_count")
    clean_children = [
        _validate_child_descriptor(descriptor, index) for index, descriptor in enumerate(children)
    ]
    seen_targets = set()
    allocation_sum = Decimal("0")
    quantity_sum = Decimal("0")
    for descriptor in clean_children:
        target = descriptor["target_price"]
        if target in seen_targets:
            _fail("BASKET_TARGET_NOT_UNIQUE")
        seen_targets.add(target)
        allocation_sum += decimal_value(descriptor["target_allocation_percent"])
        quantity_sum += decimal_value(descriptor["child_quantity"])
    if allocation_sum != Decimal("100"):
        _fail("BASKET_ALLOCATION_SUM_INVALID")
    if quantity_sum != decimal_value(plan["total_quantity"]):
        _fail("BASKET_QUANTITY_CONSERVATION_UNRESOLVABLE")
    _bounded_text(plan["strategy_id"], "strategy_id")
    _bounded_text(plan["strategy_version"], "strategy_version")
    if not _HASH64_PATTERN.fullmatch(plan["risk_policy_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "risk_policy_hash is invalid")
    if plan["operating_mode"] != BASKET_OPERATING_MODE:
        _fail("BASKET_CAPABILITY_DENIED", "basket plan operating_mode is not governed for Phase 6")
    validate_utc_timestamp(plan["created_at_utc"], "created_at_utc")
    validate_utc_timestamp(plan["expires_at_utc"], "expires_at_utc")
    expected_hash = canonical_basket_plan_hash_for(_plan_identity_fields(plan))
    if plan["canonical_basket_plan_hash"] != expected_hash:
        _fail("BASKET_HASH_MISMATCH", "canonical_basket_plan_hash does not match canonical content")
    return dict(plan)


# ---------------------------------------------------------------------
# TRL_BASKET_CHILD_INTENT.v1 (Section 10)
# ---------------------------------------------------------------------

BASKET_CHILD_INTENT_FIELDS = (
    "schema_version", "basket_id", "canonical_basket_plan_hash_at_creation",
    "basket_child_id", "child_index", "parent_order_intent_id",
    "account_fingerprint_hash", "broker_native_instrument", "side", "order_type",
    "entry_price", "stop_loss", "strategy_id", "strategy_version", "risk_policy_hash",
    "operating_mode", "expires_at_utc", "target_price", "target_allocation_percent",
    "child_quantity", "idempotency_key", "canonical_basket_child_hash",
)


def _child_identity_fields(child):
    return {key: value for key, value in child.items() if key != "canonical_basket_child_hash"}


def canonical_basket_child_hash_for(child_without_hash):
    return sha256_text(deterministic_json_text(child_without_hash))


def validate_basket_child_intent(child):
    """Validate a full TRL_BASKET_CHILD_INTENT.v1 document; return a clean copy."""
    if not isinstance(child, dict) or set(child) != set(BASKET_CHILD_INTENT_FIELDS):
        _fail("BASKET_SCHEMA_INVALID", "basket child intent has an invalid field set")
    if child["schema_version"] != BASKET_CHILD_INTENT_SCHEMA:
        _fail("BASKET_SCHEMA_VERSION_UNSUPPORTED", "basket child intent schema is unsupported")
    if not _BASKET_ID_PATTERN.fullmatch(child["basket_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_id is invalid")
    if not _HASH64_PATTERN.fullmatch(child["canonical_basket_plan_hash_at_creation"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "canonical_basket_plan_hash_at_creation is invalid")
    if not _BASKET_CHILD_ID_PATTERN.fullmatch(child["basket_child_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_child_id is invalid")
    if isinstance(child["child_index"], bool) or not isinstance(child["child_index"], int) or child["child_index"] < 0:
        _fail("BASKET_SCHEMA_INVALID", "child_index must be a non-negative integer")
    _bounded_text(child["parent_order_intent_id"], "parent_order_intent_id")
    if not _HASH64_PATTERN.fullmatch(child["account_fingerprint_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "account_fingerprint_hash is invalid")
    _bounded_text(child["broker_native_instrument"], "broker_native_instrument")
    if child["side"] not in SIDES:
        _fail("BASKET_SCHEMA_INVALID", "side is not governed")
    if child["order_type"] not in ORDER_TYPES:
        _fail("BASKET_ORDER_TYPE_MISMATCH", "order_type is not governed")
    _price(child["entry_price"], "entry_price")
    _price(child["stop_loss"], "stop_loss")
    _bounded_text(child["strategy_id"], "strategy_id")
    _bounded_text(child["strategy_version"], "strategy_version")
    if not _HASH64_PATTERN.fullmatch(child["risk_policy_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "risk_policy_hash is invalid")
    if child["operating_mode"] != BASKET_OPERATING_MODE:
        _fail("BASKET_CAPABILITY_DENIED", "basket child operating_mode is not governed for Phase 6")
    validate_utc_timestamp(child["expires_at_utc"], "expires_at_utc")
    _price(child["target_price"], "target_price")
    _price(child["target_allocation_percent"], "target_allocation_percent")
    _price(child["child_quantity"], "child_quantity")
    if child["idempotency_key"] != child["basket_child_id"]:
        _fail("BASKET_SCHEMA_INVALID", "idempotency_key must equal basket_child_id")
    expected_hash = canonical_basket_child_hash_for(_child_identity_fields(child))
    if child["canonical_basket_child_hash"] != expected_hash:
        _fail("BASKET_HASH_MISMATCH", "canonical_basket_child_hash does not match canonical content")
    return dict(child)


# ---------------------------------------------------------------------
# TRL_BASKET_CHECK_RESULT.v1 (Section 11)
# ---------------------------------------------------------------------

BASKET_CHECK_RESULT_FIELDS = (
    "schema_version", "check_result_id", "basket_id", "basket_child_id",
    "canonical_basket_child_hash_at_check", "checked_at_utc", "check_outcome",
    "reason_codes", "canonical_basket_check_hash",
)


def validate_basket_check_result(record):
    if not isinstance(record, dict) or set(record) != set(BASKET_CHECK_RESULT_FIELDS):
        _fail("BASKET_SCHEMA_INVALID", "basket check result has an invalid field set")
    if record["schema_version"] != BASKET_CHECK_RESULT_SCHEMA:
        _fail("BASKET_SCHEMA_VERSION_UNSUPPORTED", "basket check result schema is unsupported")
    if not _CHECK_RESULT_ID_PATTERN.fullmatch(record["check_result_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "check_result_id is invalid")
    if not _BASKET_ID_PATTERN.fullmatch(record["basket_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_id is invalid")
    if not _BASKET_CHILD_ID_PATTERN.fullmatch(record["basket_child_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_child_id is invalid")
    if not _HASH64_PATTERN.fullmatch(record["canonical_basket_child_hash_at_check"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "canonical_basket_child_hash_at_check is invalid")
    validate_utc_timestamp(record["checked_at_utc"], "checked_at_utc")
    if record["check_outcome"] not in CHECK_OUTCOMES:
        _fail("BASKET_SCHEMA_INVALID", "check_outcome is not governed")
    reasons = record["reason_codes"]
    if not isinstance(reasons, list) or len(reasons) > 16:
        _fail("BASKET_SCHEMA_INVALID", "reason_codes must be a bounded list")
    for reason in reasons:
        if reason not in BASKET_REASON_CODES:
            _fail("BASKET_SCHEMA_INVALID", "reason_codes contains an ungoverned code")
    expected_hash = canonical_basket_check_hash_for({
        "basket_id": record["basket_id"],
        "basket_child_id": record["basket_child_id"],
        "canonical_basket_child_hash_at_check": record["canonical_basket_child_hash_at_check"],
        "checked_at_utc": record["checked_at_utc"],
        "check_outcome": record["check_outcome"],
    })
    if record["canonical_basket_check_hash"] != expected_hash:
        _fail("BASKET_HASH_MISMATCH", "canonical_basket_check_hash does not match canonical content")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_BASKET_CHILD_EXECUTION_RESULT.v1 (Section 11.1)
# ---------------------------------------------------------------------

BASKET_CHILD_EXECUTION_RESULT_FIELDS = (
    "schema_version", "basket_id", "basket_child_id",
    "canonical_basket_child_hash_at_send", "send_reserved_at_utc", "send_outcome",
    "broker_response_hash", "filled_quantity", "broker_order_ticket",
    "broker_deal_ticket", "broker_position_ticket", "result_recorded_at_utc",
)


def validate_basket_child_execution_result(record):
    if not isinstance(record, dict) or set(record) != set(BASKET_CHILD_EXECUTION_RESULT_FIELDS):
        _fail("BASKET_SCHEMA_INVALID", "basket child execution result has an invalid field set")
    if record["schema_version"] != BASKET_CHILD_EXECUTION_RESULT_SCHEMA:
        _fail("BASKET_SCHEMA_VERSION_UNSUPPORTED", "basket child execution result schema is unsupported")
    if not _BASKET_ID_PATTERN.fullmatch(record["basket_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_id is invalid")
    if not _BASKET_CHILD_ID_PATTERN.fullmatch(record["basket_child_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_child_id is invalid")
    if not _HASH64_PATTERN.fullmatch(record["canonical_basket_child_hash_at_send"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "canonical_basket_child_hash_at_send is invalid")
    validate_utc_timestamp(record["send_reserved_at_utc"], "send_reserved_at_utc")
    if record["send_outcome"] is not None and record["send_outcome"] not in SEND_OUTCOMES:
        _fail("BASKET_SCHEMA_INVALID", "send_outcome is not governed")
    if record["filled_quantity"] is not None:
        _price(record["filled_quantity"], "filled_quantity")
    for field in ("broker_order_ticket", "broker_deal_ticket", "broker_position_ticket"):
        if record[field] is not None:
            _bounded_text(record[field], field)
    if record["result_recorded_at_utc"] is not None:
        validate_utc_timestamp(record["result_recorded_at_utc"], "result_recorded_at_utc")
    return dict(record)


# ---------------------------------------------------------------------
# TRL_BASKET_CONFIRMATION.v1 (Section 12)
# ---------------------------------------------------------------------

BASKET_CONFIRMATION_FIELDS = (
    "schema_version", "confirmation_request_id", "confirmation_cycle_number",
    "basket_id", "canonical_basket_plan_hash", "confirmation_basis_hash",
    "account_fingerprint_hash", "authorized_prior_filled_child_ids",
    "authorized_remaining_child_ids", "authorized_start_child_id",
    "ordered_required_check_ids", "ordered_required_check_hashes",
    "challenge_derivation_version", "challenge_hex", "requested_at_utc",
    "expires_at_utc", "status", "accepted_at_utc", "expired_at_utc",
    "invalidated_at_utc", "invalidation_reason", "canonical_confirmation_request_hash",
)

_CONFIRMATION_MUTABLE_FIELDS = (
    "canonical_confirmation_request_hash", "status", "accepted_at_utc",
    "expired_at_utc", "invalidated_at_utc", "invalidation_reason",
)


def _confirmation_identity_fields(record):
    return {key: value for key, value in record.items() if key not in _CONFIRMATION_MUTABLE_FIELDS}


def canonical_confirmation_request_hash_for(identity_fields):
    return sha256_text(deterministic_json_text(identity_fields))


def validate_basket_confirmation(record):
    if not isinstance(record, dict) or set(record) != set(BASKET_CONFIRMATION_FIELDS):
        _fail("BASKET_SCHEMA_INVALID", "basket confirmation has an invalid field set")
    if record["schema_version"] != BASKET_CONFIRMATION_SCHEMA:
        _fail("BASKET_SCHEMA_VERSION_UNSUPPORTED", "basket confirmation schema is unsupported")
    if not _CONFIRMATION_REQUEST_ID_PATTERN.fullmatch(record["confirmation_request_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "confirmation_request_id is invalid")
    _positive_int(record["confirmation_cycle_number"], "confirmation_cycle_number")
    if not _BASKET_ID_PATTERN.fullmatch(record["basket_id"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "basket_id is invalid")
    if not _HASH64_PATTERN.fullmatch(record["canonical_basket_plan_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "canonical_basket_plan_hash is invalid")
    if not _HASH64_PATTERN.fullmatch(record["confirmation_basis_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "confirmation_basis_hash is invalid")
    if not _HASH64_PATTERN.fullmatch(record["account_fingerprint_hash"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "account_fingerprint_hash is invalid")
    prior = _bounded_id_list(record["authorized_prior_filled_child_ids"], "authorized_prior_filled_child_ids", _BASKET_CHILD_ID_PATTERN)
    remaining = _bounded_id_list(record["authorized_remaining_child_ids"], "authorized_remaining_child_ids", _BASKET_CHILD_ID_PATTERN)
    if not remaining:
        _fail("BASKET_SCHEMA_INVALID", "authorized_remaining_child_ids must not be empty")
    if record["authorized_start_child_id"] not in remaining:
        _fail("BASKET_SCHEMA_INVALID", "authorized_start_child_id must be a member of authorized_remaining_child_ids")
    check_ids = _bounded_id_list(record["ordered_required_check_ids"], "ordered_required_check_ids", _CHECK_RESULT_ID_PATTERN)
    check_hashes = record["ordered_required_check_hashes"]
    if not isinstance(check_hashes, list) or len(check_hashes) != len(check_ids):
        _fail("BASKET_SCHEMA_INVALID", "ordered_required_check_hashes must align with ordered_required_check_ids")
    for value in check_hashes:
        if not _HASH64_PATTERN.fullmatch(value or ""):
            _fail("BASKET_SCHEMA_INVALID", "ordered_required_check_hashes contains an invalid hash")
    if len(check_ids) != len(remaining):
        _fail("BASKET_SCHEMA_INVALID", "ordered_required_check_ids must align with authorized_remaining_child_ids")
    _bounded_text(record["challenge_derivation_version"], "challenge_derivation_version")
    if not _HASH16_PATTERN.fullmatch(record["challenge_hex"] or ""):
        _fail("BASKET_SCHEMA_INVALID", "challenge_hex is invalid")
    validate_utc_timestamp(record["requested_at_utc"], "requested_at_utc")
    validate_utc_timestamp(record["expires_at_utc"], "expires_at_utc")
    if record["status"] not in CONFIRMATION_STATUSES:
        _fail("BASKET_SCHEMA_INVALID", "status is not governed")
    if record["accepted_at_utc"] is not None:
        validate_utc_timestamp(record["accepted_at_utc"], "accepted_at_utc")
    if record["expired_at_utc"] is not None:
        validate_utc_timestamp(record["expired_at_utc"], "expired_at_utc")
    if record["invalidated_at_utc"] is not None:
        validate_utc_timestamp(record["invalidated_at_utc"], "invalidated_at_utc")
    if record["invalidation_reason"] is not None and record["invalidation_reason"] not in BASKET_REASON_CODES:
        _fail("BASKET_SCHEMA_INVALID", "invalidation_reason is not governed")
    expected_hash = canonical_confirmation_request_hash_for(_confirmation_identity_fields(record))
    if record["canonical_confirmation_request_hash"] != expected_hash:
        _fail("BASKET_HASH_MISMATCH", "canonical_confirmation_request_hash does not match canonical content")
    del prior  # validated for shape only; ordering/content cross-checked by the service
    return dict(record)


# ---------------------------------------------------------------------
# TRL_BASKET_STATUS.v1 (Section 36) — read model, service-constructed
# ---------------------------------------------------------------------

BASKET_STATUS_FIELDS = (
    "schema_version", "basket_id", "basket_status", "reconciliation_required",
    "parent_proposal_id", "parent_order_intent_id", "broker_native_instrument",
    "side", "total_quantity", "child_count", "filled_child_count",
    "completed_quantity", "remaining_quantity", "children", "confirmation_status",
    "active_confirmation_request_id", "active_confirmation_cycle_number",
    "authorized_start_child_id", "authorized_remaining_child_ids",
    "live_next_eligible_child_id", "created_at_utc", "expires_at_utc",
    "rejection_reasons", "terminal_reason", "canonical_basket_plan_hash",
)


__all__ = (
    "BASKET_CHECK_RESULT_FIELDS",
    "BASKET_CHECK_RESULT_SCHEMA",
    "BASKET_CHILD_EXECUTION_RESULT_FIELDS",
    "BASKET_CHILD_EXECUTION_RESULT_SCHEMA",
    "BASKET_CHILD_INTENT_FIELDS",
    "BASKET_CHILD_INTENT_SCHEMA",
    "BASKET_CHILD_STATES",
    "BASKET_CONFIRMATION_FIELDS",
    "BASKET_CONFIRMATION_SCHEMA",
    "BASKET_OPERATING_MODE",
    "BASKET_PLAN_FIELDS",
    "BASKET_PLAN_SCHEMA",
    "BASKET_REASON_CODES",
    "BASKET_STATUS_FIELDS",
    "BASKET_STATUS_SCHEMA",
    "BASKET_STATUSES",
    "CHECK_OUTCOMES",
    "CHILD_PLAN_DESCRIPTOR_FIELDS",
    "CONFIRMATION_STATUSES",
    "MAX_CHILD_COUNT",
    "MIN_CHILD_COUNT",
    "NONTERMINAL_BASKET_CHILD_STATES",
    "NONTERMINAL_BASKET_STATUSES",
    "ORDER_TYPES",
    "RECONCILIATION_REQUIRED_STATUSES",
    "SEND_OUTCOMES",
    "SIDES",
    "TERMINAL_BASKET_CHILD_STATES",
    "TERMINAL_BASKET_STATUSES",
    "BasketValidationError",
    "approved_aggregate_risk_id_for",
    "basket_child_id_for",
    "basket_child_lookup_key",
    "basket_id_for",
    "basket_lookup_key",
    "canonical_basket_check_hash_for",
    "canonical_basket_child_hash_for",
    "canonical_basket_plan_hash_for",
    "canonical_confirmation_request_hash_for",
    "challenge_hex_for",
    "check_result_id_for",
    "compute_child_quantities",
    "confirmation_basis_hash_for",
    "confirmation_request_id_for",
    "format_confirmation_entry",
    "parse_confirmation_entry",
    "target_set_hash",
    "validate_basket_child_execution_result",
    "validate_basket_child_intent",
    "validate_basket_check_result",
    "validate_basket_confirmation",
    "validate_basket_plan",
)
