# ALSAKKAF HOLDING GROUP

# Five-Agent Trading Research Lab — Architecture v1

> "ARCHITECTURE DEMONSTRATION ONLY — NOT FINANCIAL ADVICE — NO LIVE TRADING — NO PROFIT CLAIMS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-001 |
| Document Type | Target Architecture and Verified Baseline |
| Status | ACTIVE — DESIGN AND PROTOTYPE PHASE |
| Version | 1.2 |
| Original Date | 2026-07-14 |
| Last Reconciled | 2026-07-24 |
| Owner | Abdulrahman Khalid Alsakkaf |
| Founder Authority | Approved long-term research architecture; implementation requires an explicitly authorized checkpoint |
| Related Project | PRJ-017 |
| Related Documents | STRAT-017; PRJ-011; `09_AI_Systems/02_Tools/Trading_Lab/TRL_R1_RELEASE_CONTRACT.md` |

---

# 1. Purpose and Boundaries

This document defines the approved target architecture for a controlled trading research lab and records the verified implementation baseline. The lab exists to support disciplined, auditable research. It is not an investment product, a profitability claim, or an authorization to trade.

The project permits local research, deterministic backtesting development, synthetic and historical-data testing, paper/demo simulation, and audited strategy analysis. It prohibits real-money trading, live brokerage connections, external order placement, customer funds, profit promises, claims of proven profitability, autonomous execution, and automatic paper-to-live promotion.

The target architecture, verified prototype, tested behavior, missing components, and Release 1 boundary are distinct. A documented component is not an implemented component, and an implemented component is not validated merely because narrow tests pass.

---

# 2. Target Architecture

```text
Governed Input Pack
  ├── validated market data
  └── validated news items
          ↓
Deterministic Research Core
  ├── Strategy Registry / TRL Strategy Vault
  ├── genuine event signals and regime detection
  ├── causal execution model and realistic recorded costs
  ├── mark-to-market accounting
  └── OOS and walk-forward evaluation
          ↓
Five-Agent Research Team
  ├── News Analyst
  ├── Strategy Analyst
  ├── Bull Analyst
  ├── Bear Analyst
  └── Manager
          ↓
Independent Risk Guardian ── may veto; may never weaken controls
          ↓
Explicit TRADE / NO TRADE research outcome
          ↓
Forward Paper Simulator through a platform-adapter boundary
          ↓
Immutable audit trail and Founder dashboard
```

The deterministic core owns numerical calculations, rule evaluation, accounting, cost application, and reproducibility metadata. AI components may analyze supplied artifacts and explain results, but they may not silently alter deterministic outputs, system hard limits, or audit records.

The platform-adapter boundary is a planned abstraction for approved paper environments. It does not authorize a broker adapter, credentials, external orders, or live trading.

---

# 3. Target Market-Data Input Contract

```json
{
  "pack_id": "TRL-PACK-0001",
  "as_of": "2026-07-14",
  "prepared_by": "human",
  "instruments": [
    {
      "symbol": "EXAMPLE",
      "asset_class": "equity | fx | commodity | index",
      "ohlcv": [
        {
          "date": "2026-07-11",
          "open": 0,
          "high": 0,
          "low": 0,
          "close": 0,
          "volume": 0
        }
      ],
      "data_source": "human-recorded source identifier",
      "data_quality_note": "gaps, adjustments, and known issues"
    }
  ]
}
```

Target rules require schema validation, timestamp ordering and uniqueness, OHLCV validity, declared provenance, data-quality caveats, and rejection of ambiguous or invalid data. No future bar may influence a signal. Release 1 is intentionally single-instrument; multi-instrument work must later align data by timestamp, never by list index.

No market adapter is implemented in the verified baseline. Existing tracked input data is synthetic demo data.

---

# 4. Target News-Input Contract

```json
{
  "pack_id": "TRL-NEWS-0001",
  "as_of": "2026-07-14",
  "items": [
    {
      "headline": "…",
      "source": "publication name",
      "source_reference": "human-supplied reference",
      "published": "2026-07-13",
      "reliability": "official | reputable | low | unverified",
      "summary": "2-3 sentence human or analyst summary"
    }
  ]
}
```

The target News Analyst may downgrade but never upgrade a supplied reliability label. No news adapter or News Analyst is implemented in the verified baseline.

---

# 5. Target Risk Policy and Control Ownership

| Rule | Target boundary |
|------|-----------------|
| Real-money execution | PROHIBITED; no live execution interface is authorized |
| Paper position size | System maximum 5% of paper equity per instrument |
| Paper drawdown halt | System halt threshold at -15% from mark-to-market high-water mark |
| Leverage | None; research positions are unlevered |
| Averaging into losers | PROHIBITED; a losing position may not be increased |
| Position concentration | Target maximum 3 open paper positions per asset class; Release 1 is stricter because it is single-instrument |
| Unknowns | Every Manager synthesis must contain a non-empty “What we do not know” section |
| Claims | No output may contain profit projections, promises, or claims of proven performance |

System hard limits are owned by the deterministic system, outside strategy control. Strategy input may request a lower limit but may never raise a system maximum. Manager and AI components may not override hard limits. A future independent Risk Guardian may veto an otherwise allowed action but may not weaken, bypass, or raise a control.

The current prototype does not satisfy this ownership contract because caller-supplied risk policy can raise nominal maxima. Tests that override limits demonstrate a test path; they do not prove that production-style hard limits are non-overridable.

---

# 6. Target Forward Paper-Simulation Workflow

1. A governed input pack is validated and accepted or rejected with explicit reason codes.
2. The deterministic core evaluates a versioned strategy without future information.
3. The analyst chain reviews supplied artifacts; each output is independently recorded.
4. The Manager produces a synthesis and either a paper-action proposal or an explicit `NO TRADE` outcome.
5. The independent Risk Guardian may veto but cannot weaken system controls.
6. A human records `ACCEPT` or `REJECT` for any paper action.
7. An accepted paper action becomes eligible only under the recorded causal execution rule.
8. A forward paper simulator updates cash, positions, mark-to-market equity, and the audit trail as new data arrives.
9. The Founder dashboard presents results and limitations without profitability claims.

The existing implementation replays historical arrays in one call. It is a historical demo backtest, not this forward paper simulator. The existing “paper portfolio ledger” wording referred to a target workflow and a limited historical accounting layer, not an implemented forward simulator.

---

# 7. Target Decision Record

```json
{
  "decision_id": "TRL-DEC-0001",
  "date": "2026-07-14",
  "input_packs": ["TRL-PACK-0001", "TRL-NEWS-0001"],
  "strategy_id": "governed identifier",
  "strategy_version": "governed version",
  "manager_outcome": {
    "outcome": "PAPER_ACTION | NO_TRADE",
    "action": "open | close | hold | null",
    "symbol": "EXAMPLE",
    "paper_size_pct": 0,
    "reason_codes": ["stable reason code"],
    "rationale": "…",
    "invalidation_condition": "…"
  },
  "bull_case_ref": "artifact path",
  "bear_case_ref": "artifact path",
  "unknowns": ["…"],
  "human_decision": "ACCEPT | REJECT | NOT_APPLICABLE",
  "risk_policy_checks": {
    "size_ok": true,
    "drawdown_halt": false,
    "risk_guardian_veto": false
  }
}
```

The current helper can construct a limited decision-log dictionary but does not implement this governed workflow, explicit `NO TRADE` contract, analyst chain, or independent Risk Guardian.

---

# 8. Target Research Report

The target report includes:

- Input, engine, strategy, execution, cost, terminal-position, and risk-policy identities.
- Per-bar cash, position value, total mark-to-market equity, and high-water mark.
- Open positions and closed hypothetical trades.
- Explicit `NO TRADE`, blocked, and halt events with stable reason codes.
- In-sample, out-of-sample, and walk-forward evidence when those gates are implemented.
- Data-quality limitations, assumption violations, and unresolved unknowns.
- Analyst calibration notes and an immutable audit reference.
- A fixed paper-only, hypothetical-results disclaimer.

Forbidden report content includes annualized projections presented as expectations, win-rate marketing, comparisons implying parity with real funds, profit promises, and any claim that synthetic results prove future performance.

---

# 9. Target Deterministic Backtest Contract

The target interface accepts validated data, a governed declarative strategy version, and a system-owned risk configuration. It returns a reproducible research result containing an equity curve, drawdown, hypothetical fills, positions, costs, `NO TRADE` or blocked outcomes, assumption violations, and complete audit metadata.

The target engine must provide:

- Strict input validation before evaluation.
- Genuine event detection rather than a continuing regime label.
- A causal signal-and-fill sequence.
- Deterministic next-bar execution with the exact assumed price recorded in every result.
- Per-bar cash and mark-to-market accounting.
- Explicit terminal-position handling.
- Deterministic transaction costs, commission, spread, and slippage assumptions.
- System-owned, non-overridable hard-risk maxima.
- Reproducibility identifiers and stable reason codes.
- Out-of-sample and walk-forward evaluation before any research-validity consideration.

No executable code may be loaded from strategy files. No future information may influence a signal.

---

# 10. Strategy Governance and Research Components

The approved long-term architecture includes:

- A Strategy Registry containing identity, version, parameters, status, evidence, limitations, and approval history.
- A TRL Strategy Vault for governed strategy artifacts; automation is planned, not implemented.
- Regime detection that is distinct from strategy event generation.
- SMA-001 only after a governed record is created. No such record currently exists, and SMA logic in the demo is not Founder-approved.
- FIB-001 only after separate specification, review, and authorization. It is not specified or implemented.
- Out-of-sample and walk-forward testing.
- Realistic cost-model evolution beyond the fixed Release 1 baseline.
- An independent Risk Guardian and auditable veto records.

No strategy is currently approved for real-money use or proven profitable.

---

# 11. Verified Implemented Baseline — TRL-R1-001

The read-only audit completed on 2026-07-24 verified the following baseline:

- A local deterministic demo prototype exists at `09_AI_Systems/02_Tools/Trading_Lab/`.
- It includes a historical backtest function, SMA calculations, selected risk checks, a decision-log helper, a Markdown performance-report generator, and a fixed-seed synthetic pack generator.
- Twelve narrow `unittest` tests pass.
- Five `ResourceWarning` events occur because test code opens files without closing them.
- Tracked demo market/news inputs and generated reports are synthetic, fictional, and hypothetical.
- There is no broker, credential, network, external-order, or live-trading capability.
- The five-agent workflow is documented only.

Direct tests do not establish strategy validity, profitability, realistic execution, correct portfolio accounting, complete architecture enforcement, or production readiness. Current demo results must not support an investment decision or performance claim.

---

# 12. Verified Defects and Missing Components

## 12.1 Known defects in the current prototype

- SMA output describes the current fast-above-slow regime; it is not a genuine crossover event.
- Bar `t` close information produces a signal and a fill at the same already-known close.
- Open-position profit and loss is not marked to market.
- Drawdown is computed from realized equity only and can be materially understated.
- Multiple instrument series are aligned by list index rather than timestamp.
- Transaction costs, commissions, spread, and slippage are absent.
- Caller-controlled risk policy can weaken nominal hard limits.
- Explicit `NO TRADE` results and stable blocked-reason codes are absent.
- Terminal open-position handling is not explicit.

## 12.2 Missing or planned components

- Governed SMA-001 record and any FIB-001 specification or implementation.
- Strategy Registry and TRL Strategy Vault.
- Regime-detection subsystem.
- Out-of-sample and walk-forward test harnesses.
- Independent Risk Guardian.
- Five-agent research workflow.
- Market and news adapters.
- Forward paper simulator.
- Platform adapters.
- Immutable audit-trail service and Founder dashboard.
- Local AI and Gemma evaluation.

---

# 13. Release 1 Boundary

Release 1 is a validated, causal, deterministic, single-instrument research kernel. Its detailed acceptance contract is `TRL_R1_RELEASE_CONTRACT.md`.

The causal timing rule is mandatory:

1. Bar `t` is validated and closes.
2. A genuine strategy event may be calculated using information available through the close of bar `t` only.
3. That event cannot fill at bar `t`’s already-known closing price.
4. A resulting order becomes eligible at the next chronological validated bar, `t+1`.
5. Release 1 assumes a fill based on the `t+1` open, adjusted by the recorded deterministic cost/slippage model.
6. If no valid next bar exists, no fill occurs and the result records the applicable reason code.

Every result must record the next-bar price assumption. No future bar, including the `t+1` open, may influence the signal calculated at `t`.

Release 1 excludes multi-asset portfolios, FIB-001, Strategy Vault automation, the five-agent workflow, local AI, Gemma, dashboards, broker/platform adapters, and live trading. Those exclusions do not remove them from the approved long-term architecture.

---

# 14. Escalation and Review

Any request to connect live data, brokerage services, external order systems, credentials, or real funds is outside PRJ-017’s current authority and must be escalated to the Founder as a separately governed decision. This document never authorizes implementation by itself.

---

# 15. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial design-only architecture |
| 1.1 | 2026-07-15 | Recorded the Founder-authorized paper-only historical prototype and the still-unimplemented analyst chain |
| 1.2 | 2026-07-24 | Reconciled target architecture, verified baseline, defects, missing components, control ownership, causal timing, Release 1 boundary, and continuous section numbering after TRL-R1-001 |
