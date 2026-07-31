"""Governed data contracts for deterministic forward paper research."""

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN
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


PAPER_PROPOSAL_SCHEMA = "TRL_PAPER_PROPOSAL.v1"
INSTRUMENT_METADATA_SCHEMA = "TRL_PAPER_INSTRUMENT_METADATA.v1"
MARKET_OBSERVATION_SCHEMA = "TRL_PAPER_MARKET_OBSERVATION.v1"
PAPER_ACCOUNT_SCHEMA = "TRL_PAPER_ACCOUNT.v1"
PAPER_POSITION_SCHEMA = "TRL_PAPER_POSITION.v1"
PAPER_HISTORY_SCHEMA = "TRL_PAPER_HISTORY.v1"
PAPER_HEALTH_SCHEMA = "TRL_PAPER_HEALTH.v1"
PAPER_POSITIONS_SCHEMA = "TRL_PAPER_POSITIONS.v1"

PAPER_ONLY_STATUS = "PAPER_ONLY_NO_BROKER_ORDER"
DEFAULT_STARTING_CASH = Decimal("100000")
DEFAULT_RISK_PERCENT = Decimal("0.5")
MAX_RISK_PERCENT = Decimal("1.0")
MAX_DAILY_LOSS_PERCENT = Decimal("2.0")
MAX_DRAWDOWN_PERCENT = Decimal("5.0")
DEFAULT_TARGET_ALLOCATIONS = (
    Decimal("25"),
    Decimal("25"),
    Decimal("25"),
    Decimal("25"),
)

_PROPOSAL_ID_PATTERN = re.compile(r"^pp_[0-9a-f]{32}$")
_TIMELINE_ID_PATTERN = re.compile(r"^tle_[0-9a-f]{32}$")
_BASIS_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._:/-]{0,127}$")
_CURRENCY_PATTERN = re.compile(r"^[A-Z]{3,8}$")
_PROHIBITED_CLAIMS = (
    "guaranteed profit",
    "guaranteed return",
    "99% accurate",
    "profit guarantee",
    "cannot lose",
)


class PaperValidationError(ValueError):
    """A controlled paper-contract validation failure."""


def _fail(message):
    raise PaperValidationError(message)


def _exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        _fail("{} has an invalid field set".format(label))


def _text(value, field, maximum=1000, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value or len(value) > maximum:
        _fail("{} must be a non-empty bounded string".format(field))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail("{} contains a control character".format(field))
    if any(claim in value.casefold() for claim in _PROHIBITED_CLAIMS):
        _fail("{} contains a prohibited performance claim".format(field))
    return value


def _basis_list(value, field, optional=False):
    if value is None and optional:
        return []
    if not isinstance(value, list) or not value or len(value) > 16:
        _fail("{} must be a bounded non-empty list".format(field))
    clean = []
    for item in value:
        if not isinstance(item, str) or not _BASIS_PATTERN.fullmatch(item):
            _fail("{} contains an invalid governed identifier".format(field))
        if item in clean:
            _fail("{} contains a duplicate identifier".format(field))
        clean.append(item)
    return clean


def _optional_timeline_ids(value, field):
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 16:
        _fail("{} must be a bounded list".format(field))
    clean = []
    for item in value:
        if not isinstance(item, str) or not _TIMELINE_ID_PATTERN.fullmatch(item):
            _fail("{} contains an invalid timeline event ID".format(field))
        if item in clean:
            _fail("{} contains a duplicate timeline event ID".format(field))
        clean.append(item)
    return clean


def _price(value, field, nullable=False):
    if value is None and nullable:
        return None
    try:
        rendered = canonical_decimal(value, field, positive=True, allow_zero=False)
    except TimelineValidationError as error:
        raise PaperValidationError(str(error)) from error
    return rendered


def _percent(value, field, maximum=None, allow_zero=True):
    try:
        number = decimal_value(value, field)
    except TimelineValidationError as error:
        raise PaperValidationError(str(error)) from error
    if number < 0 or (not allow_zero and number == 0):
        _fail("{} is outside its governed range".format(field))
    if maximum is not None and number > maximum:
        _fail("{} is outside its governed range".format(field))
    return canonical_decimal(number, field)


def _proposal_identity_fields(proposal):
    return {key: value for key, value in proposal.items() if key != "proposal_id"}


def proposal_id_for(proposal_without_id):
    return "pp_" + sha256_text(deterministic_json_text(proposal_without_id))[:32]


def build_proposal(**fields):
    """Build and validate a proposal with an identity derived from its content."""
    candidate = dict(fields)
    candidate["schema_version"] = PAPER_PROPOSAL_SCHEMA
    candidate["paper_only_status"] = PAPER_ONLY_STATUS
    candidate["proposal_id"] = proposal_id_for(candidate)
    return validate_proposal(candidate)


def validate_proposal(proposal):
    expected = (
        "schema_version",
        "proposal_id",
        "created_at_utc",
        "observed_at_utc",
        "expires_at_utc",
        "instrument",
        "side",
        "entry_type",
        "entry_zone_lower",
        "entry_zone_upper",
        "stop_loss",
        "targets",
        "target_allocations_percent",
        "confidence_score",
        "evidence_quality_status",
        "invalidation_reason",
        "wait_reason",
        "beginner_explanation",
        "strategy_basis_ids",
        "research_basis_ids",
        "market_data_observation_id",
        "news_observation_ids",
        "economic_event_observation_ids",
        "risk_percent",
        "paper_only_status",
    )
    _exact_keys(proposal, expected, "paper proposal")
    if proposal["schema_version"] != PAPER_PROPOSAL_SCHEMA:
        _fail("paper proposal schema is unsupported")
    if proposal["paper_only_status"] != PAPER_ONLY_STATUS:
        _fail("paper proposal must remain paper-only")
    proposal_id = proposal["proposal_id"]
    if not isinstance(proposal_id, str) or not _PROPOSAL_ID_PATTERN.fullmatch(proposal_id):
        _fail("proposal ID is invalid")
    try:
        created = validate_utc_timestamp(proposal["created_at_utc"], "created_at_utc")
        observed = validate_utc_timestamp(proposal["observed_at_utc"], "observed_at_utc")
        expires = validate_utc_timestamp(proposal["expires_at_utc"], "expires_at_utc")
        instrument = validate_instrument(proposal["instrument"])
    except TimelineValidationError as error:
        raise PaperValidationError(str(error)) from error
    if created > observed or expires <= observed:
        _fail("proposal timestamps are not causally ordered")
    side = proposal["side"]
    if side not in ("BUY", "SELL", "WAIT"):
        _fail("proposal side must be BUY, SELL or WAIT")
    entry_type = proposal["entry_type"]
    if entry_type not in ("ENTRY_ZONE", "WAIT"):
        _fail("proposal entry type is invalid")
    confidence = proposal["confidence_score"]
    if isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100:
        _fail("confidence score must be an integer from 0 through 100")
    evidence_status = proposal["evidence_quality_status"]
    if evidence_status not in ("GOVERNED", "LIMITED", "MISSING", "STALE"):
        _fail("evidence quality status is invalid")
    invalidation = _text(proposal["invalidation_reason"], "invalidation reason", 500)
    explanation = _text(proposal["beginner_explanation"], "beginner explanation", 1200)
    strategy_ids = _basis_list(proposal["strategy_basis_ids"], "strategy basis IDs")
    research_ids = _basis_list(proposal["research_basis_ids"], "research basis IDs")
    news_ids = _optional_timeline_ids(proposal["news_observation_ids"], "news observation IDs")
    event_ids = _optional_timeline_ids(
        proposal["economic_event_observation_ids"], "economic-event observation IDs"
    )
    market_id = proposal["market_data_observation_id"]
    if not isinstance(market_id, str) or not _TIMELINE_ID_PATTERN.fullmatch(market_id):
        _fail("market-data observation ID is invalid")
    risk_percent = _percent(proposal["risk_percent"], "risk percent", MAX_RISK_PERCENT)
    clean = deepcopy(proposal)
    clean.update({
        "instrument": instrument,
        "invalidation_reason": invalidation,
        "beginner_explanation": explanation,
        "strategy_basis_ids": strategy_ids,
        "research_basis_ids": research_ids,
        "news_observation_ids": news_ids,
        "economic_event_observation_ids": event_ids,
        "risk_percent": risk_percent,
    })
    if side == "WAIT":
        if entry_type != "WAIT":
            _fail("WAIT proposal must use WAIT entry type")
        wait_reason = _text(proposal["wait_reason"], "wait reason", 500)
        executable = (
            proposal["entry_zone_lower"],
            proposal["entry_zone_upper"],
            proposal["stop_loss"],
            proposal["targets"],
            proposal["target_allocations_percent"],
        )
        if any(value is not None for value in executable):
            _fail("WAIT proposal cannot contain entry, stop, size or targets")
        if decimal_value(risk_percent) != 0:
            _fail("WAIT proposal risk percent must be zero")
        clean["wait_reason"] = wait_reason
    else:
        if entry_type != "ENTRY_ZONE" or proposal["wait_reason"] is not None:
            _fail("BUY/SELL proposal must use ENTRY_ZONE and no wait reason")
        if evidence_status != "GOVERNED":
            _fail("executable paper proposal requires governed evidence")
        lower = _price(proposal["entry_zone_lower"], "entry-zone lower")
        upper = _price(proposal["entry_zone_upper"], "entry-zone upper")
        stop = _price(proposal["stop_loss"], "stop loss")
        if decimal_value(lower) > decimal_value(upper):
            _fail("entry-zone bounds are reversed")
        targets = proposal["targets"]
        allocations = proposal["target_allocations_percent"]
        if not isinstance(targets, list) or len(targets) != 4:
            _fail("proposal requires exactly TP1 through TP4")
        if not isinstance(allocations, list) or len(allocations) != 4:
            _fail("proposal requires exactly four target allocations")
        clean_targets = [_price(item, "target") for item in targets]
        clean_allocations = [
            _percent(item, "target allocation", Decimal("100"), allow_zero=False)
            for item in allocations
        ]
        if sum(decimal_value(item) for item in clean_allocations) != Decimal("100"):
            _fail("target allocations must total exactly 100 percent")
        low = decimal_value(lower)
        high = decimal_value(upper)
        stop_number = decimal_value(stop)
        target_numbers = [decimal_value(item) for item in clean_targets]
        if side == "BUY":
            ordered = stop_number < low <= high < target_numbers[0]
            ordered = ordered and all(
                left < right for left, right in zip(target_numbers, target_numbers[1:])
            )
        else:
            ordered = target_numbers[0] < low <= high < stop_number
            ordered = ordered and all(
                left > right for left, right in zip(target_numbers, target_numbers[1:])
            )
        if not ordered:
            _fail("proposal entry, stop and TP1-TP4 ordering is invalid")
        if decimal_value(risk_percent) <= 0:
            _fail("executable paper proposal requires positive risk")
        clean.update({
            "entry_zone_lower": lower,
            "entry_zone_upper": upper,
            "stop_loss": stop,
            "targets": clean_targets,
            "target_allocations_percent": clean_allocations,
            "wait_reason": None,
        })
    expected_id = proposal_id_for(_proposal_identity_fields(clean))
    if proposal_id != expected_id:
        _fail("proposal ID does not match canonical content")
    return clean


def validate_instrument_metadata(metadata, instrument=None):
    expected = (
        "schema_version",
        "instrument",
        "tick_size",
        "tick_value",
        "contract_size",
        "quantity_step",
        "minimum_quantity",
        "maximum_quantity",
        "quote_currency",
    )
    _exact_keys(metadata, expected, "instrument metadata")
    if metadata["schema_version"] != INSTRUMENT_METADATA_SCHEMA:
        _fail("instrument metadata schema is unsupported")
    try:
        symbol = validate_instrument(metadata["instrument"])
    except TimelineValidationError as error:
        raise PaperValidationError(str(error)) from error
    if instrument is not None and symbol != instrument:
        _fail("instrument metadata symbol mismatch")
    clean = deepcopy(metadata)
    clean["instrument"] = symbol
    for field in (
        "tick_size",
        "tick_value",
        "contract_size",
        "quantity_step",
        "minimum_quantity",
        "maximum_quantity",
    ):
        clean[field] = _price(metadata[field], field.replace("_", " "))
    if decimal_value(clean["minimum_quantity"]) > decimal_value(clean["maximum_quantity"]):
        _fail("instrument quantity bounds are reversed")
    currency = metadata["quote_currency"]
    if not isinstance(currency, str) or not _CURRENCY_PATTERN.fullmatch(currency):
        _fail("quote currency is invalid")
    return clean


def validate_market_observation(payload, instrument):
    expected = (
        "schema_version",
        "observation_kind",
        "bid",
        "ask",
        "open_bid",
        "high_bid",
        "low_bid",
        "close_bid",
        "open_ask",
        "high_ask",
        "low_ask",
        "close_ask",
        "spread",
        "instrument_metadata",
        "metadata_observed_at_utc",
    )
    _exact_keys(payload, expected, "market observation")
    if payload["schema_version"] != MARKET_OBSERVATION_SCHEMA:
        _fail("market observation schema is unsupported")
    kind = payload["observation_kind"]
    if kind not in ("QUOTE", "BAR"):
        _fail("market observation kind is invalid")
    clean = deepcopy(payload)
    clean["bid"] = _price(payload["bid"], "bid")
    clean["ask"] = _price(payload["ask"], "ask")
    if decimal_value(clean["ask"]) <= decimal_value(clean["bid"]):
        _fail("ask must be greater than bid")
    clean["spread"] = _price(payload["spread"], "spread")
    if decimal_value(clean["spread"]) != decimal_value(clean["ask"]) - decimal_value(clean["bid"]):
        _fail("spread must exactly equal ask minus bid")
    bar_fields = (
        "open_bid", "high_bid", "low_bid", "close_bid",
        "open_ask", "high_ask", "low_ask", "close_ask",
    )
    if kind == "QUOTE":
        if any(payload[field] is not None for field in bar_fields):
            _fail("quote observation cannot contain bar prices")
    else:
        for field in bar_fields:
            clean[field] = _price(payload[field], field.replace("_", " "))
        for suffix in ("bid", "ask"):
            low = decimal_value(clean["low_" + suffix])
            high = decimal_value(clean["high_" + suffix])
            opened = decimal_value(clean["open_" + suffix])
            closed = decimal_value(clean["close_" + suffix])
            if low > min(opened, closed) or high < max(opened, closed) or low > high:
                _fail("bar {} OHLC ordering is invalid".format(suffix))
    try:
        validate_utc_timestamp(payload["metadata_observed_at_utc"], "metadata_observed_at_utc")
    except TimelineValidationError as error:
        raise PaperValidationError(str(error)) from error
    clean["instrument_metadata"] = validate_instrument_metadata(
        payload["instrument_metadata"], instrument
    )
    return clean


def quantity_floor(value, step):
    value_number = decimal_value(value)
    step_number = decimal_value(step)
    return (value_number / step_number).to_integral_value(rounding=ROUND_DOWN) * step_number


@dataclass(frozen=True)
class PaperConfiguration:
    """Hard local research defaults; none grant execution authority."""

    starting_cash: Decimal = DEFAULT_STARTING_CASH
    default_risk_percent: Decimal = DEFAULT_RISK_PERCENT
    maximum_risk_percent: Decimal = MAX_RISK_PERCENT
    maximum_daily_loss_percent: Decimal = MAX_DAILY_LOSS_PERCENT
    maximum_drawdown_percent: Decimal = MAX_DRAWDOWN_PERCENT
    slippage_ticks: Decimal = Decimal("1")
    fee_per_quantity: Decimal = Decimal("0.5")
    maximum_observation_age_seconds: int = 300

    def __post_init__(self):
        decimal_fields = (
            "starting_cash",
            "default_risk_percent",
            "maximum_risk_percent",
            "maximum_daily_loss_percent",
            "maximum_drawdown_percent",
            "slippage_ticks",
            "fee_per_quantity",
        )
        for field in decimal_fields:
            value = getattr(self, field)
            try:
                canonical_decimal(value, field, positive=True, allow_zero=field != "starting_cash")
            except TimelineValidationError as error:
                raise PaperValidationError(str(error)) from error
        if self.default_risk_percent > self.maximum_risk_percent:
            _fail("default paper risk exceeds the maximum")
        if self.maximum_risk_percent > MAX_RISK_PERCENT:
            _fail("paper risk maximum cannot exceed 1 percent")
        if self.maximum_daily_loss_percent > MAX_DAILY_LOSS_PERCENT:
            _fail("daily paper loss maximum cannot exceed 2 percent")
        if self.maximum_drawdown_percent > MAX_DRAWDOWN_PERCENT:
            _fail("paper drawdown maximum cannot exceed 5 percent")
        age = self.maximum_observation_age_seconds
        if isinstance(age, bool) or not isinstance(age, int) or not 1 <= age <= 3600:
            _fail("maximum observation age is invalid")

    def document(self):
        return {
            "starting_cash": canonical_decimal(self.starting_cash),
            "default_risk_percent": canonical_decimal(self.default_risk_percent),
            "maximum_risk_percent": canonical_decimal(self.maximum_risk_percent),
            "maximum_daily_loss_percent": canonical_decimal(self.maximum_daily_loss_percent),
            "maximum_drawdown_percent": canonical_decimal(self.maximum_drawdown_percent),
            "slippage_ticks": canonical_decimal(self.slippage_ticks),
            "fee_per_quantity": canonical_decimal(self.fee_per_quantity),
            "maximum_observation_age_seconds": self.maximum_observation_age_seconds,
            "one_open_position_per_instrument": True,
            "martingale": False,
            "averaging_down": False,
            "increase_risk_after_loss": False,
            "automatic_breakeven_stop": False,
            "trailing_stop": False,
        }
