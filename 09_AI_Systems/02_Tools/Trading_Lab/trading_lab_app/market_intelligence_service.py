"""Authoritative TRL-R2-010 Market Intelligence V0 service (TRL CORTEX V0).

Implements TRL_R2_010_MARKET_INTELLIGENCE_V0_CONTRACT.md Sections 15, 18,
22. This is the single place research classification decisions are made;
the CLI and the read-only HTTP layer never re-derive validation, scoring,
or decision logic — they call this service and render its result.
``ModeService`` remains the sole authority for *capability*; this service
is the sole authority for Market Intelligence *record correctness*.

Never imports MetaTrader5, never constructs an adapter, never calls
``order_check``/``order_send``, never writes to the Phase 5/6 execution
journal, never calls an external API or AI model. Section 21's
"tonight-ready" acceleration decisions are documented in
``market_intelligence_data``'s module docstring.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
import stat

from . import market_intelligence_data as mid
from .market_intelligence_journal import MarketIntelligenceJournalLockTimeout
from .timeline_data import (
    decimal_value,
    format_utc,
    validate_utc_timestamp,
)


CAPABILITY = "market_intelligence_research"

MAX_INPUT_FILE_BYTES = 262144
OPPORTUNITY_DEFAULT_LIFETIME_HOURS = 24

# Service-level operational reason codes (distinct from the governed
# Section 10.4/19 decision/blocker reason codes in ``market_intelligence_data``,
# which every ``MarketIntelligenceServiceError`` raised from a data-module
# validation failure reuses directly instead).
SERVICE_REASON_CODES = (
    "MARKET_INTELLIGENCE_CAPABILITY_DENIED",
    "MARKET_INTELLIGENCE_JOURNAL_INTEGRITY_UNCERTAIN",
    "MARKET_INTELLIGENCE_INPUT_PATH_INVALID",
    "MARKET_INTELLIGENCE_INPUT_FILE_TOO_LARGE",
    "MARKET_INTELLIGENCE_INPUT_NOT_UTF8_JSON",
    "MARKET_INTELLIGENCE_INPUT_DUPLICATE_KEY",
    "MARKET_INTELLIGENCE_OPPORTUNITY_NOT_FOUND",
    "MARKET_INTELLIGENCE_VIRTUAL_OPPORTUNITY_NOT_FOUND",
    "MARKET_INTELLIGENCE_PREVIEW_NOT_AVAILABLE_FOR_STATUS",
    "MARKET_INTELLIGENCE_NO_SELECTABLE_CANDIDATE",
    "MARKET_INTELLIGENCE_NO_REFERENCE_CANDIDATE",
    "MARKET_INTELLIGENCE_EXECUTION_LOCK_UNAVAILABLE",
)


class MarketIntelligenceServiceError(RuntimeError):
    """Wraps a governed or service-level reason code for callers that want
    it without a traceback."""

    def __init__(self, reason_code, message=None):
        self.reason_code = reason_code
        super().__init__(message or reason_code)


# ---------------------------------------------------------------------
# Input-file safety (Section 15.2 / 18.2)
# ---------------------------------------------------------------------

def load_analysis_input_bytes(path):
    """Enforce every Section 15.2 input-safety rule and return the raw
    bytes. Never returns or persists the absolute path itself."""
    if not isinstance(path, str) or not path:
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_PATH_INVALID", "a single local path is required")
    if "://" in path:
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_PATH_INVALID", "a URL is not an accepted input")
    if path.startswith("\\\\") or path.startswith("//"):
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_PATH_INVALID", "a network/UNC path is not an accepted input")
    try:
        file_stat = os.lstat(path)
    except OSError as error:
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_PATH_INVALID", "input path could not be accessed") from error
    if stat.S_ISLNK(file_stat.st_mode):
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_PATH_INVALID", "a symlink/reparse point is not an accepted input")
    if not stat.S_ISREG(file_stat.st_mode):
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_PATH_INVALID", "input must be a regular file")
    if file_stat.st_size > MAX_INPUT_FILE_BYTES:
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_FILE_TOO_LARGE", "input exceeds the 262144-byte bound")
    try:
        with open(path, "rb") as handle:
            raw = handle.read(MAX_INPUT_FILE_BYTES + 1)
    except OSError as error:
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_PATH_INVALID", "input could not be read") from error
    if len(raw) > MAX_INPUT_FILE_BYTES:
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_FILE_TOO_LARGE", "input exceeds the 262144-byte bound")
    return raw


def _reject_constant(_value):
    raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_NOT_UTF8_JSON", "input contains a non-finite numeric constant")


def _unique_object_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_DUPLICATE_KEY", "input JSON contains a duplicate object key")
        result[key] = value
    return result


def parse_analysis_input_bytes(raw_bytes):
    """Strict UTF-8, duplicate-key-rejecting, non-finite-rejecting JSON
    parse of already-size-bounded bytes (Section 7.2/15.2)."""
    try:
        text = raw_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_NOT_UTF8_JSON", "input is not strict UTF-8") from error
    try:
        return json.loads(text, parse_constant=_reject_constant, object_pairs_hook=_unique_object_pairs)
    except json.JSONDecodeError as error:
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_INPUT_NOT_UTF8_JSON", "input is not strict JSON") from error


def bounded_source_label(path):
    """A bounded logical label only — never the absolute input path
    (Section 6.2/7.2/15.2)."""
    basename = os.path.basename(path)
    return ("local-file:" + basename)[:256]


# ---------------------------------------------------------------------
# Disabled (capability-denied-by-mode) service
# ---------------------------------------------------------------------

class DisabledMarketIntelligenceService:
    """The default when the current mode never grants
    ``market_intelligence_research`` at all (e.g. no mode service wired).
    Read-only status/list/inspect/journal operations remain available
    (Section 5.1); every mutation fails closed."""

    enabled = False

    def __init__(self, operating_mode="OFF"):
        self.operating_mode = operating_mode

    def status_document(self):
        return {
            "schema_version": "TRL_MARKET_INTELLIGENCE_STATUS.v1",
            "enabled": False,
            "operating_mode": self.operating_mode,
            "market_intelligence_research_granted": False,
            "research_only": True,
            "live_execution_disabled": True,
            "execution_handoff_status": mid.EXECUTION_HANDOFF_STATUS,
            "message": "Market Intelligence research is disabled in the {} operating mode.".format(self.operating_mode),
        }

    def list_opportunities_document(self, status=None):
        return {"schema_version": "TRL_MARKET_OPPORTUNITY_LIST.v1", "enabled": False, "opportunities": []}

    def inspect_opportunity_document(self, opportunity_id):
        return {"found": False, "reason_code": "MARKET_INTELLIGENCE_CAPABILITY_DENIED"}

    def list_virtual_opportunities_document(self, opportunity_id):
        return {"schema_version": "TRL_VIRTUAL_OPPORTUNITY_LIST.v1", "enabled": False, "virtual_opportunities": []}

    def inspect_virtual_opportunity_document(self, virtual_opportunity_id):
        return {"found": False, "reason_code": "MARKET_INTELLIGENCE_CAPABILITY_DENIED"}

    def journal_document(self, limit=None):
        return {"schema_version": "TRL_MARKET_INTELLIGENCE_JOURNAL_VIEW.v1", "enabled": False, "events": []}

    def telemetry_document(self):
        return {"schema_version": "TRL_LEARNING_TELEMETRY_LIST.v1", "enabled": False, "telemetry": []}

    def market_opportunities_http_document(self):
        return self.list_opportunities_document()

    def market_opportunity_http_document(self, opportunity_id):
        return self.inspect_opportunity_document(opportunity_id)

    def virtual_opportunities_http_document(self):
        return {"schema_version": "TRL_VIRTUAL_OPPORTUNITY_LIST.v1", "enabled": False, "virtual_opportunities": []}

    def _deny(self):
        raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_CAPABILITY_DENIED", "market intelligence research is disabled in this operating mode")

    def analyze_market_snapshot(self, input_path):
        self._deny()

    def preview_opportunity_basket(self, opportunity_id):
        self._deny()

    def record_opportunity_outcome(self, opportunity_id, outcome_document):
        self._deny()

    def shutdown(self):
        return True


def disabled_service(operating_mode="OFF"):
    return DisabledMarketIntelligenceService(operating_mode)


# ---------------------------------------------------------------------
# Real service
# ---------------------------------------------------------------------

class MarketIntelligenceService:
    enabled = True

    def __init__(self, mode_service=None, journal=None, clock=None):
        self._mode_service = mode_service
        from .market_intelligence_journal import in_memory_mi_journal_writer
        self._journal = journal if journal is not None else in_memory_mi_journal_writer()
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    def _now(self):
        return format_utc(self._clock())

    def _now_dt(self):
        return validate_utc_timestamp(self._now())

    def _require_capability(self):
        if self._mode_service is None or not self._mode_service.has_capability(CAPABILITY):
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_CAPABILITY_DENIED", "market_intelligence_research is not granted in the current mode")

    def _require_journal_integrity(self):
        if self._journal.startup_diagnostic_code != "OK":
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_JOURNAL_INTEGRITY_UNCERTAIN", "the market intelligence journal failed integrity validation at startup")

    # -- journal read helpers ------------------------------------------

    def _events_of_type(self, event_type):
        return [event for event in self._journal.events if event["event_type"] == event_type]

    def _latest_opportunity_record(self, opportunity_id):
        latest = None
        for event in self._journal.events:
            if event["event_type"] not in ("MI_OPPORTUNITY_CREATED", "MI_OPPORTUNITY_REUSED"):
                continue
            record = event["payload"].get("opportunity")
            if isinstance(record, dict) and record.get("opportunity_id") == opportunity_id:
                latest = record
        return deepcopy(latest) if latest is not None else None

    def _all_opportunity_ids(self):
        seen = []
        for event in self._journal.events:
            if event["event_type"] not in ("MI_OPPORTUNITY_CREATED", "MI_OPPORTUNITY_REUSED"):
                continue
            record = event["payload"].get("opportunity")
            if isinstance(record, dict):
                opportunity_id = record.get("opportunity_id")
                if opportunity_id and opportunity_id not in seen:
                    seen.append(opportunity_id)
        return seen

    def _decision_events_for(self, opportunity_id):
        return [
            event for event in self._events_of_type("MI_DECISION_RECORDED")
            if event["payload"].get("opportunity_id") == opportunity_id
        ]

    def _latest_decision_record(self, opportunity_id):
        events = self._decision_events_for(opportunity_id)
        if not events:
            return None
        return deepcopy(events[-1]["payload"]["decision"])

    def _latest_non_expired_decision_status(self, opportunity_id):
        events = self._decision_events_for(opportunity_id)
        for event in reversed(events):
            status = event["payload"]["decision"]["final_status"]
            if status != "EXPIRED":
                return status
        return None

    def _latest_lattice(self, opportunity_id):
        """Reconstruct the current virtual-opportunity state map: the
        lattice's identity/geometry fields never change, but ``state`` is a
        mutable lifecycle projection layered by later
        MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED events (Section 12.2)."""
        records = {}
        for event in self._journal.events:
            if event["event_type"] == "MI_LATTICE_CREATED" and event["payload"].get("opportunity_id") == opportunity_id:
                for record in event["payload"]["virtual_opportunities"]:
                    records[record["virtual_opportunity_id"]] = deepcopy(record)
        for event in self._journal.events:
            if event["event_type"] == "MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED" and event["payload"].get("opportunity_id") == opportunity_id:
                vid = event["payload"]["virtual_opportunity_id"]
                if vid in records:
                    records[vid]["state"] = event["payload"]["state"]
        return records

    def _find_virtual_opportunity(self, virtual_opportunity_id):
        for event in self._journal.events:
            if event["event_type"] == "MI_LATTICE_CREATED":
                for record in event["payload"]["virtual_opportunities"]:
                    if record["virtual_opportunity_id"] == virtual_opportunity_id:
                        lattice = self._latest_lattice(event["payload"]["opportunity_id"])
                        return lattice.get(virtual_opportunity_id)
        return None

    def _existing_lattice_with_candidate_inputs(self, opportunity_id):
        """Reconstruct the ``[(virtual_opportunity_record, candidate_input), ...]``
        list an already-persisted lattice produced, ordered by rank —
        used on the opportunity-reuse path so a repeated
        ``analyze_market_snapshot`` call never re-derives (and re-appends)
        an already-durable lattice."""
        lattice = self._latest_lattice(opportunity_id)
        candidate_inputs = {}
        for event in self._journal.events:
            if event["event_type"] == "MI_LATTICE_CREATED" and event["payload"].get("opportunity_id") == opportunity_id:
                candidate_inputs.update(event["payload"].get("candidate_inputs_by_vop", {}))
        ordered = sorted(lattice.values(), key=lambda record: record["rank"])
        return [(record, candidate_inputs.get(record["virtual_opportunity_id"])) for record in ordered]

    def _decision_record_by_id(self, opportunity_id, decision_id):
        for event in self._decision_events_for(opportunity_id):
            if event["payload"]["decision"]["decision_id"] == decision_id:
                return deepcopy(event["payload"]["decision"])
        return None

    def _latest_preview(self, opportunity_id):
        for event in reversed(self._events_of_type("MI_BASKET_PREVIEW_CREATED")):
            if event["payload"].get("opportunity_id") == opportunity_id:
                return deepcopy(event["payload"]["preview"]), deepcopy(event["payload"]["candidate_input"])
        return None, None

    # -- read-only documents (Section 15.1/15.3) -------------------------

    def status_document(self):
        mode = self._mode_service.current_mode if self._mode_service else "OFF"
        granted = bool(self._mode_service and self._mode_service.has_capability(CAPABILITY))
        return {
            "schema_version": "TRL_MARKET_INTELLIGENCE_STATUS.v1",
            "enabled": True,
            "operating_mode": mode,
            "market_intelligence_research_granted": granted,
            "research_only": True,
            "live_execution_disabled": True,
            "execution_handoff_status": mid.EXECUTION_HANDOFF_STATUS,
            "scoring_validation_status": "INTELLIGENCE_SCORING_NOT_VALIDATED",
            "sma001_blocked": True,
            "fib001_blocked": True,
            "journal_integrity": self._journal.startup_diagnostic_code,
            "message": "TRL CORTEX V0 research-only market intelligence. Not financial advice. No execution authority.",
        }

    def list_opportunities_document(self, status=None):
        opportunities = []
        for opportunity_id in self._all_opportunity_ids():
            record = self._latest_opportunity_record(opportunity_id)
            decision = self._latest_decision_record(opportunity_id)
            if decision is not None:
                record = dict(record)
                record["decision_status"] = decision["final_status"]
                record["decision_reason_codes"] = decision["reason_codes"]
            if status is not None and record["decision_status"] != status:
                continue
            opportunities.append(record)
        return {"schema_version": "TRL_MARKET_OPPORTUNITY_LIST.v1", "enabled": True, "opportunities": opportunities}

    def inspect_opportunity_document(self, opportunity_id):
        record = self._latest_opportunity_record(opportunity_id)
        if record is None:
            return {"found": False, "reason_code": "MARKET_INTELLIGENCE_OPPORTUNITY_NOT_FOUND"}
        decision = self._latest_decision_record(opportunity_id)
        if decision is not None:
            record = dict(record)
            record["decision_status"] = decision["final_status"]
            record["decision_reason_codes"] = decision["reason_codes"]
        preview, _candidate = self._latest_preview(opportunity_id)
        return {
            "found": True, "opportunity": record, "decision": decision,
            "virtual_opportunities": list(self._latest_lattice(opportunity_id).values()),
            "preview": preview,
        }

    def list_virtual_opportunities_document(self, opportunity_id):
        lattice = self._latest_lattice(opportunity_id)
        items = sorted(lattice.values(), key=lambda item: item["rank"])
        return {"schema_version": "TRL_VIRTUAL_OPPORTUNITY_LIST.v1", "enabled": True, "virtual_opportunities": items}

    def inspect_virtual_opportunity_document(self, virtual_opportunity_id):
        record = self._find_virtual_opportunity(virtual_opportunity_id)
        if record is None:
            return {"found": False, "reason_code": "MARKET_INTELLIGENCE_VIRTUAL_OPPORTUNITY_NOT_FOUND"}
        return {"found": True, "virtual_opportunity": record}

    def journal_document(self, limit=None):
        events = self._journal.events
        if limit is not None:
            events = events[-limit:]
        return {
            "schema_version": "TRL_MARKET_INTELLIGENCE_JOURNAL_VIEW.v1", "enabled": True,
            "event_count": len(events), "events": events,
        }

    def telemetry_document(self):
        records = [event["payload"]["telemetry"] for event in self._events_of_type("MI_TELEMETRY_RECORDED")]
        return {"schema_version": "TRL_LEARNING_TELEMETRY_LIST.v1", "enabled": True, "telemetry": records}

    def market_opportunities_http_document(self):
        return self.list_opportunities_document()

    def market_opportunity_http_document(self, opportunity_id):
        return self.inspect_opportunity_document(opportunity_id)

    def virtual_opportunities_http_document(self):
        opportunities = []
        for opportunity_id in self._all_opportunity_ids():
            opportunities.extend(self._latest_lattice(opportunity_id).values())
        return {"schema_version": "TRL_VIRTUAL_OPPORTUNITY_LIST.v1", "enabled": True, "virtual_opportunities": opportunities}

    # -- mutations (Section 15.1: capability-gated) ----------------------

    def _reject(self, reason_code, source_label, detail=None):
        payload = {"reason_code": reason_code, "source": source_label}
        if detail:
            payload["detail"] = detail[:256]
        self._journal.append("MI_RECORD_REJECTED", payload, occurred_at_utc=self._now())

    def analyze_market_snapshot(self, input_path):
        self._require_capability()
        self._require_journal_integrity()
        source_label = bounded_source_label(input_path)
        raw_bytes = load_analysis_input_bytes(input_path)
        try:
            parsed = parse_analysis_input_bytes(raw_bytes)
        except MarketIntelligenceServiceError as error:
            self._reject(error.reason_code, source_label, str(error))
            raise
        try:
            validated = mid.validate_analysis_input(parsed)
        except mid.MarketIntelligenceValidationError as error:
            self._reject(error.reason_code, source_label, str(error))
            raise MarketIntelligenceServiceError(error.reason_code, str(error))
        try:
            mid.check_instrument_and_timeframe(validated["snapshot"]["instrument"], validated["snapshot"]["timeframe"])
        except mid.MarketIntelligenceValidationError as error:
            self._reject(error.reason_code, source_label, str(error))
            raise MarketIntelligenceServiceError(error.reason_code, str(error))

        now = self._now()
        now_dt = self._now_dt()
        # Section 6.1: "observed_at_utc ... not in the future relative to
        # ingestion" — a schema-table field constraint, not a named
        # Section 10.4 decision reason code, so it reuses
        # MARKET_INTELLIGENCE_SCHEMA_VALIDATION_FAILED.
        if validate_utc_timestamp(validated["snapshot"]["observed_at_utc"]) > now_dt:
            self._reject(mid.SCHEMA_FAIL, source_label, "snapshot observed_at_utc is in the future")
            raise MarketIntelligenceServiceError(mid.SCHEMA_FAIL, "snapshot observed_at_utc is in the future")
        try:
            evidence_by_category_input = mid.check_evidence_completeness(validated["evidence_inputs"], now_dt)
        except mid.MarketIntelligenceValidationError as error:
            self._reject(error.reason_code, source_label, str(error))
            raise MarketIntelligenceServiceError(error.reason_code, str(error))

        try:
            with self._journal.acquire_creation_lock():
                # Every record below is fully deterministic given identical
                # inputs. Content-addressed re-appends are deliberately
                # skipped on the reuse path (Section 22 "opportunity
                # reuse"): two racing processes computing byte-identical
                # content at a coinciding occurred_at_utc would otherwise
                # mint the identical journal event_id twice and fail
                # closed on "duplicate journal event ID" — reloading the
                # journal (already done by acquire_creation_lock) and
                # checking for an existing opportunity BEFORE persisting
                # anything new is what makes this safe across processes.
                snapshot = mid.build_snapshot_record(validated["snapshot"])
                evidence_by_category = {
                    category: mid.build_evidence_record(
                        snapshot["snapshot_id"], snapshot["canonical_snapshot_hash"],
                        validated["proposed_side"], item,
                    )
                    for category, item in evidence_by_category_input.items()
                }
                expiry_utc = format_utc(validate_utc_timestamp(now) + timedelta(hours=OPPORTUNITY_DEFAULT_LIFETIME_HOURS))
                opportunity = mid.build_opportunity_record(
                    snapshot_record=snapshot, proposed_side=validated["proposed_side"],
                    strategy_id=validated["strategy_id"], strategy_version=validated["strategy_version"],
                    concept_input=validated["concept_input"], evidence_by_category=evidence_by_category,
                    activation_satisfied=validated["activation_satisfied"],
                    invalidation_satisfied=validated["invalidation_satisfied"],
                    created_at_utc=now, expiry_utc=expiry_utc,
                )
                existing = self._latest_opportunity_record(opportunity["opportunity_id"])

                if existing is not None:
                    opportunity = existing
                    self._journal.append("MI_OPPORTUNITY_REUSED", {"opportunity": opportunity}, occurred_at_utc=now)
                    virtual_opportunities = self._existing_lattice_with_candidate_inputs(opportunity["opportunity_id"])
                else:
                    self._journal.append("MI_SNAPSHOT_RECORDED", {"snapshot": snapshot, "source": source_label}, occurred_at_utc=now)
                    self._journal.append(
                        "MI_EVIDENCE_RECORDED",
                        {"snapshot_id": snapshot["snapshot_id"], "evidence": list(evidence_by_category.values())},
                        occurred_at_utc=now,
                    )
                    self._journal.append("MI_OPPORTUNITY_CREATED", {"opportunity": opportunity}, occurred_at_utc=now)

                    mid_price = mid.snapshot_mid_price(snapshot)
                    built_candidates = []
                    for candidate_input in validated["candidate_inputs"]:
                        built = mid.build_virtual_opportunity_record(
                            opportunity_id=opportunity["opportunity_id"],
                            canonical_opportunity_hash=opportunity["canonical_opportunity_hash"],
                            proposed_side=validated["proposed_side"], validated_candidate=candidate_input,
                            mid_price=mid_price,
                        )
                        expired = validate_utc_timestamp(built["expires_at_utc"]) <= now_dt
                        state = mid.derive_virtual_state(
                            expired=expired, invalidation_satisfied=built["invalidation_satisfied"],
                            geometry_valid=built["geometry_valid"], activation_satisfied=built["activation_satisfied"],
                        )
                        built_candidates.append((built, state, candidate_input))

                    ranks = mid.rank_virtual_opportunities([
                        {
                            "virtual_opportunity_id": built["virtual_opportunity_id"],
                            "expected_reward_risk_ratio": built["expected_reward_risk_ratio"],
                            "distance_to_market": built["distance_to_market"], "state": state,
                        }
                        for built, state, _candidate_input in built_candidates
                    ])
                    virtual_opportunities = []
                    for built, state, candidate_input in built_candidates:
                        rank = ranks[built["virtual_opportunity_id"]]
                        record = mid.finalize_virtual_opportunity_record(built, rank, state)
                        virtual_opportunities.append((record, candidate_input))

                    # ``candidate_inputs_by_vop`` preserves each candidate's
                    # originating allocations/hypothetical quantity keyed by
                    # virtual_opportunity_id, so ``preview_opportunity_basket``
                    # can copy them exactly (Section 13.1) without
                    # recomputing or redistributing.
                    self._journal.append(
                        "MI_LATTICE_CREATED",
                        {
                            "opportunity_id": opportunity["opportunity_id"],
                            "virtual_opportunities": [record for record, _candidate_input in virtual_opportunities],
                            "candidate_inputs_by_vop": {
                                record["virtual_opportunity_id"]: candidate_input
                                for record, candidate_input in virtual_opportunities
                            },
                        },
                        occurred_at_utc=now,
                    )
                    for record, candidate_input in virtual_opportunities:
                        self._journal.append(
                            "MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED",
                            {
                                "opportunity_id": opportunity["opportunity_id"],
                                "virtual_opportunity_id": record["virtual_opportunity_id"],
                                "state": record["state"],
                            },
                            occurred_at_utc=now,
                        )

                all_candidates_rejected = all(record["state"] == "REJECTED" for record, _c in virtual_opportunities) if virtual_opportunities else True
                opportunity_expired = validate_utc_timestamp(opportunity["expiry_utc"]) <= now_dt
                strategy_gate_passed, strategy_gate_reason = _strategy_gate(opportunity["strategy_id"])
                decision_parts = mid.build_decision_record(
                    opportunity=opportunity, strategy_gate_passed=strategy_gate_passed,
                    strategy_gate_reason=strategy_gate_reason, opportunity_expired=opportunity_expired,
                    all_candidates_rejected=all_candidates_rejected, evaluated_at_utc=now,
                )
                supporting_ids, opposing_ids = mid.partition_evidence_by_direction(evidence_by_category)
                decision = mid.finalize_decision_record(opportunity, decision_parts, supporting_ids, opposing_ids)
                opportunity = dict(opportunity)
                opportunity["decision_status"] = decision["final_status"]
                opportunity["decision_reason_codes"] = decision["reason_codes"]
                # Decision reuse (Section 8.5): re-evaluating an
                # opportunity whose scored inputs have not changed (same
                # decision_id) returns the existing decision record rather
                # than minting a new journal event — required for the same
                # cross-process collision-avoidance reason as above.
                existing_decision = self._decision_record_by_id(opportunity["opportunity_id"], decision["decision_id"])
                if existing_decision is not None:
                    decision = existing_decision
                else:
                    self._journal.append(
                        "MI_DECISION_RECORDED",
                        {"opportunity_id": opportunity["opportunity_id"], "decision": decision},
                        occurred_at_utc=now,
                    )
        except MarketIntelligenceJournalLockTimeout:
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_EXECUTION_LOCK_UNAVAILABLE", "the market intelligence creation lock was not available in time")

        return {
            "opportunity": opportunity, "decision": decision,
            "virtual_opportunities": [record for record, _candidate_input in virtual_opportunities],
        }

    def _candidate_input_for(self, opportunity_id, virtual_opportunity_id):
        for event in self._journal.events:
            if event["event_type"] == "MI_LATTICE_CREATED" and event["payload"].get("opportunity_id") == opportunity_id:
                index = event["payload"].get("candidate_inputs_by_vop")
                if isinstance(index, dict) and virtual_opportunity_id in index:
                    return deepcopy(index[virtual_opportunity_id])
        return None

    def preview_opportunity_basket(self, opportunity_id):
        self._require_capability()
        self._require_journal_integrity()
        try:
            with self._journal.acquire_creation_lock():
                opportunity = self._latest_opportunity_record(opportunity_id)
                if opportunity is None:
                    raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_OPPORTUNITY_NOT_FOUND")
                existing_preview, _candidate = self._latest_preview(opportunity_id)
                if existing_preview is not None:
                    return existing_preview
                decision = self._latest_decision_record(opportunity_id)
                if decision is None or decision["final_status"] != "TRADE_CANDIDATE":
                    raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_PREVIEW_NOT_AVAILABLE_FOR_STATUS")
                lattice = self._latest_lattice(opportunity_id)
                activated = [record for record in lattice.values() if record["state"] == "ACTIVATED"]
                if not activated:
                    raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_NO_SELECTABLE_CANDIDATE")
                selected = min(activated, key=lambda record: record["rank"])
                candidate_input = self._candidate_input_for(opportunity_id, selected["virtual_opportunity_id"])
                now = self._now()
                self._journal.append(
                    "MI_VIRTUAL_OPPORTUNITY_STATE_CHANGED",
                    {
                        "opportunity_id": opportunity_id,
                        "virtual_opportunity_id": selected["virtual_opportunity_id"],
                        "state": "SELECTED_FOR_PREVIEW",
                    },
                    occurred_at_utc=now,
                )
                selected = dict(selected)
                selected["state"] = "SELECTED_FOR_PREVIEW"
                preview = mid.build_preview_record(
                    opportunity=opportunity, selected_virtual_opportunity=selected,
                    candidate_input=candidate_input, created_at_utc=now,
                )
                self._journal.append(
                    "MI_BASKET_PREVIEW_CREATED",
                    {"opportunity_id": opportunity_id, "preview": preview, "candidate_input": candidate_input},
                    occurred_at_utc=now,
                )
                return preview
        except MarketIntelligenceJournalLockTimeout:
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_EXECUTION_LOCK_UNAVAILABLE")

    def record_opportunity_outcome(self, opportunity_id, outcome_document):
        self._require_capability()
        self._require_journal_integrity()
        opportunity = self._latest_opportunity_record(opportunity_id)
        if opportunity is None:
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_OPPORTUNITY_NOT_FOUND")
        decision = self._latest_decision_record(opportunity_id)
        if decision is None:
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_OPPORTUNITY_NOT_FOUND")
        original_status = decision["final_status"]
        if original_status == "EXPIRED":
            original_status = self._latest_non_expired_decision_status(opportunity_id)
        if original_status is None or original_status not in mid.TELEMETRY_ORIGINAL_STATUSES:
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_NO_REFERENCE_CANDIDATE", "no non-expired decision status exists to record telemetry against")

        lattice = self._latest_lattice(opportunity_id)
        reference_candidates = [record for record in lattice.values() if record["state"] in ("ACTIVATED", "SELECTED_FOR_PREVIEW", "WATCHING")]
        if not reference_candidates:
            raise MarketIntelligenceServiceError("MARKET_INTELLIGENCE_NO_REFERENCE_CANDIDATE")
        reference = min(reference_candidates, key=lambda record: record["rank"])

        try:
            validated_input = mid.validate_telemetry_input(outcome_document)
        except mid.MarketIntelligenceValidationError as error:
            raise MarketIntelligenceServiceError(error.reason_code, str(error))
        validated_input = dict(validated_input)
        validated_input["predicted_entry"] = reference["hypothetical_entry_trigger"]
        validated_input["predicted_stop"] = reference["stop"]
        validated_input["predicted_targets"] = reference["ordered_targets"]

        now = self._now()
        telemetry = mid.build_telemetry_record(
            opportunity=opportunity, decision_id=decision["decision_id"],
            original_decision_status=original_status, validated_input=validated_input, recorded_at_utc=now,
        )
        self._journal.append(
            "MI_TELEMETRY_RECORDED",
            {"opportunity_id": opportunity_id, "telemetry": telemetry},
            occurred_at_utc=now,
        )
        return telemetry

    def shutdown(self):
        return True


def _strategy_gate(strategy_id):
    """Independently re-checks the strategy registry (Section 10.3),
    narrowly scoped to SMA-001/FIB-001 only — imported lazily so this
    module stays free of a hard Phase 4 dependency for every other
    strategy_id, including the default CORTEX-V0-HEURISTIC. Mirrors
    ``basket_execution_service.build_basket``'s exact dual gate for
    SMA-001: the registry alone reports ``(True, None)`` for it (its
    crossing *direction* has R1-kernel parity), so execution eligibility
    additionally requires ``strategy_id`` to be a member of
    ``mt5_execution_service.EXECUTION_GEOMETRY_APPROVED_STRATEGIES``
    (currently empty — see TRL_BLOCKERS.md) — referenced dynamically, not
    imported by value, so this can never silently diverge from Phase 5's
    own enforcement state."""
    if strategy_id not in ("SMA-001", "FIB-001"):
        return True, None
    from . import signal_strategy_registry as registry
    from . import mt5_execution_service as mes
    allowed, _reason = registry.executable_status(strategy_id)
    if strategy_id == "SMA-001":
        allowed = allowed and strategy_id in mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES
        return mid.strategy_gate_status(strategy_id, allowed, True)
    return mid.strategy_gate_status(strategy_id, True, allowed)
