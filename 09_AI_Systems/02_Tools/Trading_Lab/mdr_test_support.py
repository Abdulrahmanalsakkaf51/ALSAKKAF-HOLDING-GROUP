"""Shared, non-discovered test support for TRL-R2-011 Market Data Fabric
and Replay V0 (TRL CORTEX DATA FABRIC V0) tests.

Deliberately named ``mdr_test_support.py`` (not ``test*.py``) so
``python -m unittest discover -p 'test*.py'`` never collects it directly.
No filesystem/network/broker/MT5 access happens at import time.
"""

from pathlib import Path
import sys

APP_DIRECTORY = Path(__file__).resolve().parent
if str(APP_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(APP_DIRECTORY))

from trading_lab_app import market_data_replay_data as mdd
from trading_lab_app import market_data_replay_journal as mdj
from trading_lab_app import market_data_replay_service as mdrsvc
from trading_lab_app import market_data_replay_storage as mds


FIXTURE_PATH = APP_DIRECTORY / "fixtures" / "trl_cortex_data_fabric_v0_synthetic.csv"
FIXTURE_SOURCE_REFERENCE = "trl-cortex-data-fabric-v0-synthetic"
FIXTURE_BAR_COUNT = 24
FIXTURE_GAP_COUNT = 1
FIXTURE_LARGEST_GAP_INTERVALS = 1


class FakeModeService:
    """A minimal ``ModeService``-shaped stub: grants exactly the
    capabilities listed, nothing else. Never touches the filesystem."""

    def __init__(self, current_mode="RESEARCH", granted_capabilities=("market_data_research",)):
        self.current_mode = current_mode
        self._granted = frozenset(granted_capabilities)

    def has_capability(self, capability):
        return capability in self._granted


def denied_mode_service(current_mode="OFF"):
    return FakeModeService(current_mode=current_mode, granted_capabilities=())


def build_csv_bytes(
    instrument="XAUUSD", timeframe="M5", bar_count=5,
    start="2026-01-01T00:00:00.000000Z", open_price="1900.00",
    step_minutes=5, gap_after_index=None, gap_step_minutes=None,
):
    """Build small, deterministic, strictly valid CSV bytes for a
    synthetic in-memory test dataset. ``gap_after_index`` (0-based),
    combined with ``gap_step_minutes``, inserts one exact-multiple gap."""
    from datetime import datetime, timedelta, timezone
    from decimal import Decimal

    interval = mdd.TIMEFRAME_SECONDS[timeframe]
    assert step_minutes * 60 == interval, "step_minutes must match the timeframe interval"
    t = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
    price = Decimal(open_price)
    lines = [mdd.CSV_HEADER]
    for index in range(bar_count):
        if index > 0:
            minutes = step_minutes
            if gap_after_index is not None and index == gap_after_index + 1:
                minutes = gap_step_minutes if gap_step_minutes is not None else step_minutes
            t = t + timedelta(minutes=minutes)
        open_ = price
        high = open_ + Decimal("1.50")
        low = open_ - Decimal("1.00")
        close = open_ + Decimal("0.50")
        spread = Decimal("0.20")
        volume = 100 + index
        ts_text = t.strftime("%Y-%m-%dT%H:%M:%S.%f") + "Z"
        lines.append(
            "{},{},{},{},{},{},{},{},{}".format(
                instrument, timeframe, ts_text, open_, high, low, close, spread, volume,
            )
        )
        price = close
    return ("\n".join(lines) + "\n").encode("utf-8")


def build_service(mode_service=None, journal=None, storage=None):
    """A fully wired, in-memory-only ``MarketDataReplayService`` for tests."""
    return mdrsvc.MarketDataReplayService(
        mode_service=mode_service if mode_service is not None else FakeModeService(),
        journal=journal if journal is not None else mdj.in_memory_mdr_journal_writer(),
        storage=storage if storage is not None else mds.InMemoryDatasetStorage(),
    )


def import_synthetic_dataset(service, source_reference="test-ref", csv_path=None, tmp_path_factory=None):
    """Write ``build_csv_bytes()`` (or a caller-supplied CSV) to a real
    temporary file and import it -- ``import_market_data`` requires a real
    local path (Section 7.1), never raw bytes."""
    import tempfile

    if csv_path is not None:
        return service.import_market_data(csv_path, "SYNTHETIC_FIXTURE", source_reference)
    raw = build_csv_bytes()
    handle = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    try:
        handle.write(raw)
        handle.close()
        return service.import_market_data(handle.name, "SYNTHETIC_FIXTURE", source_reference)
    finally:
        import os
        try:
            os.unlink(handle.name)
        except OSError:
            pass


__all__ = (
    "APP_DIRECTORY", "FIXTURE_PATH", "FIXTURE_SOURCE_REFERENCE",
    "FIXTURE_BAR_COUNT", "FIXTURE_GAP_COUNT", "FIXTURE_LARGEST_GAP_INTERVALS",
    "FakeModeService", "denied_mode_service",
    "build_csv_bytes", "build_service", "import_synthetic_dataset",
)
