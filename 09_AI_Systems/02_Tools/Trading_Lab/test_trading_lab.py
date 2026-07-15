# -*- coding: utf-8 -*-
"""Tests for the Trading Research Lab paper-only backtest engine (PRJ-017).
Verifies every TRL-001 Section 5 risk-policy rule is actually enforced in
code, not just documented, and that no execution/credential surface exists.
"""
import json
import os
import unittest

import trading_lab as tl

BASE = os.path.dirname(os.path.abspath(__file__))


def pack(symbol="X", asset_class="equity", closes=None):
    closes = closes or [100] * 25
    ohlcv = [{"date": "2026-01-%02d" % (i + 1), "open": c, "high": c,
              "low": c, "close": c, "volume": 100}
             for i, c in enumerate(closes)]
    return {"instruments": [{"symbol": symbol, "asset_class": asset_class,
                              "ohlcv": ohlcv}]}


class RiskPolicyTests(unittest.TestCase):
    def test_oversized_position_blocked(self):
        rules = [{"symbol": "X", "asset_class": "equity", "fast": 2,
                  "slow": 5, "paper_size_pct": 50}]
        report = tl.run_backtest(rules, pack())
        self.assertTrue(any("BLOCKED" in v and "position size" in v
                             for v in report["assumption_violations"]))
        self.assertEqual(report["trade_list"], [])

    def test_drawdown_halt_triggers(self):
        # A 5% real-policy position can only ever move equity by a few
        # percent even in a full crash, by design - so to exercise the
        # halt itself (not the position-size cap, tested separately) we
        # override max_position_pct for this isolated test only.
        closes = [100, 101, 102, 103, 104, 105] + [40] * 20  # sharp crash
        rules = [{"symbol": "X", "asset_class": "equity", "fast": 2,
                  "slow": 5, "paper_size_pct": 80}]
        report = tl.run_backtest(
            rules, pack(closes=closes),
            risk_policy={"drawdown_halt_pct": -15.0, "max_position_pct": 100.0})
        self.assertTrue(report["halted"])
        self.assertTrue(any("HALT" in v for v in report["assumption_violations"]))

    def test_martingale_reentry_blocked(self):
        # A losing 3% position was already recorded for symbol X; a rule
        # trying to re-enter X at a larger 4% size must be blocked.
        policy = {"max_position_pct": tl.MAX_POSITION_PCT,
                  "max_concentration": tl.MAX_CONCENTRATION_PER_ASSET_CLASS}
        allowed, reason = tl.check_entry_allowed(
            open_positions={}, last_loss_size_pct={"X": 3.0}, symbol="X",
            asset_class="equity", size_pct=4.0, policy=policy)
        self.assertFalse(allowed)
        self.assertIn("martingale", reason)

    def test_reentry_at_equal_or_smaller_size_allowed(self):
        policy = {"max_position_pct": tl.MAX_POSITION_PCT,
                  "max_concentration": tl.MAX_CONCENTRATION_PER_ASSET_CLASS}
        allowed, reason = tl.check_entry_allowed(
            open_positions={}, last_loss_size_pct={"X": 3.0}, symbol="X",
            asset_class="equity", size_pct=3.0, policy=policy)
        self.assertTrue(allowed)
        self.assertIsNone(reason)

    def test_no_leverage_field_anywhere(self):
        source = open(os.path.join(BASE, "trading_lab.py"),
                       encoding="utf-8").read()
        self.assertNotIn("leverage", source.lower())

    def test_no_execution_or_credential_surface(self):
        # Concrete code-level surfaces only - prose like "no brokerage
        # adapter" in comments/docstrings is expected and must not trip this.
        for name in ("trading_lab.py", "build_demo_pack.py"):
            source = open(os.path.join(BASE, name), encoding="utf-8").read().lower()
            for forbidden in ("api_key", "broker_api", "brokerage_credentials",
                              "place_order(", "order_type =", "smtplib",
                              "requests.get(", "requests.post(",
                              "urllib.request.urlopen("):
                self.assertNotIn(forbidden, source,
                                  "%s must not contain %r" % (name, forbidden))

    def test_decision_log_rejects_auto_decision(self):
        with self.assertRaises(tl.RiskPolicyViolation):
            tl.decision_log_entry("D1", [], {}, "b", "b", ["u"],
                                   "AUTO_ACCEPT", "n/a", {})

    def test_decision_log_accepts_valid_human_values(self):
        entry = tl.decision_log_entry(
            "TRL-DEC-DEMO-001", ["TRL-PACK-DEMO-001"],
            {"action": "hold", "symbol": "DEMO-EQ-A", "paper_size_pct": 0,
             "rationale": "demo only", "invalidation_condition": "n/a"},
            "bull_ref", "bear_ref", ["Not yet known: real market behavior"],
            "PENDING", "Founder (not yet reviewed)",
            {"size_ok": True, "concentration_ok": True,
             "drawdown_halt": False, "martingale_block": False})
        self.assertEqual(entry["human_decision"], "PENDING")

    def test_performance_report_forbids_marketing_claims(self):
        report = tl.run_backtest(
            [{"symbol": "X", "asset_class": "equity", "fast": 2, "slow": 5,
              "paper_size_pct": 5}], pack())
        md = tl.performance_report_markdown(report)
        for forbidden in ("guaranteed", "annualized return", "win rate",
                          "real fund", "% return per year"):
            self.assertNotIn(forbidden, md.lower())
        self.assertIn("NOT FINANCIAL ADVICE", md)

    def test_concentration_cap_enforced(self):
        rules = []
        for i in range(4):
            rules.append({"symbol": "E%d" % i, "asset_class": "equity",
                          "fast": 2, "slow": 3, "paper_size_pct": 3})
        multi_pack = {"instruments": [
            {"symbol": "E%d" % i, "asset_class": "equity",
             "ohlcv": [{"date": "2026-01-%02d" % (d + 1), "open": 100,
                        "high": 100, "low": 100, "close": 100 + d,
                        "volume": 10} for d in range(6)]}
            for i in range(4)]}
        report = tl.run_backtest(rules, multi_pack)
        self.assertTrue(any("concentration" in v
                             for v in report["assumption_violations"]))


class DemoPackTests(unittest.TestCase):
    def test_demo_pack_is_labeled_synthetic(self):
        path = os.path.join(BASE, "sample_data", "TRL-PACK-DEMO.json")
        data = json.load(open(path, encoding="utf-8"))
        self.assertIn("SYNTHETIC", data["note"])
        self.assertIn("NOT REAL MARKET DATA", data["note"])

    def test_news_pack_is_labeled_fictional(self):
        path = os.path.join(BASE, "sample_data", "TRL-NEWS-DEMO.json")
        data = json.load(open(path, encoding="utf-8"))
        self.assertIn("FICTIONAL", data["note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
