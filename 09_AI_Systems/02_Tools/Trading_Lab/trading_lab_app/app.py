"""Command-line lifecycle for the Windows-first local dashboard."""

import argparse
import sys
import webbrowser

from . import APPLICATION_NAME, APPLICATION_VERSION
from .server import BIND_HOST, DEFAULT_PORT, create_server


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app",
        description=(
            "Run the local PAPER/RESEARCH ONLY synthetic dashboard on "
            "127.0.0.1."
        ),
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="local loopback port (default: %(default)s)",
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="do not open the local dashboard in the default browser",
    )
    parser.add_argument("--version", action="version", version=APPLICATION_VERSION)
    return parser


def run_server(port=DEFAULT_PORT, open_browser=True):
    """Run until Ctrl+C, always closing the listening socket on exit."""
    server = create_server(port)
    actual_port = server.server_address[1]
    url = "http://{}:{}/".format(BIND_HOST, actual_port)
    print("{} {}".format(APPLICATION_NAME, APPLICATION_VERSION))
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
    try:
        return run_server(port=args.port, open_browser=not args.no_browser)
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
