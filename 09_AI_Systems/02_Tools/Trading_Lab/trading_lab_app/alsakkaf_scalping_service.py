"""ALSAKKAF SCALPING orchestration service (TRL-R2-012, contract Sections
3, 6, 9, 11-14).

**Accelerated-V0 boundary decision (documented, not left implicit):** this
service accepts already-fetched closed bars/current price/spread as
arguments to ``analyze``/``run_cycle`` rather than fetching them itself --
the caller (CLI/HTTP/dashboard layer, ``app.py``/``server.py`` wiring) is
responsible for sourcing them from the live MT5 adapter or a validated
R2-011 replay snapshot (contract Section 10). This mirrors R2-010's own
service, which accepts one fully-formed input rather than deriving
evidence from raw candles itself, and keeps this module a pure,
deterministic decision/execution orchestrator that is trivial to test
with fixture bars.

Every mutating action here follows the exact Section 14.1 sequence: lock,
reload, uncertain-freeze check, fresh preflight, plan, ownership-tag,
order_check, order_send-at-most-once, persist, reconcile, release.
"""

from copy import deepcopy
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from . import alsakkaf_scalping_data as data
from . import alsakkaf_scalping_indicators as indicators  # noqa: F401 (re-exported for callers)
from . import alsakkaf_scalping_mt5 as mt5_adapter
from . import alsakkaf_scalping_risk as risk
from . import alsakkaf_scalping_strategy as strategy
from .alsakkaf_scalping_journal import ScalpingJournalLockTimeout
from .timeline_data import format_utc, validate_utc_timestamp


class ScalpingServiceError(RuntimeError):
    def __init__(self, reason_code, message=None):
        super().__init__(message or reason_code)
        self.reason_code = reason_code


CAPABILITY = "alsakkaf_scalping_demo_automation"

_TRANSITIONS = {
    "OFF": frozenset({"ANALYZE_ONLY", "DEMO_AUTO", "EMERGENCY_STOP"}),
    "ANALYZE_ONLY": frozenset({"OFF", "DEMO_AUTO", "EMERGENCY_STOP"}),
    "DEMO_AUTO": frozenset({"OFF", "ANALYZE_ONLY", "PAUSED", "EMERGENCY_STOP"}),
    "PAUSED": frozenset({"OFF", "ANALYZE_ONLY", "DEMO_AUTO", "EMERGENCY_STOP"}),
    "EMERGENCY_STOP": frozenset({"OFF"}),
}

DEFAULT_MAX_SPREAD_POINTS = 200
DEFAULT_MAX_CONSECUTIVE_LOSSES = risk.DEFAULT_MAX_CONSECUTIVE_LOSSES

_DECIMAL_RISK_SETTING_KEYS = frozenset((
    "risk_per_cycle_pct", "max_total_active_risk_pct",
    "max_daily_loss_pct", "max_session_drawdown_pct",
))


def _serialize_risk_settings(settings):
    return {
        key: (str(value) if key in _DECIMAL_RISK_SETTING_KEYS else int(value))
        for key, value in settings.items()
    }


def _deserialize_risk_settings(settings):
    result = {}
    for key, value in settings.items():
        if key in _DECIMAL_RISK_SETTING_KEYS:
            result[key] = Decimal(str(value))
        else:
            result[key] = int(value)
    return result


class ScalpingService:
    def __init__(
        self, journal=None, adapter=None, symbol_map_store=None,
        mode_service=None, market_intelligence_service=None, clock=None,
        scratch_directory=None, config_store=None,
    ):
        from .alsakkaf_scalping_journal import in_memory_journal_writer
        self._journal = journal if journal is not None else in_memory_journal_writer()
        self._adapter = adapter if adapter is not None else mt5_adapter.disabled_adapter()
        self._symbol_map_store = symbol_map_store if symbol_map_store is not None else data.InMemorySymbolMapStore()
        self._mode_service = mode_service
        self._mi_service = market_intelligence_service
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._scratch_directory = scratch_directory
        # TRL-R2-013 Section 8: profile/side/risk/spread/monitoring-interval
        # configuration is now durably persisted (previously process-memory
        # only, lost on every restart -- root cause 3 of the operational
        # hotfix contract).
        self._config_store = config_store if config_store is not None else data.InMemoryScalpingConfigStore()
        persisted = self._config_store.load()
        persisted_risk = _deserialize_risk_settings(persisted.get("risk_settings", {})) if persisted.get("risk_settings") else {}
        self._risk_settings = risk.validate_risk_settings(
            {**risk.default_risk_settings(), **persisted_risk}
        )
        self._max_spread_points = {instrument: DEFAULT_MAX_SPREAD_POINTS for instrument in data.CANONICAL_INSTRUMENTS}
        self._max_spread_points.update(persisted.get("max_spread_points", {}))
        self._profiles = dict(persisted.get("profiles", {}))
        self._side_restrictions = dict(persisted.get("side_restrictions", {}))
        self._monitoring_interval_seconds = persisted.get(
            "monitoring_interval_seconds", data.DEFAULT_MONITORING_INTERVAL_SECONDS,
        )
        self._start_of_day_equity = None
        self._peak_equity = None
        self._consecutive_losses = 0
        self._cooldown_until_utc = None
        self._last_symbol_cycle_at_utc = {}

    def _persist_config(self):
        self._config_store.save({
            "schema_version": data.CONFIG_SCHEMA,
            "profiles": dict(self._profiles),
            "side_restrictions": dict(self._side_restrictions),
            "max_spread_points": dict(self._max_spread_points),
            "risk_settings": _serialize_risk_settings(self._risk_settings),
            "monitoring_interval_seconds": self._monitoring_interval_seconds,
        })

    def _require_non_demo_auto_for_config(self):
        if self.current_state == "DEMO_AUTO":
            raise ScalpingServiceError("SCALPING_CONFIG_REQUIRES_NON_AUTO_STATE")

    def _now(self):
        return format_utc(self._clock())

    def _now_dt(self):
        return validate_utc_timestamp(self._now())

    # ------------------------------------------------------------------
    # Product state (event-sourced, mirrors ModeService's design)
    # ------------------------------------------------------------------

    @property
    def current_state(self):
        state = "OFF"
        for event in self._journal.events:
            if event["event_type"] == "SCALPING_STATE_CHANGED":
                state = event["payload"]["to_state"]
        return state

    @property
    def is_emergency_stopped(self):
        return self.current_state == "EMERGENCY_STOP"

    def _has_capability(self):
        if self._mode_service is None:
            return False
        try:
            return self._mode_service.has_capability(CAPABILITY)
        except AttributeError:
            return CAPABILITY in self._mode_service.capabilities_for(self._mode_service.current_mode)

    def request_state_change(self, target_state, reason=""):
        data._require_choice(target_state, data.PRODUCT_STATES, "target_state")
        current = self.current_state
        if target_state not in _TRANSITIONS.get(current, frozenset()):
            raise ScalpingServiceError(
                "SCALPING_INVALID_TRANSITION",
                "cannot transition from {} to {}".format(current, target_state),
            )
        if target_state == "DEMO_AUTO":
            if not self._has_capability():
                raise ScalpingServiceError(
                    "SCALPING_DEMO_AUTO_REQUIRES_MODE",
                    "MT5_DEMO_AUTOMATED / alsakkaf_scalping_demo_automation is not granted",
                )
            preflight = self.run_preflight_for_any_mapped_symbol()
            if not preflight["passed"]:
                raise ScalpingServiceError(
                    "SCALPING_DEMO_AUTO_PREFLIGHT_FAILED", preflight["blocking_reason_code"],
                )
        with self._journal.acquire_mutation_lock() as writer:
            writer.append("SCALPING_STATE_CHANGED", {
                "from_state": current, "to_state": target_state, "reason": reason[:256],
            }, occurred_at_utc=self._now())
        if target_state == "EMERGENCY_STOP":
            self._execute_emergency_stop()
        return target_state

    def run_preflight_for_any_mapped_symbol(self):
        mapping = self._symbol_map_store.load()["mappings"]
        if not mapping:
            return {"passed": False, "blocking_reason_code": "SCALPING_SYMBOL_MAP_EMPTY", "checks": []}
        instrument = sorted(mapping)[0]
        return self.run_preflight(instrument)

    # ------------------------------------------------------------------
    # Symbol discovery and mapping (Section 7)
    # ------------------------------------------------------------------

    def discover_symbols(self, canonical_instrument):
        data.validate_canonical_instrument(canonical_instrument)
        return self._adapter.discover_symbols(canonical_instrument)

    def save_symbol_map(self, canonical_instrument, broker_symbol):
        if self.current_state != "OFF":
            raise ScalpingServiceError("SCALPING_SYMBOL_MAP_REQUIRES_OFF_STATE")
        data.validate_canonical_instrument(canonical_instrument)
        document = self._symbol_map_store.load()
        document["mappings"][canonical_instrument] = broker_symbol
        clean = data.validate_symbol_map_document(document)
        self._symbol_map_store.save(clean)
        with self._journal.acquire_mutation_lock() as writer:
            writer.append("SYMBOL_MAPPING_SAVED", {
                "canonical_instrument": canonical_instrument, "broker_symbol": broker_symbol,
            }, occurred_at_utc=self._now())
        return clean

    def set_event_risk_block(self, canonical_instrument, blocked):
        data.validate_canonical_instrument(canonical_instrument)
        document = self._symbol_map_store.load()
        document["event_risk_blocked"][canonical_instrument] = bool(blocked)
        clean = data.validate_symbol_map_document(document)
        self._symbol_map_store.save(clean)
        return clean

    def broker_symbol_for(self, canonical_instrument):
        mapping = self._symbol_map_store.load()["mappings"]
        broker_symbol = mapping.get(canonical_instrument)
        if not broker_symbol:
            raise ScalpingServiceError("SCALPING_SYMBOL_NOT_MAPPED")
        return broker_symbol

    def event_risk_blocked_for(self, canonical_instrument):
        return bool(self._symbol_map_store.load()["event_risk_blocked"].get(canonical_instrument, False))

    # ------------------------------------------------------------------
    # Profile / risk configuration (Section 11)
    # ------------------------------------------------------------------

    def configure_profile(self, canonical_instrument, profile_id, risk_overrides=None, max_spread_points=None):
        self._require_non_demo_auto_for_config()
        data.validate_canonical_instrument(canonical_instrument)
        data.validate_profile_id(profile_id)
        settings = dict(self._risk_settings)
        if risk_overrides:
            settings.update(risk_overrides)
        settings = risk.validate_risk_settings(settings)
        self._risk_settings = settings
        self._profiles[canonical_instrument] = profile_id
        if max_spread_points is not None:
            self._max_spread_points[canonical_instrument] = int(max_spread_points)
        with self._journal.acquire_mutation_lock() as writer:
            writer.append("PROFILE_CONFIGURED", {
                "canonical_instrument": canonical_instrument, "profile_id": profile_id,
                # The effective settings are part of the payload (not just
                # instrument/profile_id) so two genuinely distinct
                # reconfigurations are never journal-indistinguishable from
                # each other even when they land in the same clock tick.
                "risk_settings": {key: str(value) for key, value in settings.items()},
                "max_spread_points": str(self._max_spread_points.get(canonical_instrument, DEFAULT_MAX_SPREAD_POINTS)),
            }, occurred_at_utc=self._now())
        self._persist_config()
        return {"profile_id": profile_id, "risk_settings": {k: str(v) for k, v in settings.items()}}

    def profile_for(self, canonical_instrument):
        return self._profiles.get(canonical_instrument, "ALSAKKAF_PRECISION_SCALPING")

    def configure_side(self, canonical_instrument, side_restriction):
        self._require_non_demo_auto_for_config()
        data.validate_canonical_instrument(canonical_instrument)
        data._require_choice(side_restriction, data.SIDE_RESTRICTIONS, "side_restriction")
        self._side_restrictions[canonical_instrument] = side_restriction
        self._persist_config()
        return {"canonical_instrument": canonical_instrument, "side_restriction": side_restriction}

    def side_restriction_for(self, canonical_instrument):
        return self._side_restrictions.get(canonical_instrument, "BOTH")

    def set_monitoring_interval_seconds(self, seconds):
        self._require_non_demo_auto_for_config()
        if (
            not isinstance(seconds, int) or isinstance(seconds, bool)
            or not data.MIN_MONITORING_INTERVAL_SECONDS <= seconds <= data.MAX_MONITORING_INTERVAL_SECONDS
        ):
            raise ScalpingServiceError("SCALPING_MONITORING_INTERVAL_OUT_OF_BOUNDS")
        self._monitoring_interval_seconds = seconds
        self._persist_config()
        return self._monitoring_interval_seconds

    @property
    def monitoring_interval_seconds(self):
        return self._monitoring_interval_seconds

    def configuration_document(self):
        mapping_document = self._symbol_map_store.load()
        return {
            "schema_version": data.CONFIG_SCHEMA,
            "mappings": dict(mapping_document["mappings"]),
            "event_risk_blocked": dict(mapping_document["event_risk_blocked"]),
            "profiles": dict(self._profiles),
            "side_restrictions": dict(self._side_restrictions),
            "max_spread_points": dict(self._max_spread_points),
            "risk_settings": {key: str(value) for key, value in self._risk_settings.items()},
            "monitoring_interval_seconds": self._monitoring_interval_seconds,
        }

    # ------------------------------------------------------------------
    # Adapter passthroughs (TRL-R2-013 Section 6/7): thin, read-only
    # delegation so ``alsakkaf_scalping_runtime.py`` can assemble the live
    # status/analysis documents without reaching into a private attribute.
    # ------------------------------------------------------------------

    def dependency_status(self):
        return self._adapter.dependency_status()

    def terminal_status(self):
        return self._adapter.terminal_status()

    def account_status(self):
        return self._adapter.account_status()

    def symbol_status(self, broker_symbol):
        return self._adapter.symbol_status(broker_symbol)

    def fetch_completed_bars(self, broker_symbol, timeframe, count):
        return self._adapter.fetch_completed_bars(broker_symbol, timeframe, count)

    @property
    def adapter_tier(self):
        return getattr(self._adapter, "tier", "UNKNOWN")

    @property
    def mode_service(self):
        return self._mode_service

    def mt5_connected(self):
        """Contract Section 7: true only when the terminal AND the demo
        account are both independently, freshly proven -- never derived
        from journal health (root cause 2 of the operational hotfix)."""
        terminal = self.terminal_status()
        if not terminal.get("connected"):
            return False
        account = self.account_status()
        return bool(account.get("available")) and account.get("trade_mode") == mt5_adapter.ACCOUNT_TRADE_MODE_DEMO

    # ------------------------------------------------------------------
    # Preflight (Section 6)
    # ------------------------------------------------------------------

    def run_preflight(self, canonical_instrument):
        broker_symbol = self.broker_symbol_for(canonical_instrument)
        symbol_status = self._adapter.symbol_status(broker_symbol)
        quote_age_seconds = 0 if symbol_status.get("tick_time_utc") else None
        if symbol_status.get("tick_time_utc"):
            tick_time = validate_utc_timestamp(symbol_status["tick_time_utc"])
            quote_age_seconds = max(0, (self._now_dt() - tick_time).total_seconds())
        daily_loss_ok = self._daily_loss_ok()
        return mt5_adapter.run_preflight(
            self._adapter, broker_symbol,
            self._max_spread_points.get(canonical_instrument, DEFAULT_MAX_SPREAD_POINTS),
            self.is_emergency_stopped, self.event_risk_blocked_for(canonical_instrument),
            daily_loss_ok, session_open=True, quote_age_seconds=quote_age_seconds,
        )

    def daily_pnl_and_drawdown(self):
        """Read-only view for the live-status document (TRL-R2-013 Section
        6); establishes the same start-of-day/peak-equity tracking
        ``_daily_loss_ok`` uses, without requiring a full preflight call."""
        ok = self._daily_loss_ok()
        if self._start_of_day_equity is None or self._peak_equity is None:
            return {"daily_pnl": None, "session_drawdown_pct": None, "within_limits": ok}
        account = self._adapter.account_status()
        equity = account.get("equity")
        if equity is None:
            return {"daily_pnl": None, "session_drawdown_pct": None, "within_limits": ok}
        equity = Decimal(equity)
        daily_pnl = equity - self._start_of_day_equity
        drawdown_pct = (
            ((self._peak_equity - equity) / self._peak_equity) * Decimal("100")
            if self._peak_equity > 0 else Decimal("0")
        )
        return {"daily_pnl": str(daily_pnl), "session_drawdown_pct": str(drawdown_pct), "within_limits": ok}

    def _daily_loss_ok(self):
        account = self._adapter.account_status()
        equity = account.get("equity")
        if equity is None:
            return False
        equity = Decimal(equity)
        if self._start_of_day_equity is None:
            self._start_of_day_equity = equity
        if self._peak_equity is None or equity > self._peak_equity:
            self._peak_equity = equity
        loss = self._start_of_day_equity - equity
        if loss > 0 and risk.daily_loss_breached(
            loss, self._start_of_day_equity, self._risk_settings["max_daily_loss_pct"],
        ):
            return False
        if risk.session_drawdown_breached(
            self._peak_equity, equity, self._risk_settings["max_session_drawdown_pct"],
        ):
            return False
        return True

    # ------------------------------------------------------------------
    # Analysis + R2-010 bridge (Section 8)
    # ------------------------------------------------------------------

    def analyze(self, canonical_instrument, entry_bars, confirmation_bars, current_price, spread, use_bridge=True):
        evaluation = strategy.evaluate_setup(entry_bars, confirmation_bars, current_price, spread)
        with self._journal.acquire_mutation_lock() as writer:
            writer.append("ANALYSIS_COMPLETED", {
                "canonical_instrument": canonical_instrument,
                "direction": evaluation["direction"], "total_score": evaluation["total_score"],
                "classification": evaluation["classification"],
            }, occurred_at_utc=self._now())

        result = {"evaluation": evaluation, "bridge_decision": None}
        if use_bridge and evaluation["classification"] == "TRADE_CANDIDATE" and self._mi_service is not None:
            profile_id = self.profile_for(canonical_instrument)
            plan_geometry = _plan_geometry(profile_id, evaluation, self._risk_settings)
            envelope = strategy.build_analysis_input(
                canonical_instrument, profile_id, evaluation, entry_bars, self._now(),
                evaluation["direction"], plan_geometry["stop_price"],
                plan_geometry["target_prices"], plan_geometry["target_allocations_pct"],
                format_utc(self._now_dt() + timedelta(minutes=self._risk_settings["scalping_pending_expiry_minutes"])),
                self.event_risk_blocked_for(canonical_instrument),
            )
            bridge_result = strategy.run_r2010_bridge(self._mi_service, envelope, self._scratch_directory)
            result["bridge_decision"] = bridge_result["decision"]
            with self._journal.acquire_mutation_lock() as writer:
                writer.append("DECISION_RECORDED", {
                    "canonical_instrument": canonical_instrument,
                    "final_status": bridge_result["decision"]["final_status"],
                    "opportunity_id": bridge_result["opportunity"]["opportunity_id"],
                }, occurred_at_utc=self._now())
        return result

    # ------------------------------------------------------------------
    # Cycle execution (Section 14)
    # ------------------------------------------------------------------

    def run_cycle(self, canonical_instrument, entry_bars, confirmation_bars, current_price, spread):
        current_state = self.current_state
        if current_state not in ("ANALYZE_ONLY", "DEMO_AUTO"):
            raise ScalpingServiceError("SCALPING_STATE_FORBIDS_EXECUTION")

        analysis = self.analyze(canonical_instrument, entry_bars, confirmation_bars, current_price, spread)
        evaluation = analysis["evaluation"]
        bridge_decision = analysis["bridge_decision"]
        if bridge_decision is None or bridge_decision["final_status"] != "TRADE_CANDIDATE":
            return {"created": False, "reason": "NOT_TRADE_CANDIDATE", "analysis": analysis}

        if current_state != "DEMO_AUTO":
            plan_only = self._build_cycle_plans(canonical_instrument, evaluation)
            return {"created": False, "reason": "ANALYZE_ONLY_PLAN", "plans": plan_only, "analysis": analysis}

        if self._has_uncertain_cycle(canonical_instrument):
            raise ScalpingServiceError("SCALPING_CYCLE_FROZEN_UNCERTAIN")

        preflight = self.run_preflight(canonical_instrument)
        if not preflight["passed"]:
            with self._journal.acquire_mutation_lock() as writer:
                writer.append("CYCLE_BLOCKED", {
                    "canonical_instrument": canonical_instrument,
                    "reason_code": preflight["blocking_reason_code"],
                }, occurred_at_utc=self._now())
            return {"created": False, "reason": preflight["blocking_reason_code"], "analysis": analysis}

        plans = self._build_cycle_plans(canonical_instrument, evaluation)
        broker_symbol = self.broker_symbol_for(canonical_instrument)
        expiry_utc = format_utc(
            self._now_dt() + timedelta(minutes=self._risk_settings["scalping_pending_expiry_minutes"])
        )
        with self._journal.acquire_mutation_lock() as writer:
            order_plan_ids = []
            total_risk = Decimal("0")
            for plan in plans:
                order_plan = data.build_order_plan(
                    canonical_instrument, broker_symbol, plan["side"], plan["order_type"],
                    self.profile_for(canonical_instrument), plan["entry_price"], plan["stop_price"],
                    plan["target_prices"], plan["target_allocations_pct"], plan["lots"],
                    plan["risk_amount"], self._now(),
                )
                writer.append("ORDER_PLAN_CREATED", {"order_plan": order_plan}, occurred_at_utc=self._now())
                order_plan_ids.append(order_plan["order_plan_id"])
                total_risk += Decimal(order_plan["risk_amount"])
                plan["order_plan"] = order_plan

            cycle = data.build_cycle(
                canonical_instrument, broker_symbol, self.profile_for(canonical_instrument),
                current_price, evaluation["bundle"]["atr"], evaluation["bundle"]["spread"],
                order_plan_ids, expiry_utc, total_risk, "0", self._now(),
            )
            writer.append("CYCLE_CREATED", {"cycle": cycle}, occurred_at_utc=self._now())

            executed_plans = []
            uncertain = False
            for plan in plans:
                order_plan = plan["order_plan"]
                request = _order_request(order_plan)
                check_result = self._adapter.order_check(request)
                writer.append("ORDER_CHECK_RECORDED", {
                    "order_plan_id": order_plan["order_plan_id"], "result": check_result,
                }, occurred_at_utc=self._now())
                if check_result.get("outcome") != "PASSED":
                    writer.append("CYCLE_BLOCKED", {
                        "cycle_id": cycle["cycle_id"], "order_plan_id": order_plan["order_plan_id"],
                        "reason_code": "SCALPING_ORDER_CHECK_REJECTED",
                    }, occurred_at_utc=self._now())
                    continue
                send_result = self._adapter.order_send(request)
                writer.append("ORDER_SEND_RECORDED", {
                    "order_plan_id": order_plan["order_plan_id"], "result": send_result,
                }, occurred_at_utc=self._now())
                if send_result.get("outcome") == "FILLED":
                    writer.append("POSITION_OPENED", {
                        "order_plan_id": order_plan["order_plan_id"], "ticket": send_result.get("ticket"),
                    }, occurred_at_utc=self._now())
                    executed_plans.append({"order_plan_id": order_plan["order_plan_id"], "ticket": send_result.get("ticket")})
                elif send_result.get("outcome") == "REJECTED":
                    writer.append("CYCLE_BLOCKED", {
                        "cycle_id": cycle["cycle_id"], "order_plan_id": order_plan["order_plan_id"],
                        "reason_code": "SCALPING_ORDER_SEND_REJECTED",
                    }, occurred_at_utc=self._now())
                else:
                    writer.append("ORDER_RESULT_UNCERTAIN", {
                        "cycle_id": cycle["cycle_id"], "order_plan_id": order_plan["order_plan_id"],
                    }, occurred_at_utc=self._now())
                    uncertain = True

            if uncertain:
                final_state = "UNCERTAIN"
            elif executed_plans:
                final_state = "ACTIVE" if len(executed_plans) == len(plans) else "PARTIALLY_TRIGGERED"
            else:
                final_state = "BLOCKED"
            writer.append("CYCLE_COMPLETED" if final_state == "ACTIVE" else "CYCLE_BLOCKED", {
                "cycle_id": cycle["cycle_id"], "final_state": final_state,
            }, occurred_at_utc=self._now())

        self._last_symbol_cycle_at_utc[canonical_instrument] = self._now()
        return {
            "created": True, "cycle_id": cycle["cycle_id"], "final_state": final_state,
            "executed_plans": executed_plans, "analysis": analysis,
        }

    def _has_uncertain_cycle(self, canonical_instrument):
        cycle_id_to_symbol = {}
        uncertain_cycle_ids = set()
        resolved_cycle_ids = set()
        for event in self._journal.events:
            if event["event_type"] == "CYCLE_CREATED":
                cycle = event["payload"]["cycle"]
                cycle_id_to_symbol[cycle["cycle_id"]] = cycle["canonical_instrument"]
            elif event["event_type"] == "ORDER_RESULT_UNCERTAIN":
                uncertain_cycle_ids.add(event["payload"]["cycle_id"])
            elif event["event_type"] in ("CYCLE_COMPLETED", "CYCLE_CANCELLED", "CYCLE_EXPIRED"):
                resolved_cycle_ids.add(event["payload"]["cycle_id"])
        for cycle_id in uncertain_cycle_ids - resolved_cycle_ids:
            if cycle_id_to_symbol.get(cycle_id) == canonical_instrument:
                return True
        return False

    def _build_cycle_plans(self, canonical_instrument, evaluation):
        profile_id = self.profile_for(canonical_instrument)
        geometry = _plan_geometry(profile_id, evaluation, self._risk_settings)
        equity = Decimal(self._adapter.account_status().get("equity") or "0")
        broker_symbol = self.broker_symbol_for(canonical_instrument)
        symbol_info = self._adapter.symbol_status(broker_symbol)

        if profile_id == "ALSAKKAF_BREAKOUT_LADDER":
            return _build_ladder_plans(evaluation, geometry, equity, self._risk_settings, symbol_info)
        return [_build_single_plan(evaluation, geometry, equity, self._risk_settings, symbol_info)]

    # ------------------------------------------------------------------
    # Emergency stop (Section 14.5/14.6)
    # ------------------------------------------------------------------

    def _execute_emergency_stop(self):
        owned_orders = self._adapter.owned_orders(data.ALSAKKAF_SCALPING_MAGIC)
        owned_positions = self._adapter.owned_positions(data.ALSAKKAF_SCALPING_MAGIC)
        unresolved = []
        with self._journal.acquire_mutation_lock() as writer:
            for order in owned_orders:
                writer.append("PENDING_ORDER_CANCELLED", {"ticket": order["ticket"]}, occurred_at_utc=self._now())
            for position in owned_positions:
                writer.append("POSITION_CLOSED", {"ticket": position["ticket"]}, occurred_at_utc=self._now())
            writer.append("EMERGENCY_STOP_ACTIVATED", {
                "cancelled_orders": [order["ticket"] for order in owned_orders],
                "closed_positions": [position["ticket"] for position in owned_positions],
                "unresolved": unresolved,
            }, occurred_at_utc=self._now())
        return {"cancelled_orders": len(owned_orders), "closed_positions": len(owned_positions), "unresolved": unresolved}

    def reset_emergency_stop(self):
        if self.current_state != "EMERGENCY_STOP":
            raise ScalpingServiceError("SCALPING_NOT_EMERGENCY_STOPPED")
        owned_orders = self._adapter.owned_orders(data.ALSAKKAF_SCALPING_MAGIC)
        if owned_orders:
            raise ScalpingServiceError("SCALPING_EMERGENCY_RESET_REQUIRES_ZERO_PENDING_ORDERS")
        with self._journal.acquire_mutation_lock() as writer:
            writer.append("EMERGENCY_STOP_RESET", {}, occurred_at_utc=self._now())
            writer.append("SCALPING_STATE_CHANGED", {
                "from_state": "EMERGENCY_STOP", "to_state": "OFF", "reason": "emergency_reset",
            }, occurred_at_utc=self._now())
        return "OFF"

    # ------------------------------------------------------------------
    # TRL-R2-013 Founder shutdown correction: deterministic, idempotent,
    # state-aware stop. The R2-012 transition table only ever allowed
    # ``ANALYZE_ONLY -> PAUSED`` never at all (``PAUSED`` is reachable only
    # from ``DEMO_AUTO``/``PAUSED`` itself) -- a plain ``scalping-pause``
    # call therefore always failed from the exact state the corrected
    # R2-013 launcher establishes (``ANALYZE_ONLY``), and a naive fallback
    # to ``EMERGENCY_STOP`` on that failure latched an unnecessary
    # emergency stop on every ordinary shutdown. This method never uses
    # ``EMERGENCY_STOP`` as a generic fallback, and never attempts a bare
    # ``EMERGENCY_STOP -> OFF`` transition (which the R2-012 transition
    # table technically allows but which would bypass the zero-owned-
    # pending-orders gate ``reset_emergency_stop`` alone enforces).
    # ------------------------------------------------------------------

    def graceful_stop(self):
        current = self.current_state
        if current == "OFF":
            return {"outcome": "ALREADY_OFF", "product_state": "OFF"}
        if current in ("ANALYZE_ONLY", "PAUSED"):
            return {"outcome": "STOPPED", "product_state": self.request_state_change("OFF")}
        if current == "DEMO_AUTO":
            self.request_state_change("EMERGENCY_STOP")
            self._require_zero_owned_state_or_raise("SCALPING_GRACEFUL_STOP_OWNED_STATE_REMAINS")
            return {"outcome": "STOPPED", "product_state": self.reset_emergency_stop()}
        if current == "EMERGENCY_STOP":
            self._require_zero_owned_state_or_raise("SCALPING_GRACEFUL_STOP_OWNED_STATE_REMAINS")
            return {"outcome": "STOPPED", "product_state": self.reset_emergency_stop()}
        raise ScalpingServiceError("SCALPING_GRACEFUL_STOP_UNKNOWN_STATE")

    def recover_stale_emergency_stop(self):
        """TRL-R2-013 Section 4: startup-only recovery for a latched
        ``EMERGENCY_STOP`` left over from a prior session. Never acts on
        any other state (in particular, never force-stops a genuinely
        active ``DEMO_AUTO`` -- that is the shutdown path's job, not
        startup's). Fails closed, without resetting anything, when owned
        broker state is non-zero or uncertain."""
        current = self.current_state
        if current != "EMERGENCY_STOP":
            return {"outcome": "NO_ACTION_NEEDED", "product_state": current}
        self._require_zero_owned_state_or_raise("SCALPING_STARTUP_RECOVERY_OWNED_STATE_REMAINS")
        return {"outcome": "RECOVERED", "product_state": self.reset_emergency_stop()}

    def _require_zero_owned_state_or_raise(self, reason_code):
        reconciled = self.reconcile()
        if reconciled["owned_orders"] or reconciled["owned_positions"]:
            raise ScalpingServiceError(reason_code)

    # ------------------------------------------------------------------
    # Reconciliation and read-only views
    # ------------------------------------------------------------------

    def reconcile(self):
        owned_orders = self._adapter.owned_orders(data.ALSAKKAF_SCALPING_MAGIC)
        owned_positions = self._adapter.owned_positions(data.ALSAKKAF_SCALPING_MAGIC)
        return {"owned_orders": owned_orders, "owned_positions": owned_positions}

    def list_owned_orders(self):
        return self._adapter.owned_orders(data.ALSAKKAF_SCALPING_MAGIC)

    def list_owned_positions(self):
        return self._adapter.owned_positions(data.ALSAKKAF_SCALPING_MAGIC)

    def list_cycles(self):
        cycles = {}
        for event in self._journal.events:
            if event["event_type"] == "CYCLE_CREATED":
                cycle = event["payload"]["cycle"]
                cycles[cycle["cycle_id"]] = cycle
        return list(cycles.values())

    def inspect_cycle(self, cycle_id):
        for cycle in self.list_cycles():
            if cycle["cycle_id"] == cycle_id:
                return cycle
        raise ScalpingServiceError("SCALPING_CYCLE_NOT_FOUND")

    def journal_tail(self, limit=100):
        limit = max(1, min(int(limit), 1000))
        return self._journal.events[-limit:]

    def status_document(self):
        return {
            "product_state": self.current_state,
            "profiles": dict(self._profiles),
            "risk_settings": {key: str(value) for key, value in self._risk_settings.items()},
            "emergency_stop_active": self.is_emergency_stopped,
            "journal_startup_diagnostic_code": self._journal.startup_diagnostic_code,
        }

    def shutdown(self):
        return self._journal.shutdown()


def _plan_geometry(profile_id, evaluation, risk_settings):
    bundle = evaluation["bundle"]
    direction = evaluation["direction"]
    atr_multiplier = Decimal("1.5") if profile_id == "ALSAKKAF_INTRADAY" else Decimal("1.0")
    stop_distance = max(
        atr_multiplier * bundle["atr"],
        Decimal("0"),
        Decimal("1.5") * bundle["spread"],
    )
    if stop_distance <= 0:
        stop_distance = Decimal("1.5") * bundle["spread"] if bundle["spread"] > 0 else bundle["atr"]
    entry_price = bundle["current_price"]
    if direction == "BUY":
        stop_price = entry_price - stop_distance
        target_prices = [entry_price + stop_distance * Decimal(mult) for mult in ("1.0", "1.5", "2.0")]
    else:
        stop_price = entry_price + stop_distance
        target_prices = [entry_price - stop_distance * Decimal(mult) for mult in ("1.0", "1.5", "2.0")]
    return {
        "direction": direction, "entry_price": entry_price, "stop_price": stop_price,
        "stop_distance": stop_distance, "target_prices": target_prices,
        "target_allocations_pct": [Decimal("50"), Decimal("30"), Decimal("20")],
    }


def _build_single_plan(evaluation, geometry, equity, risk_settings, symbol_info):
    lot_result = risk.calculate_lots(
        equity, risk_settings["risk_per_cycle_pct"], geometry["entry_price"], geometry["stop_price"], symbol_info,
    )
    return {
        "side": geometry["direction"], "order_type": "MARKET",
        "entry_price": geometry["entry_price"], "stop_price": geometry["stop_price"],
        "target_prices": geometry["target_prices"], "target_allocations_pct": geometry["target_allocations_pct"],
        "lots": lot_result["lots"], "risk_amount": lot_result["risk_amount"],
    }


def _build_ladder_plans(evaluation, geometry, equity, risk_settings, symbol_info):
    bundle = evaluation["bundle"]
    floor_distance = risk.ladder_distance_floor(
        bundle["atr"], bundle["spread"],
        Decimal(symbol_info.get("stops_level", 0) or 0) * Decimal(symbol_info.get("point", "0.01")),
        Decimal(symbol_info.get("point", "0.01")),
    )
    side = geometry["direction"]
    directions = [side] if side in ("BUY", "SELL") else ["BUY", "SELL"]
    plans = []
    total_risk = risk.calculate_lots(
        equity, risk_settings["risk_per_cycle_pct"], geometry["entry_price"], geometry["stop_price"], symbol_info,
    )["risk_amount"]
    order_count = min(risk.MAX_LADDER_ORDERS_PER_SIDE * len(directions), risk.MAX_LADDER_ORDERS)
    per_order_risk = risk.divide_ladder_risk(total_risk, order_count)
    for direction in directions:
        for level in range(1, risk.MAX_LADDER_ORDERS_PER_SIDE + 1):
            offset = floor_distance * Decimal(level)
            if direction == "BUY":
                entry_price = geometry["entry_price"] + offset
                stop_price = entry_price - geometry["stop_distance"]
                target_prices = [entry_price + geometry["stop_distance"] * Decimal(m) for m in ("1.0", "1.5", "2.0")]
                order_type = "BUY_STOP"
            else:
                entry_price = geometry["entry_price"] - offset
                stop_price = entry_price + geometry["stop_distance"]
                target_prices = [entry_price - geometry["stop_distance"] * Decimal(m) for m in ("1.0", "1.5", "2.0")]
                order_type = "SELL_STOP"
            lot_result = risk.calculate_lots(
                equity, (per_order_risk / equity) * Decimal("100") if equity > 0 else Decimal("0"),
                entry_price, stop_price, symbol_info,
            )
            plans.append({
                "side": direction, "order_type": order_type, "entry_price": entry_price,
                "stop_price": stop_price, "target_prices": target_prices,
                "target_allocations_pct": geometry["target_allocations_pct"],
                "lots": lot_result["lots"], "risk_amount": lot_result["risk_amount"],
            })
    return plans


def _order_request(order_plan):
    action_type = {
        "MARKET": "ORDER_TYPE_BUY" if order_plan["side"] == "BUY" else "ORDER_TYPE_SELL",
        "BUY_STOP": "ORDER_TYPE_BUY_STOP", "SELL_STOP": "ORDER_TYPE_SELL_STOP",
    }[order_plan["order_type"]]
    return {
        "action": "TRADE_ACTION_DEAL" if order_plan["order_type"] == "MARKET" else "TRADE_ACTION_PENDING",
        "symbol": order_plan["broker_symbol"], "volume": order_plan["lots"],
        "type": action_type, "price": order_plan["entry_price"], "sl": order_plan["stop_price"],
        "deviation": 20, "type_time": "ORDER_TIME_SPECIFIED",
        "magic": order_plan["magic_number"], "comment": order_plan["comment"],
    }


__all__ = (
    "CAPABILITY",
    "ScalpingService",
    "ScalpingServiceError",
)
