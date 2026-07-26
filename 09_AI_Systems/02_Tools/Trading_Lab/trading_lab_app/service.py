"""Read-only application service over the stable Release 1 kernel."""

import copy
import importlib
import json
from pathlib import Path

from . import APPLICATION_NAME, APPLICATION_VERSION, CHECKPOINT_ID, OPERATING_MODE
from .capabilities import capability_manifest
from .strategy_registry import load_registry


TRADING_LAB_DIRECTORY = Path(__file__).resolve().parent.parent
DEMO_PACK_PATH = TRADING_LAB_DIRECTORY / "sample_data" / "TRL-PACK-DEMO.json"

DEMO_STRATEGY = {
    "strategy_id": "SMA-001",
    "strategy_version": "1.0.0",
    "family": "SMA_CROSS_LONG_ONLY",
    "symbol": "DEMO-EQ-A",
    "fast": 5,
    "slow": 20,
    "paper_size_pct": 5.0,
}


def _kernel_module():
    """Resolve only the sibling Release 1 facade in either launch style."""
    package = __package__ or ""
    if "." in package:
        return importlib.import_module("..trading_lab", package)
    return importlib.import_module("trading_lab")


def _load_demo_pack():
    """Load a fresh built-in JSON value without exposing its filesystem path."""
    with DEMO_PACK_PATH.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    return value


def demo_result():
    """Run the committed synthetic demo using independent mutable copies."""
    kernel = _kernel_module()
    strategy = copy.deepcopy(DEMO_STRATEGY)
    pack = copy.deepcopy(_load_demo_pack())
    return kernel.run_backtest(strategy, pack, risk_policy=None)


def demo_report():
    """Render the full deterministic Release 1 Markdown report in memory."""
    kernel = _kernel_module()
    return kernel.performance_report_markdown(demo_result())


def health_document():
    return {
        "status": "ok",
        "application": APPLICATION_NAME,
        "application_version": APPLICATION_VERSION,
        "checkpoint": CHECKPOINT_ID,
        "bind_host": "127.0.0.1",
        "paper_research_only": True,
        "synthetic_data_only": True,
    }


def version_document():
    kernel = _kernel_module()
    return {
        "application": APPLICATION_NAME,
        "application_version": APPLICATION_VERSION,
        "checkpoint": CHECKPOINT_ID,
        "operating_mode": OPERATING_MODE,
        "kernel_release": kernel.RELEASE_ID,
        "kernel_checkpoint": kernel.CHECKPOINT_ID,
        "kernel_name": kernel.ENGINE_NAME,
        "kernel_version": kernel.ENGINE_VERSION,
        "output_schema_version": kernel.OUTPUT_SCHEMA_VERSION,
        "platform_status": {
            "windows": "FIRST_TARGET; SOURCE-LAUNCH VALIDATED",
            "macos": "ARCHITECTURALLY_PORTABLE; NOT TESTED",
            "linux": "ARCHITECTURALLY_PORTABLE; NOT TESTED",
        },
    }


def capabilities_document():
    return capability_manifest()


def strategy_registry_document():
    """Return the governed local registry without running financial evaluation."""
    return load_registry(copy.deepcopy(DEMO_STRATEGY)).document()


def market_data_document():
    pack = _load_demo_pack()
    result = demo_result()
    instrument = pack["instruments"][0]
    rows = result["equity_curve"]
    signal_by_timestamp = {}
    for decision in result["decisions"]:
        signal_by_timestamp.setdefault(decision["signal_timestamp"], []).append({
            "action": decision["action"],
            "status": decision["status"],
            "reason_code": decision["reason_code"],
        })
    points = []
    for bar, row in zip(instrument["ohlcv"], rows):
        points.append({
            "timestamp": bar["date"],
            "open": bar["open"],
            "high": bar["high"],
            "low": bar["low"],
            "close": bar["close"],
            "volume": bar["volume"],
            "fast_sma": row["fast_sma"],
            "slow_sma": row["slow_sma"],
            "signals": signal_by_timestamp.get(bar["date"], []),
        })
    return {
        "pack_id": pack["pack_id"],
        "data_as_of": pack["as_of"],
        "freshness": "COMMITTED_STATIC_SYNTHETIC_FIXTURE",
        "synthetic": True,
        "symbol": instrument["symbol"],
        "asset_class": instrument["asset_class"],
        "data_source": instrument["data_source"],
        "data_quality_note": instrument["data_quality_note"],
        "points": points,
    }


def report_document():
    return {
        "filename": "TRL-R2-001-synthetic-paper-report.md",
        "media_type": "text/markdown; charset=utf-8",
        "paper_research_only": True,
        "content": demo_report(),
    }
