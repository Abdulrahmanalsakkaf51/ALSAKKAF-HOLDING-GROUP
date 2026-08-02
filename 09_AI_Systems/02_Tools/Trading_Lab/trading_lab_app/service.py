"""Read-only application service over the stable Release 1 kernel."""

import copy
import importlib
import json
from pathlib import Path

from . import APPLICATION_NAME, APPLICATION_VERSION, CHECKPOINT_ID, OPERATING_MODE
from .capabilities import capability_manifest
from .mode_service import in_memory_mode_service
from .mt5_service import disabled_service
from .news_service import disabled_service as disabled_news_service
from .paper_service import disabled_service as disabled_paper_service
from .signal_service import disabled_service as disabled_signal_service
from .mt5_execution_service import disabled_service as disabled_execution_service
from .basket_execution_service import disabled_basket_service
from .market_intelligence_service import disabled_service as disabled_market_intelligence_service
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
        "synthetic_data_only": False,
        "synthetic_mode_default": True,
        "optional_local_mt5_read_only_data": True,
        "mt5_enabled_by_default": False,
        "optional_exact_official_news_metadata": True,
        "official_news_enabled_by_default": False,
        "forward_paper_engine_available": True,
        "paper_engine_enabled_by_default": False,
        "signal_generation": False,
        "trade_recommendation": False,
        "broker_execution": False,
        "real_orders": False,
        "account_mutation": False,
        "automated_trading": False,
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
        "paper_contract_schemas": {
            "timeline": "TRL_MARKET_TIMELINE.v1",
            "timeline_event": "TRL_TIMELINE_EVENT.v1",
            "store": "TRL_FORWARD_PAPER_STORE.v1",
            "proposal": "TRL_PAPER_PROPOSAL.v1",
            "account": "TRL_PAPER_ACCOUNT.v1",
            "position": "TRL_PAPER_POSITION.v1",
            "health": "TRL_PAPER_HEALTH.v1",
        },
    }


def capabilities_document():
    return capability_manifest()


def market_connection_document(market_data_service=None):
    """Return sanitized health for the narrow local read-only connector."""
    active_service = market_data_service or disabled_service()
    return active_service.connection_document()


def market_snapshot_document(market_data_service=None):
    """Return the latest strict snapshot without invoking financial evaluation."""
    active_service = market_data_service or disabled_service()
    return active_service.snapshot_document()


def news_health_document(news_service=None):
    active_service = news_service or disabled_news_service()
    return active_service.health_document()


def news_sources_document(news_service=None):
    active_service = news_service or disabled_news_service()
    return active_service.sources_document()


def news_items_document(news_service=None):
    active_service = news_service or disabled_news_service()
    return active_service.news_items_document()


def economic_events_document(news_service=None):
    active_service = news_service or disabled_news_service()
    return active_service.economic_events_document()


def paper_account_document(paper_service=None):
    return (paper_service or disabled_paper_service()).account_document()


def paper_positions_document(paper_service=None):
    return (paper_service or disabled_paper_service()).positions_document()


def paper_history_document(paper_service=None):
    return (paper_service or disabled_paper_service()).history_document()


def market_timeline_document(paper_service=None):
    return (paper_service or disabled_paper_service()).timeline_document()


def paper_health_document(paper_service=None):
    return (paper_service or disabled_paper_service()).health_document()


def mode_status_document(mode_service=None):
    return (mode_service or in_memory_mode_service()).mode_status_document()


def signal_status_document(signal_service=None):
    return (signal_service or disabled_signal_service()).status_document()


def signal_strategy_registry_document(signal_service=None):
    return (signal_service or disabled_signal_service()).strategy_registry_document()


def signal_proposal_history_document(signal_service=None):
    return (signal_service or disabled_signal_service()).proposal_history_document()


def signal_timeline_document(signal_service=None):
    return (signal_service or disabled_signal_service()).timeline_document()


def mt5_execution_status_document(execution_service=None):
    return (execution_service or disabled_execution_service()).status_document()


def mt5_account_status_document(execution_service=None):
    return (execution_service or disabled_execution_service()).account_status_document()


def mt5_terminal_status_document(execution_service=None):
    return (execution_service or disabled_execution_service()).terminal_status_document()


def mt5_execution_journal_document(execution_service=None):
    return (execution_service or disabled_execution_service()).journal_document()


# TRL-R2-009 (Phase 6): read-only only, mirroring the Phase 5 execution
# routes above exactly — no HTTP route may create, check, confirm, send,
# retry, cancel, compensate, or otherwise mutate any basket state (see
# server.py's global method-not-allowed default for every non-GET/HEAD
# verb). The journal slice is explicitly bounded per
# TRL_R2_009_CONTROLLED_BASKET_EXECUTION_CONTRACT.md Section 35.
BASKET_JOURNAL_HTTP_MAX_EVENTS = 500


def basket_execution_status_document(basket_service=None):
    return (basket_service or disabled_basket_service()).status_document()


def execution_baskets_document(basket_service=None):
    return (basket_service or disabled_basket_service()).list_baskets_document()


def execution_basket_document(basket_service, basket_id):
    return (basket_service or disabled_basket_service()).basket_status_document(basket_id)


def execution_basket_journal_document(basket_service=None):
    return (basket_service or disabled_basket_service()).basket_journal_document(
        limit=BASKET_JOURNAL_HTTP_MAX_EVENTS,
    )


def market_intelligence_status_document(market_intelligence_service_instance=None):
    return (market_intelligence_service_instance or disabled_market_intelligence_service()).status_document()


def market_opportunities_document(market_intelligence_service_instance=None):
    return (market_intelligence_service_instance or disabled_market_intelligence_service()).market_opportunities_http_document()


def market_opportunity_document(market_intelligence_service_instance, opportunity_id):
    return (market_intelligence_service_instance or disabled_market_intelligence_service()).market_opportunity_http_document(opportunity_id)


def virtual_opportunities_document(market_intelligence_service_instance=None):
    return (market_intelligence_service_instance or disabled_market_intelligence_service()).virtual_opportunities_http_document()


def market_intelligence_telemetry_document(market_intelligence_service_instance=None):
    return (market_intelligence_service_instance or disabled_market_intelligence_service()).telemetry_document()


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
