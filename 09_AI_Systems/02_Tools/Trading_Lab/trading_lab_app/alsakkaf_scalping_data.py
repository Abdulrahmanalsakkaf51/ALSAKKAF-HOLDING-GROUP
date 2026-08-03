"""Governed schemas, deterministic identities, and symbol-map storage for
ALSAKKAF SCALPING (TRL-R2-012).

Mirrors the identity pattern used throughout this repository:
``"<prefix>_" + sha256("<DOMAIN>.v1\\n" + canonical_json(fields))[:32]``,
built on the existing ``timeline_data`` canonical/Decimal helpers so no
numeric policy is reinvented. This module never imports ``MetaTrader5``
and never connects to a broker.
"""

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_EVEN
import json
import os
from pathlib import Path
import tempfile

from .timeline_data import (
    TimelineValidationError,
    canonical_decimal,
    deterministic_json_text,
    sha256_text,
    validate_utc_timestamp,
)


class ScalpingDataValidationError(ValueError):
    """A stable, non-secret ALSAKKAF SCALPING data validation failure."""


# Reused verbatim from TRL-R2-010/TRL-R2-011 (Section 6 of the R2-012
# contract) -- no alias is ever silently normalized.
CANONICAL_INSTRUMENTS = ("XAUUSD", "NAS100", "EURUSD", "GBPUSD", "USDJPY")

PROFILE_IDS = (
    "ALSAKKAF_PRECISION_SCALPING",
    "ALSAKKAF_BREAKOUT_LADDER",
    "ALSAKKAF_INTRADAY",
)

SIDES = ("BUY", "SELL")
SIDE_RESTRICTIONS = ("BUY_ONLY", "SELL_ONLY", "BOTH")

PRODUCT_STATES = ("OFF", "ANALYZE_ONLY", "DEMO_AUTO", "PAUSED", "EMERGENCY_STOP")

CYCLE_STATES = (
    "PLANNED", "CHECKED", "ARMED", "PARTIALLY_TRIGGERED", "ACTIVE",
    "COMPLETED", "CANCELLED", "EXPIRED", "BLOCKED", "UNCERTAIN",
    "EMERGENCY_STOPPED",
)

ORDER_PLAN_TYPES = ("MARKET", "BUY_STOP", "SELL_STOP")

ALSAKKAF_SCALPING_MAGIC = 384512
COMMENT_PREFIX = "ALSAKKAF_SCALPING"
MAX_BROKER_COMMENT_LENGTH = 31  # MT5's own comment field bound.


def quantize_4(value):
    return Decimal(value).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)


def _stable_id(prefix, domain, fields):
    material = domain + ".v1\n" + deterministic_json_text(fields)
    return prefix + sha256_text(material)[:32]


def _require_choice(value, choices, field):
    if value not in choices:
        raise ScalpingDataValidationError("{} must be one of {}".format(field, choices))
    return value


def _bounded_text(value, field, maximum=256, allow_empty=False):
    if not isinstance(value, str):
        raise ScalpingDataValidationError("{} must be a string".format(field))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ScalpingDataValidationError("{} contains a control character".format(field))
    if not allow_empty and not value:
        raise ScalpingDataValidationError("{} must not be empty".format(field))
    if len(value) > maximum:
        raise ScalpingDataValidationError("{} exceeds the length bound".format(field))
    return value


def validate_canonical_instrument(value):
    return _require_choice(value, CANONICAL_INSTRUMENTS, "instrument")


def validate_profile_id(value):
    return _require_choice(value, PROFILE_IDS, "profile_id")


def broker_comment():
    """The fixed, ownership-identifying comment written on every order."""
    return COMMENT_PREFIX[:MAX_BROKER_COMMENT_LENGTH]


# --------------------------------------------------------------------------
# TRL_SCALPING_ORDER_PLAN.v1
# --------------------------------------------------------------------------

_ORDER_PLAN_FIELDS = (
    "schema_version", "order_plan_id", "canonical_instrument", "broker_symbol",
    "side", "order_type", "profile_id", "entry_price", "stop_price",
    "ordered_target_prices", "ordered_target_allocations_pct", "lots",
    "magic_number", "comment", "risk_amount", "created_at_utc",
)


def build_order_plan(
    canonical_instrument, broker_symbol, side, order_type, profile_id,
    entry_price, stop_price, ordered_target_prices,
    ordered_target_allocations_pct, lots, risk_amount, created_at_utc,
):
    validate_canonical_instrument(canonical_instrument)
    _bounded_text(broker_symbol, "broker_symbol", maximum=32)
    _require_choice(side, SIDES, "side")
    _require_choice(order_type, ORDER_PLAN_TYPES, "order_type")
    validate_profile_id(profile_id)
    entry_price = canonical_decimal(entry_price, "entry_price", positive=True, allow_zero=False)
    stop_price = canonical_decimal(stop_price, "stop_price", positive=True, allow_zero=False)
    if Decimal(entry_price) == Decimal(stop_price):
        raise ScalpingDataValidationError("stop_price must differ from entry_price")
    targets = [
        canonical_decimal(price, "target_price", positive=True, allow_zero=False)
        for price in ordered_target_prices
    ]
    if not (1 <= len(targets) <= 3):
        raise ScalpingDataValidationError("ordered_target_prices must contain 1-3 entries")
    allocations = [
        canonical_decimal(pct, "target_allocation_pct", positive=True, allow_zero=False)
        for pct in ordered_target_allocations_pct
    ]
    if len(allocations) != len(targets):
        raise ScalpingDataValidationError("target allocations must match target count")
    total_allocation = sum(Decimal(item) for item in allocations)
    if total_allocation != Decimal("100"):
        raise ScalpingDataValidationError("target allocations must sum to exactly 100")
    lots = canonical_decimal(lots, "lots", positive=True, allow_zero=False)
    risk_amount = canonical_decimal(risk_amount, "risk_amount", positive=True, allow_zero=True)
    validate_utc_timestamp(created_at_utc, "created_at_utc")

    identity_fields = {
        "canonical_instrument": canonical_instrument, "broker_symbol": broker_symbol,
        "side": side, "order_type": order_type, "profile_id": profile_id,
        "entry_price": entry_price, "stop_price": stop_price,
        "ordered_target_prices": targets,
        "ordered_target_allocations_pct": allocations, "lots": lots,
        "magic_number": ALSAKKAF_SCALPING_MAGIC, "comment": broker_comment(),
        "risk_amount": risk_amount,
    }
    order_plan_id = _stable_id("plan_", "TRL-SCALPING-ORDER-PLAN-ID", identity_fields)
    plan = dict(identity_fields)
    plan.update({
        "schema_version": "TRL_SCALPING_ORDER_PLAN.v1",
        "order_plan_id": order_plan_id,
        "created_at_utc": created_at_utc,
    })
    return validate_order_plan(plan)


def validate_order_plan(plan):
    if not isinstance(plan, dict) or set(plan) != set(_ORDER_PLAN_FIELDS):
        raise ScalpingDataValidationError("order plan has an invalid field set")
    if plan["schema_version"] != "TRL_SCALPING_ORDER_PLAN.v1":
        raise ScalpingDataValidationError("order plan schema is unsupported")
    identity_fields = {
        key: plan[key] for key in (
            "canonical_instrument", "broker_symbol", "side", "order_type",
            "profile_id", "entry_price", "stop_price", "ordered_target_prices",
            "ordered_target_allocations_pct", "lots", "magic_number", "comment",
            "risk_amount",
        )
    }
    expected_id = _stable_id("plan_", "TRL-SCALPING-ORDER-PLAN-ID", identity_fields)
    if plan["order_plan_id"] != expected_id:
        raise ScalpingDataValidationError("order plan identity mismatch")
    if plan["magic_number"] != ALSAKKAF_SCALPING_MAGIC:
        raise ScalpingDataValidationError("order plan magic number is not owned by ALSAKKAF SCALPING")
    if plan["comment"] != broker_comment():
        raise ScalpingDataValidationError("order plan comment is not owned by ALSAKKAF SCALPING")
    return deepcopy(plan)


# --------------------------------------------------------------------------
# TRL_SCALPING_CYCLE.v1
# --------------------------------------------------------------------------

_CYCLE_FIELDS = (
    "schema_version", "cycle_id", "canonical_instrument", "broker_symbol",
    "profile_id", "reference_price", "reference_atr", "reference_spread",
    "order_plan_ids", "expiry_utc", "total_risk_amount",
    "unallocated_risk_remainder", "state", "created_at_utc",
)


def build_cycle(
    canonical_instrument, broker_symbol, profile_id, reference_price,
    reference_atr, reference_spread, order_plan_ids, expiry_utc,
    total_risk_amount, unallocated_risk_remainder, created_at_utc,
):
    validate_canonical_instrument(canonical_instrument)
    _bounded_text(broker_symbol, "broker_symbol", maximum=32)
    validate_profile_id(profile_id)
    reference_price = canonical_decimal(reference_price, "reference_price", positive=True, allow_zero=False)
    reference_atr = canonical_decimal(reference_atr, "reference_atr", positive=True, allow_zero=True)
    reference_spread = canonical_decimal(reference_spread, "reference_spread", positive=True, allow_zero=True)
    if not order_plan_ids or len(order_plan_ids) > 6:
        raise ScalpingDataValidationError("cycle requires 1-6 order plans")
    for plan_id in order_plan_ids:
        _bounded_text(plan_id, "order_plan_id", maximum=48)
    validate_utc_timestamp(expiry_utc, "expiry_utc")
    total_risk_amount = canonical_decimal(total_risk_amount, "total_risk_amount", positive=True, allow_zero=True)
    unallocated_risk_remainder = canonical_decimal(
        unallocated_risk_remainder, "unallocated_risk_remainder", positive=True, allow_zero=True,
    )
    created_at_utc = created_at_utc
    validate_utc_timestamp(created_at_utc, "created_at_utc")

    identity_fields = {
        "canonical_instrument": canonical_instrument, "broker_symbol": broker_symbol,
        "profile_id": profile_id, "reference_price": reference_price,
        "reference_atr": reference_atr, "reference_spread": reference_spread,
        "order_plan_ids": list(order_plan_ids), "expiry_utc": expiry_utc,
        "total_risk_amount": total_risk_amount,
        "unallocated_risk_remainder": unallocated_risk_remainder,
    }
    cycle_id = _stable_id("cyc_", "TRL-SCALPING-CYCLE-ID", identity_fields)
    cycle = dict(identity_fields)
    cycle.update({
        "schema_version": "TRL_SCALPING_CYCLE.v1",
        "cycle_id": cycle_id,
        "state": "PLANNED",
        "created_at_utc": created_at_utc,
    })
    return validate_cycle(cycle)


def validate_cycle(cycle):
    if not isinstance(cycle, dict) or set(cycle) != set(_CYCLE_FIELDS):
        raise ScalpingDataValidationError("cycle has an invalid field set")
    if cycle["schema_version"] != "TRL_SCALPING_CYCLE.v1":
        raise ScalpingDataValidationError("cycle schema is unsupported")
    _require_choice(cycle["state"], CYCLE_STATES, "cycle state")
    return deepcopy(cycle)


# --------------------------------------------------------------------------
# Symbol map + event-risk block store (local, editable only while OFF)
# --------------------------------------------------------------------------

SYMBOL_MAP_SCHEMA = "TRL_SCALPING_SYMBOL_MAP.v1"


def default_symbol_map_path():
    local_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return root / "ALSAKKAF" / "TradingLab" / "scalping-symbol-map-v1.json"


def empty_symbol_map_document():
    return {
        "schema_version": SYMBOL_MAP_SCHEMA,
        "mappings": {},
        "event_risk_blocked": {},
    }


def validate_symbol_map_document(document):
    if not isinstance(document, dict) or set(document) != {
        "schema_version", "mappings", "event_risk_blocked",
    }:
        raise ScalpingDataValidationError("symbol map has an invalid field set")
    if document["schema_version"] != SYMBOL_MAP_SCHEMA:
        raise ScalpingDataValidationError("symbol map schema is unsupported")
    mappings = document["mappings"]
    if not isinstance(mappings, dict):
        raise ScalpingDataValidationError("symbol map mappings must be an object")
    clean_mappings = {}
    for instrument, broker_symbol in mappings.items():
        validate_canonical_instrument(instrument)
        clean_mappings[instrument] = _bounded_text(broker_symbol, "broker_symbol", maximum=32)
    blocked = document["event_risk_blocked"]
    if not isinstance(blocked, dict):
        raise ScalpingDataValidationError("event_risk_blocked must be an object")
    clean_blocked = {}
    for instrument, flag in blocked.items():
        validate_canonical_instrument(instrument)
        if not isinstance(flag, bool):
            raise ScalpingDataValidationError("event_risk_blocked value must be boolean")
        clean_blocked[instrument] = flag
    return {
        "schema_version": SYMBOL_MAP_SCHEMA,
        "mappings": clean_mappings,
        "event_risk_blocked": clean_blocked,
    }


class SymbolMapStore:
    """Atomic single-document local store, same technique as the journal
    stores (temp-file + os.replace)."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_symbol_map_path()

    def load(self):
        if not self.path.exists():
            return empty_symbol_map_document()
        try:
            raw = self.path.read_bytes()
            text = raw.decode("utf-8", errors="strict")
            document = json.loads(text)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ScalpingDataValidationError("symbol map storage is not strict UTF-8 JSON") from error
        return validate_symbol_map_document(document)

    def save(self, document):
        clean = validate_symbol_map_document(document)
        raw = (deterministic_json_text(clean) + "\n").encode("utf-8")
        temporary_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".{}-".format(self.path.name), suffix=".tmp",
                dir=str(self.path.parent), delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(temporary_path), str(self.path))
            temporary_path = None
        except OSError as error:
            raise ScalpingDataValidationError("symbol map storage atomic write failed") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass


class InMemorySymbolMapStore:
    def __init__(self, initial_document=None):
        self._document = (
            validate_symbol_map_document(initial_document)
            if initial_document is not None else empty_symbol_map_document()
        )

    def load(self):
        return deepcopy(self._document)

    def save(self, document):
        self._document = validate_symbol_map_document(document)


# --------------------------------------------------------------------------
# TRL_SCALPING_CONFIG.v1 (TRL-R2-013 Section 8): profile/side/risk/spread/
# monitoring-interval persistence -- previously held only in ScalpingService
# process memory and lost on every restart.
# --------------------------------------------------------------------------

CONFIG_SCHEMA = "TRL_SCALPING_CONFIG.v1"
MIN_MONITORING_INTERVAL_SECONDS = 5
MAX_MONITORING_INTERVAL_SECONDS = 300
DEFAULT_MONITORING_INTERVAL_SECONDS = 15


def default_config_path():
    local_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return root / "ALSAKKAF" / "TradingLab" / "scalping-configuration-v1.json"


def default_scratch_directory():
    """TRL-R2-013 root cause 5: the real running service never passed a
    ``scratch_directory`` to ``strategy.run_r2010_bridge`` at all, which
    would raise ``TypeError`` the first time a real ``TRADE_CANDIDATE``
    reached the bridge in production. Same ``%LOCALAPPDATA%`` root as the
    symbol-map/config stores, never a network/UNC path."""
    local_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return str(root / "ALSAKKAF" / "TradingLab" / "scratch")


def empty_config_document():
    return {
        "schema_version": CONFIG_SCHEMA,
        "profiles": {},
        "side_restrictions": {},
        "max_spread_points": {},
        "risk_settings": {},
        "monitoring_interval_seconds": DEFAULT_MONITORING_INTERVAL_SECONDS,
    }


def validate_config_document(document):
    if not isinstance(document, dict) or set(document) != {
        "schema_version", "profiles", "side_restrictions", "max_spread_points",
        "risk_settings", "monitoring_interval_seconds",
    }:
        raise ScalpingDataValidationError("configuration has an invalid field set")
    if document["schema_version"] != CONFIG_SCHEMA:
        raise ScalpingDataValidationError("configuration schema is unsupported")
    profiles = document["profiles"]
    if not isinstance(profiles, dict):
        raise ScalpingDataValidationError("profiles must be an object")
    clean_profiles = {}
    for instrument, profile_id in profiles.items():
        validate_canonical_instrument(instrument)
        clean_profiles[instrument] = validate_profile_id(profile_id)
    side_restrictions = document["side_restrictions"]
    if not isinstance(side_restrictions, dict):
        raise ScalpingDataValidationError("side_restrictions must be an object")
    clean_sides = {}
    for instrument, side in side_restrictions.items():
        validate_canonical_instrument(instrument)
        clean_sides[instrument] = _require_choice(side, SIDE_RESTRICTIONS, "side_restriction")
    spreads = document["max_spread_points"]
    if not isinstance(spreads, dict):
        raise ScalpingDataValidationError("max_spread_points must be an object")
    clean_spreads = {}
    for instrument, points in spreads.items():
        validate_canonical_instrument(instrument)
        if not isinstance(points, int) or isinstance(points, bool) or points <= 0:
            raise ScalpingDataValidationError("max_spread_points value must be a positive integer")
        clean_spreads[instrument] = points
    risk_settings = document["risk_settings"]
    if not isinstance(risk_settings, dict):
        raise ScalpingDataValidationError("risk_settings must be an object")
    interval = document["monitoring_interval_seconds"]
    if (
        not isinstance(interval, int) or isinstance(interval, bool)
        or not MIN_MONITORING_INTERVAL_SECONDS <= interval <= MAX_MONITORING_INTERVAL_SECONDS
    ):
        raise ScalpingDataValidationError("monitoring_interval_seconds is out of bounds")
    return {
        "schema_version": CONFIG_SCHEMA,
        "profiles": clean_profiles,
        "side_restrictions": clean_sides,
        "max_spread_points": clean_spreads,
        "risk_settings": dict(risk_settings),
        "monitoring_interval_seconds": interval,
    }


class ScalpingConfigStore:
    """Atomic single-document local store (same temp-file + os.replace
    technique as ``SymbolMapStore``)."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_config_path()

    def load(self):
        if not self.path.exists():
            return empty_config_document()
        try:
            raw = self.path.read_bytes()
            text = raw.decode("utf-8", errors="strict")
            document = json.loads(text)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ScalpingDataValidationError("configuration storage is not strict UTF-8 JSON") from error
        return validate_config_document(document)

    def save(self, document):
        clean = validate_config_document(document)
        raw = (deterministic_json_text(clean) + "\n").encode("utf-8")
        temporary_path = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", prefix=".{}-".format(self.path.name), suffix=".tmp",
                dir=str(self.path.parent), delete=False,
            ) as handle:
                temporary_path = Path(handle.name)
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(str(temporary_path), str(self.path))
            temporary_path = None
        except OSError as error:
            raise ScalpingDataValidationError("configuration storage atomic write failed") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass


class InMemoryScalpingConfigStore:
    def __init__(self, initial_document=None):
        self._document = (
            validate_config_document(initial_document)
            if initial_document is not None else empty_config_document()
        )

    def load(self):
        return deepcopy(self._document)

    def save(self, document):
        self._document = validate_config_document(document)


__all__ = (
    "ALSAKKAF_SCALPING_MAGIC",
    "CANONICAL_INSTRUMENTS",
    "CONFIG_SCHEMA",
    "COMMENT_PREFIX",
    "CYCLE_STATES",
    "DEFAULT_MONITORING_INTERVAL_SECONDS",
    "InMemoryScalpingConfigStore",
    "InMemorySymbolMapStore",
    "MAX_MONITORING_INTERVAL_SECONDS",
    "MIN_MONITORING_INTERVAL_SECONDS",
    "ORDER_PLAN_TYPES",
    "PRODUCT_STATES",
    "PROFILE_IDS",
    "ScalpingConfigStore",
    "ScalpingDataValidationError",
    "SIDES",
    "SIDE_RESTRICTIONS",
    "SYMBOL_MAP_SCHEMA",
    "SymbolMapStore",
    "broker_comment",
    "build_cycle",
    "build_order_plan",
    "default_config_path",
    "default_symbol_map_path",
    "empty_config_document",
    "empty_symbol_map_document",
    "quantize_4",
    "validate_canonical_instrument",
    "default_scratch_directory",
    "validate_config_document",
    "validate_cycle",
    "validate_order_plan",
    "validate_profile_id",
    "validate_symbol_map_document",
)
