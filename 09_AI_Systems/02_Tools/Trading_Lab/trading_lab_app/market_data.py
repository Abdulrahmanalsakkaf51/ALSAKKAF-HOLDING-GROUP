"""Pure validation and normalization for local read-only market data."""

import math
import numbers
import re
from datetime import datetime, timezone
from itertools import islice


SNAPSHOT_SCHEMA_VERSION = "TRL-MARKET-SNAPSHOT-1.0"
SUPPORTED_TIMEFRAMES = {
    "M1": {"seconds": 60},
    "M5": {"seconds": 300},
    "H4": {"seconds": 14400},
    "D1": {"seconds": 86400},
}
DEFAULT_TIMEFRAMES = ("M1", "M5", "H4", "D1")
MIN_BAR_COUNT = 1
MAX_BAR_COUNT = 2000
MAX_SYMBOL_LENGTH = 64
MAX_SYMBOLS_INSPECTED = 5000
MAX_CANDIDATES = 20
MIN_INITIALIZATION_TIMEOUT_MS = 1000
MAX_INITIALIZATION_TIMEOUT_MS = 30000
DEFAULT_INITIALIZATION_TIMEOUT_MS = 5000
DEFAULT_STALE_THRESHOLD_SECONDS = 180
MAX_FUTURE_TICK_SKEW_SECONDS = 5

STABLE_STATUS_CODES = (
    "MT5_DISABLED",
    "MT5_DEPENDENCY_MISSING",
    "MT5_INITIALIZATION_FAILED",
    "MT5_CONNECTED",
    "MT5_SYMBOL_NOT_FOUND",
    "MT5_SYMBOL_AMBIGUOUS",
    "MT5_SYMBOL_NOT_VISIBLE",
    "MT5_TICK_UNAVAILABLE",
    "MT5_BAR_DATA_UNAVAILABLE",
    "MT5_INVALID_TICK",
    "MT5_TICK_CLOCK_SKEW",
    "MT5_INVALID_SYMBOL_SPECIFICATION",
    "MT5_INVALID_BAR_DATA",
    "MT5_STALE",
    "MT5_PROVIDER_INCOMPATIBLE",
    "MT5_PROVIDER_ERROR",
    "MT5_READ_ONLY_SNAPSHOT_VALID",
)

FRESHNESS_STATUS_CODES = (
    "UNAVAILABLE",
    "FRESH",
    "CLOCK_SKEW_WITHIN_TOLERANCE",
    "STALE_BY_THRESHOLD",
)

_SAFE_SYMBOL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._#+-]{0,63}$")
_GOLD_COMPARISON_NAMES = frozenset(("GOLD", "XAUUSD"))

LIMITATIONS = (
    "Read-only data from an already authenticated MT5 terminal on this PC.",
    "Candidate symbols are comparison hints, never financial equivalence claims.",
    "Market-session state and commission are unknown.",
    "Bars are broker-provided and are not filled, interpolated, or aggregated.",
    "No strategy, recommendation, paper fill, order proposal, or order capability exists.",
)


class MarketDataValidationError(ValueError):
    """Stable validation failure which never embeds provider data."""

    def __init__(self, reason_code):
        super().__init__(reason_code)
        self.reason_code = reason_code


def validate_symbol(value):
    if type(value) is not str or not _SAFE_SYMBOL.fullmatch(value):
        raise ValueError(
            "symbol must be 1-64 ASCII letters, digits, dot, underscore, #, +, or hyphen"
        )
    return value


def validate_timeframes(values):
    if type(values) not in (tuple, list) or not values:
        raise ValueError("at least one timeframe is required")
    result = []
    for value in values:
        if type(value) is not str or value not in SUPPORTED_TIMEFRAMES:
            raise ValueError("unsupported timeframe: {}".format(value))
        if value in result:
            raise ValueError("duplicate timeframe: {}".format(value))
        result.append(value)
    return tuple(result)


def validate_bar_count(value):
    if type(value) is not int or not MIN_BAR_COUNT <= value <= MAX_BAR_COUNT:
        raise ValueError(
            "bar count must be an integer from {} through {}".format(
                MIN_BAR_COUNT, MAX_BAR_COUNT,
            )
        )
    return value


def validate_timeout_ms(value):
    if type(value) is not int or not MIN_INITIALIZATION_TIMEOUT_MS <= value <= MAX_INITIALIZATION_TIMEOUT_MS:
        raise ValueError(
            "initialization timeout must be {}-{} milliseconds".format(
                MIN_INITIALIZATION_TIMEOUT_MS, MAX_INITIALIZATION_TIMEOUT_MS,
            )
        )
    return value


def _field(source, name, default=None):
    if type(source) is dict:
        return source.get(name, default)
    value = getattr(source, name, default)
    if value is not default:
        return value
    try:
        return source[name]
    except (IndexError, KeyError, TypeError):
        return default


def _finite_number(value, reason_code):
    if isinstance(value, bool) or not isinstance(value, numbers.Real):
        raise MarketDataValidationError(reason_code)
    normalized = int(value) if isinstance(value, numbers.Integral) else float(value)
    if not math.isfinite(normalized):
        raise MarketDataValidationError(reason_code)
    return normalized


def _nonnegative_number(value, reason_code):
    value = _finite_number(value, reason_code)
    if value < 0:
        raise MarketDataValidationError(reason_code)
    return value


def _safe_optional_text(value, maximum=256):
    if value is None or type(value) is not str:
        return None
    if (
        not value or len(value) > maximum
        or any(ord(char) < 32 for char in value)
        or any(character in value for character in ("/", "\\", ":"))
    ):
        return None
    return value


def _timestamp_parts(seconds, milliseconds=None, reason_code="MT5_INVALID_BAR_DATA"):
    seconds = _finite_number(seconds, reason_code)
    try:
        instant = datetime.fromtimestamp(seconds, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        raise MarketDataValidationError(reason_code)
    if milliseconds is not None:
        if isinstance(milliseconds, bool) or not isinstance(milliseconds, numbers.Integral) or milliseconds < 0:
            raise MarketDataValidationError(reason_code)
        milliseconds = int(milliseconds)
        millisecond_seconds, _ = divmod(milliseconds, 1000)
        try:
            datetime.fromtimestamp(millisecond_seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            raise MarketDataValidationError(reason_code)
    return instant.isoformat(timespec="milliseconds").replace("+00:00", "Z"), milliseconds


def normalize_symbol_name(value):
    """Normalize only for candidate comparison; never for resolved identity."""
    if type(value) is not str:
        return ""
    return "".join(character for character in value.upper() if character.isalnum())


def _is_candidate(requested, available):
    requested_name = normalize_symbol_name(requested)
    available_name = normalize_symbol_name(available)
    if not requested_name or not available_name or requested == available:
        return False
    if available_name.startswith(requested_name) or requested_name.startswith(available_name):
        return True
    return requested_name in _GOLD_COMPARISON_NAMES and available_name in _GOLD_COMPARISON_NAMES


def discover_symbols(requested_symbol, provider_symbols):
    """Return an exact name and bounded deterministic candidate names."""
    validate_symbol(requested_symbol)
    if provider_symbols is None:
        provider_symbols = ()
    names = []
    for source in islice(iter(provider_symbols), MAX_SYMBOLS_INSPECTED):
        name = _field(source, "name")
        if type(name) is str and _SAFE_SYMBOL.fullmatch(name) and name not in names:
            names.append(name)
    exact = requested_symbol if requested_symbol in names else None
    candidates = sorted(
        name for name in names if _is_candidate(requested_symbol, name)
    )[:MAX_CANDIDATES]
    return exact, candidates


def normalize_tick(source, point):
    bid = _finite_number(_field(source, "bid"), "MT5_INVALID_TICK")
    ask = _finite_number(_field(source, "ask"), "MT5_INVALID_TICK")
    if ask < bid:
        raise MarketDataValidationError("MT5_INVALID_TICK")
    last_value = _field(source, "last")
    last = None if last_value is None else _finite_number(last_value, "MT5_INVALID_TICK")
    volume_value = _field(source, "volume")
    volume = None if volume_value is None else _nonnegative_number(volume_value, "MT5_INVALID_TICK")
    source_timestamp, source_milliseconds = _timestamp_parts(
        _field(source, "time"), _field(source, "time_msc"), "MT5_INVALID_TICK"
    )
    spread_price = ask - bid
    if not math.isfinite(spread_price):
        raise MarketDataValidationError("MT5_INVALID_TICK")
    spread_points = None
    if isinstance(point, numbers.Real) and not isinstance(point, bool) and math.isfinite(point) and point > 0:
        spread_points = spread_price / point
        if not math.isfinite(spread_points):
            raise MarketDataValidationError("MT5_INVALID_TICK")
    return {
        "source_timestamp_utc": source_timestamp,
        "source_timestamp_milliseconds": source_milliseconds,
        "bid": bid,
        "ask": ask,
        "last": last,
        "volume": volume,
        "spread_price": spread_price,
        "spread_points": spread_points,
    }


def normalized_tick_source_seconds(tick):
    """Return validated seconds and optional millisecond time without provider hooks."""
    timestamp = datetime.fromisoformat(
        tick["source_timestamp_utc"].replace("Z", "+00:00")
    ).timestamp()
    milliseconds = tick["source_timestamp_milliseconds"]
    if milliseconds is None:
        return timestamp, None
    whole_seconds, remainder = divmod(milliseconds, 1000)
    millisecond_timestamp = whole_seconds + (remainder / 1000.0)
    return timestamp, millisecond_timestamp


def normalize_symbol_specification(source, resolved_symbol):
    if _field(source, "name") != resolved_symbol:
        raise MarketDataValidationError("MT5_INVALID_SYMBOL_SPECIFICATION")
    digits = _field(source, "digits")
    if isinstance(digits, bool) or not isinstance(digits, numbers.Integral) or not 0 <= digits <= 16:
        raise MarketDataValidationError("MT5_INVALID_SYMBOL_SPECIFICATION")
    digits = int(digits)
    point = _finite_number(_field(source, "point"), "MT5_INVALID_SYMBOL_SPECIFICATION")
    contract_size = _finite_number(
        _field(source, "trade_contract_size"), "MT5_INVALID_SYMBOL_SPECIFICATION"
    )
    volume_minimum = _finite_number(
        _field(source, "volume_min"), "MT5_INVALID_SYMBOL_SPECIFICATION"
    )
    volume_maximum = _finite_number(
        _field(source, "volume_max"), "MT5_INVALID_SYMBOL_SPECIFICATION"
    )
    volume_step = _finite_number(
        _field(source, "volume_step"), "MT5_INVALID_SYMBOL_SPECIFICATION"
    )
    if point <= 0 or contract_size <= 0 or volume_minimum <= 0 or volume_maximum < volume_minimum or volume_step <= 0:
        raise MarketDataValidationError("MT5_INVALID_SYMBOL_SPECIFICATION")
    stops_level = _field(source, "trade_stops_level")
    freeze_level = _field(source, "trade_freeze_level")
    trade_mode = _field(source, "trade_mode")
    if any(
        isinstance(value, bool) or not isinstance(value, numbers.Integral) or value < 0
        for value in (stops_level, freeze_level, trade_mode)
    ):
        raise MarketDataValidationError("MT5_INVALID_SYMBOL_SPECIFICATION")
    stops_level = int(stops_level)
    freeze_level = int(freeze_level)
    trade_mode = int(trade_mode)
    reported_spread = _field(source, "spread")
    if reported_spread is not None:
        reported_spread = _nonnegative_number(
            reported_spread, "MT5_INVALID_SYMBOL_SPECIFICATION"
        )
    return {
        "symbol": resolved_symbol,
        "description": _safe_optional_text(_field(source, "description")),
        "currency_base": _safe_optional_text(_field(source, "currency_base"), 32),
        "currency_profit": _safe_optional_text(_field(source, "currency_profit"), 32),
        "currency_margin": _safe_optional_text(_field(source, "currency_margin"), 32),
        "digits": digits,
        "point": point,
        "trade_contract_size": contract_size,
        "volume_minimum": volume_minimum,
        "volume_maximum": volume_maximum,
        "volume_step": volume_step,
        "stops_level": stops_level,
        "freeze_level": freeze_level,
        "trade_mode": trade_mode,
        "broker_reported_spread_points": reported_spread,
        "commission": None,
        "commission_status": "UNKNOWN_NO_GOVERNED_SOURCE",
    }


def normalize_bars(provider_rows, timeframe, retrieval_time):
    if timeframe not in SUPPORTED_TIMEFRAMES:
        raise ValueError("unsupported timeframe: {}".format(timeframe))
    if provider_rows is None:
        provider_rows = ()
    rows = list(islice(iter(provider_rows), MAX_BAR_COUNT + 1))
    if len(rows) > MAX_BAR_COUNT:
        raise MarketDataValidationError("MT5_INVALID_BAR_DATA")
    normalized = []
    previous_seconds = None
    for source in rows:
        seconds = _finite_number(_field(source, "time"), "MT5_INVALID_BAR_DATA")
        if seconds > retrieval_time.timestamp():
            raise MarketDataValidationError("MT5_INVALID_BAR_DATA")
        if previous_seconds is not None and seconds <= previous_seconds:
            raise MarketDataValidationError("MT5_INVALID_BAR_DATA")
        timestamp, _ = _timestamp_parts(seconds, reason_code="MT5_INVALID_BAR_DATA")
        open_value = _finite_number(_field(source, "open"), "MT5_INVALID_BAR_DATA")
        high = _finite_number(_field(source, "high"), "MT5_INVALID_BAR_DATA")
        low = _finite_number(_field(source, "low"), "MT5_INVALID_BAR_DATA")
        close = _finite_number(_field(source, "close"), "MT5_INVALID_BAR_DATA")
        if high < max(open_value, low, close) or low > min(open_value, high, close):
            raise MarketDataValidationError("MT5_INVALID_BAR_DATA")
        tick_volume = _nonnegative_number(
            _field(source, "tick_volume"), "MT5_INVALID_BAR_DATA"
        )
        spread = _nonnegative_number(_field(source, "spread"), "MT5_INVALID_BAR_DATA")
        real_volume = _nonnegative_number(
            _field(source, "real_volume"), "MT5_INVALID_BAR_DATA"
        )
        normalized.append({
            "timestamp_utc": timestamp,
            "open": open_value,
            "high": high,
            "low": low,
            "close": close,
            "tick_volume": tick_volume,
            "spread": spread,
            "real_volume": real_volume,
            "bar_state": "CLOSED",
        })
        previous_seconds = seconds
    if normalized:
        interval = SUPPORTED_TIMEFRAMES[timeframe]["seconds"]
        retrieval_seconds = retrieval_time.timestamp()
        if previous_seconds <= retrieval_seconds < previous_seconds + interval:
            normalized[-1]["bar_state"] = "FORMING"
    closed = sum(row["bar_state"] == "CLOSED" for row in normalized)
    forming = sum(row["bar_state"] == "FORMING" for row in normalized)
    return {
        "timeframe": timeframe,
        "status": "AVAILABLE" if normalized else "UNAVAILABLE",
        "reason_code": "MT5_READ_ONLY_SNAPSHOT_VALID" if normalized else "MT5_BAR_DATA_UNAVAILABLE",
        "bar_count": len(normalized),
        "closed_bar_count": closed,
        "forming_bar_count": forming,
        "latest_source_timestamp_utc": normalized[-1]["timestamp_utc"] if normalized else None,
        "bars": normalized,
    }


def empty_timeframe_series(timeframes, reason_code):
    return {
        timeframe: {
            "timeframe": timeframe,
            "status": "UNAVAILABLE",
            "reason_code": reason_code,
            "bar_count": 0,
            "closed_bar_count": 0,
            "forming_bar_count": 0,
            "latest_source_timestamp_utc": None,
            "bars": [],
        }
        for timeframe in timeframes
    }


def utc_now(clock):
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc)


def utc_text(value):
    return value.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def base_snapshot(requested_symbol, timeframes, retrieval_time, status, reason_code):
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "source_type": "LOCAL_MT5_TERMINAL",
        "connector_mode": "READ_ONLY",
        "connection_status": status,
        "reason_code": reason_code,
        "requested_symbol": requested_symbol,
        "resolved_symbol": None,
        "candidate_symbols": [],
        "retrieval_timestamp_utc": utc_text(retrieval_time),
        "tick": None,
        "symbol_specification": None,
        "timeframe_series": empty_timeframe_series(timeframes, reason_code),
        "data_quality": {
            "snapshot_valid": False,
            "freshness_status": "UNAVAILABLE",
            "market_session_status": "MARKET_SESSION_UNKNOWN",
            "tick_age_seconds": None,
            "future_tick_skew_seconds": None,
            "stale_threshold_seconds": DEFAULT_STALE_THRESHOLD_SECONDS,
            "provider_error_code": None,
            "diagnostic": "No validated local MT5 market snapshot is available.",
        },
        "limitations": list(LIMITATIONS),
    }
