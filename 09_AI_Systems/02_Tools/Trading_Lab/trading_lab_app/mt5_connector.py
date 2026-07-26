"""Allowlisted, serialized boundary to an optional local MetaTrader 5 provider."""

import importlib
import numbers
import threading
from datetime import datetime, timezone

from . import market_data


PROVIDER_METHOD_ALLOWLIST = frozenset((
    "initialize",
    "shutdown",
    "last_error",
    "symbols_get",
    "symbol_info",
    "symbol_info_tick",
    "copy_rates_from_pos",
))
PROVIDER_CONSTANT_ALLOWLIST = frozenset((
    "TIMEFRAME_M1",
    "TIMEFRAME_M5",
    "TIMEFRAME_H4",
    "TIMEFRAME_D1",
))
_TIMEFRAME_CONSTANT_NAMES = {
    "M1": "TIMEFRAME_M1",
    "M5": "TIMEFRAME_M5",
    "H4": "TIMEFRAME_H4",
    "D1": "TIMEFRAME_D1",
}
MAX_PROVIDER_TIMEFRAME_IDENTIFIER = (2 ** 31) - 1
_PROVIDER_SESSION_LOCK = threading.Lock()


class LocalMT5ReadOnlyConnector:
    """Retrieve one fail-closed snapshot from an already authenticated terminal."""

    def __init__(self, provider=None, clock=None):
        self._provider = provider
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._provider_lock = _PROVIDER_SESSION_LOCK

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
        method = getattr(provider, operation)
        return method(*args, **kwargs)

    @staticmethod
    def _timeframe_constants(provider):
        resolved = {}
        for timeframe, constant_name in _TIMEFRAME_CONSTANT_NAMES.items():
            if constant_name not in PROVIDER_CONSTANT_ALLOWLIST:
                raise market_data.MarketDataValidationError("MT5_PROVIDER_INCOMPATIBLE")
            try:
                value = getattr(provider, constant_name)
            except AttributeError:
                raise market_data.MarketDataValidationError("MT5_PROVIDER_INCOMPATIBLE")
            if (
                isinstance(value, bool)
                or not isinstance(value, numbers.Integral)
                or value <= 0
                or value > MAX_PROVIDER_TIMEFRAME_IDENTIFIER
            ):
                raise market_data.MarketDataValidationError("MT5_PROVIDER_INCOMPATIBLE")
            resolved[timeframe] = int(value)
        if len(set(resolved.values())) != len(resolved):
            raise market_data.MarketDataValidationError("MT5_PROVIDER_INCOMPATIBLE")
        return resolved

    @classmethod
    def _last_error_code(cls, provider):
        try:
            value = cls._call(provider, "last_error")
        except Exception:
            return None
        if type(value) in (tuple, list) and value and type(value[0]) is int:
            return value[0]
        if type(value) is int:
            return value
        return None

    @staticmethod
    def _failure(
        requested_symbol,
        timeframes,
        retrieval_time,
        status,
        reason_code=None,
        candidates=None,
        provider_error_code=None,
        diagnostic=None,
    ):
        result = market_data.base_snapshot(
            requested_symbol,
            timeframes,
            retrieval_time,
            status,
            reason_code or status,
        )
        result["candidate_symbols"] = list(candidates or ())
        result["data_quality"]["provider_error_code"] = provider_error_code
        if diagnostic:
            result["data_quality"]["diagnostic"] = diagnostic
        return result

    def snapshot(
        self,
        requested_symbol,
        timeframes=market_data.DEFAULT_TIMEFRAMES,
        bar_count=500,
        timeout_ms=market_data.DEFAULT_INITIALIZATION_TIMEOUT_MS,
        stale_threshold_seconds=market_data.DEFAULT_STALE_THRESHOLD_SECONDS,
    ):
        requested_symbol = market_data.validate_symbol(requested_symbol)
        timeframes = market_data.validate_timeframes(timeframes)
        bar_count = market_data.validate_bar_count(bar_count)
        timeout_ms = market_data.validate_timeout_ms(timeout_ms)
        if type(stale_threshold_seconds) is not int or stale_threshold_seconds <= 0:
            raise ValueError("stale threshold must be a positive integer")
        request_started_time = market_data.utc_now(self._clock)
        provider = self._provider_or_import()
        if provider is None:
            return self._failure(
                requested_symbol,
                timeframes,
                request_started_time,
                "MT5_DEPENDENCY_MISSING",
                diagnostic=(
                    "The optional MetaTrader5 package is not installed in this local Python environment."
                ),
            )

        with self._provider_lock:
            initialized = False
            result = None
            retrieval_time = request_started_time
            try:
                initialized = bool(self._call(provider, "initialize", timeout=timeout_ms))
                if not initialized:
                    provider_error_code = self._last_error_code(provider)
                    retrieval_time = market_data.utc_now(self._clock)
                    result = self._failure(
                        requested_symbol,
                        timeframes,
                        retrieval_time,
                        "MT5_INITIALIZATION_FAILED",
                        provider_error_code=provider_error_code,
                        diagnostic=(
                            "The local MT5 terminal session could not be initialized; no market data was used."
                        ),
                    )
                else:
                    result, retrieval_time = self._snapshot_initialized(
                        provider,
                        requested_symbol,
                        timeframes,
                        bar_count,
                        stale_threshold_seconds,
                    )
            except market_data.MarketDataValidationError as error:
                retrieval_time = market_data.utc_now(self._clock)
                result = self._failure(
                    requested_symbol,
                    timeframes,
                    retrieval_time,
                    error.reason_code,
                    diagnostic=(
                        "The local MT5 provider is incompatible with the required read-only interface; provider details were withheld."
                        if error.reason_code == "MT5_PROVIDER_INCOMPATIBLE"
                        else "The local MT5 provider returned data that failed strict validation; no partial bar collection was accepted."
                    ),
                )
            except Exception:
                provider_error_code = self._last_error_code(provider)
                retrieval_time = market_data.utc_now(self._clock)
                result = self._failure(
                    requested_symbol,
                    timeframes,
                    retrieval_time,
                    "MT5_PROVIDER_ERROR",
                    provider_error_code=provider_error_code,
                    diagnostic=(
                        "A local MT5 provider operation failed. Provider details were withheld from the browser."
                    ),
                )
            finally:
                if initialized:
                    try:
                        self._call(provider, "shutdown")
                    except Exception:
                        result = self._failure(
                            requested_symbol,
                            timeframes,
                            retrieval_time,
                            "MT5_PROVIDER_ERROR",
                            diagnostic=(
                                "The local MT5 integration session did not close cleanly; snapshot data was withheld."
                            ),
                        )
            return result

    def _snapshot_initialized(
        self,
        provider,
        requested_symbol,
        timeframes,
        bar_count,
        stale_threshold_seconds,
    ):
        source_specification = self._call(provider, "symbol_info", requested_symbol)
        reported_name = market_data._field(source_specification, "name")
        if source_specification is None or reported_name != requested_symbol:
            provider_symbols = self._call(provider, "symbols_get")
            _, candidates = market_data.discover_symbols(
                requested_symbol, provider_symbols
            )
            retrieval_time = market_data.utc_now(self._clock)
            status = "MT5_SYMBOL_AMBIGUOUS" if len(candidates) > 1 else "MT5_SYMBOL_NOT_FOUND"
            return self._failure(
                requested_symbol,
                timeframes,
                retrieval_time,
                status,
                candidates=candidates,
                diagnostic=(
                    "Choose an exact visible broker symbol on a later launch; candidates were not selected."
                    if candidates
                    else "The exact symbol was not found. Make it visible in MT5 Market Watch and relaunch."
                ),
            ), retrieval_time

        exact = requested_symbol
        if market_data._field(source_specification, "visible", True) is not True:
            retrieval_time = market_data.utc_now(self._clock)
            return self._failure(
                requested_symbol,
                timeframes,
                retrieval_time,
                "MT5_SYMBOL_NOT_FOUND",
                reason_code="MT5_SYMBOL_NOT_VISIBLE",
                diagnostic=(
                    "The exact broker symbol is unavailable. Make it visible in MT5 Market Watch and relaunch."
                ),
            ), retrieval_time
        specification = market_data.normalize_symbol_specification(
            source_specification, exact
        )
        source_tick = self._call(provider, "symbol_info_tick", exact)
        if source_tick is None:
            provider_error_code = self._last_error_code(provider)
            retrieval_time = market_data.utc_now(self._clock)
            return self._failure(
                requested_symbol,
                timeframes,
                retrieval_time,
                "MT5_TICK_UNAVAILABLE",
                provider_error_code=provider_error_code,
                diagnostic="No broker tick was available; no price was fabricated.",
            ), retrieval_time

        provider_timeframes = self._timeframe_constants(provider)
        source_series = {}
        for timeframe in timeframes:
            source_series[timeframe] = self._call(
                provider,
                "copy_rates_from_pos",
                exact,
                provider_timeframes[timeframe],
                0,
                bar_count,
            )
        retrieval_time = market_data.utc_now(self._clock)

        try:
            tick = market_data.normalize_tick(source_tick, specification["point"])
            series = {}
            for timeframe, source_rows in source_series.items():
                series[timeframe] = market_data.normalize_bars(
                    source_rows, timeframe, retrieval_time
                )

            empty_timeframes = [
                timeframe for timeframe, document in series.items()
                if document["status"] == "UNAVAILABLE"
            ]
            source_seconds, source_milliseconds = market_data.normalized_tick_source_seconds(tick)
            future_reference = max(
                value for value in (source_seconds, source_milliseconds)
                if value is not None
            )
            future_skew = future_reference - retrieval_time.timestamp()
            if future_skew > market_data.MAX_FUTURE_TICK_SKEW_SECONDS:
                raise market_data.MarketDataValidationError("MT5_TICK_CLOCK_SKEW")
        except market_data.MarketDataValidationError as error:
            return self._failure(
                requested_symbol,
                timeframes,
                retrieval_time,
                error.reason_code,
                diagnostic=(
                    "The local MT5 provider returned data that failed strict validation; no partial bar collection was accepted."
                ),
            ), retrieval_time
        if future_skew > 0:
            tick_age = 0.0
            freshness = "CLOCK_SKEW_WITHIN_TOLERANCE"
            future_tick_skew = future_skew
        else:
            tick_age = retrieval_time.timestamp() - source_seconds
            freshness = "STALE_BY_THRESHOLD" if tick_age > stale_threshold_seconds else "FRESH"
            future_tick_skew = 0.0
        reason_code = "MT5_READ_ONLY_SNAPSHOT_VALID"
        snapshot_valid = True
        diagnostic = "The read-only local MT5 snapshot passed validation."
        if empty_timeframes:
            reason_code = "MT5_BAR_DATA_UNAVAILABLE"
            snapshot_valid = False
            diagnostic = "One or more requested broker timeframes returned no bars; no bars were invented."
        elif freshness == "STALE_BY_THRESHOLD":
            reason_code = "MT5_STALE"
            diagnostic = (
                "The quote is stale by threshold; the market session is unknown, so this is not treated as a broker failure."
            )
        elif freshness == "CLOCK_SKEW_WITHIN_TOLERANCE":
            diagnostic = (
                "The source tick is slightly ahead of the retrieval clock within the fixed tolerance; the source timestamp was preserved."
            )

        result = market_data.base_snapshot(
            requested_symbol,
            timeframes,
            retrieval_time,
            "MT5_CONNECTED",
            reason_code,
        )
        result["resolved_symbol"] = exact
        result["tick"] = tick
        result["symbol_specification"] = specification
        result["timeframe_series"] = series
        result["data_quality"] = {
            "snapshot_valid": snapshot_valid,
            "freshness_status": freshness,
            "market_session_status": "MARKET_SESSION_UNKNOWN",
            "tick_age_seconds": tick_age,
            "future_tick_skew_seconds": future_tick_skew,
            "stale_threshold_seconds": stale_threshold_seconds,
            "provider_error_code": None,
            "diagnostic": diagnostic,
        }
        return result, retrieval_time
