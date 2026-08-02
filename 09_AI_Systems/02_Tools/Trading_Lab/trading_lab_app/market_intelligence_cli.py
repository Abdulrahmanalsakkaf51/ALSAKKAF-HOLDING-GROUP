"""Local-only operator CLI for the TRL-R2-010 Market Intelligence V0 service
(TRL CORTEX V0).

Every mutating command (``analyze-market-snapshot``,
``preview-opportunity-basket``, ``record-opportunity-outcome``) requires
``ModeService`` to already grant ``market_intelligence_research``
(``RESEARCH``, ``SYNTHETIC_PAPER``, or ``MT5_DEMO_MANUAL`` — set via
``python -m trading_lab_app.mode_cli request-mode <mode>``) and reports the
exact fail-closed reason code otherwise. Every read-only command
(``market-intelligence-status``, ``list-opportunities``,
``inspect-opportunity``, ``list-virtual-opportunities``,
``inspect-virtual-opportunity``, ``market-intelligence-journal``) remains
available regardless of mode, including ``OFF``. There is no HTTP mutation
route for anything in this module — this CLI is the only mutation path
(Section 15.1).

Usage (from the Trading_Lab directory):
    python -B -W error -m trading_lab_app.market_intelligence_cli market-intelligence-status
    python -B -W error -m trading_lab_app.market_intelligence_cli analyze-market-snapshot <input-json-path>
    python -B -W error -m trading_lab_app.market_intelligence_cli list-opportunities --status TRADE_CANDIDATE
    python -B -W error -m trading_lab_app.market_intelligence_cli inspect-opportunity <opportunity_id>
    python -B -W error -m trading_lab_app.market_intelligence_cli list-virtual-opportunities <opportunity_id>
    python -B -W error -m trading_lab_app.market_intelligence_cli inspect-virtual-opportunity <virtual_opportunity_id>
    python -B -W error -m trading_lab_app.market_intelligence_cli preview-opportunity-basket <opportunity_id>
    python -B -W error -m trading_lab_app.market_intelligence_cli record-opportunity-outcome <opportunity_id> <outcome-fixture-path>
    python -B -W error -m trading_lab_app.market_intelligence_cli market-intelligence-journal --limit 20
"""

import argparse
import json
import re
import sys

from . import market_intelligence_data as mid
from . import market_intelligence_service as svc
from . import mode_service


_OPPORTUNITY_ID_PATTERN = re.compile(r"^opp_[0-9a-f]{32}$")
_VIRTUAL_OPPORTUNITY_ID_PATTERN = re.compile(r"^vop_[0-9a-f]{32}$")


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _print_banners():
    print(
        "TRL CORTEX V0 | RESEARCH ONLY | LIVE EXECUTION DISABLED | NOT FINANCIAL ADVICE | "
        + mid.EXECUTION_HANDOFF_STATUS
    )


def _build_services():
    from .app import _subsystem_builder_for_mode, _market_intelligence_service_for_mode

    mode_svc = mode_service.ModeService(subsystem_builder=_subsystem_builder_for_mode)
    mi_svc = _market_intelligence_service_for_mode(mode_svc.current_mode, mode_svc)
    return mode_svc, mi_svc


def _handle_service_error(error):
    print(json.dumps({"outcome": "REJECTED", "reason_code": error.reason_code}, sort_keys=True))
    return 1


def _safe_opportunity_id(value):
    if not _OPPORTUNITY_ID_PATTERN.fullmatch(value or ""):
        print(json.dumps({"outcome": "REJECTED", "reason_code": "MARKET_INTELLIGENCE_OPPORTUNITY_NOT_FOUND"}, sort_keys=True))
        return None
    return value


def _safe_virtual_opportunity_id(value):
    if not _VIRTUAL_OPPORTUNITY_ID_PATTERN.fullmatch(value or ""):
        print(json.dumps({"outcome": "REJECTED", "reason_code": "MARKET_INTELLIGENCE_VIRTUAL_OPPORTUNITY_NOT_FOUND"}, sort_keys=True))
        return None
    return value


def _cmd_status(_args):
    _, mi_svc = _build_services()
    _print_banners()
    _print_json(mi_svc.status_document())
    return 0


def _cmd_analyze(args):
    _, mi_svc = _build_services()
    _print_banners()
    try:
        result = mi_svc.analyze_market_snapshot(args.input_json_path)
    except svc.MarketIntelligenceServiceError as error:
        return _handle_service_error(error)
    _print_json(result)
    return 0


def _cmd_list_opportunities(args):
    _, mi_svc = _build_services()
    _print_json(mi_svc.list_opportunities_document(status=args.status))
    return 0


def _cmd_inspect_opportunity(args):
    _, mi_svc = _build_services()
    opportunity_id = _safe_opportunity_id(args.opportunity_id)
    if opportunity_id is None:
        return 1
    document = mi_svc.inspect_opportunity_document(opportunity_id)
    _print_json(document)
    return 0 if document.get("found") else 1


def _cmd_list_virtual_opportunities(args):
    _, mi_svc = _build_services()
    opportunity_id = _safe_opportunity_id(args.opportunity_id)
    if opportunity_id is None:
        return 1
    _print_json(mi_svc.list_virtual_opportunities_document(opportunity_id))
    return 0


def _cmd_inspect_virtual_opportunity(args):
    _, mi_svc = _build_services()
    virtual_opportunity_id = _safe_virtual_opportunity_id(args.virtual_opportunity_id)
    if virtual_opportunity_id is None:
        return 1
    document = mi_svc.inspect_virtual_opportunity_document(virtual_opportunity_id)
    _print_json(document)
    return 0 if document.get("found") else 1


def _cmd_preview_opportunity_basket(args):
    _, mi_svc = _build_services()
    _print_banners()
    opportunity_id = _safe_opportunity_id(args.opportunity_id)
    if opportunity_id is None:
        return 1
    try:
        preview = mi_svc.preview_opportunity_basket(opportunity_id)
    except svc.MarketIntelligenceServiceError as error:
        return _handle_service_error(error)
    _print_json(preview)
    return 0


def _cmd_record_opportunity_outcome(args):
    _, mi_svc = _build_services()
    _print_banners()
    opportunity_id = _safe_opportunity_id(args.opportunity_id)
    if opportunity_id is None:
        return 1
    try:
        raw_bytes = svc.load_analysis_input_bytes(args.outcome_fixture_path)
        outcome_document = svc.parse_analysis_input_bytes(raw_bytes)
    except svc.MarketIntelligenceServiceError as error:
        return _handle_service_error(error)
    try:
        telemetry = mi_svc.record_opportunity_outcome(opportunity_id, outcome_document)
    except svc.MarketIntelligenceServiceError as error:
        return _handle_service_error(error)
    _print_json(telemetry)
    return 0


def _cmd_journal(args):
    _, mi_svc = _build_services()
    document = mi_svc.journal_document(limit=None)
    events = document["events"]
    if args.since:
        indices = [index for index, event in enumerate(events) if event["event_id"] == args.since]
        events = events[indices[0] + 1:] if indices else events
    if args.limit is not None:
        events = events[-args.limit:]
    document = dict(document)
    document["events"] = events
    document["event_count"] = len(events)
    _print_json(document)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app.market_intelligence_cli",
        description=(
            "Local-only operator control for TRL-R2-010 Market Intelligence "
            "V0 (TRL CORTEX V0). Research-only, non-executable. No HTTP "
            "route can analyze a snapshot, generate a preview, or record "
            "an outcome — this CLI is the only mutation path."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("market-intelligence-status", help="show capability/mode status")

    analyze = subparsers.add_parser("analyze-market-snapshot", help="validate and record one analysis input bundle")
    analyze.add_argument("input_json_path", help="exact local path to a TRL_MARKET_INTELLIGENCE_ANALYSIS_INPUT.v1 JSON file")

    list_opportunities = subparsers.add_parser("list-opportunities", help="list recorded opportunity cards")
    list_opportunities.add_argument("--status", choices=mid.DECISION_STATUSES, default=None)

    inspect_opportunity = subparsers.add_parser("inspect-opportunity", help="show one opportunity card, its decision, lattice and preview")
    inspect_opportunity.add_argument("opportunity_id", help="exact opportunity_id")

    list_vops = subparsers.add_parser("list-virtual-opportunities", help="list the virtual opportunity lattice for one opportunity")
    list_vops.add_argument("opportunity_id", help="exact opportunity_id")

    inspect_vop = subparsers.add_parser("inspect-virtual-opportunity", help="show one virtual opportunity")
    inspect_vop.add_argument("virtual_opportunity_id", help="exact virtual_opportunity_id")

    preview = subparsers.add_parser("preview-opportunity-basket", help="generate (or reuse) the non-executable basket preview for a TRADE_CANDIDATE opportunity")
    preview.add_argument("opportunity_id", help="exact opportunity_id")

    outcome = subparsers.add_parser("record-opportunity-outcome", help="record immutable outcome telemetry for one opportunity")
    outcome.add_argument("opportunity_id", help="exact opportunity_id")
    outcome.add_argument("outcome_fixture_path", help="exact local path to an outcome telemetry input JSON file")

    journal = subparsers.add_parser("market-intelligence-journal", help="show the Market Intelligence journal event slice")
    journal.add_argument("--since", default=None, help="only events strictly after this event_id")
    journal.add_argument("--limit", type=int, default=None, help="most recent N events only")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "market-intelligence-status": _cmd_status,
        "analyze-market-snapshot": _cmd_analyze,
        "list-opportunities": _cmd_list_opportunities,
        "inspect-opportunity": _cmd_inspect_opportunity,
        "list-virtual-opportunities": _cmd_list_virtual_opportunities,
        "inspect-virtual-opportunity": _cmd_inspect_virtual_opportunity,
        "preview-opportunity-basket": _cmd_preview_opportunity_basket,
        "record-opportunity-outcome": _cmd_record_opportunity_outcome,
        "market-intelligence-journal": _cmd_journal,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
