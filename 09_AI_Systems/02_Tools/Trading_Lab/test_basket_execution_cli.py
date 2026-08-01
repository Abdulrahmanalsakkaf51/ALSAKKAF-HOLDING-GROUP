"""Tests for basket_execution_cli.py — the TRL-R2-009 Phase 6 local-only
operator CLI. Mirrors test_mt5_execution_cli.py's isolated-storage style;
every test runs against an isolated LOCALAPPDATA and starts at OFF."""

import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from trading_lab_app import basket_execution_cli as cli


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

    def test_send_basket_next_takes_only_basket_id(self):
        parser = cli.build_parser()
        args = parser.parse_args(["send-basket-next", "bsk_" + "0" * 32])
        self.assertEqual(args.basket_id, "bsk_" + "0" * 32)
        with self.assertRaises(SystemExit):
            # No child-identifying argument is accepted.
            parser.parse_args(["send-basket-next", "bsk_" + "0" * 32, "bc_" + "0" * 16])

    def test_confirm_basket_requires_both_arguments(self):
        parser = cli.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["confirm-basket", "bsk_" + "0" * 32])

    def test_all_documented_commands_are_registered(self):
        parser = cli.build_parser()
        shapes = {
            "basket-status": [],
            "inspect-basket": ["bsk_x"],
            "build-basket": ["oid_x"],
            "check-basket": ["bsk_x"],
            "request-basket-confirmation": ["bsk_x"],
            "confirm-basket": ["bsk_x", "CONFIRM-BASKET " + "a" * 16],
            "send-basket-next": ["bsk_x"],
            "inspect-basket-child": ["bsk_x", "bc_x"],
            "basket-journal": [],
        }
        for command, extra in shapes.items():
            with self.subTest(command=command):
                parser.parse_args([command] + extra)


class ModeGatedCliTests(_IsolatedLocalAppData):
    def test_basket_status_always_succeeds_and_reports_disabled_at_off(self):
        exit_code = cli.main(["basket-status"])
        self.assertEqual(exit_code, 0)

    def test_build_basket_fails_closed_at_off(self):
        exit_code = cli.main(["build-basket", "oid_" + "0" * 16])
        self.assertEqual(exit_code, 1)

    def test_check_basket_fails_closed_at_off(self):
        exit_code = cli.main(["check-basket", "bsk_" + "0" * 32])
        self.assertEqual(exit_code, 1)

    def test_request_basket_confirmation_fails_closed_at_off(self):
        exit_code = cli.main(["request-basket-confirmation", "bsk_" + "0" * 32])
        self.assertEqual(exit_code, 1)

    def test_confirm_basket_fails_closed_at_off(self):
        exit_code = cli.main(["confirm-basket", "bsk_" + "0" * 32, "CONFIRM-BASKET " + "a" * 16])
        self.assertEqual(exit_code, 1)

    def test_send_basket_next_fails_closed_at_off(self):
        exit_code = cli.main(["send-basket-next", "bsk_" + "0" * 32])
        self.assertEqual(exit_code, 1)

    def test_inspect_basket_not_found_at_off(self):
        exit_code = cli.main(["inspect-basket", "bsk_" + "0" * 32])
        self.assertEqual(exit_code, 1)

    def test_basket_journal_always_succeeds_at_off(self):
        exit_code = cli.main(["basket-journal"])
        self.assertEqual(exit_code, 0)


class OutputSafetyTests(_IsolatedLocalAppData):
    def test_no_password_or_credential_ever_printed(self):
        with mock.patch("builtins.print") as mocked_print:
            cli.main(["basket-status"])
        for call in mocked_print.call_args_list:
            for arg in call.args:
                lowered = str(arg).lower()
                self.assertNotIn("password", lowered)
                self.assertNotIn("credential", lowered)

    def test_exit_codes_are_stable_nonzero_on_rejection(self):
        exit_code = cli.main(["check-basket", "bsk_" + "0" * 32])
        self.assertNotEqual(exit_code, 0)

    def test_live_and_manual_confirmation_banners_present_on_mutating_commands(self):
        with mock.patch("builtins.print") as mocked_print:
            cli.main(["build-basket", "oid_" + "0" * 16])
        combined = "\n".join(str(call.args[0]) for call in mocked_print.call_args_list if call.args)
        self.assertIn("LIVE EXECUTION DISABLED", combined)
        self.assertIn("MANUAL CONFIRMATION REQUIRED", combined)

    def test_confirm_basket_malformed_entry_text_fails_closed_not_crashes_at_off(self):
        # At OFF, capability denial is checked before entry-text parsing,
        # so a malformed "yes" still produces a stable, governed rejection
        # (never an uncaught traceback) rather than reaching the parser at
        # all. See test_basket_execution_service.ConfirmationCycleTests
        # .test_invalid_format_rejected for the equivalent check against a
        # real, capability-granted service, where the malformed text does
        # reach basket_execution_data.parse_confirmation_entry and must
        # still surface as a governed BasketExecutionServiceError rather
        # than an uncaught BasketValidationError.
        with mock.patch("builtins.print") as mocked_print:
            exit_code = cli.main(["confirm-basket", "bsk_" + "0" * 32, "yes"])
        self.assertEqual(exit_code, 1)
        last_call = mocked_print.call_args_list[-1]
        document = json.loads(last_call.args[0])
        self.assertEqual(document["outcome"], "REJECTED")
        self.assertEqual(document["reason_code"], "BASKET_CAPABILITY_DENIED")

    def test_confirm_basket_error_output_is_json_reason_code_only(self):
        with mock.patch("builtins.print") as mocked_print:
            cli.main(["confirm-basket", "bsk_" + "0" * 32, "CONFIRM-BASKET " + "a" * 16])
        last_call = mocked_print.call_args_list[-1]
        document = json.loads(last_call.args[0])
        self.assertEqual(document["outcome"], "REJECTED")
        self.assertIn("reason_code", document)


if __name__ == "__main__":
    unittest.main(verbosity=2)
