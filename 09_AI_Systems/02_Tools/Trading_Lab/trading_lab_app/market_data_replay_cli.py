"""Local-only operator CLI for the TRL-R2-011 Market Data Fabric and Replay
V0 service (TRL CORTEX DATA FABRIC V0).

Every mutating command (``import-market-data``, ``create-replay-session``,
``replay-next``, ``cancel-replay-session``) requires ``ModeService`` to
already grant ``market_data_research`` (``RESEARCH``, ``SYNTHETIC_PAPER``,
or ``MT5_DEMO_MANUAL`` -- set via
``python -m trading_lab_app.mode_cli request-mode <mode>``) and reports the
exact fail-closed reason code otherwise. Every read-only command
(``market-data-status``, ``list-market-datasets``, ``inspect-market-dataset``,
``list-replay-sessions``, ``inspect-replay-session``,
``inspect-replay-snapshot``, ``market-data-journal``) remains available
regardless of mode, including ``OFF``. There is no HTTP mutation route for
anything in this module -- this CLI is the only mutation path (Section 21).

Usage (from the Trading_Lab directory):
    python -B -W error -m trading_lab_app.market_data_replay_cli market-data-status
    python -B -W error -m trading_lab_app.market_data_replay_cli import-market-data <csv-path> --source-classification SYNTHETIC_FIXTURE --source-reference my-fixture
    python -B -W error -m trading_lab_app.market_data_replay_cli list-market-datasets --limit 20
    python -B -W error -m trading_lab_app.market_data_replay_cli inspect-market-dataset <dataset_id>
    python -B -W error -m trading_lab_app.market_data_replay_cli create-replay-session <dataset_id> --start-index 0 --end-index 9 --step-size 1
    python -B -W error -m trading_lab_app.market_data_replay_cli list-replay-sessions
    python -B -W error -m trading_lab_app.market_data_replay_cli inspect-replay-session <replay_session_id>
    python -B -W error -m trading_lab_app.market_data_replay_cli replay-next <replay_session_id>
    python -B -W error -m trading_lab_app.market_data_replay_cli inspect-replay-snapshot <replay_session_id>
    python -B -W error -m trading_lab_app.market_data_replay_cli cancel-replay-session <replay_session_id>
    python -B -W error -m trading_lab_app.market_data_replay_cli market-data-journal --tail 20
"""

import argparse
import json
import sys

from . import market_data_replay_data as mdd
from . import market_data_replay_service as svc
from . import mode_service


def _print_json(value):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2))


def _print_banners():
    print("TRL CORTEX DATA FABRIC V0 | RESEARCH ONLY | LOCAL DATA ONLY | LIVE DATA DISABLED | EXECUTION DISABLED")


def _build_services():
    from .app import _subsystem_builder_for_mode, _market_data_replay_service_for_mode

    mode_svc = mode_service.ModeService(subsystem_builder=_subsystem_builder_for_mode)
    mdr_svc = _market_data_replay_service_for_mode(mode_svc.current_mode, mode_svc)
    return mode_svc, mdr_svc


def _handle_service_error(error):
    print(json.dumps({"outcome": "REJECTED", "reason_code": error.reason_code}, sort_keys=True))
    return 1


def _safe_dataset_id(value):
    if not mdd.DATASET_ID_PATTERN.fullmatch(value or ""):
        print(json.dumps({"outcome": "REJECTED", "reason_code": "MARKET_DATA_DATASET_NOT_FOUND"}, sort_keys=True))
        return None
    return value


def _safe_replay_session_id(value):
    if not mdd.REPLAY_SESSION_ID_PATTERN.fullmatch(value or ""):
        print(json.dumps({"outcome": "REJECTED", "reason_code": "MARKET_DATA_REPLAY_SESSION_NOT_FOUND"}, sort_keys=True))
        return None
    return value


def _cmd_status(_args):
    _, mdr_svc = _build_services()
    _print_banners()
    _print_json(mdr_svc.status_document())
    return 0


def _cmd_import(args):
    _, mdr_svc = _build_services()
    _print_banners()
    try:
        manifest = mdr_svc.import_market_data(args.csv_path, args.source_classification, args.source_reference)
    except svc.MarketDataServiceError as error:
        return _handle_service_error(error)
    _print_json(manifest)
    return 0


def _cmd_list_datasets(args):
    _, mdr_svc = _build_services()
    try:
        document = mdr_svc.list_market_datasets_document(offset=args.offset, limit=args.limit)
    except svc.MarketDataServiceError as error:
        return _handle_service_error(error)
    _print_json(document)
    return 0


def _cmd_inspect_dataset(args):
    _, mdr_svc = _build_services()
    dataset_id = _safe_dataset_id(args.dataset_id)
    if dataset_id is None:
        return 1
    try:
        document = mdr_svc.inspect_market_dataset_document(dataset_id, offset=args.offset, limit=args.limit)
    except svc.MarketDataServiceError as error:
        return _handle_service_error(error)
    _print_json(document)
    return 0 if document.get("found") else 1


def _cmd_create_replay_session(args):
    _, mdr_svc = _build_services()
    _print_banners()
    dataset_id = _safe_dataset_id(args.dataset_id)
    if dataset_id is None:
        return 1
    try:
        document = mdr_svc.create_replay_session(dataset_id, args.start_index, args.end_index, args.step_size)
    except svc.MarketDataServiceError as error:
        return _handle_service_error(error)
    _print_json(document)
    return 0


def _cmd_list_replay_sessions(args):
    _, mdr_svc = _build_services()
    try:
        document = mdr_svc.list_replay_sessions_document(offset=args.offset, limit=args.limit)
    except svc.MarketDataServiceError as error:
        return _handle_service_error(error)
    _print_json(document)
    return 0


def _cmd_inspect_replay_session(args):
    _, mdr_svc = _build_services()
    replay_session_id = _safe_replay_session_id(args.replay_session_id)
    if replay_session_id is None:
        return 1
    document = mdr_svc.inspect_replay_session_document(replay_session_id)
    _print_json(document)
    return 0 if document.get("found") else 1


def _cmd_replay_next(args):
    _, mdr_svc = _build_services()
    _print_banners()
    replay_session_id = _safe_replay_session_id(args.replay_session_id)
    if replay_session_id is None:
        return 1
    try:
        document = mdr_svc.replay_next(replay_session_id)
    except svc.MarketDataServiceError as error:
        return _handle_service_error(error)
    _print_json(document)
    return 0


def _cmd_inspect_replay_snapshot(args):
    _, mdr_svc = _build_services()
    replay_session_id = _safe_replay_session_id(args.replay_session_id)
    if replay_session_id is None:
        return 1
    document = mdr_svc.inspect_replay_snapshot_document(replay_session_id)
    _print_json(document)
    return 0 if document.get("found") else 1


def _cmd_cancel_replay_session(args):
    _, mdr_svc = _build_services()
    _print_banners()
    replay_session_id = _safe_replay_session_id(args.replay_session_id)
    if replay_session_id is None:
        return 1
    try:
        document = mdr_svc.cancel_replay_session(replay_session_id)
    except svc.MarketDataServiceError as error:
        return _handle_service_error(error)
    _print_json(document)
    return 0


def _cmd_journal(args):
    _, mdr_svc = _build_services()
    try:
        document = mdr_svc.journal_document(tail=args.tail)
    except svc.MarketDataServiceError as error:
        return _handle_service_error(error)
    _print_json(document)
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="trading_lab_app.market_data_replay_cli",
        description=(
            "Local-only operator control for TRL-R2-011 Market Data Fabric "
            "and Replay V0 (TRL CORTEX DATA FABRIC V0). Research-only, "
            "local-only, non-executable. No HTTP route can import data, "
            "create a replay session, advance replay, or cancel a replay "
            "session -- this CLI is the only mutation path."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("market-data-status", help="show capability/mode status")

    import_cmd = subparsers.add_parser("import-market-data", help="strictly import one local CSV dataset")
    import_cmd.add_argument("csv_path", help="exact local path to a strict CSV file (Section 7)")
    import_cmd.add_argument("--source-classification", required=True, choices=mdd.SOURCE_CLASSIFICATIONS)
    import_cmd.add_argument("--source-reference", required=True, help="bounded logical source label, maximum 256 Unicode code points")

    list_datasets = subparsers.add_parser("list-market-datasets", help="list accepted dataset manifests")
    list_datasets.add_argument("--offset", type=int, default=None)
    list_datasets.add_argument("--limit", type=int, default=None)

    inspect_dataset = subparsers.add_parser("inspect-market-dataset", help="show one dataset manifest and its paginated bar references")
    inspect_dataset.add_argument("dataset_id", help="exact dataset_id")
    inspect_dataset.add_argument("--offset", type=int, default=None)
    inspect_dataset.add_argument("--limit", type=int, default=None)

    create_session = subparsers.add_parser("create-replay-session", help="create (or deterministically reuse) one replay session")
    create_session.add_argument("dataset_id", help="exact dataset_id")
    create_session.add_argument("--start-index", type=int, required=True)
    create_session.add_argument("--end-index", type=int, required=True)
    create_session.add_argument("--step-size", type=int, required=True)

    list_sessions = subparsers.add_parser("list-replay-sessions", help="list replay sessions")
    list_sessions.add_argument("--offset", type=int, default=None)
    list_sessions.add_argument("--limit", type=int, default=None)

    inspect_session = subparsers.add_parser("inspect-replay-session", help="show one replay session's derived projection")
    inspect_session.add_argument("replay_session_id", help="exact replay_session_id")

    replay_next = subparsers.add_parser("replay-next", help="advance one replay session by exactly one step")
    replay_next.add_argument("replay_session_id", help="exact replay_session_id")

    inspect_snapshot = subparsers.add_parser("inspect-replay-snapshot", help="show the latest replay snapshot for one session")
    inspect_snapshot.add_argument("replay_session_id", help="exact replay_session_id")

    cancel_session = subparsers.add_parser("cancel-replay-session", help="cancel one READY or RUNNING replay session (idempotent)")
    cancel_session.add_argument("replay_session_id", help="exact replay_session_id")

    journal = subparsers.add_parser("market-data-journal", help="show the Market Data Fabric journal event tail")
    journal.add_argument("--tail", type=int, default=None, help="most recent N events (default 100, maximum 1000)")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    handlers = {
        "market-data-status": _cmd_status,
        "import-market-data": _cmd_import,
        "list-market-datasets": _cmd_list_datasets,
        "inspect-market-dataset": _cmd_inspect_dataset,
        "create-replay-session": _cmd_create_replay_session,
        "list-replay-sessions": _cmd_list_replay_sessions,
        "inspect-replay-session": _cmd_inspect_replay_session,
        "replay-next": _cmd_replay_next,
        "inspect-replay-snapshot": _cmd_inspect_replay_snapshot,
        "cancel-replay-session": _cmd_cancel_replay_session,
        "market-data-journal": _cmd_journal,
    }
    try:
        return handlers[args.command](args)
    except (svc.MarketDataServiceError, mdd.MarketDataValidationError) as error:
        print(json.dumps({"outcome": "REJECTED", "reason_code": error.reason_code}, sort_keys=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())
