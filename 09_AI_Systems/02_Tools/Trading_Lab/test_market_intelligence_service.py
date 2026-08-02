"""Tests for market_intelligence_service.py — TRL-R2-010 orchestration:
capability gating, input-file safety, and the full snapshot -> evidence ->
opportunity -> decision -> lattice -> preview -> telemetry pipeline.
"""

import os
import tempfile
import unittest

from trading_lab_app import market_intelligence_service as svc
from trading_lab_app import market_intelligence_data as mid
from trading_lab_app.mode_service import in_memory_mode_service
from trading_lab_app.market_intelligence_journal import in_memory_mi_journal_writer

import mi_test_support as support


def _service_in_mode(mode_name):
    mode = in_memory_mode_service()
    if mode_name != "OFF":
        result = mode.request_transition(mode_name, actor="test")
        assert result.outcome == "ACCEPTED", result
    journal = in_memory_mi_journal_writer()
    service = svc.MarketIntelligenceService(mode_service=mode, journal=journal)
    return mode, service


def _analyze(service, envelope):
    path = support.write_temp_json(envelope)
    try:
        return service.analyze_market_snapshot(path)
    finally:
        os.unlink(path)


class CapabilityGatingTests(unittest.TestCase):
    def test_off_mode_denies_mutation(self):
        _mode, service = _service_in_mode("OFF")
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            _analyze(service, support.analysis_envelope())
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_CAPABILITY_DENIED")

    def test_off_mode_allows_read_only_status(self):
        _mode, service = _service_in_mode("OFF")
        status = service.status_document()
        self.assertFalse(status["market_intelligence_research_granted"])
        # read-only list/inspect/journal never raise, regardless of mode
        service.list_opportunities_document()
        service.journal_document()

    def test_granted_in_research_synthetic_paper_and_mt5_demo_manual(self):
        for mode_name in ("RESEARCH", "SYNTHETIC_PAPER", "MT5_DEMO_MANUAL"):
            _mode, service = _service_in_mode(mode_name)
            result = _analyze(service, support.analysis_envelope())
            self.assertIn(result["decision"]["final_status"], mid.DECISION_STATUSES)

    def test_denied_when_mode_transitions_back_to_off(self):
        mode, service = _service_in_mode("RESEARCH")
        mode.request_transition("OFF", actor="test")
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            _analyze(service, support.analysis_envelope())
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_CAPABILITY_DENIED")


class InputFileSafetyTests(unittest.TestCase):
    def test_file_too_large_rejected(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as handle:
            handle.write(b"{" + b"\"a\":1," * 60000 + b"\"z\":1}")  # well over the 262144-byte bound
            path = handle.name
        try:
            with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
                svc.load_analysis_input_bytes(path)
            self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INPUT_FILE_TOO_LARGE")
        finally:
            os.unlink(path)

    def test_directory_path_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
                svc.load_analysis_input_bytes(directory)
            self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INPUT_PATH_INVALID")

    def test_url_rejected(self):
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            svc.load_analysis_input_bytes("https://example.com/input.json")
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INPUT_PATH_INVALID")

    def test_unc_path_rejected(self):
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            svc.load_analysis_input_bytes(r"\\server\share\input.json")
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INPUT_PATH_INVALID")

    def test_nonexistent_path_rejected(self):
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            svc.load_analysis_input_bytes(os.path.join(tempfile.gettempdir(), "does-not-exist-mi.json"))
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INPUT_PATH_INVALID")

    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            svc.parse_analysis_input_bytes(b'{"a": 1, "a": 2}')
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INPUT_DUPLICATE_KEY")

    def test_non_utf8_bytes_rejected(self):
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            svc.parse_analysis_input_bytes(b"\xff\xfe\x00\x01")
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INPUT_NOT_UTF8_JSON")

    def test_nan_and_infinity_rejected(self):
        for token in (b'{"x": NaN}', b'{"x": Infinity}', b'{"x": -Infinity}'):
            with self.assertRaises(svc.MarketIntelligenceServiceError):
                svc.parse_analysis_input_bytes(token)

    def test_source_label_never_contains_absolute_path(self):
        label = svc.bounded_source_label("C:\\Users\\someone\\secret\\input.json")
        self.assertNotIn("Users", label)
        self.assertNotIn("secret", label)
        self.assertTrue(label.startswith("local-file:"))


class FullPipelineTests(unittest.TestCase):
    def test_trade_candidate_fixture_produces_trade_candidate_and_conserving_preview(self):
        _mode, service = _service_in_mode("RESEARCH")
        result = _analyze(service, support.analysis_envelope())
        self.assertEqual(result["decision"]["final_status"], "TRADE_CANDIDATE")
        preview = service.preview_opportunity_basket(result["opportunity"]["opportunity_id"])
        self.assertEqual(preview["execution_handoff_status"], "EXECUTION_HANDOFF_NOT_APPROVED")
        self.assertTrue(preview["non_executable"])

    def test_wait_reachable_via_dedicated_fixture(self):
        _mode, service = _service_in_mode("RESEARCH")
        envelope = support.analysis_envelope(activation_satisfied=False)
        result = _analyze(service, envelope)
        self.assertEqual(result["decision"]["final_status"], "WAIT")
        self.assertEqual(result["decision"]["reason_codes"][0], "MARKET_INTELLIGENCE_TRIGGER_NOT_ACTIVE")

    def test_reject_reachable_via_dedicated_fixture(self):
        _mode, service = _service_in_mode("RESEARCH")
        weak = [support.evidence_input(item["category"], "OPPOSES", "0.9000", "0.9500") if item["category"] in mid.DIRECTIONAL_EVIDENCE_CATEGORIES else item for item in support.strong_evidence_inputs()]
        envelope = support.analysis_envelope(evidence_inputs=weak)
        result = _analyze(service, envelope)
        self.assertEqual(result["decision"]["final_status"], "REJECT")

    def test_blocked_reachable_via_dedicated_fixture(self):
        _mode, service = _service_in_mode("RESEARCH")
        raw = support.strong_evidence_inputs()
        by_cat = {item["category"]: item for item in raw}
        by_cat["DATA_QUALITY"] = support.evidence_input("DATA_QUALITY", "NEUTRAL", "0.1000", "0.9500")
        envelope = support.analysis_envelope(evidence_inputs=list(by_cat.values()))
        result = _analyze(service, envelope)
        self.assertEqual(result["decision"]["final_status"], "BLOCKED")
        self.assertEqual(result["decision"]["reason_codes"][0], "MARKET_INTELLIGENCE_DATA_QUALITY_BELOW_MINIMUM")

    def test_expired_reachable_via_dedicated_fixture(self):
        import datetime
        _mode, service = _service_in_mode("RESEARCH")
        result = _analyze(service, support.analysis_envelope())
        self.assertEqual(result["decision"]["final_status"], "TRADE_CANDIDATE")
        # Advance the clock forward past the opportunity's 24h default
        # lifetime (never backward — the fixture's fixed observed_at_utc
        # must always remain in the past relative to "now").
        real_clock = service._clock
        advanced = real_clock() + datetime.timedelta(hours=25)
        service._clock = lambda: advanced
        second = _analyze(service, support.analysis_envelope())
        self.assertEqual(second["opportunity"]["opportunity_id"], result["opportunity"]["opportunity_id"])
        self.assertEqual(second["decision"]["final_status"], "EXPIRED")

    def test_sma001_blocked(self):
        _mode, service = _service_in_mode("RESEARCH")
        envelope = support.analysis_envelope(strategy_id="SMA-001")
        result = _analyze(service, envelope)
        self.assertEqual(result["decision"]["final_status"], "BLOCKED")
        self.assertEqual(result["decision"]["reason_codes"][0], "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED")

    def test_fib001_blocked(self):
        _mode, service = _service_in_mode("RESEARCH")
        envelope = support.analysis_envelope(strategy_id="FIB-001")
        result = _analyze(service, envelope)
        self.assertEqual(result["decision"]["final_status"], "BLOCKED")
        self.assertEqual(result["decision"]["reason_codes"][0], "STRATEGY_PARAMETERS_NOT_APPROVED")

    def test_generic_cortex_not_blocked_by_sma_fib_registry(self):
        _mode, service = _service_in_mode("RESEARCH")
        result = _analyze(service, support.analysis_envelope())
        self.assertNotIn("STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED", result["decision"]["reason_codes"])
        self.assertNotIn("STRATEGY_PARAMETERS_NOT_APPROVED", result["decision"]["reason_codes"])

    def test_unsupported_instrument_fails_closed_no_opportunity_created(self):
        _mode, service = _service_in_mode("RESEARCH")
        envelope = support.analysis_envelope(snapshot=support.snapshot_input(instrument="GOLD"))
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            _analyze(service, envelope)
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_INSTRUMENT_NOT_ALLOWED")
        self.assertEqual(service.list_opportunities_document()["opportunities"], [])

    def test_opportunity_reuse_across_identical_analysis(self):
        _mode, service = _service_in_mode("RESEARCH")
        first = _analyze(service, support.analysis_envelope())
        second = _analyze(service, support.analysis_envelope())
        self.assertEqual(first["opportunity"]["opportunity_id"], second["opportunity"]["opportunity_id"])
        reused_events = [event for event in service.journal_document()["events"] if event["event_type"] == "MI_OPPORTUNITY_REUSED"]
        self.assertEqual(len(reused_events), 1)

    def test_preview_denied_for_wait_status(self):
        _mode, service = _service_in_mode("RESEARCH")
        result = _analyze(service, support.analysis_envelope(activation_satisfied=False))
        with self.assertRaises(svc.MarketIntelligenceServiceError) as ctx:
            service.preview_opportunity_basket(result["opportunity"]["opportunity_id"])
        self.assertEqual(ctx.exception.reason_code, "MARKET_INTELLIGENCE_PREVIEW_NOT_AVAILABLE_FOR_STATUS")

    def test_at_most_one_preview_selected_idempotent_reuse(self):
        _mode, service = _service_in_mode("RESEARCH")
        result = _analyze(service, support.analysis_envelope())
        opportunity_id = result["opportunity"]["opportunity_id"]
        first = service.preview_opportunity_basket(opportunity_id)
        second = service.preview_opportunity_basket(opportunity_id)
        self.assertEqual(first["preview_id"], second["preview_id"])
        created_events = [event for event in service.journal_document()["events"] if event["event_type"] == "MI_BASKET_PREVIEW_CREATED"]
        self.assertEqual(len(created_events), 1)

    def test_no_metatrader5_import_anywhere_in_module_tree(self):
        import re
        import trading_lab_app.market_intelligence_data as data_module
        import trading_lab_app.market_intelligence_journal as journal_module
        import trading_lab_app.market_intelligence_cli as cli_module
        # Checks actual import/construct/call statements, not prose —
        # every module's own docstring legitimately *mentions*
        # MetaTrader5/order_check/order_send/RealMT5ExecutionAdapter to
        # document that it never does any of them (Section 22).
        import_pattern = re.compile(r"^\s*(import|from)\s+MetaTrader5\b", re.MULTILINE)
        construct_pattern = re.compile(r"RealMT5ExecutionAdapter\s*\(")
        call_pattern = re.compile(r"\.\s*order_(check|send)\s*\(")
        for module in (svc, data_module, journal_module, cli_module):
            source_path = module.__file__
            with open(source_path, "r", encoding="utf-8") as handle:
                source = handle.read()
            self.assertIsNone(import_pattern.search(source), source_path)
            self.assertIsNone(construct_pattern.search(source), source_path)
            self.assertIsNone(call_pattern.search(source), source_path)

    def test_telemetry_recording_and_immutability(self):
        _mode, service = _service_in_mode("RESEARCH")
        result = _analyze(service, support.analysis_envelope())
        opportunity_id = result["opportunity"]["opportunity_id"]
        service.preview_opportunity_basket(opportunity_id)
        outcome = {
            "observation_window_start_utc": "2026-08-01T12:00:00.000000Z",
            "observation_window_end_utc": "2026-08-01T18:00:00.000000Z",
            "predicted_entry": "1.00", "predicted_stop": "1.00", "predicted_targets": ["1.00", "1.00"],
            "realized_movement": "5.0000", "maximum_favorable_excursion": "6.0000",
            "maximum_adverse_excursion": "1.0000", "theoretical_result_after_costs": "4.5000",
            "calibration_bucket": "HIGH_CONFIDENCE", "outcome_classification": "TRUE_POSITIVE",
            "missing_data_status": "COMPLETE",
        }
        telemetry = service.record_opportunity_outcome(opportunity_id, outcome)
        self.assertEqual(telemetry["original_decision_status"], "TRADE_CANDIDATE")
        before = service.inspect_opportunity_document(opportunity_id)["opportunity"]
        service.record_opportunity_outcome(opportunity_id, outcome)
        after = service.inspect_opportunity_document(opportunity_id)["opportunity"]
        self.assertEqual(before["canonical_opportunity_hash"], after["canonical_opportunity_hash"])

    def test_restart_persistence_via_shared_store(self):
        from trading_lab_app.market_intelligence_journal import InMemoryMarketIntelligenceJournalStore, MarketIntelligenceJournalWriter
        mode = in_memory_mode_service()
        mode.request_transition("RESEARCH", actor="test")
        store = InMemoryMarketIntelligenceJournalStore()
        journal1 = MarketIntelligenceJournalWriter(store=store)
        service1 = svc.MarketIntelligenceService(mode_service=mode, journal=journal1)
        result = _analyze(service1, support.analysis_envelope())
        journal2 = MarketIntelligenceJournalWriter(store=store)
        service2 = svc.MarketIntelligenceService(mode_service=mode, journal=journal2)
        found = service2.inspect_opportunity_document(result["opportunity"]["opportunity_id"])
        self.assertTrue(found["found"])


class DisabledServiceTests(unittest.TestCase):
    def test_disabled_service_denies_every_mutation(self):
        service = svc.disabled_service("OFF")
        with self.assertRaises(svc.MarketIntelligenceServiceError):
            service.analyze_market_snapshot("does-not-matter.json")
        with self.assertRaises(svc.MarketIntelligenceServiceError):
            service.preview_opportunity_basket("opp_" + "a" * 32)
        with self.assertRaises(svc.MarketIntelligenceServiceError):
            service.record_opportunity_outcome("opp_" + "a" * 32, {})

    def test_disabled_service_read_only_still_works(self):
        service = svc.disabled_service("OFF")
        self.assertFalse(service.status_document()["enabled"])
        self.assertEqual(service.list_opportunities_document()["opportunities"], [])
        self.assertEqual(service.journal_document()["events"], [])


if __name__ == "__main__":
    unittest.main()
