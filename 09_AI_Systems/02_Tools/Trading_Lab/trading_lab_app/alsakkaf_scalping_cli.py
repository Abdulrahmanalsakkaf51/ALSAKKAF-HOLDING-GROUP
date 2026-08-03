"""Local-only operator CLI for ALSAKKAF SCALPING (TRL-R2-012).

Usage (from the Trading_Lab directory):
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-status
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-preflight XAUUSD
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-discover-symbols XAUUSD
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-save-symbol-map XAUUSD XAUUSDm
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-configure-profile XAUUSD ALSAKKAF_PRECISION_SCALPING
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-start-demo-auto
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-pause
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-resume
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-emergency-stop
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-reset-emergency-stop
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-list-cycles
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-inspect-cycle <cycle_id>
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-list-owned-orders
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-list-owned-positions
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-reconcile
    python -B -W error -m trading_lab_app.alsakkaf_scalping_cli scalping-journal --limit 20
"""

import argparse
import json
import sys

from . import mode_service
from .alsakkaf_scalping_service import ScalpingServiceError


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str))


def _build_service():
    from .app import _scalping_service_for_mode

    mode_svc = mode_service.ModeService()
    return _scalping_service_for_mode(mode_svc.current_mode, mode_svc)


def _handle_service_error(error):
    print(json.dumps({"outcome": "REJECTED", "reason_code": error.reason_code}, sort_keys=True))
    return 1


def _cmd_status(_args):
    service = _build_service()
    _print_json(service.status_document())
    return 0


def _cmd_preflight(args):
    service = _build_service()
    try:
        _print_json(service.run_preflight(args.instrument))
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_discover_symbols(args):
    service = _build_service()
    _print_json({"candidates": service.discover_symbols(args.instrument)})
    return 0


def _cmd_save_symbol_map(args):
    service = _build_service()
    try:
        _print_json(service.save_symbol_map(args.instrument, args.broker_symbol))
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_configure_profile(args):
    service = _build_service()
    try:
        _print_json(service.configure_profile(args.instrument, args.profile_id))
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_analyze(_args):
    print(json.dumps({
        "outcome": "REJECTED",
        "reason_code": "SCALPING_ANALYZE_REQUIRES_BAR_INPUT",
        "detail": "scalping-analyze requires bar data supplied via the HTTP API or dashboard in this V0 CLI",
    }, sort_keys=True))
    return 1


def _cmd_start_demo_auto(_args):
    service = _build_service()
    try:
        _print_json({"product_state": service.request_state_change("DEMO_AUTO")})
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_pause(_args):
    service = _build_service()
    try:
        _print_json({"product_state": service.request_state_change("PAUSED")})
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_resume(_args):
    service = _build_service()
    try:
        _print_json({"product_state": service.request_state_change("ANALYZE_ONLY")})
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_emergency_stop(_args):
    service = _build_service()
    try:
        _print_json({"product_state": service.request_state_change("EMERGENCY_STOP")})
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_reset_emergency_stop(_args):
    service = _build_service()
    try:
        _print_json({"product_state": service.reset_emergency_stop()})
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_run_cycle(_args):
    print(json.dumps({
        "outcome": "REJECTED",
        "reason_code": "SCALPING_RUN_CYCLE_REQUIRES_BAR_INPUT",
        "detail": "scalping-run-cycle requires bar data supplied via the HTTP API or dashboard in this V0 CLI",
    }, sort_keys=True))
    return 1


def _cmd_list_cycles(_args):
    service = _build_service()
    _print_json({"cycles": service.list_cycles()})
    return 0


def _cmd_inspect_cycle(args):
    service = _build_service()
    try:
        _print_json(service.inspect_cycle(args.cycle_id))
    except ScalpingServiceError as error:
        return _handle_service_error(error)
    return 0


def _cmd_list_owned_orders(_args):
    service = _build_service()
    _print_json({"owned_orders": service.list_owned_orders()})
    return 0


def _cmd_list_owned_positions(_args):
    service = _build_service()
    _print_json({"owned_positions": service.list_owned_positions()})
    return 0


def _cmd_reconcile(_args):
    service = _build_service()
    _print_json(service.reconcile())
    return 0


def _cmd_journal(args):
    service = _build_service()
    _print_json({"events": service.journal_tail(limit=args.limit)})
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app.alsakkaf_scalping_cli",
        description=(
            "Local-only operator control for ALSAKKAF SCALPING (TRL-R2-012). "
            "DEMO_AUTO automation requires MT5_DEMO_AUTOMATED plus a passing "
            "twenty-check demo-account preflight on every cycle."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("scalping-status", help="show overall ALSAKKAF SCALPING status")

    preflight = subparsers.add_parser("scalping-preflight", help="run the twenty-check demo-only safety gate")
    preflight.add_argument("instrument", help="canonical instrument, e.g. XAUUSD")

    discover = subparsers.add_parser("scalping-discover-symbols", help="list candidate broker symbols")
    discover.add_argument("instrument", help="canonical instrument, e.g. XAUUSD")

    save_map = subparsers.add_parser("scalping-save-symbol-map", help="save an explicit canonical-to-broker mapping")
    save_map.add_argument("instrument", help="canonical instrument, e.g. XAUUSD")
    save_map.add_argument("broker_symbol", help="exact broker-native symbol")

    configure = subparsers.add_parser("scalping-configure-profile", help="assign a strategy profile to an instrument")
    configure.add_argument("instrument", help="canonical instrument, e.g. XAUUSD")
    configure.add_argument("profile_id", help="ALSAKKAF_PRECISION_SCALPING / ALSAKKAF_BREAKOUT_LADDER / ALSAKKAF_INTRADAY")

    subparsers.add_parser("scalping-analyze", help="(HTTP/dashboard only in this V0 CLI)")
    subparsers.add_parser("scalping-start-demo-auto", help="transition to DEMO_AUTO")
    subparsers.add_parser("scalping-pause", help="transition to PAUSED")
    subparsers.add_parser("scalping-resume", help="transition to ANALYZE_ONLY")
    subparsers.add_parser("scalping-emergency-stop", help="latch EMERGENCY_STOP and flatten owned exposure")
    subparsers.add_parser("scalping-reset-emergency-stop", help="clear the EMERGENCY_STOP latch")
    subparsers.add_parser("scalping-run-cycle", help="(HTTP/dashboard only in this V0 CLI)")
    subparsers.add_parser("scalping-list-cycles", help="list every recorded cycle")

    inspect_cycle = subparsers.add_parser("scalping-inspect-cycle", help="show one cycle's full record")
    inspect_cycle.add_argument("cycle_id", help="exact cycle_id")

    subparsers.add_parser("scalping-list-owned-orders", help="list ALSAKKAF-owned pending orders")
    subparsers.add_parser("scalping-list-owned-positions", help="list ALSAKKAF-owned open positions")
    subparsers.add_parser("scalping-reconcile", help="reconcile owned orders/positions against MT5")

    journal = subparsers.add_parser("scalping-journal", help="show the append-only ALSAKKAF SCALPING journal")
    journal.add_argument("--limit", type=int, default=100, help="most recent N events only")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "scalping-status": _cmd_status,
        "scalping-preflight": _cmd_preflight,
        "scalping-discover-symbols": _cmd_discover_symbols,
        "scalping-save-symbol-map": _cmd_save_symbol_map,
        "scalping-configure-profile": _cmd_configure_profile,
        "scalping-analyze": _cmd_analyze,
        "scalping-start-demo-auto": _cmd_start_demo_auto,
        "scalping-pause": _cmd_pause,
        "scalping-resume": _cmd_resume,
        "scalping-emergency-stop": _cmd_emergency_stop,
        "scalping-reset-emergency-stop": _cmd_reset_emergency_stop,
        "scalping-run-cycle": _cmd_run_cycle,
        "scalping-list-cycles": _cmd_list_cycles,
        "scalping-inspect-cycle": _cmd_inspect_cycle,
        "scalping-list-owned-orders": _cmd_list_owned_orders,
        "scalping-list-owned-positions": _cmd_list_owned_positions,
        "scalping-reconcile": _cmd_reconcile,
        "scalping-journal": _cmd_journal,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
