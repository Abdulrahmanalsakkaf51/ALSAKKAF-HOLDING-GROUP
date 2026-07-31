"""Governed data contracts for the TRL-R2-006 signal-intelligence pipeline.

Defines ``TRL_SIGNAL_PROPOSAL.v1``, which extends R2-005's
``TRL_PAPER_PROPOSAL.v1`` (see ``paper_data.py``) with the additional fields
TRL_R2_006_SIGNAL_INTELLIGENCE_CONTRACT.md Section 4 requires. All R2-005
structural invariants (entry/stop/TP1-TP4 ordering, allocation-sum = 100%,
causal evidence IDs, the prohibited-claim-string filter) are reused, not
forked: for an executable (BUY/SELL) proposal this module builds the R2-005
field subset and validates it with ``paper_data.validate_proposal`` itself,
then layers the R2-006 extension fields on top. R2-006 extends the ``side``
vocabulary to five values (BUY/SELL/HOLD/WAIT/BLOCKED, vs. R2-005's three),
so the WAIT-shaped branch (HOLD/WAIT/BLOCKED all carry zero risk and no
entry/stop/target fields) is validated directly here rather than through
``paper_data.validate_proposal``, which does not know the two additional
outcome values.

No field on a governed proposal is ever set by a generative/LLM component;
see ``signal_llm_adapter.py`` for that boundary.
"""

from copy import deepcopy
from decimal import Decimal
import re

from . import mode_service
from . import signal_confidence
from .paper_data import (
    MAX_RISK_PERCENT,
    PAPER_ONLY_STATUS,
    PAPER_PROPOSAL_SCHEMA,
    PaperValidationError,
    proposal_id_for as paper_proposal_id_for,
    validate_market_observation,
    validate_proposal as validate_paper_proposal,
)
from .timeline_data import (
    TimelineValidationError,
    canonical_decimal,
    decimal_value,
    deterministic_json_text,
    sanitize_payload,
    sha256_text,
    validate_instrument,
    validate_utc_timestamp,
)


SIGNAL_PROPOSAL_SCHEMA = "TRL_SIGNAL_PROPOSAL.v1"

SIDES = ("BUY", "SELL", "HOLD", "WAIT", "BLOCKED")
EXECUTABLE_SIDES = ("BUY", "SELL")
WAIT_SHAPED_SIDES = ("HOLD", "WAIT", "BLOCKED")
ENTRY_TYPES = ("ENTRY_ZONE", "WAIT")
EVIDENCE_QUALITY_STATUSES = ("GOVERNED", "LIMITED", "MISSING", "STALE")
REGIME_CLASSIFICATIONS = ("TREND_UP", "TREND_DOWN", "RANGE", "HIGH_VOLATILITY", "UNKNOWN")
SAMPLE_LABELS = (
    # VALIDATION added alongside the R2-006 contract's original five
    # (Section 7 lists IN_SAMPLE/OUT_OF_SAMPLE/WALK_FORWARD/SYNTHETIC_PAPER/
    # BROKER_DEMO/BROKER_LIVE) because the Phase 4 performance-reporting
    # requirement explicitly separates IN_SAMPLE/VALIDATION/OUT_OF_SAMPLE
    # as three distinct labels, not two.
    "IN_SAMPLE", "VALIDATION", "OUT_OF_SAMPLE", "WALK_FORWARD",
    "SYNTHETIC_PAPER", "BROKER_DEMO", "BROKER_LIVE",
)

ROLE_NAMES = (
    "data_quality",
    "market_regime",
    "technical_strategy",
    "news_event_risk",
    "independent_risk",
    "execution_eligibility",
)

# Section 2's exact mandatory failure/reason-code vocabulary, plus the
# pipeline-internal-error and Role 5 size-mismatch codes from Sections 6.4
# and 8. This is the closed vocabulary `rejection_reasons` values are drawn
# from; each role's own finer-grained `reasons[]` may add detail beyond this
# set (see individual role modules), but the top-level blocking code that
# reaches `rejection_reasons` is always one of these.
ROLE_FAILURE_REASON_CODES = (
    "DATA_QUALITY_REJECTED",
    "REGIME_UNCLASSIFIABLE",
    "NO_STRATEGY_SIGNAL",
    "NEWS_EVENT_RISK_BLOCK",
    "RISK_REJECTED",
    "SIZE_MISMATCH_BETWEEN_PARTNERS",
    "EXECUTION_INELIGIBLE",
    "PIPELINE_INTERNAL_ERROR",
)

_PROPOSAL_ID_PATTERN = re.compile(r"^sp_[0-9a-f]{32}$")
_TIMELINE_ID_PATTERN = re.compile(r"^tle_[0-9a-f]{32}$")
_HASH64_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_BASIS_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9._:/-]{0,127}$")
_STRATEGY_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*-[A-Z0-9]+$")
_SEMVER_PATTERN = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_CALIBRATION_SOURCE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_REASON_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,63}$")
_PROHIBITED_CLAIMS = (
    "guaranteed profit",
    "guaranteed return",
    "99% accurate",
    "profit guarantee",
    "cannot lose",
)


class SignalValidationError(ValueError):
    """A controlled, non-secret signal-contract validation failure."""


def _fail(message):
    raise SignalValidationError(message)


def _exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        _fail("{} has an invalid field set".format(label))


def _text(value, field, maximum=1200, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value or len(value) > maximum:
        _fail("{} must be a non-empty bounded string".format(field))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        _fail("{} contains a control character".format(field))
    if any(claim in value.casefold() for claim in _PROHIBITED_CLAIMS):
        _fail("{} contains a prohibited performance claim".format(field))
    return value


def _price(value, field, nullable=False):
    if value is None and nullable:
        return None
    try:
        return canonical_decimal(value, field, positive=True, allow_zero=False)
    except TimelineValidationError as error:
        raise SignalValidationError(str(error)) from error


def _pattern_id(value, field, pattern, nullable=False):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not pattern.fullmatch(value):
        _fail("{} is invalid".format(field))
    return value


def _bounded_reason_list(value, field, maximum=16):
    if not isinstance(value, list) or len(value) > maximum:
        _fail("{} must be a bounded list".format(field))
    clean = []
    for item in value:
        if not isinstance(item, str) or not _REASON_CODE_PATTERN.fullmatch(item):
            _fail("{} contains an invalid reason code".format(field))
        clean.append(item)
    return clean


def _timeline_id_list(value, field, maximum=16):
    if not isinstance(value, list) or len(value) > maximum:
        _fail("{} must be a bounded list".format(field))
    clean = []
    for item in value:
        if not isinstance(item, str) or not _TIMELINE_ID_PATTERN.fullmatch(item):
            _fail("{} contains an invalid governed timeline event ID".format(field))
        if item in clean:
            _fail("{} contains a duplicate timeline event ID".format(field))
        clean.append(item)
    return clean


def _basis_list(value, field, maximum=16):
    if not isinstance(value, list) or not value or len(value) > maximum:
        _fail("{} must be a bounded non-empty list".format(field))
    clean = []
    for item in value:
        if not isinstance(item, str) or not _BASIS_PATTERN.fullmatch(item):
            _fail("{} contains an invalid governed identifier".format(field))
        if item in clean:
            _fail("{} contains a duplicate identifier".format(field))
        clean.append(item)
    return clean


def _bounded_object(value, field, expected_keys=None):
    try:
        clean = sanitize_payload(value)
    except TimelineValidationError as error:
        raise SignalValidationError(str(error)) from error
    if not isinstance(clean, dict):
        _fail("{} must be a governed bounded object".format(field))
    if expected_keys is not None and set(clean) != set(expected_keys):
        _fail("{} has an invalid field set".format(field))
    return clean


def _role_result(value, field, status_values):
    clean = _bounded_object(value, field)
    if "status" not in clean or clean["status"] not in status_values:
        _fail("{} status is not governed".format(field))
    if "reasons" not in clean or not isinstance(clean["reasons"], list):
        _fail("{} reasons must be a list".format(field))
    return clean


SIGNAL_PROPOSAL_FIELDS = (
    # -- R2-005-inherited fields (see paper_data.PAPER_PROPOSAL_SCHEMA) --
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
    # -- R2-006 additions (Section 4) --
    "strategy_id",
    "strategy_version",
    "broker_native_instrument",
    "regime_classification",
    "feature_snapshot_hash",
    "data_quality_result",
    "news_event_risk_result",
    "confidence_calibration_source",
    "confidence_status",
    "explanation",
    "rejection_reasons",
    "model_rule_versions",
    "role_results",
    "candidate_quantity",
    "independent_quantity",
    "maximum_spread",
    "active_risk_policy_hash",
    "operating_mode",
    "sample_label",
    "canonical_proposal_hash",
)

_R2005_BASE_FIELDS = (
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


def _identity_fields(proposal):
    return {
        key: value for key, value in proposal.items()
        if key not in ("proposal_id", "canonical_proposal_hash")
    }


def signal_proposal_id_for(proposal_without_id):
    digest = sha256_text(deterministic_json_text(proposal_without_id))
    return "sp_" + digest[:32], digest


def validate_signal_proposal(proposal):
    """Validate a full TRL_SIGNAL_PROPOSAL.v1 document; return a clean copy."""
    _exact_keys(proposal, SIGNAL_PROPOSAL_FIELDS, "signal proposal")
    if proposal["schema_version"] != SIGNAL_PROPOSAL_SCHEMA:
        _fail("signal proposal schema is unsupported")
    if proposal["paper_only_status"] != PAPER_ONLY_STATUS:
        _fail("signal proposal must remain paper-only")
    proposal_id = proposal["proposal_id"]
    if not isinstance(proposal_id, str) or not _PROPOSAL_ID_PATTERN.fullmatch(proposal_id):
        _fail("proposal ID is invalid")
    side = proposal["side"]
    if side not in SIDES:
        _fail("proposal side must be one of {}".format(SIDES))

    if side in EXECUTABLE_SIDES:
        base = {key: proposal[key] for key in _R2005_BASE_FIELDS}
        base["schema_version"] = PAPER_PROPOSAL_SCHEMA
        base["proposal_id"] = paper_proposal_id_for(
            {key: value for key, value in base.items() if key != "proposal_id"}
        )
        try:
            clean_base = validate_paper_proposal(base)
        except PaperValidationError as error:
            raise SignalValidationError(str(error)) from error
    else:
        try:
            created = validate_utc_timestamp(proposal["created_at_utc"], "created_at_utc")
            observed = validate_utc_timestamp(proposal["observed_at_utc"], "observed_at_utc")
            expires = validate_utc_timestamp(proposal["expires_at_utc"], "expires_at_utc")
            instrument = validate_instrument(proposal["instrument"])
        except TimelineValidationError as error:
            raise SignalValidationError(str(error)) from error
        if created > observed or expires <= observed:
            _fail("proposal timestamps are not causally ordered")
        if proposal["entry_type"] != "WAIT":
            _fail("HOLD/WAIT/BLOCKED proposal must use WAIT entry type")
        executable_fields = (
            proposal["entry_zone_lower"],
            proposal["entry_zone_upper"],
            proposal["stop_loss"],
            proposal["targets"],
            proposal["target_allocations_percent"],
        )
        if any(value is not None for value in executable_fields):
            _fail("HOLD/WAIT/BLOCKED proposal cannot contain entry, stop or targets")
        risk_percent = decimal_value(proposal["risk_percent"], "risk_percent")
        if risk_percent != 0:
            _fail("HOLD/WAIT/BLOCKED proposal risk percent must be zero")
        evidence_status = proposal["evidence_quality_status"]
        if evidence_status not in EVIDENCE_QUALITY_STATUSES:
            _fail("evidence quality status is invalid")
        confidence = proposal["confidence_score"]
        if isinstance(confidence, bool) or not isinstance(confidence, int) or not 0 <= confidence <= 100:
            _fail("confidence score must be an integer from 0 through 100")
        wait_reason = _text(proposal["wait_reason"], "wait reason", 500)
        clean_base = dict(proposal)
        clean_base.update({
            "instrument": instrument,
            "invalidation_reason": _text(proposal["invalidation_reason"], "invalidation reason", 500),
            "beginner_explanation": _text(proposal["beginner_explanation"], "beginner explanation", 1200),
            "strategy_basis_ids": _basis_list(proposal["strategy_basis_ids"], "strategy basis IDs"),
            "research_basis_ids": _basis_list(proposal["research_basis_ids"], "research basis IDs"),
            "news_observation_ids": _timeline_id_list(proposal["news_observation_ids"], "news observation IDs"),
            "economic_event_observation_ids": _timeline_id_list(
                proposal["economic_event_observation_ids"], "economic-event observation IDs"
            ),
            "market_data_observation_id": _pattern_id(
                proposal["market_data_observation_id"], "market-data observation ID", _TIMELINE_ID_PATTERN
            ),
            "risk_percent": canonical_decimal(risk_percent),
            "evidence_quality_status": evidence_status,
            "wait_reason": wait_reason,
            "entry_zone_lower": None,
            "entry_zone_upper": None,
            "stop_loss": None,
            "targets": None,
            "target_allocations_percent": None,
        })

    if side == "BLOCKED":
        rejection_reasons = _bounded_reason_list(proposal["rejection_reasons"], "rejection reasons")
        if not rejection_reasons:
            _fail("BLOCKED proposal must carry at least one rejection reason")
        if any(code not in ROLE_FAILURE_REASON_CODES for code in rejection_reasons):
            _fail("rejection reasons must be governed role failure codes")
    else:
        rejection_reasons = _bounded_reason_list(proposal["rejection_reasons"], "rejection reasons")
        if rejection_reasons:
            _fail("rejection reasons must be empty unless side is BLOCKED")

    clean = dict(clean_base)

    clean["strategy_id"] = _pattern_id(proposal["strategy_id"], "strategy_id", _STRATEGY_ID_PATTERN)
    clean["strategy_version"] = _pattern_id(proposal["strategy_version"], "strategy_version", _SEMVER_PATTERN)
    try:
        clean["broker_native_instrument"] = validate_instrument(
            proposal["broker_native_instrument"], nullable=True
        )
    except TimelineValidationError as error:
        raise SignalValidationError(str(error)) from error
    if proposal["regime_classification"] not in REGIME_CLASSIFICATIONS:
        _fail("regime classification is not governed")
    clean["regime_classification"] = proposal["regime_classification"]
    clean["feature_snapshot_hash"] = _pattern_id(
        proposal["feature_snapshot_hash"], "feature_snapshot_hash", _HASH64_PATTERN
    )
    clean["data_quality_result"] = _role_result(
        proposal["data_quality_result"], "data_quality_result", ("PASS", "DATA_QUALITY_REJECTED")
    )
    news_result = _bounded_object(proposal["news_event_risk_result"], "news_event_risk_result")
    # NOT_EVALUATED covers a BLOCKED proposal that never reached Role 4
    # because an earlier mandatory role (1-3) already blocked the pipeline.
    if "status" not in news_result or news_result["status"] not in (
        "PASS", "NEWS_EVENT_RISK_BLOCK", "NOT_EVALUATED",
    ):
        _fail("news_event_risk_result status is not governed")
    if "reasons" not in news_result or not isinstance(news_result["reasons"], list):
        _fail("news_event_risk_result reasons must be a list")
    if "evidence_ids" not in news_result or not isinstance(news_result["evidence_ids"], list):
        _fail("news_event_risk_result evidence_ids must be a list")
    clean["news_event_risk_result"] = news_result
    calibration_source = _pattern_id(
        proposal["confidence_calibration_source"],
        "confidence_calibration_source",
        _CALIBRATION_SOURCE_PATTERN,
    )
    # Section 8: a calibration source that does not resolve to a real
    # stored record is rejected at schema validation, not published with
    # an unverifiable confidence number.
    if not signal_confidence.resolve_calibration_source(calibration_source):
        _fail("confidence_calibration_source does not resolve to a governed calibration record")
    clean["confidence_calibration_source"] = calibration_source
    expected_status = signal_confidence.confidence_status_for(calibration_source)
    if proposal["confidence_status"] not in signal_confidence.CONFIDENCE_STATUSES:
        _fail("confidence_status is not governed")
    if proposal["confidence_status"] != expected_status:
        _fail("confidence_status does not match the resolved calibration source")
    clean["confidence_status"] = proposal["confidence_status"]
    clean["explanation"] = _text(proposal["explanation"], "explanation", 1200)
    clean["rejection_reasons"] = rejection_reasons
    model_versions = _bounded_object(
        proposal["model_rule_versions"], "model_rule_versions",
        expected_keys=("strategy_version", "risk_engine_version", "pipeline_version"),
    )
    for key in ("strategy_version", "risk_engine_version", "pipeline_version"):
        if not isinstance(model_versions[key], str) or not _SEMVER_PATTERN.fullmatch(model_versions[key]):
            _fail("model_rule_versions.{} must be a semantic version".format(key))
    clean["model_rule_versions"] = model_versions
    role_results = _bounded_object(
        proposal["role_results"], "role_results", expected_keys=ROLE_NAMES
    )
    clean["role_results"] = role_results
    clean["candidate_quantity"] = _price(
        proposal["candidate_quantity"], "candidate_quantity", nullable=True
    )
    clean["independent_quantity"] = _price(
        proposal["independent_quantity"], "independent_quantity", nullable=True
    )
    if side in EXECUTABLE_SIDES:
        if clean["candidate_quantity"] is None or clean["independent_quantity"] is None:
            _fail("executable proposal requires both candidate and independent quantity")
    else:
        if clean["candidate_quantity"] is not None or clean["independent_quantity"] is not None:
            _fail("non-executable proposal cannot carry a sizing quantity")
    clean["maximum_spread"] = _price(proposal["maximum_spread"], "maximum_spread")
    clean["active_risk_policy_hash"] = _pattern_id(
        proposal["active_risk_policy_hash"], "active_risk_policy_hash", _HASH64_PATTERN
    )
    if proposal["operating_mode"] not in mode_service.MODES:
        _fail("operating_mode is not governed")
    clean["operating_mode"] = proposal["operating_mode"]
    if proposal["sample_label"] not in SAMPLE_LABELS:
        _fail("sample_label is not governed")
    clean["sample_label"] = proposal["sample_label"]

    clean["schema_version"] = SIGNAL_PROPOSAL_SCHEMA
    clean["paper_only_status"] = PAPER_ONLY_STATUS
    clean.pop("canonical_proposal_hash", None)
    clean.pop("proposal_id", None)
    proposal_id, digest = signal_proposal_id_for(clean)
    clean["proposal_id"] = proposal_id
    clean["canonical_proposal_hash"] = digest
    if proposal["proposal_id"] != proposal_id:
        _fail("proposal ID does not match canonical content")
    if proposal["canonical_proposal_hash"] != digest:
        _fail("canonical proposal hash does not match canonical content")
    return {key: clean[key] for key in SIGNAL_PROPOSAL_FIELDS}


def build_signal_proposal(**fields):
    """Build and validate a proposal with an identity derived from its content."""
    candidate = dict(fields)
    candidate["schema_version"] = SIGNAL_PROPOSAL_SCHEMA
    candidate["paper_only_status"] = PAPER_ONLY_STATUS
    identity_source = {
        key: value for key, value in candidate.items()
        if key not in ("proposal_id", "canonical_proposal_hash")
    }
    proposal_id, digest = signal_proposal_id_for(identity_source)
    candidate["proposal_id"] = proposal_id
    candidate["canonical_proposal_hash"] = digest
    return validate_signal_proposal(candidate)


EVALUATION_REQUEST_SCHEMA = "TRL_SIGNAL_EVALUATION_REQUEST.v1"
BAR_FIELDS = ("date", "open", "high", "low", "close", "volume")
MIN_BARS = 2
MAX_BARS = 500
MAX_MODEL_HYPOTHESIS_LENGTH = 2000

_CORRELATION_GROUP_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{0,31}$")


def validate_bar_series(bars, instrument, evaluated_at_utc):
    """Validate a governed, causal, chronologically ascending OHLCV series.

    Returns (clean_bars, feature_material) where feature_material is the
    exact JSON-serializable structure hashed into ``feature_snapshot_hash``.
    """
    if not isinstance(bars, list) or not MIN_BARS <= len(bars) <= MAX_BARS:
        _fail("bar_series must contain from {} through {} bars".format(MIN_BARS, MAX_BARS))
    try:
        evaluated = validate_utc_timestamp(evaluated_at_utc, "evaluated_at_utc")
    except TimelineValidationError as error:
        raise SignalValidationError(str(error)) from error
    clean = []
    previous_date = None
    for bar in bars:
        if not isinstance(bar, dict) or set(bar) != set(BAR_FIELDS):
            _fail("bar_series entry has an invalid field set")
        try:
            bar_date = validate_utc_timestamp(bar["date"], "bar date")
        except TimelineValidationError as error:
            raise SignalValidationError(str(error)) from error
        if bar_date > evaluated:
            _fail("bar_series contains a future-dated (non-causal) bar")
        if previous_date is not None and bar_date <= previous_date:
            _fail("bar_series must be strictly chronologically ascending")
        previous_date = bar_date
        clean_bar = {"date": bar["date"]}
        for field in ("open", "high", "low", "close"):
            clean_bar[field] = _price(bar[field], "bar {}".format(field))
        clean_bar["volume"] = canonical_decimal(bar["volume"], "bar volume", positive=True, allow_zero=True)
        high = decimal_value(clean_bar["high"])
        low = decimal_value(clean_bar["low"])
        openv = decimal_value(clean_bar["open"])
        closev = decimal_value(clean_bar["close"])
        if low > min(openv, closev) or high < max(openv, closev) or low > high:
            _fail("bar_series OHLC ordering is invalid")
        clean.append(clean_bar)
    try:
        clean_instrument = validate_instrument(instrument)
    except TimelineValidationError as error:
        raise SignalValidationError(str(error)) from error
    feature_material = {
        "instrument": clean_instrument,
        "evaluated_at_utc": evaluated_at_utc,
        "bars": clean,
    }
    return clean, feature_material


def feature_snapshot_hash_for(feature_material):
    return sha256_text(deterministic_json_text(feature_material))


def validate_account_state(payload):
    expected = (
        "schema_version", "equity", "risk_halt", "risk_halt_reason",
        "open_positions", "last_closed_trade_realized_pnl_negative",
        "last_closed_trade_risk_percent",
    )
    _exact_keys(payload, expected, "account state")
    if payload["schema_version"] != "TRL_SIGNAL_ACCOUNT_STATE.v1":
        _fail("account state schema is unsupported")
    clean = {"schema_version": payload["schema_version"]}
    clean["equity"] = _price(payload["equity"], "equity")
    if not isinstance(payload["risk_halt"], bool):
        _fail("risk_halt must be a boolean")
    clean["risk_halt"] = payload["risk_halt"]
    reason = payload["risk_halt_reason"]
    if clean["risk_halt"]:
        clean["risk_halt_reason"] = _text(reason, "risk_halt_reason", 200)
    else:
        if reason is not None:
            _fail("risk_halt_reason must be null when risk_halt is false")
        clean["risk_halt_reason"] = None
    positions = payload["open_positions"]
    if not isinstance(positions, list) or len(positions) > 32:
        _fail("open_positions must be a bounded list")
    clean_positions = []
    for item in positions:
        if not isinstance(item, dict) or set(item) != {"instrument", "correlation_group"}:
            _fail("open_positions entry has an invalid field set")
        try:
            clean_position_instrument = validate_instrument(item["instrument"])
        except TimelineValidationError as error:
            raise SignalValidationError(str(error)) from error
        clean_positions.append({
            "instrument": clean_position_instrument,
            "correlation_group": _pattern_id(
                item["correlation_group"], "correlation_group", _CORRELATION_GROUP_PATTERN
            ),
        })
    clean["open_positions"] = clean_positions
    if not isinstance(payload["last_closed_trade_realized_pnl_negative"], bool):
        _fail("last_closed_trade_realized_pnl_negative must be a boolean")
    clean["last_closed_trade_realized_pnl_negative"] = payload["last_closed_trade_realized_pnl_negative"]
    risk_pct = payload["last_closed_trade_risk_percent"]
    clean["last_closed_trade_risk_percent"] = (
        None if risk_pct is None
        else canonical_decimal(risk_pct, "last_closed_trade_risk_percent", positive=True, allow_zero=False)
    )
    return clean


def validate_risk_policy(payload):
    expected = (
        "schema_version", "risk_percent", "maximum_spread",
        "maximum_correlated_positions", "quantity_step_tolerance_percent",
    )
    _exact_keys(payload, expected, "risk policy")
    if payload["schema_version"] != "TRL_SIGNAL_RISK_POLICY.v1":
        _fail("risk policy schema is unsupported")
    risk_percent = decimal_value(payload["risk_percent"], "risk_percent")
    if risk_percent <= 0 or risk_percent > MAX_RISK_PERCENT:
        _fail("risk_percent is outside its governed range")
    maximum_correlated = payload["maximum_correlated_positions"]
    if (
        isinstance(maximum_correlated, bool)
        or not isinstance(maximum_correlated, int)
        or not 1 <= maximum_correlated <= 10
    ):
        _fail("maximum_correlated_positions is outside its governed range")
    tolerance = decimal_value(payload["quantity_step_tolerance_percent"], "quantity_step_tolerance_percent")
    if tolerance < 0 or tolerance > Decimal("5"):
        _fail("quantity_step_tolerance_percent is outside its governed range")
    clean = {
        "schema_version": payload["schema_version"],
        "risk_percent": canonical_decimal(risk_percent),
        "maximum_spread": _price(payload["maximum_spread"], "maximum_spread"),
        "maximum_correlated_positions": maximum_correlated,
        "quantity_step_tolerance_percent": canonical_decimal(tolerance),
    }
    return clean


def risk_policy_hash(clean_risk_policy):
    return sha256_text(deterministic_json_text(clean_risk_policy))


def validate_news_context(payload, evaluated_at_utc):
    expected = ("schema_version", "elevated_risk", "reason", "evidence_ids", "as_of_utc")
    _exact_keys(payload, expected, "news context")
    if payload["schema_version"] != "TRL_SIGNAL_NEWS_CONTEXT.v1":
        _fail("news context schema is unsupported")
    if not isinstance(payload["elevated_risk"], bool):
        _fail("elevated_risk must be a boolean")
    try:
        as_of = validate_utc_timestamp(payload["as_of_utc"], "as_of_utc")
        evaluated = validate_utc_timestamp(evaluated_at_utc, "evaluated_at_utc")
    except TimelineValidationError as error:
        raise SignalValidationError(str(error)) from error
    if as_of > evaluated:
        _fail("news context as_of_utc is from the future")
    clean = {
        "schema_version": payload["schema_version"],
        "elevated_risk": payload["elevated_risk"],
        "reason": (
            _text(payload["reason"], "news context reason", 500)
            if payload["elevated_risk"] else None
        ),
        "evidence_ids": _timeline_id_list(payload["evidence_ids"], "news context evidence_ids"),
        "as_of_utc": payload["as_of_utc"],
    }
    if not payload["elevated_risk"] and payload["reason"] is not None:
        _fail("news context reason must be null when elevated_risk is false")
    return clean


def validate_session_window(payload):
    expected = ("schema_version", "status", "reason_code")
    _exact_keys(payload, expected, "session window")
    if payload["schema_version"] != "TRL_SIGNAL_SESSION_WINDOW.v1":
        _fail("session window schema is unsupported")
    if payload["status"] not in ("OPEN", "CLOSED"):
        _fail("session window status is not governed")
    clean = {"schema_version": payload["schema_version"], "status": payload["status"]}
    if payload["status"] == "CLOSED":
        clean["reason_code"] = _pattern_id(
            payload["reason_code"], "session window reason_code", _REASON_CODE_PATTERN
        )
    else:
        if payload["reason_code"] is not None:
            _fail("session window reason_code must be null when status is OPEN")
        clean["reason_code"] = None
    return clean


EVALUATION_REQUEST_FIELDS = (
    "schema_version",
    "instrument",
    "strategy_id",
    "strategy_parameters",
    "evaluated_at_utc",
    "expires_after_seconds",
    "bar_series",
    "market_observation",
    "market_data_observation_id",
    "market_observation_occurred_at_utc",
    "market_observation_first_observed_at_utc",
    "instrument_allowlisted",
    "broker_native_instrument",
    "account_state",
    "risk_policy",
    "news_context",
    "session_window",
    "sample_label",
    "model_hypothesis",
)


def validate_evaluation_request(payload):
    """Validate the single governed envelope the CLI/service pass to the
    pipeline. Each embedded sub-object is validated by its own governed
    validator; this function only owns the envelope shape and cross-field
    causal ordering."""
    _exact_keys(payload, EVALUATION_REQUEST_FIELDS, "signal evaluation request")
    if payload["schema_version"] != EVALUATION_REQUEST_SCHEMA:
        _fail("signal evaluation request schema is unsupported")
    instrument = validate_instrument(payload["instrument"])
    strategy_id = _pattern_id(payload["strategy_id"], "strategy_id", _STRATEGY_ID_PATTERN)
    strategy_parameters = _bounded_object(payload["strategy_parameters"], "strategy_parameters")
    try:
        evaluated_at = validate_utc_timestamp(payload["evaluated_at_utc"], "evaluated_at_utc")
        occurred_at = validate_utc_timestamp(
            payload["market_observation_occurred_at_utc"], "market_observation_occurred_at_utc"
        )
        observed_at = validate_utc_timestamp(
            payload["market_observation_first_observed_at_utc"],
            "market_observation_first_observed_at_utc",
        )
    except TimelineValidationError as error:
        raise SignalValidationError(str(error)) from error
    if observed_at > evaluated_at:
        _fail("market observation is from the future relative to the evaluation time")
    expires_after = payload["expires_after_seconds"]
    if isinstance(expires_after, bool) or not isinstance(expires_after, int) or not 60 <= expires_after <= 86400:
        _fail("expires_after_seconds is outside its governed range")
    bar_series, feature_material = validate_bar_series(
        payload["bar_series"], instrument, payload["evaluated_at_utc"]
    )
    try:
        market_observation = validate_market_observation(payload["market_observation"], instrument)
    except PaperValidationError as error:
        raise SignalValidationError(str(error)) from error
    market_data_observation_id = _pattern_id(
        payload["market_data_observation_id"], "market_data_observation_id", _TIMELINE_ID_PATTERN
    )
    if not isinstance(payload["instrument_allowlisted"], bool):
        _fail("instrument_allowlisted must be a boolean")
    try:
        broker_native_instrument = validate_instrument(payload["broker_native_instrument"], nullable=True)
    except TimelineValidationError as error:
        raise SignalValidationError(str(error)) from error
    account_state = validate_account_state(payload["account_state"])
    policy = validate_risk_policy(payload["risk_policy"])
    news_context = validate_news_context(payload["news_context"], payload["evaluated_at_utc"])
    session_window = validate_session_window(payload["session_window"])
    if payload["sample_label"] not in SAMPLE_LABELS:
        _fail("sample_label is not governed")
    model_hypothesis = payload["model_hypothesis"]
    if model_hypothesis is not None:
        if not isinstance(model_hypothesis, str) or len(model_hypothesis) > MAX_MODEL_HYPOTHESIS_LENGTH:
            _fail("model_hypothesis must be a bounded string when present")
    return {
        "schema_version": EVALUATION_REQUEST_SCHEMA,
        "instrument": instrument,
        "strategy_id": strategy_id,
        "strategy_parameters": strategy_parameters,
        "evaluated_at_utc": payload["evaluated_at_utc"],
        "expires_after_seconds": expires_after,
        "bar_series": bar_series,
        "feature_material": feature_material,
        "market_observation": market_observation,
        "market_data_observation_id": market_data_observation_id,
        "market_observation_occurred_at_utc": payload["market_observation_occurred_at_utc"],
        "market_observation_first_observed_at_utc": payload["market_observation_first_observed_at_utc"],
        "instrument_allowlisted": payload["instrument_allowlisted"],
        "broker_native_instrument": broker_native_instrument,
        "account_state": account_state,
        "risk_policy": policy,
        "news_context": news_context,
        "session_window": session_window,
        "sample_label": payload["sample_label"],
        "model_hypothesis": model_hypothesis,
    }


__all__ = (
    "ENTRY_TYPES",
    "EVALUATION_REQUEST_SCHEMA",
    "EVIDENCE_QUALITY_STATUSES",
    "EXECUTABLE_SIDES",
    "MAX_BARS",
    "MIN_BARS",
    "REGIME_CLASSIFICATIONS",
    "ROLE_FAILURE_REASON_CODES",
    "ROLE_NAMES",
    "SAMPLE_LABELS",
    "SIDES",
    "SIGNAL_PROPOSAL_FIELDS",
    "SIGNAL_PROPOSAL_SCHEMA",
    "WAIT_SHAPED_SIDES",
    "SignalValidationError",
    "build_signal_proposal",
    "feature_snapshot_hash_for",
    "risk_policy_hash",
    "signal_proposal_id_for",
    "validate_account_state",
    "validate_bar_series",
    "validate_evaluation_request",
    "validate_news_context",
    "validate_risk_policy",
    "validate_session_window",
    "validate_signal_proposal",
)
