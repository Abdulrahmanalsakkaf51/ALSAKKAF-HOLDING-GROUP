"""Tests for mt5_execution_cli.py — the local-only operator CLI."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from trading_lab_app import mt5_execution_cli as cli


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

    def test_mt5_symbol_status_requires_symbol_argument(self):
        parser = cli.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["mt5-symbol-status"])

    def test_send_demo_order_confirm_is_optional(self):
        parser = cli.build_parser()
        args = parser.parse_args(["send-demo-order", "exi_x"])
        self.assertIsNone(args.confirm)
        args = parser.parse_args(["send-demo-order", "exi_x", "--confirm", "abc"])
        self.assertEqual(args.confirm, "abc")

    def test_all_documented_commands_are_registered(self):
        parser = cli.build_parser()
        handlers = {
            "mt5-status", "mt5-dependency-status", "mt5-terminal-status", "mt5-account-status",
            "mt5-symbol-status", "execution-capabilities", "execution-journal", "inspect-proposal",
            "build-order-intent", "check-order", "send-demo-order", "inspect-execution",
        }
        for command in handlers:
            with self.subTest(command=command):
                # Parses without raising for a representative argv shape.
                if command in ("mt5-symbol-status",):
                    parser.parse_args([command, "XAUUSD"])
                elif command in ("inspect-proposal", "build-order-intent"):
                    parser.parse_args([command, "{}"])
                elif command in ("check-order", "send-demo-order", "inspect-execution"):
                    parser.parse_args([command, "exi_x"])
                else:
                    parser.parse_args([command])


class ModeGatedCliTests(_IsolatedLocalAppData):
    def test_mt5_status_fails_closed_at_off(self):
        exit_code = cli.main(["mt5-status"])
        self.assertEqual(exit_code, 0)  # status commands always succeed; they report disabled

    def test_build_order_intent_fails_closed_at_off(self):
        proposal_path = Path(self._tmpdir.name) / "proposal.json"
        proposal_path.write_text(json.dumps({"side": "BUY"}), encoding="utf-8")
        exit_code = cli.main(["build-order-intent", str(proposal_path)])
        self.assertEqual(exit_code, 1)

    def test_check_order_fails_closed_at_off(self):
        exit_code = cli.main(["check-order", "exi_" + "0" * 32])
        self.assertEqual(exit_code, 1)

    def test_send_demo_order_fails_closed_at_off(self):
        exit_code = cli.main(["send-demo-order", "exi_" + "0" * 32])
        self.assertEqual(exit_code, 1)


class ProposalInputTests(_IsolatedLocalAppData):
    def test_missing_file_reports_error(self):
        exit_code = cli.main(["inspect-proposal", "/no/such/file.json"])
        self.assertEqual(exit_code, 2)

    def test_invalid_json_reports_error(self):
        bad_path = Path(self._tmpdir.name) / "bad.json"
        bad_path.write_text("{not valid json", encoding="utf-8")
        exit_code = cli.main(["inspect-proposal", str(bad_path)])
        self.assertEqual(exit_code, 2)

    def test_inline_json_is_accepted(self):
        exit_code = cli.main(["inspect-proposal", "{}"])
        self.assertEqual(exit_code, 0)  # inspect-proposal reports a document, never raises for OFF mode


class OutputSafetyTests(_IsolatedLocalAppData):
    def test_no_password_ever_printed(self):
        with mock.patch("builtins.print") as mocked_print:
            cli.main(["mt5-status"])
        for call in mocked_print.call_args_list:
            for arg in call.args:
                self.assertNotIn("password", str(arg).lower())

    def test_exit_codes_are_stable_nonzero_on_rejection(self):
        exit_code = cli.main(["check-order", "exi_" + "0" * 32])
        self.assertNotEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
