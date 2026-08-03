"""Shared, non-discovered test helpers for the ALSAKKAF SCALPING test
suite (TRL-R2-012). Mirrors ``mdr_test_support.py`` / ``mi_test_support.py``'s
house convention: a plain module (no ``test_`` prefix) so ``unittest
discover`` never collects it directly.
"""

import tempfile
from decimal import Decimal

from trading_lab_app import alsakkaf_scalping_mt5 as mt5a
from trading_lab_app import alsakkaf_scalping_service as svc
from trading_lab_app.alsakkaf_scalping_data import (
    ALSAKKAF_SCALPING_MAGIC,
    InMemorySymbolMapStore,
)
from trading_lab_app.alsakkaf_scalping_journal import in_memory_journal_writer
from trading_lab_app.market_intelligence_journal import in_memory_mi_journal_writer
from trading_lab_app.market_intelligence_service import MarketIntelligenceService
from trading_lab_app.mode_service import in_memory_mode_service


def make_chop_then_breakout_bars(chop_count=20, breakout_count=40, start=Decimal("1900.0")):
    """A deterministic fixture: a flat chop (creating a clean swing low),
    then a strong, accelerating, strong-bodied breakout leg -- reliably
    clears both this module's own 75-point TRADE_CANDIDATE threshold and
    R2-010's independent supporting_score threshold at the same time."""
    bars = []
    price = start
    for index in range(chop_count):
        open_price = price
        close_price = price + (Decimal("0.05") if index % 2 == 0 else Decimal("-0.05"))
        high = max(open_price, close_price) + Decimal("0.05")
        low = min(open_price, close_price) - Decimal("0.05")
        bars.append({
            "open": str(open_price), "high": str(high), "low": str(low), "close": str(close_price),
        })
        price = close_price
    step = Decimal("0.5")
    for _index in range(breakout_count):
        step += Decimal("0.05")
        open_price = price
        close_price = price + step
        high = close_price + Decimal("0.02")
        low = open_price - Decimal("0.02")
        bars.append({
            "open": str(open_price), "high": str(high), "low": str(low), "close": str(close_price),
        })
        price = close_price
    return bars


def make_flat_choppy_bars(count=60, start=Decimal("1900.0")):
    """A directionless fixture -- never produces a TRADE_CANDIDATE
    (direction NONE or a low score); used for WAIT/REJECT coverage."""
    bars = []
    price = start
    for index in range(count):
        open_price = price
        close_price = price + (Decimal("0.05") if index % 2 == 0 else Decimal("-0.05"))
        high = max(open_price, close_price) + Decimal("0.05")
        low = min(open_price, close_price) - Decimal("0.05")
        bars.append({
            "open": str(open_price), "high": str(high), "low": str(low), "close": str(close_price),
        })
        price = close_price
    return bars


def make_fake_adapter(broker_symbol="XAUUSDm", current_price="1961.0", spread="0.05"):
    adapter = mt5a.fake_adapter()
    ask = str(Decimal(current_price) + Decimal(spread))
    adapter.set_symbol(
        broker_symbol, bid=current_price, ask=ask, tick_value="1.00", tick_size="0.01",
        volume_minimum="0.01", volume_maximum="100", volume_step="0.01",
        stops_level=50, freeze_level=0,
    )
    return adapter


def make_mode_service(target_mode="MT5_DEMO_AUTOMATED"):
    mode_svc = in_memory_mode_service()
    if target_mode in ("RESEARCH", "MT5_DEMO_AUTOMATED"):
        mode_svc.request_transition("RESEARCH", actor="tester", actor_channel="LOCAL_OPERATOR")
    if target_mode == "MT5_DEMO_AUTOMATED":
        mode_svc.request_transition("MT5_DEMO_AUTOMATED", actor="tester", actor_channel="LOCAL_OPERATOR")
    return mode_svc


def make_mi_service(mode_svc):
    return MarketIntelligenceService(mode_service=mode_svc, journal=in_memory_mi_journal_writer())


def make_service(
    canonical_instrument="XAUUSD", broker_symbol="XAUUSDm", profile_id="ALSAKKAF_PRECISION_SCALPING",
    target_mode="MT5_DEMO_AUTOMATED", adapter=None, current_price="1961.0", spread="0.05",
    journal=None, clock=None,
):
    mode_svc = make_mode_service(target_mode)
    mi_service = make_mi_service(mode_svc)
    adapter = adapter if adapter is not None else make_fake_adapter(broker_symbol, current_price, spread)
    service = svc.ScalpingService(
        journal=journal if journal is not None else in_memory_journal_writer(),
        adapter=adapter, symbol_map_store=InMemorySymbolMapStore(),
        mode_service=mode_svc, market_intelligence_service=mi_service,
        scratch_directory=tempfile.mkdtemp(), clock=clock,
    )
    service.save_symbol_map(canonical_instrument, broker_symbol)
    service.configure_profile(canonical_instrument, profile_id)
    return service, adapter, mode_svc


def owned_order(ticket=1, symbol="XAUUSDm"):
    return {"ticket": ticket, "symbol": symbol, "magic": ALSAKKAF_SCALPING_MAGIC, "comment": "ALSAKKAF_SCALPING"}


def owned_position(ticket=2, symbol="XAUUSDm"):
    return {"ticket": ticket, "symbol": symbol, "magic": ALSAKKAF_SCALPING_MAGIC, "comment": "ALSAKKAF_SCALPING"}
