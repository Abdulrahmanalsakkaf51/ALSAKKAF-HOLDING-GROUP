# -*- coding: utf-8 -*-
"""Deterministic paper-only Markdown reporting."""

from .constants import DISCLAIMER, PERFORMANCE_DISCLAIMER

def performance_report_markdown(report, title="Paper Portfolio Performance Report"):
    """Render a deterministic in-memory paper-only report."""
    metadata = report["metadata"]
    instrument = metadata.get("instrument") or {}
    lines = [
        "# %s" % title,
        "",
        "> \"%s\"" % DISCLAIMER,
        "",
        "> %s" % PERFORMANCE_DISCLAIMER,
        "",
        "## Research Identity",
        "",
        "- Run: %s" % metadata["run_id"],
        "- Engine: %s %s" % (metadata["engine"]["name"],
                              metadata["engine"]["version"]),
        "- Strategy: %s %s" % (metadata.get("strategy_id"),
                                metadata.get("strategy_version")),
        "- Data pack / as-of: %s / %s" % (metadata.get("pack_id"),
                                           metadata.get("data_as_of")),
        "- Instrument: %s (%s)" % (instrument.get("symbol"),
                                    instrument.get("asset_class")),
        "- Outcome: %s / %s" % (report["outcome"], report["reason_code"]),
        "",
        "## Mark-to-Market Accounting",
        "",
        "- Final cash: %.8f" % report["final_cash"],
        "- Final marked equity: %.8f" % report["final_equity"],
        "- Realized P&L: %.8f" % report["realized_pnl"],
        "- Unrealized P&L: %.8f" % report["unrealized_pnl"],
        "- Commission: %.8f" % report["cumulative_commission"],
        "- Slippage allowance: %.8f" % report["cumulative_slippage_cost"],
        "- Maximum marked drawdown: %.8f%%" % report["max_drawdown_pct"],
        "",
        "## Closed Hypothetical Trades",
        "",
    ]
    if report["trade_list"]:
        for trade in report["trade_list"]:
            lines.append(
                "- %s: entry signal %s, fill %s; exit signal %s, fill %s; "
                "net realized P&L %.8f"
                % (trade["symbol"], trade["entry_signal_time"],
                   trade["entry_fill_time"], trade["exit_signal_time"],
                   trade["exit_fill_time"], trade["net_realized_pnl"])
            )
    else:
        lines.append("- None.")
    lines += ["", "## Terminal Position", ""]
    if report["open_position"]:
        position = report["open_position"]
        lines.append(
            "- OPEN: %.12f units, entry fill %s @ %.8f, final market value "
            "%.8f, unrealized P&L %.8f. No terminal liquidation was invented."
            % (position["units"], position["entry_fill_time"],
               position["slipped_fill_price"], position["market_value"],
               position["unrealized_pnl"])
        )
    else:
        lines.append("- None.")
    unfilled = [decision for decision in report["decisions"]
                if decision["status"] == "NO_FILL"]
    lines += ["", "## Unfilled Signals", ""]
    if unfilled:
        for decision in unfilled:
            lines.append("- %s at %s: %s" % (
                decision["action"], decision["signal_timestamp"],
                decision["reason_code"],
            ))
    else:
        lines.append("- None.")
    lines += [
        "", "---", "",
        "*PAPER/RESEARCH ONLY. %s*" % PERFORMANCE_DISCLAIMER,
        "",
    ]
    return "\n".join(lines)
