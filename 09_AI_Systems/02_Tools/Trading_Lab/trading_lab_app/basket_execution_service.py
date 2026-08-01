"""Authoritative TRL-R2-009 controlled basket execution service (Phase 6).

Implements TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md. This is the
single place basket decisions are made; the CLI and the read-only HTTP
layer never re-derive authorization or state-machine logic — they call
this service and render its result. ``ModeService`` remains the sole
authority for *capability*; this service is the sole authority for basket
*execution correctness*.

Extends, and never duplicates, the existing Phase 5 (TRL-R2-007)
architecture: the same durable ``ExecutionJournalWriter`` (Section 38), the
same cross-process lock (Section 19), the same three-tier adapter boundary
(Section 32). Every basket document (``TRL_BASKET_PLAN.v1`` and friends) is
a separate, independently versioned schema (``basket_execution_data``);
``TRL_MT5_ORDER_INTENT.v1`` and every Phase 5 identity function are
unchanged (Section 1.1) — this module only *reads* an existing parent
order intent, it never constructs, mutates, or re-hashes one.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone

from . import basket_execution_data as bed
from . import mt5_execution_data as med
from . import mt5_execution_service as mes
from . import signal_strategy_registry as registry
from .mt5_execution_journal import ExecutionJournalLockTimeout
from .mt5_execution_service import (
    CHECK_FRESHNESS_SECONDS,
    CONFIRMATION_LIFETIME_SECONDS,
)
from .timeline_data import (
    canonical_decimal,
    decimal_value,
    deterministic_json_text,
    format_utc,
    sha256_text,
    validate_utc_timestamp,
)


BASKET_STATUS_VIEW_SCHEMA = "TRL_BASKET_STATUS.v1"


class BasketExecutionServiceError(RuntimeError):
    """Wraps a BasketValidationError-equivalent outcome with the exact
    governed reason_code, for callers that want it without a traceback."""

    def __init__(self, reason_code, message=None):
        self.reason_code = reason_code
        super().__init__(message or reason_code)


class DisabledBasketExecutionService:
    """The default. No basket mutation is ever possible; every mutating
    call fails closed with BASKET_CAPABILITY_DENIED."""

    enabled = False

    def __init__(self, operating_mode="OFF"):
        self.operating_mode = operating_mode

    def status_document(self):
        return {
            "schema_version": "TRL_BASKET_EXECUTION_STATUS.v1",
            "enabled": False,
            "operating_mode": self.operating_mode,
            "manual_basket_execution_granted": False,
            "demo_only": True,
            "live_execution_disabled": True,
            "automated_execution_disabled": True,
            "manual_confirmation_required": True,
            "sma001_blocked": True,
            "fib001_blocked": True,
            "message": "Basket execution is disabled in the {} operating mode.".format(self.operating_mode),
        }

    def _deny(self):
        raise BasketExecutionServiceError("BASKET_CAPABILITY_DENIED", "basket execution is disabled in this operating mode")

    def build_basket(self, order_intent_id):
        self._deny()

    def check_basket(self, basket_id):
        self._deny()

    def request_basket_confirmation(self, basket_id):
        self._deny()

    def confirm_basket(self, basket_id, entry_text, actor_channel="LOCAL_OPERATOR"):
        self._deny()

    def send_basket_next(self, basket_id):
        self._deny()

    def basket_status_document(self, basket_id):
        return {"found": False, "reason_code": "BASKET_CAPABILITY_DENIED"}

    def inspect_basket_document(self, basket_id):
        return {"found": False, "reason_code": "BASKET_CAPABILITY_DENIED"}

    def inspect_basket_child_document(self, basket_id, basket_child_id):
        return {"found": False, "reason_code": "BASKET_CAPABILITY_DENIED"}

    def list_baskets_document(self):
        return {"schema_version": "TRL_BASKET_LIST.v1", "enabled": False, "baskets": []}

    def basket_journal_document(self, limit=None):
        return {"schema_version": "TRL_BASKET_JOURNAL_VIEW.v1", "enabled": False, "events": []}

    def shutdown(self):
        return True


def disabled_basket_service(operating_mode="OFF"):
    return DisabledBasketExecutionService(operating_mode)


def _magic_number_for(strategy_id):
    digest = sha256_text(strategy_id)
    return int(digest[:7], 16) % 900000000 + 100000000


def _bounded_comment_for(basket_child_id):
    return ("TRLB:" + basket_child_id[3:19])[:26]


def _order_request_for_child(child_intent, parent_snapshot):
    order_type = "ORDER_TYPE_BUY_LIMIT" if child_intent["order_type"] == "BUY_LIMIT" else "ORDER_TYPE_SELL_LIMIT"
    return {
        "action": "TRADE_ACTION_PENDING",
        "symbol": child_intent["broker_native_instrument"],
        "volume": child_intent["child_quantity"],
        "type": order_type,
        "price": child_intent["entry_price"],
        "sl": child_intent["stop_loss"],
        "deviation": parent_snapshot["maximum_deviation_points"],
        "type_time": "ORDER_TIME_GTC",
        "type_filling": parent_snapshot["fill_policy"],
        "magic": _magic_number_for(child_intent["strategy_id"]),
        "comment": _bounded_comment_for(child_intent["basket_child_id"]),
    }


def _request_hash(request):
    return sha256_text(deterministic_json_text(request))


class BasketExecutionService:
    """The real Phase 6 basket execution service, bound to the same
    adapter/journal/account-fingerprint the Phase 5 ExecutionService uses."""

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
        from . import mt5_execution_adapter as adapter_module
        self._adapter = adapter if adapter is not None else adapter_module.disabled_adapter()
        self._mode_service = mode_service
        from .mt5_execution_journal import in_memory_journal_writer
        self._journal = journal if journal is not None else in_memory_journal_writer()
        self._account_fingerprint_config = account_fingerprint
        self.expected_risk_policy_hash = expected_risk_policy_hash
        self._clock = clock or (lambda: datetime.now(timezone.utc))

    # -- internals ----------------------------------------------------

    def _now(self):
        return format_utc(self._clock())

    def _now_dt(self):
        return validate_utc_timestamp(self._now())

    def _require_capability(self, *capabilities):
        if self._mode_service is None:
            raise BasketExecutionServiceError("BASKET_CAPABILITY_DENIED", "no mode service is wired")
        for capability in capabilities:
            if not self._mode_service.has_capability(capability):
                raise BasketExecutionServiceError("BASKET_CAPABILITY_DENIED", "capability {} is not granted".format(capability))
        if self._mode_service.current_mode != bed.BASKET_OPERATING_MODE:
            raise BasketExecutionServiceError(
                "BASKET_CAPABILITY_DENIED",
                "current mode {} does not authorize basket execution".format(self._mode_service.current_mode),
            )

    def _require_journal_integrity(self):
        if self._journal.startup_diagnostic_code != "OK":
            raise BasketExecutionServiceError("BASKET_JOURNAL_INTEGRITY_UNCERTAIN", "the execution journal failed integrity validation at startup")

    def _fingerprint_hash(self):
        config = self._account_fingerprint_config
        if config is None or not getattr(config, "configured", False):
            return None
        return config.fingerprint_hash()

    # -- durable basket-record read path --------------------------------
    # A "basket record" is this service's internal working representation
    # of one basket (the immutable TRL_BASKET_PLAN.v1 plus every mutable
    # fact about its progress) — not itself a formal contract schema.
    # Mirrors mt5_execution_service.py's `_persist_intent`/`_load_intent`
    # pattern: the FULL current record is attached to every basket-scoped
    # journal event, so loading is always "read the latest snapshot",
    # never incremental replay.

    def _all_basket_events(self):
        return [
            event for event in self._journal.events
            if isinstance(event.get("payload"), dict) and isinstance(event["payload"].get("basket_record"), dict)
        ]

    def _events_for_basket(self, basket_id):
        return [event for event in self._all_basket_events() if event["payload"]["basket_record"].get("basket_id") == basket_id]

    def _load_basket_record(self, basket_id):
        events = self._events_for_basket(basket_id)
        if not events:
            return None
        return deepcopy(events[-1]["payload"]["basket_record"])

    def _find_basket_by_lookup_key(self, lookup_key):
        seen = set()
        for event in reversed(self._all_basket_events()):
            record = event["payload"]["basket_record"]
            basket_id = record.get("basket_id")
            if basket_id in seen:
                continue
            seen.add(basket_id)
            if record.get("basket_lookup_key") == lookup_key:
                return self._load_basket_record(basket_id)
        return None

    def _find_confirmation_by_challenge(self, challenge_hex):
        """Search every basket's confirmation-cycle history for a matching
        challenge_hex. Returns (basket_id, cycle_dict) or (None, None)."""
        basket_ids = []
        seen = set()
        for event in self._all_basket_events():
            basket_id = event["payload"]["basket_record"].get("basket_id")
            if basket_id not in seen:
                seen.add(basket_id)
                basket_ids.append(basket_id)
        for basket_id in basket_ids:
            record = self._load_basket_record(basket_id)
            for cycle in record.get("confirmation_cycles", []):
                if cycle["challenge_hex"] == challenge_hex:
                    return basket_id, cycle
        return None, None

    def _persist(self, basket_record, event_type, extra_payload=None):
        payload = {"basket_id": basket_record["basket_id"], "basket_record": basket_record}
        if extra_payload:
            payload.update(extra_payload)
        return self._journal.append(event_type, payload, occurred_at_utc=self._now())

    # -- parent order-intent lookup (Phase 5 journal, read-only) ---------

    def _all_intent_events(self, order_intent_id):
        return [
            event for event in self._journal.events
            if isinstance(event.get("payload"), dict)
            and isinstance(event["payload"].get("intent"), dict)
            and event["payload"]["intent"].get("order_intent_id") == order_intent_id
        ]

    def _load_parent_intent(self, order_intent_id):
        events = self._all_intent_events(order_intent_id)
        if not events:
            return None
        return deepcopy(events[-1]["payload"]["intent"])

    # -- read-only status -------------------------------------------------

    def status_document(self):
        mode = self._mode_service.current_mode if self._mode_service else "OFF"
        granted = bool(self._mode_service and self._mode_service.has_capability("manual_basket_execution"))
        return {
            "schema_version": "TRL_BASKET_EXECUTION_STATUS.v1",
            "enabled": True,
            "operating_mode": mode,
            "manual_basket_execution_granted": granted,
            "demo_only": True,
            "live_execution_disabled": True,
            "automated_execution_disabled": True,
            "manual_confirmation_required": True,
            "sma001_blocked": "SMA-001" not in mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES,
            "fib001_blocked": True,
            "message": (
                "Phase 6 controlled manual demo basket execution only. Live and "
                "automated execution are unavailable. Every child order_send "
                "requires a fresh explicit local manual confirmation."
            ),
        }

    def list_baskets_document(self):
        seen = []
        for event in self._all_basket_events():
            basket_id = event["payload"]["basket_record"]["basket_id"]
            if basket_id not in seen:
                seen.append(basket_id)
        return {
            "schema_version": "TRL_BASKET_LIST.v1",
            "enabled": True,
            "baskets": [self.basket_status_document(basket_id) for basket_id in seen],
        }

    def basket_journal_document(self, limit=None):
        events = self._all_basket_events()
        if limit is not None:
            events = events[-limit:]
        return {
            "schema_version": "TRL_BASKET_JOURNAL_VIEW.v1",
            "enabled": True,
            "event_count": len(events),
            "events": events,
        }

    def inspect_basket_document(self, basket_id):
        record = self._load_basket_record(basket_id)
        if record is None:
            return {"found": False, "reason_code": "BASKET_NOT_FOUND"}
        return {"found": True, "plan": record["plan"], "status": self.basket_status_document(basket_id)}

    def inspect_basket_child_document(self, basket_id, basket_child_id):
        record = self._load_basket_record(basket_id)
        if record is None or basket_child_id not in record.get("children", {}):
            return {"found": False, "reason_code": "BASKET_NOT_FOUND"}
        child = record["children"][basket_child_id]
        return {"found": True, "child": child}

    def basket_status_document(self, basket_id):
        record = self._load_basket_record(basket_id)
        if record is None:
            return {"found": False, "reason_code": "BASKET_NOT_FOUND"}
        plan = record["plan"]
        children = record["children"]
        filled = [cid for cid, c in children.items() if c["execution_state"] == "FILLED"]
        filled_count = len(filled)
        completed_quantity = sum((decimal_value(children[cid]["intent"]["child_quantity"]) for cid in filled), decimal_value("0"))
        total_quantity = decimal_value(plan["total_quantity"])
        active_cycle = self._active_cycle(record)
        confirmation_status = "NOT_REQUESTED"
        active_request_id = None
        active_cycle_number = None
        authorized_start = None
        authorized_remaining = None
        if active_cycle is not None:
            confirmation_status = {
                "REQUESTED": "AWAITING", "ACCEPTED": "ACCEPTED",
                "INVALIDATED": "INVALIDATED", "EXPIRED": "EXPIRED",
            }[active_cycle["status"]]
            active_request_id = active_cycle["confirmation_request_id"]
            active_cycle_number = active_cycle["confirmation_cycle_number"]
            authorized_start = active_cycle["authorized_start_child_id"]
            authorized_remaining = list(active_cycle["authorized_remaining_child_ids"])
        live_next = None
        try:
            live_next = self._compute_live_next_eligible(record, active_cycle) if active_cycle is not None else None
        except BasketExecutionServiceError:
            live_next = None
        child_docs = []
        for descriptor in plan["children"]:
            cid = descriptor["basket_child_id"]
            child = children[cid]
            last_check = child.get("last_check")
            fresh = False
            if last_check is not None:
                age = (self._now_dt() - validate_utc_timestamp(last_check["checked_at_utc"])).total_seconds()
                fresh = last_check["check_outcome"] == "PASSED" and age <= CHECK_FRESHNESS_SECONDS
            child_docs.append({
                "basket_child_id": cid,
                "target_price": descriptor["target_price"],
                "target_allocation_percent": descriptor["target_allocation_percent"],
                "child_quantity": descriptor["child_quantity"],
                "check_status": last_check["check_outcome"] if last_check else None,
                "check_fresh": fresh,
                "send_status": (child.get("send_result") or {}).get("send_outcome"),
                "execution_state": child["execution_state"],
            })
        return {
            "found": True,
            "schema_version": BASKET_STATUS_VIEW_SCHEMA,
            "basket_id": basket_id,
            "basket_status": record["basket_status"],
            "reconciliation_required": record["basket_status"] in bed.RECONCILIATION_REQUIRED_STATUSES,
            "parent_proposal_id": plan["parent_proposal_id"],
            "parent_order_intent_id": plan["parent_order_intent_id"],
            "broker_native_instrument": plan["broker_native_instrument"],
            "side": plan["side"],
            "total_quantity": plan["total_quantity"],
            "child_count": plan["child_count"],
            "filled_child_count": filled_count,
            "completed_quantity": canonical_decimal(completed_quantity),
            "remaining_quantity": canonical_decimal(total_quantity - completed_quantity),
            "children": child_docs,
            "confirmation_status": confirmation_status,
            "active_confirmation_request_id": active_request_id,
            "active_confirmation_cycle_number": active_cycle_number,
            "authorized_start_child_id": authorized_start,
            "authorized_remaining_child_ids": authorized_remaining,
            "live_next_eligible_child_id": live_next,
            "created_at_utc": plan["created_at_utc"],
            "expires_at_utc": plan["expires_at_utc"],
            "rejection_reasons": record["rejection_reasons"],
            "terminal_reason": record["terminal_reason"],
            "canonical_basket_plan_hash": plan["canonical_basket_plan_hash"],
        }

    # -- shared helpers ---------------------------------------------------

    def _active_cycle(self, record):
        cycles = record.get("confirmation_cycles") or []
        return cycles[-1] if cycles else None

    def _currently_required_children(self, record):
        """Every basket child not yet FILLED and not otherwise terminal —
        Section 24.2's exact definition of "currently required"."""
        return [
            (cid, child) for cid, child in record["children"].items()
            if child["execution_state"] not in bed.TERMINAL_BASKET_CHILD_STATES
        ]

    def _check_basket_expiry(self, record):
        if record["basket_status"] in bed.TERMINAL_BASKET_STATUSES:
            return record
        if self._now_dt() < validate_utc_timestamp(record["plan"]["expires_at_utc"]):
            return record
        filled_count = sum(1 for c in record["children"].values() if c["execution_state"] == "FILLED")
        new_status = "PARTIALLY_COMPLETED" if filled_count > 0 else "EXPIRED"
        record["basket_status"] = new_status
        record["terminal_reason"] = "BASKET_EXPIRED"
        record["rejection_reasons"].append("BASKET_EXPIRED")
        active = self._active_cycle(record)
        if active is not None and active["status"] in ("REQUESTED", "ACCEPTED"):
            active["status"] = "INVALIDATED"
            active["invalidated_at_utc"] = self._now()
            active["invalidation_reason"] = "BASKET_EXPIRED"
        event_type = "BASKET_PARTIALLY_COMPLETED" if new_status == "PARTIALLY_COMPLETED" else "BASKET_EXPIRED"
        self._persist(record, event_type, {"reason_code": "BASKET_EXPIRED"})
        raise BasketExecutionServiceError("BASKET_EXPIRED", "the basket plan or parent intent has expired")

    def _verify_fresh_or_recover(self, record):
        """Section 24.1/24.2: revalidate freshness of every currently-
        required child's latest PASSED check. If any is missing entirely,
        the caller's own gate gives BASKET_NOT_CHECK_COMPLETE. If any HAS a
        passed check that has gone stale, this method performs the exact
        stale-check recovery (invalidate the active cycle if any, return
        every currently-required child to CHECK_REQUIRED, preserve every
        FILLED child untouched) and raises BASKET_CHILD_CHECK_STALE."""
        now = self._now_dt()
        required = self._currently_required_children(record)
        stale = False
        for _cid, child in required:
            last_check = child.get("last_check")
            if last_check is None or last_check["check_outcome"] != "PASSED":
                continue
            age = (now - validate_utc_timestamp(last_check["checked_at_utc"])).total_seconds()
            if age > CHECK_FRESHNESS_SECONDS:
                stale = True
        if not stale:
            return record
        active = self._active_cycle(record)
        if active is not None and active["status"] in ("REQUESTED", "ACCEPTED"):
            active["status"] = "INVALIDATED"
            active["invalidated_at_utc"] = self._now()
            active["invalidation_reason"] = "BASKET_CHILD_CHECK_STALE"
            self._persist(record, "BASKET_CONFIRMATION_INVALIDATED", {
                "confirmation_request_id": active["confirmation_request_id"],
                "confirmation_cycle_number": active["confirmation_cycle_number"],
                "reason_code": "BASKET_CHILD_CHECK_STALE",
            })
        for cid, child in required:
            child["execution_state"] = "CHECK_REQUIRED"
        record["basket_status"] = "CHECK_REQUIRED"
        self._persist(record, "BASKET_CHILD_CHECK_STALE")
        self._persist(record, "BASKET_RECHECK_REQUIRED")
        raise BasketExecutionServiceError("BASKET_CHILD_CHECK_STALE", "one or more required checks are no longer fresh; a new confirmation cycle is required")

    def _compute_live_next_eligible(self, record, active_cycle):
        if active_cycle is None or active_cycle["status"] != "ACCEPTED":
            raise BasketExecutionServiceError("BASKET_CONFIRMATION_UNAVAILABLE", "no accepted confirmation cycle exists")
        prior = set(active_cycle["authorized_prior_filled_child_ids"])
        remaining = active_cycle["authorized_remaining_child_ids"]
        plan_children = record["plan"]["children"]
        for descriptor in plan_children:
            cid = descriptor["basket_child_id"]
            if cid not in remaining:
                continue
            child = record["children"][cid]
            if child["execution_state"] in bed.TERMINAL_BASKET_CHILD_STATES:
                continue
            lower_ok = True
            for other in plan_children:
                if other["child_index"] >= descriptor["child_index"]:
                    continue
                other_id = other["basket_child_id"]
                if other_id in prior:
                    continue
                if record["children"][other_id]["execution_state"] == "FILLED":
                    continue
                lower_ok = False
                break
            if not lower_ok:
                continue
            if child["execution_state"] == "SEND_RESERVED":
                raise BasketExecutionServiceError("BASKET_CHILD_SEND_ALREADY_RESERVED", "a child send reservation is already in progress")
            return cid
        raise BasketExecutionServiceError("BASKET_CHILD_NOT_NEXT_ELIGIBLE", "no live next-eligible child exists for the active cycle")

    # -- basket construction (Sections 7, 8, 17, 20, 21, 22) -------------

    def build_basket(self, order_intent_id):
        self._require_capability("manual_basket_execution")
        self._require_journal_integrity()

        intent = self._load_parent_intent(order_intent_id)
        if intent is None:
            raise BasketExecutionServiceError("BASKET_PARENT_INTENT_NOT_FOUND")
        if intent.get("schema_version") != med.ORDER_INTENT_SCHEMA:
            raise BasketExecutionServiceError("PARENT_SCHEMA_VERSION_UNSUPPORTED")
        try:
            intent = med.validate_order_intent(intent)
        except med.ExecutionValidationError as error:
            raise BasketExecutionServiceError("BASKET_PARENT_INTENT_HASH_MISMATCH", str(error))

        if intent["operating_mode"] != bed.BASKET_OPERATING_MODE:
            raise BasketExecutionServiceError("BASKET_PARENT_INTENT_NOT_ELIGIBLE", "parent operating_mode is not MT5_DEMO_MANUAL")
        if intent["execution_status"] != "CREATED":
            raise BasketExecutionServiceError("BASKET_PARENT_INTENT_NOT_ELIGIBLE", "parent intent has already left the CREATED state")
        targets = intent["targets"]
        allocations = intent["target_allocations_percent"]
        if len(targets) != len(allocations) or not (bed.MIN_CHILD_COUNT <= len(targets) <= bed.MAX_CHILD_COUNT):
            raise BasketExecutionServiceError("BASKET_CHILD_COUNT_INVALID", "parent must declare between 2 and 4 targets")
        if self._now_dt() >= validate_utc_timestamp(intent["expires_at_utc"]):
            raise BasketExecutionServiceError("BASKET_PARENT_EXPIRED")

        configured_fingerprint = self._fingerprint_hash()
        if configured_fingerprint is None:
            raise BasketExecutionServiceError("BASKET_PARENT_INTENT_NOT_ELIGIBLE", "no approved demo account fingerprint is configured")
        if intent["account_fingerprint_hash"] != configured_fingerprint:
            raise BasketExecutionServiceError("BASKET_PARENT_INTENT_NOT_ELIGIBLE", "account fingerprint mismatch")
        if self.expected_risk_policy_hash is not None and intent["risk_policy_hash"] != self.expected_risk_policy_hash:
            raise BasketExecutionServiceError("BASKET_PARENT_INTENT_NOT_ELIGIBLE", "risk policy hash mismatch")

        lookup_fields = {
            "parent_order_intent_id": order_intent_id,
            "canonical_parent_order_intent_hash": intent["canonical_order_intent_hash"],
            "account_fingerprint_hash": intent["account_fingerprint_hash"],
            "broker_native_instrument": intent["broker_native_instrument"],
            "side": intent["side"],
            "strategy_id": intent["strategy_id"],
            "strategy_version": intent["strategy_version"],
            "risk_policy_hash": intent["risk_policy_hash"],
            "operating_mode": bed.BASKET_OPERATING_MODE,
            "authorization_identity": "LOCAL_OPERATOR",
            "child_count": len(targets),
            "target_set_hash": bed.target_set_hash(targets, allocations),
        }
        lookup_key = bed.basket_lookup_key(lookup_fields)
        basket_id = bed.basket_id_for(lookup_key)

        try:
            with self._journal.acquire_creation_lock():
                existing = self._find_basket_by_lookup_key(lookup_key)
                if existing is not None:
                    self._persist(existing, "BASKET_REUSED", {"basket_lookup_key": lookup_key})
                    return existing

                # SMA-001/FIB-001 blockers (Section 7) — checked only once
                # a basket_id is computable, so a blocked attempt is itself
                # persisted (BLOCKED), not silently dropped.
                allowed, reason = registry.executable_status(intent["strategy_id"])
                blocked_reason = None
                if not allowed:
                    blocked_reason = reason
                elif intent["strategy_id"] not in mes.EXECUTION_GEOMETRY_APPROVED_STRATEGIES:
                    blocked_reason = "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED"

                if blocked_reason is not None:
                    record = self._skeleton_record(basket_id, lookup_key, "BLOCKED", blocked_reason)
                    self._persist(record, "BASKET_BLOCKED", {"reason_code": blocked_reason})
                    raise BasketExecutionServiceError(blocked_reason)

                symbol = self._adapter.symbol_status(intent["broker_native_instrument"])
                if not symbol.get("available"):
                    record = self._skeleton_record(basket_id, lookup_key, "REJECTED", "SYMBOL_UNAVAILABLE")
                    self._persist(record, "BASKET_REJECTED", {"reason_code": "SYMBOL_UNAVAILABLE"})
                    raise BasketExecutionServiceError("SYMBOL_UNAVAILABLE")

                try:
                    quantities = bed.compute_child_quantities(
                        intent["quantity"], allocations,
                        symbol["volume_minimum"], symbol["volume_maximum"], symbol["volume_step"],
                    )
                except bed.BasketValidationError as error:
                    record = self._skeleton_record(basket_id, lookup_key, "REJECTED", error.reason_code)
                    self._persist(record, "BASKET_REJECTED", {"reason_code": error.reason_code})
                    raise BasketExecutionServiceError(error.reason_code)

                if len(set(targets)) != len(targets):
                    record = self._skeleton_record(basket_id, lookup_key, "REJECTED", "BASKET_TARGET_NOT_UNIQUE")
                    self._persist(record, "BASKET_REJECTED", {"reason_code": "BASKET_TARGET_NOT_UNIQUE"})
                    raise BasketExecutionServiceError("BASKET_TARGET_NOT_UNIQUE")
                if intent["order_type"] not in bed.ORDER_TYPES:
                    record = self._skeleton_record(basket_id, lookup_key, "REJECTED", "BASKET_ORDER_TYPE_MISMATCH")
                    self._persist(record, "BASKET_REJECTED", {"reason_code": "BASKET_ORDER_TYPE_MISMATCH"})
                    raise BasketExecutionServiceError("BASKET_ORDER_TYPE_MISMATCH")

                now = self._now()
                approved_aggregate_risk_id = bed.approved_aggregate_risk_id_for(basket_id)
                children_state = {}
                child_descriptors = []
                for index, (target, allocation, quantity) in enumerate(zip(targets, allocations, quantities)):
                    # Founder-approved non-circular formula (correction round,
                    # entry 2026-08-01-020): the child lookup key is derived
                    # only from basket_id plus the immutable parent-proposal/
                    # parent-order-intent identity and the per-child economic
                    # fields — never from canonical_basket_plan_hash, which is
                    # itself computed below FROM these children's own IDs. A
                    # plan hash can never be an input to the child IDs that
                    # are themselves part of that same plan hash.
                    child_lookup_key = bed.basket_child_lookup_key({
                        "basket_id": basket_id,
                        "parent_proposal_id": intent["proposal_id"],
                        "canonical_parent_proposal_hash": intent["canonical_proposal_hash"],
                        "parent_order_intent_id": order_intent_id,
                        "canonical_parent_order_intent_hash": intent["canonical_order_intent_hash"],
                        "account_fingerprint_hash": intent["account_fingerprint_hash"],
                        "child_index": index,
                        "target_price": target,
                        "target_allocation_percent": allocation,
                        "child_quantity": quantity,
                        "broker_native_instrument": intent["broker_native_instrument"],
                        "side": intent["side"],
                        "order_type": intent["order_type"],
                        "entry_price": intent["entry_price"],
                        "stop_loss": intent["stop_loss"],
                        "strategy_id": intent["strategy_id"],
                        "strategy_version": intent["strategy_version"],
                        "risk_policy_hash": intent["risk_policy_hash"],
                        "operating_mode": bed.BASKET_OPERATING_MODE,
                        "expires_at_utc": intent["expires_at_utc"],
                    })
                    basket_child_id = bed.basket_child_id_for(child_lookup_key)
                    descriptor = {
                        "child_index": index, "basket_child_id": basket_child_id,
                        "target_price": target, "target_allocation_percent": allocation,
                        "child_quantity": quantity,
                    }
                    child_descriptors.append(descriptor)

                plan_without_hash = {
                    "schema_version": bed.BASKET_PLAN_SCHEMA,
                    "basket_id": basket_id,
                    "basket_lookup_key": lookup_key,
                    "parent_proposal_id": intent["proposal_id"],
                    "canonical_parent_proposal_hash": intent["canonical_proposal_hash"],
                    "parent_order_intent_id": order_intent_id,
                    "canonical_parent_order_intent_hash": intent["canonical_order_intent_hash"],
                    "account_fingerprint_hash": intent["account_fingerprint_hash"],
                    "broker_native_instrument": intent["broker_native_instrument"],
                    "side": intent["side"],
                    "order_type": intent["order_type"],
                    "entry_price": intent["entry_price"],
                    "stop_loss": intent["stop_loss"],
                    "total_quantity": intent["quantity"],
                    "approved_aggregate_risk_id": approved_aggregate_risk_id,
                    "child_count": len(child_descriptors),
                    "children": child_descriptors,
                    "strategy_id": intent["strategy_id"],
                    "strategy_version": intent["strategy_version"],
                    "risk_policy_hash": intent["risk_policy_hash"],
                    "operating_mode": bed.BASKET_OPERATING_MODE,
                    "created_at_utc": now,
                    "expires_at_utc": intent["expires_at_utc"],
                }
                plan_hash = bed.canonical_basket_plan_hash_for(plan_without_hash)
                plan = dict(plan_without_hash)
                plan["canonical_basket_plan_hash"] = plan_hash
                plan = bed.validate_basket_plan(plan)

                for descriptor in child_descriptors:
                    child_doc_without_hash = {
                        "schema_version": bed.BASKET_CHILD_INTENT_SCHEMA,
                        "basket_id": basket_id,
                        "canonical_basket_plan_hash_at_creation": plan_hash,
                        "basket_child_id": descriptor["basket_child_id"],
                        "child_index": descriptor["child_index"],
                        "parent_order_intent_id": order_intent_id,
                        "account_fingerprint_hash": intent["account_fingerprint_hash"],
                        "broker_native_instrument": intent["broker_native_instrument"],
                        "side": intent["side"],
                        "order_type": intent["order_type"],
                        "entry_price": intent["entry_price"],
                        "stop_loss": intent["stop_loss"],
                        "strategy_id": intent["strategy_id"],
                        "strategy_version": intent["strategy_version"],
                        "risk_policy_hash": intent["risk_policy_hash"],
                        "operating_mode": bed.BASKET_OPERATING_MODE,
                        "expires_at_utc": intent["expires_at_utc"],
                        "target_price": descriptor["target_price"],
                        "target_allocation_percent": descriptor["target_allocation_percent"],
                        "child_quantity": descriptor["child_quantity"],
                        "idempotency_key": descriptor["basket_child_id"],
                    }
                    child_hash = bed.canonical_basket_child_hash_for(child_doc_without_hash)
                    child_doc = dict(child_doc_without_hash)
                    child_doc["canonical_basket_child_hash"] = child_hash
                    child_doc = bed.validate_basket_child_intent(child_doc)
                    children_state[descriptor["basket_child_id"]] = {
                        "intent": child_doc,
                        "execution_state": "CREATED",
                        "last_check": None,
                        "send_result": None,
                    }

                record = {
                    "basket_id": basket_id,
                    "basket_lookup_key": lookup_key,
                    "plan": plan,
                    "parent_intent_snapshot": intent,
                    "basket_status": "CREATED",
                    "rejection_reasons": [],
                    "terminal_reason": None,
                    "children": children_state,
                    "confirmation_cycles": [],
                }
                self._persist(record, "BASKET_CREATED")
                for descriptor in child_descriptors:
                    self._persist(record, "BASKET_CHILD_CREATED", {"basket_child_id": descriptor["basket_child_id"]})
                return record
        except ExecutionJournalLockTimeout:
            raise BasketExecutionServiceError("BASKET_EXECUTION_LOCK_UNAVAILABLE", "the basket creation lock was not available in time")

    def _skeleton_record(self, basket_id, lookup_key, status, reason_code):
        return {
            "basket_id": basket_id,
            "basket_lookup_key": lookup_key,
            "plan": None,
            "parent_intent_snapshot": None,
            "basket_status": status,
            "rejection_reasons": [reason_code],
            "terminal_reason": reason_code,
            "children": {},
            "confirmation_cycles": [],
        }

    # -- child check sequence (Sections 11, 24) ---------------------------

    def check_basket(self, basket_id):
        self._require_capability("manual_basket_execution", "mt5_order_check")
        self._require_journal_integrity()
        record = self._load_basket_record(basket_id)
        if record is None:
            raise BasketExecutionServiceError("BASKET_NOT_FOUND")
        if record["basket_status"] in bed.TERMINAL_BASKET_STATUSES:
            raise BasketExecutionServiceError("BASKET_ALREADY_TERMINAL")
        self._check_basket_expiry(record)

        required = self._currently_required_children(record)
        target = None
        for cid, child in required:
            last_check = child.get("last_check")
            fresh_passed = (
                last_check is not None and last_check["check_outcome"] == "PASSED"
                and (self._now_dt() - validate_utc_timestamp(last_check["checked_at_utc"])).total_seconds() <= CHECK_FRESHNESS_SECONDS
            )
            if not fresh_passed:
                target = (cid, child)
                break
        if target is None:
            record["basket_status"] = "CHECK_COMPLETE"
            self._persist(record, "BASKET_CHILD_CHECK_RESULT", {"already_complete": True})
            return record

        cid, child = target
        if child["execution_state"] == "FILLED" or child["execution_state"] in bed.TERMINAL_BASKET_CHILD_STATES:
            raise BasketExecutionServiceError("BASKET_CHILD_ALREADY_FILLED")

        child_intent = child["intent"]
        record["basket_status"] = "CHECKING"
        self._persist(record, "BASKET_CHILD_CHECK_REQUESTED", {"basket_child_id": cid})

        request = _order_request_for_child(child_intent, record["parent_intent_snapshot"])
        result = self._adapter.order_check(request)
        checked_at = self._now()
        if not isinstance(result, dict) or result.get("outcome") not in med.CHECK_OUTCOMES:
            outcome, reasons = "MALFORMED", ["BASKET_CHILD_CHECK_FAILED"]
        elif result["outcome"] != "PASSED":
            outcome, reasons = "FAILED", ["BASKET_CHILD_CHECK_FAILED"]
        else:
            outcome, reasons = "PASSED", []

        check_result_id = bed.check_result_id_for(basket_id, cid, child_intent["canonical_basket_child_hash"], checked_at)
        check_hash = bed.canonical_basket_check_hash_for({
            "basket_id": basket_id, "basket_child_id": cid,
            "canonical_basket_child_hash_at_check": child_intent["canonical_basket_child_hash"],
            "checked_at_utc": checked_at, "check_outcome": outcome,
        })
        check_record = bed.validate_basket_check_result({
            "schema_version": bed.BASKET_CHECK_RESULT_SCHEMA,
            "check_result_id": check_result_id,
            "basket_id": basket_id, "basket_child_id": cid,
            "canonical_basket_child_hash_at_check": child_intent["canonical_basket_child_hash"],
            "checked_at_utc": checked_at, "check_outcome": outcome,
            "reason_codes": reasons, "canonical_basket_check_hash": check_hash,
        })
        child["last_check"] = check_record
        if outcome == "PASSED":
            child["execution_state"] = "CHECK_PASSED"
        else:
            child["execution_state"] = "CHECK_REQUIRED"

        remaining_required = self._currently_required_children(record)
        all_passed = all(
            c["last_check"] is not None and c["last_check"]["check_outcome"] == "PASSED"
            and (self._now_dt() - validate_utc_timestamp(c["last_check"]["checked_at_utc"])).total_seconds() <= CHECK_FRESHNESS_SECONDS
            for _cid, c in remaining_required
        )
        record["basket_status"] = "CHECK_COMPLETE" if all_passed else "CHECK_REQUIRED"
        self._persist(record, "BASKET_CHILD_CHECK_RESULT", {"basket_child_id": cid, "check_outcome": outcome})
        return record

    # -- confirmation cycle (Section 13) ----------------------------------

    def _build_confirmation_basis(self, record):
        required = self._currently_required_children(record)
        prior = sorted(
            (cid for cid, c in record["children"].items() if c["execution_state"] == "FILLED"),
            key=lambda cid: record["children"][cid]["intent"]["child_index"],
        )
        remaining_pairs = sorted(required, key=lambda item: item[1]["intent"]["child_index"])
        remaining = [cid for cid, _c in remaining_pairs]
        if not remaining:
            raise BasketExecutionServiceError("BASKET_NOT_CHECK_COMPLETE", "no unsent child remains")
        check_ids, check_hashes = [], []
        for cid, child in remaining_pairs:
            last_check = child.get("last_check")
            if last_check is None or last_check["check_outcome"] != "PASSED":
                raise BasketExecutionServiceError("BASKET_NOT_CHECK_COMPLETE")
            age = (self._now_dt() - validate_utc_timestamp(last_check["checked_at_utc"])).total_seconds()
            if age > CHECK_FRESHNESS_SECONDS:
                raise BasketExecutionServiceError("BASKET_NOT_CHECK_COMPLETE")
            check_ids.append(last_check["check_result_id"])
            check_hashes.append(last_check["canonical_basket_check_hash"])
        basis_fields = {
            "basket_id": record["basket_id"],
            "canonical_basket_plan_hash": record["plan"]["canonical_basket_plan_hash"],
            "account_fingerprint_hash": record["plan"]["account_fingerprint_hash"],
            "authorized_prior_filled_child_ids": prior,
            "authorized_remaining_child_ids": remaining,
            "authorized_start_child_id": remaining[0],
            "ordered_required_check_ids": check_ids,
            "ordered_required_check_hashes": check_hashes,
            "operating_mode": bed.BASKET_OPERATING_MODE,
            "confirmation_lifetime_seconds": CONFIRMATION_LIFETIME_SECONDS,
        }
        basis_hash = bed.confirmation_basis_hash_for(basis_fields)
        return basis_fields, basis_hash

    def request_basket_confirmation(self, basket_id):
        self._require_capability("manual_basket_execution")
        self._require_journal_integrity()
        try:
            with self._journal.acquire_creation_lock():
                record = self._load_basket_record(basket_id)
                if record is None:
                    raise BasketExecutionServiceError("BASKET_NOT_FOUND")
                if record["basket_status"] in bed.TERMINAL_BASKET_STATUSES:
                    raise BasketExecutionServiceError("BASKET_ALREADY_TERMINAL")
                if record["basket_status"] not in ("CHECK_COMPLETE", "AWAITING_CONFIRMATION"):
                    raise BasketExecutionServiceError("BASKET_NOT_CHECK_COMPLETE")
                self._check_basket_expiry(record)
                self._verify_fresh_or_recover(record)

                basis_fields, basis_hash = self._build_confirmation_basis(record)
                active = self._active_cycle(record)
                highest_cycle = max((c["confirmation_cycle_number"] for c in record["confirmation_cycles"]), default=0)
                now = self._now()

                if active is not None and active["status"] == "REQUESTED":
                    active_expired = self._now_dt() >= validate_utc_timestamp(active["expires_at_utc"])
                    if not active_expired and active["confirmation_basis_hash"] == basis_hash:
                        record["basket_status"] = "AWAITING_CONFIRMATION"
                        self._persist(record, "BASKET_CONFIRMATION_REQUEST_REUSED", {
                            "confirmation_request_id": active["confirmation_request_id"],
                            "confirmation_cycle_number": active["confirmation_cycle_number"],
                        })
                        return active
                    if active_expired:
                        active["status"] = "EXPIRED"
                        active["expired_at_utc"] = now
                        self._persist(record, "BASKET_CONFIRMATION_EXPIRED", {
                            "confirmation_request_id": active["confirmation_request_id"],
                            "confirmation_cycle_number": active["confirmation_cycle_number"],
                        })
                    else:
                        active["status"] = "INVALIDATED"
                        active["invalidated_at_utc"] = now
                        active["invalidation_reason"] = "BASKET_CONFIRMATION_BASIS_CHANGED"
                        self._persist(record, "BASKET_CONFIRMATION_INVALIDATED", {
                            "confirmation_request_id": active["confirmation_request_id"],
                            "confirmation_cycle_number": active["confirmation_cycle_number"],
                            "reason_code": "BASKET_CONFIRMATION_BASIS_CHANGED",
                        })

                cycle_number = highest_cycle + 1
                expires_at = format_utc(self._clock() + timedelta(seconds=CONFIRMATION_LIFETIME_SECONDS))
                request_id = bed.confirmation_request_id_for(
                    record["basket_id"], record["plan"]["canonical_basket_plan_hash"], basis_hash,
                    cycle_number, now, expires_at,
                )
                challenge = bed.challenge_hex_for(request_id, record["basket_id"], record["plan"]["canonical_basket_plan_hash"], basis_hash)
                cycle_without_hash = {
                    "schema_version": bed.BASKET_CONFIRMATION_SCHEMA,
                    "confirmation_request_id": request_id,
                    "confirmation_cycle_number": cycle_number,
                    "basket_id": record["basket_id"],
                    "canonical_basket_plan_hash": record["plan"]["canonical_basket_plan_hash"],
                    "confirmation_basis_hash": basis_hash,
                    "account_fingerprint_hash": basis_fields["account_fingerprint_hash"],
                    "authorized_prior_filled_child_ids": basis_fields["authorized_prior_filled_child_ids"],
                    "authorized_remaining_child_ids": basis_fields["authorized_remaining_child_ids"],
                    "authorized_start_child_id": basis_fields["authorized_start_child_id"],
                    "ordered_required_check_ids": basis_fields["ordered_required_check_ids"],
                    "ordered_required_check_hashes": basis_fields["ordered_required_check_hashes"],
                    "challenge_derivation_version": bed.CONFIRM_CHALLENGE_DOMAIN,
                    "challenge_hex": challenge,
                    "requested_at_utc": now,
                    "expires_at_utc": expires_at,
                    "status": "REQUESTED",
                    "accepted_at_utc": None,
                    "expired_at_utc": None,
                    "invalidated_at_utc": None,
                    "invalidation_reason": None,
                }
                identity_fields = bed._confirmation_identity_fields(cycle_without_hash)
                cycle = dict(cycle_without_hash)
                cycle["canonical_confirmation_request_hash"] = bed.canonical_confirmation_request_hash_for(identity_fields)
                cycle = bed.validate_basket_confirmation(cycle)
                record["confirmation_cycles"].append(cycle)
                record["basket_status"] = "AWAITING_CONFIRMATION"
                self._persist(record, "BASKET_CONFIRMATION_REQUESTED", {
                    "confirmation_request_id": request_id, "confirmation_cycle_number": cycle_number,
                })
                return cycle
        except ExecutionJournalLockTimeout:
            raise BasketExecutionServiceError("BASKET_EXECUTION_LOCK_UNAVAILABLE")

    def confirm_basket(self, basket_id, entry_text, actor_channel="LOCAL_OPERATOR"):
        self._require_capability("manual_basket_execution")
        self._require_journal_integrity()
        try:
            challenge = bed.parse_confirmation_entry(entry_text)
        except bed.BasketValidationError as error:
            # entry_text is raw, untrusted, operator-typed text — unlike
            # every other bed.* call in this module (which validate data
            # this service just computed internally and would only ever
            # fail on a genuine internal defect), a malformed confirmation
            # phrase is an entirely normal, expected rejection outcome and
            # must surface as a governed, catchable error — never a raw
            # traceback — exactly like every other confirm_basket rejection.
            raise BasketExecutionServiceError(error.reason_code, str(error))

        try:
            with self._journal.acquire_creation_lock():
                record = self._load_basket_record(basket_id)
                if record is None:
                    raise BasketExecutionServiceError("BASKET_NOT_FOUND")
                if record["basket_status"] in bed.TERMINAL_BASKET_STATUSES:
                    raise BasketExecutionServiceError("BASKET_ALREADY_TERMINAL")
                self._check_basket_expiry(record)

                active = self._active_cycle(record)
                if active is not None and active["challenge_hex"] == challenge and active["status"] in ("REQUESTED", "ACCEPTED"):
                    matched_cycle, matched_kind = active, "current"
                else:
                    matched_cycle, matched_kind = None, None
                    for cycle in record["confirmation_cycles"]:
                        if cycle["challenge_hex"] == challenge and cycle is not active:
                            if cycle["status"] == "EXPIRED":
                                matched_cycle, matched_kind = cycle, "expired"
                            elif cycle["status"] == "INVALIDATED":
                                matched_cycle, matched_kind = cycle, "invalidated"
                            else:
                                matched_cycle, matched_kind = cycle, "wrong"
                            break
                    if matched_cycle is None:
                        other_basket_id, other_cycle = self._find_confirmation_by_challenge(challenge)
                        if other_cycle is not None and other_basket_id != basket_id:
                            matched_cycle, matched_kind = other_cycle, "wrong"

                if matched_kind == "expired":
                    self._persist(record, "BASKET_CONFIRMATION_REJECTED", {"reason_code": "BASKET_CONFIRMATION_EXPIRED"})
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_EXPIRED")
                if matched_kind == "invalidated":
                    self._persist(record, "BASKET_CONFIRMATION_REJECTED", {"reason_code": "BASKET_CONFIRMATION_INVALIDATED"})
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_INVALIDATED")
                if matched_kind == "wrong":
                    self._persist(record, "BASKET_CONFIRMATION_REJECTED", {"reason_code": "BASKET_CONFIRMATION_WRONG_REQUEST"})
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_WRONG_REQUEST")
                if matched_kind != "current":
                    self._persist(record, "BASKET_CONFIRMATION_REJECTED", {"reason_code": "BASKET_CONFIRMATION_MISMATCH"})
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_MISMATCH")

                if active["status"] == "ACCEPTED":
                    # Checked before the generic basket_status gate below:
                    # acceptance itself moves basket_status away from
                    # AWAITING_CONFIRMATION, so a second confirm attempt
                    # against the same already-accepted cycle would
                    # otherwise always be misreported as the vaguer
                    # BASKET_CONFIRMATION_UNAVAILABLE instead of this exact,
                    # more specific, contract-mandated reason code.
                    self._persist(record, "BASKET_CONFIRMATION_REJECTED", {"reason_code": "BASKET_CONFIRMATION_ALREADY_ACCEPTED"})
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_ALREADY_ACCEPTED")
                if record["basket_status"] != "AWAITING_CONFIRMATION":
                    self._persist(record, "BASKET_CONFIRMATION_REJECTED", {"reason_code": "BASKET_CONFIRMATION_UNAVAILABLE"})
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_UNAVAILABLE")
                if self._now_dt() >= validate_utc_timestamp(active["expires_at_utc"]):
                    active["status"] = "EXPIRED"
                    active["expired_at_utc"] = self._now()
                    record["basket_status"] = "CHECK_COMPLETE"
                    self._persist(record, "BASKET_CONFIRMATION_EXPIRED", {
                        "confirmation_request_id": active["confirmation_request_id"],
                        "confirmation_cycle_number": active["confirmation_cycle_number"],
                    })
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_EXPIRED")
                if actor_channel != "LOCAL_OPERATOR":
                    self._persist(record, "BASKET_CONFIRMATION_REJECTED", {"reason_code": "BASKET_CONFIRMATION_CHANNEL_NOT_LOCAL"})
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_CHANNEL_NOT_LOCAL")

                # Defensive re-verification only — see contract Section
                # 13.4/13.3 step 6: normal progression can never make this
                # fire, since acceptance always precedes the first send.
                self._verify_fresh_or_recover(record)
                _basis_fields, basis_hash = self._build_confirmation_basis(record)
                if basis_hash != active["confirmation_basis_hash"]:
                    active["status"] = "INVALIDATED"
                    active["invalidated_at_utc"] = self._now()
                    active["invalidation_reason"] = "BASKET_CONFIRMATION_BASIS_CHANGED"
                    record["basket_status"] = "CHECK_COMPLETE"
                    self._persist(record, "BASKET_CONFIRMATION_INVALIDATED", {
                        "confirmation_request_id": active["confirmation_request_id"],
                        "confirmation_cycle_number": active["confirmation_cycle_number"],
                        "reason_code": "BASKET_CONFIRMATION_BASIS_CHANGED",
                    })
                    raise BasketExecutionServiceError("BASKET_CONFIRMATION_BASIS_CHANGED")

                active["status"] = "ACCEPTED"
                active["accepted_at_utc"] = self._now()
                record["basket_status"] = "CONFIRMED"
                self._persist(record, "BASKET_CONFIRMATION_ACCEPTED", {
                    "confirmation_request_id": active["confirmation_request_id"],
                    "confirmation_cycle_number": active["confirmation_cycle_number"],
                })
                return record
        except ExecutionJournalLockTimeout:
            raise BasketExecutionServiceError("BASKET_EXECUTION_LOCK_UNAVAILABLE")

    # -- sequential child send (Section 26) --------------------------------

    def send_basket_next(self, basket_id):
        self._require_capability("manual_basket_execution", "mt5_order_send", "manual_broker_execution")
        self._require_journal_integrity()

        try:
            with self._journal.acquire_creation_lock():
                record = self._load_basket_record(basket_id)
                if record is None:
                    raise BasketExecutionServiceError("BASKET_NOT_FOUND")
                if record["basket_status"] in bed.TERMINAL_BASKET_STATUSES:
                    raise BasketExecutionServiceError("BASKET_ALREADY_TERMINAL")
                if record["basket_status"] not in ("CONFIRMED", "SENDING"):
                    raise BasketExecutionServiceError("BASKET_CHILD_NOT_NEXT_ELIGIBLE")
                self._check_basket_expiry(record)
                self._verify_fresh_or_recover(record)

                active = self._active_cycle(record)
                next_child_id = self._compute_live_next_eligible(record, active)
                child = record["children"][next_child_id]

                configured_fingerprint = self._fingerprint_hash()
                if configured_fingerprint is None or configured_fingerprint != record["plan"]["account_fingerprint_hash"]:
                    raise BasketExecutionServiceError("ACCOUNT_FINGERPRINT_MISMATCH")
                account = self._adapter.account_status()
                if not account.get("available"):
                    raise BasketExecutionServiceError("ACCOUNT_UNAVAILABLE")
                symbol = self._adapter.symbol_status(record["plan"]["broker_native_instrument"])
                if not symbol.get("available") or not symbol.get("tradeable"):
                    raise BasketExecutionServiceError("SYMBOL_UNAVAILABLE")
                bid, ask = symbol.get("bid"), symbol.get("ask")
                if bid is None or ask is None:
                    raise BasketExecutionServiceError("TICK_UNAVAILABLE")

                child["execution_state"] = "SEND_RESERVED"
                child["send_result"] = {
                    "schema_version": bed.BASKET_CHILD_EXECUTION_RESULT_SCHEMA,
                    "basket_id": basket_id, "basket_child_id": next_child_id,
                    "canonical_basket_child_hash_at_send": child["intent"]["canonical_basket_child_hash"],
                    "send_reserved_at_utc": self._now(),
                    "send_outcome": None, "broker_response_hash": None, "filled_quantity": None,
                    "broker_order_ticket": None, "broker_deal_ticket": None,
                    "broker_position_ticket": None, "result_recorded_at_utc": None,
                }
                record["basket_status"] = "SENDING"
                self._persist(record, "BASKET_CHILD_SEND_RESERVED", {"basket_child_id": next_child_id})
                request = _order_request_for_child(child["intent"], record["parent_intent_snapshot"])
        except ExecutionJournalLockTimeout:
            raise BasketExecutionServiceError("BASKET_EXECUTION_LOCK_UNAVAILABLE")

        result = self._adapter.order_send(request)
        return self._finalize_send(basket_id, next_child_id, result)

    def _finalize_send(self, basket_id, basket_child_id, result):
        record = self._load_basket_record(basket_id)
        child = record["children"][basket_child_id]
        if not isinstance(result, dict) or result.get("outcome") not in med.SEND_OUTCOMES:
            result = {"outcome": "MALFORMED", "comment": "malformed broker response"}
        outcome = result["outcome"]
        requested = decimal_value(child["intent"]["child_quantity"])
        filled_value = None
        if outcome in ("FILLED", "PARTIALLY_FILLED"):
            filled = result.get("volume_filled")
            filled_value = decimal_value(filled) if filled is not None else None
            if filled_value is None or filled_value <= 0 or filled_value > requested:
                outcome = "MALFORMED"

        send_result = child["send_result"]
        send_result["result_recorded_at_utc"] = self._now()
        send_result["broker_response_hash"] = _request_hash(result)

        prior_filled = any(
            c["execution_state"] == "FILLED" and cid != basket_child_id
            for cid, c in record["children"].items()
        )

        if outcome == "FILLED" and filled_value == requested:
            child["execution_state"] = "FILLED"
            send_result["send_outcome"] = "FILLED"
            send_result["filled_quantity"] = child["intent"]["child_quantity"]
            send_result["broker_order_ticket"] = str(result.get("ticket")) if result.get("ticket") is not None else None
            all_filled = all(c["execution_state"] == "FILLED" for c in record["children"].values())
            if all_filled:
                record["basket_status"] = "COMPLETED"
                self._persist(record, "BASKET_CHILD_SEND_RESULT", {"basket_child_id": basket_child_id, "outcome": "FILLED"})
                self._persist(record, "BASKET_COMPLETED")
            else:
                record["basket_status"] = "SENDING"
                self._persist(record, "BASKET_CHILD_SEND_RESULT", {"basket_child_id": basket_child_id, "outcome": "FILLED"})
        elif outcome in ("FILLED", "PARTIALLY_FILLED"):
            # Founder correction round (2026-08-01-020), Section 6: a
            # partial fill freezes the basket (basket_status -> FROZEN,
            # never PARTIALLY_COMPLETED) regardless of whether any earlier
            # child already reached FILLED. PARTIALLY_COMPLETED is reserved
            # exclusively for a definitive, no-uncertainty-remaining later
            # rejection/failure after >=1 prior FILLED child (Section 27) —
            # a broker-confirmed partial fill is never that; it always
            # requires the same reconciliation-required freeze a broker
            # uncertain/malformed result already requires (Section 29).
            child["execution_state"] = "PARTIALLY_FILLED"
            send_result["send_outcome"] = "PARTIALLY_FILLED"
            send_result["filled_quantity"] = canonical_decimal(filled_value) if filled_value is not None else None
            send_result["broker_order_ticket"] = str(result.get("ticket")) if result.get("ticket") is not None else None
            record["basket_status"] = "FROZEN"
            record["terminal_reason"] = "BASKET_CHILD_SEND_PARTIALLY_FILLED"
            record["rejection_reasons"].append("BASKET_CHILD_SEND_PARTIALLY_FILLED")
            self._invalidate_active_cycle(record, "BASKET_CHILD_SEND_PARTIALLY_FILLED")
            self._persist(record, "BASKET_CHILD_SEND_RESULT", {"basket_child_id": basket_child_id, "outcome": "PARTIALLY_FILLED"})
            self._persist(record, "BASKET_CHILD_PARTIAL", {"basket_child_id": basket_child_id})
            self._persist(record, "BASKET_FROZEN")
            self._persist(record, "BASKET_RECONCILIATION_REQUIRED")
        elif outcome == "REJECTED":
            child["execution_state"] = "REJECTED"
            send_result["send_outcome"] = "REJECTED"
            new_status = "PARTIALLY_COMPLETED" if prior_filled else "FAILED"
            record["basket_status"] = new_status
            record["terminal_reason"] = "BASKET_CHILD_SEND_REJECTED"
            record["rejection_reasons"].append("BASKET_CHILD_SEND_REJECTED")
            self._invalidate_active_cycle(record, "BASKET_CHILD_SEND_REJECTED")
            self._persist(record, "BASKET_CHILD_SEND_RESULT", {"basket_child_id": basket_child_id, "outcome": "REJECTED"})
            self._persist(record, "BASKET_PARTIALLY_COMPLETED" if new_status == "PARTIALLY_COMPLETED" else "BASKET_FAILED")
        else:  # UNCERTAIN / MALFORMED
            child["execution_state"] = "FROZEN_PENDING_RECONCILIATION"
            send_result["send_outcome"] = outcome
            record["basket_status"] = "FROZEN"
            record["terminal_reason"] = "BASKET_FROZEN"
            record["rejection_reasons"].append("BASKET_FROZEN")
            self._invalidate_active_cycle(record, "BASKET_FROZEN")
            self._persist(record, "BASKET_CHILD_SEND_RESULT", {"basket_child_id": basket_child_id, "outcome": outcome})
            self._persist(record, "BASKET_CHILD_UNCERTAIN", {"basket_child_id": basket_child_id})
            self._persist(record, "BASKET_FROZEN")
            self._persist(record, "BASKET_RECONCILIATION_REQUIRED")

        return record

    def _invalidate_active_cycle(self, record, reason_code):
        active = self._active_cycle(record)
        if active is not None and active["status"] in ("REQUESTED", "ACCEPTED"):
            active["status"] = "INVALIDATED"
            active["invalidated_at_utc"] = self._now()
            active["invalidation_reason"] = reason_code if reason_code in bed.BASKET_REASON_CODES else "BASKET_FROZEN"

    def shutdown(self):
        return True


def in_memory_basket_service(mode_service=None, adapter=None, account_fingerprint=None, journal=None, clock=None):
    from . import mt5_execution_adapter as adapter_module
    from .mt5_execution_journal import in_memory_journal_writer
    return BasketExecutionService(
        adapter=adapter if adapter is not None else adapter_module.fake_adapter(clock=clock),
        mode_service=mode_service,
        journal=journal if journal is not None else in_memory_journal_writer(clock=clock),
        account_fingerprint=account_fingerprint,
        clock=clock,
    )


__all__ = (
    "BasketExecutionService",
    "BasketExecutionServiceError",
    "DisabledBasketExecutionService",
    "disabled_basket_service",
    "in_memory_basket_service",
)
