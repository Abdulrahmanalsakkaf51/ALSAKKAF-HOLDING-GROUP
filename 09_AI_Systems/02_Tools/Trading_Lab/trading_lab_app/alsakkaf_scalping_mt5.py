"""MT5 demo-only adapter and 20-check preflight for ALSAKKAF SCALPING
(TRL-R2-012 contract Sections 2, 6, 7).

Mirrors ``mt5_execution_adapter.py``'s three-tier boundary (Disabled/Fake/
Real) exactly: lazy import, allowlisted provider methods, a single
serializing lock, strict response normalization, always-run shutdown. This
module never caches a demo-account determination across calls -- every
preflight call independently re-verifies ``trade_mode ==
ACCOUNT_TRADE_MODE_DEMO`` (contract Section 2's real-money hard lock).
"""

import importlib
import numbers
import threading
from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal

from . import market_data
from .timeline_data import format_utc


PROVIDER_METHOD_ALLOWLIST = frozenset((
    "initialize",
    "shutdown",
    "last_error",
    "terminal_info",
    "account_info",
    "symbol_info",
    "symbol_info_tick",
    "symbol_select",
    "symbols_get",
    "order_check",
    "order_send",
    "positions_get",
    "orders_get",
    "copy_rates_from_pos",
))
_PROVIDER_SESSION_LOCK = threading.Lock()

# TRL-R2-013 Section 5: bar timeframes needed for entry/confirmation/context
# analysis (R2-012 only ever needed symbol/tick metadata). Private to this
# adapter -- ``mt5_connector.py``'s own constant allowlist is unmodified.
BAR_TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4")
_BAR_TIMEFRAME_CONSTANT_NAMES = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "M15": "TIMEFRAME_M15",
    "H1": "TIMEFRAME_H1",
    "H4": "TIMEFRAME_H4",
}
_MAX_PROVIDER_TIMEFRAME_IDENTIFIER = (2 ** 31) - 1
MAX_BAR_FETCH_COUNT = 500

_ACCOUNT_TRADE_MODE_DEMO = 0
_ACCOUNT_TRADE_MODE_CONTEST = 1
_ACCOUNT_TRADE_MODE_REAL = 2
_SYMBOL_TRADE_MODE_DISABLED = 0
_SYMBOL_TRADE_MODE_CLOSEONLY = 3

ACCOUNT_TRADE_MODE_DEMO = _ACCOUNT_TRADE_MODE_DEMO
ACCOUNT_TRADE_MODE_NAMES = {
    _ACCOUNT_TRADE_MODE_DEMO: "DEMO",
    _ACCOUNT_TRADE_MODE_CONTEST: "CONTEST",
    _ACCOUNT_TRADE_MODE_REAL: "REAL",
}

MAX_QUOTE_STALENESS_SECONDS = 10

INSTRUMENT_ALIASES = {
    "XAUUSD": ("xauusd", "gold"),
    "NAS100": ("nas100", "us100", "usa100", "ustec", "nq100"),
    "EURUSD": ("eurusd",),
    "GBPUSD": ("gbpusd",),
    "USDJPY": ("usdjpy",),
}


def _now(clock):
    return format_utc(datetime.now(timezone.utc) if clock is None else clock())


class ScalpingMT5AdapterError(RuntimeError):
    """Raised only for programmer errors (disallowed provider method)."""


class DisabledScalpingAdapter:
    """The default adapter. No import, no connection, every call denied."""

    tier = "DISABLED"

    def dependency_status(self):
        return {"available": False, "reason_code": "ADAPTER_DISABLED"}

    def terminal_status(self):
        return {"connected": False, "trade_allowed": False, "reason_code": "ADAPTER_DISABLED"}

    def account_status(self):
        return {
            "available": False, "login_last4": None, "trade_mode": None,
            "trade_mode_name": None, "trade_allowed": False, "equity": None,
            "balance": None, "currency": None, "leverage": None,
            "reason_code": "ADAPTER_DISABLED",
        }

    def symbol_status(self, symbol):
        return {
            "available": False, "symbol": symbol, "visible": False,
            "trade_mode": None, "tradeable": False, "reason_code": "ADAPTER_DISABLED",
        }

    def discover_symbols(self, canonical_instrument):
        return []

    def fetch_completed_bars(self, symbol, timeframe, count):
        return {"available": False, "bars": [], "reason_code": "ADAPTER_DISABLED"}

    def owned_orders(self, magic_number):
        return []

    def owned_positions(self, magic_number):
        return []

    def order_check(self, request):
        return {"outcome": "FAILED", "retcode": None, "comment": "ADAPTER_DISABLED", "checked_at_utc": _now(None)}

    def order_send(self, request):
        return {
            "outcome": "REJECTED", "retcode": None, "ticket": None, "deal": None,
            "comment": "ADAPTER_DISABLED", "sent_at_utc": _now(None),
        }


def disabled_adapter():
    return DisabledScalpingAdapter()


class FakeScalpingAdapter:
    """Deterministic in-memory adapter for automated tests. No network."""

    tier = "FAKE"

    def __init__(self, clock=None):
        self._clock = clock
        self.calls = []
        self.dependency = {"available": True, "reason_code": None}
        self.terminal = {"connected": True, "trade_allowed": True, "reason_code": None}
        self.account = {
            "available": True, "login_last4": "0100", "trade_mode": _ACCOUNT_TRADE_MODE_DEMO,
            "trade_mode_name": "DEMO", "trade_allowed": True, "equity": "10000",
            "balance": "10000", "currency": "USD", "leverage": 100,
            "reason_code": None,
        }
        self.symbols = {}
        self.symbol_candidates = {}
        self._bars = {}
        self._check_queue = []
        self._send_queue = []
        self._positions = []
        self._orders = []

    def _record(self, operation, request):
        self.calls.append((operation, deepcopy(request)))

    def set_symbol(self, symbol, **fields):
        base = {
            "available": True, "symbol": symbol, "visible": True,
            "trade_mode": 4, "tradeable": True,
            "bid": "1900.00", "ask": "1900.20", "digits": 2, "point": "0.01",
            "volume_minimum": "0.01", "volume_maximum": "100", "volume_step": "0.01",
            "tick_value": "1.00", "tick_size": "0.01",
            "stops_level": 50, "freeze_level": 0,
            "tick_time_utc": _now(self._clock), "reason_code": None,
        }
        base.update(fields)
        self.symbols[symbol] = base

    def set_symbol_candidates(self, canonical_instrument, candidates):
        self.symbol_candidates[canonical_instrument] = list(candidates)

    def set_bars(self, symbol, timeframe, bars):
        """``bars`` is a list of closed-bar dicts (oldest first), each with
        open/high/low/close/time_utc -- the deterministic fixture shape
        tests build directly, never touching MetaTrader5."""
        self._bars[(symbol, timeframe)] = list(bars)

    def set_owned_positions(self, positions):
        self._positions = list(positions)

    def set_owned_orders(self, orders):
        self._orders = list(orders)

    def queue_check_result(self, result):
        self._check_queue.append(result)

    def queue_send_result(self, result):
        self._send_queue.append(result)

    def dependency_status(self):
        return dict(self.dependency)

    def terminal_status(self):
        return dict(self.terminal)

    def account_status(self):
        return dict(self.account)

    def symbol_status(self, symbol):
        if symbol not in self.symbols:
            return {
                "available": False, "symbol": symbol, "visible": False,
                "trade_mode": None, "tradeable": False, "reason_code": "SYMBOL_UNAVAILABLE",
            }
        return dict(self.symbols[symbol])

    def discover_symbols(self, canonical_instrument):
        return list(self.symbol_candidates.get(canonical_instrument, []))

    def fetch_completed_bars(self, symbol, timeframe, count):
        bars = self._bars.get((symbol, timeframe))
        if not bars:
            return {"available": False, "bars": [], "reason_code": "HISTORY_INSUFFICIENT"}
        if len(bars) < count:
            return {"available": False, "bars": [], "reason_code": "HISTORY_INSUFFICIENT"}
        return {"available": True, "bars": deepcopy(bars[-count:]), "reason_code": None}

    def owned_orders(self, magic_number):
        return [order for order in self._orders if order.get("magic") == magic_number]

    def owned_positions(self, magic_number):
        return [position for position in self._positions if position.get("magic") == magic_number]

    def order_check(self, request):
        self._record("order_check", request)
        if self._check_queue:
            return self._check_queue.pop(0)
        return {"outcome": "PASSED", "retcode": 0, "comment": "fake order_check ok", "checked_at_utc": _now(self._clock)}

    def order_send(self, request):
        self._record("order_send", request)
        if self._send_queue:
            return self._send_queue.pop(0)
        return {
            "outcome": "FILLED", "retcode": 10009, "ticket": 700001, "deal": 700002,
            "volume_filled": request.get("volume"), "comment": "fake order_send filled",
            "sent_at_utc": _now(self._clock),
        }


def fake_adapter(clock=None):
    return FakeScalpingAdapter(clock=clock)


class RealScalpingMT5Adapter:
    """Isolated boundary to the optional real ``MetaTrader5`` package.
    Never imports at module/construction time; every method independently
    initializes and shuts down within one serializing lock, exactly like
    ``mt5_execution_adapter.RealMT5ExecutionAdapter``."""

    tier = "REAL"

    def __init__(self, provider=None, clock=None, timeout_ms=market_data.DEFAULT_INITIALIZATION_TIMEOUT_MS):
        self._provider = provider
        self._clock = clock
        self._timeout_ms = timeout_ms
        self._lock = _PROVIDER_SESSION_LOCK

    def _provider_or_import(self):
        if self._provider is not None:
            return self._provider
        try:
            return importlib.import_module("MetaTrader5")
        except ImportError:
            return None

    @staticmethod
    def _call(provider, operation, *args, **kwargs):
        if operation not in PROVIDER_METHOD_ALLOWLIST:
            raise ScalpingMT5AdapterError("provider operation is not allowlisted")
        return getattr(provider, operation)(*args, **kwargs)

    def _now(self):
        return _now(self._clock)

    def dependency_status(self):
        provider = self._provider_or_import()
        if provider is None:
            return {"available": False, "reason_code": "MT5_DEPENDENCY_MISSING"}
        return {"available": True, "reason_code": None}

    def _with_session(self, body):
        provider = self._provider_or_import()
        if provider is None:
            return None, "MT5_DEPENDENCY_MISSING"
        with self._lock:
            initialized = False
            try:
                initialized = bool(self._call(provider, "initialize", timeout=self._timeout_ms))
                if not initialized:
                    return None, "TERMINAL_UNAVAILABLE"
                return body(provider), None
            except Exception:
                return None, "BROKER_RESPONSE_MALFORMED"
            finally:
                if initialized:
                    try:
                        self._call(provider, "shutdown")
                    except Exception:
                        pass

    def terminal_status(self):
        def body(provider):
            info = self._call(provider, "terminal_info")
            if info is None:
                return None
            return {
                "connected": bool(market_data._field(info, "connected", False)),
                "trade_allowed": bool(market_data._field(info, "trade_allowed", False)),
                "reason_code": None,
            }
        result, reason = self._with_session(body)
        if reason is not None or result is None:
            return {"connected": False, "trade_allowed": False, "reason_code": reason or "TERMINAL_UNAVAILABLE"}
        return result

    def account_status(self):
        """Never surfaces a full login, password, or broker server -- only
        the last-4-digit login fragment and the trade-mode classification
        (contract Section 2, Section 6)."""
        def body(provider):
            info = self._call(provider, "account_info")
            if info is None:
                return None
            login_value = market_data._field(info, "login")
            login_last4 = None
            if isinstance(login_value, numbers.Integral) and not isinstance(login_value, bool):
                login_last4 = str(int(login_value))[-4:]
            trade_mode_value = market_data._field(info, "trade_mode")
            trade_mode = None
            if isinstance(trade_mode_value, numbers.Integral) and not isinstance(trade_mode_value, bool):
                trade_mode = int(trade_mode_value)
            equity_value = market_data._field(info, "equity")
            equity = None
            if isinstance(equity_value, numbers.Real) and not isinstance(equity_value, bool):
                equity = str(Decimal(str(equity_value)))
            balance_value = market_data._field(info, "balance")
            balance = None
            if isinstance(balance_value, numbers.Real) and not isinstance(balance_value, bool):
                balance = str(Decimal(str(balance_value)))
            leverage_value = market_data._field(info, "leverage")
            leverage = None
            if isinstance(leverage_value, numbers.Integral) and not isinstance(leverage_value, bool):
                leverage = int(leverage_value)
            currency = market_data._safe_optional_text(market_data._field(info, "currency"), 8)
            return {
                "available": login_last4 is not None,
                "login_last4": login_last4,
                "trade_mode": trade_mode,
                "trade_mode_name": ACCOUNT_TRADE_MODE_NAMES.get(trade_mode),
                "trade_allowed": bool(market_data._field(info, "trade_allowed", False)),
                "equity": equity,
                "balance": balance,
                "currency": currency,
                "leverage": leverage,
                "reason_code": None,
            }
        result, reason = self._with_session(body)
        if reason is not None or result is None:
            return {
                "available": False, "login_last4": None, "trade_mode": None,
                "trade_mode_name": None, "trade_allowed": False, "equity": None,
                "balance": None, "currency": None, "leverage": None,
                "reason_code": reason or "ACCOUNT_UNAVAILABLE",
            }
        return result

    def symbol_status(self, symbol):
        def body(provider):
            info = self._call(provider, "symbol_info", symbol)
            if info is None or market_data._field(info, "name") != symbol:
                return None
            visible = market_data._field(info, "visible", True)
            if visible is not True:
                self._call(provider, "symbol_select", symbol, True)
                info = self._call(provider, "symbol_info", symbol)
                if info is None:
                    return None
                visible = market_data._field(info, "visible", True)
            try:
                specification = market_data.normalize_symbol_specification(info, symbol)
            except market_data.MarketDataValidationError:
                return None
            tick_source = self._call(provider, "symbol_info_tick", symbol)
            bid = ask = None
            tick_time = None
            if tick_source is not None:
                try:
                    tick = market_data.normalize_tick(tick_source, specification["point"])
                except market_data.MarketDataValidationError:
                    tick = None
                if tick is not None:
                    bid, ask = tick["bid"], tick["ask"]
                    # ``market_data.normalize_tick`` formats to millisecond
                    # precision (3 fractional digits); this repo's own
                    # ``timeline_data.validate_utc_timestamp`` (used by
                    # every preflight/analysis quote-age check) requires
                    # exactly 6 -- reformatted here so a real broker tick
                    # is never rejected by that stricter, unrelated
                    # convention (found during the R2-013 real-terminal
                    # rehearsal; never triggered by the fake adapter, whose
                    # timestamps already come from ``format_utc``).
                    seconds, millisecond_seconds = market_data.normalized_tick_source_seconds(tick)
                    precise_seconds = millisecond_seconds if millisecond_seconds is not None else seconds
                    tick_time = format_utc(datetime.fromtimestamp(precise_seconds, tz=timezone.utc))
            trade_mode = specification["trade_mode"]
            tradeable = trade_mode not in (_SYMBOL_TRADE_MODE_DISABLED, _SYMBOL_TRADE_MODE_CLOSEONLY)
            return {
                "available": True, "symbol": symbol, "visible": bool(visible),
                "trade_mode": trade_mode, "tradeable": tradeable,
                "bid": str(bid) if bid is not None else None,
                "ask": str(ask) if ask is not None else None,
                "digits": specification["digits"], "point": str(specification["point"]),
                "volume_minimum": str(specification["volume_minimum"]),
                "volume_maximum": str(specification["volume_maximum"]),
                "volume_step": str(specification["volume_step"]),
                "tick_value": str(market_data._field(info, "trade_tick_value", 0)),
                "tick_size": str(market_data._field(info, "trade_tick_size", specification["point"])),
                "stops_level": specification["stops_level"],
                "freeze_level": specification["freeze_level"],
                "tick_time_utc": tick_time,
                "reason_code": None,
            }
        result, reason = self._with_session(body)
        if reason is not None or result is None:
            return {
                "available": False, "symbol": symbol, "visible": False,
                "trade_mode": None, "tradeable": False, "reason_code": reason or "SYMBOL_UNAVAILABLE",
            }
        return result

    def _bar_timeframe_constants(self, provider):
        resolved = {}
        for timeframe, constant_name in _BAR_TIMEFRAME_CONSTANT_NAMES.items():
            try:
                value = getattr(provider, constant_name)
            except AttributeError:
                return None
            if (
                isinstance(value, bool) or not isinstance(value, numbers.Integral)
                or value <= 0 or value > _MAX_PROVIDER_TIMEFRAME_IDENTIFIER
            ):
                return None
            resolved[timeframe] = int(value)
        if len(set(resolved.values())) != len(resolved):
            return None
        return resolved

    @staticmethod
    def _normalize_bar_rows(rows, count):
        """Self-contained OHLC normalization (mirrors
        ``market_data.normalize_bars``'s validation exactly, without that
        function's per-timeframe FORMING-bar bookkeeping, which does not
        apply here since ``start_pos=1`` already excludes the forming
        bar). Returns closed bars oldest-first, or ``None`` if fewer than
        ``count`` valid rows were returned."""
        if rows is None:
            return None
        previous_seconds = None
        normalized = []
        for source in rows:
            try:
                seconds = market_data._finite_number(market_data._field(source, "time"), "MT5_INVALID_BAR_DATA")
                open_value = market_data._finite_number(market_data._field(source, "open"), "MT5_INVALID_BAR_DATA")
                high = market_data._finite_number(market_data._field(source, "high"), "MT5_INVALID_BAR_DATA")
                low = market_data._finite_number(market_data._field(source, "low"), "MT5_INVALID_BAR_DATA")
                close = market_data._finite_number(market_data._field(source, "close"), "MT5_INVALID_BAR_DATA")
            except market_data.MarketDataValidationError:
                return None
            if high < max(open_value, low, close) or low > min(open_value, high, close):
                return None
            if previous_seconds is not None and seconds <= previous_seconds:
                return None
            timestamp_utc, _ = market_data._timestamp_parts(seconds, reason_code="MT5_INVALID_BAR_DATA")
            normalized.append({
                "timestamp_utc": timestamp_utc, "open": open_value, "high": high,
                "low": low, "close": close, "bar_state": "CLOSED",
            })
            previous_seconds = seconds
        if len(normalized) < count:
            return None
        return normalized

    def fetch_completed_bars(self, symbol, timeframe, count):
        """Server-authoritative closed-bar fetch (contract Section 5/8.1):
        ``start_pos=1`` always skips the currently-forming bar, so the
        returned ``count`` bars are all closed -- never the current
        unfinished candle."""
        if timeframe not in BAR_TIMEFRAMES:
            return {"available": False, "bars": [], "reason_code": "HISTORY_INSUFFICIENT"}
        if not isinstance(count, numbers.Integral) or isinstance(count, bool) or not 1 <= count <= MAX_BAR_FETCH_COUNT:
            return {"available": False, "bars": [], "reason_code": "HISTORY_INSUFFICIENT"}

        def body(provider):
            constants = self._bar_timeframe_constants(provider)
            if constants is None:
                return None
            rows = self._call(provider, "copy_rates_from_pos", symbol, constants[timeframe], 1, count)
            return self._normalize_bar_rows(rows, count)
        result, reason = self._with_session(body)
        if reason is not None or result is None:
            return {"available": False, "bars": [], "reason_code": "HISTORY_INSUFFICIENT"}
        return {"available": True, "bars": result, "reason_code": None}

    def discover_symbols(self, canonical_instrument):
        aliases = INSTRUMENT_ALIASES.get(canonical_instrument, ())

        def body(provider):
            symbols = self._call(provider, "symbols_get") or ()
            matches = []
            for entry in symbols:
                name = market_data._field(entry, "name")
                if not isinstance(name, str):
                    continue
                normalized = name.lower()
                if any(alias in normalized for alias in aliases):
                    matches.append(name)
            return sorted(set(matches))
        result, reason = self._with_session(body)
        if reason is not None or result is None:
            return []
        return result

    def _owned(self, provider_method, magic_number):
        def body(provider):
            items = self._call(provider, provider_method) or ()
            owned = []
            for item in items:
                magic = market_data._field(item, "magic")
                if isinstance(magic, numbers.Integral) and int(magic) == magic_number:
                    owned.append({
                        "ticket": int(market_data._field(item, "ticket", 0)),
                        "symbol": market_data._field(item, "symbol"),
                        "magic": int(magic),
                        "comment": market_data._safe_optional_text(market_data._field(item, "comment"), 32),
                    })
            return owned
        result, reason = self._with_session(body)
        if reason is not None or result is None:
            return []
        return result

    def owned_orders(self, magic_number):
        return self._owned("orders_get", magic_number)

    def owned_positions(self, magic_number):
        return self._owned("positions_get", magic_number)

    def order_check(self, request):
        def body(provider):
            response = self._call(provider, "order_check", _build_mt5_request(request))
            return _normalize_check_response(response, self._now())
        result, reason = self._with_session(body)
        if reason is not None:
            return {"outcome": "MALFORMED", "retcode": None, "comment": reason, "checked_at_utc": self._now()}
        return result

    def order_send(self, request):
        def body(provider):
            response = self._call(provider, "order_send", _build_mt5_request(request))
            return _normalize_send_response(response, self._now())
        result, reason = self._with_session(body)
        if reason is not None:
            return {
                "outcome": "UNCERTAIN", "retcode": None, "ticket": None, "deal": None,
                "comment": reason, "sent_at_utc": self._now(),
            }
        return result


def _build_mt5_request(request):
    return {
        "action": request.get("action"), "symbol": request.get("symbol"),
        "volume": request.get("volume"), "type": request.get("type"),
        "price": request.get("price"), "sl": request.get("sl"), "tp": request.get("tp"),
        "deviation": request.get("deviation"), "type_time": request.get("type_time"),
        "expiration": request.get("expiration"), "type_filling": request.get("type_filling"),
        "magic": request.get("magic"), "comment": request.get("comment"),
    }


def _normalize_check_response(response, checked_at_utc):
    if response is None:
        return {"outcome": "MALFORMED", "retcode": None, "comment": "no response", "checked_at_utc": checked_at_utc}
    retcode = market_data._field(response, "retcode")
    if not isinstance(retcode, numbers.Integral) or isinstance(retcode, bool):
        return {"outcome": "MALFORMED", "retcode": None, "comment": "invalid retcode", "checked_at_utc": checked_at_utc}
    retcode = int(retcode)
    comment = market_data._safe_optional_text(market_data._field(response, "comment"), 64) or ""
    outcome = "PASSED" if retcode == 0 else "FAILED"
    return {"outcome": outcome, "retcode": retcode, "comment": comment, "checked_at_utc": checked_at_utc}


_DONE_RETCODES = frozenset((10008, 10009))


def _normalize_send_response(response, sent_at_utc):
    if response is None:
        return {
            "outcome": "UNCERTAIN", "retcode": None, "ticket": None, "deal": None,
            "comment": "no response", "sent_at_utc": sent_at_utc,
        }
    retcode = market_data._field(response, "retcode")
    if not isinstance(retcode, numbers.Integral) or isinstance(retcode, bool):
        return {
            "outcome": "MALFORMED", "retcode": None, "ticket": None, "deal": None,
            "comment": "invalid retcode", "sent_at_utc": sent_at_utc,
        }
    retcode = int(retcode)
    comment = market_data._safe_optional_text(market_data._field(response, "comment"), 64) or ""
    if retcode not in _DONE_RETCODES:
        return {
            "outcome": "REJECTED", "retcode": retcode, "ticket": None, "deal": None,
            "comment": comment, "sent_at_utc": sent_at_utc,
        }
    order_value = market_data._field(response, "order")
    deal_value = market_data._field(response, "deal")
    volume_value = market_data._field(response, "volume")
    ticket = int(order_value) if isinstance(order_value, numbers.Integral) and not isinstance(order_value, bool) else None
    deal = int(deal_value) if isinstance(deal_value, numbers.Integral) and not isinstance(deal_value, bool) else None
    if ticket is None or deal is None or not isinstance(volume_value, numbers.Real) or isinstance(volume_value, bool) or volume_value <= 0:
        return {
            "outcome": "MALFORMED", "retcode": retcode, "ticket": None, "deal": None,
            "comment": "incomplete fill fields", "sent_at_utc": sent_at_utc,
        }
    return {
        "outcome": "FILLED", "retcode": retcode, "ticket": ticket, "deal": deal,
        "volume_filled": str(volume_value), "comment": comment, "sent_at_utc": sent_at_utc,
    }


# --------------------------------------------------------------------------
# Twenty-check preflight (contract Section 6)
# --------------------------------------------------------------------------

PREFLIGHT_CHECK_IDS = (
    "MT5_PACKAGE_IMPORTS", "TERMINAL_INITIALIZES", "TERMINAL_CONNECTED",
    "ACCOUNT_INFO_READABLE", "ACCOUNT_IS_DEMO", "ACCOUNT_NOT_CONTEST_OR_REAL",
    "ACCOUNT_TRADE_ALLOWED", "ALGO_TRADING_ENABLED", "SYMBOL_EXISTS",
    "SYMBOL_VISIBLE_OR_SELECTABLE", "QUOTE_FRESH", "SESSION_OPEN",
    "VOLUME_CONSTRAINTS_KNOWN", "DIGITS_POINT_KNOWN", "STOP_FREEZE_LEVEL_KNOWN",
    "SPREAD_WITHIN_BOUND", "EQUITY_POSITIVE", "DAILY_LOSS_DRAWDOWN_OK",
    "NOT_EMERGENCY_STOPPED", "NO_MANUAL_EVENT_RISK_BLOCK",
)


def run_preflight(
    adapter, broker_symbol, max_spread_points, is_emergency_stopped,
    event_risk_blocked, daily_loss_ok, session_open, quote_age_seconds,
    now=None,
):
    """Run all twenty checks in order; stop and report the first failure.
    Every result (pass or fail) is returned for full audit -- the caller
    decides how to record it (contract Section 6/14.1: preflight itself is
    read-only and is recorded only as part of the cycle that consumes it).
    """
    results = []

    def record(check_id, passed, detail=None):
        results.append({"check_id": check_id, "passed": passed, "detail": detail})
        return passed

    dependency = adapter.dependency_status()
    if not record("MT5_PACKAGE_IMPORTS", dependency["available"], dependency.get("reason_code")):
        return _preflight_result(results, "SCALPING_MT5_DEPENDENCY_MISSING")

    terminal = adapter.terminal_status()
    if not record("TERMINAL_INITIALIZES", terminal.get("connected") is not None):
        return _preflight_result(results, "SCALPING_TERMINAL_UNAVAILABLE")
    if not record("TERMINAL_CONNECTED", bool(terminal.get("connected"))):
        return _preflight_result(results, "SCALPING_TERMINAL_NOT_CONNECTED")

    account = adapter.account_status()
    if not record("ACCOUNT_INFO_READABLE", bool(account.get("available"))):
        return _preflight_result(results, "SCALPING_ACCOUNT_UNAVAILABLE")
    if not record("ACCOUNT_IS_DEMO", account.get("trade_mode") == ACCOUNT_TRADE_MODE_DEMO):
        return _preflight_result(results, "SCALPING_ACCOUNT_NOT_PROVEN_DEMO")
    if not record(
        "ACCOUNT_NOT_CONTEST_OR_REAL",
        account.get("trade_mode") == ACCOUNT_TRADE_MODE_DEMO
        and account.get("trade_mode_name") == "DEMO",
    ):
        return _preflight_result(results, "SCALPING_ACCOUNT_NOT_PROVEN_DEMO")
    if not record("ACCOUNT_TRADE_ALLOWED", bool(account.get("trade_allowed"))):
        return _preflight_result(results, "SCALPING_TRADE_NOT_ALLOWED")
    if not record("ALGO_TRADING_ENABLED", bool(terminal.get("trade_allowed"))):
        return _preflight_result(results, "SCALPING_ALGO_TRADING_DISABLED")

    symbol = adapter.symbol_status(broker_symbol)
    if not record("SYMBOL_EXISTS", bool(symbol.get("available"))):
        return _preflight_result(results, "SCALPING_SYMBOL_UNAVAILABLE")
    if not record("SYMBOL_VISIBLE_OR_SELECTABLE", bool(symbol.get("visible"))):
        return _preflight_result(results, "SCALPING_SYMBOL_NOT_VISIBLE")
    if not record("QUOTE_FRESH", quote_age_seconds is not None and quote_age_seconds <= MAX_QUOTE_STALENESS_SECONDS):
        return _preflight_result(results, "SCALPING_QUOTE_STALE")
    if not record("SESSION_OPEN", bool(session_open) and bool(symbol.get("tradeable"))):
        return _preflight_result(results, "SCALPING_MARKET_CLOSED")
    if not record(
        "VOLUME_CONSTRAINTS_KNOWN",
        symbol.get("volume_minimum") is not None and symbol.get("volume_maximum") is not None
        and symbol.get("volume_step") is not None,
    ):
        return _preflight_result(results, "SCALPING_VOLUME_CONSTRAINTS_UNKNOWN")
    if not record("DIGITS_POINT_KNOWN", symbol.get("digits") is not None and symbol.get("point") is not None):
        return _preflight_result(results, "SCALPING_SYMBOL_METADATA_UNKNOWN")
    if not record(
        "STOP_FREEZE_LEVEL_KNOWN",
        symbol.get("stops_level") is not None and symbol.get("freeze_level") is not None,
    ):
        return _preflight_result(results, "SCALPING_SYMBOL_METADATA_UNKNOWN")

    spread_points = None
    if symbol.get("bid") is not None and symbol.get("ask") is not None and symbol.get("point"):
        spread_points = (Decimal(symbol["ask"]) - Decimal(symbol["bid"])) / Decimal(symbol["point"])
    if not record(
        "SPREAD_WITHIN_BOUND",
        spread_points is not None and spread_points <= Decimal(str(max_spread_points)),
    ):
        return _preflight_result(results, "SCALPING_SPREAD_EXCEEDS_BOUND")

    if not record("EQUITY_POSITIVE", account.get("equity") is not None and Decimal(account["equity"]) > 0):
        return _preflight_result(results, "SCALPING_EQUITY_NOT_POSITIVE")
    if not record("DAILY_LOSS_DRAWDOWN_OK", bool(daily_loss_ok)):
        return _preflight_result(results, "SCALPING_DAILY_LIMIT_BREACHED")
    if not record("NOT_EMERGENCY_STOPPED", not is_emergency_stopped):
        return _preflight_result(results, "SCALPING_EMERGENCY_STOP_ACTIVE")
    if not record("NO_MANUAL_EVENT_RISK_BLOCK", not event_risk_blocked):
        return _preflight_result(results, "SCALPING_MANUAL_EVENT_RISK_BLOCK")

    return _preflight_result(results, None)


def _preflight_result(results, blocking_reason_code):
    return {
        "passed": blocking_reason_code is None,
        "blocking_reason_code": blocking_reason_code,
        "checks": results,
    }


__all__ = (
    "ACCOUNT_TRADE_MODE_DEMO",
    "ACCOUNT_TRADE_MODE_NAMES",
    "BAR_TIMEFRAMES",
    "DisabledScalpingAdapter",
    "FakeScalpingAdapter",
    "INSTRUMENT_ALIASES",
    "MAX_BAR_FETCH_COUNT",
    "MAX_QUOTE_STALENESS_SECONDS",
    "PREFLIGHT_CHECK_IDS",
    "PROVIDER_METHOD_ALLOWLIST",
    "RealScalpingMT5Adapter",
    "ScalpingMT5AdapterError",
    "disabled_adapter",
    "fake_adapter",
    "run_preflight",
)
