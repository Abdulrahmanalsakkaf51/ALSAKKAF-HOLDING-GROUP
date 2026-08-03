"""ALSAKKAF SCALPING operational runtime (TRL-R2-013): server-authoritative
live analysis, the sanitized live-status document, and bounded read-only
monitoring.

This module never widens ``ScalpingService``'s state machine or execution
authority -- it only supplies the two things R2-012 deliberately deferred to
"the caller" (contract Section 9 of R2-012's evidence): fetching bars/quote
from the real adapter, and assembling a browser-facing status document. No
function here ever calls ``request_state_change("DEMO_AUTO")``,
``order_check``, or ``order_send``.
"""

import threading
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal

from . import alsakkaf_scalping_data as data
from . import alsakkaf_scalping_mt5 as mt5_adapter
from . import alsakkaf_scalping_strategy as strategy
from .alsakkaf_scalping_service import ScalpingServiceError
from .timeline_data import format_utc, validate_utc_timestamp

MONITOR_STOP_JOIN_TIMEOUT_SECONDS = 5.0

_REAL_ADAPTER_MODES = frozenset(("RESEARCH", "MT5_DEMO_MANUAL", "MT5_DEMO_AUTOMATED"))


class ScalpingRuntimeError(RuntimeError):
    def __init__(self, reason_code, message=None):
        super().__init__(message or reason_code)
        self.reason_code = reason_code


def _decimal(value):
    return value if isinstance(value, Decimal) else Decimal(str(value))


def _sanitize_bundle(bundle):
    sanitized = {}
    for key, value in bundle.items():
        if isinstance(value, Decimal):
            sanitized[key] = str(value)
        elif value is None:
            sanitized[key] = None
        else:
            sanitized[key] = value
    return sanitized


def _sanitize_evaluation(evaluation):
    return {
        "direction": evaluation["direction"],
        "scores": dict(evaluation["scores"]),
        "total_score": evaluation["total_score"],
        "classification": evaluation["classification"],
        "bundle": _sanitize_bundle(evaluation["bundle"]),
    }


class ScalpingRuntime:
    """Wraps one ``ScalpingService`` instance with server-side bar/quote
    fetch, a sanitized live-status document, and a single bounded
    read-only monitoring thread. Holds no independent execution authority
    -- every mutation still goes through the wrapped service."""

    def __init__(self, service, clock=None):
        self._service = service
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._last_analysis = {}
        # Two distinct locks, deliberately not one: ``_cache_lock`` guards
        # the ``_last_analysis`` dict and is held only briefly by
        # ``analyze_now`` itself (any caller, any thread); ``_overlap_lock``
        # is the monitor loop's own non-blocking no-overlap guard, held for
        # the whole duration of one tick's ``analyze_now`` call. A single
        # shared, non-reentrant ``Lock`` for both would self-deadlock the
        # monitor thread the moment ``analyze_now`` tried to cache its own
        # result while the loop still held that same lock.
        self._cache_lock = threading.Lock()
        self._overlap_lock = threading.Lock()
        self._monitor_thread = None
        self._monitor_stop_event = threading.Event()
        self._monitor_state = {
            "running": False, "instrument": None, "interval_seconds": None,
            "started_at_utc": None, "last_tick_at_utc": None, "tick_count": 0,
            "stopped_reason": None,
        }
        self._monitor_state_lock = threading.Lock()

    def _now(self):
        return format_utc(self._clock())

    # ------------------------------------------------------------------
    # Server-authoritative live analysis (Section 5)
    # ------------------------------------------------------------------

    def analyze_now(self, canonical_instrument):
        data.validate_canonical_instrument(canonical_instrument)
        try:
            broker_symbol = self._service.broker_symbol_for(canonical_instrument)
        except ScalpingServiceError:
            return self._record_failure(canonical_instrument, "SYMBOL_NOT_MAPPED")

        profile_id = self._service.profile_for(canonical_instrument)
        entry_timeframe = strategy.ENTRY_TIMEFRAME_FOR_PROFILE[profile_id]
        confirmation_timeframe = strategy.CONFIRMATION_TIMEFRAME_FOR_PROFILE[profile_id]

        if not self._service.mt5_connected():
            return self._record_failure(canonical_instrument, "TERMINAL_NOT_CONNECTED")

        quote = self._service.symbol_status(broker_symbol)
        if not quote.get("available") or quote.get("bid") is None or quote.get("ask") is None:
            return self._record_failure(canonical_instrument, "QUOTE_UNAVAILABLE")
        tick_time_utc = quote.get("tick_time_utc")
        if not tick_time_utc:
            return self._record_failure(canonical_instrument, "QUOTE_UNAVAILABLE")
        tick_time = validate_utc_timestamp(tick_time_utc)
        age_seconds = max(0.0, (self._clock() - tick_time).total_seconds())
        if age_seconds > mt5_adapter.MAX_QUOTE_STALENESS_SECONDS:
            return self._record_failure(canonical_instrument, "QUOTE_UNAVAILABLE")

        entry_result = self._service.fetch_completed_bars(broker_symbol, entry_timeframe, strategy.MIN_ENTRY_BARS)
        if not entry_result.get("available"):
            return self._record_failure(canonical_instrument, "HISTORY_INSUFFICIENT")
        confirmation_result = self._service.fetch_completed_bars(
            broker_symbol, confirmation_timeframe, strategy.MIN_CONFIRMATION_BARS,
        )
        if not confirmation_result.get("available"):
            return self._record_failure(canonical_instrument, "HISTORY_INSUFFICIENT")

        bid, ask = _decimal(quote["bid"]), _decimal(quote["ask"])
        current_price = (bid + ask) / Decimal("2")
        spread = ask - bid

        try:
            outcome = self._service.run_cycle(
                canonical_instrument, entry_result["bars"], confirmation_result["bars"],
                current_price, spread,
            )
        except ScalpingServiceError as error:
            return self._record_failure(canonical_instrument, "ANALYSIS_NOT_RUN", detail=error.reason_code)

        evaluation = _sanitize_evaluation(outcome["analysis"]["evaluation"])
        bridge_decision = outcome["analysis"].get("bridge_decision")
        record = {
            "ok": True, "canonical_instrument": canonical_instrument,
            "broker_symbol": broker_symbol, "profile_id": profile_id,
            "evaluation": evaluation,
            "final_status": bridge_decision["final_status"] if bridge_decision else evaluation["classification"],
            "reasons": list(bridge_decision.get("reason_codes", [])) if bridge_decision else [],
            "cycle_created": outcome["created"],
            "cycle_id": outcome.get("cycle_id"),
            "outcome_reason": outcome.get("reason"),
            "bid": str(bid), "ask": str(ask), "spread": str(spread),
            "analyzed_at_utc": self._now(),
        }
        with self._cache_lock:
            self._last_analysis[canonical_instrument] = record
        return record

    def _record_failure(self, canonical_instrument, reason_code, detail=None):
        record = {
            "ok": False, "canonical_instrument": canonical_instrument,
            "reason_code": reason_code, "detail": detail,
            "analyzed_at_utc": self._now(),
        }
        with self._cache_lock:
            self._last_analysis[canonical_instrument] = record
        return record

    def latest_analysis(self, canonical_instrument):
        with self._cache_lock:
            record = self._last_analysis.get(canonical_instrument)
        if record is None:
            return {"ok": False, "canonical_instrument": canonical_instrument, "reason_code": "ANALYSIS_NOT_RUN"}
        return deepcopy(record)

    # ------------------------------------------------------------------
    # Read-only monitoring (Section 10)
    # ------------------------------------------------------------------

    def monitoring_status(self):
        with self._monitor_state_lock:
            return dict(self._monitor_state)

    def _monitoring_safety_check(self, canonical_instrument):
        if self._service.is_emergency_stopped:
            return "SCALPING_EMERGENCY_STOP_ACTIVE"
        if self._service.current_state not in ("ANALYZE_ONLY", "DEMO_AUTO"):
            return "SCALPING_STATE_FORBIDS_EXECUTION"
        if not self._service.terminal_status().get("connected"):
            return "TERMINAL_NOT_CONNECTED"
        if not self._service.mt5_connected():
            return "ACCOUNT_NOT_DEMO"
        mode_service = self._service.mode_service
        if mode_service is not None and getattr(mode_service, "current_mode", None) not in _REAL_ADAPTER_MODES:
            return "OPERATING_MODE_NOT_RESEARCH"
        return None

    def start_monitoring(self, canonical_instrument, interval_seconds=None):
        data.validate_canonical_instrument(canonical_instrument)
        with self._monitor_state_lock:
            if self._monitor_state["running"]:
                raise ScalpingRuntimeError("SCALPING_MONITORING_ALREADY_RUNNING")
        interval = interval_seconds if interval_seconds is not None else self._service.monitoring_interval_seconds
        if (
            not isinstance(interval, int) or isinstance(interval, bool)
            or not data.MIN_MONITORING_INTERVAL_SECONDS <= interval <= data.MAX_MONITORING_INTERVAL_SECONDS
        ):
            raise ScalpingRuntimeError("SCALPING_MONITORING_INTERVAL_OUT_OF_BOUNDS")
        blocking_reason = self._monitoring_safety_check(canonical_instrument)
        if blocking_reason is not None:
            raise ScalpingRuntimeError("SCALPING_MONITORING_PREFLIGHT_FAILED", blocking_reason)

        self._monitor_stop_event = threading.Event()
        with self._monitor_state_lock:
            self._monitor_state.update({
                "running": True, "instrument": canonical_instrument, "interval_seconds": interval,
                "started_at_utc": self._now(), "last_tick_at_utc": None, "tick_count": 0,
                "stopped_reason": None,
            })
        thread = threading.Thread(
            target=self._monitor_loop, args=(canonical_instrument, interval), daemon=True,
            name="alsakkaf-scalping-monitor",
        )
        self._monitor_thread = thread
        thread.start()
        return self.monitoring_status()

    def _monitor_loop(self, canonical_instrument, interval_seconds):
        while not self._monitor_stop_event.is_set():
            blocking_reason = self._monitoring_safety_check(canonical_instrument)
            if blocking_reason is not None:
                self._stop_monitoring_internal(blocking_reason)
                return
            if self._overlap_lock.acquire(blocking=False):
                try:
                    self.analyze_now(canonical_instrument)
                finally:
                    self._overlap_lock.release()
                    with self._monitor_state_lock:
                        self._monitor_state["last_tick_at_utc"] = self._now()
                        self._monitor_state["tick_count"] += 1
            if self._monitor_stop_event.wait(interval_seconds):
                return

    def _stop_monitoring_internal(self, reason):
        with self._monitor_state_lock:
            self._monitor_state["running"] = False
            self._monitor_state["stopped_reason"] = reason
        self._monitor_stop_event.set()

    def stop_monitoring(self, reason="SCALPING_MONITORING_STOPPED_BY_OPERATOR"):
        thread = self._monitor_thread
        self._stop_monitoring_internal(reason)
        if thread is not None and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=MONITOR_STOP_JOIN_TIMEOUT_SECONDS)
        self._monitor_thread = None
        return self.monitoring_status()

    def shutdown(self):
        if self._monitor_state.get("running"):
            self.stop_monitoring("SCALPING_MONITORING_STOPPED_SERVER_SHUTDOWN")

    # ------------------------------------------------------------------
    # Live status document (Section 6/7)
    # ------------------------------------------------------------------

    def live_status_document(self, canonical_instrument=None):
        service = self._service
        mapping_document = service.configuration_document()
        mappings = mapping_document["mappings"]
        if canonical_instrument is None:
            canonical_instrument = sorted(mappings)[0] if mappings else None

        dependency = service.dependency_status()
        terminal = service.terminal_status()
        account = service.account_status()
        mt5_connected = service.mt5_connected()
        mode_service = service.mode_service
        operating_mode = getattr(mode_service, "current_mode", None) if mode_service is not None else None
        pnl_and_drawdown = service.daily_pnl_and_drawdown()

        document = {
            "schema_version": "TRL_SCALPING_LIVE_STATUS.v1",
            "application_state": "RUNNING",
            "operating_mode": operating_mode or "UNKNOWN",
            "product_state": service.current_state,
            "adapter_tier": service.adapter_tier,
            "mt5_package_available": bool(dependency.get("available")),
            "terminal_initialized": terminal.get("connected") is not None,
            "terminal_connected": bool(terminal.get("connected")),
            "algo_trading_enabled": bool(terminal.get("trade_allowed")),
            "mt5_connected": mt5_connected,
            "account_type": account.get("trade_mode_name") or ("UNKNOWN" if account.get("available") else "ACCOUNT_NOT_DEMO"),
            "demo_verified": mt5_connected,
            "account_trade_allowed": bool(account.get("trade_allowed")),
            "account_login_last4": account.get("login_last4"),
            "currency": account.get("currency"),
            "leverage": account.get("leverage"),
            "balance": account.get("balance"),
            "equity": account.get("equity"),
            "daily_pnl": pnl_and_drawdown["daily_pnl"],
            "session_drawdown_pct": pnl_and_drawdown["session_drawdown_pct"],
            "canonical_instrument": canonical_instrument,
            "monitoring_status": self.monitoring_status(),
            "emergency_stop_active": service.is_emergency_stopped,
            "journal_health": service.status_document()["journal_startup_diagnostic_code"],
            "owned_cycle_count": len(service.list_cycles()),
            "owned_pending_order_count": len(service.list_owned_orders()),
            "owned_position_count": len(service.list_owned_positions()),
            "last_update_utc": self._now(),
        }

        if canonical_instrument is None or canonical_instrument not in mappings:
            document.update({
                "broker_symbol": None, "mapping_status": "SYMBOL_NOT_MAPPED",
                "profile": None, "side_restriction": None, "event_risk_blocked": None,
                "quote_status": "SYMBOL_NOT_MAPPED", "bid": None, "ask": None,
                "spread_points": None, "quote_timestamp_utc": None, "quote_age_seconds": None,
                "volume_minimum": None, "volume_maximum": None, "volume_step": None,
                "digits": None, "point": None, "stop_level": None, "freeze_level": None,
                "completed_bar_readiness": "SYMBOL_NOT_MAPPED",
                "last_analysis": {"ok": False, "reason_code": "SYMBOL_NOT_MAPPED"},
            })
            return document

        broker_symbol = mappings[canonical_instrument]
        document["broker_symbol"] = broker_symbol
        document["mapping_status"] = "MAPPED"
        document["profile"] = service.profile_for(canonical_instrument)
        document["side_restriction"] = service.side_restriction_for(canonical_instrument)
        document["event_risk_blocked"] = service.event_risk_blocked_for(canonical_instrument)

        if not terminal.get("connected"):
            quote_status = "TERMINAL_NOT_CONNECTED"
        elif not mt5_connected:
            quote_status = "ACCOUNT_NOT_DEMO"
        else:
            quote_status = None

        symbol_status = service.symbol_status(broker_symbol) if quote_status is None else {}
        if quote_status is None and (not symbol_status.get("available") or symbol_status.get("bid") is None):
            quote_status = "QUOTE_UNAVAILABLE"

        if quote_status is not None:
            document.update({
                "quote_status": quote_status, "bid": None, "ask": None, "spread_points": None,
                "quote_timestamp_utc": None, "quote_age_seconds": None,
                "volume_minimum": None, "volume_maximum": None, "volume_step": None,
                "digits": None, "point": None, "stop_level": None, "freeze_level": None,
                "completed_bar_readiness": quote_status,
            })
        else:
            tick_time_utc = symbol_status.get("tick_time_utc")
            quote_age_seconds = None
            if tick_time_utc:
                quote_age_seconds = max(0.0, (self._clock() - validate_utc_timestamp(tick_time_utc)).total_seconds())
            spread_points = None
            if symbol_status.get("point"):
                spread_points = str(
                    (Decimal(symbol_status["ask"]) - Decimal(symbol_status["bid"])) / Decimal(symbol_status["point"])
                )
            document.update({
                "quote_status": "FRESH" if (quote_age_seconds is not None and quote_age_seconds <= mt5_adapter.MAX_QUOTE_STALENESS_SECONDS) else "STALE",
                "bid": symbol_status.get("bid"), "ask": symbol_status.get("ask"),
                "spread_points": spread_points,
                "quote_timestamp_utc": tick_time_utc, "quote_age_seconds": quote_age_seconds,
                "volume_minimum": symbol_status.get("volume_minimum"),
                "volume_maximum": symbol_status.get("volume_maximum"),
                "volume_step": symbol_status.get("volume_step"),
                "digits": symbol_status.get("digits"), "point": symbol_status.get("point"),
                "stop_level": symbol_status.get("stops_level"),
                "freeze_level": symbol_status.get("freeze_level"),
                "completed_bar_readiness": "READY",
            })

        document["last_analysis"] = self.latest_analysis(canonical_instrument)
        return document


__all__ = (
    "MONITOR_STOP_JOIN_TIMEOUT_SECONDS",
    "ScalpingRuntime",
    "ScalpingRuntimeError",
)
