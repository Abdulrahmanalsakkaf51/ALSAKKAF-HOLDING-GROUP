"""Strict schema, deterministic queries, and eligibility for local strategies."""

import copy
import math
import re

from . import strategy_vault


REGISTRY_SCHEMA_VERSION = "1.0.0"
BACKLOG_SCHEMA_VERSION = "1.0.0"
KERNEL_STRATEGY_DEFINITION_HASH = (
    "e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955"
)
IMPLEMENTATION_STATUSES = (
    "IMPLEMENTED",
    "PLANNED_NOT_IMPLEMENTED",
    "RETIRED",
)
APPROVAL_STATUSES = (
    "EXPERIMENTAL_RESEARCH_ONLY",
    "FOUNDER_REJECTED",
    "PAPER_ELIGIBLE",
    "RETIRED",
)
REASON_CODES = (
    "REGISTRY_VALID",
    "REGISTRY_FILE_MISSING",
    "REGISTRY_UNEXPECTED_FILE",
    "REGISTRY_INVALID_UTF8",
    "REGISTRY_INVALID_JSON",
    "REGISTRY_SCHEMA_INVALID",
    "REGISTRY_DUPLICATE_STRATEGY",
    "REGISTRY_STATUS_COMBINATION_INVALID",
    "REGISTRY_IDENTITY_MISMATCH",
    "REGISTRY_BUNDLE_DIGEST_MISMATCH",
    "REGISTRY_RESEARCH_ELIGIBLE",
    "REGISTRY_NOT_RESEARCH_ELIGIBLE",
    "REGISTRY_STRATEGY_NOT_FOUND",
)
RECORD_FIELDS = frozenset((
    "strategy_id",
    "strategy_version",
    "display_name",
    "family",
    "description",
    "implementation_status",
    "approval_status",
    "research_eligibility",
    "supported_markets",
    "supported_instrument_types",
    "supported_timeframes",
    "required_market_fields",
    "required_indicators",
    "parameter_schema",
    "risk_characteristics",
    "known_limitations",
    "source_checkpoint",
    "kernel_strategy_definition_hash",
    "record_schema_version",
))
BACKLOG_FIELDS = frozenset((
    "backlog_id",
    "display_name",
    "intended_markets",
    "intended_timeframes",
    "required_future_data",
    "research_questions",
    "principal_risks",
    "status",
    "execution_eligible",
))
MAX_STRING_LENGTH = 2048
MAX_LIST_ITEMS = 32
_SEMVER = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
_STRATEGY_ID = re.compile(r"^[A-Z][A-Z0-9]*-[A-Z0-9]+$")
_BACKLOG_ID = re.compile(r"^BACKLOG-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
_CHECKPOINT_ID = re.compile(r"^TRL-R[0-9]+-[0-9]{3}$")
_TOKEN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_PARAMETER_NAME = re.compile(r"^[a-z][a-z0-9_]*$")
_HASH = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_TEXT = re.compile(
    r"(?:\.\.[/\\]|[/\\]{2}|[A-Za-z]:[/\\]|://|\bimport\s+|\blambda\b|"
    r"\beval\s*\(|\bexec\s*\(|\bcompile\s*\(|\bsubprocess\b|__[^ ]*__|\.py\b)",
    re.IGNORECASE,
)


class SchemaViolation(Exception):
    """Internal validation failure with a stable public reason code."""

    def __init__(self, reason_code="REGISTRY_SCHEMA_INVALID"):
        super().__init__(reason_code)
        self.reason_code = reason_code


def _exact_dict(value):
    if type(value) is not dict:
        raise SchemaViolation()
    if not all(type(key) is str for key in value):
        raise SchemaViolation()


def _fields(value, expected):
    _exact_dict(value)
    if frozenset(value) != expected:
        raise SchemaViolation()


def _string(value, pattern=None):
    if type(value) is not str or not value.strip() or value != value.strip():
        raise SchemaViolation()
    if len(value) > MAX_STRING_LENGTH or _UNSAFE_TEXT.search(value):
        raise SchemaViolation()
    if pattern is not None and pattern.fullmatch(value) is None:
        raise SchemaViolation()


def _enum(value, allowed):
    _string(value)
    if value not in allowed:
        raise SchemaViolation()


def _set_like_strings(value, pattern=None):
    if type(value) is not list or not value or len(value) > MAX_LIST_ITEMS:
        raise SchemaViolation()
    for item in value:
        _string(item, pattern=pattern)
    if value != sorted(value) or len(value) != len(set(value)):
        raise SchemaViolation()


def _number(value):
    if type(value) not in (int, float) or type(value) is bool:
        raise SchemaViolation()
    if type(value) is float and not math.isfinite(value):
        raise SchemaViolation()


def _parameter_schema(value):
    _exact_dict(value)
    if not value or len(value) > MAX_LIST_ITEMS:
        raise SchemaViolation()
    if list(value) != sorted(value):
        raise SchemaViolation()
    for name, specification in value.items():
        _string(name, pattern=_PARAMETER_NAME)
        _exact_dict(specification)
        allowed = frozenset(("type", "minimum", "maximum", "exclusive_minimum", "relation"))
        if not specification or not frozenset(specification).issubset(allowed):
            raise SchemaViolation()
        _enum(specification.get("type"), ("INTEGER", "NUMBER"))
        for bound in ("minimum", "maximum", "exclusive_minimum"):
            if bound in specification:
                _number(specification[bound])
                if specification["type"] == "INTEGER" and type(specification[bound]) is not int:
                    raise SchemaViolation()
        if "relation" in specification:
            _enum(specification["relation"], ("LESS_THAN_SLOW",))
        if "minimum" in specification and "maximum" in specification:
            if specification["minimum"] > specification["maximum"]:
                raise SchemaViolation()


def validate_strategy_record(record):
    """Validate the exact executable-record schema; return an isolated copy."""
    _fields(record, RECORD_FIELDS)
    _string(record["strategy_id"], pattern=_STRATEGY_ID)
    _string(record["strategy_version"], pattern=_SEMVER)
    _string(record["display_name"])
    _string(record["family"], pattern=_TOKEN)
    _string(record["description"])
    _enum(record["implementation_status"], IMPLEMENTATION_STATUSES)
    _enum(record["approval_status"], APPROVAL_STATUSES)
    if type(record["research_eligibility"]) is not bool:
        raise SchemaViolation()
    for field in (
        "supported_markets",
        "supported_instrument_types",
        "supported_timeframes",
        "required_indicators",
    ):
        _set_like_strings(record[field], pattern=_TOKEN)
    _set_like_strings(record["required_market_fields"], pattern=_PARAMETER_NAME)
    _set_like_strings(record["risk_characteristics"])
    _set_like_strings(record["known_limitations"])
    _parameter_schema(record["parameter_schema"])
    _string(record["source_checkpoint"], pattern=_CHECKPOINT_ID)
    _string(record["kernel_strategy_definition_hash"], pattern=_HASH)
    _string(record["record_schema_version"], pattern=_SEMVER)
    if record["record_schema_version"] != REGISTRY_SCHEMA_VERSION:
        raise SchemaViolation()

    combination = (record["implementation_status"], record["approval_status"], record["research_eligibility"])
    allowed_combinations = frozenset((
        ("IMPLEMENTED", "EXPERIMENTAL_RESEARCH_ONLY", True),
        ("IMPLEMENTED", "PAPER_ELIGIBLE", True),
        ("IMPLEMENTED", "FOUNDER_REJECTED", False),
        ("PLANNED_NOT_IMPLEMENTED", "EXPERIMENTAL_RESEARCH_ONLY", False),
        ("PLANNED_NOT_IMPLEMENTED", "FOUNDER_REJECTED", False),
        ("RETIRED", "RETIRED", False),
    ))
    if combination not in allowed_combinations:
        raise SchemaViolation("REGISTRY_STATUS_COMBINATION_INVALID")
    return copy.deepcopy(record)


def validate_backlog_document(document):
    """Validate the separately governed, permanently non-executable backlog."""
    _fields(document, frozenset(("backlog_schema_version", "entries")))
    _string(document["backlog_schema_version"], pattern=_SEMVER)
    if document["backlog_schema_version"] != BACKLOG_SCHEMA_VERSION:
        raise SchemaViolation()
    entries = document["entries"]
    if type(entries) is not list or not entries or len(entries) > MAX_LIST_ITEMS:
        raise SchemaViolation()
    ids = []
    validated = []
    for entry in entries:
        _fields(entry, BACKLOG_FIELDS)
        _string(entry["backlog_id"], pattern=_BACKLOG_ID)
        _string(entry["display_name"])
        for field in (
            "intended_markets",
            "intended_timeframes",
            "required_future_data",
            "research_questions",
            "principal_risks",
        ):
            pattern = _TOKEN if field in ("intended_markets", "intended_timeframes") else None
            _set_like_strings(entry[field], pattern=pattern)
        if entry["status"] != "PLANNED_NOT_IMPLEMENTED":
            raise SchemaViolation("REGISTRY_STATUS_COMBINATION_INVALID")
        if type(entry["execution_eligible"]) is not bool or entry["execution_eligible"] is not False:
            raise SchemaViolation("REGISTRY_STATUS_COMBINATION_INVALID")
        ids.append(entry["backlog_id"])
        validated.append(copy.deepcopy(entry))
    if ids != sorted(ids) or len(ids) != len(set(ids)):
        raise SchemaViolation()
    return validated


def _validate_release1_identity(record, release1_strategy):
    _exact_dict(release1_strategy)
    expected_fields = frozenset((
        "strategy_id", "strategy_version", "family", "symbol", "fast", "slow", "paper_size_pct",
    ))
    if frozenset(release1_strategy) != expected_fields:
        raise SchemaViolation("REGISTRY_IDENTITY_MISMATCH")
    if (
        record["strategy_id"] != release1_strategy["strategy_id"]
        or record["strategy_version"] != release1_strategy["strategy_version"]
        or record["family"] != release1_strategy["family"]
        or record["kernel_strategy_definition_hash"] != KERNEL_STRATEGY_DEFINITION_HASH
        or record["source_checkpoint"] != "TRL-R1-004"
    ):
        raise SchemaViolation("REGISTRY_IDENTITY_MISMATCH")
    if type(release1_strategy["symbol"]) is not str or not release1_strategy["symbol"]:
        raise SchemaViolation("REGISTRY_IDENTITY_MISMATCH")
    fast = release1_strategy["fast"]
    slow = release1_strategy["slow"]
    size = release1_strategy["paper_size_pct"]
    if type(fast) is not int or type(slow) is not int or not 1 <= fast < slow:
        raise SchemaViolation("REGISTRY_IDENTITY_MISMATCH")
    if type(size) not in (int, float) or type(size) is bool or not math.isfinite(size) or not 0 < size <= 5.0:
        raise SchemaViolation("REGISTRY_IDENTITY_MISMATCH")
    if set(record["parameter_schema"]) != {"fast", "slow", "paper_size_pct"}:
        raise SchemaViolation("REGISTRY_IDENTITY_MISMATCH")


class RegistrySnapshot:
    """Validated immutable-by-isolation registry view and deterministic queries."""

    def __init__(self, records, backlog, manifest, bundle_digest, record_digests, backlog_digest):
        self._records = tuple(copy.deepcopy(records))
        self._backlog = tuple(copy.deepcopy(backlog))
        self._manifest = tuple(copy.deepcopy(manifest))
        self._bundle_digest = bundle_digest
        self._record_digests = dict(record_digests)
        self._backlog_digest = backlog_digest

    def list_executable(self, market=None, timeframe=None, implementation_status=None, approval_status=None):
        records = []
        for record in self._records:
            if market is not None and market not in record["supported_markets"]:
                continue
            if timeframe is not None and timeframe not in record["supported_timeframes"]:
                continue
            if implementation_status is not None and implementation_status != record["implementation_status"]:
                continue
            if approval_status is not None and approval_status != record["approval_status"]:
                continue
            records.append(self._envelope(record))
        return records

    def _envelope(self, record):
        key = (record["strategy_id"], record["strategy_version"])
        return {
            "record": copy.deepcopy(record),
            "registry_record_digest": self._record_digests[key],
            "eligibility": self.research_eligibility(*key),
        }

    def get(self, strategy_id, strategy_version):
        for record in self._records:
            if record["strategy_id"] == strategy_id and record["strategy_version"] == strategy_version:
                return {"found": True, "reason_code": "REGISTRY_VALID", "strategy": self._envelope(record)}
        return {"found": False, "reason_code": "REGISTRY_STRATEGY_NOT_FOUND", "strategy": None}

    def research_eligibility(self, strategy_id, strategy_version):
        for record in self._records:
            if record["strategy_id"] == strategy_id and record["strategy_version"] == strategy_version:
                eligible = (
                    record["implementation_status"] == "IMPLEMENTED"
                    and record["research_eligibility"] is True
                    and record["approval_status"] in ("EXPERIMENTAL_RESEARCH_ONLY", "PAPER_ELIGIBLE")
                )
                return {
                    "eligible": eligible,
                    "reason_code": "REGISTRY_RESEARCH_ELIGIBLE" if eligible else "REGISTRY_NOT_RESEARCH_ELIGIBLE",
                }
        return {"eligible": False, "reason_code": "REGISTRY_STRATEGY_NOT_FOUND"}

    def list_backlog(self):
        return copy.deepcopy(list(self._backlog))

    def provenance(self):
        return {
            "algorithm": "SHA-256",
            "canonical_json": "UTF-8; SORTED_KEYS; COMPACT_SEPARATORS; TERMINAL_LF",
            "newline_normalization": "CRLF_AND_CR_TO_LF",
            "manifest": copy.deepcopy(list(self._manifest)),
            "bundle_digest": self._bundle_digest,
            "research_backlog_digest": self._backlog_digest,
        }


def _snapshot(records, backlog_document, manifest, bundle_digest, release1_strategy):
    if type(records) is not list:
        raise SchemaViolation()
    validated = []
    keys = set()
    record_digests = {}
    for candidate in records:
        record = validate_strategy_record(candidate)
        key = (record["strategy_id"], record["strategy_version"])
        if key in keys:
            raise SchemaViolation("REGISTRY_DUPLICATE_STRATEGY")
        keys.add(key)
        validated.append(record)
        record_digests[key] = strategy_vault.sha256_hex(strategy_vault.canonical_json_bytes(record))
    validated.sort(key=lambda record: (record["strategy_id"], record["strategy_version"]))
    if len(validated) != 1 or keys != {("SMA-001", "1.0.0")}:
        raise SchemaViolation("REGISTRY_IDENTITY_MISMATCH")
    _validate_release1_identity(validated[0], release1_strategy)
    backlog = validate_backlog_document(backlog_document)
    backlog_digest = strategy_vault.sha256_hex(strategy_vault.canonical_json_bytes(backlog_document))
    return RegistrySnapshot(validated, backlog, manifest, bundle_digest, record_digests, backlog_digest)


class RegistryLoadResult:
    """Success or failure wrapper that never retains a partially valid registry."""

    def __init__(self, status, reason_code, registry=None):
        self.status = status
        self.reason_code = reason_code
        self.registry = registry

    def document(self):
        if self.registry is None:
            executable = []
            backlog = []
            provenance = {
                "algorithm": "SHA-256",
                "canonical_json": "UTF-8; SORTED_KEYS; COMPACT_SEPARATORS; TERMINAL_LF",
                "newline_normalization": "CRLF_AND_CR_TO_LF",
                "manifest": [],
                "bundle_digest": None,
                "research_backlog_digest": None,
            }
        else:
            executable = self.registry.list_executable()
            backlog = self.registry.list_backlog()
            provenance = self.registry.provenance()
        eligible_count = sum(1 for item in executable if item["eligibility"]["eligible"])
        return {
            "registry_health": {"status": self.status, "reason_code": self.reason_code},
            "registry_schema_version": REGISTRY_SCHEMA_VERSION,
            "installed_strategy_count": len(executable),
            "executable_research_strategy_count": eligible_count,
            "installed_executable_strategies": executable,
            "research_backlog": {
                "collection_status": "PLANNED_NOT_IMPLEMENTED",
                "execution_eligible": False,
                "entries": backlog,
            },
            "vault": provenance,
            "boundaries": {
                "registry_selects_best_strategy": False,
                "investment_approved_strategy_exists": False,
                "live_market_data_capability": False,
                "broker_capability": False,
                "execution_capability": False,
                "local_processing_only": True,
            },
            "stable_reason_codes": list(REASON_CODES),
        }


def load_registry(release1_strategy):
    """Load the local registry fail-closed without evaluating a strategy."""
    try:
        vault = strategy_vault.inspect_catalog()
        documents = vault["documents"]
        snapshot = _snapshot(
            [documents[strategy_vault.EXECUTABLE_FILENAME]],
            documents[strategy_vault.BACKLOG_FILENAME],
            vault["manifest"],
            vault["bundle_digest"],
            release1_strategy,
        )
        return RegistryLoadResult("VALID", "REGISTRY_VALID", snapshot)
    except (strategy_vault.VaultFailure, SchemaViolation) as error:
        return RegistryLoadResult("FAILED", error.reason_code, None)
    except (OSError, TypeError, ValueError, OverflowError):
        return RegistryLoadResult("FAILED", "REGISTRY_SCHEMA_INVALID", None)


__all__ = (
    "APPROVAL_STATUSES",
    "BACKLOG_SCHEMA_VERSION",
    "IMPLEMENTATION_STATUSES",
    "KERNEL_STRATEGY_DEFINITION_HASH",
    "REASON_CODES",
    "RECORD_FIELDS",
    "REGISTRY_SCHEMA_VERSION",
    "RegistryLoadResult",
    "RegistrySnapshot",
    "SchemaViolation",
    "load_registry",
    "validate_backlog_document",
    "validate_strategy_record",
)
