# -*- coding: utf-8 -*-
"""Deterministic, paper-only Trading Research Lab Release 1 kernel.

ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING -
NO PROFIT CLAIMS. All fills, cash, positions, and performance are hypothetical.
The module is standard-library only and has no network, AI, credential, broker,
or external-order surface.
"""
import copy
import datetime
import hashlib
import json
import math
import os
import re


BASE = os.path.dirname(os.path.abspath(__file__))
DISCLAIMER = (
    "ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - "
    "NO LIVE TRADING - NO PROFIT CLAIMS"
)
PERFORMANCE_DISCLAIMER = (
    "Hypothetical research results from paper-only processing; they do not "
    "represent actual trading, predict future returns, or authorize a trade."
)

PROJECT_ID = "PRJ-017"
RELEASE_ID = "TRL-R1"
CHECKPOINT_ID = "TRL-R1-003"
ENGINE_NAME = "ALSAKKAF_TRL_CAUSAL_KERNEL"
ENGINE_VERSION = "1.0.0"
COMMITTED_BASE_REVISION = "bb3af4e"
ENGINE_SOURCE_DIGEST_ALGORITHM = "SHA-256"
ENGINE_SOURCE_NORMALIZATION = "UTF-8; CRLF_AND_CR_TO_LF"
PUBLIC_SCHEMA_TYPE_POLICY = (
    "EXACT BUILT-INS ONLY: dict, list, str, int, float; "
    "numeric bool rejected; finite/range rules apply"
)
OUTPUT_SCHEMA_VERSION = "1.0.0"
STRATEGY_ID = "SMA-001"
STRATEGY_VERSION = "1.0.0"
STRATEGY_FAMILY = "SMA_CROSS_LONG_ONLY"
STRATEGY_STATUS = "EXPERIMENTAL_RESEARCH_ONLY"

STARTING_CASH = 100.0
ACCOUNTING_UNIT = "paper_units_not_real_currency"
MAX_POSITION_PCT = 5.0
DRAWDOWN_HALT_PCT = -15.0
MAX_OPEN_POSITIONS = 1
COMMISSION_RATE = 0.0005
SLIPPAGE_RATE = 0.0005
SUPPORTED_ASSET_CLASSES = frozenset(("equity", "fx", "commodity", "index"))

OUTCOME_SIGNAL = "SIGNAL_SCHEDULED"
OUTCOME_FILL = "HYPOTHETICAL_FILL"
OUTCOME_NO_TRADE = "NO_TRADE"
OUTCOME_BLOCKED = "BLOCKED"
OUTCOME_HALT = "HALT"
OUTCOME_NO_FILL = "NO_FILL"

NO_TRADE_INSUFFICIENT_HISTORY = "NO_TRADE_INSUFFICIENT_HISTORY"
NO_TRADE_NO_CROSS = "NO_TRADE_NO_CROSS"
NO_TRADE_ALREADY_POSITIONED = "NO_TRADE_ALREADY_POSITIONED"
NO_TRADE_NO_OPEN_POSITION = "NO_TRADE_NO_OPEN_POSITION"
BLOCKED_INVALID_INPUT = "BLOCKED_INVALID_INPUT"
BLOCKED_INVALID_STRATEGY_PARAMETERS = "BLOCKED_INVALID_STRATEGY_PARAMETERS"
BLOCKED_POSITION_LIMIT = "BLOCKED_POSITION_LIMIT"
BLOCKED_DRAWDOWN_HALT = "BLOCKED_DRAWDOWN_HALT"
BLOCKED_RISK_OVERRIDE_ATTEMPT = "BLOCKED_RISK_OVERRIDE_ATTEMPT"
BLOCKED_INCREASE_TO_LOSER = "BLOCKED_INCREASE_TO_LOSER"
BLOCKED_REPRODUCIBILITY_ERROR = "BLOCKED_REPRODUCIBILITY_ERROR"
NO_FILL_END_OF_DATA = "NO_FILL_END_OF_DATA"

ENTRY_SIGNAL_SCHEDULED = "ENTRY_SIGNAL_SCHEDULED"
EXIT_SIGNAL_SCHEDULED = "EXIT_SIGNAL_SCHEDULED"
ENTRY_HYPOTHETICALLY_FILLED = "ENTRY_HYPOTHETICALLY_FILLED"
EXIT_HYPOTHETICALLY_FILLED = "EXIT_HYPOTHETICALLY_FILLED"
OPEN_TERMINAL_POSITION = "OPEN_TERMINAL_POSITION"
COMPLETED_TRADE_HISTORY = "COMPLETED_TRADE_HISTORY"

_PACK_REQUIRED = frozenset(("pack_id", "as_of", "prepared_by", "instruments"))
_PACK_ALLOWED = _PACK_REQUIRED | frozenset(("note",))
_INSTRUMENT_FIELDS = frozenset(
    ("symbol", "asset_class", "data_source", "data_quality_note", "ohlcv")
)
_BAR_FIELDS = frozenset(("date", "open", "high", "low", "close", "volume"))
_STRATEGY_REQUIRED = frozenset(
    ("strategy_id", "strategy_version", "family", "symbol", "fast", "slow",
     "paper_size_pct")
)
_STRATEGY_ALLOWED = _STRATEGY_REQUIRED | frozenset(
    ("name", "lifecycle_status", "author", "review_status", "drawdown_halt_pct")
)
_SEMVER = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_MAX_SAFE_INPUT_MAGNITUDE = 1e150
_MIN_SAFE_PRICE = 1e-150
_MAX_CANONICAL_INTEGER_BITS = 512
_MAX_CANONICAL_DEPTH = 64
_MAX_CANONICAL_NODES = 100000


class RiskPolicyViolation(Exception):
    """Raised by the legacy decision-log helper for invalid human decisions."""


class ReproducibilityError(RuntimeError):
    """Raised when the implemented engine source cannot be identified safely."""


def _stable_type_name(value):
    value_type = type(value)
    module = type.__getattribute__(value_type, "__module__")
    qualname = type.__getattribute__(value_type, "__qualname__")
    if type(module) is not str or type(qualname) is not str:
        return "unsupported_python_type"
    return "%s.%s" % (module, qualname)


def _stable_short_type_name(value):
    name = type.__getattribute__(type(value), "__name__")
    return name if type(name) is str else "unsupported_python_type"


def _marker_text(value):
    """Return marker text that cannot contain unpaired Unicode surrogates."""
    return "".join(
        "\\u%04x" % ord(character)
        if 0xD800 <= ord(character) <= 0xDFFF else character
        for character in value
    )


def _safe_string_for_hash(value):
    if not any(0xD800 <= ord(character) <= 0xDFFF for character in value):
        return value, False
    return {
        "__unicode_codepoints__": [
            "U+%04X" % ord(character) for character in value
        ]
    }, True


def _path_key(key):
    dumped = json.dumps(key, ensure_ascii=True, separators=(",", ":"))
    if len(dumped) > 80:
        digest = hashlib.sha256(dumped.encode("utf-8")).hexdigest()
        return "[<key-sha256:%s>]" % digest
    return "[%s]" % dumped


class _CanonicalTraversalLimit(RuntimeError):
    def __init__(self, path, type_name, visited_nodes, prefix_digest):
        super().__init__("canonical traversal node limit exceeded")
        self.path = path
        self.type_name = type_name
        self.visited_nodes = visited_nodes
        self.prefix_digest = prefix_digest


class _CanonicalStreamingError(ValueError):
    """Raised when schema-valid JSON cannot be hashed canonically."""

    def __init__(self, error_name):
        super().__init__("streaming canonical hashing failed: %s" % error_name)
        self.error_name = error_name


class _HashCanonicalizer:
    """Bounded mapper for deterministic, rejected-input-safe hash material."""

    def __init__(self):
        self.active = []
        self.nodes = 0
        self.issues = []
        self.prefix_digest = hashlib.sha256()
        self._record_prefix("bounded_rejected_input_fingerprint_v1")

    def _record_prefix(self, event, path=None, type_name=None, material=None):
        """Incrementally hash stable tokens for the safely visited prefix."""
        token = {"event": event}
        if path is not None:
            token["path"] = path
        if type_name is not None:
            token["type"] = type_name
        if material is not None:
            token["material"] = material
        encoder = json.JSONEncoder(
            sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        )
        for chunk in encoder.iterencode(token):
            self.prefix_digest.update(chunk.encode("utf-8", "strict"))
        self.prefix_digest.update(b"\n")

    def _issue_marker(self, kind, value, path):
        type_name = _marker_text(_stable_type_name(value))
        self._record_prefix(
            kind, path, type_name, {"visited_nodes": self.nodes},
        )
        self.issues.append(
            "%s encountered at %s for %s" % (kind, path, type_name)
        )
        return {
            "__canonicalization_issue__": {
                "kind": kind,
                "path": path,
                "type": type_name,
            }
        }

    def _enter_container(self, value, path, depth):
        for active_value, reference_path in self.active:
            if value is active_value:
                marker = self._issue_marker(
                    "active_container_cycle", value, path,
                )
                marker["__canonicalization_issue__"]["reference_path"] = (
                    reference_path
                )
                return marker
        if depth >= _MAX_CANONICAL_DEPTH:
            return self._issue_marker("maximum_depth_exceeded", value, path)
        self.active.append((value, path))
        return None

    def _mapping_entries(self, value, path, depth, subclass=False):
        raw_items = list(dict.items(value))
        keyed_items = []
        for key, item in raw_items:
            key_material = self.visit(
                key, "%s[<key>]" % path, depth + 1,
            )
            key_dump = _canonical_dump(key_material)
            self._record_prefix(
                "mapping_key", "%s[<key>]" % path,
                _marker_text(_stable_type_name(key)), key_material,
            )
            keyed_items.append((key_dump, key_material, item))
        keyed_items.sort(key=lambda entry: entry[0])
        entries = []
        for key_dump, key_material, item in keyed_items:
            key_digest = hashlib.sha256(key_dump.encode("utf-8")).hexdigest()
            item_material = self.visit(
                item, "%s[<value:%s>]" % (path, key_digest), depth + 1,
            )
            entries.append([key_material, item_material])
        entries.sort(key=_canonical_dump)
        marker = "__dict_subclass__" if subclass else "__mapping__"
        if subclass:
            return {marker: {
                "type": _marker_text(_stable_type_name(value)),
                "entries": entries,
            }}
        return {marker: entries}

    def visit(self, value, path="$", depth=0):
        type_name = _marker_text(_stable_type_name(value))
        if self.nodes >= _MAX_CANONICAL_NODES:
            self._record_prefix(
                "maximum_nodes_exceeded", path, type_name,
                {"visited_nodes": self.nodes},
            )
            raise _CanonicalTraversalLimit(
                path, type_name, self.nodes, self.prefix_digest.hexdigest(),
            )
        self.nodes += 1
        self._record_prefix(
            "visit", path, type_name, {"visited_nodes": self.nodes},
        )
        if (type(value) is int
                and value.bit_length() > _MAX_CANONICAL_INTEGER_BITS):
            magnitude = abs(value)
            byte_length = (magnitude.bit_length() + 7) // 8
            digest = hashlib.sha256(
                magnitude.to_bytes(byte_length, byteorder="big", signed=False)
            ).hexdigest()
            marker = {
                "__oversized_integer__": {
                    "sign": -1 if value < 0 else 1,
                    "bit_length": magnitude.bit_length(),
                    "magnitude_sha256": digest,
                }
            }
            self._record_prefix("scalar", path, type_name, marker)
            return marker
        if type(value) is float and not math.isfinite(value):
            if math.isnan(value):
                marker = {"__nonfinite_float__": "NaN"}
            else:
                infinity = "+Infinity" if value > 0 else "-Infinity"
                marker = {"__nonfinite_float__": infinity}
            self._record_prefix("scalar", path, type_name, marker)
            return marker
        if type(value) is dict or isinstance(value, dict):
            marker = self._enter_container(value, path, depth)
            if marker is not None:
                return marker
            self._record_prefix("container_start", path, type_name, "mapping")
            try:
                if (type(value) is dict
                        and all(type(key) is str for key in dict.keys(value))
                        and not any(
                            any(0xD800 <= ord(character) <= 0xDFFF
                                for character in key)
                            for key in dict.keys(value)
                        )):
                    keys = sorted(
                        dict.keys(value),
                        key=lambda key: (
                            isinstance(dict.__getitem__(value, key),
                                       (dict, list, tuple, set, frozenset)),
                            key,
                        ),
                    )
                    mapped = {}
                    for key in keys:
                        key_path = path + _path_key(key)
                        self._record_prefix(
                            "mapping_key", key_path, "builtins.str", key,
                        )
                        mapped[key] = self.visit(
                            dict.__getitem__(value, key), key_path, depth + 1,
                        )
                    return mapped
                return self._mapping_entries(
                    value, path, depth, subclass=type(value) is not dict,
                )
            finally:
                self._record_prefix("container_end", path, type_name, "mapping")
                self.active.pop()
        if type(value) is list or isinstance(value, list):
            marker = self._enter_container(value, path, depth)
            if marker is not None:
                return marker
            self._record_prefix("container_start", path, type_name, "list")
            try:
                items = [
                    self.visit(
                        list.__getitem__(value, index),
                        "%s[%d]" % (path, index), depth + 1,
                    )
                    for index in range(list.__len__(value))
                ]
            finally:
                self._record_prefix("container_end", path, type_name, "list")
                self.active.pop()
            if type(value) is list:
                return items
            return {"__list_subclass__": {
                "type": _marker_text(_stable_type_name(value)),
                "items": items,
            }}
        if type(value) is tuple or isinstance(value, tuple):
            marker = self._enter_container(value, path, depth)
            if marker is not None:
                return marker
            self._record_prefix("container_start", path, type_name, "tuple")
            try:
                items = [
                    self.visit(
                        tuple.__getitem__(value, index),
                        "%s[%d]" % (path, index), depth + 1,
                    )
                    for index in range(tuple.__len__(value))
                ]
            finally:
                self._record_prefix("container_end", path, type_name, "tuple")
                self.active.pop()
            if type(value) is tuple:
                return {"__tuple__": items}
            return {"__tuple_subclass__": {
                "type": _marker_text(_stable_type_name(value)),
                "items": items,
            }}
        if type(value) in (set, frozenset) or isinstance(value, (set, frozenset)):
            marker = self._enter_container(value, path, depth)
            if marker is not None:
                return marker
            self._record_prefix("container_start", path, type_name, "set")
            try:
                iterator = (set.__iter__(value) if isinstance(value, set)
                            else frozenset.__iter__(value))
                items = [
                    self.visit(item, "%s[<set-item>]" % path, depth + 1)
                    for item in iterator
                ]
                items.sort(key=_canonical_dump)
            finally:
                self._record_prefix("container_end", path, type_name, "set")
                self.active.pop()
            if type(value) in (set, frozenset):
                marker_name = "__set__" if type(value) is set else "__frozenset__"
                return {marker_name: items}
            marker_name = ("__set_subclass__" if isinstance(value, set)
                           else "__frozenset_subclass__")
            return {marker_name: {
                "type": _marker_text(_stable_type_name(value)),
                "items": items,
            }}
        if type(value) is str:
            material, has_surrogate = _safe_string_for_hash(value)
            if has_surrogate:
                self.issues.append("lone_surrogate encountered at %s" % path)
            self._record_prefix("scalar", path, type_name, material)
            return material
        if isinstance(value, str):
            exact_value = str.__str__(value)
            material, has_surrogate = _safe_string_for_hash(exact_value)
            if has_surrogate:
                self.issues.append("lone_surrogate encountered at %s" % path)
            marker = {"__str_subclass__": {
                "type": _marker_text(_stable_type_name(value)),
                "value": material,
            }}
            self._record_prefix("scalar", path, type_name, marker)
            return marker
        if value is None or type(value) in (int, float, bool):
            self._record_prefix("scalar", path, type_name, value)
            return value
        if isinstance(value, int):
            return {"__int_subclass__": {
                "type": _marker_text(_stable_type_name(value)),
                "value": self.visit(int.__int__(value), path + ".value", depth + 1),
            }}
        if isinstance(value, float):
            return {"__float_subclass__": {
                "type": _marker_text(_stable_type_name(value)),
                "value": self.visit(float.__float__(value), path + ".value", depth + 1),
            }}
        return {"__unsupported_type__": _marker_text(
            _stable_short_type_name(value)
        )}


def _safe_for_hash_details(value):
    canonicalizer = _HashCanonicalizer()
    try:
        material = canonicalizer.visit(value)
    except _CanonicalTraversalLimit as error:
        issue = (
            "maximum_nodes_exceeded encountered at %s for %s after %d nodes"
            % (error.path, error.type_name, error.visited_nodes)
        )
        canonicalizer.issues.append(issue)
        material = {
            "__canonicalization_issue__": {
                "kind": "maximum_nodes_exceeded",
                "path": error.path,
                "type": error.type_name,
                "visited_nodes": error.visited_nodes,
                "traversed_prefix_sha256": error.prefix_digest,
            }
        }
    return material, canonicalizer.issues


def _safe_for_hash(value):
    """Map even rejected Python values into deterministic JSON hash material."""
    material, _issues = _safe_for_hash_details(value)
    return material


def _canonical_dump(value):
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    )


def canonical_json(value):
    """Return the documented canonical UTF-8 JSON representation."""
    return _canonical_dump(_safe_for_hash(value))


def canonical_sha256(value):
    payload = canonical_json(value).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _streaming_canonical_sha256(value):
    """Hash complete schema-valid JSON without building one large string."""
    encoder = json.JSONEncoder(
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False, check_circular=True,
    )
    digest = hashlib.sha256()
    try:
        for chunk in encoder.iterencode(value):
            digest.update(chunk.encode("utf-8", "strict"))
    except (TypeError, ValueError, UnicodeError, RecursionError,
            OverflowError) as error:
        raise _CanonicalStreamingError(type(error).__name__) from error
    return digest.hexdigest()


def _canonical_sha256_with_issues(value):
    try:
        material, issues = _safe_for_hash_details(value)
    except (RecursionError, UnicodeError, ValueError, OverflowError) as error:
        error_name = type(error).__name__
        material = {"__canonicalization_failure__": error_name}
        issues = ["canonical hashing failed closed: %s" % error_name]
    payload = _canonical_dump(material).encode("utf-8")
    return hashlib.sha256(payload).hexdigest(), issues


def _normalized_source_sha256(source_bytes):
    """Hash strict UTF-8 source after normalizing CRLF/CR line endings to LF."""
    if type(source_bytes) is not bytes:
        raise ReproducibilityError("engine source must be supplied as exact bytes")
    try:
        source_text = source_bytes.decode("utf-8", "strict")
        normalized = source_text.replace("\r\n", "\n").replace("\r", "\n")
        normalized_bytes = normalized.encode("utf-8", "strict")
    except UnicodeError as error:
        raise ReproducibilityError(
            "engine source is not safely normalized UTF-8"
        ) from error
    return hashlib.sha256(normalized_bytes).hexdigest()


def _engine_source_digest():
    try:
        with open(os.path.abspath(__file__), "rb") as source_handle:
            source_bytes = source_handle.read()
    except OSError as error:
        raise ReproducibilityError(
            "engine source could not be read for reproducibility"
        ) from error
    return _normalized_source_sha256(source_bytes)


def _nonempty_string(value):
    return type(value) is str and bool(value.strip())


def _is_number(value):
    return type(value) in (int, float)


def _finite_float(value):
    """Return a finite losslessly representable built-in number as float."""
    if not _is_number(value):
        return None
    try:
        converted = float(value)
    except (OverflowError, ValueError):
        return None
    if not math.isfinite(converted):
        return None
    if type(value) is int and int(converted) != value:
        return None
    return converted


class NumericSafetyError(ValueError):
    """Raised when validated inputs still produce unsafe float arithmetic."""


class AllocationSafetyError(NumericSafetyError):
    """Raised when an allocation cannot reconcile in float accounting."""


def _checked_result(value, operation):
    converted = _finite_float(value)
    if converted is None:
        raise NumericSafetyError("non-finite result during %s" % operation)
    return converted


def _checked_add(left, right, operation):
    try:
        result = left + right
    except (OverflowError, ValueError) as error:
        raise NumericSafetyError("unsafe arithmetic during %s" % operation) from error
    return _checked_result(result, operation)


def _checked_subtract(left, right, operation):
    try:
        result = left - right
    except (OverflowError, ValueError) as error:
        raise NumericSafetyError("unsafe arithmetic during %s" % operation) from error
    return _checked_result(result, operation)


def _checked_multiply(left, right, operation):
    try:
        result = left * right
    except (OverflowError, ValueError) as error:
        raise NumericSafetyError("unsafe arithmetic during %s" % operation) from error
    converted = _checked_result(result, operation)
    if left != 0 and right != 0 and converted == 0:
        raise NumericSafetyError("underflow to zero during %s" % operation)
    return converted


def _checked_divide(numerator, denominator, operation):
    if denominator == 0:
        raise NumericSafetyError("zero divisor during %s" % operation)
    try:
        result = numerator / denominator
    except (OverflowError, ValueError) as error:
        raise NumericSafetyError("unsafe arithmetic during %s" % operation) from error
    converted = _checked_result(result, operation)
    if numerator != 0 and converted == 0:
        raise NumericSafetyError("underflow to zero during %s" % operation)
    return converted


def _checked_cash_subtract(cash, debit, operation):
    result = _checked_effective_subtract(cash, debit, operation)
    return result


def _checked_effective_subtract(left, right, operation):
    result = _checked_subtract(left, right, operation)
    if right != 0 and result == left:
        raise NumericSafetyError("value did not change during %s" % operation)
    return result


def _checked_cash_add(cash, credit, operation):
    return _checked_effective_add(cash, credit, operation)


def _checked_effective_add(left, right, operation):
    result = _checked_add(left, right, operation)
    if right != 0 and result == left:
        raise NumericSafetyError("value did not change during %s" % operation)
    return result


def _checked_accumulate(total, amount, operation):
    return _checked_effective_add(total, amount, operation)


def _allocation_validation_error(size):
    """Return an error when starting-cash allocation accounting loses value."""
    try:
        target = _checked_divide(
            _checked_multiply(
                STARTING_CASH, size, "allocation validation percentage",
            ),
            100.0,
            "allocation validation notional",
        )
        commission = _checked_multiply(
            target, COMMISSION_RATE, "allocation validation commission",
        )
        debit = _checked_effective_add(
            target, commission, "allocation validation debit",
        )
        _checked_cash_subtract(
            STARTING_CASH, debit, "allocation validation cash debit",
        )
    except NumericSafetyError:
        return (
            "strategy paper_size_pct cannot produce representable nonzero "
            "allocation costs and cash change"
        )
    return None


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


def _system_risk_limits():
    return {
        "max_position_pct": MAX_POSITION_PCT,
        "drawdown_halt_pct": DRAWDOWN_HALT_PCT,
        "max_open_positions": MAX_OPEN_POSITIONS,
        "leverage_allowed": False,
        "shorting_allowed": False,
        "increase_to_loser_allowed": False,
    }


def _effective_policy(risk_policy, strategy):
    policy = _system_risk_limits()
    if risk_policy is not None:
        if type(risk_policy) is not dict:
            return None, [
                "risk_policy must be an exact built-in dictionary when supplied"
            ]
        if not all(type(key) is str for key in risk_policy):
            return None, ["risk-policy field names must be exact built-in strings"]
        unsupported = set(risk_policy) - {"max_position_pct", "drawdown_halt_pct"}
        if unsupported:
            return None, ["unsupported risk-policy fields: %s" %
                          _field_list(unsupported)]
        if "max_position_pct" in risk_policy:
            value = risk_policy["max_position_pct"]
            safe_value = _finite_float(value)
            if (safe_value is None or safe_value <= 0
                    or safe_value > MAX_POSITION_PCT):
                return None, ["risk_policy cannot raise or invalidate max_position_pct"]
            policy["max_position_pct"] = safe_value
        if "drawdown_halt_pct" in risk_policy:
            value = risk_policy["drawdown_halt_pct"]
            safe_value = _finite_float(value)
            if (safe_value is None or safe_value >= 0
                    or safe_value < DRAWDOWN_HALT_PCT):
                return None, ["risk_policy cannot weaken or invalidate drawdown_halt_pct"]
            policy["drawdown_halt_pct"] = safe_value
    if strategy and "drawdown_halt_pct" in strategy:
        policy["drawdown_halt_pct"] = max(
            policy["drawdown_halt_pct"], float(strategy["drawdown_halt_pct"])
        )
    return policy, []


def sma(closes, period):
    """Simple moving averages with no intermediate rounding."""
    if type(period) is not int or period <= 0:
        raise ValueError("period must be a positive integer")
    if type(closes) is not list:
        raise ValueError("closes must be an exact built-in list")
    values = []
    for value in closes:
        converted = _finite_float(value)
        if converted is None:
            raise ValueError("closes must contain finite numeric non-boolean values")
        values.append(converted)
    result = []
    for index in range(len(values)):
        if index + 1 < period:
            result.append(None)
            continue
        window = values[index + 1 - period:index + 1]
        try:
            window_sum = math.fsum(window)
        except (OverflowError, ValueError) as error:
            raise NumericSafetyError("unsafe arithmetic during SMA window sum") from error
        checked_sum = _checked_result(window_sum, "SMA window sum")
        result.append(_checked_divide(checked_sum, period, "SMA average"))
    return result


def _sma_cross_signals_from_series(ohlcv, fast_series, slow_series):
    """Derive transition-only signals from complete, aligned SMA series."""
    if type(ohlcv) is not list:
        raise ValueError("ohlcv must be an exact built-in list")
    if type(fast_series) is not list or type(slow_series) is not list:
        raise ValueError("SMA series must be exact built-in lists")
    if len(fast_series) != len(ohlcv) or len(slow_series) != len(ohlcv):
        raise ValueError("SMA series lengths must match ohlcv")
    signals = []
    for index, bar in enumerate(ohlcv):
        action = "none"
        if index > 0:
            previous_fast = fast_series[index - 1]
            previous_slow = slow_series[index - 1]
            current_fast = fast_series[index]
            current_slow = slow_series[index]
            if None not in (previous_fast, previous_slow, current_fast, current_slow):
                if previous_fast <= previous_slow and current_fast > current_slow:
                    action = "enter"
                elif previous_fast >= previous_slow and current_fast < current_slow:
                    action = "exit"
        signals.append((bar["date"], action))
    return signals


def sma_cross_signals(ohlcv, fast, slow):
    """Return only genuine bullish/bearish transitions, never regime repeats."""
    if (type(fast) is not int or fast <= 0
            or type(slow) is not int or slow <= 0
            or fast >= slow):
        raise ValueError("SMA periods must satisfy 1 <= fast < slow")
    if type(ohlcv) is not list:
        raise ValueError("ohlcv must be an exact built-in list")
    closes = [bar["close"] for bar in ohlcv]
    fast_series = sma(closes, fast)
    slow_series = sma(closes, slow)
    return _sma_cross_signals_from_series(ohlcv, fast_series, slow_series)


def check_entry_allowed(open_positions, last_loss_size_pct, symbol,
                        asset_class, size_pct, policy=None):
    """Pure risk gate retained for focused tests; run policy stays system-owned."""
    del asset_class
    effective_max = MAX_POSITION_PCT
    if policy and _is_number(policy.get("max_position_pct")):
        effective_max = min(effective_max, policy["max_position_pct"])
    if size_pct > effective_max:
        return False, BLOCKED_POSITION_LIMIT
    if open_positions:
        return False, NO_TRADE_ALREADY_POSITIONED
    prior_loss = last_loss_size_pct.get(symbol)
    if prior_loss is not None and size_pct > prior_loss:
        return False, BLOCKED_INCREASE_TO_LOSER
    return True, None


def _assumptions():
    return {
        "starting_cash": STARTING_CASH,
        "accounting_unit": ACCOUNTING_UNIT,
        "commission_bps_per_fill": 5.0,
        "commission_rate": COMMISSION_RATE,
        "slippage_bps_per_fill": 5.0,
        "slippage_rate": SLIPPAGE_RATE,
        "buy_fill_rule": "NEXT_BAR_OPEN_MULTIPLIED_BY_1.0005",
        "sell_fill_rule": "NEXT_BAR_OPEN_MULTIPLIED_BY_0.9995",
        "separate_spread_bps": 0.0,
        "minimum_fee": 0.0,
        "taxes_financing_borrow_venue_fees": 0.0,
        "market_impact_model": "NONE_BEYOND_FIXED_SLIPPAGE",
        "partial_fills": False,
        "signal_information_cutoff": "BAR_CLOSE_T",
        "execution_bar": "NEXT_VALIDATED_BAR",
        "reference_price": "NEXT_BAR_OPEN",
        "terminal_position_policy": "MARK_TO_MARKET_OPEN",
        "numeric_rounding_policy": "NO_INTERMEDIATE_ROUNDING; DISPLAY_ONLY",
        "timezone_convention": "ISO_INPUT_NORMALIZED_TO_UTC_FOR_VALIDATION",
    }


def _safe_raw_strategy_identity(strategy_rules):
    candidate = None
    if type(strategy_rules) is dict:
        candidate = strategy_rules
    elif (type(strategy_rules) is list and len(strategy_rules) == 1
          and type(strategy_rules[0]) is dict):
        candidate = strategy_rules[0]
    if candidate is None:
        return None
    identity = {}
    for field in ("strategy_id", "strategy_version", "family", "symbol"):
        value = candidate.get(field)
        if type(value) is str:
            identity[field] = value
    return identity or None


def _metadata(historical_pack, strategy, input_hash, strategy_hash, policy,
              engine_source_digest=None, raw_strategy_identity=None):
    if engine_source_digest is None:
        engine_source_digest = _engine_source_digest()
    if (type(engine_source_digest) is not str
            or re.fullmatch(r"[0-9a-f]{64}", engine_source_digest) is None):
        raise ReproducibilityError(
            "engine source digest must be lowercase SHA-256 text"
        )
    instrument = None
    if (type(historical_pack) is dict
            and type(historical_pack.get("instruments")) is list
            and len(historical_pack["instruments"]) == 1
            and type(historical_pack["instruments"][0]) is dict):
        instrument = historical_pack["instruments"][0]
    candidate_dates = instrument.get("ohlcv", []) if instrument else []
    dates = candidate_dates if type(candidate_dates) is list else []
    first_date = dates[0].get("date") if dates and type(dates[0]) is dict else None
    last_date = dates[-1].get("date") if dates and type(dates[-1]) is dict else None
    identity = strategy if type(strategy) is dict else raw_strategy_identity
    material = {
        "input_hash": input_hash,
        "strategy_hash": strategy_hash,
        "engine_version": ENGINE_VERSION,
        "engine_checkpoint": CHECKPOINT_ID,
        "engine_source_digest": engine_source_digest,
    }
    return {
        "run_id": "TRL-RUN-" + canonical_sha256(material)[:20].upper(),
        "project_id": PROJECT_ID,
        "release_id": RELEASE_ID,
        "checkpoint_id": CHECKPOINT_ID,
        "engine": {
            "name": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "checkpoint_id": CHECKPOINT_ID,
            "digest_algorithm": ENGINE_SOURCE_DIGEST_ALGORITHM,
            "source_normalization": ENGINE_SOURCE_NORMALIZATION,
            "engine_source_digest": engine_source_digest,
            "committed_base_revision": COMMITTED_BASE_REVISION,
        },
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "public_schema_type_policy": PUBLIC_SCHEMA_TYPE_POLICY,
        "strategy_id": (_safe_for_hash(identity.get("strategy_id"))
                        if type(identity) is dict else None),
        "strategy_name": (_safe_for_hash(strategy.get(
            "name", "SMA Close Crossing Long-Only Research Rule"))
            if type(strategy) is dict else None),
        "strategy_version": (_safe_for_hash(strategy.get("strategy_version"))
                             if type(strategy) is dict else
                             _safe_for_hash(identity.get("strategy_version"))
                             if type(identity) is dict else None),
        "strategy_status": STRATEGY_STATUS,
        "strategy_author": (_safe_for_hash(strategy.get(
            "author", "ALSAKKAF Trading Research Lab"))
            if type(strategy) is dict else None),
        "strategy_review_status": (
            _safe_for_hash(strategy.get("review_status", "NOT_FOUNDER_APPROVED"))
            if type(strategy) is dict else None
        ),
        "strategy_founder_approved": False,
        "strategy_parameters": (_safe_for_hash(strategy)
                                 if type(strategy) is dict else None),
        "strategy_definition_hash": (
            canonical_sha256(strategy) if type(strategy) is dict else None
        ),
        "raw_strategy_identity": (
            _safe_for_hash(raw_strategy_identity)
            if type(raw_strategy_identity) is dict else None
        ),
        "raw_strategy_identity_hash": (
            canonical_sha256(raw_strategy_identity)
            if type(raw_strategy_identity) is dict else None
        ),
        "configuration_hash": strategy_hash,
        "pack_id": (_safe_for_hash(historical_pack.get("pack_id"))
                    if type(historical_pack) is dict else None),
        "data_as_of": (_safe_for_hash(historical_pack.get("as_of"))
                       if type(historical_pack) is dict else None),
        "instrument": {
            "symbol": _safe_for_hash(instrument.get("symbol")),
            "asset_class": _safe_for_hash(instrument.get("asset_class")),
            "data_source": _safe_for_hash(instrument.get("data_source")),
            "data_quality_note": _safe_for_hash(instrument.get("data_quality_note")),
        } if instrument else None,
        "input_data_hash": input_hash,
        "engine_source_digest": engine_source_digest,
        "canonical_serialization": "UTF-8 JSON; SORTED KEYS; COMPACT SEPARATORS; NO NaN/Infinity",
        "effective_system_risk_limits": copy.deepcopy(policy),
        "execution_assumptions": _assumptions(),
        "run_start_timestamp": _safe_for_hash(first_date),
        "run_end_timestamp": _safe_for_hash(last_date),
        "paper_research_only": True,
        "performance_disclaimer": PERFORMANCE_DISCLAIMER,
    }


def _reproducibility_failure_metadata(historical_pack, input_hash,
                                      strategy_hash, raw_strategy_identity):
    material = {
        "input_hash": input_hash,
        "strategy_hash": strategy_hash,
        "engine_version": ENGINE_VERSION,
        "engine_checkpoint": CHECKPOINT_ID,
        "engine_source_digest": None,
        "reproducibility_status": "FAILED_CLOSED",
    }
    return {
        "run_id": "TRL-RUN-" + canonical_sha256(material)[:20].upper(),
        "project_id": PROJECT_ID,
        "release_id": RELEASE_ID,
        "checkpoint_id": CHECKPOINT_ID,
        "engine": {
            "name": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "checkpoint_id": CHECKPOINT_ID,
            "digest_algorithm": ENGINE_SOURCE_DIGEST_ALGORITHM,
            "source_normalization": ENGINE_SOURCE_NORMALIZATION,
            "engine_source_digest": None,
            "committed_base_revision": COMMITTED_BASE_REVISION,
        },
        "output_schema_version": OUTPUT_SCHEMA_VERSION,
        "public_schema_type_policy": PUBLIC_SCHEMA_TYPE_POLICY,
        "strategy_id": (raw_strategy_identity.get("strategy_id")
                        if type(raw_strategy_identity) is dict else None),
        "strategy_name": None,
        "strategy_version": (raw_strategy_identity.get("strategy_version")
                             if type(raw_strategy_identity) is dict else None),
        "strategy_status": STRATEGY_STATUS,
        "strategy_author": None,
        "strategy_review_status": None,
        "strategy_founder_approved": False,
        "strategy_parameters": None,
        "strategy_definition_hash": None,
        "raw_strategy_identity": _safe_for_hash(raw_strategy_identity),
        "raw_strategy_identity_hash": canonical_sha256(raw_strategy_identity),
        "configuration_hash": strategy_hash,
        "pack_id": (_safe_for_hash(historical_pack.get("pack_id"))
                    if type(historical_pack) is dict else None),
        "data_as_of": (_safe_for_hash(historical_pack.get("as_of"))
                       if type(historical_pack) is dict else None),
        "instrument": None,
        "input_data_hash": input_hash,
        "engine_source_digest": None,
        "canonical_serialization": "UTF-8 JSON; SORTED KEYS; COMPACT SEPARATORS; NO NaN/Infinity",
        "effective_system_risk_limits": _system_risk_limits(),
        "execution_assumptions": _assumptions(),
        "run_start_timestamp": None,
        "run_end_timestamp": None,
        "paper_research_only": True,
        "performance_disclaimer": PERFORMANCE_DISCLAIMER,
        "reproducibility_status": "FAILED_CLOSED",
    }


def _empty_result(metadata, outcome, reason_code, validation_errors=None):
    event = {
        "event_id": "EVT-0001",
        "outcome": outcome,
        "reason_code": reason_code,
        "timestamp": metadata.get("data_as_of"),
        "strategy_id": metadata.get("strategy_id"),
        "context": {},
    }
    return {
        "report_type": "BacktestReport",
        "outcome": outcome,
        "reason_code": reason_code,
        "reason_codes": [reason_code],
        "validation": {
            "outcome": "VALID" if not validation_errors else "INVALID",
            "reason_codes": [] if not validation_errors else [reason_code],
            "errors": validation_errors or [],
        },
        "metadata": metadata,
        "assumptions": metadata["execution_assumptions"],
        "events": [event],
        "decisions": [],
        "hypothetical_fills": [],
        "trade_list": [],
        "equity_curve": [],
        "open_position": None,
        "starting_cash": STARTING_CASH,
        "final_cash": STARTING_CASH,
        "final_equity": STARTING_CASH,
        "realized_pnl": 0.0,
        "unrealized_pnl": 0.0,
        "cumulative_commission": 0.0,
        "cumulative_slippage_cost": 0.0,
        "cumulative_costs": 0.0,
        "max_drawdown_pct": 0.0,
        "halted": outcome == OUTCOME_HALT,
        "assumption_violations": validation_errors or [],
        "disclaimer": DISCLAIMER,
        "performance_disclaimer": PERFORMANCE_DISCLAIMER,
    }


def _event(events, outcome, reason, timestamp, strategy, context=None):
    events.append({
        "event_id": "EVT-%04d" % (len(events) + 1),
        "outcome": outcome,
        "reason_code": reason,
        "timestamp": timestamp,
        "strategy_id": strategy["strategy_id"],
        "context": context or {},
    })


def _decision(decisions, action, timestamp, status, reason, target_notional=None):
    record = {
        "decision_id": "SIG-%04d" % (len(decisions) + 1),
        "action": action,
        "signal_timestamp": timestamp,
        "information_cutoff": "BAR_CLOSE_T",
        "eligible_fill_rule": "NEXT_VALIDATED_BAR_OPEN",
        "status": status,
        "reason_code": reason,
    }
    if target_notional is not None:
        record["target_gross_notional"] = target_notional
    decisions.append(record)
    return record


def _run_validated(strategy, pack, policy, metadata, initial_last_loss_size_pct=None):
    """Internal deterministic state machine; the optional state is a test seam."""
    instrument = pack["instruments"][0]
    bars = instrument["ohlcv"]
    symbol = instrument["symbol"]
    strategy_size = _checked_result(
        strategy["paper_size_pct"], "strategy size conversion",
    )
    closes = [bar["close"] for bar in bars]
    fast_series = sma(closes, strategy["fast"])
    slow_series = sma(closes, strategy["slow"])
    signals = _sma_cross_signals_from_series(bars, fast_series, slow_series)

    cash = _checked_result(STARTING_CASH, "starting cash initialization")
    units = 0.0
    position = None
    realized_pnl = 0.0
    cumulative_commission = 0.0
    cumulative_slippage = 0.0
    peak = STARTING_CASH
    max_drawdown = 0.0
    halted = False
    pending = None
    last_loss_size_pct = copy.deepcopy(initial_last_loss_size_pct or {})
    events = []
    decisions = []
    fills = []
    trades = []
    curve = []

    for index, bar in enumerate(bars):
        timestamp = bar["date"]
        raw_open = _checked_result(bar["open"], "opening price conversion")

        if pending is not None:
            action = pending["action"]
            if action == "enter":
                allowed, block_reason = check_entry_allowed(
                    {symbol: position} if position else {}, last_loss_size_pct,
                    symbol, instrument["asset_class"], strategy["paper_size_pct"],
                    policy,
                )
                if halted:
                    allowed, block_reason = False, BLOCKED_DRAWDOWN_HALT
                if not allowed:
                    pending["decision"]["status"] = "BLOCKED"
                    pending["decision"]["reason_code"] = block_reason
                    _event(events, OUTCOME_BLOCKED, block_reason, timestamp, strategy,
                           {"signal_timestamp": pending["signal_timestamp"]})
                else:
                    try:
                        fill_price = _checked_multiply(
                            raw_open, 1.0 + SLIPPAGE_RATE, "buy slippage",
                        )
                        target_notional = pending["target_notional"]
                        if target_notional <= 0:
                            raise NumericSafetyError(
                                "zero target notional during entry allocation"
                            )
                        units = _checked_divide(
                            target_notional, fill_price, "entry units",
                        )
                        commission = _checked_multiply(
                            target_notional, COMMISSION_RATE, "entry commission",
                        )
                        slippage_delta = _checked_subtract(
                            fill_price, raw_open, "entry slippage delta",
                        )
                        if slippage_delta <= 0:
                            raise NumericSafetyError(
                                "zero slippage cost basis during entry allocation"
                            )
                        slippage_cost = _checked_multiply(
                            units, slippage_delta, "entry slippage cost",
                        )
                        entry_debit = _checked_effective_add(
                            target_notional, commission, "entry cash debit",
                        )
                        next_cash = _checked_cash_subtract(
                            cash, entry_debit, "entry cash",
                        )
                        next_commission = _checked_accumulate(
                            cumulative_commission, commission,
                            "cumulative commission",
                        )
                        next_slippage = _checked_accumulate(
                            cumulative_slippage, slippage_cost,
                            "cumulative slippage",
                        )
                    except NumericSafetyError as error:
                        raise AllocationSafetyError(
                            "entry allocation rejected: %s" % error
                        ) from error
                    cash = next_cash
                    cumulative_commission = next_commission
                    cumulative_slippage = next_slippage
                    position = {
                        "symbol": symbol,
                        "units": units,
                        "requested_position_pct": float(strategy["paper_size_pct"]),
                        "entry_signal_time": pending["signal_timestamp"],
                        "entry_fill_time": timestamp,
                        "raw_opening_price": raw_open,
                        "slipped_fill_price": fill_price,
                        "entry_filled_notional": target_notional,
                        "entry_commission": commission,
                        "entry_slippage_cost": slippage_cost,
                    }
                    fill = {
                        "fill_id": "FILL-%04d" % (len(fills) + 1),
                        "side": "BUY",
                        "signal_timestamp": pending["signal_timestamp"],
                        "fill_timestamp": timestamp,
                        "raw_opening_price": raw_open,
                        "slipped_fill_price": fill_price,
                        "units": units,
                        "filled_notional": target_notional,
                        "commission": commission,
                        "slippage_cost": slippage_cost,
                    }
                    fills.append(fill)
                    pending["decision"]["status"] = "FILLED"
                    pending["decision"]["fill_id"] = fill["fill_id"]
                    _event(events, OUTCOME_FILL, ENTRY_HYPOTHETICALLY_FILLED,
                           timestamp, strategy,
                           {"signal_timestamp": pending["signal_timestamp"],
                            "fill_id": fill["fill_id"]})
            else:
                if position is None:
                    pending["decision"]["status"] = "NO_TRADE"
                    pending["decision"]["reason_code"] = NO_TRADE_NO_OPEN_POSITION
                    _event(events, OUTCOME_NO_TRADE, NO_TRADE_NO_OPEN_POSITION,
                           timestamp, strategy,
                           {"signal_timestamp": pending["signal_timestamp"]})
                else:
                    try:
                        fill_price = _checked_multiply(
                            raw_open, 1.0 - SLIPPAGE_RATE, "sell slippage",
                        )
                        exit_notional = _checked_multiply(
                            units, fill_price, "exit notional",
                        )
                        commission = _checked_multiply(
                            exit_notional, COMMISSION_RATE, "exit commission",
                        )
                        slippage_delta = _checked_subtract(
                            raw_open, fill_price, "exit slippage delta",
                        )
                        if slippage_delta <= 0:
                            raise NumericSafetyError(
                                "zero slippage cost basis during exit allocation"
                            )
                        slippage_cost = _checked_multiply(
                            units, slippage_delta, "exit slippage cost",
                        )
                        exit_credit = _checked_effective_subtract(
                            exit_notional, commission, "exit cash credit",
                        )
                        next_cash = _checked_cash_add(
                            cash, exit_credit, "exit cash",
                        )
                        next_commission = _checked_accumulate(
                            cumulative_commission, commission,
                            "cumulative commission",
                        )
                        next_slippage = _checked_accumulate(
                            cumulative_slippage, slippage_cost,
                            "cumulative slippage",
                        )
                    except NumericSafetyError as error:
                        raise AllocationSafetyError(
                            "exit allocation rejected: %s" % error
                        ) from error
                    cash = next_cash
                    cumulative_commission = next_commission
                    cumulative_slippage = next_slippage
                    try:
                        trade_net = _checked_effective_subtract(
                            exit_credit, position["entry_filled_notional"],
                            "trade net before entry commission",
                        )
                        trade_net = _checked_effective_subtract(
                            trade_net, position["entry_commission"], "trade net",
                        )
                        next_realized_pnl = _checked_effective_add(
                            realized_pnl, trade_net, "realized P&L",
                        )
                    except NumericSafetyError as error:
                        raise AllocationSafetyError(
                            "exit allocation rejected: %s" % error
                        ) from error
                    realized_pnl = next_realized_pnl
                    fill = {
                        "fill_id": "FILL-%04d" % (len(fills) + 1),
                        "side": "SELL",
                        "signal_timestamp": pending["signal_timestamp"],
                        "fill_timestamp": timestamp,
                        "raw_opening_price": raw_open,
                        "slipped_fill_price": fill_price,
                        "units": units,
                        "filled_notional": exit_notional,
                        "commission": commission,
                        "slippage_cost": slippage_cost,
                    }
                    fills.append(fill)
                    trade = {
                        "trade_id": "TRADE-%04d" % (len(trades) + 1),
                        "symbol": symbol,
                        "entry_signal_time": position["entry_signal_time"],
                        "entry_fill_time": position["entry_fill_time"],
                        "exit_signal_time": pending["signal_timestamp"],
                        "exit_fill_time": timestamp,
                        "entry_raw_opening_price": position["raw_opening_price"],
                        "entry_fill_price": position["slipped_fill_price"],
                        "exit_raw_opening_price": raw_open,
                        "exit_fill_price": fill_price,
                        "units": units,
                        "entry_commission": position["entry_commission"],
                        "exit_commission": commission,
                        "gross_pnl": _checked_subtract(
                            exit_notional, position["entry_filled_notional"],
                            "gross P&L",
                        ),
                        "net_realized_pnl": trade_net,
                        "requested_position_pct": position["requested_position_pct"],
                    }
                    trades.append(trade)
                    if trade_net < 0:
                        last_loss_size_pct[symbol] = position["requested_position_pct"]
                    else:
                        last_loss_size_pct.pop(symbol, None)
                    units = 0.0
                    position = None
                    pending["decision"]["status"] = "FILLED"
                    pending["decision"]["fill_id"] = fill["fill_id"]
                    _event(events, OUTCOME_FILL, EXIT_HYPOTHETICALLY_FILLED,
                           timestamp, strategy,
                           {"signal_timestamp": pending["signal_timestamp"],
                            "fill_id": fill["fill_id"]})
            pending = None

        close = _checked_result(bar["close"], "closing price conversion")
        try:
            marked_value = _checked_multiply(units, close, "position value")
            if position is None:
                unrealized_pnl = 0.0
                equity = _checked_add(cash, marked_value, "marked equity")
            else:
                unrealized_pnl = _checked_effective_subtract(
                    marked_value, position["entry_filled_notional"],
                    "unrealized P&L before commission",
                )
                unrealized_pnl = _checked_effective_subtract(
                    unrealized_pnl, position["entry_commission"],
                    "unrealized P&L",
                )
                equity = _checked_effective_add(
                    cash, marked_value, "marked equity",
                )
        except NumericSafetyError as error:
            if position is not None:
                raise AllocationSafetyError(
                    "position accounting rejected: %s" % error
                ) from error
            raise
        peak = max(peak, equity)
        drawdown_amount = _checked_subtract(equity, peak, "drawdown amount")
        drawdown_ratio = _checked_divide(
            drawdown_amount, peak, "drawdown ratio",
        )
        drawdown = _checked_multiply(
            drawdown_ratio, 100.0, "drawdown percentage",
        )
        max_drawdown = min(max_drawdown, drawdown)
        if drawdown <= policy["drawdown_halt_pct"] and not halted:
            halted = True
            _event(events, OUTCOME_HALT, BLOCKED_DRAWDOWN_HALT, timestamp,
                   strategy, {"drawdown_pct": drawdown,
                              "halt_threshold_pct": policy["drawdown_halt_pct"]})

        curve.append({
            "accounting_row_id": "ACCT-%06d" % (len(curve) + 1),
            "timestamp": timestamp,
            "cash": cash,
            "position_units": units,
            "position_value": marked_value,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "cumulative_commission": cumulative_commission,
            "cumulative_slippage_cost": cumulative_slippage,
            "cumulative_costs": _checked_add(
                cumulative_commission, cumulative_slippage, "cumulative costs",
            ),
            "total_marked_equity": equity,
            "equity_peak": peak,
            "drawdown_pct": drawdown,
            "close": close,
            "fast_sma": fast_series[index],
            "slow_sma": slow_series[index],
        })

        action = signals[index][1]
        has_next_bar = index + 1 < len(bars)
        if action == "enter":
            if halted:
                _decision(decisions, action, timestamp, "BLOCKED",
                          BLOCKED_DRAWDOWN_HALT)
                _event(events, OUTCOME_BLOCKED, BLOCKED_DRAWDOWN_HALT,
                       timestamp, strategy)
            elif position is not None:
                _decision(decisions, action, timestamp, "NO_TRADE",
                          NO_TRADE_ALREADY_POSITIONED)
                _event(events, OUTCOME_NO_TRADE, NO_TRADE_ALREADY_POSITIONED,
                       timestamp, strategy)
            else:
                allowed, block_reason = check_entry_allowed(
                    {}, last_loss_size_pct, symbol, instrument["asset_class"],
                    strategy["paper_size_pct"], policy,
                )
                try:
                    target_notional = _checked_multiply(
                        equity, strategy_size,
                        "target notional percentage",
                    )
                    target_notional = _checked_divide(
                        target_notional, 100.0, "target notional",
                    )
                    if target_notional <= 0:
                        raise NumericSafetyError(
                            "zero target notional during entry allocation"
                        )
                except NumericSafetyError as error:
                    raise AllocationSafetyError(
                        "entry allocation rejected: %s" % error
                    ) from error
                if not allowed:
                    _decision(decisions, action, timestamp, "BLOCKED", block_reason,
                              target_notional)
                    _event(events, OUTCOME_BLOCKED, block_reason, timestamp,
                           strategy, {"requested_position_pct": strategy["paper_size_pct"]})
                elif not has_next_bar:
                    _decision(decisions, action, timestamp, "NO_FILL",
                              NO_FILL_END_OF_DATA, target_notional)
                    _event(events, OUTCOME_NO_FILL, NO_FILL_END_OF_DATA,
                           timestamp, strategy, {"action": "enter"})
                else:
                    decision = _decision(
                        decisions, action, timestamp, "SCHEDULED",
                        ENTRY_SIGNAL_SCHEDULED, target_notional,
                    )
                    pending = {
                        "action": action,
                        "signal_timestamp": timestamp,
                        "target_notional": target_notional,
                        "decision": decision,
                    }
                    _event(events, OUTCOME_SIGNAL, ENTRY_SIGNAL_SCHEDULED,
                           timestamp, strategy,
                           {"eligible_fill_timestamp": bars[index + 1]["date"]})
        elif action == "exit":
            if position is None:
                _decision(decisions, action, timestamp, "NO_TRADE",
                          NO_TRADE_NO_OPEN_POSITION)
                _event(events, OUTCOME_NO_TRADE, NO_TRADE_NO_OPEN_POSITION,
                       timestamp, strategy)
            elif not has_next_bar:
                _decision(decisions, action, timestamp, "NO_FILL",
                          NO_FILL_END_OF_DATA)
                _event(events, OUTCOME_NO_FILL, NO_FILL_END_OF_DATA,
                       timestamp, strategy, {"action": "exit"})
            else:
                decision = _decision(decisions, action, timestamp, "SCHEDULED",
                                     EXIT_SIGNAL_SCHEDULED)
                pending = {
                    "action": action,
                    "signal_timestamp": timestamp,
                    "decision": decision,
                }
                _event(events, OUTCOME_SIGNAL, EXIT_SIGNAL_SCHEDULED,
                       timestamp, strategy,
                       {"eligible_fill_timestamp": bars[index + 1]["date"]})
        else:
            reason = (NO_TRADE_INSUFFICIENT_HISTORY
                      if index < strategy["slow"] else NO_TRADE_NO_CROSS)
            _event(events, OUTCOME_NO_TRADE, reason, timestamp, strategy)

    open_position = None
    if position is not None:
        open_position = copy.deepcopy(position)
        open_position.update({
            "market_timestamp": bars[-1]["date"],
            "market_close": _checked_result(
                bars[-1]["close"], "terminal closing price conversion",
            ),
            "market_value": curve[-1]["position_value"],
            "unrealized_pnl": curve[-1]["unrealized_pnl"],
            "terminal_status": "OPEN_MARKED_TO_MARKET",
        })

    reason_codes = []
    for item in events:
        if item["reason_code"] not in reason_codes:
            reason_codes.append(item["reason_code"])
    if halted:
        outcome, reason_code = OUTCOME_HALT, BLOCKED_DRAWDOWN_HALT
    elif any(item["outcome"] == OUTCOME_NO_FILL for item in events):
        outcome, reason_code = OUTCOME_NO_FILL, NO_FILL_END_OF_DATA
    elif any(item["reason_code"] == BLOCKED_INCREASE_TO_LOSER for item in events):
        outcome, reason_code = OUTCOME_BLOCKED, BLOCKED_INCREASE_TO_LOSER
    elif fills:
        outcome = OUTCOME_FILL
        reason_code = OPEN_TERMINAL_POSITION if open_position else COMPLETED_TRADE_HISTORY
        if reason_code not in reason_codes:
            reason_codes.append(reason_code)
    elif len(bars) <= strategy["slow"]:
        outcome, reason_code = OUTCOME_NO_TRADE, NO_TRADE_INSUFFICIENT_HISTORY
    elif any(item["reason_code"] == NO_TRADE_ALREADY_POSITIONED for item in events):
        outcome, reason_code = OUTCOME_NO_TRADE, NO_TRADE_ALREADY_POSITIONED
    elif any(item["reason_code"] == NO_TRADE_NO_OPEN_POSITION for item in events):
        outcome, reason_code = OUTCOME_NO_TRADE, NO_TRADE_NO_OPEN_POSITION
    else:
        outcome, reason_code = OUTCOME_NO_TRADE, NO_TRADE_NO_CROSS

    final_row = curve[-1]
    violations = [
        item["reason_code"] for item in events
        if item["outcome"] in (OUTCOME_BLOCKED, OUTCOME_HALT, OUTCOME_NO_FILL)
    ]
    return {
        "report_type": "BacktestReport",
        "outcome": outcome,
        "reason_code": reason_code,
        "reason_codes": reason_codes,
        "validation": {"outcome": "VALID", "reason_codes": [], "errors": []},
        "metadata": metadata,
        "assumptions": metadata["execution_assumptions"],
        "events": events,
        "decisions": decisions,
        "hypothetical_fills": fills,
        "trade_list": trades,
        "equity_curve": curve,
        "open_position": open_position,
        "starting_cash": STARTING_CASH,
        "final_cash": cash,
        "final_equity": final_row["total_marked_equity"],
        "realized_pnl": realized_pnl,
        "unrealized_pnl": final_row["unrealized_pnl"],
        "cumulative_commission": cumulative_commission,
        "cumulative_slippage_cost": cumulative_slippage,
        "cumulative_costs": _checked_add(
            cumulative_commission, cumulative_slippage, "final cumulative costs",
        ),
        "max_drawdown_pct": max_drawdown,
        "halted": halted,
        "assumption_violations": violations,
        "disclaimer": DISCLAIMER,
        "performance_disclaimer": PERFORMANCE_DISCLAIMER,
    }


def run_backtest(strategy_rules, historical_pack, risk_policy=None):
    """Validate and evaluate one declarative SMA-001 rule and one instrument."""
    raw_strategy_identity = _safe_raw_strategy_identity(strategy_rules)
    strategy, strategy_errors, position_limit = validate_strategy(strategy_rules)
    data_errors = validate_market_pack(historical_pack)
    policy = None
    policy_errors = []
    if not strategy_errors:
        policy, policy_errors = _effective_policy(risk_policy, strategy)

    if data_errors:
        input_hash, input_hash_issues = _canonical_sha256_with_issues(
            historical_pack
        )
    else:
        input_hash_issues = []
        try:
            input_hash = _streaming_canonical_sha256(historical_pack)
        except _CanonicalStreamingError as error:
            input_hash, input_hash_issues = _canonical_sha256_with_issues(
                historical_pack
            )
            data_errors.append(
                "pack canonical hashing failed closed: %s" % error.error_name
            )

    raw_strategy_material = {
        "strategy": strategy_rules,
        "risk_policy": risk_policy,
        "system_limits": _system_risk_limits(),
        "costs": {"commission_rate": COMMISSION_RATE,
                  "slippage_rate": SLIPPAGE_RATE},
        "execution": "BAR_CLOSE_T_TO_NEXT_VALIDATED_BAR_OPEN",
        "terminal": "MARK_TO_MARKET_OPEN",
        "starting_cash": STARTING_CASH,
    }
    if strategy_errors or policy_errors:
        raw_strategy_hash, strategy_hash_issues = (
            _canonical_sha256_with_issues(raw_strategy_material)
        )
    else:
        strategy_hash_issues = []
        try:
            raw_strategy_hash = _streaming_canonical_sha256(
                raw_strategy_material
            )
        except _CanonicalStreamingError as error:
            raw_strategy_hash, strategy_hash_issues = (
                _canonical_sha256_with_issues(raw_strategy_material)
            )
            strategy_errors.append(
                "strategy canonical hashing failed closed: %s" % error.error_name
            )
    try:
        engine_source_digest = _engine_source_digest()
    except ReproducibilityError:
        metadata = _reproducibility_failure_metadata(
            historical_pack, input_hash, raw_strategy_hash, raw_strategy_identity,
        )
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_REPRODUCIBILITY_ERROR,
            ["engine source digest could not be established; execution failed closed"],
        )

    if input_hash_issues:
        data_errors.extend(
            "pack canonicalization rejected: %s" % issue
            for issue in sorted(set(input_hash_issues))
        )
    if strategy_hash_issues:
        strategy_errors.extend(
            "strategy canonicalization rejected: %s" % issue
            for issue in sorted(set(strategy_hash_issues))
        )
    if data_errors:
        metadata_policy = policy if policy is not None else _system_risk_limits()
        metadata = _metadata(
            historical_pack,
            strategy if not strategy_errors else None,
            input_hash,
            raw_strategy_hash,
            metadata_policy,
            engine_source_digest=engine_source_digest,
            raw_strategy_identity=(None if not strategy_errors
                                   else raw_strategy_identity),
        )
        return _empty_result(metadata, OUTCOME_BLOCKED, BLOCKED_INVALID_INPUT,
                             data_errors)

    symbol = historical_pack["instruments"][0]["symbol"]
    if not strategy_errors and strategy["symbol"] != symbol:
        strategy_errors.append("strategy symbol does not match instrument symbol")
    base_policy = _system_risk_limits()
    if strategy_errors:
        metadata = _metadata(
            historical_pack, None, input_hash, raw_strategy_hash, base_policy,
            engine_source_digest=engine_source_digest,
            raw_strategy_identity=raw_strategy_identity,
        )
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_INVALID_STRATEGY_PARAMETERS,
            strategy_errors,
        )
    if position_limit:
        metadata_policy = policy if policy is not None else base_policy
        metadata = _metadata(historical_pack, strategy, input_hash,
                             raw_strategy_hash, metadata_policy,
                             engine_source_digest=engine_source_digest)
        return _empty_result(metadata, OUTCOME_BLOCKED, BLOCKED_POSITION_LIMIT,
                             [position_limit])
    if policy_errors:
        metadata = _metadata(historical_pack, strategy, input_hash,
                             raw_strategy_hash, base_policy,
                             engine_source_digest=engine_source_digest)
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_RISK_OVERRIDE_ATTEMPT,
            policy_errors,
        )
    if strategy["paper_size_pct"] > policy["max_position_pct"]:
        metadata = _metadata(historical_pack, strategy, input_hash,
                             raw_strategy_hash, policy,
                             engine_source_digest=engine_source_digest)
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_POSITION_LIMIT,
            ["requested paper_size_pct exceeds the effective stricter limit"],
        )

    strategy_hash = canonical_sha256({
        "strategy": strategy,
        "effective_policy": policy,
        "costs": {"commission_rate": COMMISSION_RATE,
                  "slippage_rate": SLIPPAGE_RATE},
        "execution": "BAR_CLOSE_T_TO_NEXT_VALIDATED_BAR_OPEN",
        "terminal": "MARK_TO_MARKET_OPEN",
        "starting_cash": STARTING_CASH,
    })
    metadata = _metadata(
        historical_pack, strategy, input_hash, strategy_hash, policy,
        engine_source_digest=engine_source_digest,
    )
    try:
        return _run_validated(strategy, historical_pack, policy, metadata)
    except AllocationSafetyError as error:
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_INVALID_STRATEGY_PARAMETERS,
            ["allocation calculation rejected: %s" % error],
        )
    except NumericSafetyError as error:
        return _empty_result(
            metadata, OUTCOME_BLOCKED, BLOCKED_INVALID_INPUT,
            ["numeric calculation rejected: %s" % error],
        )


def performance_report_markdown(report, title="Paper Portfolio Performance Report"):
    """Render a deterministic in-memory paper-only report."""
    metadata = report["metadata"]
    instrument = metadata.get("instrument") or {}
    lines = [
        "# %s" % title,
        "",
        "> \"%s\"" % DISCLAIMER,
        "",
        "> %s" % PERFORMANCE_DISCLAIMER,
        "",
        "## Research Identity",
        "",
        "- Run: %s" % metadata["run_id"],
        "- Engine: %s %s" % (metadata["engine"]["name"],
                              metadata["engine"]["version"]),
        "- Strategy: %s %s" % (metadata.get("strategy_id"),
                                metadata.get("strategy_version")),
        "- Data pack / as-of: %s / %s" % (metadata.get("pack_id"),
                                           metadata.get("data_as_of")),
        "- Instrument: %s (%s)" % (instrument.get("symbol"),
                                    instrument.get("asset_class")),
        "- Outcome: %s / %s" % (report["outcome"], report["reason_code"]),
        "",
        "## Mark-to-Market Accounting",
        "",
        "- Final cash: %.8f" % report["final_cash"],
        "- Final marked equity: %.8f" % report["final_equity"],
        "- Realized P&L: %.8f" % report["realized_pnl"],
        "- Unrealized P&L: %.8f" % report["unrealized_pnl"],
        "- Commission: %.8f" % report["cumulative_commission"],
        "- Slippage allowance: %.8f" % report["cumulative_slippage_cost"],
        "- Maximum marked drawdown: %.8f%%" % report["max_drawdown_pct"],
        "",
        "## Closed Hypothetical Trades",
        "",
    ]
    if report["trade_list"]:
        for trade in report["trade_list"]:
            lines.append(
                "- %s: entry signal %s, fill %s; exit signal %s, fill %s; "
                "net realized P&L %.8f"
                % (trade["symbol"], trade["entry_signal_time"],
                   trade["entry_fill_time"], trade["exit_signal_time"],
                   trade["exit_fill_time"], trade["net_realized_pnl"])
            )
    else:
        lines.append("- None.")
    lines += ["", "## Terminal Position", ""]
    if report["open_position"]:
        position = report["open_position"]
        lines.append(
            "- OPEN: %.12f units, entry fill %s @ %.8f, final market value "
            "%.8f, unrealized P&L %.8f. No terminal liquidation was invented."
            % (position["units"], position["entry_fill_time"],
               position["slipped_fill_price"], position["market_value"],
               position["unrealized_pnl"])
        )
    else:
        lines.append("- None.")
    unfilled = [decision for decision in report["decisions"]
                if decision["status"] == "NO_FILL"]
    lines += ["", "## Unfilled Signals", ""]
    if unfilled:
        for decision in unfilled:
            lines.append("- %s at %s: %s" % (
                decision["action"], decision["signal_timestamp"],
                decision["reason_code"],
            ))
    else:
        lines.append("- None.")
    lines += [
        "", "---", "",
        "*PAPER/RESEARCH ONLY. %s*" % PERFORMANCE_DISCLAIMER,
        "",
    ]
    return "\n".join(lines)


def decision_log_entry(decision_id, input_packs, manager_proposal, bull_ref,
                       bear_ref, unknowns, human_decision, human_name,
                       risk_checks):
    """Construct a passive human decision record; never decide automatically."""
    if human_decision not in ("ACCEPT", "REJECT", "PENDING"):
        raise RiskPolicyViolation(
            "human_decision must be ACCEPT, REJECT, or PENDING - never auto-set"
        )
    return {
        "decision_id": decision_id,
        "input_packs": input_packs,
        "manager_proposal": manager_proposal,
        "bull_case_ref": bull_ref,
        "bear_case_ref": bear_ref,
        "unknowns": unknowns,
        "human_decision": human_decision,
        "human_name": human_name,
        "risk_policy_checks": risk_checks,
    }


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        pack_path = os.path.join(BASE, "sample_data", "TRL-PACK-DEMO.json")
        with open(pack_path, encoding="utf-8") as handle:
            demo_pack = json.load(handle)
        demo_strategy = {
            "strategy_id": STRATEGY_ID,
            "strategy_version": STRATEGY_VERSION,
            "family": STRATEGY_FAMILY,
            "symbol": "DEMO-EQ-A",
            "fast": 5,
            "slow": 20,
            "paper_size_pct": 5.0,
        }
        demo_report = run_backtest(demo_strategy, demo_pack)
        print(canonical_json(demo_report))
