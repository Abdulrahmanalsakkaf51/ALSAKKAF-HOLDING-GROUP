"""Tests for market_intelligence_cli.py — the TRL-R2-010 local-only
operator CLI. Mirrors test_basket_execution_cli.py's isolated-storage
style; every test runs against an isolated LOCALAPPDATA and starts at OFF.
"""

import io
import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest import mock

from trading_lab_app import market_intelligence_cli as cli

import mi_test_support as support


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

    def test_all_nine_documented_commands_are_registered(self):
        parser = cli.build_parser()
        shapes = {
            "market-intelligence-status": [],
            "analyze-market-snapshot": ["path.json"],
            "list-opportunities": [],
            "inspect-opportunity": ["opp_x"],
            "list-virtual-opportunities": ["opp_x"],
            "inspect-virtual-opportunity": ["vop_x"],
            "preview-opportunity-basket": ["opp_x"],
            "record-opportunity-outcome": ["opp_x", "outcome.json"],
            "market-intelligence-journal": [],
        }
        self.assertEqual(len(shapes), 9)
        for command, arguments in shapes.items():
            args = parser.parse_args([command] + arguments)
            self.assertEqual(args.command, command)

    def test_record_opportunity_outcome_requires_both_arguments(self):
        parser = cli.build_parser()
        with self.assertRaises(SystemExit):
            parser.parse_args(["record-opportunity-outcome", "opp_x"])


class OffModeFailClosedTests(_IsolatedLocalAppData):
    def test_status_always_succeeds_and_reports_disabled_at_off(self):
        exit_code = cli.main(["market-intelligence-status"])
        self.assertEqual(exit_code, 0)

    def test_analyze_market_snapshot_fails_closed_at_off(self):
        exit_code = cli.main(["analyze-market-snapshot", "fixtures/trl_cortex_v0_synthetic_trade_candidate.json"])
        self.assertEqual(exit_code, 1)

    def test_preview_opportunity_basket_fails_closed_at_off(self):
        exit_code = cli.main(["preview-opportunity-basket", "opp_" + "0" * 32])
        self.assertEqual(exit_code, 1)

    def test_record_opportunity_outcome_fails_closed_at_off(self):
        path = support.write_temp_json({})
        try:
            exit_code = cli.main(["record-opportunity-outcome", "opp_" + "0" * 32, path])
        finally:
            os.unlink(path)
        self.assertEqual(exit_code, 1)

    def test_list_opportunities_always_succeeds_at_off(self):
        self.assertEqual(cli.main(["list-opportunities"]), 0)

    def test_inspect_opportunity_not_found_at_off(self):
        self.assertEqual(cli.main(["inspect-opportunity", "opp_" + "0" * 32]), 1)

    def test_journal_always_succeeds_at_off(self):
        self.assertEqual(cli.main(["market-intelligence-journal"]), 0)

    def test_exit_codes_stable_nonzero_on_rejection(self):
        exit_code = cli.main(["preview-opportunity-basket", "opp_" + "0" * 32])
        self.assertNotEqual(exit_code, 0)

    def test_research_only_banners_present_on_mutating_commands(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            cli.main(["analyze-market-snapshot", "fixtures/trl_cortex_v0_synthetic_trade_candidate.json"])
        output = buffer.getvalue()
        self.assertIn("RESEARCH ONLY", output)
        self.assertIn("EXECUTION_HANDOFF_NOT_APPROVED", output)

    def test_rejection_output_is_json_reason_code_only_no_traceback(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = cli.main(["preview-opportunity-basket", "opp_" + "0" * 32])
        self.assertEqual(exit_code, 1)
        lines = [line for line in buffer.getvalue().splitlines() if line.strip().startswith("{")]
        self.assertTrue(lines)
        payload = json.loads(lines[-1])
        self.assertEqual(payload["outcome"], "REJECTED")
        self.assertIn("reason_code", payload)
        self.assertNotIn("Traceback", buffer.getvalue())


class SafeIdentifierTests(_IsolatedLocalAppData):
    def test_malformed_opportunity_id_rejected_before_lookup(self):
        exit_code = cli.main(["inspect-opportunity", "not-a-valid-id; rm -rf"])
        self.assertEqual(exit_code, 1)

    def test_malformed_virtual_opportunity_id_rejected_before_lookup(self):
        exit_code = cli.main(["inspect-virtual-opportunity", "../../etc/passwd"])
        self.assertEqual(exit_code, 1)


class GrantedModeTests(_IsolatedLocalAppData):
    def _grant_research_mode(self):
        from trading_lab_app import mode_service
        from trading_lab_app.app import _subsystem_builder_for_mode
        service = mode_service.ModeService(subsystem_builder=_subsystem_builder_for_mode)
        result = service.request_transition("RESEARCH", actor="test")
        self.assertEqual(result.outcome, "ACCEPTED")
        service.shutdown()

    def test_analyze_and_inspect_round_trip_when_granted(self):
        self._grant_research_mode()
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = cli.main(["analyze-market-snapshot", "fixtures/trl_cortex_v0_synthetic_trade_candidate.json"])
        self.assertEqual(exit_code, 0)
        match = re.search(r'"opportunity_id":\s*"(opp_[0-9a-f]{32})"', buffer.getvalue())
        self.assertIsNotNone(match)
        opportunity_id = match.group(1)
        exit_code = cli.main(["inspect-opportunity", opportunity_id])
        self.assertEqual(exit_code, 0)

    def test_preview_generated_when_granted(self):
        self._grant_research_mode()
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            cli.main(["analyze-market-snapshot", "fixtures/trl_cortex_v0_synthetic_trade_candidate.json"])
        match = re.search(r'"opportunity_id":\s*"(opp_[0-9a-f]{32})"', buffer.getvalue())
        opportunity_id = match.group(1)
        preview_buffer = io.StringIO()
        with redirect_stdout(preview_buffer):
            exit_code = cli.main(["preview-opportunity-basket", opportunity_id])
        self.assertEqual(exit_code, 0)
        self.assertIn("EXECUTION_HANDOFF_NOT_APPROVED", preview_buffer.getvalue())


if __name__ == "__main__":
    unittest.main()
