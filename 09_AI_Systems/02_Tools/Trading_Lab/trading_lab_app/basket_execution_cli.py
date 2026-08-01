"""Local-only operator CLI for the TRL-R2-009 Phase 6 controlled basket
execution service.

Every mutating command here requires ``ModeService`` to already be in
``MT5_DEMO_MANUAL`` with ``manual_basket_execution`` granted (set via
``python -m trading_lab_app.mode_cli request-mode MT5_DEMO_MANUAL``) and
reports the exact fail-closed reason code otherwise. There is no HTTP route
that can build, check, confirm, or send a basket child — this CLI is the
only mutation path, mirroring ``mt5_execution_cli.py``'s own "local-only
mutation" convention exactly (Section 34).

Usage (from the Trading_Lab directory):
    python -B -W error -m trading_lab_app.basket_execution_cli basket-status
    python -B -W error -m trading_lab_app.basket_execution_cli inspect-basket <basket_id>
    python -B -W error -m trading_lab_app.basket_execution_cli build-basket <parent_order_intent_id>
    python -B -W error -m trading_lab_app.basket_execution_cli check-basket <basket_id>
    python -B -W error -m trading_lab_app.basket_execution_cli request-basket-confirmation <basket_id>
    python -B -W error -m trading_lab_app.basket_execution_cli confirm-basket <basket_id> "CONFIRM-BASKET <16-hex>"
    python -B -W error -m trading_lab_app.basket_execution_cli send-basket-next <basket_id>
    python -B -W error -m trading_lab_app.basket_execution_cli inspect-basket-child <basket_id> <basket_child_id>
    python -B -W error -m trading_lab_app.basket_execution_cli basket-journal --limit 20
"""

import argparse
import json
import sys

from . import mode_service
from . import basket_execution_service


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _build_services():
    # Reuse app.py's exact mode-transition/subsystem-construction path, and
    # its exact basket-service construction rule (same adapter tier, same
    # durable journal file, same account-fingerprint source the Phase 5 CLI
    # uses) — mirrors mt5_execution_cli.py's own ``_build_services``.
    from .app import _subsystem_builder_for_mode, _basket_service_for_mode

    mode_svc = mode_service.ModeService(subsystem_builder=_subsystem_builder_for_mode)
    basket_svc = _basket_service_for_mode(mode_svc.current_mode, mode_svc)
    return mode_svc, basket_svc


def _handle_service_error(error):
    print(json.dumps({"outcome": "REJECTED", "reason_code": error.reason_code}, sort_keys=True))
    return 1


def _print_banners():
    print("LIVE EXECUTION DISABLED | AUTOMATED EXECUTION DISABLED | MANUAL CONFIRMATION REQUIRED")


def _cmd_basket_status(_args):
    _, basket_svc = _build_services()
    _print_banners()
    _print_json(basket_svc.status_document())
    return 0


def _cmd_inspect_basket(args):
    _, basket_svc = _build_services()
    document = basket_svc.inspect_basket_document(args.basket_id)
    _print_json(document)
    return 0 if document.get("found") else 1


def _cmd_build_basket(args):
    _, basket_svc = _build_services()
    _print_banners()
    try:
        record = basket_svc.build_basket(args.parent_order_intent_id)
    except basket_execution_service.BasketExecutionServiceError as error:
        return _handle_service_error(error)
    _print_json(basket_svc.basket_status_document(record["basket_id"]))
    return 0


def _cmd_check_basket(args):
    _, basket_svc = _build_services()
    try:
        basket_svc.check_basket(args.basket_id)
    except basket_execution_service.BasketExecutionServiceError as error:
        return _handle_service_error(error)
    _print_json(basket_svc.basket_status_document(args.basket_id))
    return 0


def _cmd_request_basket_confirmation(args):
    _, basket_svc = _build_services()
    _print_banners()
    try:
        cycle = basket_svc.request_basket_confirmation(args.basket_id)
    except basket_execution_service.BasketExecutionServiceError as error:
        return _handle_service_error(error)
    from . import basket_execution_data as bed
    print(
        "Manual confirmation required. Enter exactly: {} before {} to accept "
        "this confirmation cycle.".format(
            bed.format_confirmation_entry(cycle["challenge_hex"]), cycle["expires_at_utc"],
        )
    )
    _print_json(cycle)
    return 0


def _cmd_confirm_basket(args):
    _, basket_svc = _build_services()
    _print_banners()
    try:
        record = basket_svc.confirm_basket(args.basket_id, args.entry_text, actor_channel="LOCAL_OPERATOR")
    except basket_execution_service.BasketExecutionServiceError as error:
        return _handle_service_error(error)
    _print_json(basket_svc.basket_status_document(record["basket_id"]))
    return 0


def _cmd_send_basket_next(args):
    _, basket_svc = _build_services()
    _print_banners()
    try:
        record = basket_svc.send_basket_next(args.basket_id)
    except basket_execution_service.BasketExecutionServiceError as error:
        return _handle_service_error(error)
    _print_json(basket_svc.basket_status_document(record["basket_id"]))
    return 0


def _cmd_inspect_basket_child(args):
    _, basket_svc = _build_services()
    document = basket_svc.inspect_basket_child_document(args.basket_id, args.basket_child_id)
    _print_json(document)
    return 0 if document.get("found") else 1


def _cmd_basket_journal(args):
    _, basket_svc = _build_services()
    _print_json(basket_svc.basket_journal_document(limit=args.limit))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app.basket_execution_cli",
        description=(
            "Local-only operator control for the Phase 6 (TRL-R2-009) "
            "controlled manual demo basket execution service. No HTTP route "
            "can build, check, confirm, or send a basket child; this CLI is "
            "the only mutation path."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("basket-status", help="show overall basket capability/status")

    inspect_basket = subparsers.add_parser("inspect-basket", help="show a basket's full plan and status rollup")
    inspect_basket.add_argument("basket_id", help="exact basket_id")

    build_basket = subparsers.add_parser("build-basket", help="construct (or reuse) a basket from an eligible parent order intent")
    build_basket.add_argument("parent_order_intent_id", help="exact parent order_intent_id")

    check_basket = subparsers.add_parser("check-basket", help="run the check for the next currently-required child")
    check_basket.add_argument("basket_id", help="exact basket_id")

    request_confirmation = subparsers.add_parser(
        "request-basket-confirmation",
        help="issue the exact challenge for the current confirmation cycle",
    )
    request_confirmation.add_argument("basket_id", help="exact basket_id")

    confirm_basket = subparsers.add_parser("confirm-basket", help="accept a confirmation cycle by exact challenge text")
    confirm_basket.add_argument("basket_id", help="exact basket_id")
    confirm_basket.add_argument("entry_text", help='exactly "CONFIRM-BASKET <16-hex-challenge>"')

    send_next = subparsers.add_parser(
        "send-basket-next",
        help="send exactly the service-computed next eligible child; takes no child-identifying argument",
    )
    send_next.add_argument("basket_id", help="exact basket_id")

    inspect_child = subparsers.add_parser("inspect-basket-child", help="show one basket child's full intent plus check/send history")
    inspect_child.add_argument("basket_id", help="exact basket_id")
    inspect_child.add_argument("basket_child_id", help="exact basket_child_id")

    journal = subparsers.add_parser("basket-journal", help="show the raw basket-scoped journal event slice")
    journal.add_argument("--limit", type=int, default=None, help="most recent N events only")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "basket-status": _cmd_basket_status,
        "inspect-basket": _cmd_inspect_basket,
        "build-basket": _cmd_build_basket,
        "check-basket": _cmd_check_basket,
        "request-basket-confirmation": _cmd_request_basket_confirmation,
        "confirm-basket": _cmd_confirm_basket,
        "send-basket-next": _cmd_send_basket_next,
        "inspect-basket-child": _cmd_inspect_basket_child,
        "basket-journal": _cmd_basket_journal,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
