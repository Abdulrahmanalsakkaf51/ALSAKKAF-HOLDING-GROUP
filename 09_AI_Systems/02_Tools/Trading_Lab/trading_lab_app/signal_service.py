"""The single authoritative signal-intelligence service (TRL-R2-006).

Owns the governed six-role pipeline's evidence timeline, mode gating, and
persistence. No other module in this application may construct a
proposal, evaluate a strategy, or decide whether signal intelligence is
available — every caller (CLI, HTTP read-only routes, dashboard) goes
through one instance of this service, itself constructed only via
``app.py``'s single mode-gated subsystem-construction path (mirroring
``_paper_service_for_mode``), never via a direct/parallel mode check.

This module never calls ``order_check`` or ``order_send`` and never
imports the real ``MetaTrader5`` module — proposals stay
``PAPER_ONLY_NO_BROKER_ORDER`` regardless of mode.
"""

from copy import deepcopy
from datetime import datetime, timezone

from . import signal_data as sd
from . import signal_pipeline as pipeline
from . import signal_role1_data_quality as role1
from . import signal_strategy_registry as registry
from .paper_data import PAPER_ONLY_STATUS, validate_market_observation
from .paper_data import PaperValidationError
from .signal_llm_adapter import NoOpGenerativeAdapter
from .signal_store import (
    InMemorySignalStore,
    LocalSignalStore,
    SignalStorageError,
    SignalStorageValidationError,
    storage_document,
)
from .timeline_data import GENESIS_HASH, MarketTimeline, TimelineValidationError, format_utc


SIGNAL_SERVICE_SCHEMA = "TRL_SIGNAL_INTELLIGENCE_SERVICE.v1"
SIGNAL_STATUS_SCHEMA = "TRL_SIGNAL_STATUS.v1"
SIGNAL_HISTORY_SCHEMA = "TRL_SIGNAL_PROPOSAL_HISTORY.v1"
SIGNAL_TIMELINE_API_SCHEMA = "TRL_SIGNAL_TIMELINE_API.v1"
ENGINE_BASIS = "TRL-R2-006_SIGNAL_INTELLIGENCE_SERVICE"
MAX_API_PROPOSAL_ITEMS = 200
MAX_API_TIMELINE_EVENTS = 200
_ENABLED_MODES = ("RESEARCH", "SYNTHETIC_PAPER")

# No R2-006 contract-defined reason code covers local-storage corruption
# (an implementation-layer concern, like paper_service.py's own
# INVALID_PAPER_STORAGE/PAPER_STORAGE_READ_FAILED codes), so this stable
# fail-closed reason is defined here, matching the correction's guidance.
SIGNAL_STORE_INTEGRITY_FAILURE = "SIGNAL_STORE_INTEGRITY_FAILURE"


class SignalEngineError(RuntimeError):
    """A controlled fail-closed engine condition (never a broker error)."""


def _disabled_status_document(operating_mode):
    return {
        "schema_version": SIGNAL_STATUS_SCHEMA,
        "enabled": False,
        "operational": False,
        "operating_mode": operating_mode,
        "paper_only_status": PAPER_ONLY_STATUS,
        "signal_generation": False,
        "broker_execution": False,
        "storage_constructed": False,
        "persistence_status": "DISABLED",
        "persistence_failure_count": 0,
        "startup_diagnostic_code": "SIGNAL_ENGINE_DISABLED",
        "strategy_registry": registry.list_strategies(),
        "message": (
            "Signal intelligence is unavailable in the OFF operating mode. "
            "Transition to RESEARCH or SYNTHETIC_PAPER with "
            "'python -m trading_lab_app.mode_cli request-mode RESEARCH' to enable it."
        ),
    }


class DisabledSignalService:
    """Explicit network-silent default that constructs no store, matching
    ``DisabledPaperService``'s no-side-effect-by-default philosophy."""

    enabled = False
    operational = False
    store = None

    def __init__(self, operating_mode="OFF"):
        self.operating_mode = operating_mode

    def status_document(self):
        return _disabled_status_document(self.operating_mode)

    def generate_proposal(self, _evaluation_request_payload):
        raise SignalEngineError(
            "signal intelligence is disabled in the {} operating mode".format(self.operating_mode)
        )

    def proposal_history_document(self):
        return {
            "schema_version": SIGNAL_HISTORY_SCHEMA,
            "enabled": False,
            "proposal_count": 0,
            "response_truncated": False,
            "proposals": [],
        }

    def timeline_document(self):
        return {
            "schema_version": SIGNAL_TIMELINE_API_SCHEMA,
            "timeline_schema_version": "TRL_MARKET_TIMELINE.v1",
            "enabled": False,
            "event_count": 0,
            "tail_event_hash": GENESIS_HASH,
            "response_truncated": False,
            "events": [],
        }

    def strategy_registry_document(self):
        return {"schema_version": registry.REGISTRY_SCHEMA_VERSION, "strategies": registry.list_strategies()}

    def shutdown(self):
        return True


def disabled_service(operating_mode="OFF"):
    return DisabledSignalService(operating_mode)


class SignalIntelligenceService:
    """Event-sourced signal-intelligence engine with no order/account
    authority. Every proposal it produces carries
    ``paper_only_status == PAPER_ONLY_NO_BROKER_ORDER``."""

    enabled = True

    def __init__(self, store=None, operating_mode="RESEARCH", session_started_at_utc=None, adapter=None):
        if operating_mode not in _ENABLED_MODES:
            raise SignalEngineError(
                "SignalIntelligenceService cannot be constructed for operating_mode={!r}; "
                "only {} are permitted".format(operating_mode, _ENABLED_MODES)
            )
        self.operating_mode = operating_mode
        # Matches ForwardPaperService's default exactly: a bare
        # SignalIntelligenceService() persists durably (LocalSignalStore);
        # callers that must not touch the filesystem (every automated test,
        # and the SYNTHETIC_PAPER mode builder) pass InMemorySignalStore()
        # explicitly via in_memory_service().
        self.store = store if store is not None else LocalSignalStore()
        self._adapter = adapter or NoOpGenerativeAdapter()
        self._settings_document = {}
        self._timeline = None
        self._shutdown = False
        self.operational = True
        self.persistence_status = "OK"
        self.persistence_failure_count = 0
        self.startup_diagnostic_code = "OK"
        try:
            loaded = self.store.load()
            if loaded is None:
                self._timeline = MarketTimeline()
                started = session_started_at_utc or format_utc(datetime.now(timezone.utc))
                self._timeline.append(
                    "PAPER_SESSION_EVENT",
                    None,
                    started,
                    started,
                    ENGINE_BASIS,
                    {"event_type": "SESSION_STARTED", "session_started_at_utc": started},
                )
                self._persist()
            else:
                self._timeline = MarketTimeline.from_document(loaded["timeline"])
        except SignalStorageValidationError:
            # Corrupted, hand-edited, or otherwise unverifiable content:
            # fail closed rather than silently replacing it with a fresh
            # empty store or generating a new proposal.
            self.operational = False
            self.startup_diagnostic_code = SIGNAL_STORE_INTEGRITY_FAILURE
            self.persistence_status = "LOAD_VALIDATION_FAILED"
        except SignalStorageError:
            self.operational = False
            self.startup_diagnostic_code = "SIGNAL_STORAGE_READ_FAILED"
            self.persistence_status = "LOAD_FAILED"

    def _require_operational(self):
        if not self.operational or self._timeline is None:
            raise SignalEngineError("signal intelligence engine is fail-closed")

    def _persist(self):
        if self._timeline is None:
            return
        document = storage_document(self._settings_document, self._timeline)
        try:
            self.store.save(document)
        except SignalStorageError:
            self.persistence_status = "WRITE_FAILED_IN_MEMORY_VALID"
            self.persistence_failure_count += 1
        else:
            self.persistence_status = "OK"

    def _append(self, category, instrument, occurred, observed, payload):
        self._require_operational()
        try:
            event = self._timeline.append(category, instrument, occurred, observed, ENGINE_BASIS, payload)
        except TimelineValidationError as error:
            raise SignalEngineError(str(error)) from error
        self._persist()
        return event

    def _event_by_id(self, event_id):
        for event in self._timeline.events:
            if event["timeline_event_id"] == event_id:
                return event
        return None

    def append_market_observation(
        self, instrument, occurred_at_utc, first_observed_at_utc, payload,
    ):
        """Register one governed market observation as evidence. Returns
        the append-only timeline event; its ``timeline_event_id`` is the
        value later evaluation requests must supply as
        ``market_data_observation_id``."""
        self._require_operational()
        try:
            clean_payload = validate_market_observation(payload, instrument)
        except PaperValidationError as error:
            raise SignalEngineError(str(error)) from error
        return self._append("MARKET_OBSERVATION", instrument, occurred_at_utc, first_observed_at_utc, clean_payload)

    def _verify_evidence(self, clean_request):
        event = self._event_by_id(clean_request["market_data_observation_id"])
        if event is None or event["event_category"] != "MARKET_OBSERVATION":
            return False, role1.REASON_MARKET_EVIDENCE_NOT_FOUND
        if event["instrument"] != clean_request["instrument"]:
            return False, role1.REASON_MARKET_EVIDENCE_NOT_FOUND
        if event["payload"] != clean_request["market_observation"]:
            return False, role1.REASON_MARKET_EVIDENCE_HASH_MISMATCH
        if event["first_observed_at_utc"] > clean_request["evaluated_at_utc"]:
            return False, role1.REASON_MARKET_EVIDENCE_FUTURE_DATED
        return True, None

    def _existing_proposal_event(self, proposal_id):
        for event in reversed(self._timeline.events):
            if event["event_category"] == "PAPER_PROPOSAL" and event["payload"]["proposal"]["proposal_id"] == proposal_id:
                return event
        return None

    def generate_proposal(self, evaluation_request_payload):
        """The only mutation path for this service. Runs the full
        six-role pipeline and returns {"proposal": ..., "role_step_results":
        ..., "model_annotation": ...}; every role outcome (pass or
        BLOCKED) is recorded as an append-only SIGNAL_PIPELINE_STEP event
        before the final PAPER_PROPOSAL event, so a BLOCKED result is
        fully auditable.

        Idempotent by content: since ``proposal_id`` is derived purely from
        governed evidence/configuration (Section 4), re-submitting the
        identical evaluation against the same timeline reproduces the
        identical proposal_id. Rather than attempting to append duplicate
        timeline events (which the append-only hash chain correctly
        rejects), this returns the already-recorded result unchanged — the
        history stays append-only with no duplicate entries, and the
        retry is provably deterministic."""
        self._require_operational()
        try:
            clean_request = sd.validate_evaluation_request(evaluation_request_payload)
        except sd.SignalValidationError as error:
            raise SignalEngineError(str(error)) from error
        evidence_ok, evidence_reason = self._verify_evidence(clean_request)
        working_request = dict(clean_request)
        working_request["_evidence_integrity_ok"] = evidence_ok
        working_request["_evidence_integrity_reason"] = evidence_reason

        result = pipeline.evaluate(working_request, self.operating_mode, adapter=self._adapter)

        existing = self._existing_proposal_event(result["proposal"]["proposal_id"])
        if existing is not None:
            return {
                "proposal": deepcopy(existing["payload"]["proposal"]),
                "role_step_results": result["role_step_results"],
                "model_annotation": deepcopy(existing["payload"]["model_annotation"]),
            }

        for role_name, role_result in result["role_step_results"]:
            self._append(
                "SIGNAL_PIPELINE_STEP",
                clean_request["instrument"],
                clean_request["evaluated_at_utc"],
                clean_request["evaluated_at_utc"],
                {"role": role_name, "result": role_result},
            )
        self._append(
            "PAPER_PROPOSAL",
            clean_request["instrument"],
            clean_request["evaluated_at_utc"],
            clean_request["evaluated_at_utc"],
            {
                "proposal": result["proposal"],
                "model_annotation": result["model_annotation"],
                "paper_only_status": PAPER_ONLY_STATUS,
            },
        )
        return result

    def status_document(self):
        return {
            "schema_version": SIGNAL_STATUS_SCHEMA,
            "enabled": True,
            "operational": self.operational,
            "operating_mode": self.operating_mode,
            "paper_only_status": PAPER_ONLY_STATUS,
            "signal_generation": self.operational,
            "broker_execution": False,
            "storage_constructed": True,
            "persistence_status": self.persistence_status,
            "persistence_failure_count": self.persistence_failure_count,
            "startup_diagnostic_code": self.startup_diagnostic_code,
            "strategy_registry": registry.list_strategies(),
            "message": (
                "Signal intelligence produces research proposals only; "
                "no broker order is ever submitted."
            ),
        }

    def proposal_history_document(self):
        if self._timeline is None:
            return DisabledSignalService(self.operating_mode).proposal_history_document()
        events = [event for event in self._timeline.events if event["event_category"] == "PAPER_PROPOSAL"]
        trimmed = events[-MAX_API_PROPOSAL_ITEMS:]
        return {
            "schema_version": SIGNAL_HISTORY_SCHEMA,
            "enabled": True,
            "proposal_count": len(events),
            "response_truncated": len(events) > len(trimmed),
            "proposals": [deepcopy(event["payload"]["proposal"]) for event in trimmed],
        }

    def strategy_registry_document(self):
        return {"schema_version": registry.REGISTRY_SCHEMA_VERSION, "strategies": registry.list_strategies()}

    def timeline_document(self):
        if self._timeline is None:
            return DisabledSignalService(self.operating_mode).timeline_document()
        source = self._timeline.to_document()
        events = source["events"][-MAX_API_TIMELINE_EVENTS:]
        return {
            "schema_version": SIGNAL_TIMELINE_API_SCHEMA,
            "timeline_schema_version": source["schema_version"],
            "enabled": True,
            "event_count": source["event_count"],
            "tail_event_hash": source["tail_event_hash"],
            "response_truncated": source["event_count"] > len(events),
            "events": deepcopy(events),
        }

    def shutdown(self):
        if self._shutdown:
            return True
        self._shutdown = True
        return self.store.shutdown()


def in_memory_service(operating_mode="RESEARCH", session_started_at_utc=None, adapter=None):
    return SignalIntelligenceService(
        store=InMemorySignalStore(),
        operating_mode=operating_mode,
        session_started_at_utc=session_started_at_utc,
        adapter=adapter,
    )


__all__ = (
    "DisabledSignalService",
    "SIGNAL_STORE_INTEGRITY_FAILURE",
    "SignalEngineError",
    "SignalIntelligenceService",
    "disabled_service",
    "in_memory_service",
)
