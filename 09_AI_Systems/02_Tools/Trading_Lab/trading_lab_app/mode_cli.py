"""Local-only operator CLI for the operating-mode state machine.

This talks directly to the durable mode-state store; it does not require
the HTTP server to be running, and there is no HTTP route that can mutate
mode. Every mutating command here uses actor_channel="LOCAL_OPERATOR",
which is the only channel the mode service accepts a transition from
besides its own startup/system resolution.

Usage (from the Trading_Lab directory):
    python -B -W error -m trading_lab_app.mode_cli show-mode
    python -B -W error -m trading_lab_app.mode_cli list-modes
    python -B -W error -m trading_lab_app.mode_cli explain-mode SYNTHETIC_PAPER
    python -B -W error -m trading_lab_app.mode_cli request-mode RESEARCH --reason "start research"
    python -B -W error -m trading_lab_app.mode_cli transition-history --limit 10
"""

import argparse
import json
import sys

from . import mode_service


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _build_service():
    # Reuse app.py's single combined subsystem-construction path (paper
    # service + signal-intelligence service) so a CLI-driven transition
    # validates real subsystem construction the same way a server-startup
    # transition does, before the transition is allowed to commit. Imported
    # lazily to avoid any import-time coupling beyond what this one call
    # needs.
    from .app import _subsystem_builder_for_mode

    return mode_service.ModeService(subsystem_builder=_subsystem_builder_for_mode)


def _cmd_show_mode(_args):
    service = _build_service()
    _print_json(service.mode_status_document())
    return 0


def _cmd_list_modes(_args):
    service = _build_service()
    _print_json({
        "modes": list(mode_service.MODES),
        "available_modes": service.available_modes(),
        "unavailable_modes": service.unavailable_modes(),
    })
    return 0


def _cmd_explain_mode(args):
    try:
        mode_service.validate_mode(args.mode)
    except mode_service.ModeValidationError:
        print(
            "Unknown mode {!r}. Known modes: {}".format(
                args.mode, ", ".join(mode_service.MODES)
            ),
            file=sys.stderr,
        )
        return 2
    service = _build_service()
    _print_json(service.explain_mode(args.mode))
    return 0


def _cmd_request_mode(args):
    service = _build_service()
    result = service.request_transition(
        args.mode, actor="LOCAL_OPERATOR_CLI", reason=args.reason,
        actor_channel="LOCAL_OPERATOR",
    )
    _print_json({
        "outcome": result.outcome,
        "requested_mode": result.requested_mode,
        "previous_mode": result.previous_mode,
        "resulting_mode": result.resulting_mode,
        "reason_code": result.reason_code,
        "prerequisite_results": list(result.prerequisite_results),
    })
    return 0 if result.outcome == "ACCEPTED" else 1


def _cmd_transition_history(args):
    service = _build_service()
    _print_json(service.transition_history(limit=args.limit))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app.mode_cli",
        description=(
            "Local-only operator control for the Trading Lab operating-mode "
            "state machine. No HTTP route can mutate mode; this CLI is the "
            "only mutation path."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("show-mode", help="show the current mode and full status")

    subparsers.add_parser("list-modes", help="list all governed modes and their availability")

    explain = subparsers.add_parser("explain-mode", help="explain one mode in detail")
    explain.add_argument("mode", help="exact mode name, e.g. SYNTHETIC_PAPER")

    request = subparsers.add_parser("request-mode", help="request a transition to a mode")
    request.add_argument("mode", help="exact mode name to request")
    request.add_argument("--reason", default=None, help="optional bounded reason text")

    history = subparsers.add_parser("transition-history", help="show the audit event history")
    history.add_argument("--limit", type=int, default=None, help="most recent N events only")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "show-mode": _cmd_show_mode,
        "list-modes": _cmd_list_modes,
        "explain-mode": _cmd_explain_mode,
        "request-mode": _cmd_request_mode,
        "transition-history": _cmd_transition_history,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
