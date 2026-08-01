"""Three-tier MT5 execution-adapter boundary (TRL-R2-007, Phase 5).

Mirrors ``mt5_connector.py``'s house style for the read-only connector:
lazy import, an allowlist of provider method names, a single serializing
lock, strict response normalization, and an always-run shutdown. This
module never makes a governance decision (account/symbol/risk approval) —
it only talks to the broker and returns strictly normalized documents.
``mt5_execution_service.py`` is the sole authority that decides whether a
normalized document satisfies Phase 5's preflight requirements.

Three tiers, selected only by ``mt5_execution_service._adapter_for_mode``:

* ``DisabledExecutionAdapter`` — the default. Never imports MetaTrader5,
  never opens a socket, every operation fails closed with
  ``ADAPTER_DISABLED``.
* ``FakeExecutionAdapter`` — deterministic, in-memory, scriptable. Used by
  every automated test; makes no network call and touches no terminal.
* ``RealMT5ExecutionAdapter`` — imports the optional ``MetaTrader5``
  package lazily, only inside a method call, never at import time or at
  construction time. Every provider call goes through the same
  allowlist + lock pattern as ``LocalMT5ReadOnlyConnector``, and every
  method independently initializes and shuts down the terminal session
  (no session is held open between calls), so a caller can never leave a
  broker connection dangling.
"""

import importlib
import numbers
import threading
from copy import deepcopy
from datetime import datetime, timezone

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
    "order_check",
    "order_send",
))
_PROVIDER_SESSION_LOCK = threading.Lock()

# Standard, publicly documented MetaTrader5/MQL5 numeric constants. These
# are stable API values, not broker- or account-specific secrets. Kept as
# local constants (never imported from the optional package) so every
# normalization function works identically whether or not the real
# package is installed.
_SYMBOL_TRADE_MODE_DISABLED = 0
_SYMBOL_TRADE_MODE_CLOSEONLY = 3
_SYMBOL_TRADE_MODE_FULL = 4
_ACCOUNT_TRADE_MODE_DEMO = 0
_ACCOUNT_TRADE_MODE_CONTEST = 1
_ACCOUNT_TRADE_MODE_REAL = 2
_FILLING_FOK_BIT = 1
_FILLING_IOC_BIT = 2

ACCOUNT_TRADE_MODE_DEMO = _ACCOUNT_TRADE_MODE_DEMO
ACCOUNT_TRADE_MODE_NAMES = {
    _ACCOUNT_TRADE_MODE_DEMO: "DEMO",
    _ACCOUNT_TRADE_MODE_CONTEST: "CONTEST",
    _ACCOUNT_TRADE_MODE_REAL: "REAL",
}


def _now(clock):
    return format_utc(datetime.now(timezone.utc) if clock is None else clock())


class DisabledExecutionAdapter:
    """The default adapter. No import, no connection, every call denied."""

    tier = "DISABLED"

    def dependency_status(self):
        return {"available": False, "reason_code": "ADAPTER_DISABLED"}

    def terminal_status(self):
        return {
            "connected": False, "trade_allowed": False, "path": None,
            "build": None, "reason_code": "ADAPTER_DISABLED",
        }

    def account_status(self):
        return {
            "available": False, "login": None, "company": None, "server": None,
            "currency": None, "trade_mode": None, "trade_mode_name": None,
            "trade_allowed": False, "trade_expert": False,
            "margin_level": None, "reason_code": "ADAPTER_DISABLED",
        }

    def symbol_status(self, symbol):
        return {
            "available": False, "symbol": symbol, "visible": False,
            "trade_mode": None, "tradeable": False, "reason_code": "ADAPTER_DISABLED",
        }

    def order_check(self, request):
        return {
            "outcome": "FAILED", "retcode": None,
            "comment": "ADAPTER_DISABLED", "checked_at_utc": _now(None),
        }

    def order_send(self, request):
        return {
            "outcome": "REJECTED", "retcode": None, "ticket": None, "deal": None,
            "position": None, "volume_filled": None,
            "comment": "ADAPTER_DISABLED", "sent_at_utc": _now(None),
        }


def disabled_adapter():
    return DisabledExecutionAdapter()


class FakeExecutionAdapter:
    """Deterministic in-memory adapter for automated tests. No network."""

    tier = "FAKE"

    def __init__(self, clock=None):
        self._clock = clock
        self.calls = []
        self.dependency = {"available": True, "reason_code": None}
        self.terminal = {
            "connected": True, "trade_allowed": True,
            "path": "C:\\FAKE\\terminal64.exe", "build": 4100, "reason_code": None,
        }
        self.account = {
            "available": True, "login": 900100100, "company": "Fake Demo Broker Ltd",
            "server": "FakeDemo-Server", "currency": "USD",
            "trade_mode": _ACCOUNT_TRADE_MODE_DEMO, "trade_mode_name": "DEMO",
            "trade_allowed": True, "trade_expert": True,
            "margin_level": "5000", "reason_code": None,
        }
        self.symbols = {}
        self._check_queue = []
        self._send_queue = []

    def _record(self, operation, request):
        self.calls.append((operation, deepcopy(request)))

    def set_symbol(self, symbol, **fields):
        base = {
            "available": True, "symbol": symbol, "visible": True,
            "trade_mode": _SYMBOL_TRADE_MODE_FULL, "tradeable": True,
            "bid": "1900.00", "ask": "1900.20", "digits": 2, "point": "0.01",
            "volume_minimum": "0.01", "volume_maximum": "100", "volume_step": "0.01",
            "stops_level": 50, "freeze_level": 0, "filling_modes": ("FOK", "IOC"),
            "tick_time_utc": _now(self._clock), "reason_code": None,
        }
        base.update(fields)
        self.symbols[symbol] = base

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

    def order_check(self, request):
        self._record("order_check", request)
        if self._check_queue:
            return self._check_queue.pop(0)
        return {
            "outcome": "PASSED", "retcode": 0,
            "comment": "fake order_check ok", "checked_at_utc": _now(self._clock),
        }

    def order_send(self, request):
        self._record("order_send", request)
        if self._send_queue:
            return self._send_queue.pop(0)
        return {
            "outcome": "FILLED", "retcode": 10009, "ticket": 555001,
            "deal": 555002, "position": 555003, "volume_filled": request.get("volume"),
            "comment": "fake order_send filled", "sent_at_utc": _now(self._clock),
        }


def fake_adapter(clock=None):
    return FakeExecutionAdapter(clock=clock)


class RealMT5ExecutionAdapter:
    """Isolated boundary to the optional real ``MetaTrader5`` package.

    Never imports the package at module or construction time. Every
    method independently ``initialize()``s and ``shutdown()``s within the
    single provider-session lock, mirroring ``LocalMT5ReadOnlyConnector``,
    so no broker session is ever held open between calls and a caller can
    never forget to disconnect.
    """

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
            raise RuntimeError("provider operation is not allowlisted")
        return getattr(provider, operation)(*args, **kwargs)

    def _now(self):
        return _now(self._clock)

    def dependency_status(self):
        provider = self._provider_or_import()
        if provider is None:
            return {"available": False, "reason_code": "MT5_DEPENDENCY_MISSING"}
        return {"available": True, "reason_code": None}

    def _with_session(self, body):
        """Initialize, run ``body(provider)``, always shut down. Returns
        ``body``'s result, or a controlled failure document if
        initialize/shutdown itself fails."""
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
            path = market_data._safe_optional_text(market_data._field(info, "path"), 512)
            build_value = market_data._field(info, "build")
            build = None
            if isinstance(build_value, numbers.Integral) and not isinstance(build_value, bool):
                build = int(build_value)
            trade_allowed = bool(market_data._field(info, "trade_allowed", False))
            connected = bool(market_data._field(info, "connected", False))
            return {
                "connected": connected, "trade_allowed": trade_allowed,
                "path": path, "build": build, "reason_code": None,
            }
        result, reason = self._with_session(body)
        if reason is not None:
            return {
                "connected": False, "trade_allowed": False, "path": None,
                "build": None, "reason_code": reason,
            }
        if result is None:
            return {
                "connected": False, "trade_allowed": False, "path": None,
                "build": None, "reason_code": "TERMINAL_UNAVAILABLE",
            }
        return result

    def account_status(self):
        def body(provider):
            info = self._call(provider, "account_info")
            if info is None:
                return None
            login_value = market_data._field(info, "login")
            login = None
            if isinstance(login_value, numbers.Integral) and not isinstance(login_value, bool) and login_value > 0:
                login = int(login_value)
            trade_mode_value = market_data._field(info, "trade_mode")
            trade_mode = None
            if isinstance(trade_mode_value, numbers.Integral) and not isinstance(trade_mode_value, bool):
                trade_mode = int(trade_mode_value)
            margin_level_value = market_data._field(info, "margin_level")
            margin_level = None
            if isinstance(margin_level_value, numbers.Real) and not isinstance(margin_level_value, bool):
                margin_level = str(margin_level_value)
            return {
                "available": login is not None,
                "login": login,
                "company": market_data._safe_optional_text(market_data._field(info, "company"), 128),
                "server": market_data._safe_optional_text(market_data._field(info, "server"), 128),
                "currency": market_data._safe_optional_text(market_data._field(info, "currency"), 16),
                "trade_mode": trade_mode,
                "trade_mode_name": ACCOUNT_TRADE_MODE_NAMES.get(trade_mode),
                "trade_allowed": bool(market_data._field(info, "trade_allowed", False)),
                "trade_expert": bool(market_data._field(info, "trade_expert", False)),
                "margin_level": margin_level,
                "reason_code": None,
            }
        result, reason = self._with_session(body)
        if reason is not None or result is None:
            return {
                "available": False, "login": None, "company": None, "server": None,
                "currency": None, "trade_mode": None, "trade_mode_name": None,
                "trade_allowed": False, "trade_expert": False, "margin_level": None,
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
                    tick_time = tick["source_timestamp_utc"]
            filling_flags_value = market_data._field(info, "filling_mode", 0)
            filling_flags = filling_flags_value if isinstance(filling_flags_value, int) else 0
            filling_modes = []
            if filling_flags & _FILLING_FOK_BIT:
                filling_modes.append("FOK")
            if filling_flags & _FILLING_IOC_BIT:
                filling_modes.append("IOC")
            filling_modes.append("RETURN")
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
                "stops_level": specification["stops_level"],
                "freeze_level": specification["freeze_level"],
                "filling_modes": tuple(filling_modes),
                "tick_time_utc": tick_time,
                "reason_code": None,
            }
        result, reason = self._with_session(body)
        if reason is not None or result is None:
            return {
                "available": False, "symbol": symbol, "visible": False,
                "trade_mode": None, "tradeable": False,
                "reason_code": reason or "SYMBOL_UNAVAILABLE",
            }
        return result

    def order_check(self, request):
        def body(provider):
            mt5_request = _build_mt5_request(request)
            response = self._call(provider, "order_check", mt5_request)
            return _normalize_check_response(response, self._now())
        result, reason = self._with_session(body)
        if reason is not None:
            return {
                "outcome": "MALFORMED", "retcode": None,
                "comment": reason, "checked_at_utc": self._now(),
            }
        return result

    def order_send(self, request):
        def body(provider):
            mt5_request = _build_mt5_request(request)
            response = self._call(provider, "order_send", mt5_request)
            return _normalize_send_response(response, self._now())
        result, reason = self._with_session(body)
        if reason is not None:
            return {
                "outcome": "UNCERTAIN", "retcode": None, "ticket": None, "deal": None,
                "position": None, "volume_filled": None,
                "comment": reason, "sent_at_utc": self._now(),
            }
        return result


def _build_mt5_request(request):
    """A minimal, allowlisted-field broker request dict. Never includes a
    credential; every value here already passed the service layer's own
    preflight and is being handed to the terminal unchanged."""
    return {
        "action": request.get("action"),
        "symbol": request.get("symbol"),
        "volume": request.get("volume"),
        "type": request.get("type"),
        "price": request.get("price"),
        "sl": request.get("sl"),
        "deviation": request.get("deviation"),
        "type_time": request.get("type_time"),
        "type_filling": request.get("type_filling"),
        "magic": request.get("magic"),
        "comment": request.get("comment"),
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


_DONE_RETCODES = frozenset((10008, 10009))  # TRADE_RETCODE_PLACED, TRADE_RETCODE_DONE


def _normalize_send_response(response, sent_at_utc):
    if response is None:
        return {
            "outcome": "UNCERTAIN", "retcode": None, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": "no response", "sent_at_utc": sent_at_utc,
        }
    retcode = market_data._field(response, "retcode")
    if not isinstance(retcode, numbers.Integral) or isinstance(retcode, bool):
        return {
            "outcome": "MALFORMED", "retcode": None, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": "invalid retcode", "sent_at_utc": sent_at_utc,
        }
    retcode = int(retcode)
    comment = market_data._safe_optional_text(market_data._field(response, "comment"), 64) or ""
    if retcode not in _DONE_RETCODES:
        # An order object being non-null is never itself proof of success.
        return {
            "outcome": "REJECTED", "retcode": retcode, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": comment, "sent_at_utc": sent_at_utc,
        }
    order_value = market_data._field(response, "order")
    deal_value = market_data._field(response, "deal")
    volume_value = market_data._field(response, "volume")
    ticket = int(order_value) if isinstance(order_value, numbers.Integral) and not isinstance(order_value, bool) else None
    deal = int(deal_value) if isinstance(deal_value, numbers.Integral) and not isinstance(deal_value, bool) else None
    if ticket is None or deal is None or not isinstance(volume_value, numbers.Real) or isinstance(volume_value, bool) or volume_value <= 0:
        return {
            "outcome": "MALFORMED", "retcode": retcode, "ticket": None, "deal": None,
            "position": None, "volume_filled": None, "comment": "incomplete fill fields", "sent_at_utc": sent_at_utc,
        }
    return {
        "outcome": "FILLED", "retcode": retcode, "ticket": ticket, "deal": deal,
        "position": ticket, "volume_filled": str(volume_value), "comment": comment, "sent_at_utc": sent_at_utc,
    }


__all__ = (
    "DisabledExecutionAdapter",
    "FakeExecutionAdapter",
    "RealMT5ExecutionAdapter",
    "disabled_adapter",
    "fake_adapter",
)
