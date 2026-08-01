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
    return paper_service, signal_service_instance, execution_service_instance


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
    try:
        _validate_subsystem_consistency(operating_mode_service.current_mode, paper_service)
        _validate_signal_subsystem_consistency(operating_mode_service.current_mode, signal_service_instance)
        _validate_execution_subsystem_consistency(operating_mode_service.current_mode, execution_service_instance)
        _validate_basket_subsystem_consistency(operating_mode_service.current_mode, basket_service_instance)
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
