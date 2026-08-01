"""Local-only operator CLI for the TRL-R2-007 Phase 5 MT5 execution adapter.

Every mutating command here requires ModeService to already be in
MT5_DEMO_MANUAL (set via ``python -m trading_lab_app.mode_cli request-mode
MT5_DEMO_MANUAL``) and reports the exact fail-closed reason code
otherwise. There is no HTTP route that can check, confirm, or send an
order — this CLI is the only path, mirroring ``mode_cli.py``'s own
"local-only mutation" convention.

Usage (from the Trading_Lab directory):
    python -B -W error -m trading_lab_app.mt5_execution_cli mt5-status
    python -B -W error -m trading_lab_app.mt5_execution_cli mt5-dependency-status
    python -B -W error -m trading_lab_app.mt5_execution_cli mt5-terminal-status
    python -B -W error -m trading_lab_app.mt5_execution_cli mt5-account-status
    python -B -W error -m trading_lab_app.mt5_execution_cli mt5-symbol-status XAUUSD
    python -B -W error -m trading_lab_app.mt5_execution_cli execution-capabilities
    python -B -W error -m trading_lab_app.mt5_execution_cli execution-journal --limit 20
    python -B -W error -m trading_lab_app.mt5_execution_cli inspect-proposal proposal.json
    python -B -W error -m trading_lab_app.mt5_execution_cli build-order-intent proposal.json
    python -B -W error -m trading_lab_app.mt5_execution_cli check-order <order_intent_id>
    python -B -W error -m trading_lab_app.mt5_execution_cli send-demo-order <order_intent_id>
    python -B -W error -m trading_lab_app.mt5_execution_cli send-demo-order <order_intent_id> --confirm <code>
    python -B -W error -m trading_lab_app.mt5_execution_cli inspect-execution <order_intent_id>
"""

import argparse
import json
from pathlib import Path
import sys

from . import mode_service
from . import mt5_execution_service


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _build_services():
    # Reuse app.py's single combined subsystem-construction path so a
    # CLI-driven mode transition validates real subsystem construction
    # the same way a server-startup transition does. Imported lazily to
    # avoid import-time coupling beyond what this one call needs (mirrors
    # mode_cli.py's own ``_build_service``).
    from .app import _subsystem_builder_for_mode, _execution_service_for_mode

    mode_svc = mode_service.ModeService(subsystem_builder=_subsystem_builder_for_mode)
    execution_svc = _execution_service_for_mode(mode_svc.current_mode, mode_svc)
    return mode_svc, execution_svc


def _load_proposal_argument(value):
    """Accept a path to a JSON file, or literal JSON text starting with
    '{'. Phase 5 does not couple this CLI to SignalIntelligenceService's
    store; an operator supplies an already-generated governed proposal
    document explicitly."""
    text = value
    if not value.lstrip().startswith("{"):
        path = Path(value)
        if not path.is_file():
            print("Proposal input is neither literal JSON nor an existing file: {}".format(value), file=sys.stderr)
            return None
        text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError as error:
        print("Proposal input is not valid JSON: {}".format(error), file=sys.stderr)
        return None


def _handle_service_error(error):
    print(json.dumps({"outcome": "REJECTED", "reason_code": error.reason_code}, sort_keys=True))
    return 1


def _cmd_mt5_status(_args):
    _, execution_svc = _build_services()
    _print_json(execution_svc.status_document())
    return 0


def _cmd_mt5_dependency_status(_args):
    _, execution_svc = _build_services()
    _print_json(execution_svc.dependency_status_document())
    return 0


def _cmd_mt5_terminal_status(_args):
    _, execution_svc = _build_services()
    _print_json(execution_svc.terminal_status_document())
    return 0


def _cmd_mt5_account_status(_args):
    _, execution_svc = _build_services()
    _print_json(execution_svc.account_status_document())
    return 0


def _cmd_mt5_symbol_status(args):
    _, execution_svc = _build_services()
    _print_json(execution_svc.symbol_status_document(args.symbol))
    return 0


def _cmd_execution_capabilities(_args):
    _, execution_svc = _build_services()
    _print_json(execution_svc.capabilities_document())
    return 0


def _cmd_execution_journal(args):
    _, execution_svc = _build_services()
    _print_json(execution_svc.journal_document(limit=args.limit))
    return 0


def _cmd_inspect_proposal(args):
    proposal = _load_proposal_argument(args.proposal)
    if proposal is None:
        return 2
    _, execution_svc = _build_services()
    _print_json(execution_svc.inspect_proposal(proposal))
    return 0


def _cmd_build_order_intent(args):
    proposal = _load_proposal_argument(args.proposal)
    if proposal is None:
        return 2
    _, execution_svc = _build_services()
    try:
        intent = execution_svc.build_order_intent(proposal)
    except mt5_execution_service.ExecutionServiceError as error:
        return _handle_service_error(error)
    _print_json(intent)
    return 0


def _cmd_check_order(args):
    _, execution_svc = _build_services()
    try:
        result = execution_svc.order_check(args.order_intent_id)
    except mt5_execution_service.ExecutionServiceError as error:
        return _handle_service_error(error)
    _print_json(result)
    return 0


def _cmd_send_demo_order(args):
    _, execution_svc = _build_services()
    if args.confirm is None:
        try:
            challenge = execution_svc.request_confirmation(args.order_intent_id)
        except mt5_execution_service.ExecutionServiceError as error:
            return _handle_service_error(error)
        print(
            "Manual confirmation required. Re-run this exact command with "
            "--confirm {} before {} to submit the order.".format(
                challenge["challenge_code"], challenge["expires_at_utc"],
            )
        )
        _print_json(challenge)
        return 0
    try:
        result = execution_svc.confirm_and_send(
            args.order_intent_id, args.confirm, actor_channel="LOCAL_OPERATOR",
        )
    except mt5_execution_service.ExecutionServiceError as error:
        return _handle_service_error(error)
    _print_json(result)
    return 0


def _cmd_inspect_execution(args):
    _, execution_svc = _build_services()
    _print_json(execution_svc.execution_result_document(args.order_intent_id))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app.mt5_execution_cli",
        description=(
            "Local-only operator control for the Phase 5 (TRL-R2-007) MT5 "
            "demo-manual execution adapter. No HTTP route can check, "
            "confirm, or send an order; this CLI is the only mutation path."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("mt5-status", help="show overall execution status")
    subparsers.add_parser("mt5-dependency-status", help="show MetaTrader5 dependency availability")
    subparsers.add_parser("mt5-terminal-status", help="show terminal connection status")
    subparsers.add_parser("mt5-account-status", help="show redacted account status")

    symbol_status = subparsers.add_parser("mt5-symbol-status", help="show symbol status")
    symbol_status.add_argument("symbol", help="exact broker-native symbol")

    subparsers.add_parser("execution-capabilities", help="show granted execution capabilities")

    journal = subparsers.add_parser("execution-journal", help="show the append-only execution journal")
    journal.add_argument("--limit", type=int, default=None, help="most recent N events only")

    inspect_proposal = subparsers.add_parser("inspect-proposal", help="validate a governed proposal document")
    inspect_proposal.add_argument("proposal", help="path to a proposal JSON file, or literal JSON")

    build_intent = subparsers.add_parser("build-order-intent", help="construct (or reuse) a governed order intent")
    build_intent.add_argument("proposal", help="path to a proposal JSON file, or literal JSON")

    check_order = subparsers.add_parser("check-order", help="run order_check for an existing order intent")
    check_order.add_argument("order_intent_id", help="exact order_intent_id")

    send_order = subparsers.add_parser(
        "send-demo-order",
        help="request manual confirmation, or (with --confirm) send the order",
    )
    send_order.add_argument("order_intent_id", help="exact order_intent_id")
    send_order.add_argument(
        "--confirm", default=None,
        help="the exact confirmation challenge code shown by a prior invocation without --confirm",
    )

    inspect_execution = subparsers.add_parser("inspect-execution", help="show the current state of an order intent")
    inspect_execution.add_argument("order_intent_id", help="exact order_intent_id")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "mt5-status": _cmd_mt5_status,
        "mt5-dependency-status": _cmd_mt5_dependency_status,
        "mt5-terminal-status": _cmd_mt5_terminal_status,
        "mt5-account-status": _cmd_mt5_account_status,
        "mt5-symbol-status": _cmd_mt5_symbol_status,
        "execution-capabilities": _cmd_execution_capabilities,
        "execution-journal": _cmd_execution_journal,
        "inspect-proposal": _cmd_inspect_proposal,
        "build-order-intent": _cmd_build_order_intent,
        "check-order": _cmd_check_order,
        "send-demo-order": _cmd_send_demo_order,
        "inspect-execution": _cmd_inspect_execution,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
