"""Tests for alsakkaf_scalping_cli.py (TRL-R2-012 contract Section 18.1)."""

import json
import os
import tempfile
import unittest
from unittest import mock

from trading_lab_app import alsakkaf_scalping_cli as cli


class _IsolatedLocalAppData(unittest.TestCase):
    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self._patcher = mock.patch.dict(os.environ, {"LOCALAPPDATA": self._tmpdir.name}, clear=False)
        self._patcher.start()
        self.addCleanup(self._patcher.stop)


class ArgumentParsingTests(unittest.TestCase):
    def test_build_parser_requires_a_command(self):
        parser = cli.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args([])

    def test_all_eighteen_commands_registered(self):
        parser = cli.build_parser()
        commands = {
            "scalping-status", "scalping-preflight", "scalping-discover-symbols",
            "scalping-save-symbol-map", "scalping-configure-profile", "scalping-analyze",
            "scalping-start-demo-auto", "scalping-pause", "scalping-resume",
            "scalping-emergency-stop", "scalping-reset-emergency-stop", "scalping-run-cycle",
            "scalping-list-cycles", "scalping-inspect-cycle", "scalping-list-owned-orders",
            "scalping-list-owned-positions", "scalping-reconcile", "scalping-journal",
        }
        self.assertEqual(len(commands), 18)
        for command in commands:
            with self.subTest(command=command):
                if command == "scalping-preflight":
                    parser.parse_args([command, "XAUUSD"])
                elif command == "scalping-discover-symbols":
                    parser.parse_args([command, "XAUUSD"])
                elif command == "scalping-save-symbol-map":
                    parser.parse_args([command, "XAUUSD", "XAUUSDm"])
                elif command == "scalping-configure-profile":
                    parser.parse_args([command, "XAUUSD", "ALSAKKAF_PRECISION_SCALPING"])
                elif command == "scalping-inspect-cycle":
                    parser.parse_args([command, "cyc_x"])
                else:
                    parser.parse_args([command])


class StatusCommandTests(_IsolatedLocalAppData):
    def test_status_always_succeeds(self):
        exit_code = cli.main(["scalping-status"])
        self.assertEqual(exit_code, 0)

    def test_list_cycles_starts_empty(self):
        exit_code = cli.main(["scalping-list-cycles"])
        self.assertEqual(exit_code, 0)

    def test_list_owned_orders_starts_empty(self):
        exit_code = cli.main(["scalping-list-owned-orders"])
        self.assertEqual(exit_code, 0)

    def test_journal_command_succeeds(self):
        exit_code = cli.main(["scalping-journal", "--limit", "10"])
        self.assertEqual(exit_code, 0)


class GatedMutationCliTests(_IsolatedLocalAppData):
    def test_start_demo_auto_fails_closed_at_off(self):
        exit_code = cli.main(["scalping-start-demo-auto"])
        self.assertEqual(exit_code, 1)

    def test_inspect_cycle_not_found(self):
        exit_code = cli.main(["scalping-inspect-cycle", "cyc_" + "0" * 32])
        self.assertEqual(exit_code, 1)

    def test_reset_emergency_stop_fails_when_not_stopped(self):
        exit_code = cli.main(["scalping-reset-emergency-stop"])
        self.assertEqual(exit_code, 1)

    def test_preflight_fails_closed_without_dependency(self):
        exit_code = cli.main(["scalping-preflight", "XAUUSD"])
        self.assertEqual(exit_code, 1)

    def test_save_symbol_map_succeeds_at_off(self):
        exit_code = cli.main(["scalping-save-symbol-map", "XAUUSD", "XAUUSDm"])
        self.assertEqual(exit_code, 0)

    def test_configure_profile_succeeds(self):
        exit_code = cli.main(["scalping-configure-profile", "XAUUSD", "ALSAKKAF_BREAKOUT_LADDER"])
        self.assertEqual(exit_code, 0)

    def test_analyze_and_run_cycle_report_bar_input_required(self):
        self.assertEqual(cli.main(["scalping-analyze"]), 1)
        self.assertEqual(cli.main(["scalping-run-cycle"]), 1)


if __name__ == "__main__":
    unittest.main()
