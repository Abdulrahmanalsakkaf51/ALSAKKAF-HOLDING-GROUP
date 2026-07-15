# ALSAKKAF HOLDING GROUP

# Five-Agent Trading Research Lab — Architecture v1

> "ARCHITECTURE DEMONSTRATION ONLY — NOT FINANCIAL ADVICE — NO LIVE TRADING — NO PROFIT CLAIMS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-001 |
| Document Type | Architecture Design (research lab; Section 12 prototype implemented) |
| Status | Draft — awaiting Founder review (paper-only prototype authorized) |
| Version | 1.1 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-017 |
| Related Documents | STRAT-017, PRJ-011 (Playground demo), 09_AI_Systems/02_Tools/Trading_Lab/ |

---

# 1. Purpose and Boundaries

A research lab architecture for multi-agent market analysis. It exists to (a) demonstrate disciplined multi-agent design to prospective clients, and (b) study whether adversarial analyst structures produce better-calibrated research. It is not an investment product. Nothing in this design can place a trade: there is no brokerage adapter, no credential field anywhere in any schema, and no order type in any interface.

---

# 2. Pipeline Architecture

```text
Input Pack (files, human-supplied)
  ├── market_data.json  (schema §3)
  └── news_items.json   (schema §4)
        ↓
News Analyst      → news summary with per-source reliability labels
Strategy Analyst  → scenario map with explicit assumptions
Bull Analyst      → strongest honest positive case (cites scenario assumptions)
Bear Analyst      → strongest honest negative case (must attack bull assumptions)
        ↓
Manager           → synthesis: agreements, disagreements, unknowns,
                    paper-action proposal (§6) bounded by risk policy (§5)
        ↓
Decision Log (§7) → Paper Portfolio Ledger → Performance Report (§8)
```

Every stage reads only the artifacts of prior stages. No agent has network access in v1; input packs are supplied by a human.

---

# 3. Market-Data Input Format

```json
{
  "pack_id": "TRL-PACK-0001",
  "as_of": "2026-07-14",
  "prepared_by": "human",
  "instruments": [
    {
      "symbol": "EXAMPLE",
      "asset_class": "equity | fx | commodity | index",
      "ohlcv": [{"date": "2026-07-11", "open": 0, "high": 0, "low": 0,
                  "close": 0, "volume": 0}],
      "data_source": "name + URL of the human-chosen source",
      "data_quality_note": "gaps, adjustments, known issues"
    }
  ]
}
```

Rules: no live feeds in v1; historical files only; every pack names its source and quality caveats.

---

# 4. News-Summary Input Format

```json
{
  "pack_id": "TRL-NEWS-0001",
  "as_of": "2026-07-14",
  "items": [
    {
      "headline": "…",
      "source": "publication name",
      "url": "…",
      "published": "2026-07-13",
      "reliability": "official | reputable | low | unverified",
      "summary": "2-3 sentence human or analyst summary"
    }
  ]
}
```

The News Analyst may downgrade but never upgrade a reliability label.

---

# 5. Risk Policy (design constraints, not preferences)

| Rule | Value |
|------|-------|
| Real-money execution | PROHIBITED — no execution interface exists |
| Paper position size | Max 5% of paper portfolio per instrument |
| Paper portfolio drawdown halt | Analysis pipeline flags HALT at -15% from high-water mark; Manager must document before any further proposals |
| Leverage | None. Paper positions are unlevered |
| Averaging into losers (martingale-like) | PROHIBITED — a losing paper position may not be increased |
| Position concentration | Max 3 open paper positions per asset class |
| Unknowns rule | Every Manager synthesis must contain a non-empty "What we do not know" section |
| Claims rule | No output may contain profit projections or performance promises |

---

# 6. Paper / Demo-Trading Workflow

1. Human supplies an input pack (§3, §4).
2. Analyst chain runs (§2); each output is a standalone artifact.
3. Manager produces a synthesis with at most one paper-action proposal: `{action: open|close|hold, symbol, paper_size_pct ≤ 5, rationale, invalidation_condition}`.
4. A human reviews the proposal and records ACCEPT or REJECT in the decision log. Nothing updates the paper ledger without the human record.
5. The paper ledger applies accepted actions at the next pack's prices — no intraday pretence.
6. Weekly performance report (§8).

---

# 7. Decision Log Format

```json
{
  "decision_id": "TRL-DEC-0001",
  "date": "2026-07-14",
  "input_packs": ["TRL-PACK-0001", "TRL-NEWS-0001"],
  "manager_proposal": {"action": "hold", "symbol": "EXAMPLE",
                        "paper_size_pct": 0, "rationale": "…",
                        "invalidation_condition": "…"},
  "bull_case_ref": "artifact path",
  "bear_case_ref": "artifact path",
  "unknowns": ["…"],
  "human_decision": "ACCEPT | REJECT",
  "human_name": "…",
  "risk_policy_checks": {"size_ok": true, "concentration_ok": true,
                          "drawdown_halt": false, "martingale_block": false}
}
```

---

# 8. Performance-Report Format

Weekly Markdown report with: paper portfolio value series (from ledger, computed); open paper positions; closed-action outcomes vs. invalidation conditions; analyst calibration notes (which analyst's case aged better, with examples); risk-policy events (halts, blocked proposals); and the fixed footer disclaimer. Forbidden content: annualized projections, win-rate marketing, any comparison to real funds.

---

# 9. Backtest Interface (definition only)

`run_backtest(strategy_rules, historical_packs, risk_policy) → BacktestReport` where `strategy_rules` are declarative conditions (no code execution from strategy files), `historical_packs` are §3 files, and `BacktestReport` contains equity curve, max drawdown, trade list, and assumption violations. The interface definition exists so a future paper-only prototype has a fixed contract; no implementation is authorized in this phase.

---

# 10. Escalation and Review

Any request to connect live data, brokerage APIs, or real funds is out of scope and must be escalated to the Founder as a new project with Guardian review. This document alone never authorizes implementation.

---

# 12. Implementation Update — Paper-Only Backtest Prototype

Founder authorized a paper-only prototype of the backtest interface (Section 9) on 2026-07-15. Implemented at `09_AI_Systems/02_Tools/Trading_Lab/` (`trading_lab.py`, `build_demo_pack.py`, `test_trading_lab.py`). Scope so far:

- `run_backtest()` implements the Section 9 interface using declarative SMA-cross strategy rules (plain JSON integers — no code execution from strategy files).
- All Section 5 risk-policy rules are enforced in code and unit-tested: 5% max paper position size, -15% drawdown halt, no leverage field anywhere, martingale (loss re-entry) block, max 3 open positions per asset class.
- Market data used is 100% synthetic (fixed-seed generator, fictional symbol `DEMO-EQ-A`), clearly labeled `SYNTHETIC EXAMPLE DATA - NOT REAL MARKET DATA` — no live feed, no network access anywhere in the code.
- Decision Log (Section 7) and Performance Report (Section 8) generators are implemented; the one demo decision log entry has `human_decision: "PENDING"` — nothing here is an accepted trade.
- Not yet implemented: the News/Strategy/Bull/Bear/Manager analyst chain (Section 2) — the current prototype is the backtest/ledger layer only, driven directly by a strategy rule rather than analyst synthesis.
- Still out of scope, unchanged from Section 1/10: no brokerage adapter, no credential field, no order type, no live trading, no real funds.

---

# 13. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial design-only architecture |
| 1.1 | 2026-07-15 | Added Section 12: Founder-authorized paper-only backtest/ledger prototype implemented and unit-tested; analyst chain still not implemented |
