"""Command-line lifecycle for the Windows-first local dashboard."""

import argparse
import sys
import webbrowser

from . import APPLICATION_NAME, APPLICATION_VERSION
from . import market_data
from .mode_service import ModeService, in_memory_mode_service
from .mt5_service import MT5ReadOnlyConfiguration, MarketDataService
from .news_service import (
    MAX_REFRESH_SECONDS,
    MIN_REFRESH_SECONDS,
    OfficialNewsConfiguration,
    OfficialNewsService,
)
from .paper_service import (
    DisabledPaperService,
    ForwardPaperService,
    build_synthetic_demonstration_service,
)
from .signal_service import DisabledSignalService, SignalIntelligenceService
from . import signal_service as signal_service_module
from . import mt5_execution_adapter
from . import mt5_execution_service
from . import basket_execution_service
from . import market_intelligence_data
from . import market_intelligence_service
from . import market_data_replay_service
from . import alsakkaf_scalping_mt5
from . import alsakkaf_scalping_service
from .server import BIND_HOST, DEFAULT_PORT, create_server


def _symbol_argument(value):
    try:
        return market_data.validate_symbol(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error))


def _timeframes_argument(value):
    items = value.split(",")
    try:
        return market_data.validate_timeframes(items)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error))


def _bars_argument(value):
    try:
        return market_data.validate_bar_count(int(value))
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError(str(error))


def _news_refresh_argument(value):
    try:
        parsed = int(value)
    except (TypeError, ValueError) as error:
        raise argparse.ArgumentTypeError("official-news refresh must be an integer") from error
    if not MIN_REFRESH_SECONDS <= parsed <= MAX_REFRESH_SECONDS:
        raise argparse.ArgumentTypeError(
            "official-news refresh must be from 300 through 3600 seconds"
        )
    return parsed


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app",
        description=(
            "Run the local PAPER/RESEARCH ONLY dashboard on 127.0.0.1. "
            "Synthetic mode is the default; local MT5 data and official-source "
            "metadata each require explicit enablement and remain read-only."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="local loopback port (default: %(default)s)",
    )
    parser.add_argument(
        "--enable-mt5-read-only",
        action="store_true",
        help="enable data-only access to the already authenticated local MT5 terminal",
    )
    parser.add_argument(
        "--mt5-symbol",
        type=_symbol_argument,
        default=None,
        help="exact broker symbol; no alias is selected automatically",
    )
    parser.add_argument(
        "--mt5-timeframes",
        type=_timeframes_argument,
        default=None,
        help="comma-separated allowlist: M1,M5,H4,D1",
    )
    parser.add_argument(
        "--mt5-bars",
        type=_bars_argument,
        default=None,
        help="bars per requested timeframe (maximum {})".format(market_data.MAX_BAR_COUNT),
    )
    parser.add_argument(
        "--enable-official-news",
        action="store_true",
        help="enable exact-allowlist official publisher metadata retrieval",
    )
    parser.add_argument(
        "--official-news-refresh-seconds",
        type=_news_refresh_argument,
        default=None,
        help="bounded local refresh interval from 300 through 3600 seconds (default: 900)",
    )
    parser.add_argument(
        "--enable-forward-paper-engine",
        action="store_true",
        help=(
            "DEPRECATED and always fails closed in Phase 3: no approved operating "
            "mode authorizes this capability yet; the server does not start. "
            "See TRL_PHASE_3_OPERATING_MODE_CONTRACT.md"
        ),
    )
    parser.add_argument(
        "--enable-forward-paper-demo",
        action="store_true",
        help=(
            "DEPRECATED compatibility path: requests a transition to the governed "
            "SYNTHETIC_PAPER mode through the operating-mode state machine, then "
            "loads the committed SYNTHETIC DEMONSTRATION fixture; in-memory only, "
            "never reads or writes production paper storage, not live market data. "
            "Prefer: python -m trading_lab_app.mode_cli request-mode SYNTHETIC_PAPER"
        ),
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="do not open the local dashboard in the default browser",
    )
    parser.add_argument("--version", action="version", version=APPLICATION_VERSION)
    return parser


LEGACY_FORWARD_PAPER_MODE_UNAVAILABLE = "LEGACY_FORWARD_PAPER_MODE_UNAVAILABLE"
MODE_SUBSYSTEM_CONFIGURATION_MISMATCH = "MODE_SUBSYSTEM_CONFIGURATION_MISMATCH"


class ModeSubsystemConfigurationError(RuntimeError):
    """Fail-closed signal that a constructed subsystem does not match mode."""


def _paper_service_for_mode(current_mode):
    """The single, sole path from a ModeService-resolved mode to a paper
    service. Nothing else in this module constructs a paper service.

    This same function is used two ways: (a) as ModeService's
    subsystem_builder, so a transition itself validates that construction
    succeeds before the transition is allowed to commit, and (b) again at
    startup, after the mode is resolved, to build the service actually
    wired into the running server. Because both calls go through this one
    function for the same resolved mode, the two can never disagree.
    """
    if current_mode == "SYNTHETIC_PAPER":
        return build_synthetic_demonstration_service()
    if current_mode in ("OFF", "RESEARCH", "MT5_DEMO_MANUAL"):
        # The forward-paper engine is unrelated to Phase 5 MT5 execution;
        # it stays disabled in MT5_DEMO_MANUAL exactly as it does in OFF/
        # RESEARCH.
        return DisabledPaperService()
    # The three remaining MT5 modes can never reach here: ModeService.request_transition
    # rejects them during the availability check, before any subsystem_builder
    # call, and no other caller may request one either. This branch exists as
    # a defensive invariant, not a reachable path.
    raise ModeSubsystemConfigurationError(
        "no Phase 3 subsystem-construction rule exists for mode {!r}".format(current_mode)
    )


def _validate_subsystem_consistency(current_mode, paper_service):
    """Fail closed if the constructed subsystem set does not exactly match
    the authoritative capability set of the resolved current mode."""
    if current_mode in ("OFF", "RESEARCH", "MT5_DEMO_MANUAL"):
        consistent = (
            isinstance(paper_service, DisabledPaperService) and not paper_service.enabled
        )
    elif current_mode == "SYNTHETIC_PAPER":
        consistent = (
            isinstance(paper_service, ForwardPaperService)
            and paper_service.enabled
            and getattr(paper_service, "is_synthetic_demonstration", False)
        )
    else:
        consistent = False
    if not consistent:
        raise ModeSubsystemConfigurationError(
            "{}: mode={!r} constructed paper_service={}".format(
                MODE_SUBSYSTEM_CONFIGURATION_MISMATCH, current_mode, type(paper_service).__name__,
            )
        )


def _signal_service_preflight_for_mode(current_mode):
    """Side-effect-free construction used ONLY to validate, during a
    ModeService transition attempt, that a signal service *could* be
    constructed for the requested mode. Used exclusively as (part of)
    ModeService's ``subsystem_builder`` — see
    ``_subsystem_builder_for_mode`` — which is exercised on every
    transition attempt, including from automated tests, and must
    therefore never touch the filesystem regardless of mode. The object
    this returns is discarded by ModeService immediately after the
    construction-succeeds check; it is never wired into anything real.
    Real runtime construction is ``_signal_service_for_mode`` below."""
    if current_mode in ("RESEARCH", "SYNTHETIC_PAPER"):
        return signal_service_module.in_memory_service(operating_mode=current_mode)
    if current_mode in ("OFF", "MT5_DEMO_MANUAL"):
        # Signal proposal generation is not part of MT5_DEMO_MANUAL's
        # capability grant (see mode_service._CAPABILITY_MATRIX); an
        # operator building an order intent supplies an already-generated
        # governed proposal (e.g. from a RESEARCH/SYNTHETIC_PAPER session)
        # rather than generating one while execution capabilities are
        # active.
        return DisabledSignalService(operating_mode=current_mode)
    raise ModeSubsystemConfigurationError(
        "no Phase 4 signal-service preflight rule exists for mode {!r}".format(current_mode)
    )


def _signal_service_for_mode(current_mode):
    """The single, sole path from a ModeService-resolved mode to the REAL
    runtime signal-intelligence service (TRL-R2-006/Phase 4) — the object
    actually wired into the running server or a CLI invocation, called
    only *after* a mode has already been resolved and validated (mirroring
    ``_paper_service_for_mode``'s role for the paper engine). Never used as
    ModeService's subsystem_builder (see ``_signal_service_preflight_for_mode``
    for that side-effect-free path); this function's RESEARCH mapping
    constructs a real, durable ``LocalSignalStore``-backed service on
    purpose, which must not happen merely to check whether a transition
    *would* succeed.

    Both RESEARCH and SYNTHETIC_PAPER use SignalIntelligenceService's own
    bare-construction default (LocalSignalStore), matching
    ForwardPaperService's durable-by-default convention — proposal and
    audit history survive an application/CLI restart for either mode
    (Founder correction, 2026-08-01: an earlier draft kept SYNTHETIC_PAPER
    in-memory only; that was rejected — synthetic evaluations are still
    real governed evidence worth auditing, and losing that history was
    never actually required by anything in the R2-006 contract). Both
    modes share the one durable store; every persisted proposal already
    carries its own ``operating_mode`` and ``sample_label`` fields, so
    RESEARCH and SYNTHETIC_PAPER records can never become indistinguishable
    even though they live in the same append-only timeline (see
    ``TRL_R2_006_SIGNAL_INTELLIGENCE_EVIDENCE.md``).
    """
    if current_mode in ("RESEARCH", "SYNTHETIC_PAPER"):
        return SignalIntelligenceService(operating_mode=current_mode)
    if current_mode in ("OFF", "MT5_DEMO_MANUAL"):
        return DisabledSignalService(operating_mode=current_mode)
    # The three remaining MT5 modes can never reach here for the same
    # reason _paper_service_for_mode's MT5 branch can't: ModeService
    # rejects them during the availability check before any
    # subsystem_builder call.
    raise ModeSubsystemConfigurationError(
        "no Phase 4 signal-service construction rule exists for mode {!r}".format(current_mode)
    )


def _validate_signal_subsystem_consistency(current_mode, signal_service):
    """Fail closed if the constructed signal-intelligence subsystem does
    not exactly match the authoritative capability set of the resolved
    current mode."""
    if current_mode in ("OFF", "MT5_DEMO_MANUAL"):
        consistent = isinstance(signal_service, DisabledSignalService) and not signal_service.enabled
    elif current_mode in ("RESEARCH", "SYNTHETIC_PAPER"):
        consistent = (
            isinstance(signal_service, SignalIntelligenceService)
            and signal_service.enabled
            and signal_service.operating_mode == current_mode
        )
    else:
        consistent = False
    if not consistent:
        raise ModeSubsystemConfigurationError(
            "{}: mode={!r} constructed signal_service={}".format(
                MODE_SUBSYSTEM_CONFIGURATION_MISMATCH, current_mode, type(signal_service).__name__,
            )
        )


def _execution_adapter_for_mode(current_mode):
    """The single, sole path from a resolved mode to an MT5 execution
    adapter TIER. Constructing ``RealMT5ExecutionAdapter`` here is safe
    and side-effect-free (mirrors ``LocalMT5ReadOnlyConnector``): it never
    imports MetaTrader5 and never opens a broker session merely by being
    instantiated — the import and the session both happen lazily, only
    inside a later adapter method call that ``mt5_execution_service``
    itself only reaches after ModeService has already granted the
    relevant capability. OFF/RESEARCH/SYNTHETIC_PAPER always get the
    disabled adapter, which cannot import MetaTrader5 under any call."""
    if current_mode == "MT5_DEMO_MANUAL":
        return mt5_execution_adapter.RealMT5ExecutionAdapter()
    if current_mode in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
        return mt5_execution_adapter.disabled_adapter()
    raise ModeSubsystemConfigurationError(
        "no Phase 5 execution-adapter construction rule exists for mode {!r}".format(current_mode)
    )


def _execution_service_preflight_for_mode(current_mode):
    """Side-effect-free construction used ONLY to validate, during a
    ModeService transition attempt, that an execution service *could* be
    constructed for the requested mode. Discarded immediately afterward;
    never wired into anything real. See ``_execution_service_for_mode``
    for the real runtime construction path."""
    if current_mode in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
        return mt5_execution_service.disabled_service(operating_mode=current_mode)
    if current_mode == "MT5_DEMO_MANUAL":
        return mt5_execution_service.ExecutionService(adapter=_execution_adapter_for_mode(current_mode))
    raise ModeSubsystemConfigurationError(
        "no Phase 5 execution-service preflight rule exists for mode {!r}".format(current_mode)
    )


def _execution_service_for_mode(current_mode, mode_service_instance, journal=None, account_fingerprint=None):
    """The real runtime execution service, wired to the live ModeService
    instance (so every capability check reflects the actual current mode,
    not the mode at construction time) and, in MT5_DEMO_MANUAL, the real
    adapter tier. Called only after a mode has already been resolved."""
    if current_mode in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
        return mt5_execution_service.disabled_service(operating_mode=current_mode)
    if current_mode == "MT5_DEMO_MANUAL":
        from .mt5_execution_journal import ExecutionJournalWriter
        return mt5_execution_service.ExecutionService(
            adapter=_execution_adapter_for_mode(current_mode),
            mode_service=mode_service_instance,
            journal=journal if journal is not None else ExecutionJournalWriter(),
            account_fingerprint=account_fingerprint or mt5_execution_service.account_fingerprint_from_environment(),
        )
    raise ModeSubsystemConfigurationError(
        "no Phase 5 execution-service construction rule exists for mode {!r}".format(current_mode)
    )


def _validate_execution_subsystem_consistency(current_mode, execution_service_instance):
    if current_mode in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
        consistent = (
            isinstance(execution_service_instance, mt5_execution_service.DisabledExecutionService)
            and not execution_service_instance.enabled
        )
    elif current_mode == "MT5_DEMO_MANUAL":
        consistent = (
            isinstance(execution_service_instance, mt5_execution_service.ExecutionService)
            and execution_service_instance.enabled
        )
    else:
        consistent = False
    if not consistent:
        raise ModeSubsystemConfigurationError(
            "{}: mode={!r} constructed execution_service={}".format(
                MODE_SUBSYSTEM_CONFIGURATION_MISMATCH, current_mode, type(execution_service_instance).__name__,
            )
        )


def _basket_service_for_mode(current_mode, mode_service_instance, journal=None, account_fingerprint=None):
    """The real runtime Phase 6 (TRL-R2-009) basket-execution service,
    constructed only after a mode has already been resolved — mirrors
    ``_execution_service_for_mode`` exactly, including its adapter-tier
    selection rule (``_execution_adapter_for_mode``) and its default
    journal/account-fingerprint construction, so both services always
    agree on which adapter tier, which durable journal file, and which
    account fingerprint are in force for a given mode: no second adapter
    tier, no second journal file, no second fingerprint source is ever
    introduced. Never reaches into ``ExecutionService``'s private
    attributes — mt5_execution_service.py is Phase 5 and stays untouched
    (Section 1.1); this function reconstructs the identical inputs from
    the same side-effect-free construction rules instead."""
    if current_mode in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
        return basket_execution_service.disabled_basket_service(operating_mode=current_mode)
    if current_mode == "MT5_DEMO_MANUAL":
        from .mt5_execution_journal import ExecutionJournalWriter
        return basket_execution_service.BasketExecutionService(
            adapter=_execution_adapter_for_mode(current_mode),
            mode_service=mode_service_instance,
            journal=journal if journal is not None else ExecutionJournalWriter(),
            account_fingerprint=account_fingerprint or mt5_execution_service.account_fingerprint_from_environment(),
        )
    raise ModeSubsystemConfigurationError(
        "no Phase 6 basket-service construction rule exists for mode {!r}".format(current_mode)
    )


def _validate_basket_subsystem_consistency(current_mode, basket_service_instance):
    if current_mode in ("OFF", "RESEARCH", "SYNTHETIC_PAPER"):
        consistent = (
            isinstance(basket_service_instance, basket_execution_service.DisabledBasketExecutionService)
            and not basket_service_instance.enabled
        )
    elif current_mode == "MT5_DEMO_MANUAL":
        consistent = (
            isinstance(basket_service_instance, basket_execution_service.BasketExecutionService)
            and basket_service_instance.enabled
        )
    else:
        consistent = False
    if not consistent:
        raise ModeSubsystemConfigurationError(
            "{}: mode={!r} constructed basket_service={}".format(
                MODE_SUBSYSTEM_CONFIGURATION_MISMATCH, current_mode, type(basket_service_instance).__name__,
            )
        )


def _market_intelligence_service_preflight_for_mode(current_mode):
    """Side-effect-free construction used ONLY to validate, during a
    ModeService transition attempt, that a Market Intelligence V0 (TRL
    CORTEX V0, TRL-R2-010) service *could* be constructed for the
    requested mode. Discarded immediately afterward; never wired into
    anything real, never touches the durable journal file. See
    ``_market_intelligence_service_for_mode`` for the real runtime
    construction path."""
    if current_mode in ("RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL"):
        from .market_intelligence_journal import in_memory_mi_journal_writer
        return market_intelligence_service.MarketIntelligenceService(journal=in_memory_mi_journal_writer())
    if current_mode == "OFF":
        return market_intelligence_service.disabled_service(operating_mode=current_mode)
    raise ModeSubsystemConfigurationError(
        "no Phase 6A Market Intelligence preflight rule exists for mode {!r}".format(current_mode)
    )


def _market_intelligence_service_for_mode(current_mode, mode_service_instance, journal=None):
    """The real runtime Market Intelligence V0 service (TRL-R2-010),
    granted in RESEARCH/SYNTHETIC_PAPER/MT5_DEMO_MANUAL exactly per the
    ``market_intelligence_research`` capability grant
    (``mode_service._CAPABILITY_MATRIX``) — never in OFF or any other MT5
    mode. Uses its own dedicated, durable Market Intelligence journal file
    (Section 17), wholly separate from the Phase 5/6 execution journal
    ``_execution_service_for_mode``/``_basket_service_for_mode`` share."""
    if current_mode in ("RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL"):
        from .market_intelligence_journal import MarketIntelligenceJournalWriter
        return market_intelligence_service.MarketIntelligenceService(
            mode_service=mode_service_instance,
            journal=journal if journal is not None else MarketIntelligenceJournalWriter(),
        )
    if current_mode == "OFF":
        return market_intelligence_service.disabled_service(operating_mode=current_mode)
    raise ModeSubsystemConfigurationError(
        "no Phase 6A Market Intelligence construction rule exists for mode {!r}".format(current_mode)
    )


def _validate_market_intelligence_subsystem_consistency(current_mode, mi_service_instance):
    if current_mode == "OFF":
        consistent = (
            isinstance(mi_service_instance, market_intelligence_service.DisabledMarketIntelligenceService)
            and not mi_service_instance.enabled
        )
    elif current_mode in ("RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL"):
        consistent = (
            isinstance(mi_service_instance, market_intelligence_service.MarketIntelligenceService)
            and mi_service_instance.enabled
        )
    else:
        consistent = False
    if not consistent:
        raise ModeSubsystemConfigurationError(
            "{}: mode={!r} constructed market_intelligence_service={}".format(
                MODE_SUBSYSTEM_CONFIGURATION_MISMATCH, current_mode, type(mi_service_instance).__name__,
            )
        )


def _market_data_replay_service_preflight_for_mode(current_mode):
    """Side-effect-free construction used ONLY to validate, during a
    ModeService transition attempt, that a Market Data Fabric and Replay V0
    (TRL CORTEX DATA FABRIC V0, TRL-R2-011) service *could* be constructed
    for the requested mode. Discarded immediately afterward; never wired
    into anything real, never touches the durable journal or dataset
    storage. See ``_market_data_replay_service_for_mode`` for the real
    runtime construction path."""
    if current_mode in ("RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL"):
        from .market_data_replay_journal import in_memory_mdr_journal_writer
        from .market_data_replay_storage import InMemoryDatasetStorage
        return market_data_replay_service.MarketDataReplayService(
            journal=in_memory_mdr_journal_writer(), storage=InMemoryDatasetStorage(),
        )
    if current_mode == "OFF":
        return market_data_replay_service.disabled_service(operating_mode=current_mode)
    raise ModeSubsystemConfigurationError(
        "no Phase 6B Market Data Fabric preflight rule exists for mode {!r}".format(current_mode)
    )


def _market_data_replay_service_for_mode(current_mode, mode_service_instance, journal=None, storage=None):
    """The real runtime Market Data Fabric and Replay V0 service
    (TRL-R2-011), granted in RESEARCH/SYNTHETIC_PAPER/MT5_DEMO_MANUAL
    exactly per the ``market_data_research`` capability grant
    (``mode_service._CAPABILITY_MATRIX``) -- never in OFF or any other MT5
    mode. Uses its own dedicated, durable Market Data Fabric journal file
    and dataset storage directory (Section 17.1), wholly separate from the
    Phase 5/6 execution journal and the R2-010 Market Intelligence
    journal."""
    if current_mode in ("RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL"):
        from .market_data_replay_journal import MarketDataReplayJournalWriter
        from .market_data_replay_storage import LocalDatasetStorage
        return market_data_replay_service.MarketDataReplayService(
            mode_service=mode_service_instance,
            journal=journal if journal is not None else MarketDataReplayJournalWriter(),
            storage=storage if storage is not None else LocalDatasetStorage(),
        )
    if current_mode == "OFF":
        return market_data_replay_service.disabled_service(operating_mode=current_mode)
    raise ModeSubsystemConfigurationError(
        "no Phase 6B Market Data Fabric construction rule exists for mode {!r}".format(current_mode)
    )


def _validate_market_data_replay_subsystem_consistency(current_mode, mdr_service_instance):
    if current_mode == "OFF":
        consistent = (
            isinstance(mdr_service_instance, market_data_replay_service.DisabledMarketDataReplayService)
            and not mdr_service_instance.enabled
        )
    elif current_mode in ("RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL"):
        consistent = (
            isinstance(mdr_service_instance, market_data_replay_service.MarketDataReplayService)
            and mdr_service_instance.enabled
        )
    else:
        consistent = False
    if not consistent:
        raise ModeSubsystemConfigurationError(
            "{}: mode={!r} constructed market_data_replay_service={}".format(
                MODE_SUBSYSTEM_CONFIGURATION_MISMATCH, current_mode, type(mdr_service_instance).__name__,
            )
        )


def _scalping_adapter_for_mode(current_mode):
    """TRL-R2-012: the single path from a resolved mode to an ALSAKKAF
    SCALPING MT5 adapter TIER. Real for every mode that already implies
    MT5 read access in this program (RESEARCH, MT5_DEMO_MANUAL,
    MT5_DEMO_AUTOMATED) so ANALYZE_ONLY can read live demo quotes/bars in
    any of them (contract Section 3 does not gate ANALYZE_ONLY on a
    ModeService capability, only DEMO_AUTO is capability-gated); disabled
    everywhere else (OFF, SYNTHETIC_PAPER). Constructing
    ``RealScalpingMT5Adapter`` here is side-effect-free -- it never
    imports MetaTrader5 or opens a broker session merely by being
    instantiated, mirroring ``_execution_adapter_for_mode``."""
    if current_mode in ("RESEARCH", "MT5_DEMO_MANUAL", "MT5_DEMO_AUTOMATED"):
        return alsakkaf_scalping_mt5.RealScalpingMT5Adapter()
    return alsakkaf_scalping_mt5.disabled_adapter()


def _scalping_service_for_mode(
    current_mode, mode_service_instance, journal=None, symbol_map_store=None,
    market_intelligence_service_instance=None, scratch_directory=None,
):
    """The real runtime ALSAKKAF SCALPING service (TRL-R2-012). Unlike
    Phase 5/6/6A/6B's disabled-vs-enabled services, this service is always
    constructed and always enabled -- its own product state machine
    (Section 3) is independent of ``ModeService.current_mode`` and starts
    at ``OFF`` regardless; only a transition into ``DEMO_AUTO`` performs a
    live capability check against ``mode_service_instance`` at request
    time (``ScalpingService.request_state_change``), never at
    construction time. This keeps read-only status/list/inspect/journal
    operations available in every mode, matching contract Section 5.2."""
    from .alsakkaf_scalping_journal import ScalpingJournalWriter
    from .alsakkaf_scalping_data import SymbolMapStore

    return alsakkaf_scalping_service.ScalpingService(
        journal=journal if journal is not None else ScalpingJournalWriter(),
        adapter=_scalping_adapter_for_mode(current_mode),
        symbol_map_store=symbol_map_store if symbol_map_store is not None else SymbolMapStore(),
        mode_service=mode_service_instance,
        market_intelligence_service=market_intelligence_service_instance,
        scratch_directory=scratch_directory,
    )


def _scalping_service_preflight_for_mode(current_mode):
    """Side-effect-free construction used ONLY to validate, during a
    ModeService transition attempt, that an ALSAKKAF SCALPING service
    *could* be constructed for the requested mode. In-memory journal and
    symbol-map store; discarded immediately afterward; never wired into
    anything real."""
    from .alsakkaf_scalping_journal import in_memory_journal_writer
    from .alsakkaf_scalping_data import InMemorySymbolMapStore

    return alsakkaf_scalping_service.ScalpingService(
        journal=in_memory_journal_writer(),
        adapter=_scalping_adapter_for_mode(current_mode),
        symbol_map_store=InMemorySymbolMapStore(),
    )


def _subsystem_builder_for_mode(current_mode):
    """The combined subsystem builder ModeService actually calls: builds
    the paper service, a side-effect-free signal-intelligence *preflight*
    service, and a side-effect-free execution-adapter preflight service
    for the requested mode, so a transition validates that every
    construction would succeed before it is allowed to commit (Section
    5's SUBSYSTEM_ACTIVATION_FAILED gate applies to all three), without
    touching any durable store or broker session. The real runtime
    services are constructed separately, only after a transition/startup
    mode resolution has already completed — see ``_signal_service_for_mode``
    and ``_execution_service_for_mode`` and their call sites in ``main()``."""
    paper_service = _paper_service_for_mode(current_mode)
    signal_service_instance = _signal_service_preflight_for_mode(current_mode)
    execution_service_instance = _execution_service_preflight_for_mode(current_mode)
    market_intelligence_service_instance = _market_intelligence_service_preflight_for_mode(current_mode)
    market_data_replay_service_instance = _market_data_replay_service_preflight_for_mode(current_mode)
    scalping_service_instance = _scalping_service_preflight_for_mode(current_mode)
    return (
        paper_service, signal_service_instance, execution_service_instance,
        market_intelligence_service_instance, market_data_replay_service_instance,
        scalping_service_instance,
    )


def run_server(
    port=DEFAULT_PORT,
    open_browser=True,
    market_data_service=None,
    official_news_service=None,
    paper_service=None,
    mode_service=None,
    signal_service=None,
    execution_service=None,
    basket_service=None,
    market_intelligence_service_instance=None,
    market_data_replay_service_instance=None,
    scalping_service_instance=None,
):
    """Run until Ctrl+C, always closing the listening socket on exit."""
    server = create_server(
        port,
        market_data_service=market_data_service,
        official_news_service=official_news_service,
        paper_service=paper_service,
        mode_service=mode_service,
        signal_service=signal_service,
        execution_service=execution_service,
        basket_service=basket_service,
        market_intelligence_service_instance=market_intelligence_service_instance,
        market_data_replay_service_instance=market_data_replay_service_instance,
        scalping_service_instance=scalping_service_instance,
    )
    actual_port = server.server_address[1]
    url = "http://{}:{}/".format(BIND_HOST, actual_port)
    print("{} {}".format(APPLICATION_NAME, APPLICATION_VERSION))
    active_market_service = market_data_service or getattr(
        server, "market_data_service", None
    )
    if not isinstance(active_market_service, MarketDataService):
        active_market_service = MarketDataService()
    configuration = active_market_service.configuration
    if configuration.enabled:
        print(
            "LOCAL MT5 READ-ONLY | {} | {} | {} BARS | NO STRATEGY OR ORDERS".format(
                configuration.symbol,
                ",".join(configuration.timeframes),
                configuration.bars,
            )
        )
    else:
        print("PAPER/RESEARCH ONLY | COMMITTED SYNTHETIC DATA | NO EXTERNAL ORDERS")
    active_news_service = official_news_service or getattr(
        server, "official_news_service", None
    )
    if not isinstance(active_news_service, OfficialNewsService):
        active_news_service = OfficialNewsService()
    if active_news_service.configuration.enabled:
        print(
            "OFFICIAL-SOURCE INFORMATION ONLY | LOCAL RETRIEVAL | NO STRATEGY OR TRADE INSTRUCTION"
        )
    else:
        print("OFFICIAL NEWS DISABLED | STARTUP NETWORK-SILENT")
    active_paper_service = paper_service or vars(server).get("paper_service")
    if not isinstance(active_paper_service, (ForwardPaperService, DisabledPaperService)):
        active_paper_service = DisabledPaperService()
    if active_paper_service.enabled:
        if getattr(active_paper_service, "is_synthetic_demonstration", False):
            print(
                "FORWARD PAPER ENGINE — SYNTHETIC DEMONSTRATION MODE | "
                "NOT LIVE MARKET DATA | IN-MEMORY ONLY | NO BROKER ORDERS"
            )
        else:
            print("FORWARD PAPER ENGINE ENABLED | LOCAL TIMELINE | NO BROKER ORDERS")
    else:
        print("FORWARD PAPER ENGINE DISABLED | STORAGE NOT CONSTRUCTED")
        print(
            "  To rehearse: python -m trading_lab_app.mode_cli request-mode "
            "SYNTHETIC_PAPER (then restart), or the deprecated "
            "--enable-forward-paper-demo flag"
        )
    active_signal_service = signal_service or vars(server).get("signal_service")
    if not isinstance(active_signal_service, (SignalIntelligenceService, DisabledSignalService)):
        active_signal_service = DisabledSignalService()
    if active_signal_service.enabled:
        print(
            "SIGNAL INTELLIGENCE ENABLED | {} | RESEARCH PROPOSALS ONLY | "
            "NO BROKER EXECUTION".format(active_signal_service.operating_mode)
        )
    else:
        print("SIGNAL INTELLIGENCE DISABLED | OFF MODE")
    active_execution_service = execution_service or vars(server).get("execution_service")
    if not isinstance(active_execution_service, (mt5_execution_service.ExecutionService, mt5_execution_service.DisabledExecutionService)):
        active_execution_service = mt5_execution_service.disabled_service()
    if active_execution_service.enabled:
        print(
            "MT5 EXECUTION ENABLED | DEMO-MANUAL ONLY | LIVE EXECUTION DISABLED | "
            "MANUAL CONFIRMATION REQUIRED FOR EVERY ORDER"
        )
        if not active_execution_service.account_fingerprint.configured:
            print("  No approved MT5 demo account fingerprint is configured (external blocker).")
    else:
        print("MT5 EXECUTION DISABLED | {} MODE".format(active_execution_service.operating_mode))
    active_basket_service = basket_service or vars(server).get("basket_service")
    if not isinstance(active_basket_service, (basket_execution_service.BasketExecutionService, basket_execution_service.DisabledBasketExecutionService)):
        active_basket_service = basket_execution_service.disabled_basket_service()
    if active_basket_service.enabled:
        print(
            "BASKET EXECUTION ENABLED | DEMO-MANUAL ONLY | LIVE/AUTOMATED EXECUTION DISABLED | "
            "MANUAL CONFIRMATION REQUIRED FOR EVERY CHILD SEND"
        )
    else:
        print("BASKET EXECUTION DISABLED | {} MODE".format(active_basket_service.operating_mode))
    active_mi_service = market_intelligence_service_instance or vars(server).get("market_intelligence_service_instance")
    if not isinstance(active_mi_service, (market_intelligence_service.MarketIntelligenceService, market_intelligence_service.DisabledMarketIntelligenceService)):
        active_mi_service = market_intelligence_service.disabled_service()
    if active_mi_service.enabled:
        print(
            "TRL CORTEX V0 MARKET INTELLIGENCE ENABLED | RESEARCH ONLY | LIVE EXECUTION DISABLED | "
            + market_intelligence_data.EXECUTION_HANDOFF_STATUS
        )
    else:
        print("TRL CORTEX V0 MARKET INTELLIGENCE DISABLED | {} MODE".format(active_mi_service.operating_mode))
    active_mdr_service = market_data_replay_service_instance or vars(server).get("market_data_replay_service_instance")
    if not isinstance(active_mdr_service, (market_data_replay_service.MarketDataReplayService, market_data_replay_service.DisabledMarketDataReplayService)):
        active_mdr_service = market_data_replay_service.disabled_service()
    if active_mdr_service.enabled:
        print("TRL CORTEX DATA FABRIC V0 ENABLED | RESEARCH ONLY | LOCAL DATA ONLY | LIVE DATA DISABLED | EXECUTION DISABLED")
    else:
        print("TRL CORTEX DATA FABRIC V0 DISABLED | {} MODE".format(active_mdr_service.operating_mode))
    active_mode_service = mode_service or getattr(server, "mode_service", None)
    if not isinstance(active_mode_service, ModeService):
        active_mode_service = in_memory_mode_service()
    mode_status = active_mode_service.mode_status_document()
    print(
        "OPERATING MODE: {} | BROKER EXECUTION: {} | AUTOMATED TRADING: {}".format(
            mode_status["current_mode"],
            "AVAILABLE" if mode_status["broker_execution_available"] else "UNAVAILABLE",
            "AVAILABLE" if mode_status["automated_trading_available"] else "UNAVAILABLE",
        )
    )
    if mode_status["startup_diagnostic_code"] != "OK":
        print(
            "  Mode startup recovery: {}".format(mode_status["startup_diagnostic_code"])
        )
    print("Local dashboard: {}".format(url))
    print("Press Ctrl+C to stop.")
    try:
        if open_browser:
            webbrowser.open(url, new=2)
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nShutdown requested.")
    finally:
        try:
            active_paper = vars(server).get("paper_service")
            if active_paper is not None:
                while active_paper.shutdown() is False:
                    pass
        finally:
            try:
                active_signal = vars(server).get("signal_service")
                if active_signal is not None:
                    while active_signal.shutdown() is False:
                        pass
            finally:
                try:
                    active_execution = vars(server).get("execution_service")
                    if active_execution is not None:
                        while active_execution.shutdown() is False:
                            pass
                finally:
                    try:
                        active_basket = vars(server).get("basket_service")
                        if active_basket is not None:
                            while active_basket.shutdown() is False:
                                pass
                    finally:
                        try:
                            active_mi = vars(server).get("market_intelligence_service_instance")
                            if active_mi is not None:
                                while active_mi.shutdown() is False:
                                    pass
                        finally:
                            try:
                                active_mdr = vars(server).get("market_data_replay_service_instance")
                                if active_mdr is not None:
                                    while active_mdr.shutdown() is False:
                                        pass
                            finally:
                                try:
                                    news_service = getattr(server, "official_news_service", None)
                                    if news_service is not None:
                                        while news_service.shutdown() is False:
                                            pass
                                finally:
                                    try:
                                        active_mode_service.shutdown()
                                    finally:
                                        server.server_close()
        print("Local dashboard stopped.")
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
    if not args.enable_official_news and args.official_news_refresh_seconds is not None:
        print(
            "Official-news refresh controls require --enable-official-news; news remains disabled.",
            file=sys.stderr,
        )
        return 2
    if not args.enable_mt5_read_only and any(
        value is not None for value in (args.mt5_symbol, args.mt5_timeframes, args.mt5_bars)
    ):
        print(
            "MT5 controls require --enable-mt5-read-only; synthetic mode remains the default.",
            file=sys.stderr,
        )
        return 2
    if args.enable_mt5_read_only and args.mt5_symbol is None:
        print(
            "Explicit MT5 read-only mode requires --mt5-symbol with the exact broker symbol.",
            file=sys.stderr,
        )
        return 2
    if args.enable_forward_paper_engine and args.enable_forward_paper_demo:
        print(
            "--enable-forward-paper-engine and --enable-forward-paper-demo "
            "are mutually exclusive; choose one.",
            file=sys.stderr,
        )
        return 2
    if args.enable_forward_paper_engine:
        print(
            "{}: no approved Phase 3 operating mode authorizes the legacy "
            "--enable-forward-paper-engine capability. The application did not "
            "start the forward-paper engine. No external connection or paper "
            "execution occurred. Adding an eighth mode is prohibited without "
            "Founder approval. Use --enable-forward-paper-demo, or "
            "'python -m trading_lab_app.mode_cli request-mode SYNTHETIC_PAPER', "
            "for a governed alternative.".format(LEGACY_FORWARD_PAPER_MODE_UNAVAILABLE),
            file=sys.stderr,
        )
        return 2
    configuration = MT5ReadOnlyConfiguration(
        enabled=args.enable_mt5_read_only,
        symbol=args.mt5_symbol or "XAUUSD",
        timeframes=args.mt5_timeframes or market_data.DEFAULT_TIMEFRAMES,
        bars=args.mt5_bars or 500,
    )
    market_service = MarketDataService(configuration)
    news_configuration = OfficialNewsConfiguration(
        enabled=args.enable_official_news,
        refresh_seconds=args.official_news_refresh_seconds or 900,
    )
    official_news_service = OfficialNewsService(news_configuration)
    # The one authoritative decision path: ModeService resolved mode ->
    # capability check -> paper-service AND signal-service construction. No
    # flag may construct or activate either subsystem outside it.
    operating_mode_service = ModeService(subsystem_builder=_subsystem_builder_for_mode)
    if args.enable_forward_paper_demo:
        if operating_mode_service.current_mode == "SYNTHETIC_PAPER":
            # Already there (e.g. a prior mode_cli.py transition persisted
            # it): nothing to request. INVALID_TRANSITION would otherwise
            # reject a same-mode request, which must not make an already-
            # correct startup fail closed.
            pass
        else:
            transition = operating_mode_service.request_transition(
                "SYNTHETIC_PAPER",
                actor="LEGACY_CLI_FLAG:--enable-forward-paper-demo",
                reason="deprecated --enable-forward-paper-demo compatibility request",
                actor_channel="LOCAL_OPERATOR",
            )
            if transition.outcome != "ACCEPTED":
                print(
                    "Unable to activate SYNTHETIC_PAPER via the deprecated "
                    "--enable-forward-paper-demo flag: outcome={} reason_code={}".format(
                        transition.outcome, transition.reason_code,
                    ),
                    file=sys.stderr,
                )
                return 2
        print(
            "DEPRECATED: --enable-forward-paper-demo now requests SYNTHETIC_PAPER "
            "through the governed operating-mode state machine. Prefer: "
            "python -m trading_lab_app.mode_cli request-mode SYNTHETIC_PAPER"
        )
    paper_service = _paper_service_for_mode(operating_mode_service.current_mode)
    signal_service_instance = _signal_service_for_mode(operating_mode_service.current_mode)
    # One shared journal writer and one shared account-fingerprint config
    # for this process, handed to both the Phase 5 execution service and
    # the Phase 6 basket service — the exact same durable journal file and
    # the exact same fingerprint, never a second instance of either.
    shared_journal = None
    shared_account_fingerprint = None
    if operating_mode_service.current_mode == "MT5_DEMO_MANUAL":
        from .mt5_execution_journal import ExecutionJournalWriter
        shared_journal = ExecutionJournalWriter()
        shared_account_fingerprint = mt5_execution_service.account_fingerprint_from_environment()
    execution_service_instance = _execution_service_for_mode(
        operating_mode_service.current_mode, operating_mode_service,
        journal=shared_journal, account_fingerprint=shared_account_fingerprint,
    )
    basket_service_instance = _basket_service_for_mode(
        operating_mode_service.current_mode, operating_mode_service,
        journal=shared_journal, account_fingerprint=shared_account_fingerprint,
    )
    # Market Intelligence V0 (TRL-R2-010) uses its own dedicated, durable
    # journal file (Section 17) — never the Phase 5/6 shared_journal above.
    market_intelligence_service_instance = _market_intelligence_service_for_mode(
        operating_mode_service.current_mode, operating_mode_service,
    )
    # Market Data Fabric and Replay V0 (TRL-R2-011) uses its own dedicated,
    # durable journal file and dataset storage directory (Section 17.1) --
    # never the Phase 5/6 shared_journal, and never the R2-010 Market
    # Intelligence journal.
    market_data_replay_service_instance = _market_data_replay_service_for_mode(
        operating_mode_service.current_mode, operating_mode_service,
    )
    # ALSAKKAF SCALPING (TRL-R2-012) uses its own dedicated, durable
    # journal file and symbol-map store -- never the Phase 5/6
    # shared_journal, never the R2-010/R2-011 journals. It reuses the same
    # market_intelligence_service_instance already built above so the
    # Section 8.3 bridge and a direct R2-010 caller always agree on which
    # journal/mode-service authority is in force.
    scalping_service_instance = _scalping_service_for_mode(
        operating_mode_service.current_mode, operating_mode_service,
        market_intelligence_service_instance=market_intelligence_service_instance,
    )
    try:
        _validate_subsystem_consistency(operating_mode_service.current_mode, paper_service)
        _validate_signal_subsystem_consistency(operating_mode_service.current_mode, signal_service_instance)
        _validate_execution_subsystem_consistency(operating_mode_service.current_mode, execution_service_instance)
        _validate_basket_subsystem_consistency(operating_mode_service.current_mode, basket_service_instance)
        _validate_market_intelligence_subsystem_consistency(operating_mode_service.current_mode, market_intelligence_service_instance)
        _validate_market_data_replay_subsystem_consistency(operating_mode_service.current_mode, market_data_replay_service_instance)
    except ModeSubsystemConfigurationError as error:
        print(str(error), file=sys.stderr)
        return 2
    try:
        return run_server(
            port=args.port,
            open_browser=not args.no_browser,
            market_data_service=market_service,
            official_news_service=official_news_service,
            paper_service=paper_service,
            mode_service=operating_mode_service,
            signal_service=signal_service_instance,
            execution_service=execution_service_instance,
            basket_service=basket_service_instance,
            market_intelligence_service_instance=market_intelligence_service_instance,
            market_data_replay_service_instance=market_data_replay_service_instance,
            scalping_service_instance=scalping_service_instance,
        )
    except OSError as error:
        print(
            "Unable to start the local dashboard on {}:{}: {}".format(
                BIND_HOST, args.port, error,
            ),
            file=sys.stderr,
        )
        return 2
    except ValueError as error:
        print("Invalid local server configuration: {}".format(error), file=sys.stderr)
        return 2
