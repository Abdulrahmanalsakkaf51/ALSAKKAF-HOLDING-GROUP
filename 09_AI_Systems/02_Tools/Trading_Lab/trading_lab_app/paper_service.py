"""Forward-only deterministic paper account and position projection."""

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path

from .paper_data import (
    PAPER_ACCOUNT_SCHEMA,
    PAPER_HEALTH_SCHEMA,
    PAPER_HISTORY_SCHEMA,
    PAPER_ONLY_STATUS,
    PAPER_POSITION_SCHEMA,
    PAPER_POSITIONS_SCHEMA,
    INSTRUMENT_METADATA_SCHEMA,
    MARKET_OBSERVATION_SCHEMA,
    PaperConfiguration,
    PaperValidationError,
    build_proposal,
    canonical_decimal,
    decimal_value,
    quantity_floor,
    validate_market_observation,
    validate_proposal,
)
from .paper_store import (
    InMemoryPaperStore,
    LocalPaperStore,
    PaperStorageError,
    PaperStorageValidationError,
    storage_document,
)
from .timeline_data import (
    GENESIS_HASH,
    MarketTimeline,
    TimelineValidationError,
    format_utc,
    sha256_text,
    deterministic_json_text,
    validate_utc_timestamp,
)


PAPER_SERVICE_SCHEMA = "TRL_FORWARD_PAPER_SERVICE.v1"
PAPER_TIMELINE_API_SCHEMA = "TRL_MARKET_TIMELINE_API.v1"
MAX_API_TIMELINE_EVENTS = 200
MAX_API_HISTORY_ITEMS = 200
ENGINE_BASIS = "TRL-R2-005_FORWARD_PAPER_ENGINE"


class PaperEngineError(RuntimeError):
    """A controlled fail-closed engine condition."""


class PaperRiskRejection(PaperEngineError):
    """A governed paper-risk rejection, never a broker rejection."""


def _d(value):
    return decimal_value(value)


def _s(value):
    return canonical_decimal(value)


def _stable_id(prefix, *parts):
    material = "\n".join(str(part) for part in parts)
    return prefix + sha256_text(material)[:32]


def _disabled_account_document():
    return {
        "schema_version": PAPER_ACCOUNT_SCHEMA,
        "projection_id": None,
        "enabled": False,
        "paper_only_status": PAPER_ONLY_STATUS,
        "synthetic_demonstration_values": False,
        "starting_cash_basis": None,
        "starting_cash": None,
        "cash": None,
        "marked_equity": None,
        "realized_pnl": None,
        "unrealized_pnl": None,
        "closed_pnl": None,
        "fees": None,
        "modeled_slippage": None,
        "peak_equity": None,
        "current_drawdown": None,
        "current_drawdown_percent": None,
        "daily_paper_pnl": None,
        "open_paper_risk_amount": None,
        "open_position_count": 0,
        "completed_paper_trade_count": 0,
        "session_start_at_utc": None,
        "last_observation_at_utc": None,
        "risk_halt": False,
        "risk_halt_reason": None,
        "message": (
            "The paper engine is disabled by default. Start with "
            "--enable-forward-paper-engine for a local research timeline, or "
            "--enable-forward-paper-demo for a SYNTHETIC DEMONSTRATION (in-memory, "
            "not live market data)."
        ),
    }


class DisabledPaperService:
    """Explicit network-silent default that constructs no store."""

    enabled = False
    operational = False
    store = None

    def account_document(self):
        return _disabled_account_document()

    def positions_document(self):
        return {
            "schema_version": PAPER_POSITIONS_SCHEMA,
            "projection_id": None,
            "enabled": False,
            "paper_only_status": PAPER_ONLY_STATUS,
            "position_count": 0,
            "positions": [],
            "message": _disabled_account_document()["message"],
        }

    def history_document(self):
        return {
            "schema_version": PAPER_HISTORY_SCHEMA,
            "projection_id": None,
            "enabled": False,
            "paper_only_status": PAPER_ONLY_STATUS,
            "history_count": 0,
            "history": [],
        }

    def timeline_document(self):
        return {
            "schema_version": PAPER_TIMELINE_API_SCHEMA,
            "timeline_schema_version": "TRL_MARKET_TIMELINE.v1",
            "enabled": False,
            "timeline_id": None,
            "event_count": 0,
            "tail_event_hash": GENESIS_HASH,
            "response_truncated": False,
            "events": [],
        }

    def health_document(self):
        return {
            "schema_version": PAPER_HEALTH_SCHEMA,
            "enabled": False,
            "enabled_by_default": False,
            "operational": False,
            "paper_only_status": PAPER_ONLY_STATUS,
            "signal_generation": False,
            "trade_recommendation": False,
            "broker_execution": False,
            "real_orders": False,
            "account_mutation": False,
            "automated_trading": False,
            "storage_constructed": False,
            "persistence_status": "DISABLED",
            "persistence_failure_count": 0,
            "startup_diagnostic_code": "PAPER_ENGINE_DISABLED",
            "last_market_observation_status": "NONE",
            "risk_halt": False,
            "risk_halt_reason": None,
        }

    def shutdown(self):
        return True


def disabled_service():
    return DisabledPaperService()


class ForwardPaperService:
    """Event-sourced paper engine with no order or account authority."""

    enabled = True

    def __init__(self, store=None, configuration=None, session_started_at_utc=None):
        self.configuration = configuration or PaperConfiguration()
        self.store = store if store is not None else LocalPaperStore()
        self._timeline = None
        self._proposals = {}
        self._positions = {}
        self._account = None
        self._history = []
        self._shutdown = False
        self.operational = True
        self.persistence_status = "OK"
        self.persistence_failure_count = 0
        self.startup_diagnostic_code = "OK"
        self.last_market_observation_status = "NONE"
        self.is_synthetic_demonstration = False
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
                self._rebuild()
                self._persist()
            else:
                if loaded["settings"] != self.configuration.document():
                    raise PaperStorageValidationError("paper storage settings mismatch")
                self._timeline = MarketTimeline.from_document(loaded["timeline"])
                self._rebuild()
        except PaperStorageValidationError:
            self.operational = False
            self.startup_diagnostic_code = "INVALID_PAPER_STORAGE"
            self.persistence_status = "LOAD_VALIDATION_FAILED"
        except PaperStorageError:
            self.operational = False
            self.startup_diagnostic_code = "PAPER_STORAGE_READ_FAILED"
            self.persistence_status = "LOAD_FAILED"

    @property
    def timeline(self):
        return self._timeline

    def _require_operational(self):
        if not self.operational or self._timeline is None:
            raise PaperEngineError("paper engine is fail-closed")

    def _persist(self):
        if self._timeline is None:
            return
        document = storage_document(self.configuration.document(), self._timeline)
        try:
            self.store.save(document)
        except PaperStorageError:
            self.persistence_status = "WRITE_FAILED_IN_MEMORY_VALID"
            self.persistence_failure_count += 1
        else:
            self.persistence_status = "OK"

    def _append(self, category, instrument, occurred, observed, payload):
        self._require_operational()
        try:
            event = self._timeline.append(
                category,
                instrument,
                occurred,
                observed,
                ENGINE_BASIS,
                payload,
            )
        except TimelineValidationError as error:
            raise PaperEngineError(str(error)) from error
        self._rebuild()
        self._persist()
        return event

    def _empty_projection(self):
        starting = self.configuration.starting_cash
        return {
            "starting_cash": starting,
            "cash": starting,
            "realized": Decimal("0"),
            "closed": Decimal("0"),
            "fees": Decimal("0"),
            "slippage": Decimal("0"),
            "peak": starting,
            "session_start": None,
            "last_observation": None,
            "risk_halt": False,
            "risk_halt_reason": None,
        }

    @staticmethod
    def _position_unrealized(position):
        if position["status"] != "OPEN":
            return Decimal("0")
        remaining = _d(position["remaining_quantity"])
        entry = _d(position["entry_price"])
        mark = _d(position["mark_price"])
        value_per_price = _d(position["value_per_price_unit"])
        direction = Decimal("1") if position["side"] == "BUY" else Decimal("-1")
        return (mark - entry) * direction * remaining * value_per_price

    def _rebuild(self):
        if self._timeline is None:
            return
        proposals = {}
        positions = {}
        history = []
        projection = self._empty_projection()
        for event in self._timeline.events:
            payload = event["payload"]
            category = event["event_category"]
            if category == "PAPER_SESSION_EVENT":
                event_type = payload["event_type"]
                if event_type == "SESSION_STARTED":
                    projection["session_start"] = payload["session_started_at_utc"]
                elif event_type == "RISK_HALT":
                    projection["risk_halt"] = True
                    projection["risk_halt_reason"] = payload["reason_code"]
                elif event_type == "PROPOSAL_EXPIRED":
                    proposal = proposals.get(payload["proposal_id"])
                    if proposal is not None and proposal["status"] == "PENDING":
                        proposal["status"] = "EXPIRED"
            elif category == "MARKET_OBSERVATION":
                projection["last_observation"] = event["first_observed_at_utc"]
            elif category == "PAPER_PROPOSAL":
                proposal = deepcopy(payload["proposal"])
                proposals[proposal["proposal_id"]] = {
                    "proposal": proposal,
                    "proposal_event_id": event["timeline_event_id"],
                    "proposal_append_sequence": event["append_sequence"],
                    "status": "WAIT" if proposal["side"] == "WAIT" else "PENDING",
                    "rejection_reason": None,
                    "position_id": None,
                }
            elif category == "PAPER_RISK_REJECTION":
                proposal = proposals.get(payload["proposal_id"])
                if proposal is not None:
                    proposal["status"] = "REJECTED"
                    proposal["rejection_reason"] = payload["reason_code"]
                history.append(deepcopy(payload))
            elif category == "PAPER_ENTRY":
                position = deepcopy(payload["position"])
                positions[position["position_id"]] = position
                proposal = proposals[position["proposal_id"]]
                proposal["status"] = "FILLED"
                proposal["position_id"] = position["position_id"]
                entry_fee = _d(position["entry_fee"])
                projection["cash"] -= entry_fee
                projection["fees"] += entry_fee
                projection["slippage"] += _d(position["entry_slippage_amount"])
                history.append({
                    "history_type": "PAPER_ENTRY",
                    "position_id": position["position_id"],
                    "proposal_id": position["proposal_id"],
                    "at_utc": position["opened_at_utc"],
                    "quantity": position["initial_quantity"],
                    "price": position["entry_price"],
                })
            elif category == "PAPER_MARK":
                position = positions.get(payload["position_id"])
                if position is not None and position["status"] == "OPEN":
                    position["mark_price"] = payload["mark_price"]
                    position["last_mark_at_utc"] = event["first_observed_at_utc"]
            elif category in ("PAPER_TP", "PAPER_STOP"):
                position = positions[payload["position_id"]]
                quantity = _d(payload["quantity"])
                remaining = _d(position["remaining_quantity"]) - quantity
                if remaining < 0:
                    raise PaperEngineError("paper exit exceeds remaining quantity")
                position["remaining_quantity"] = _s(remaining)
                position["realized_pnl"] = _s(
                    _d(position["realized_pnl"]) + _d(payload["net_pnl"])
                )
                position["fees"] = _s(_d(position["fees"]) + _d(payload["exit_fee"]))
                position["modeled_slippage"] = _s(
                    _d(position["modeled_slippage"]) + _d(payload["slippage_amount"])
                )
                position["mark_price"] = payload["exit_price"]
                position["exits"].append(deepcopy(payload))
                if category == "PAPER_TP":
                    position["next_target_number"] = payload["target_number"] + 1
                projection["cash"] += _d(payload["gross_pnl"]) - _d(payload["exit_fee"])
                projection["realized"] += _d(payload["net_pnl"])
                projection["fees"] += _d(payload["exit_fee"])
                projection["slippage"] += _d(payload["slippage_amount"])
                history.append(deepcopy(payload))
                if remaining == 0:
                    position["status"] = "CLOSED"
                    position["closed_at_utc"] = event["first_observed_at_utc"]
                    projection["closed"] += _d(position["realized_pnl"])
            elif category == "PAPER_EXIT":
                history.append(deepcopy(payload))
            unrealized = sum(
                (self._position_unrealized(item) for item in positions.values()),
                Decimal("0"),
            )
            equity = projection["cash"] + unrealized
            if equity > projection["peak"]:
                projection["peak"] = equity
        unrealized = sum(
            (self._position_unrealized(item) for item in positions.values()),
            Decimal("0"),
        )
        equity = projection["cash"] + unrealized
        drawdown = max(Decimal("0"), projection["peak"] - equity)
        open_risk = Decimal("0")
        for position in positions.values():
            if position["status"] == "OPEN":
                initial = _d(position["initial_quantity"])
                remaining = _d(position["remaining_quantity"])
                open_risk += _d(position["initial_risk_amount"]) * remaining / initial
        tail = self._timeline.tail_hash
        projection_id = _stable_id(
            "pap_", PAPER_SERVICE_SCHEMA, tail, deterministic_json_text(self.configuration.document())
        )
        self._proposals = proposals
        self._positions = positions
        self._history = history
        self._account = {
            "schema_version": PAPER_ACCOUNT_SCHEMA,
            "projection_id": projection_id,
            "enabled": True,
            "paper_only_status": PAPER_ONLY_STATUS,
            "synthetic_demonstration_values": False,
            "starting_cash_basis": "SYNTHETIC_RESEARCH_DEFAULT_NOT_BROKER_BALANCE",
            "starting_cash": _s(projection["starting_cash"]),
            "cash": _s(projection["cash"]),
            "marked_equity": _s(equity),
            "realized_pnl": _s(projection["realized"]),
            "unrealized_pnl": _s(unrealized),
            "closed_pnl": _s(projection["closed"]),
            "fees": _s(projection["fees"]),
            "modeled_slippage": _s(projection["slippage"]),
            "peak_equity": _s(projection["peak"]),
            "current_drawdown": _s(drawdown),
            "current_drawdown_percent": _s(
                Decimal("0") if projection["peak"] == 0 else drawdown * 100 / projection["peak"]
            ),
            "daily_paper_pnl": _s(equity - projection["starting_cash"]),
            "open_paper_risk_amount": _s(open_risk),
            "open_position_count": sum(
                item["status"] == "OPEN" for item in positions.values()
            ),
            "completed_paper_trade_count": sum(
                item["status"] == "CLOSED" for item in positions.values()
            ),
            "session_start_at_utc": projection["session_start"],
            "last_observation_at_utc": projection["last_observation"],
            "risk_halt": projection["risk_halt"],
            "risk_halt_reason": projection["risk_halt_reason"],
            "message": (
                "No active paper proposal yet. Market research proposals will appear here "
                "when the Signal Desk is enabled."
                if not proposals else "Paper projections use governed forward observations only."
            ),
        }

    def _event_by_id(self, event_id):
        for event in self._timeline.events:
            if event["timeline_event_id"] == event_id:
                return event
        return None

    def append_market_observation(
        self,
        instrument,
        occurred_at_utc,
        first_observed_at_utc,
        payload,
        governed_source_basis="GOVERNED_LOCAL_MARKET_OBSERVATION",
    ):
        self._require_operational()
        try:
            clean_payload = validate_market_observation(payload, instrument)
            occurred = validate_utc_timestamp(occurred_at_utc, "occurred_at_utc")
            observed = validate_utc_timestamp(first_observed_at_utc, "first_observed_at_utc")
            metadata_observed = validate_utc_timestamp(
                clean_payload["metadata_observed_at_utc"], "metadata_observed_at_utc"
            )
        except (PaperValidationError, TimelineValidationError) as error:
            raise PaperEngineError(str(error)) from error
        event = self._timeline.append(
            "MARKET_OBSERVATION",
            instrument,
            occurred_at_utc,
            first_observed_at_utc,
            governed_source_basis,
            clean_payload,
        )
        self._rebuild()
        self._persist()
        age_seconds = Decimal(str((observed - occurred).total_seconds()))
        metadata_age = Decimal(str((observed - metadata_observed).total_seconds()))
        maximum_age = Decimal(self.configuration.maximum_observation_age_seconds)
        if metadata_observed > observed or age_seconds > maximum_age or metadata_age > maximum_age:
            self.last_market_observation_status = "STALE_REJECTED"
            return {"market_event": event, "actions": [], "status": "STALE_REJECTED"}
        self.last_market_observation_status = "ACCEPTED"
        actions = self._process_forward_observation(event, clean_payload)
        self._evaluate_risk_halt(first_observed_at_utc)
        return {"market_event": event, "actions": actions, "status": "ACCEPTED"}

    def submit_proposal(self, proposal):
        self._require_operational()
        try:
            clean = validate_proposal(proposal)
        except PaperValidationError as error:
            raise PaperEngineError(str(error)) from error
        evidence = self._event_by_id(clean["market_data_observation_id"])
        if evidence is None or evidence["event_category"] != "MARKET_OBSERVATION":
            raise PaperEngineError("proposal market evidence is missing")
        if evidence["instrument"] != clean["instrument"]:
            raise PaperEngineError("proposal market evidence instrument mismatch")
        if evidence["first_observed_at_utc"] > clean["created_at_utc"]:
            raise PaperEngineError("proposal market evidence is from the future")
        for event_id in clean["news_observation_ids"]:
            event = self._event_by_id(event_id)
            if event is None or event["event_category"] != "OFFICIAL_NEWS_OBSERVATION":
                raise PaperEngineError("proposal governed news evidence is missing")
            if event["first_observed_at_utc"] > clean["created_at_utc"]:
                raise PaperEngineError("proposal news evidence is from the future")
        for event_id in clean["economic_event_observation_ids"]:
            event = self._event_by_id(event_id)
            if event is None or event["event_category"] != "ECONOMIC_EVENT_OBSERVATION":
                raise PaperEngineError("proposal governed event evidence is missing")
            if event["first_observed_at_utc"] > clean["created_at_utc"]:
                raise PaperEngineError("proposal event evidence is from the future")
        proposal_event = self._append(
            "PAPER_PROPOSAL",
            clean["instrument"],
            clean["created_at_utc"],
            clean["observed_at_utc"],
            {"proposal": clean, "confidence_interpretation": "RESEARCH_SCORE_NOT_PROBABILITY"},
        )
        if clean["side"] == "WAIT":
            return {"proposal_event": proposal_event, "status": "WAIT"}
        reason = self._proposal_risk_rejection_reason(clean)
        if reason is not None:
            rejection = self._append_rejection(clean, reason, clean["observed_at_utc"], None)
            return {
                "proposal_event": proposal_event,
                "rejection_event": rejection,
                "status": "REJECTED",
                "reason_code": reason,
            }
        return {"proposal_event": proposal_event, "status": "PENDING"}

    def _proposal_risk_rejection_reason(self, proposal):
        if _d(proposal["risk_percent"]) > self.configuration.maximum_risk_percent:
            return "PROPOSAL_RISK_EXCEEDS_GOVERNED_MAXIMUM"
        if self._account["risk_halt"]:
            return "PAPER_SESSION_RISK_HALT"
        if any(
            position["status"] == "OPEN" and position["instrument"] == proposal["instrument"]
            for position in self._positions.values()
        ):
            return "ONE_OPEN_POSITION_PER_INSTRUMENT"
        closed = [item for item in self._positions.values() if item["status"] == "CLOSED"]
        entered = [
            item for item in self._positions.values()
            if item["status"] in ("OPEN", "CLOSED")
        ]
        if closed and entered:
            latest_closed = max(closed, key=lambda item: item["closed_at_utc"])
            latest_entered = max(entered, key=lambda item: item["opened_at_utc"])
            if _d(latest_closed["realized_pnl"]) < 0:
                prior = _d(latest_entered["risk_percent"])
                if _d(proposal["risk_percent"]) > prior:
                    return "RISK_INCREASE_AFTER_LOSS_FORBIDDEN"
        return None

    def _append_rejection(self, proposal, reason, observed_at, observation_id):
        return self._append(
            "PAPER_RISK_REJECTION",
            proposal["instrument"],
            observed_at,
            observed_at,
            {
                "history_type": "PAPER_RISK_REJECTION",
                "proposal_id": proposal["proposal_id"],
                "reason_code": reason,
                "market_observation_id": observation_id,
                "paper_only_status": PAPER_ONLY_STATUS,
            },
        )

    @staticmethod
    def _zone_reached(proposal, observation):
        lower = _d(proposal["entry_zone_lower"])
        upper = _d(proposal["entry_zone_upper"])
        side_suffix = "ask" if proposal["side"] == "BUY" else "bid"
        if observation["observation_kind"] == "QUOTE":
            price = _d(observation[side_suffix])
            return lower <= price <= upper, price
        low = _d(observation["low_" + side_suffix])
        high = _d(observation["high_" + side_suffix])
        if low <= upper and high >= lower:
            return True, upper if proposal["side"] == "BUY" else lower
        return False, None

    def _size_and_entry(self, proposal, observation, market_event):
        metadata = observation["instrument_metadata"]
        reached, basis_price = self._zone_reached(proposal, observation)
        if not reached:
            return None, None
        tick_size = _d(metadata["tick_size"])
        tick_value = _d(metadata["tick_value"])
        slippage = tick_size * self.configuration.slippage_ticks
        direction = Decimal("1") if proposal["side"] == "BUY" else Decimal("-1")
        entry_price = basis_price + direction * slippage
        stop = _d(proposal["stop_loss"])
        distance = abs(entry_price - stop)
        if distance <= 0 or tick_size <= 0 or tick_value <= 0:
            return None, "INVALID_CONTRACT_OR_STOP_DISTANCE"
        equity = _d(self._account["marked_equity"])
        risk_amount = equity * _d(proposal["risk_percent"]) / Decimal("100")
        value_per_price = tick_value / tick_size
        raw_quantity = risk_amount / (distance * value_per_price)
        quantity = quantity_floor(raw_quantity, metadata["quantity_step"])
        minimum = _d(metadata["minimum_quantity"])
        maximum = _d(metadata["maximum_quantity"])
        if quantity < minimum:
            return None, "RISK_SIZE_BELOW_MINIMUM_QUANTITY"
        quantity = min(quantity, maximum)
        actual_risk = quantity * distance * value_per_price
        fill_id = _stable_id(
            "pfl_", proposal["proposal_id"], market_event["timeline_event_id"], _s(entry_price)
        )
        position_id = _stable_id("ppos_", proposal["proposal_id"], fill_id)
        entry_fee = quantity * self.configuration.fee_per_quantity
        slippage_amount = slippage * quantity * value_per_price
        position = {
            "schema_version": PAPER_POSITION_SCHEMA,
            "position_id": position_id,
            "fill_id": fill_id,
            "proposal_id": proposal["proposal_id"],
            "instrument": proposal["instrument"],
            "side": proposal["side"],
            "status": "OPEN",
            "paper_only_status": PAPER_ONLY_STATUS,
            "opened_at_utc": market_event["first_observed_at_utc"],
            "closed_at_utc": None,
            "entry_market_observation_id": market_event["timeline_event_id"],
            "entry_price": _s(entry_price),
            "entry_basis_price": _s(basis_price),
            "entry_side": "ASK" if proposal["side"] == "BUY" else "BID",
            "entry_spread": observation["spread"],
            "entry_slippage_price": _s(slippage),
            "entry_slippage_amount": _s(slippage_amount),
            "entry_fee": _s(entry_fee),
            "initial_quantity": _s(quantity),
            "remaining_quantity": _s(quantity),
            "quantity_step": metadata["quantity_step"],
            "stop_loss": proposal["stop_loss"],
            "initial_stop_loss": proposal["stop_loss"],
            "targets": deepcopy(proposal["targets"]),
            "target_allocations_percent": deepcopy(proposal["target_allocations_percent"]),
            "next_target_number": 1,
            "risk_percent": proposal["risk_percent"],
            "initial_risk_amount": _s(actual_risk),
            "tick_size": metadata["tick_size"],
            "tick_value": metadata["tick_value"],
            "contract_size": metadata["contract_size"],
            "value_per_price_unit": _s(value_per_price),
            "quote_currency": metadata["quote_currency"],
            "mark_price": _s(entry_price),
            "last_mark_at_utc": market_event["first_observed_at_utc"],
            "realized_pnl": "0",
            "fees": _s(entry_fee),
            "modeled_slippage": _s(slippage_amount),
            "exits": [],
        }
        return position, None

    def _process_forward_observation(self, market_event, observation):
        actions = []
        for record in sorted(
            self._proposals.values(), key=lambda item: item["proposal_append_sequence"]
        ):
            if record["status"] != "PENDING":
                continue
            proposal = record["proposal"]
            observed_at = market_event["first_observed_at_utc"]
            if observed_at > proposal["expires_at_utc"]:
                expired = self._append(
                    "PAPER_SESSION_EVENT",
                    proposal["instrument"],
                    observed_at,
                    observed_at,
                    {
                        "event_type": "PROPOSAL_EXPIRED",
                        "proposal_id": proposal["proposal_id"],
                        "market_observation_id": market_event["timeline_event_id"],
                    },
                )
                actions.append(expired)
                continue
            if proposal["instrument"] != market_event["instrument"]:
                continue
            if market_event["append_sequence"] <= record["proposal_append_sequence"]:
                continue
            if market_event["occurred_at_utc"] <= proposal["created_at_utc"]:
                continue
            if market_event["timeline_event_id"] == proposal["market_data_observation_id"]:
                continue
            reason = self._proposal_risk_rejection_reason(proposal)
            if reason is not None:
                rejection = self._append_rejection(
                    proposal, reason, observed_at, market_event["timeline_event_id"]
                )
                actions.append(rejection)
                continue
            position, rejection_reason = self._size_and_entry(
                proposal, observation, market_event
            )
            if rejection_reason is not None:
                rejection = self._append_rejection(
                    proposal,
                    rejection_reason,
                    observed_at,
                    market_event["timeline_event_id"],
                )
                actions.append(rejection)
            elif position is not None:
                entry = self._append(
                    "PAPER_ENTRY",
                    proposal["instrument"],
                    observed_at,
                    observed_at,
                    {
                        "position": position,
                        "proposal_event_id": record["proposal_event_id"],
                        "market_observation_id": market_event["timeline_event_id"],
                        "forward_observation_only": True,
                    },
                )
                actions.append(entry)
        actions.extend(self._process_open_positions(market_event, observation))
        return actions

    @staticmethod
    def _exit_touches(position, observation):
        side = position["side"]
        if observation["observation_kind"] == "QUOTE":
            price = _d(observation["bid"] if side == "BUY" else observation["ask"])
            stop_touched = price <= _d(position["stop_loss"]) if side == "BUY" else price >= _d(position["stop_loss"])
            target_touched = []
            for index, target in enumerate(position["targets"], start=1):
                if index < position["next_target_number"]:
                    continue
                touched = price >= _d(target) if side == "BUY" else price <= _d(target)
                if touched:
                    target_touched.append(index)
            return stop_touched, target_touched, False
        adverse = _d(observation["low_bid"] if side == "BUY" else observation["high_ask"])
        favorable = _d(observation["high_bid"] if side == "BUY" else observation["low_ask"])
        stop_touched = adverse <= _d(position["stop_loss"]) if side == "BUY" else adverse >= _d(position["stop_loss"])
        target_touched = []
        for index, target in enumerate(position["targets"], start=1):
            if index < position["next_target_number"]:
                continue
            touched = favorable >= _d(target) if side == "BUY" else favorable <= _d(target)
            if touched:
                target_touched.append(index)
        return stop_touched, target_touched, stop_touched and bool(target_touched)

    def _exit_payload(
        self, position, market_event, kind, quantity, target_number=None, ambiguous=False
    ):
        base_price = (
            _d(position["stop_loss"])
            if kind == "STOP"
            else _d(position["targets"][target_number - 1])
        )
        tick_size = _d(position["tick_size"])
        slippage_price = tick_size * self.configuration.slippage_ticks
        direction = Decimal("-1") if position["side"] == "BUY" else Decimal("1")
        exit_price = base_price + direction * slippage_price
        pnl_direction = Decimal("1") if position["side"] == "BUY" else Decimal("-1")
        gross = (
            (exit_price - _d(position["entry_price"]))
            * pnl_direction
            * quantity
            * _d(position["value_per_price_unit"])
        )
        exit_fee = quantity * self.configuration.fee_per_quantity
        entry_fee_allocated = _d(position["entry_fee"]) * quantity / _d(position["initial_quantity"])
        net = gross - exit_fee - entry_fee_allocated
        slippage_amount = slippage_price * quantity * _d(position["value_per_price_unit"])
        exit_id = _stable_id(
            "pex_",
            position["position_id"],
            market_event["timeline_event_id"],
            kind,
            target_number or 0,
        )
        return {
            "history_type": "PAPER_{}".format("TP" if kind == "TP" else "STOP"),
            "exit_id": exit_id,
            "position_id": position["position_id"],
            "proposal_id": position["proposal_id"],
            "market_observation_id": market_event["timeline_event_id"],
            "at_utc": market_event["first_observed_at_utc"],
            "exit_kind": kind,
            "target_number": target_number,
            "quantity": _s(quantity),
            "exit_price": _s(exit_price),
            "exit_side": "BID" if position["side"] == "BUY" else "ASK",
            "gross_pnl": _s(gross),
            "exit_fee": _s(exit_fee),
            "allocated_entry_fee": _s(entry_fee_allocated),
            "net_pnl": _s(net),
            "slippage_price": _s(slippage_price),
            "slippage_amount": _s(slippage_amount),
            "ambiguous_intrabar": ambiguous,
            "ambiguity_resolution": (
                "CONSERVATIVE_STOP_FIRST_UNKNOWN_INTRABAR_ORDER"
                if ambiguous else "NOT_AMBIGUOUS"
            ),
            "paper_only_status": PAPER_ONLY_STATUS,
        }

    def _append_exit_summary(self, position_id, observed_at, reason, observation_id):
        position = self._positions[position_id]
        return self._append(
            "PAPER_EXIT",
            position["instrument"],
            observed_at,
            observed_at,
            {
                "history_type": "PAPER_EXIT",
                "position_id": position_id,
                "proposal_id": position["proposal_id"],
                "at_utc": observed_at,
                "close_reason": reason,
                "market_observation_id": observation_id,
                "realized_pnl": position["realized_pnl"],
                "paper_only_status": PAPER_ONLY_STATUS,
            },
        )

    def _process_open_positions(self, market_event, observation):
        actions = []
        open_ids = sorted(
            position_id
            for position_id, position in self._positions.items()
            if position["status"] == "OPEN"
            and position["instrument"] == market_event["instrument"]
        )
        for position_id in open_ids:
            position = self._positions[position_id]
            stop_touched, target_numbers, ambiguous = self._exit_touches(position, observation)
            if stop_touched:
                quantity = _d(position["remaining_quantity"])
                payload = self._exit_payload(
                    position, market_event, "STOP", quantity, ambiguous=ambiguous
                )
                stop_event = self._append(
                    "PAPER_STOP",
                    position["instrument"],
                    market_event["first_observed_at_utc"],
                    market_event["first_observed_at_utc"],
                    payload,
                )
                actions.append(stop_event)
                summary = self._append_exit_summary(
                    position_id,
                    market_event["first_observed_at_utc"],
                    "STOP_FIRST_AMBIGUOUS_BAR" if ambiguous else "INITIAL_STOP",
                    market_event["timeline_event_id"],
                )
                actions.append(summary)
                continue
            for target_number in target_numbers:
                position = self._positions[position_id]
                if position["status"] != "OPEN":
                    break
                if target_number != position["next_target_number"]:
                    break
                remaining = _d(position["remaining_quantity"])
                if target_number == 4:
                    quantity = remaining
                else:
                    allocation = _d(position["target_allocations_percent"][target_number - 1])
                    quantity = quantity_floor(
                        _d(position["initial_quantity"]) * allocation / Decimal("100"),
                        position["quantity_step"],
                    )
                    quantity = min(quantity, remaining)
                payload = self._exit_payload(
                    position, market_event, "TP", quantity, target_number=target_number
                )
                tp_event = self._append(
                    "PAPER_TP",
                    position["instrument"],
                    market_event["first_observed_at_utc"],
                    market_event["first_observed_at_utc"],
                    payload,
                )
                actions.append(tp_event)
                if self._positions[position_id]["status"] != "OPEN":
                    summary = self._append_exit_summary(
                        position_id,
                        market_event["first_observed_at_utc"],
                        "TP4_COMPLETE",
                        market_event["timeline_event_id"],
                    )
                    actions.append(summary)
            position = self._positions[position_id]
            if position["status"] == "OPEN":
                mark = (
                    observation["bid"] if position["side"] == "BUY" else observation["ask"]
                )
                if observation["observation_kind"] == "BAR":
                    mark = (
                        observation["close_bid"]
                        if position["side"] == "BUY" else observation["close_ask"]
                    )
                mark_event = self._append(
                    "PAPER_MARK",
                    position["instrument"],
                    market_event["first_observed_at_utc"],
                    market_event["first_observed_at_utc"],
                    {
                        "position_id": position_id,
                        "market_observation_id": market_event["timeline_event_id"],
                        "mark_price": mark,
                        "mark_side": "BID" if position["side"] == "BUY" else "ASK",
                    },
                )
                actions.append(mark_event)
        return actions

    def _evaluate_risk_halt(self, observed_at):
        if self._account["risk_halt"]:
            return None
        starting = _d(self._account["starting_cash"])
        daily_limit = starting * self.configuration.maximum_daily_loss_percent / Decimal("100")
        drawdown_limit = self.configuration.maximum_drawdown_percent
        reason = None
        if _d(self._account["daily_paper_pnl"]) <= -daily_limit:
            reason = "MAXIMUM_DAILY_PAPER_LOSS"
        elif _d(self._account["current_drawdown_percent"]) >= drawdown_limit:
            reason = "MAXIMUM_PAPER_ACCOUNT_DRAWDOWN"
        if reason is None:
            return None
        return self._append(
            "PAPER_SESSION_EVENT",
            None,
            observed_at,
            observed_at,
            {
                "event_type": "RISK_HALT",
                "reason_code": reason,
                "sticky_for_session": True,
            },
        )

    def account_document(self):
        if self._account is None:
            document = _disabled_account_document()
            document["enabled"] = True
            document["message"] = "Paper storage is invalid; the engine is fail-closed."
            return document
        document = deepcopy(self._account)
        document["synthetic_demonstration_values"] = self.is_synthetic_demonstration
        return document

    def positions_document(self):
        positions = [] if self._account is None else [
            deepcopy(item) for item in sorted(self._positions.values(), key=lambda row: row["position_id"])
            if item["status"] == "OPEN"
        ]
        return {
            "schema_version": PAPER_POSITIONS_SCHEMA,
            "projection_id": None if self._account is None else self._account["projection_id"],
            "enabled": True,
            "paper_only_status": PAPER_ONLY_STATUS,
            "position_count": len(positions),
            "positions": positions,
            "message": (
                "No active paper proposal yet. Market research proposals will appear here "
                "when the Signal Desk is enabled."
                if not positions else "Active positions are forward paper projections only."
            ),
        }

    def history_document(self):
        history = self._history[-MAX_API_HISTORY_ITEMS:] if self._account is not None else []
        return {
            "schema_version": PAPER_HISTORY_SCHEMA,
            "projection_id": None if self._account is None else self._account["projection_id"],
            "enabled": True,
            "paper_only_status": PAPER_ONLY_STATUS,
            "history_count": len(self._history) if self._account is not None else 0,
            "response_truncated": len(self._history) > len(history) if self._account is not None else False,
            "history": deepcopy(history),
        }

    def timeline_document(self):
        if self._timeline is None:
            document = disabled_service().timeline_document()
            document["enabled"] = True
            return document
        source = self._timeline.to_document()
        events = source["events"][-MAX_API_TIMELINE_EVENTS:]
        return {
            "schema_version": PAPER_TIMELINE_API_SCHEMA,
            "timeline_schema_version": source["schema_version"],
            "enabled": True,
            "timeline_id": source["timeline_id"],
            "event_count": source["event_count"],
            "tail_event_hash": source["tail_event_hash"],
            "response_truncated": source["event_count"] > len(events),
            "events": deepcopy(events),
        }

    def health_document(self):
        return {
            "schema_version": PAPER_HEALTH_SCHEMA,
            "enabled": True,
            "enabled_by_default": False,
            "operational": self.operational,
            "paper_only_status": PAPER_ONLY_STATUS,
            "signal_generation": False,
            "trade_recommendation": False,
            "broker_execution": False,
            "real_orders": False,
            "account_mutation": False,
            "automated_trading": False,
            "storage_constructed": True,
            "persistence_status": self.persistence_status,
            "persistence_failure_count": self.persistence_failure_count,
            "startup_diagnostic_code": self.startup_diagnostic_code,
            "last_market_observation_status": self.last_market_observation_status,
            "risk_halt": False if self._account is None else self._account["risk_halt"],
            "risk_halt_reason": None if self._account is None else self._account["risk_halt_reason"],
        }

    def shutdown(self):
        if self._shutdown:
            return True
        self._shutdown = True
        return self.store.shutdown()


def in_memory_service(configuration=None, session_started_at_utc=None):
    return ForwardPaperService(
        store=InMemoryPaperStore(),
        configuration=configuration,
        session_started_at_utc=session_started_at_utc,
    )


SYNTHETIC_DEMONSTRATION_PATH = (
    Path(__file__).resolve().parent / "synthetic_paper_demonstration.json"
)


def _synthetic_market_payload(operation, metadata):
    at_utc = operation["at_utc"]
    if operation["type"] == "QUOTE":
        bid = _d(operation["bid"])
        ask = _d(operation["ask"])
        return {
            "schema_version": MARKET_OBSERVATION_SCHEMA,
            "observation_kind": "QUOTE",
            "bid": _s(bid),
            "ask": _s(ask),
            "open_bid": None,
            "high_bid": None,
            "low_bid": None,
            "close_bid": None,
            "open_ask": None,
            "high_ask": None,
            "low_ask": None,
            "close_ask": None,
            "spread": _s(ask - bid),
            "instrument_metadata": deepcopy(metadata),
            "metadata_observed_at_utc": at_utc,
        }
    spread = _d(operation["spread"])
    return {
        "schema_version": MARKET_OBSERVATION_SCHEMA,
        "observation_kind": "BAR",
        "bid": operation["close_bid"],
        "ask": _s(_d(operation["close_bid"]) + spread),
        "open_bid": operation["open_bid"],
        "high_bid": operation["high_bid"],
        "low_bid": operation["low_bid"],
        "close_bid": operation["close_bid"],
        "open_ask": _s(_d(operation["open_bid"]) + spread),
        "high_ask": _s(_d(operation["high_bid"]) + spread),
        "low_ask": _s(_d(operation["low_bid"]) + spread),
        "close_ask": _s(_d(operation["close_bid"]) + spread),
        "spread": operation["spread"],
        "instrument_metadata": deepcopy(metadata),
        "metadata_observed_at_utc": at_utc,
    }


def _load_synthetic_demonstration_fixture():
    with SYNTHETIC_DEMONSTRATION_PATH.open("r", encoding="utf-8") as handle:
        fixture = json.load(handle)
    expected_label = "SYNTHETIC DEMONSTRATION — NOT LIVE MARKET DATA"
    if (
        fixture.get("schema_version") != "TRL_SYNTHETIC_FORWARD_PAPER_DEMO.v1"
        or fixture.get("label") != expected_label
        or fixture.get("synthetic") is not True
    ):
        raise PaperEngineError("synthetic paper demonstration fixture is invalid")
    metadata = fixture["instrument_metadata"]
    if metadata.get("schema_version") != INSTRUMENT_METADATA_SCHEMA:
        raise PaperEngineError("synthetic instrument metadata is invalid")
    return fixture, metadata, expected_label


def build_synthetic_demonstration_service():
    """Return a live in-memory engine pre-loaded with the committed synthetic
    fixture. Uses InMemoryPaperStore only; never touches production storage."""
    fixture, metadata, _ = _load_synthetic_demonstration_fixture()
    configuration = PaperConfiguration()
    engine = ForwardPaperService(
        store=InMemoryPaperStore(),
        configuration=configuration,
        session_started_at_utc=fixture["session_started_at_utc"],
    )
    _replay_synthetic_demonstration(engine, fixture, metadata)
    engine.is_synthetic_demonstration = True
    return engine


def _replay_synthetic_demonstration(engine, fixture, metadata):
    aliases = {}
    proposal_results = {}
    for operation in fixture["operations"]:
        operation_type = operation["type"]
        if operation_type in ("QUOTE", "BAR"):
            result = engine.append_market_observation(
                metadata["instrument"],
                operation["at_utc"],
                operation["at_utc"],
                _synthetic_market_payload(operation, metadata),
                governed_source_basis="SYNTHETIC_DEMONSTRATION_FIXTURE",
            )
            aliases[operation["alias"]] = result["market_event"]["timeline_event_id"]
            continue
        if operation_type != "PROPOSAL":
            raise PaperEngineError("synthetic fixture operation type is invalid")
        side = operation["side"]
        proposal = build_proposal(
            created_at_utc=operation["created_at_utc"],
            observed_at_utc=operation["created_at_utc"],
            expires_at_utc=operation["expires_at_utc"],
            instrument=metadata["instrument"],
            side=side,
            entry_type="WAIT" if side == "WAIT" else "ENTRY_ZONE",
            entry_zone_lower=operation["entry_zone_lower"],
            entry_zone_upper=operation["entry_zone_upper"],
            stop_loss=operation["stop_loss"],
            targets=operation["targets"],
            target_allocations_percent=operation["target_allocations_percent"],
            confidence_score=50,
            evidence_quality_status="GOVERNED",
            invalidation_reason="The governed synthetic setup conditions no longer hold.",
            wait_reason=operation["wait_reason"],
            beginner_explanation=(
                "This is a synthetic paper-only contract example, not live market data "
                "or a recommendation."
            ),
            strategy_basis_ids=["TRL-R2-005.SYNTHETIC-CONTRACT"],
            research_basis_ids=["SYNTHETIC.DEMONSTRATION"],
            market_data_observation_id=aliases[operation["evidence_alias"]],
            news_observation_ids=[],
            economic_event_observation_ids=[],
            risk_percent=operation["risk_percent"],
        )
        proposal_results[operation["alias"]] = engine.submit_proposal(proposal)
    return aliases, proposal_results


def run_synthetic_demonstration():
    """Run the committed offline fixture and prove deterministic restart recovery."""
    fixture, metadata, expected_label = _load_synthetic_demonstration_fixture()
    configuration = PaperConfiguration()
    store = InMemoryPaperStore()
    engine = ForwardPaperService(
        store=store,
        configuration=configuration,
        session_started_at_utc=fixture["session_started_at_utc"],
    )
    aliases, proposal_results = _replay_synthetic_demonstration(engine, fixture, metadata)
    before_account = engine.account_document()
    before_positions = deepcopy(engine._positions)
    before_timeline = engine.timeline_document()
    before_history = engine.history_document()
    restarted = ForwardPaperService(store=store, configuration=configuration)
    after_account = restarted.account_document()
    after_positions = deepcopy(restarted._positions)
    after_timeline = restarted.timeline_document()
    after_history = restarted.history_document()
    categories = [event["event_category"] for event in after_timeline["events"]]
    ambiguous = [
        item for item in after_history["history"]
        if item.get("ambiguous_intrabar") is True
    ]
    demonstration_account = deepcopy(after_account)
    demonstration_account["synthetic_demonstration_values"] = True
    return {
        "schema_version": "TRL_SYNTHETIC_FORWARD_PAPER_DEMO_RESULT.v1",
        "label": expected_label,
        "synthetic": True,
        "account": demonstration_account,
        "timeline_event_count": after_timeline["event_count"],
        "event_category_counts": {
            category: categories.count(category) for category in sorted(set(categories))
        },
        "wait_proposal_status": proposal_results["WAIT_EXAMPLE"]["status"],
        "buy_proposal_status": restarted._proposals[
            next(
                proposal_id for proposal_id, record in restarted._proposals.items()
                if record["proposal"]["side"] == "BUY"
                and record["status"] == "FILLED"
            )
        ]["status"],
        "sell_proposal_status": restarted._proposals[
            next(
                proposal_id for proposal_id, record in restarted._proposals.items()
                if record["proposal"]["side"] == "SELL"
            )
        ]["status"],
        "risk_rejected_status": proposal_results["RISK_REJECTED_EXAMPLE"]["status"],
        "ambiguous_stop_first_count": len(ambiguous),
        "ambiguous_resolution": (
            ambiguous[0]["ambiguity_resolution"] if ambiguous else None
        ),
        "restart_reconstruction_exact": (
            before_account == after_account
            and before_positions == after_positions
            and before_timeline == after_timeline
            and before_history == after_history
        ),
    }
