"""Tests for mt5_execution_adapter.py — the disabled/fake/real adapter tiers."""

from pathlib import Path
import unittest
from unittest import mock

from trading_lab_app import mt5_execution_adapter as maa


APP_DIRECTORY = Path(__file__).resolve().parent / "trading_lab_app"


class ImportBoundaryTests(unittest.TestCase):
    def test_no_top_level_metatrader5_import(self):
        source = (APP_DIRECTORY / "mt5_execution_adapter.py").read_text(encoding="utf-8")
        self.assertNotIn("import MetaTrader5", source)

    def test_real_adapter_construction_does_not_import(self):
        with mock.patch("importlib.import_module") as mocked_import:
            maa.RealMT5ExecutionAdapter()
            mocked_import.assert_not_called()

    def test_real_adapter_dependency_missing_fails_closed(self):
        adapter = maa.RealMT5ExecutionAdapter(provider=None)
        with mock.patch("importlib.import_module", side_effect=ImportError):
            status = adapter.dependency_status()
        self.assertFalse(status["available"])
        self.assertEqual(status["reason_code"], "MT5_DEPENDENCY_MISSING")

    def test_real_adapter_terminal_status_fails_closed_when_dependency_missing(self):
        adapter = maa.RealMT5ExecutionAdapter(provider=None)
        with mock.patch("importlib.import_module", side_effect=ImportError):
            status = adapter.terminal_status()
        self.assertFalse(status["connected"])
        self.assertEqual(status["reason_code"], "MT5_DEPENDENCY_MISSING")

    def test_real_adapter_never_holds_a_session_open(self):
        provider = mock.Mock()
        provider.initialize.return_value = True
        provider.terminal_info.return_value = {"path": "C:\\x", "build": 1, "trade_allowed": True, "connected": True}
        adapter = maa.RealMT5ExecutionAdapter(provider=provider)
        adapter.terminal_status()
        provider.shutdown.assert_called_once()

    def test_real_adapter_failed_initialize_fails_closed(self):
        provider = mock.Mock()
        provider.initialize.return_value = False
        adapter = maa.RealMT5ExecutionAdapter(provider=provider)
        status = adapter.terminal_status()
        self.assertFalse(status["connected"])
        self.assertEqual(status["reason_code"], "TERMINAL_UNAVAILABLE")
        provider.shutdown.assert_not_called()

    def test_real_adapter_only_allowlisted_operations_reachable(self):
        provider = mock.Mock(spec=list(maa.PROVIDER_METHOD_ALLOWLIST))
        with self.assertRaises(RuntimeError):
            maa.RealMT5ExecutionAdapter._call(provider, "not_allowlisted")


class DisabledAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = maa.DisabledExecutionAdapter()

    def test_dependency_status_denied(self):
        self.assertFalse(self.adapter.dependency_status()["available"])

    def test_terminal_status_denied(self):
        self.assertFalse(self.adapter.terminal_status()["connected"])

    def test_account_status_denied(self):
        self.assertFalse(self.adapter.account_status()["available"])

    def test_symbol_status_denied(self):
        self.assertFalse(self.adapter.symbol_status("XAUUSD")["available"])

    def test_order_check_denied(self):
        result = self.adapter.order_check({})
        self.assertEqual(result["outcome"], "FAILED")

    def test_order_send_denied(self):
        result = self.adapter.order_send({})
        self.assertEqual(result["outcome"], "REJECTED")


class FakeAdapterTests(unittest.TestCase):
    def setUp(self):
        self.adapter = maa.FakeExecutionAdapter()
        self.adapter.set_symbol("XAUUSD")

    def test_deterministic_defaults(self):
        first = self.adapter.terminal_status()
        second = self.adapter.terminal_status()
        self.assertEqual(first, second)

    def test_order_check_records_exactly_one_call(self):
        self.adapter.order_check({"symbol": "XAUUSD"})
        self.assertEqual(len(self.adapter.calls), 1)
        self.assertEqual(self.adapter.calls[0][0], "order_check")

    def test_scripted_check_result_is_returned(self):
        self.adapter.queue_check_result({"outcome": "FAILED", "retcode": 10006, "comment": "x", "checked_at_utc": "t"})
        result = self.adapter.order_check({})
        self.assertEqual(result["outcome"], "FAILED")

    def test_scripted_send_result_is_returned(self):
        self.adapter.queue_send_result({"outcome": "UNCERTAIN", "comment": "timeout"})
        result = self.adapter.order_send({"volume": "0.01"})
        self.assertEqual(result["outcome"], "UNCERTAIN")

    def test_default_send_echoes_requested_volume(self):
        result = self.adapter.order_send({"volume": "0.02"})
        self.assertEqual(result["volume_filled"], "0.02")

    def test_symbol_not_configured_is_unavailable(self):
        status = self.adapter.symbol_status("EURUSD")
        self.assertFalse(status["available"])


class ResponseNormalizationTests(unittest.TestCase):
    def test_check_response_missing_retcode_is_malformed(self):
        result = maa._normalize_check_response({}, "t")
        self.assertEqual(result["outcome"], "MALFORMED")

    def test_check_response_success_retcode(self):
        result = maa._normalize_check_response({"retcode": 0, "comment": "ok"}, "t")
        self.assertEqual(result["outcome"], "PASSED")

    def test_check_response_nonzero_retcode_is_failed(self):
        result = maa._normalize_check_response({"retcode": 10006}, "t")
        self.assertEqual(result["outcome"], "FAILED")

    def test_send_response_none_is_uncertain(self):
        result = maa._normalize_send_response(None, "t")
        self.assertEqual(result["outcome"], "UNCERTAIN")

    def test_send_response_non_done_retcode_is_rejected(self):
        result = maa._normalize_send_response({"retcode": 10004, "comment": "requote"}, "t")
        self.assertEqual(result["outcome"], "REJECTED")

    def test_send_response_success_requires_order_and_deal(self):
        # A DONE retcode with a missing order/deal ticket is never treated
        # as proof of success.
        result = maa._normalize_send_response({"retcode": 10009, "volume": 0.01}, "t")
        self.assertEqual(result["outcome"], "MALFORMED")

    def test_send_response_full_success(self):
        result = maa._normalize_send_response(
            {"retcode": 10009, "order": 111, "deal": 222, "volume": 0.01, "comment": "ok"}, "t",
        )
        self.assertEqual(result["outcome"], "FILLED")
        self.assertEqual(result["ticket"], 111)

    def test_send_response_truthy_object_is_not_treated_as_success(self):
        # An order object being non-null must never itself be proof of
        # success — only a DONE-family retcode with complete fields is.
        class Truthy:
            retcode = 10004
            comment = "rejected"
            order = None
            deal = None
            volume = None
        result = maa._normalize_send_response(Truthy(), "t")
        self.assertEqual(result["outcome"], "REJECTED")


if __name__ == "__main__":
    unittest.main()
