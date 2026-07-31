"""Authoritative operating-mode state machine and capability matrix.

This is the single governed source of truth for which Trading Lab
capabilities are active. No other module decides mode; every subsystem
that needs to know what is permitted consults this service.

Distinct from the static `trading_lab_app.OPERATING_MODE` string constant,
which describes this checkpoint's overall capability envelope and does not
change at runtime. This module implements the dynamic, persisted,
audited state machine described in the TRL Phase 3 design.
"""

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Optional

from .timeline_data import (
    deterministic_json_text,
    format_utc,
    sha256_text,
    validate_utc_timestamp,
)


MODE_STORE_SCHEMA = "TRL_OPERATING_MODE_STORE.v1"
MODE_STORE_ID = "trl-operating-mode-local-store-v1"
MODE_EVENT_SCHEMA = "TRL_MODE_TRANSITION_EVENT.v1"
MAX_MODE_EVENTS = 2000
MAX_MODE_STORE_BYTES = 512 * 1024
MAX_PAYLOAD_BYTES = 8 * 1024
MAX_TEXT_LENGTH = 256
GENESIS_HASH = "0" * 64

MODES = (
    "OFF",
    "RESEARCH",
    "SYNTHETIC_PAPER",
    "MT5_DEMO_MANUAL",
    "MT5_DEMO_AUTOMATED",
    "MT5_LIVE_MANUAL",
    "MT5_LIVE_AUTOMATED",
)

MT5_MODES = (
    "MT5_DEMO_MANUAL",
    "MT5_DEMO_AUTOMATED",
    "MT5_LIVE_MANUAL",
    "MT5_LIVE_AUTOMATED",
)

CAPABILITIES = (
    "historical_research",
    "strategy_evaluation",
    "synthetic_evidence",
    "forward_paper_fills",
    "live_market_data_read",
    "mt5_read_only_access",
    "mt5_order_check",
    "mt5_order_send",
    "manual_broker_execution",
    "automated_broker_execution",
    "basket_execution",
    "tradingview_proposal_intake",
    "private_remote_access",
    "live_arming",
    "emergency_controls",
    "report_export",
)

REASON_CODES = (
    "UNKNOWN_MODE",
    "MODE_UNAVAILABLE",
    "MISSING_MT5_ADAPTER",
    "MISSING_LIVE_ARMING",
    "MISSING_PRIVATE_AUTH",
    "INVALID_TRANSITION",
    "PERSISTED_STATE_INVALID",
    "PERSISTENCE_FAILED",
    "SUBSYSTEM_ACTIVATION_FAILED",
    "STARTUP_LIVE_AUTOMATION_FORBIDDEN",
    "CAPABILITY_DENIED",
    "MODE_CHANGE_REQUIRES_LOCAL_OPERATOR",
)

EVENT_TYPES = (
    "MODE_STATE_LOADED",
    "MODE_STATE_DEFAULTED",
    "MODE_STATE_CORRUPTION_RECOVERED",
    "MODE_TRANSITION_REQUESTED",
    "MODE_TRANSITION_ACCEPTED",
    "MODE_TRANSITION_REJECTED",
    "MODE_TRANSITION_COMPLETED",
    "MODE_TRANSITION_ROLLED_BACK",
    "MODE_CAPABILITY_UNAVAILABLE",
    "MODE_STARTUP_SAFE_DOWNGRADE",
)

# Which local-operator channels may request a transition at all. Nothing in
# this module ever accepts "HTTP" / "REMOTE" / "BROWSER" here — there is no
# HTTP mutation route for mode in Phase 3, and this gate is defense in depth
# in case one is ever wired up by mistake in a later change.
_PERMITTED_ACTOR_CHANNELS = ("LOCAL_OPERATOR", "STARTUP", "SYSTEM")

MODE_DESCRIPTIONS = {
    "OFF": (
        "No strategy evaluation loop, no forward-paper execution, no MT5 "
        "connection, no broker mutation. Read-only static application "
        "health may remain available. The safest default on a new "
        "installation or invalid state."
    ),
    "RESEARCH": (
        "Historical research, deterministic strategy analysis and reports "
        "only. No forward-paper fills, no broker order execution, no MT5 "
        "mutation. Read-only governed market evidence may be used where "
        "already authorized."
    ),
    "SYNTHETIC_PAPER": (
        "The existing synthetic demonstration mode. Synthetic evidence "
        "only; no live market data, no external broker, no broker "
        "credentials, no external network call."
    ),
    "MT5_DEMO_MANUAL": (
        "Represents future manually confirmed MT5 demo execution. "
        "Unavailable until the Phase 5 MT5 execution adapter exists."
    ),
    "MT5_DEMO_AUTOMATED": (
        "Represents future governed automated MT5 demo execution. "
        "Unavailable until the Phase 5 MT5 execution adapter and Phase 9 "
        "automation-arming controls exist."
    ),
    "MT5_LIVE_MANUAL": (
        "Represents future Founder-confirmed, one-proposal-at-a-time live "
        "execution. Unavailable until the Phase 5 MT5 execution adapter "
        "exists. No Phase 3 code may connect to MT5 or submit an order."
    ),
    "MT5_LIVE_AUTOMATED": (
        "Represents future armed automated live execution. Unavailable "
        "until the Phase 5 MT5 execution adapter and Phase 9 live-arming "
        "capability exist. Never activates merely because a stored mode "
        "value says so."
    ),
}

# The capabilities each mode would grant. For the four MT5 modes this is the
# intended future grant, recorded for documentation/forward-compatibility —
# it is never actually applied in Phase 3 because those modes can never be
# entered (see _AVAILABLE_MODES / _UNAVAILABLE_REASONS below).
_CAPABILITY_MATRIX = {
    "OFF": frozenset(),
    "RESEARCH": frozenset({
        "historical_research", "strategy_evaluation", "report_export",
        "mt5_read_only_access", "live_market_data_read",
    }),
    "SYNTHETIC_PAPER": frozenset({
        "synthetic_evidence", "forward_paper_fills", "report_export",
    }),
    "MT5_DEMO_MANUAL": frozenset({
        "mt5_read_only_access", "mt5_order_check", "mt5_order_send",
        "manual_broker_execution", "emergency_controls", "report_export",
    }),
    "MT5_DEMO_AUTOMATED": frozenset({
        "mt5_read_only_access", "mt5_order_check", "mt5_order_send",
        "manual_broker_execution", "automated_broker_execution",
        "basket_execution", "emergency_controls", "report_export",
    }),
    "MT5_LIVE_MANUAL": frozenset({
        "mt5_read_only_access", "mt5_order_check", "mt5_order_send",
        "manual_broker_execution", "emergency_controls", "report_export",
    }),
    "MT5_LIVE_AUTOMATED": frozenset({
        "mt5_read_only_access", "mt5_order_check", "mt5_order_send",
        "manual_broker_execution", "automated_broker_execution",
        "basket_execution", "live_arming", "emergency_controls",
        "report_export",
    }),
}

# Modes that can actually be entered in this checkpoint. All four MT5 modes
# are represented in MODES/_CAPABILITY_MATRIX/MODE_DESCRIPTIONS but are never
# available here, because no MT5 execution adapter (Phase 5) or live-arming
# capability (Phase 9) has been implemented yet.
_AVAILABLE_MODES = frozenset({"OFF", "RESEARCH", "SYNTHETIC_PAPER"})

_UNAVAILABLE_REASONS = {
    "MT5_DEMO_MANUAL": ("MISSING_MT5_ADAPTER",),
    "MT5_DEMO_AUTOMATED": ("MISSING_MT5_ADAPTER", "MISSING_LIVE_ARMING"),
    "MT5_LIVE_MANUAL": ("MISSING_MT5_ADAPTER",),
    "MT5_LIVE_AUTOMATED": ("MISSING_MT5_ADAPTER", "MISSING_LIVE_ARMING"),
}

# The exact allowed transition matrix among currently-available modes. MT5
# modes have no entries here at all (source or destination) because they can
# never be the current mode nor a reachable destination in Phase 3; requests
# targeting them are rejected earlier, during the availability check.
_ALLOWED_TRANSITIONS = {
    "OFF": frozenset({"RESEARCH", "SYNTHETIC_PAPER"}),
    "RESEARCH": frozenset({"OFF", "SYNTHETIC_PAPER"}),
    "SYNTHETIC_PAPER": frozenset({"OFF", "RESEARCH"}),
}


class ModeValidationError(ValueError):
    """A stable, non-secret operating-mode validation failure."""


class ModeStorageError(RuntimeError):
    """Controlled storage failure with no path or exception-detail disclosure."""


class ModeStorageValidationError(ModeStorageError):
    """Invalid persisted content; callers must fail closed."""


def _sha256_text(value):
    return sha256_text(value)


def _stable_id(prefix, *parts):
    material = "\n".join(str(part) for part in parts)
    return prefix + _sha256_text(material)[:32]


def _bounded_text(value, field_name, maximum=MAX_TEXT_LENGTH, allow_empty=False):
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ModeValidationError("{} must be a string".format(field_name))
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise ModeValidationError("{} contains a control character".format(field_name))
    if not allow_empty and not value:
        raise ModeValidationError("{} must not be empty".format(field_name))
    return value[:maximum]


def validate_mode(value):
    if not isinstance(value, str) or value not in MODES:
        raise ModeValidationError("operating mode is not governed")
    return value


def capabilities_for(mode):
    """Return the frozenset of capabilities the given mode would grant."""
    validate_mode(mode)
    return _CAPABILITY_MATRIX[mode]


def is_available(mode):
    validate_mode(mode)
    return mode in _AVAILABLE_MODES


def unavailable_reasons(mode):
    """Return the ordered tuple of reason codes a mode is unavailable for."""
    validate_mode(mode)
    return _UNAVAILABLE_REASONS.get(mode, ())


def prerequisite_results(mode):
    """Return a structured prerequisite-check list for the given mode."""
    validate_mode(mode)
    if mode in _AVAILABLE_MODES:
        return [{"prerequisite": "mode_available", "satisfied": True, "reason": None}]
    results = []
    for reason in _UNAVAILABLE_REASONS.get(mode, ("MODE_UNAVAILABLE",)):
        prerequisite_name = {
            "MISSING_MT5_ADAPTER": "mt5_execution_adapter",
            "MISSING_LIVE_ARMING": "live_arming_capability",
        }.get(reason, "mode_available")
        results.append({
            "prerequisite": prerequisite_name,
            "satisfied": False,
            "reason": reason,
        })
    return results


def allowed_destinations(mode):
    """Return the modes reachable directly from the given mode."""
    validate_mode(mode)
    return _ALLOWED_TRANSITIONS.get(mode, frozenset())


def _sanitize_payload_value(value, depth=0):
    if depth > 6:
        raise ModeValidationError("mode payload nesting exceeds the bound")
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        return _bounded_text(value, "payload string", allow_empty=True)
    if isinstance(value, (list, tuple)):
        if len(value) > 128:
            raise ModeValidationError("mode payload list exceeds the item bound")
        return [_sanitize_payload_value(item, depth + 1) for item in value]
    if isinstance(value, dict):
        if len(value) > 64:
            raise ModeValidationError("mode payload object exceeds the item bound")
        clean = {}
        for key, item in value.items():
            if not isinstance(key, str) or not key or len(key) > 64:
                raise ModeValidationError("mode payload key is not canonical")
            clean[key] = _sanitize_payload_value(item, depth + 1)
        return clean
    raise ModeValidationError("mode payload contains an unsupported type")


def _require_exact_keys(value, expected, label):
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ModeValidationError("{} has an invalid field set".format(label))


def _event_without_current_hash(event):
    return {key: value for key, value in event.items() if key != "current_event_hash"}


def _validate_event(event, previous_event=None, seen_ids=None):
    expected = (
        "schema_version", "event_id", "event_type", "occurred_at_utc",
        "append_sequence", "payload", "payload_sha256",
        "previous_event_hash", "current_event_hash",
    )
    _require_exact_keys(event, expected, "mode transition event")
    if event["schema_version"] != MODE_EVENT_SCHEMA:
        raise ModeValidationError("mode event schema is unsupported")
    if event["event_type"] not in EVENT_TYPES:
        raise ModeValidationError("mode event type is not governed")
    occurred = validate_utc_timestamp(event["occurred_at_utc"], "occurred_at_utc")
    if previous_event is not None:
        prior_occurred = validate_utc_timestamp(previous_event["occurred_at_utc"])
        if occurred < prior_occurred:
            raise ModeValidationError("mode event was backdated")
    sequence = event["append_sequence"]
    if isinstance(sequence, bool) or not isinstance(sequence, int) or sequence < 1:
        raise ModeValidationError("mode append sequence must be a positive integer")
    expected_sequence = 1 if previous_event is None else previous_event["append_sequence"] + 1
    if sequence != expected_sequence:
        raise ModeValidationError("mode append sequence is not contiguous")
    clean_payload = _sanitize_payload_value(event["payload"])
    payload_text = deterministic_json_text(clean_payload)
    if len(payload_text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        raise ModeValidationError("mode payload exceeds the byte bound")
    payload_hash = _sha256_text(payload_text)
    if event["payload_sha256"] != payload_hash:
        raise ModeValidationError("mode payload hash mismatch")
    previous_hash = GENESIS_HASH if previous_event is None else previous_event["current_event_hash"]
    if event["previous_event_hash"] != previous_hash:
        raise ModeValidationError("mode previous-event hash mismatch")
    stable_fields = {
        "schema_version": MODE_EVENT_SCHEMA,
        "event_type": event["event_type"],
        "occurred_at_utc": event["occurred_at_utc"],
        "payload_sha256": payload_hash,
    }
    expected_id = "mev_" + _sha256_text(deterministic_json_text(stable_fields))[:32]
    if event["event_id"] != expected_id:
        raise ModeValidationError("mode event ID mismatch")
    expected_current = _sha256_text(
        deterministic_json_text(_event_without_current_hash(event))
    )
    if event["current_event_hash"] != expected_current:
        raise ModeValidationError("mode current-event hash mismatch")
    if seen_ids is not None and event["event_id"] in seen_ids:
        raise ModeValidationError("duplicate mode event ID")
    clean_event = deepcopy(event)
    clean_event["payload"] = clean_payload
    return clean_event


class ModeTransitionLog:
    """An in-memory validated hash chain of mode transition/audit events."""

    def __init__(self, events=None):
        self._events = []
        if events:
            seen_ids = set()
            previous = None
            for candidate in events:
                clean = _validate_event(candidate, previous, seen_ids)
                self._events.append(clean)
                seen_ids.add(clean["event_id"])
                previous = clean
        self._validate_bounds()

    @property
    def events(self):
        return deepcopy(self._events)

    @property
    def tail_hash(self):
        return self._events[-1]["current_event_hash"] if self._events else GENESIS_HASH

    def _validate_bounds(self):
        if len(self._events) > MAX_MODE_EVENTS:
            raise ModeValidationError("mode event count exceeds the bound")
        encoded = deterministic_json_text(self.to_document()).encode("utf-8")
        if len(encoded) > MAX_MODE_STORE_BYTES:
            raise ModeValidationError("mode event log exceeds the byte bound")

    def append(self, event_type, occurred_at_utc, payload):
        if event_type not in EVENT_TYPES:
            raise ModeValidationError("mode event type is not governed")
        validate_utc_timestamp(occurred_at_utc, "occurred_at_utc")
        if self._events:
            prior = validate_utc_timestamp(self._events[-1]["occurred_at_utc"])
            if validate_utc_timestamp(occurred_at_utc) < prior:
                raise ModeValidationError("mode event was backdated")
        clean_payload = _sanitize_payload_value(payload)
        payload_text = deterministic_json_text(clean_payload)
        if len(payload_text.encode("utf-8")) > MAX_PAYLOAD_BYTES:
            raise ModeValidationError("mode payload exceeds the byte bound")
        payload_hash = _sha256_text(payload_text)
        stable_fields = {
            "schema_version": MODE_EVENT_SCHEMA,
            "event_type": event_type,
            "occurred_at_utc": occurred_at_utc,
            "payload_sha256": payload_hash,
        }
        event_id = "mev_" + _sha256_text(deterministic_json_text(stable_fields))[:32]
        if any(item["event_id"] == event_id for item in self._events):
            raise ModeValidationError("duplicate mode event ID")
        event = dict(stable_fields)
        event.update({
            "event_id": event_id,
            "append_sequence": len(self._events) + 1,
            "payload": clean_payload,
            "previous_event_hash": self.tail_hash,
        })
        event["current_event_hash"] = _sha256_text(
            deterministic_json_text(_event_without_current_hash(event))
        )
        clean = _validate_event(
            event, self._events[-1] if self._events else None,
            {item["event_id"] for item in self._events},
        )
        self._events.append(clean)
        try:
            self._validate_bounds()
        except Exception:
            self._events.pop()
            raise
        return deepcopy(clean)

    def to_document(self):
        return {
            "schema_version": "TRL_MODE_TRANSITION_LOG.v1",
            "event_count": len(self._events),
            "tail_event_hash": self.tail_hash,
            "events": deepcopy(self._events),
        }

    @classmethod
    def from_document(cls, document):
        expected = ("schema_version", "event_count", "tail_event_hash", "events")
        _require_exact_keys(document, expected, "mode transition log")
        if document["schema_version"] != "TRL_MODE_TRANSITION_LOG.v1":
            raise ModeValidationError("mode transition log schema is unsupported")
        count = document["event_count"]
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ModeValidationError("mode event count is invalid")
        if not isinstance(document["events"], list) or count != len(document["events"]):
            raise ModeValidationError("mode transition log is truncated or count-mismatched")
        log = cls(document["events"])
        if document["tail_event_hash"] != log.tail_hash:
            raise ModeValidationError("mode transition log tail hash mismatch")
        return log


def validate_storage_document(document):
    expected = {"schema_version", "storage_id", "session_started_at_utc", "log"}
    if not isinstance(document, dict) or set(document) != expected:
        raise ModeStorageValidationError("mode storage has an invalid field set")
    if document["schema_version"] != MODE_STORE_SCHEMA:
        raise ModeStorageValidationError("mode storage schema is unsupported")
    if document["storage_id"] != MODE_STORE_ID:
        raise ModeStorageValidationError("mode storage identity is invalid")
    try:
        validate_utc_timestamp(document["session_started_at_utc"])
        log = ModeTransitionLog.from_document(document["log"])
    except ModeValidationError as error:
        raise ModeStorageValidationError(str(error)) from error
    clean = {
        "schema_version": MODE_STORE_SCHEMA,
        "storage_id": MODE_STORE_ID,
        "session_started_at_utc": document["session_started_at_utc"],
        "log": log.to_document(),
    }
    if len((deterministic_json_text(clean) + "\n").encode("utf-8")) > MAX_MODE_STORE_BYTES:
        raise ModeStorageValidationError("mode storage exceeds the byte bound")
    return clean


def storage_document(session_started_at_utc, log):
    if not isinstance(log, ModeTransitionLog):
        raise ModeStorageValidationError("mode storage requires a validated transition log")
    return validate_storage_document({
        "schema_version": MODE_STORE_SCHEMA,
        "storage_id": MODE_STORE_ID,
        "session_started_at_utc": session_started_at_utc,
        "log": log.to_document(),
    })


class InMemoryModeStateStore:
    """Exact serialization round-trip storage used by deterministic tests."""

    def __init__(self, initial_document=None):
        self._document = None
        self.fail_writes = False
        self.save_count = 0
        if initial_document is not None:
            self._document = deepcopy(validate_storage_document(initial_document))

    def load(self):
        if self._document is None:
            return None
        raw = (deterministic_json_text(self._document) + "\n").encode("utf-8")
        return _parse_document(raw)

    def save(self, document):
        clean = validate_storage_document(document)
        raw = (deterministic_json_text(clean) + "\n").encode("utf-8")
        clean = _parse_document(raw)
        if self.fail_writes:
            raise ModeStorageError("mode storage atomic write failed")
        self._document = deepcopy(clean)
        self.save_count += 1

    def replace_raw_for_test(self, raw):
        if isinstance(raw, bytes):
            self._document = json.loads(raw.decode("utf-8"))
        else:
            self._document = deepcopy(raw)

    def shutdown(self):
        return True


def _reject_constant(_value):
    raise ModeStorageValidationError("mode storage contains a non-finite number")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ModeStorageValidationError("mode storage contains a duplicate object key")
        result[key] = value
    return result


def _parse_document(raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_MODE_STORE_BYTES:
        raise ModeStorageValidationError("mode storage exceeds the byte bound")
    try:
        text = raw.decode("utf-8", errors="strict")
        document = json.loads(
            text, parse_constant=_reject_constant, object_pairs_hook=_unique_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ModeStorageValidationError("mode storage is not strict UTF-8 JSON") from error
    return validate_storage_document(document)


def default_mode_store_path():
    """Return an isolated application-data path; never create it here."""
    local_data = os.environ.get("LOCALAPPDATA")
    root = Path(local_data) if local_data else Path.home() / "AppData" / "Local"
    return root / "ALSAKKAF" / "TradingLab" / "operating-mode-state-v1.json"


class LocalModeStateStore:
    """Atomic single-document storage, mirroring the paper store's design."""

    def __init__(self, path=None):
        self.path = Path(path) if path is not None else default_mode_store_path()

    def load(self):
        if not self.path.exists():
            return None
        try:
            raw = self.path.read_bytes()
            return _parse_document(raw)
        except ModeStorageValidationError:
            raise
        except OSError as error:
            raise ModeStorageError("mode storage read failed") from error

    def save(self, document):
        clean = validate_storage_document(document)
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
            raise ModeStorageError("mode storage atomic write failed") from error
        finally:
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass
                except OSError:
                    pass

    def shutdown(self):
        return True


@dataclass(frozen=True)
class TransitionResult:
    """The outcome of one request_transition call."""

    outcome: str  # ACCEPTED / REJECTED / ROLLED_BACK
    transition_id: str
    requested_mode: str
    previous_mode: str
    resulting_mode: str
    reason_code: Optional[str] = None
    prerequisite_results: tuple = field(default_factory=tuple)


def _default_subsystem_builder(_mode):
    return None


class ModeService:
    """Event-sourced operating-mode state machine. No order/account authority."""

    def __init__(self, store=None, session_started_at_utc=None, subsystem_builder=None):
        self.store = store if store is not None else LocalModeStateStore()
        self._subsystem_builder = subsystem_builder or _default_subsystem_builder
        self._session_started_at_utc = session_started_at_utc or format_utc(
            datetime.now(timezone.utc)
        )
        self._log = ModeTransitionLog()
        self._current_mode = "OFF"
        self._previous_mode = None
        self._last_transition_id = None
        self.persistence_status = "OK"
        self.persistence_failure_count = 0
        self.startup_diagnostic_code = "OK"
        self._shutdown = False
        self._load_startup_state()

    # -- startup -----------------------------------------------------

    def _now(self):
        return format_utc(datetime.now(timezone.utc))

    def _load_startup_state(self):
        try:
            loaded = self.store.load()
        except ModeStorageValidationError:
            self.startup_diagnostic_code = "PERSISTED_STATE_INVALID"
            self._append_event("MODE_STATE_CORRUPTION_RECOVERED", {
                "resulting_mode": "OFF",
                "rejection_reason_code": "PERSISTED_STATE_INVALID",
            }, allow_persist_failure_block=False)
            return
        except ModeStorageError:
            self.startup_diagnostic_code = "PERSISTED_STATE_INVALID"
            self._append_event("MODE_STATE_CORRUPTION_RECOVERED", {
                "resulting_mode": "OFF",
                "rejection_reason_code": "PERSISTED_STATE_INVALID",
            }, allow_persist_failure_block=False)
            return
        if loaded is None:
            self._append_event(
                "MODE_STATE_DEFAULTED", {"resulting_mode": "OFF"},
                allow_persist_failure_block=False,
            )
            return
        try:
            self._log = ModeTransitionLog.from_document(loaded["log"])
        except ModeValidationError:
            self._log = ModeTransitionLog()
            self.startup_diagnostic_code = "PERSISTED_STATE_INVALID"
            self._append_event("MODE_STATE_CORRUPTION_RECOVERED", {
                "resulting_mode": "OFF",
                "rejection_reason_code": "PERSISTED_STATE_INVALID",
            }, allow_persist_failure_block=False)
            return
        resolved_mode = self._replay_current_mode()
        if resolved_mode in MT5_MODES:
            self._current_mode = "OFF"
            self._append_event("MODE_STARTUP_SAFE_DOWNGRADE", {
                "loaded_mode": resolved_mode,
                "resulting_mode": "OFF",
                "rejection_reason_code": "STARTUP_LIVE_AUTOMATION_FORBIDDEN",
            }, allow_persist_failure_block=False)
            return
        self._current_mode = resolved_mode
        self._append_event(
            "MODE_STATE_LOADED", {"resulting_mode": resolved_mode},
            allow_persist_failure_block=False,
        )

    def _replay_current_mode(self):
        mode = "OFF"
        for event in self._log.events:
            if event["event_type"] in ("MODE_TRANSITION_COMPLETED", "MODE_STARTUP_SAFE_DOWNGRADE"):
                candidate = event["payload"].get("resulting_mode")
                if candidate in MODES:
                    mode = candidate
        return mode

    # -- read-only surface --------------------------------------------

    @property
    def current_mode(self):
        return self._current_mode

    @property
    def previous_mode(self):
        return self._previous_mode

    def available_modes(self):
        return sorted(_AVAILABLE_MODES)

    def unavailable_modes(self):
        return {mode: list(unavailable_reasons(mode)) for mode in MT5_MODES}

    def capability_snapshot(self, mode=None):
        target = mode if mode is not None else self._current_mode
        validate_mode(target)
        return sorted(_CAPABILITY_MATRIX[target])

    def has_capability(self, capability, mode=None):
        if capability not in CAPABILITIES:
            raise ModeValidationError("capability is not governed")
        target = mode if mode is not None else self._current_mode
        validate_mode(target)
        return capability in _CAPABILITY_MATRIX[target]

    def explain_mode(self, mode):
        validate_mode(mode)
        available = is_available(mode)
        return {
            "mode": mode,
            "description": MODE_DESCRIPTIONS[mode],
            "available": available,
            "capabilities": sorted(_CAPABILITY_MATRIX[mode]),
            "prerequisite_results": prerequisite_results(mode),
            "reachable_from": sorted(
                source for source, targets in _ALLOWED_TRANSITIONS.items()
                if mode in targets
            ),
            "reachable_to": sorted(_ALLOWED_TRANSITIONS.get(mode, frozenset())),
        }

    def transition_history(self, limit=None):
        events = self._log.events
        if limit is not None:
            events = events[-limit:]
        return events

    def mode_status_document(self):
        broker_execution_available = any(
            "manual_broker_execution" in _CAPABILITY_MATRIX[mode]
            or "automated_broker_execution" in _CAPABILITY_MATRIX[mode]
            for mode in (self._current_mode,)
        )
        automated_trading_available = "automated_broker_execution" in _CAPABILITY_MATRIX[self._current_mode]
        live_arming_available = "live_arming" in _CAPABILITY_MATRIX[self._current_mode]
        private_remote_available = "private_remote_access" in _CAPABILITY_MATRIX[self._current_mode]
        last_events = self._log.events[-1:] if self._log.events else []
        return {
            "schema_version": "TRL_MODE_STATUS.v1",
            "current_mode": self._current_mode,
            "previous_mode": self._previous_mode,
            "available_modes": self.available_modes(),
            "unavailable_modes": self.unavailable_modes(),
            "capability_matrix": {
                mode: sorted(_CAPABILITY_MATRIX[mode]) for mode in MODES
            },
            "current_capabilities": self.capability_snapshot(),
            "broker_execution_available": broker_execution_available,
            "automated_trading_available": automated_trading_available,
            "live_arming_available": live_arming_available,
            "private_remote_access_available": private_remote_available,
            "last_transition": last_events[0] if last_events else None,
            "startup_diagnostic_code": self.startup_diagnostic_code,
            "persistence_status": self.persistence_status,
            "persistence_failure_count": self.persistence_failure_count,
            "session_started_at_utc": self._session_started_at_utc,
        }

    # -- transitions ----------------------------------------------------

    def request_transition(self, requested_mode, actor, reason=None, actor_channel="LOCAL_OPERATOR"):
        if actor_channel not in _PERMITTED_ACTOR_CHANNELS:
            return TransitionResult(
                outcome="REJECTED",
                transition_id=_stable_id("mxn_", self._log.tail_hash, "denied-channel"),
                requested_mode=str(requested_mode)[:MAX_TEXT_LENGTH],
                previous_mode=self._current_mode,
                resulting_mode=self._current_mode,
                reason_code="MODE_CHANGE_REQUIRES_LOCAL_OPERATOR",
            )
        bounded_requested = str(requested_mode)[:MAX_TEXT_LENGTH] if requested_mode is not None else ""
        bounded_actor = _bounded_text(actor, "actor")
        bounded_reason = _bounded_text(reason, "reason", allow_empty=True)
        previous_mode = self._current_mode
        transition_id = _stable_id(
            "mxn_", self._log.tail_hash, bounded_requested, bounded_actor,
            bounded_reason, self._now(),
        )
        self._append_event("MODE_TRANSITION_REQUESTED", {
            "requested_mode": bounded_requested,
            "previous_mode": previous_mode,
            "actor": bounded_actor,
            "reason": bounded_reason,
            "transition_id": transition_id,
        })

        if bounded_requested not in MODES:
            self._append_event("MODE_TRANSITION_REJECTED", {
                "requested_mode": bounded_requested,
                "previous_mode": previous_mode,
                "rejection_reason_code": "UNKNOWN_MODE",
                "transition_id": transition_id,
            })
            return TransitionResult(
                outcome="REJECTED", transition_id=transition_id,
                requested_mode=bounded_requested, previous_mode=previous_mode,
                resulting_mode=previous_mode, reason_code="UNKNOWN_MODE",
            )

        checks = prerequisite_results(bounded_requested)
        if not is_available(bounded_requested):
            primary_reason = next(
                (item["reason"] for item in checks if not item["satisfied"]),
                "MODE_UNAVAILABLE",
            )
            self._append_event("MODE_CAPABILITY_UNAVAILABLE", {
                "requested_mode": bounded_requested,
                "prerequisite_results": checks,
                "transition_id": transition_id,
            })
            self._append_event("MODE_TRANSITION_REJECTED", {
                "requested_mode": bounded_requested,
                "previous_mode": previous_mode,
                "rejection_reason_code": primary_reason,
                "prerequisite_results": checks,
                "transition_id": transition_id,
            })
            return TransitionResult(
                outcome="REJECTED", transition_id=transition_id,
                requested_mode=bounded_requested, previous_mode=previous_mode,
                resulting_mode=previous_mode, reason_code=primary_reason,
                prerequisite_results=tuple(checks),
            )

        if bounded_requested not in _ALLOWED_TRANSITIONS.get(previous_mode, frozenset()):
            self._append_event("MODE_TRANSITION_REJECTED", {
                "requested_mode": bounded_requested,
                "previous_mode": previous_mode,
                "rejection_reason_code": "INVALID_TRANSITION",
                "transition_id": transition_id,
            })
            return TransitionResult(
                outcome="REJECTED", transition_id=transition_id,
                requested_mode=bounded_requested, previous_mode=previous_mode,
                resulting_mode=previous_mode, reason_code="INVALID_TRANSITION",
            )

        self._append_event("MODE_TRANSITION_ACCEPTED", {
            "requested_mode": bounded_requested,
            "previous_mode": previous_mode,
            "transition_id": transition_id,
        })

        try:
            self._subsystem_builder(bounded_requested)
        except Exception:
            self._append_event("MODE_TRANSITION_ROLLED_BACK", {
                "requested_mode": bounded_requested,
                "previous_mode": previous_mode,
                "rejection_reason_code": "SUBSYSTEM_ACTIVATION_FAILED",
                "transition_id": transition_id,
            })
            return TransitionResult(
                outcome="ROLLED_BACK", transition_id=transition_id,
                requested_mode=bounded_requested, previous_mode=previous_mode,
                resulting_mode=previous_mode, reason_code="SUBSYSTEM_ACTIVATION_FAILED",
            )

        committed = self._append_event("MODE_TRANSITION_COMPLETED", {
            "requested_mode": bounded_requested,
            "previous_mode": previous_mode,
            "resulting_mode": bounded_requested,
            "actor": bounded_actor,
            "transition_id": transition_id,
            "capability_snapshot": sorted(_CAPABILITY_MATRIX[bounded_requested]),
        }, hard_gate=True)

        if not committed:
            self._append_event("MODE_TRANSITION_ROLLED_BACK", {
                "requested_mode": bounded_requested,
                "previous_mode": previous_mode,
                "rejection_reason_code": "PERSISTENCE_FAILED",
                "transition_id": transition_id,
            })
            return TransitionResult(
                outcome="ROLLED_BACK", transition_id=transition_id,
                requested_mode=bounded_requested, previous_mode=previous_mode,
                resulting_mode=previous_mode, reason_code="PERSISTENCE_FAILED",
            )

        self._previous_mode = previous_mode
        self._current_mode = bounded_requested
        self._last_transition_id = transition_id
        return TransitionResult(
            outcome="ACCEPTED", transition_id=transition_id,
            requested_mode=bounded_requested, previous_mode=previous_mode,
            resulting_mode=bounded_requested, reason_code=None,
        )

    # -- internals --------------------------------------------------

    def _append_event(self, event_type, payload, allow_persist_failure_block=True, hard_gate=False):
        """Append one audit event. Returns True unless a hard-gated persist failed."""
        occurred = self._now()
        try:
            self._log.append(event_type, occurred, payload)
        except ModeValidationError:
            # A validation failure here is an internal bug, not an
            # operator-triggerable condition; fail closed by refusing to
            # record a malformed event rather than corrupting the chain.
            raise
        document = storage_document(self._session_started_at_utc, self._log)
        try:
            self.store.save(document)
        except ModeStorageError:
            self.persistence_status = "WRITE_FAILED_IN_MEMORY_VALID"
            self.persistence_failure_count += 1
            if hard_gate:
                # Roll back the in-memory append: the mode change this event
                # represents must not take effect if it could not be
                # durably persisted.
                self._log._events.pop()
                return False
            return True
        else:
            self.persistence_status = "OK"
            return True

    def shutdown(self):
        if self._shutdown:
            return True
        self._shutdown = True
        return self.store.shutdown()


def in_memory_mode_service(session_started_at_utc=None, subsystem_builder=None):
    return ModeService(
        store=InMemoryModeStateStore(),
        session_started_at_utc=session_started_at_utc,
        subsystem_builder=subsystem_builder,
    )
