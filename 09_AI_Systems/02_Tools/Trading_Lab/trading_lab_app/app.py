"""Command-line lifecycle for the Windows-first local dashboard."""

import argparse
import sys
import webbrowser

from . import APPLICATION_NAME, APPLICATION_VERSION
from . import market_data
from .mt5_service import MT5ReadOnlyConfiguration, MarketDataService
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


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app",
        description=(
            "Run the local PAPER/RESEARCH ONLY dashboard on 127.0.0.1. "
            "Synthetic mode is the default; local MT5 data is explicit and read-only."
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
        "--no-browser",
        action="store_true",
        help="do not open the local dashboard in the default browser",
    )
    parser.add_argument("--version", action="version", version=APPLICATION_VERSION)
    return parser


def run_server(port=DEFAULT_PORT, open_browser=True, market_data_service=None):
    """Run until Ctrl+C, always closing the listening socket on exit."""
    server = create_server(port, market_data_service=market_data_service)
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
    print("Local dashboard: {}".format(url))
    print("Press Ctrl+C to stop.")
    try:
        if open_browser:
            webbrowser.open(url, new=2)
        server.serve_forever(poll_interval=0.25)
    except KeyboardInterrupt:
        print("\nShutdown requested.")
    finally:
        server.server_close()
        print("Local dashboard stopped.")
    return 0


def main(argv=None):
    args = build_parser().parse_args(argv)
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
    configuration = MT5ReadOnlyConfiguration(
        enabled=args.enable_mt5_read_only,
        symbol=args.mt5_symbol or "XAUUSD",
        timeframes=args.mt5_timeframes or market_data.DEFAULT_TIMEFRAMES,
        bars=args.mt5_bars or 500,
    )
    market_service = MarketDataService(configuration)
    try:
        return run_server(
            port=args.port,
            open_browser=not args.no_browser,
            market_data_service=market_service,
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
