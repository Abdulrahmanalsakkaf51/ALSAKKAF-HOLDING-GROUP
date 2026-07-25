# -*- coding: utf-8 -*-
"""Fail-closed validation for packs, instruments, bars, and strategies."""
import datetime
import math

from .canonical import (
    _allocation_validation_error,
    _canonical_dump,
    _finite_float,
    _is_number,
    _nonempty_string,
    _safe_for_hash,
)
from .constants import (
    DRAWDOWN_HALT_PCT,
    MAX_POSITION_PCT,
    STRATEGY_FAMILY,
    STRATEGY_ID,
    STRATEGY_STATUS,
    STRATEGY_VERSION,
    SUPPORTED_ASSET_CLASSES,
    _BAR_FIELDS,
    _INSTRUMENT_FIELDS,
    _MAX_CANONICAL_INTEGER_BITS,
    _MAX_SAFE_INPUT_MAGNITUDE,
    _MIN_SAFE_PRICE,
    _PACK_ALLOWED,
    _PACK_REQUIRED,
    _SEMVER,
    _STRATEGY_ALLOWED,
    _STRATEGY_REQUIRED,
)

def _field_list(values):
    labels = []
    for value in values:
        if (type(value) is int
                and value.bit_length() > _MAX_CANONICAL_INTEGER_BITS):
            labels.append(_canonical_dump(_safe_for_hash(value)))
        elif type(value) in (str, int, float, bool) or value is None:
            labels.append(_canonical_dump(_safe_for_hash(value)))
        else:
            labels.append("<unsupported %s>" % type(value).__name__)
    return ", ".join(sorted(labels))


def _parse_iso(value, field_name, errors):
    if not _nonempty_string(value):
        errors.append("%s must be a non-empty ISO date or timestamp" % field_name)
        return None
    candidate = value
    try:
        if "T" not in candidate and " " not in candidate:
            parsed = datetime.datetime.combine(
                datetime.date.fromisoformat(candidate), datetime.time(),
                tzinfo=datetime.timezone.utc,
            )
        else:
            parsed = datetime.datetime.fromisoformat(candidate.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=datetime.timezone.utc)
            parsed = parsed.astimezone(datetime.timezone.utc)
    except (ValueError, OverflowError):
        errors.append("%s must be a valid ISO date or timestamp" % field_name)
        return None
    return parsed


def validate_market_pack(historical_pack):
    """Return a deterministic list of data-contract violations."""
    errors = []
    if type(historical_pack) is not dict:
        return ["pack must be an exact built-in dictionary"]
    if not all(type(key) is str for key in historical_pack):
        return ["pack field names must be exact built-in strings"]
    keys = frozenset(historical_pack)
    missing = _PACK_REQUIRED - keys
    extra = keys - _PACK_ALLOWED
    if missing:
        errors.append("pack missing required fields: %s" % _field_list(missing))
    if extra:
        errors.append("pack has unsupported fields: %s" % _field_list(extra))
    if "pack_id" in historical_pack and not _nonempty_string(historical_pack["pack_id"]):
        errors.append("pack_id must be a non-empty string")
    if "prepared_by" in historical_pack and not _nonempty_string(historical_pack["prepared_by"]):
        errors.append("prepared_by must be a non-empty string")
    if "note" in historical_pack and not _nonempty_string(historical_pack["note"]):
        errors.append("note must be a non-empty string when supplied")
    if "as_of" in historical_pack:
        _parse_iso(historical_pack["as_of"], "as_of", errors)

    instruments = historical_pack.get("instruments")
    if type(instruments) is not list:
        errors.append("instruments must be an exact built-in list containing exactly one instrument")
        return errors
    if len(instruments) != 1:
        errors.append("instruments must contain exactly one instrument")
        return errors
    instrument = instruments[0]
    if type(instrument) is not dict:
        errors.append("instrument must be an exact built-in dictionary")
        return errors
    if not all(type(key) is str for key in instrument):
        errors.append("instrument field names must be exact built-in strings")
        return errors
    instrument_keys = frozenset(instrument)
    missing = _INSTRUMENT_FIELDS - instrument_keys
    extra = instrument_keys - _INSTRUMENT_FIELDS
    if missing:
        errors.append("instrument missing required fields: %s" % _field_list(missing))
    if extra:
        errors.append("instrument has unsupported fields: %s" % _field_list(extra))
    for field in ("symbol", "data_source", "data_quality_note"):
        if field in instrument and not _nonempty_string(instrument[field]):
            errors.append("instrument %s must be a non-empty string" % field)
    if "asset_class" in instrument:
        if (type(instrument["asset_class"]) is not str
                or instrument["asset_class"] not in SUPPORTED_ASSET_CLASSES):
            errors.append("unsupported asset_class: %s" %
                          _field_list((instrument["asset_class"],)))

    bars = instrument.get("ohlcv")
    if type(bars) is not list or not bars:
        errors.append("ohlcv must be a non-empty exact built-in list")
        return errors
    prior_timestamp = None
    for index, bar in enumerate(bars):
        prefix = "bar[%d]" % index
        if type(bar) is not dict:
            errors.append("%s must be an exact built-in dictionary" % prefix)
            continue
        if not all(type(key) is str for key in bar):
            errors.append("%s field names must be exact built-in strings" % prefix)
            continue
        bar_keys = frozenset(bar)
        missing = _BAR_FIELDS - bar_keys
        extra = bar_keys - _BAR_FIELDS
        if missing:
            errors.append("%s missing required fields: %s" %
                          (prefix, _field_list(missing)))
        if extra:
            errors.append("%s has unsupported fields: %s" %
                          (prefix, _field_list(extra)))
        timestamp = None
        if "date" in bar:
            timestamp = _parse_iso(bar["date"], "%s.date" % prefix, errors)
        if timestamp is not None and prior_timestamp is not None:
            if timestamp == prior_timestamp:
                errors.append("%s.date duplicates the prior timestamp" % prefix)
            elif timestamp < prior_timestamp:
                errors.append("%s.date is out of chronological order" % prefix)
        if timestamp is not None:
            prior_timestamp = timestamp
        raw_ohlc = {}
        for field in ("open", "high", "low", "close"):
            value = bar.get(field)
            if (_is_number(value)
                    and (type(value) is int or math.isfinite(value))):
                raw_ohlc[field] = value
        if len(raw_ohlc) == 4:
            if raw_ohlc["high"] < max(raw_ohlc["open"], raw_ohlc["close"]):
                errors.append("%s.high must be >= max(open, close)" % prefix)
            if raw_ohlc["low"] > min(raw_ohlc["open"], raw_ohlc["close"]):
                errors.append("%s.low must be <= min(open, close)" % prefix)
            if raw_ohlc["high"] < raw_ohlc["low"]:
                errors.append("%s.high must be >= low" % prefix)

        numeric_ok = {}
        numeric_values = {}
        for field in ("open", "high", "low", "close", "volume"):
            if field not in bar:
                numeric_ok[field] = False
                continue
            value = bar[field]
            converted = _finite_float(value)
            if not _is_number(value):
                errors.append("%s.%s must be numeric and not boolean" % (prefix, field))
                numeric_ok[field] = False
            elif converted is None:
                errors.append(
                    "%s.%s must convert to a finite float without numeric loss"
                    % (prefix, field)
                )
                numeric_ok[field] = False
            elif abs(converted) > _MAX_SAFE_INPUT_MAGNITUDE:
                errors.append("%s.%s exceeds the safe calculation range" %
                              (prefix, field))
                numeric_ok[field] = False
            else:
                numeric_ok[field] = True
                numeric_values[field] = converted
        for field in ("open", "high", "low", "close"):
            if numeric_ok.get(field) and numeric_values[field] < _MIN_SAFE_PRICE:
                errors.append("%s.%s must be positive and within the safe calculation range" %
                              (prefix, field))
                numeric_ok[field] = False
        if numeric_ok.get("volume") and numeric_values["volume"] < 0:
            errors.append("%s.volume must be nonnegative" % prefix)
    return errors


def _coerce_single_strategy(strategy_rules):
    if type(strategy_rules) is dict:
        return strategy_rules, []
    if isinstance(strategy_rules, dict):
        return None, ["strategy must be an exact built-in dictionary"]
    if type(strategy_rules) is list and len(strategy_rules) == 1:
        return strategy_rules[0], []
    return None, ["exactly one declarative strategy object is required"]


def validate_strategy(strategy_rules, instrument_symbol=None):
    rule, errors = _coerce_single_strategy(strategy_rules)
    if errors:
        return None, errors, None
    if type(rule) is not dict:
        return None, ["strategy must be an exact built-in dictionary"], None
    if not all(type(key) is str for key in rule):
        return rule, ["strategy field names must be exact built-in strings"], None
    keys = frozenset(rule)
    missing = _STRATEGY_REQUIRED - keys
    extra = keys - _STRATEGY_ALLOWED
    if missing:
        errors.append("strategy missing required fields: %s" % _field_list(missing))
    if extra:
        errors.append("strategy has unsupported fields: %s" % _field_list(extra))
    if type(rule.get("strategy_id")) is not str:
        errors.append("strategy_id must be an exact built-in string")
    elif rule["strategy_id"] != STRATEGY_ID:
        errors.append("unsupported strategy_id")
    if type(rule.get("strategy_version")) is not str:
        errors.append("strategy_version must be an exact built-in string")
    elif rule["strategy_version"] != STRATEGY_VERSION:
        errors.append("unsupported strategy_version")
    elif not _SEMVER.match(rule["strategy_version"]):
        errors.append("strategy_version must be semantic version text")
    if type(rule.get("family")) is not str:
        errors.append("strategy family must be an exact built-in string")
    elif rule["family"] != STRATEGY_FAMILY:
        errors.append("unsupported strategy family")
    if "lifecycle_status" in rule:
        if type(rule["lifecycle_status"]) is not str:
            errors.append("strategy lifecycle_status must be an exact built-in string")
        elif rule["lifecycle_status"] != STRATEGY_STATUS:
            errors.append("unsupported strategy lifecycle_status")
    for field in ("name", "author", "review_status"):
        if field in rule and not _nonempty_string(rule[field]):
            errors.append("strategy %s must be a non-empty string" % field)
    if not _nonempty_string(rule.get("symbol")):
        errors.append("strategy symbol must be a non-empty string")
    elif instrument_symbol is not None and rule["symbol"] != instrument_symbol:
        errors.append("strategy symbol does not match instrument symbol")
    for field in ("fast", "slow"):
        value = rule.get(field)
        if type(value) is not int or value <= 0:
            errors.append("strategy %s must be a positive integer" % field)
        elif value.bit_length() > _MAX_CANONICAL_INTEGER_BITS:
            errors.append("strategy %s exceeds the supported integer range" % field)
    if (type(rule.get("fast")) is int and type(rule.get("slow")) is int
            and rule["fast"] > 0 and rule["slow"] > 0
            and rule["fast"] >= rule["slow"]):
        errors.append("strategy fast must be less than slow")
    size = rule.get("paper_size_pct")
    position_limit = None
    safe_size = _finite_float(size)
    if safe_size is None or safe_size <= 0:
        errors.append("strategy paper_size_pct must be finite and positive")
    elif safe_size > MAX_POSITION_PCT:
        position_limit = "requested paper_size_pct exceeds the 5% system maximum"
    else:
        allocation_error = _allocation_validation_error(safe_size)
        if allocation_error:
            errors.append(allocation_error)
    if "drawdown_halt_pct" in rule:
        threshold = rule["drawdown_halt_pct"]
        safe_threshold = _finite_float(threshold)
        if safe_threshold is None or safe_threshold >= 0:
            errors.append("strategy drawdown_halt_pct must be finite and negative")
        elif safe_threshold < DRAWDOWN_HALT_PCT:
            errors.append("strategy drawdown_halt_pct may not weaken the -15% system halt")
    return rule, errors, position_limit
