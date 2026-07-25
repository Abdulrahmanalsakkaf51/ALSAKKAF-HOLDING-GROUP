# -*- coding: utf-8 -*-
"""Canonical hashing, numeric safety, and engine-source reproducibility."""
import hashlib
import json
import math
import os

from .constants import (
    COMMISSION_RATE,
    STARTING_CASH,
    _MAX_CANONICAL_DEPTH,
    _MAX_CANONICAL_INTEGER_BITS,
    _MAX_CANONICAL_NODES,
)

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


def _normalized_source_bytes(source_bytes):
    """Return strict UTF-8 source with CRLF and CR normalized to LF."""
    if type(source_bytes) is not bytes:
        raise ReproducibilityError("engine source must be supplied as exact bytes")
    try:
        source_text = source_bytes.decode("utf-8", "strict")
        normalized = source_text.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.encode("utf-8", "strict")
    except UnicodeError as error:
        raise ReproducibilityError(
            "engine source is not safely normalized UTF-8"
        ) from error


def _normalized_source_sha256(source_bytes):
    """Hash strict UTF-8 source after deterministic line normalization."""
    return hashlib.sha256(_normalized_source_bytes(source_bytes)).hexdigest()


def _engine_source_paths():
    """Return sorted repository-relative POSIX paths and absolute paths."""
    core_directory = os.path.dirname(os.path.abspath(__file__))
    lab_directory = os.path.dirname(core_directory)
    repository_root = os.path.abspath(os.path.join(lab_directory, "..", "..", ".."))
    absolute_paths = [os.path.join(lab_directory, "trading_lab.py")]
    try:
        core_names = os.listdir(core_directory)
    except OSError as error:
        raise ReproducibilityError(
            "engine source manifest could not be enumerated"
        ) from error
    absolute_paths.extend(
        os.path.join(core_directory, name)
        for name in core_names
        if name.endswith(".py")
        and os.path.isfile(os.path.join(core_directory, name))
    )
    paths = []
    for absolute_path in absolute_paths:
        relative_path = os.path.relpath(absolute_path, repository_root)
        paths.append((relative_path.replace(os.sep, "/"), absolute_path))
    return sorted(paths, key=lambda item: item[0])


def _engine_source_manifest():
    """Return the deterministic ordered manifest recorded in run metadata."""
    _digest, manifest = _engine_source_snapshot()
    return manifest


def _engine_source_items(source_files=None):
    """Capture one ordered source bundle for digest and manifest production."""
    if source_files is not None:
        if type(source_files) is not dict:
            raise ReproducibilityError(
                "engine source bundle must be an exact dictionary"
            )
        return sorted(source_files.items(), key=lambda item: item[0])

    source_paths = _engine_source_paths()
    source_items = []
    for relative_path, absolute_path in source_paths:
        try:
            with open(absolute_path, "rb") as source_handle:
                source_bytes = source_handle.read()
        except OSError as error:
            raise ReproducibilityError(
                "engine source could not be read for reproducibility"
            ) from error
        source_items.append((relative_path, source_bytes))
    return source_items


def _engine_source_digest_from_items(source_items):
    """Hash one already captured ordered source bundle."""
    digest = hashlib.sha256()
    digest.update(b"TRL_ENGINE_SOURCE_BUNDLE_V1\n")
    for relative_path, source_bytes in source_items:
        if type(relative_path) is not str or type(source_bytes) is not bytes:
            raise ReproducibilityError(
                "engine source bundle paths and contents require exact types"
            )
        try:
            path_bytes = relative_path.encode("utf-8", "strict")
        except UnicodeError as error:
            raise ReproducibilityError(
                "engine source path is not safely encoded UTF-8"
            ) from error
        normalized_bytes = _normalized_source_bytes(source_bytes)
        digest.update(b"PATH\0")
        digest.update(str(len(path_bytes)).encode("ascii"))
        digest.update(b"\0")
        digest.update(path_bytes)
        digest.update(b"\nSIZE\0")
        digest.update(str(len(normalized_bytes)).encode("ascii"))
        digest.update(b"\0")
        digest.update(normalized_bytes)
        digest.update(b"\nEND\0")
        digest.update(path_bytes)
        digest.update(b"\n")
    return digest.hexdigest()


def _engine_source_snapshot(source_files=None):
    """Return digest and manifest derived from one exact ordered snapshot."""
    source_items = _engine_source_items(source_files)
    manifest = []
    for relative_path, source_bytes in source_items:
        if type(relative_path) is not str or type(source_bytes) is not bytes:
            raise ReproducibilityError(
                "engine source bundle paths and contents require exact types"
            )
        manifest.append(relative_path)
    return _engine_source_digest_from_items(source_items), manifest


def _engine_source_bundle_digest(source_files=None):
    """Hash normalized source with explicit path and file boundaries."""
    digest, _manifest = _engine_source_snapshot(source_files)
    return digest


def _engine_source_digest():
    digest, _manifest = _engine_source_snapshot()
    return digest


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
