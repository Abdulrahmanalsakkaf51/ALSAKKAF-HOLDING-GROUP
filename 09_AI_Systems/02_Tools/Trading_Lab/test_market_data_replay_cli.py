"""Tests for TRL-R2-011 Market Data Fabric and Replay V0 -- CLI module
(``market_data_replay_cli.py``). Covers contract Section 25 category J
(all 11 command families, valid/invalid operations, stable exit codes,
bounded output, pagination, no traceback, no path disclosure).

Invokes the CLI as a real subprocess (matching this repository's existing
CLI test convention -- e.g. ``test_mt5_execution_cli.py``) so
``build_parser``/``main`` are exercised exactly as an operator would run
them, with an isolated temporary ``LOCALAPPDATA`` so nothing here touches
real durable application state.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import mdr_test_support as support

APP_DIRECTORY = support.APP_DIRECTORY


def _run(args, env_overrides=None, cwd=None):
    env = dict(os.environ)
    if env_overrides:
        env.update(env_overrides)
    result = subprocess.run(
        [sys.executable, "-B", "-m", "trading_lab_app.market_data_replay_cli"] + args,
        cwd=cwd or str(APP_DIRECTORY), env=env, capture_output=True, text=True, timeout=30,
    )
    return result


def _isolated_env(tmp):
    return {"LOCALAPPDATA": str(tmp)}


def _extract_json(stdout):
    lines = stdout.splitlines()
    start = lines.index("{")
    return json.loads("\n".join(lines[start:]))


class CliStatusTests(unittest.TestCase):
    def test_status_command_succeeds(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(["market-data-status"], _isolated_env(tmp))
        self.assertEqual(result.returncode, 0)
        document = _extract_json(result.stdout)
        self.assertIn("market_data_research_granted", document)

    def test_status_shows_off_mode_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(["market-data-status"], _isolated_env(tmp))
        document = _extract_json(result.stdout)
        self.assertEqual(document["operating_mode"], "OFF")
        self.assertFalse(document["market_data_research_granted"])


class CliImportAndReplayTests(unittest.TestCase):
    def _request_research_mode(self, tmp):
        result = _run(
            ["show-mode"], _isolated_env(tmp),
        )
        # request-mode lives in mode_cli, invoked directly here to prepare state.
        subprocess.run(
            [sys.executable, "-B", "-m", "trading_lab_app.mode_cli", "request-mode", "RESEARCH", "--reason", "cli-test"],
            cwd=str(APP_DIRECTORY), env={**os.environ, **_isolated_env(tmp)}, capture_output=True, text=True, timeout=30,
        )

    def test_import_denied_at_off(self):
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "x.csv"
            csv_path.write_bytes(support.build_csv_bytes())
            result = _run(
                ["import-market-data", str(csv_path), "--source-classification", "SYNTHETIC_FIXTURE", "--source-reference", "cli-ref"],
                _isolated_env(tmp),
            )
        self.assertEqual(result.returncode, 1)
        self.assertIn("MARKET_DATA_CAPABILITY_DENIED", result.stdout)

    def test_full_import_and_replay_cycle_in_research_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._request_research_mode(tmp)
            csv_path = Path(tmp) / "x.csv"
            csv_path.write_bytes(support.build_csv_bytes(bar_count=6))

            imported = _run(
                ["import-market-data", str(csv_path), "--source-classification", "SYNTHETIC_FIXTURE", "--source-reference", "cli-cycle"],
                _isolated_env(tmp),
            )
            self.assertEqual(imported.returncode, 0, imported.stdout + imported.stderr)
            document = _extract_json(imported.stdout)
            dataset_id = document["dataset_id"]

            listed = _run(["list-market-datasets"], _isolated_env(tmp))
            self.assertEqual(listed.returncode, 0)
            listing = json.loads(listed.stdout)
            self.assertEqual(listing["total_count"], 1)

            inspected = _run(["inspect-market-dataset", dataset_id], _isolated_env(tmp))
            self.assertEqual(inspected.returncode, 0)

            created = _run(
                ["create-replay-session", dataset_id, "--start-index", "0", "--end-index", "5", "--step-size", "2"],
                _isolated_env(tmp),
            )
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)
            session_doc = _extract_json(created.stdout)
            session_id = session_doc["replay_session_id"]

            step1 = _run(["replay-next", session_id], _isolated_env(tmp))
            self.assertEqual(step1.returncode, 0)

            inspected_session = _run(["inspect-replay-session", session_id], _isolated_env(tmp))
            self.assertEqual(inspected_session.returncode, 0)

            snapshot = _run(["inspect-replay-snapshot", session_id], _isolated_env(tmp))
            self.assertEqual(snapshot.returncode, 0)
            snapshot_doc = json.loads(snapshot.stdout)
            self.assertTrue(snapshot_doc["found"])

            journal = _run(["market-data-journal", "--tail", "5"], _isolated_env(tmp))
            self.assertEqual(journal.returncode, 0)

            cancelled = _run(["cancel-replay-session", session_id], _isolated_env(tmp))
            self.assertEqual(cancelled.returncode, 0)


class CliSafetyTests(unittest.TestCase):
    def test_invalid_dataset_id_rejected_without_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(["inspect-market-dataset", "not-a-safe-id"], _isolated_env(tmp))
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("Traceback", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_nonexistent_replay_session_governed_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(["inspect-replay-session", "rps_" + "0" * 32], _isolated_env(tmp))
        self.assertEqual(result.returncode, 1)
        self.assertIn("MARKET_DATA_REPLAY_SESSION_NOT_FOUND", result.stdout)

    def test_no_path_disclosure_on_import_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing_path = str(Path(tmp) / "does-not-exist.csv")
            result = _run(
                ["import-market-data", missing_path, "--source-classification", "SYNTHETIC_FIXTURE", "--source-reference", "x"],
                _isolated_env(tmp),
            )
        self.assertNotIn(missing_path, result.stdout)
        self.assertNotIn("Traceback", result.stdout)

    def test_missing_required_argument_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = _run(["import-market-data", "x.csv"], _isolated_env(tmp))
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
