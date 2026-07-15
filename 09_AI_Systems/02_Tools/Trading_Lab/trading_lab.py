# -*- coding: utf-8 -*-
"""AOS Trading Research Lab - paper-only backtest engine (PRJ-017 / TRL-001).

ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING -
NO PROFIT CLAIMS.

Implements the backtest interface and paper-portfolio ledger defined in
Trading_Research_Lab_Architecture.md (TRL-001 Section 9), under Founder
authorization to begin a paper-only prototype (see TRL-001 Revision
History). Stdlib only. No network access. No brokerage adapter. No
credential field anywhere in any schema. No order type - "trades" here are
paper ledger entries only, applied at next-pack closing prices.

Usage (from repo root):
  py 09_AI_Systems\\02_Tools\\Trading_Lab\\build_demo_pack.py
  py 09_AI_Systems\\02_Tools\\Trading_Lab\\trading_lab.py --demo
"""
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DISCLAIMER = ("ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - "
              "NO LIVE TRADING - NO PROFIT CLAIMS")

# Risk policy constants - TRL-001 Section 5. Not preferences; hard limits
# enforced in code.
MAX_POSITION_PCT = 5.0
DRAWDOWN_HALT_PCT = -15.0
MAX_CONCENTRATION_PER_ASSET_CLASS = 3


class RiskPolicyViolation(Exception):
    pass


def sma(closes, period):
    """Simple moving average series; None until enough data exists."""
    out = []
    for i in range(len(closes)):
        if i + 1 < period:
            out.append(None)
        else:
            out.append(sum(closes[i + 1 - period:i + 1]) / float(period))
    return out


def sma_cross_signals(ohlcv, fast, slow):
    """Declarative SMA-cross signal generator. No code execution from
    strategy files - fast/slow are plain integers from a JSON rule."""
    closes = [bar["close"] for bar in ohlcv]
    fast_series = sma(closes, fast)
    slow_series = sma(closes, slow)
    signals = []
    for i, bar in enumerate(ohlcv):
        f, s = fast_series[i], slow_series[i]
        if f is None or s is None:
            signals.append((bar["date"], "none"))
            continue
        signals.append((bar["date"], "enter" if f > s else "exit"))
    return signals


def _asset_class_open_count(open_positions, asset_class):
    return sum(1 for p in open_positions.values()
               if p["asset_class"] == asset_class)


def check_entry_allowed(open_positions, last_loss_size_pct, symbol,
                         asset_class, size_pct, policy):
    """Risk-policy gate for opening a new paper position (TRL-001 Section 5).
    Returns (allowed: bool, reason: str or None). Pure function - no state
    mutation - so each rule can be tested in isolation."""
    prior_loss = last_loss_size_pct.get(symbol)
    if prior_loss is not None and size_pct > prior_loss:
        return False, (
            "BLOCKED (martingale rule): %s re-entry at %.1f%% exceeds "
            "prior losing size %.1f%%" % (symbol, size_pct, prior_loss))
    if _asset_class_open_count(open_positions, asset_class) >= \
            policy["max_concentration"]:
        return False, (
            "BLOCKED (concentration rule): %s open would exceed max %d "
            "positions in asset class %s"
            % (symbol, policy["max_concentration"], asset_class))
    return True, None


def run_backtest(strategy_rules, historical_pack, risk_policy=None):
    """run_backtest(strategy_rules, historical_packs, risk_policy) ->
    BacktestReport, per TRL-001 Section 9.

    strategy_rules: list of declarative dicts, each:
      {"symbol": str, "asset_class": str, "fast": int, "slow": int,
       "paper_size_pct": float}
    historical_pack: parsed TRL-PACK JSON (Section 3 schema).
    risk_policy: optional override dict for the constants above (tests use
      this to exercise limits without waiting for real market moves).
    """
    policy = {
        "max_position_pct": MAX_POSITION_PCT,
        "drawdown_halt_pct": DRAWDOWN_HALT_PCT,
        "max_concentration": MAX_CONCENTRATION_PER_ASSET_CLASS,
    }
    if risk_policy:
        policy.update(risk_policy)

    instruments = {i["symbol"]: i for i in historical_pack["instruments"]}
    equity = 100.0
    high_water_mark = equity
    halted = False
    open_positions = {}   # symbol -> {asset_class, entry_price, entry_date, size_pct}
    last_loss_size_pct = {}   # symbol -> size_pct of most recent losing trade (global, cross-rule)
    trade_list = []
    assumption_violations = []
    equity_curve = []

    # Build one active rule + signal series per valid symbol, so state
    # (equity, halted, concentration, martingale memory) is shared across
    # all rules instead of resetting per rule.
    active = []
    for rule in strategy_rules:
        symbol = rule["symbol"]
        instrument = instruments.get(symbol)
        if instrument is None:
            assumption_violations.append(
                "Strategy rule references unknown symbol %s - skipped" % symbol)
            continue
        if rule["paper_size_pct"] > policy["max_position_pct"]:
            assumption_violations.append(
                "BLOCKED: rule for %s requested %.1f%% > max %.1f%% paper "
                "position size" % (symbol, rule["paper_size_pct"],
                                    policy["max_position_pct"]))
            continue
        ohlcv = instrument["ohlcv"]
        signals = sma_cross_signals(ohlcv, rule["fast"], rule["slow"])
        active.append({
            "rule": rule, "symbol": symbol,
            "asset_class": instrument["asset_class"],
            "ohlcv": ohlcv, "signals": signals,
        })

    max_len = max((len(a["signals"]) for a in active), default=0)

    for idx in range(max_len):
        date = None
        for a in active:
            if idx < len(a["signals"]):
                date = a["signals"][idx][0]
                break
        if date is None:
            continue

        if not halted:
            for a in active:
                if idx >= len(a["signals"]):
                    continue
                symbol, asset_class, rule = a["symbol"], a["asset_class"], a["rule"]
                _, action = a["signals"][idx]
                price = a["ohlcv"][idx]["close"]

                if action == "enter" and symbol not in open_positions:
                    allowed, reason = check_entry_allowed(
                        open_positions, last_loss_size_pct, symbol,
                        asset_class, rule["paper_size_pct"], policy)
                    if not allowed:
                        assumption_violations.append("%s on %s" % (reason, date))
                    else:
                        open_positions[symbol] = {
                            "asset_class": asset_class,
                            "entry_price": price,
                            "entry_date": date,
                            "size_pct": rule["paper_size_pct"],
                        }

                elif action == "exit" and symbol in open_positions:
                    pos = open_positions.pop(symbol)
                    pnl_pct = (price - pos["entry_price"]) / pos["entry_price"] * 100.0
                    equity_delta = equity * (pos["size_pct"] / 100.0) * (pnl_pct / 100.0)
                    equity += equity_delta
                    trade_list.append({
                        "symbol": symbol,
                        "entry_date": pos["entry_date"],
                        "exit_date": date,
                        "entry_price": pos["entry_price"],
                        "exit_price": price,
                        "size_pct": pos["size_pct"],
                        "pnl_pct": round(pnl_pct, 4),
                    })
                    if pnl_pct < 0:
                        last_loss_size_pct[symbol] = pos["size_pct"]
                    else:
                        last_loss_size_pct.pop(symbol, None)

            high_water_mark = max(high_water_mark, equity)
            drawdown_pct = (equity - high_water_mark) / high_water_mark * 100.0
            if drawdown_pct <= policy["drawdown_halt_pct"] and not halted:
                halted = True
                assumption_violations.append(
                    "HALT: drawdown %.2f%% breached %.1f%% limit on %s - "
                    "Manager must document before any further proposals"
                    % (drawdown_pct, policy["drawdown_halt_pct"], date))

        equity_curve.append({"date": date, "equity": round(equity, 4)})

    max_drawdown = 0.0
    peak = equity_curve[0]["equity"] if equity_curve else 100.0
    for point in equity_curve:
        peak = max(peak, point["equity"])
        dd = (point["equity"] - peak) / peak * 100.0
        max_drawdown = min(max_drawdown, dd)

    return {
        "report_type": "BacktestReport",
        "disclaimer": DISCLAIMER,
        "equity_curve": equity_curve,
        "max_drawdown_pct": round(max_drawdown, 4),
        "trade_list": trade_list,
        "assumption_violations": assumption_violations,
        "final_equity": round(equity, 4),
        "halted": halted,
    }


def performance_report_markdown(report, title="Paper Portfolio Performance Report"):
    """Weekly performance report per TRL-001 Section 8. Forbidden content:
    annualized projections, win-rate marketing, comparison to real funds -
    none of those are computed or written here."""
    import datetime
    lines = [
        "# %s" % title,
        "",
        "> \"%s\"" % DISCLAIMER,
        "",
        "## Document Information",
        "",
        "| Field | Value |",
        "|-------|-------|",
        "| Generated By | Trading Research Lab (`trading_lab.py`) |",
        "| Status | Paper-only demo - not a recommendation |",
        "| Date | %s |" % datetime.date.today().isoformat(),
        "| Related Project | PRJ-017 |",
        "| Related Document | TRL-001 |",
        "",
        "## Paper Portfolio Value Series (from ledger, computed)",
        "",
    ]
    for point in report["equity_curve"][-10:] or [{"date": "n/a", "equity": 100.0}]:
        lines.append("- %s: %.4f" % (point["date"], point["equity"]))
    lines += ["", "## Closed Paper Trades", ""]
    if report["trade_list"]:
        for t in report["trade_list"]:
            lines.append(
                "- %s: entered %s @ %.4f, exited %s @ %.4f, size %.1f%%, "
                "pnl %.2f%%" % (t["symbol"], t["entry_date"], t["entry_price"],
                                 t["exit_date"], t["exit_price"], t["size_pct"],
                                 t["pnl_pct"]))
    else:
        lines.append("- None closed in this pack.")
    lines += ["", "## Risk-Policy Events (halts, blocked proposals)", ""]
    if report["assumption_violations"]:
        for v in report["assumption_violations"]:
            lines.append("- %s" % v)
    else:
        lines.append("- None recorded.")
    lines += [
        "", "## Analyst Calibration Notes", "",
        "- Not yet populated: requires multiple packs over time to compare "
        "bull/bear case aging. See TRL-001 Section 8.",
        "", "## Final Paper Equity (starting base = 100.0, not real currency)",
        "", "- %.4f (max drawdown observed: %.2f%%)"
        % (report["final_equity"], report["max_drawdown_pct"]),
        "", "---", "", "*%s*" % DISCLAIMER, "",
    ]
    return "\n".join(lines)


def decision_log_entry(decision_id, input_packs, manager_proposal, bull_ref,
                        bear_ref, unknowns, human_decision, human_name,
                        risk_checks):
    """Decision Log Format per TRL-001 Section 7. human_decision must be
    supplied by an actual human review - this function does not decide."""
    if human_decision not in ("ACCEPT", "REJECT", "PENDING"):
        raise RiskPolicyViolation(
            "human_decision must be ACCEPT, REJECT, or PENDING - never auto-set")
    return {
        "decision_id": decision_id,
        "input_packs": input_packs,
        "manager_proposal": manager_proposal,
        "bull_case_ref": bull_ref,
        "bear_case_ref": bear_ref,
        "unknowns": unknowns,
        "human_decision": human_decision,
        "human_name": human_name,
        "risk_policy_checks": risk_checks,
    }


if __name__ == "__main__":
    import sys
    if "--demo" in sys.argv:
        pack_path = os.path.join(BASE, "sample_data", "TRL-PACK-DEMO.json")
        with open(pack_path, encoding="utf-8") as handle:
            pack = json.load(handle)
        rules = [{"symbol": "DEMO-EQ-A", "asset_class": "equity",
                  "fast": 5, "slow": 20, "paper_size_pct": 5}]
        report = run_backtest(rules, pack)
        out_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(BASE))),
            "01_Holding_Company", "08_Reports", "Trading_Lab_Demo")
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "Backtest_Report_Demo.json"),
                   "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
        with open(os.path.join(out_dir, "Performance_Report_Demo.md"),
                   "w", encoding="utf-8") as handle:
            handle.write(performance_report_markdown(report))
        print("Demo backtest complete. Final paper equity: %.4f (base 100.0)"
              % report["final_equity"])
        print("Max drawdown: %.2f%%" % report["max_drawdown_pct"])
        print("Violations logged: %d" % len(report["assumption_violations"]))
        print(DISCLAIMER)
