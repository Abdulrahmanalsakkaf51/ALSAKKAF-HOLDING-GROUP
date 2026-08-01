"""Authoritative TRL-R2-007 execution service (Phase 5: MT5_DEMO_MANUAL only).

This is the single place execution decisions are made. The CLI and the
read-only HTTP layer never re-derive authorization or preflight logic —
they call this service and render its result. ``ModeService`` remains the
sole authority for *capability*; this service is the sole authority for
*execution correctness* (proposal freshness, account/symbol/risk
preflight, idempotency, journaling).

Phase 5 deliberately implements a single-attempt-per-intent model: one
``order_check`` and one manual-confirmed ``order_send`` per execution
intent. TRL_R2_007_MT5_EXECUTION_CONTRACT.md's multi-attempt
repriced-retry machinery (Section 5.4/6) is out of scope for this
checkpoint — a materially different situation requires a new proposal
(and therefore a new intent, via a new lookup key), which is a strictly
more conservative narrowing of the full contract, not a deviation from
its safety intent. Baskets, live modes, arming tokens and automatic
reconciliation are equally out of scope (Phase 6/9/10 respectively; see
TRL_FULL_VISION_MASTER_PROGRAM.md).

Entry-zone-to-order-type mapping: the Phase 5 kickoff instructions
require failing closed rather than inventing a general entry-zone -> MT5
order-type/price mapping. The one case Phase 5 supports is the
unambiguous one: a proposal whose ``entry_zone_lower`` equals
``entry_zone_upper`` (a single exact price, not a range) is mapped to a
pending ``BUY_LIMIT``/``SELL_LIMIT`` order at that exact price — nothing
is "converted" because the entry was already a single price. A genuine
range, or a price the market has already crossed through, fails closed
with a distinct reason code recording the missing approval rather than
guessing a broader rule.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import os
import secrets

from . import mt5_execution_adapter as adapter_module
from . import mt5_execution_data as med
from . import signal_data as sd
from . import signal_strategy_registry as registry
from . import signal_role3_strategy as role3
from .mt5_execution_journal import (
    ExecutionJournalLockTimeout,
    ExecutionJournalWriter,
    in_memory_journal_writer,
)
from .timeline_data import (
    canonical_decimal,
    decimal_value,
    deterministic_json_text,
    format_utc,
    sha256_text,
    validate_utc_timestamp,
)


EXECUTION_STATUS_SCHEMA = "TRL_MT5_EXECUTION_STATUS.v1"

# No strategy has received Founder-approved MT5 execution geometry in this
# checkpoint. SMA-001's crossing detection already fails closed inside
# Role 3 (signal_role3_strategy.REASON_STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED)
# before an executable proposal can ever exist, but a hand-built,
# schema-valid proposal object could still claim strategy_id="SMA-001"
# with side=BUY/SELL without going through the pipeline — this adapter-level
# allowlist is the defense-in-depth gate that blocks that path too. See
# TRL_BLOCKERS.md; do not add an entry here without a dated
# TRL_DECISION_LOG.md Founder approval.
EXECUTION_GEOMETRY_APPROVED_STRATEGIES = frozenset()

# Phase 5 supports exactly one broker-native instrument, matching the
# existing R2-003 read-only default (mt5_service.MT5ReadOnlyConfiguration's
# default symbol). Expanding this allowlist is a Founder decision, not a
# code change made silently by this module.
MT5_INSTRUMENT_ALLOWLIST = frozenset({"XAUUSD"})

DEFAULT_MAX_DEVIATION_POINTS = 20
CHECK_FRESHNESS_SECONDS = 120
CONFIRMATION_LIFETIME_SECONDS = 300
TICK_STALENESS_SECONDS = 30
SYMBOL_METADATA_STALENESS_SECONDS = 120


class AccountFingerprintConfiguration:
    """The Founder-supplied allowlisted demo-account fingerprint. Unset by
    default: 'no approved MT5 demo fingerprint configured' is an explicit,
    reportable external blocker, never silently bypassed."""

    __slots__ = ("configured", "login", "company", "server", "expected_terminal_path")

    def __init__(self, login=None, company=None, server=None, expected_terminal_path=None):
        self.configured = login is not None and company is not None and server is not None
        self.login = login
        self.company = company
        self.server = server
        self.expected_terminal_path = expected_terminal_path

    def fingerprint_hash(self):
        if not self.configured:
            return None
        return med.account_fingerprint_hash(self.login, self.company, self.server)


def unconfigured_account_fingerprint():
    return AccountFingerprintConfiguration()


def account_fingerprint_from_environment(environ=None):
    """Read the optional Founder-approved demo fingerprint from local
    environment variables only — never from a committed file, never from
    an HTTP request. All four of TRL_MT5_DEMO_LOGIN / _COMPANY / _SERVER /
    (optionally) TRL_MT5_TERMINAL_PATH must be present and non-empty;
    partial configuration is treated as unconfigured (fail closed), never
    as a partially-trusted fingerprint."""
    source = environ if environ is not None else os.environ
    login_text = source.get("TRL_MT5_DEMO_LOGIN")
    company = source.get("TRL_MT5_DEMO_COMPANY")
    server = source.get("TRL_MT5_DEMO_SERVER")
    terminal_path = source.get("TRL_MT5_TERMINAL_PATH") or None
    if not login_text or not company or not server:
        return unconfigured_account_fingerprint()
    try:
        login = int(login_text)
    except ValueError:
        return unconfigured_account_fingerprint()
    if login <= 0:
        return unconfigured_account_fingerprint()
    return AccountFingerprintConfiguration(
        login=login, company=company, server=server, expected_terminal_path=terminal_path,
    )


def _redact_login(login):
    if login is None:
        return None
    text = str(login)
    if len(text) <= 2:
        return "*" * len(text)
    return "*" * (len(text) - 2) + text[-2:]


class ExecutionServiceError(RuntimeError):
    """Wraps an ExecutionValidationError with the current partial state,
    for callers that want the reason_code without a full traceback."""

    def __init__(self, reason_code, message=None):
        self.reason_code = reason_code
        super().__init__(message or reason_code)


class DisabledExecutionService:
    """The default. No adapter is constructed; every mutation is denied."""

    enabled = False

    def __init__(self, operating_mode="OFF"):
        self.operating_mode = operating_mode

    def status_document(self):
        return {
            "schema_version": EXECUTION_STATUS_SCHEMA,
            "enabled": False,
            "operating_mode": self.operating_mode,
            "adapter_tier": "DISABLED",
            "capabilities": {
                "mt5_read_only_access": False,
                "mt5_order_check": False,
                "mt5_order_send": False,
                "manual_broker_execution": False,
            },
            "demo_only": True,
            "live_execution_disabled": True,
            "sma001_blocked": True,
            "fib001_blocked": True,
            "message": "MT5 execution is disabled in the {} operating mode.".format(self.operating_mode),
        }

    def capabilities_document(self):
        return {
            "mt5_read_only_access": False, "mt5_order_check": False,
            "mt5_order_send": False, "manual_broker_execution": False,
        }

    def journal_document(self, limit=None):
        return {"schema_version": "TRL_MT5_EXECUTION_JOURNAL_VIEW.v1", "enabled": False, "events": []}

    def dependency_status_document(self):
        return {"available": False, "reason_code": "ADAPTER_DISABLED"}

    def terminal_status_document(self):
        return {"connected": False, "trade_allowed": False, "path": None, "build": None, "reason_code": "ADAPTER_DISABLED"}

    def account_status_document(self):
        return {"available": False, "reason_code": "ADAPTER_DISABLED"}

    def symbol_status_document(self, symbol):
        return {"available": False, "symbol": symbol, "reason_code": "ADAPTER_DISABLED"}

    def _deny(self):
        raise ExecutionServiceError("ADAPTER_DISABLED", "MT5 execution is disabled in this operating mode")

    def inspect_proposal(self, proposal):
        # Pure schema/hash validation, no adapter or capability involved —
        # available regardless of operating mode, mirroring how
        # ExecutionService.inspect_proposal never touches the adapter.
        try:
            clean = sd.validate_signal_proposal(proposal)
        except sd.SignalValidationError as error:
            reason = "PROPOSAL_HASH_MISMATCH" if "does not match canonical content" in str(error) else "PROPOSAL_SCHEMA_INVALID"
            return {"valid": False, "reason_code": reason, "detail": str(error)}
        return {"valid": True, "proposal": clean}

    def build_order_intent(self, proposal):
        self._deny()

    def order_check(self, order_intent_id):
        self._deny()

    def request_confirmation(self, order_intent_id):
        self._deny()

    def confirm_and_send(self, order_intent_id, confirmation_code, actor_channel="LOCAL_OPERATOR"):
        self._deny()

    def execution_result_document(self, order_intent_id):
        return {"found": False, "reason_code": "ADAPTER_DISABLED"}

    def shutdown(self):
        return True


def disabled_service(operating_mode="OFF"):
    return DisabledExecutionService(operating_mode)


class ExecutionService:
    """The real Phase 5 execution service, bound to one adapter tier."""

    enabled = True

    def __init__(
        self,
        adapter=None,
        mode_service=None,
        journal=None,
        account_fingerprint=None,
        expected_risk_policy_hash=None,
        clock=None,
    ):
        self._adapter = adapter if adapter is not None else adapter_module.disabled_adapter()
        self._mode_service = mode_service
        self._journal = journal if journal is not None else in_memory_journal_writer()
        self.account_fingerprint = account_fingerprint or unconfigured_account_fingerprint()
        self.expected_risk_policy_hash = expected_risk_policy_hash
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # -- internals --------------------------------------------------

    def _now(self):
        return format_utc(self._clock())

    def _now_dt(self):
        return validate_utc_timestamp(self._now())

    def _require_capability(self, capability):
        if self._mode_service is None:
            raise ExecutionServiceError("CAPABILITY_DENIED", "no mode service is wired")
        if not self._mode_service.has_capability(capability):
            raise ExecutionServiceError("CAPABILITY_DENIED", "capability {} is not granted".format(capability))
        if self._mode_service.current_mode != med.PHASE5_OPERATING_MODE:
            raise ExecutionServiceError(
                "OPERATING_MODE_NOT_MT5_DEMO_MANUAL",
                "current mode {} does not authorize MT5 execution".format(self._mode_service.current_mode),
            )

    def _require_journal_integrity(self):
        if self._journal.startup_diagnostic_code != "OK":
            raise ExecutionServiceError(
                "LOOKUP_STORE_INTEGRITY_UNCERTAIN",
                "the execution journal failed integrity validation at startup",
            )

    def _journal_append(self, event_type, payload):
        return self._journal.append(event_type, payload, occurred_at_utc=self._now())

    def _all_intent_events(self, order_intent_id):
        return [
            event for event in self._journal.events
            if isinstance(event.get("payload"), dict)
            and isinstance(event["payload"].get("intent"), dict)
            and event["payload"]["intent"].get("order_intent_id") == order_intent_id
        ]

    def _load_intent(self, order_intent_id):
        events = self._all_intent_events(order_intent_id)
        if not events:
            return None
        return deepcopy(events[-1]["payload"]["intent"])

    def _find_intent_by_lookup_key(self, lookup_key):
        for event in self._journal.events:
            if event["event_type"] != "ORDER_INTENT_CREATED":
                continue
            if event["payload"].get("lookup_key") == lookup_key:
                return self._load_intent(event["payload"]["intent"]["order_intent_id"])
        return None

    def _last_check_result_event(self, order_intent_id):
        for event in reversed(self._all_intent_events(order_intent_id)):
            if event["event_type"] == "ORDER_CHECK_RESULT":
                return event
        return None

    def _has_send_attempt(self, order_intent_id):
        return any(
            event["event_type"] in ("ORDER_SEND_REQUESTED", "ORDER_SEND_RESULT")
            for event in self._all_intent_events(order_intent_id)
        )

    def _persist_intent(self, intent, event_type, extra_payload=None):
        payload = {"intent": intent}
        if extra_payload:
            payload.update(extra_payload)
        return self._journal_append(event_type, payload)

    # -- read-only status --------------------------------------------

    def capabilities_document(self):
        if self._mode_service is None:
            return {
                "mt5_read_only_access": False, "mt5_order_check": False,
                "mt5_order_send": False, "manual_broker_execution": False,
            }
        return {
            capability: self._mode_service.has_capability(capability)
            for capability in ("mt5_read_only_access", "mt5_order_check", "mt5_order_send", "manual_broker_execution")
        }

    def dependency_status_document(self):
        return self._adapter.dependency_status()

    def terminal_status_document(self):
        status = self._adapter.terminal_status()
        if self.account_fingerprint.expected_terminal_path and status.get("path"):
            status = dict(status)
            status["path_matches_expected"] = status["path"] == self.account_fingerprint.expected_terminal_path
        return status

    def account_status_document(self):
        status = dict(self._adapter.account_status())
        status["login_redacted"] = _redact_login(status.get("login"))
        status.pop("login", None)
        status["fingerprint_configured"] = self.account_fingerprint.configured
        return status

    def symbol_status_document(self, symbol):
        return self._adapter.symbol_status(symbol)

    def journal_document(self, limit=None):
        events = self._journal.events
        if limit is not None:
            events = events[-limit:]
        return {
            "schema_version": "TRL_MT5_EXECUTION_JOURNAL_VIEW.v1",
            "enabled": True,
            "startup_diagnostic_code": self._journal.startup_diagnostic_code,
            "persistence_status": self._journal.persistence_status,
            "event_count": len(self._journal.events),
            "events": events,
        }

    def status_document(self):
        mode = self._mode_service.current_mode if self._mode_service else "OFF"
        return {
            "schema_version": EXECUTION_STATUS_SCHEMA,
            "enabled": True,
            "operating_mode": mode,
            "adapter_tier": self._adapter.tier,
            "capabilities": self.capabilities_document(),
            "dependency": self.dependency_status_document(),
            "account_fingerprint_configured": self.account_fingerprint.configured,
            "journal_startup_diagnostic_code": self._journal.startup_diagnostic_code,
            "demo_only": True,
            "live_execution_disabled": True,
            "manual_confirmation_required": True,
            "sma001_blocked": "SMA-001" not in EXECUTION_GEOMETRY_APPROVED_STRATEGIES,
            "fib001_blocked": True,
            "message": (
                "Phase 5 demo-manual execution only. Live execution is unavailable. "
                "Every order_send requires explicit local manual confirmation."
            ),
        }

    def execution_result_document(self, order_intent_id):
        intent = self._load_intent(order_intent_id)
        if intent is None:
            return {"found": False, "reason_code": "INTENT_NOT_FOUND"}
        return {"found": True, "intent": intent}

    # -- proposal inspection / intent construction -----------------------

    def inspect_proposal(self, proposal):
        try:
            clean = sd.validate_signal_proposal(proposal)
        except sd.SignalValidationError as error:
            reason = "PROPOSAL_HASH_MISMATCH" if "does not match canonical content" in str(error) else "PROPOSAL_SCHEMA_INVALID"
            return {"valid": False, "reason_code": reason, "detail": str(error)}
        return {"valid": True, "proposal": clean}

    def _reject_proposal(self, proposal_id, reason_code, detail=None):
        self._journal_append("PROPOSAL_REJECTED", {
            "proposal_id": proposal_id or "",
            "reason_code": reason_code,
            "detail": (detail or "")[:200],
        })
        raise ExecutionServiceError(reason_code, detail or reason_code)

    def build_order_intent(self, proposal):
        """Independently revalidate a proposal and construct (or reuse,
        via the lookup-before-create flow) its governed order intent. No
        adapter call is made here — see order_check for the first broker
        interaction."""
        self._require_capability("manual_broker_execution")
        self._require_journal_integrity()

        raw_proposal_id = proposal.get("proposal_id") if isinstance(proposal, dict) else None
        try:
            clean = sd.validate_signal_proposal(proposal)
        except sd.SignalValidationError as error:
            reason = "PROPOSAL_HASH_MISMATCH" if "does not match canonical content" in str(error) else "PROPOSAL_SCHEMA_INVALID"
            self._reject_proposal(raw_proposal_id, reason, str(error))

        if clean["side"] == "BLOCKED":
            self._reject_proposal(clean["proposal_id"], "PROPOSAL_BLOCKED", "proposal side is BLOCKED")
        if clean["side"] == "HOLD":
            self._reject_proposal(clean["proposal_id"], "PROPOSAL_HOLD", "proposal side is HOLD")
        if clean["side"] == "WAIT":
            self._reject_proposal(clean["proposal_id"], "PROPOSAL_WAIT", "proposal side is WAIT")
        if clean["side"] not in med.SIDES:
            self._reject_proposal(clean["proposal_id"], "PROPOSAL_NOT_EXECUTABLE_SIDE")

        if self._now_dt() >= validate_utc_timestamp(clean["expires_at_utc"]):
            self._reject_proposal(clean["proposal_id"], "PROPOSAL_EXPIRED")

        strategy_id = clean["strategy_id"]
        # Checked id-only first (registration/approval state), then the
        # proposal's declared version is independently compared against
        # the registry's current version as its own distinct gate — calling
        # executable_status with the proposal's (possibly wrong) version
        # directly would fold a version mismatch into STRATEGY_NOT_REGISTERED
        # and never surface the more precise STRATEGY_VERSION_MISMATCH code.
        allowed, reason = registry.executable_status(strategy_id)
        if not allowed:
            self._reject_proposal(clean["proposal_id"], reason)
        record = registry.get_strategy(strategy_id)
        if record["strategy_version"] != clean["strategy_version"]:
            self._reject_proposal(clean["proposal_id"], "STRATEGY_VERSION_MISMATCH")
        if strategy_id not in EXECUTION_GEOMETRY_APPROVED_STRATEGIES:
            self._reject_proposal(
                clean["proposal_id"], "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED",
                role3.REASON_STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED,
            )

        if self.expected_risk_policy_hash is not None and clean["active_risk_policy_hash"] != self.expected_risk_policy_hash:
            self._reject_proposal(clean["proposal_id"], "RISK_POLICY_HASH_MISMATCH")

        if decimal_value(clean["candidate_quantity"]) != decimal_value(clean["independent_quantity"]):
            self._reject_proposal(clean["proposal_id"], "ROLE_QUANTITY_MISMATCH")

        broker_symbol = clean["broker_native_instrument"] or clean["instrument"]
        if broker_symbol not in MT5_INSTRUMENT_ALLOWLIST:
            self._reject_proposal(clean["proposal_id"], "INSTRUMENT_NOT_ALLOWLISTED")

        lower = decimal_value(clean["entry_zone_lower"])
        upper = decimal_value(clean["entry_zone_upper"])
        if lower != upper:
            self._reject_proposal(clean["proposal_id"], "ENTRY_ZONE_RANGE_MAPPING_NOT_APPROVED")
        entry_price = canonical_decimal(lower)
        order_type = "BUY_LIMIT" if clean["side"] == "BUY" else "SELL_LIMIT"

        if not self.account_fingerprint.configured:
            self._reject_proposal(
                clean["proposal_id"], "ACCOUNT_UNAVAILABLE",
                "no approved MT5 demo account fingerprint has been configured; see TRL_BLOCKERS.md",
            )
        account_hash = self.account_fingerprint.fingerprint_hash()

        quantity = canonical_decimal(decimal_value(clean["candidate_quantity"]))

        lookup_fields = {
            "proposal_id": clean["proposal_id"],
            "account_fingerprint_hash": account_hash,
            "broker_native_instrument": broker_symbol,
            "side": clean["side"],
            "quantity": quantity,
            "strategy_id": strategy_id,
            "strategy_version": clean["strategy_version"],
            "risk_policy_hash": clean["active_risk_policy_hash"],
            "operating_mode": med.PHASE5_OPERATING_MODE,
            "authorization_identity": "LOCAL_OPERATOR",
        }
        lookup_key = med.execution_intent_lookup_key(lookup_fields)

        # Sections 5.2 (lookup-before-create) and 11 of the contract require
        # that a genuinely repeated submission always resolve to the same
        # intent — never a second one. That guarantee only holds if the
        # "search, then decide, then persist" sequence is atomic across
        # every concurrent caller sharing this durable store, not just
        # within one process: the CLI-driven workflow means concurrent
        # callers are frequently separate OS processes, which a plain
        # in-process lock cannot serialize. acquire_creation_lock() is a
        # cross-process lock that also reloads the journal from disk on
        # acquisition, so the search below always sees the latest state any
        # other process may have persisted while this caller was waiting.
        try:
            with self._journal.acquire_creation_lock():
                existing = self._find_intent_by_lookup_key(lookup_key)
                if existing is not None:
                    self._journal_append("ORDER_INTENT_REUSED", {"intent": existing, "lookup_key": lookup_key})
                    return existing

                nonce = secrets.token_hex(16)
                order_intent_id = med.order_intent_id_for(lookup_fields, nonce)
                now = self._now()
                # Only the immutable identity fields feed the hash — matching
                # mt5_execution_data._identity_fields, which excludes
                # execution_status/rejection_reasons/the hash field itself, so
                # the hash stays valid across the intent's whole lifecycle
                # even as its execution_status changes (CREATED ->
                # CHECK_PASSED -> ... ).
                identity_fields = {
                    "schema_version": med.ORDER_INTENT_SCHEMA,
                    "order_intent_id": order_intent_id,
                    "proposal_id": clean["proposal_id"],
                    "canonical_proposal_hash": clean["canonical_proposal_hash"],
                    "created_at_utc": now,
                    "expires_at_utc": clean["expires_at_utc"],
                    "operating_mode": med.PHASE5_OPERATING_MODE,
                    "account_fingerprint_hash": account_hash,
                    "broker_native_instrument": broker_symbol,
                    "side": clean["side"],
                    "order_type": order_type,
                    "quantity": quantity,
                    "entry_price": entry_price,
                    "stop_loss": clean["stop_loss"],
                    "targets": clean["targets"],
                    "target_allocations_percent": clean["target_allocations_percent"],
                    "maximum_spread": clean["maximum_spread"],
                    "maximum_deviation_points": DEFAULT_MAX_DEVIATION_POINTS,
                    "time_in_force": "GTC",
                    "fill_policy": "FOK",
                    "strategy_id": strategy_id,
                    "strategy_version": clean["strategy_version"],
                    "risk_policy_hash": clean["active_risk_policy_hash"],
                    "idempotency_key": order_intent_id,
                    "manual_confirmation_required": True,
                }
                intent_hash = med.order_intent_hash_for(identity_fields)
                intent = dict(identity_fields)
                intent["execution_status"] = "CREATED"
                intent["rejection_reasons"] = []
                intent["canonical_order_intent_hash"] = intent_hash
                intent = med.validate_order_intent(intent)

                self._journal_append("ORDER_INTENT_CREATED", {"intent": intent, "lookup_key": lookup_key})
                return intent
        except ExecutionJournalLockTimeout:
            raise ExecutionServiceError(
                "EXECUTION_LOCK_UNAVAILABLE",
                "the execution journal creation lock was not available in time",
            )

    # -- order_check --------------------------------------------------

    def _fail_check(self, intent, reason_code, comment=None):
        intent = dict(intent)
        intent["execution_status"] = "REJECTED"
        intent["rejection_reasons"] = [reason_code]
        self._persist_intent(intent, "ORDER_CHECK_RESULT", {
            "outcome": "FAILED", "reason_code": reason_code, "comment": (comment or reason_code)[:200],
        })
        raise ExecutionServiceError(reason_code, comment or reason_code)

    def order_check(self, order_intent_id):
        self._require_capability("mt5_order_check")
        self._require_journal_integrity()

        intent = self._load_intent(order_intent_id)
        if intent is None:
            raise ExecutionServiceError("INTENT_NOT_FOUND")
        if intent["execution_status"] in med.TERMINAL_INTENT_STATES:
            raise ExecutionServiceError("INTENT_ALREADY_TERMINAL")
        if self._now_dt() >= validate_utc_timestamp(intent["expires_at_utc"]):
            expired = dict(intent)
            expired["execution_status"] = "CANCELLED"
            expired["rejection_reasons"] = ["INTENT_EXPIRED"]
            self._persist_intent(expired, "EXPIRY_BLOCKED", {"reason_code": "INTENT_EXPIRED"})
            raise ExecutionServiceError("INTENT_EXPIRED")

        med.validate_order_intent(intent)

        dependency = self._adapter.dependency_status()
        if not dependency.get("available"):
            self._fail_check(intent, "MT5_DEPENDENCY_MISSING")

        terminal = self._adapter.terminal_status()
        if not terminal.get("connected"):
            self._fail_check(intent, "TERMINAL_UNAVAILABLE", terminal.get("reason_code"))
        if not terminal.get("trade_allowed"):
            self._fail_check(intent, "TERMINAL_TRADE_NOT_ALLOWED")
        expected_path = self.account_fingerprint.expected_terminal_path
        if expected_path and terminal.get("path") and terminal["path"] != expected_path:
            self._fail_check(intent, "TERMINAL_PATH_MISMATCH")

        account = self._adapter.account_status()
        if not account.get("available"):
            self._fail_check(intent, "ACCOUNT_UNAVAILABLE")
        if not self.account_fingerprint.configured:
            self._fail_check(intent, "ACCOUNT_UNAVAILABLE", "no approved fingerprint configured")
        live_hash = med.account_fingerprint_hash(account["login"], account["company"], account["server"])
        if live_hash != intent["account_fingerprint_hash"]:
            self._fail_check(intent, "ACCOUNT_FINGERPRINT_MISMATCH")
        if account.get("trade_mode") != adapter_module.ACCOUNT_TRADE_MODE_DEMO:
            self._fail_check(intent, "ACCOUNT_MODE_MISMATCH")
        if not account.get("trade_allowed") or not account.get("trade_expert"):
            self._fail_check(intent, "ACCOUNT_TRADE_NOT_ALLOWED")

        symbol = self._adapter.symbol_status(intent["broker_native_instrument"])
        if not symbol.get("available"):
            self._fail_check(intent, "SYMBOL_UNAVAILABLE", symbol.get("reason_code"))
        if symbol.get("symbol") != intent["broker_native_instrument"]:
            self._fail_check(intent, "SYMBOL_MAPPING_MISMATCH")
        if not symbol.get("visible") or not symbol.get("tradeable"):
            self._fail_check(intent, symbol.get("reason_code") or "SYMBOL_NOT_TRADEABLE")

        tick_time = symbol.get("tick_time_utc")
        if not tick_time:
            self._fail_check(intent, "TICK_UNAVAILABLE")
        tick_age = (self._now_dt() - validate_utc_timestamp(tick_time)).total_seconds()
        if tick_age > TICK_STALENESS_SECONDS:
            self._fail_check(intent, "TICK_STALE")

        bid = symbol.get("bid")
        ask = symbol.get("ask")
        if bid is None or ask is None:
            self._fail_check(intent, "TICK_UNAVAILABLE")
        bid_value, ask_value = decimal_value(bid), decimal_value(ask)
        if bid_value <= 0 or ask_value <= 0 or ask_value <= bid_value:
            self._fail_check(intent, "INVALID_BID_ASK")

        point = decimal_value(symbol["point"])
        spread_points = (ask_value - bid_value) / point if point > 0 else None
        max_spread = decimal_value(intent["maximum_spread"])
        if spread_points is None or spread_points > max_spread:
            self._fail_check(intent, "SPREAD_EXCEEDS_LIMIT")

        entry_price = decimal_value(intent["entry_price"])
        if intent["side"] == "BUY" and entry_price >= ask_value:
            self._fail_check(intent, "ENTRY_PRICE_ALREADY_CROSSED_MAPPING_NOT_APPROVED")
        if intent["side"] == "SELL" and entry_price <= bid_value:
            self._fail_check(intent, "ENTRY_PRICE_ALREADY_CROSSED_MAPPING_NOT_APPROVED")

        quantity = decimal_value(intent["quantity"])
        volume_min = decimal_value(symbol["volume_minimum"])
        volume_max = decimal_value(symbol["volume_maximum"])
        volume_step = decimal_value(symbol["volume_step"])
        if quantity < volume_min or quantity > volume_max:
            self._fail_check(intent, "INVALID_QUANTITY")
        steps = (quantity - volume_min) / volume_step if volume_step > 0 else Decimal("0")
        if steps != steps.to_integral_value():
            self._fail_check(intent, "QUANTITY_STEP_MISMATCH")

        stop_loss = decimal_value(intent["stop_loss"])
        stop_distance = abs(entry_price - stop_loss) / point if point > 0 else Decimal("0")
        stops_level = Decimal(symbol.get("stops_level") or 0)
        freeze_level = Decimal(symbol.get("freeze_level") or 0)
        if stop_distance <= 0:
            self._fail_check(intent, "INVALID_STOP")
        if stops_level > 0 and stop_distance < stops_level:
            self._fail_check(intent, "STOP_LEVEL_VIOLATION")
        if freeze_level > 0 and stop_distance < freeze_level:
            self._fail_check(intent, "FREEZE_LEVEL_VIOLATION")

        filling_modes = symbol.get("filling_modes") or ()
        if intent["fill_policy"] not in filling_modes:
            self._fail_check(intent, "FILLING_MODE_UNAVAILABLE")

        request = _order_check_request(intent)
        self._persist_intent(intent, "ORDER_CHECK_REQUESTED", {"request_hash": _request_hash(request)})
        result = self._adapter.order_check(request)
        if not isinstance(result, dict) or result.get("outcome") not in med.CHECK_OUTCOMES:
            self._fail_check(intent, "BROKER_RESPONSE_MALFORMED")
        if result["outcome"] != "PASSED":
            self._fail_check(intent, "ORDER_CHECK_FAILED", result.get("comment"))

        updated = dict(intent)
        updated["execution_status"] = "CHECK_PASSED"
        self._persist_intent(updated, "ORDER_CHECK_RESULT", {"outcome": "PASSED", "checked_at_utc": self._now()})
        return {"intent": updated, "check_result": result}

    # -- manual confirmation --------------------------------------------

    def request_confirmation(self, order_intent_id):
        """The challenge code is a pure deterministic hash of the intent's
        own ID and content hash (``mt5_execution_data.confirmation_challenge_code``)
        — it is never stored as a secret anywhere, so it can be safely
        recomputed by ``confirm_and_send`` in a *separate* CLI process
        invocation without any in-memory state surviving between them.
        What IS durably persisted here (in the journal, so it survives a
        restart) is the confirmation *window* — when it was issued and
        when it expires — and the intent's AWAITING_CONFIRMATION state."""
        self._require_capability("manual_broker_execution")
        intent = self._load_intent(order_intent_id)
        if intent is None:
            raise ExecutionServiceError("INTENT_NOT_FOUND")
        if intent["execution_status"] == "CREATED":
            raise ExecutionServiceError("ORDER_CHECK_NOT_YET_PERFORMED")
        if intent["execution_status"] in med.TERMINAL_INTENT_STATES:
            raise ExecutionServiceError("INTENT_ALREADY_TERMINAL")

        check_event = self._last_check_result_event(order_intent_id)
        if check_event is None or check_event["payload"].get("outcome") != "PASSED":
            raise ExecutionServiceError("ORDER_CHECK_NOT_YET_PERFORMED")
        checked_at = validate_utc_timestamp(check_event["occurred_at_utc"])
        if (self._now_dt() - checked_at).total_seconds() > CHECK_FRESHNESS_SECONDS:
            raise ExecutionServiceError("ORDER_CHECK_STALE")

        challenge_code = med.confirmation_challenge_code(order_intent_id, intent["canonical_order_intent_hash"])
        issued_at = self._now()
        expires_at = format_utc(self._clock() + timedelta(seconds=CONFIRMATION_LIFETIME_SECONDS))
        updated = dict(intent)
        updated["execution_status"] = "AWAITING_CONFIRMATION"
        self._persist_intent(updated, "MANUAL_CONFIRMATION_REQUESTED", {
            "intent_hash_fragment": intent["canonical_order_intent_hash"][:12],
            "issued_at_utc": issued_at,
            "expires_at_utc": expires_at,
        })
        return {
            "order_intent_id": order_intent_id,
            "challenge_code": challenge_code,
            "expires_at_utc": expires_at,
        }

    def _last_confirmation_requested_event(self, order_intent_id):
        for event in reversed(self._all_intent_events(order_intent_id)):
            if event["event_type"] == "MANUAL_CONFIRMATION_REQUESTED":
                return event
        return None

    def _confirmation_already_accepted(self, order_intent_id):
        return any(
            event["event_type"] == "MANUAL_CONFIRMATION_ACCEPTED"
            for event in self._all_intent_events(order_intent_id)
        )

    # -- manual order_send --------------------------------------------

    def confirm_and_send(self, order_intent_id, confirmation_code, actor_channel="LOCAL_OPERATOR"):
        if actor_channel != "LOCAL_OPERATOR":
            raise ExecutionServiceError("CONFIRMATION_CHANNEL_NOT_LOCAL")
        self._require_capability("mt5_order_send")
        self._require_journal_integrity()

        # Sections 5.2/11 of the contract require order_send to be called
        # at most once per intent; the entire decision sequence below (has
        # this confirmation already been consumed, has a send already been
        # attempted, mark both as done) must be atomic across every
        # concurrent caller sharing this durable store — not just within
        # one process — for exactly the same reason build_order_intent's
        # lookup-before-create section needs the cross-process lock (see
        # its comment). The lock is released again right after
        # ORDER_SEND_REQUESTED is durably persisted, before the adapter is
        # ever called, so the (potentially slow, real-world) broker call
        # itself never happens while holding it.
        try:
            with self._journal.acquire_creation_lock():
                intent = self._load_intent(order_intent_id)
                if intent is None:
                    raise ExecutionServiceError("INTENT_NOT_FOUND")
                if intent["execution_status"] in med.TERMINAL_INTENT_STATES:
                    if self._confirmation_already_accepted(order_intent_id):
                        raise ExecutionServiceError("CONFIRMATION_ALREADY_CONSUMED")
                    raise ExecutionServiceError("INTENT_ALREADY_TERMINAL")
                if intent["execution_status"] != "AWAITING_CONFIRMATION":
                    raise ExecutionServiceError("CONFIRMATION_REQUIRED")

                request_event = self._last_confirmation_requested_event(order_intent_id)
                if request_event is None:
                    raise ExecutionServiceError("CONFIRMATION_REQUIRED")
                if self._confirmation_already_accepted(order_intent_id):
                    raise ExecutionServiceError("CONFIRMATION_ALREADY_CONSUMED")
                if self._now_dt() >= validate_utc_timestamp(request_event["payload"]["expires_at_utc"]):
                    raise ExecutionServiceError("CONFIRMATION_EXPIRED")

                expected_code = med.confirmation_challenge_code(order_intent_id, intent["canonical_order_intent_hash"])
                if confirmation_code != expected_code:
                    other_intent_match = any(
                        event["event_type"] == "ORDER_INTENT_CREATED"
                        and event["payload"]["intent"]["order_intent_id"] != order_intent_id
                        and med.confirmation_challenge_code(
                            event["payload"]["intent"]["order_intent_id"],
                            event["payload"]["intent"]["canonical_order_intent_hash"],
                        ) == confirmation_code
                        for event in self._journal.events
                    )
                    reason = "CONFIRMATION_WRONG_INTENT" if other_intent_match else "CONFIRMATION_MISMATCH"
                    self._persist_intent(intent, "MANUAL_CONFIRMATION_REJECTED", {"reason_code": reason})
                    raise ExecutionServiceError(reason)

                if self._has_send_attempt(order_intent_id):
                    raise ExecutionServiceError("DUPLICATE_SEND_BLOCKED")
                if self._now_dt() >= validate_utc_timestamp(intent["expires_at_utc"]):
                    raise ExecutionServiceError("PROPOSAL_EXPIRED")

                account = self._adapter.account_status()
                if not account.get("available"):
                    raise ExecutionServiceError("ACCOUNT_UNAVAILABLE")
                live_hash = med.account_fingerprint_hash(account["login"], account["company"], account["server"])
                if live_hash != intent["account_fingerprint_hash"]:
                    raise ExecutionServiceError("ACCOUNT_FINGERPRINT_MISMATCH")

                symbol = self._adapter.symbol_status(intent["broker_native_instrument"])
                if not symbol.get("available") or not symbol.get("tradeable"):
                    raise ExecutionServiceError("SYMBOL_UNAVAILABLE")
                bid, ask = symbol.get("bid"), symbol.get("ask")
                if bid is None or ask is None:
                    raise ExecutionServiceError("TICK_UNAVAILABLE")
                point = decimal_value(symbol["point"])
                spread_points = (decimal_value(ask) - decimal_value(bid)) / point if point > 0 else None
                if spread_points is None or spread_points > decimal_value(intent["maximum_spread"]):
                    raise ExecutionServiceError("SPREAD_EXCEEDS_LIMIT")

                self._persist_intent(intent, "MANUAL_CONFIRMATION_ACCEPTED", {
                    "intent_hash_fragment": intent["canonical_order_intent_hash"][:12],
                })

                request = _order_send_request(intent)
                self._persist_intent(intent, "ORDER_SEND_REQUESTED", {"request_hash": _request_hash(request)})
        except ExecutionJournalLockTimeout:
            raise ExecutionServiceError(
                "EXECUTION_LOCK_UNAVAILABLE",
                "the execution journal send lock was not available in time",
            )

        result = self._adapter.order_send(request)
        return self._finalize_send(intent, result)

    def _finalize_send(self, intent, result):
        if not isinstance(result, dict) or result.get("outcome") not in med.SEND_OUTCOMES:
            result = {"outcome": "MALFORMED", "comment": "malformed broker response"}

        outcome = result["outcome"]
        updated = dict(intent)

        if outcome == "FILLED":
            filled = result.get("volume_filled")
            requested = decimal_value(intent["quantity"])
            filled_value = decimal_value(filled) if filled is not None else None
            if filled_value is None or filled_value <= 0 or filled_value > requested:
                updated["execution_status"] = "FROZEN_PENDING_RECONCILIATION"
                updated["rejection_reasons"] = ["BROKER_RESULT_MISMATCH"]
                self._persist_intent(updated, "ORDER_SEND_RESULT", {"outcome": "BROKER_RESULT_MISMATCH", "raw_outcome": outcome})
                self._journal_append("UNCERTAIN_RESULT", {"order_intent_id": intent["order_intent_id"]})
            elif filled_value < requested:
                updated["execution_status"] = "PARTIALLY_FILLED"
                self._persist_intent(updated, "ORDER_SEND_RESULT", {"outcome": "PARTIALLY_FILLED", "ticket": result.get("ticket")})
            else:
                updated["execution_status"] = "FILLED"
                self._persist_intent(updated, "ORDER_SEND_RESULT", {"outcome": "FILLED", "ticket": result.get("ticket")})
        elif outcome == "PARTIALLY_FILLED":
            updated["execution_status"] = "PARTIALLY_FILLED"
            self._persist_intent(updated, "ORDER_SEND_RESULT", {"outcome": "PARTIALLY_FILLED", "ticket": result.get("ticket")})
        elif outcome == "REJECTED":
            updated["execution_status"] = "REJECTED"
            updated["rejection_reasons"] = ["ORDER_CHECK_FAILED"]
            self._persist_intent(updated, "ORDER_SEND_RESULT", {"outcome": "REJECTED", "comment": result.get("comment")})
        else:  # UNCERTAIN / MALFORMED
            updated["execution_status"] = "FROZEN_PENDING_RECONCILIATION"
            updated["rejection_reasons"] = ["UNCERTAIN_RESULT_BLOCKED"]
            self._persist_intent(updated, "ORDER_SEND_RESULT", {"outcome": outcome, "comment": result.get("comment")})
            self._journal_append("UNCERTAIN_RESULT", {"order_intent_id": intent["order_intent_id"]})

        return {"intent": updated, "send_result": result}

    def shutdown(self):
        return self._journal.shutdown()


def _request_hash(request):
    return sha256_text(deterministic_json_text(request))


def _magic_number_for(strategy_id):
    digest = sha256_text(strategy_id)
    return int(digest[:7], 16) % 900000000 + 100000000


def _bounded_comment_for(order_intent_id):
    return ("TRL:" + order_intent_id[4:20])[:26]


def _order_check_request(intent):
    order_type = "ORDER_TYPE_BUY_LIMIT" if intent["order_type"] == "BUY_LIMIT" else "ORDER_TYPE_SELL_LIMIT"
    return {
        "action": "TRADE_ACTION_PENDING",
        "symbol": intent["broker_native_instrument"],
        "volume": intent["quantity"],
        "type": order_type,
        "price": intent["entry_price"],
        "sl": intent["stop_loss"],
        "deviation": intent["maximum_deviation_points"],
        "type_time": "ORDER_TIME_GTC",
        "type_filling": intent["fill_policy"],
        "magic": _magic_number_for(intent["strategy_id"]),
        "comment": _bounded_comment_for(intent["order_intent_id"]),
    }


def _order_send_request(intent):
    return _order_check_request(intent)


def in_memory_service(mode_service=None, adapter=None, account_fingerprint=None, clock=None):
    return ExecutionService(
        adapter=adapter if adapter is not None else adapter_module.fake_adapter(clock=clock),
        mode_service=mode_service,
        journal=in_memory_journal_writer(clock=clock),
        account_fingerprint=account_fingerprint,
        clock=clock,
    )


__all__ = (
    "AccountFingerprintConfiguration",
    "DisabledExecutionService",
    "EXECUTION_GEOMETRY_APPROVED_STRATEGIES",
    "ExecutionService",
    "ExecutionServiceError",
    "MT5_INSTRUMENT_ALLOWLIST",
    "account_fingerprint_from_environment",
    "disabled_service",
    "in_memory_service",
    "unconfigured_account_fingerprint",
)
