"""Application configuration and service facade for local MT5 market data."""

import copy
import threading
from dataclasses import dataclass
from datetime import datetime, timezone

from . import market_data
from .mt5_connector import LocalMT5ReadOnlyConnector


@dataclass(frozen=True)
class MT5ReadOnlyConfiguration:
    """Validated local-only connector controls; it contains no credentials."""

    enabled: bool = False
    symbol: str = "XAUUSD"
    timeframes: tuple = market_data.DEFAULT_TIMEFRAMES
    bars: int = 500
    timeout_ms: int = market_data.DEFAULT_INITIALIZATION_TIMEOUT_MS
    stale_threshold_seconds: int = market_data.DEFAULT_STALE_THRESHOLD_SECONDS

    def __post_init__(self):
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be a boolean")
        market_data.validate_symbol(self.symbol)
        object.__setattr__(self, "timeframes", market_data.validate_timeframes(self.timeframes))
        market_data.validate_bar_count(self.bars)
        market_data.validate_timeout_ms(self.timeout_ms)
        if type(self.stale_threshold_seconds) is not int or self.stale_threshold_seconds <= 0:
            raise ValueError("stale threshold must be a positive integer")


class MarketDataService:
    """Keep synthetic default mode separate from the optional MT5 connector."""

    def __init__(self, configuration=None, provider=None, clock=None):
        self.configuration = configuration or MT5ReadOnlyConfiguration()
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._connector = LocalMT5ReadOnlyConnector(provider=provider, clock=self._clock)
        self._state_lock = threading.Lock()
        self._latest = None

    def snapshot_document(self):
        with self._state_lock:
            if not self.configuration.enabled:
                retrieval_time = market_data.utc_now(self._clock)
                result = market_data.base_snapshot(
                    None,
                    self.configuration.timeframes,
                    retrieval_time,
                    "MT5_DISABLED",
                    "MT5_DISABLED",
                )
                result["source_type"] = "SYNTHETIC_DEMONSTRATION"
                result["connector_mode"] = "SYNTHETIC_DEFAULT_MT5_DISABLED"
                result["data_quality"]["diagnostic"] = (
                    "MT5 read-only mode is disabled. The separate committed synthetic dashboard remains available."
                )
            else:
                result = self._connector.snapshot(
                    requested_symbol=self.configuration.symbol,
                    timeframes=self.configuration.timeframes,
                    bar_count=self.configuration.bars,
                    timeout_ms=self.configuration.timeout_ms,
                    stale_threshold_seconds=self.configuration.stale_threshold_seconds,
                )
            self._latest = copy.deepcopy(result)
            return copy.deepcopy(result)

    def connection_document(self):
        snapshot = self.snapshot_document()
        return {
            "schema_version": "TRL-MARKET-CONNECTION-1.0",
            "source_type": snapshot["source_type"],
            "connector_mode": snapshot["connector_mode"],
            "connection_status": snapshot["connection_status"],
            "reason_code": snapshot["reason_code"],
            "enabled": self.configuration.enabled,
            "requested_symbol": snapshot["requested_symbol"],
            "resolved_symbol": snapshot["resolved_symbol"],
            "candidate_symbols": copy.deepcopy(snapshot["candidate_symbols"]),
            "requested_timeframes": list(self.configuration.timeframes),
            "requested_bar_count": self.configuration.bars,
            "retrieval_timestamp_utc": snapshot["retrieval_timestamp_utc"],
            "freshness_status": snapshot["data_quality"]["freshness_status"],
            "market_session_status": snapshot["data_quality"]["market_session_status"],
            "diagnostic": snapshot["data_quality"]["diagnostic"],
            "local_only": True,
            "credential_input_accepted": False,
            "order_capability": False,
            "stable_status_codes": list(market_data.STABLE_STATUS_CODES),
        }


_DISABLED_SERVICE = MarketDataService()


def disabled_service():
    return _DISABLED_SERVICE
