# ALSAKKAF HOLDING GROUP

# PRJ-017 — Five-Agent Trading Research Lab

> "ARCHITECTURE DEMONSTRATION ONLY — NOT FINANCIAL ADVICE — NO LIVE TRADING — NO PROFIT CLAIMS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-017 |
| Document Type | Project Record |
| Status | ACTIVE — DESIGN AND PROTOTYPE PHASE |
| Active Checkpoint | TRL-R1-002 — Baseline Reconciliation and Release 1 Contract |
| Version | 1.1 |
| Original Date | 2026-07-14 |
| Last Reconciled | 2026-07-24 |
| Owner | Abdulrahman Khalid Alsakkaf |
| Approved By | Founder for explicitly authorized research and prototype checkpoints only; no strategy is Founder-approved |
| Related System | AOS |
| Related Projects | PRJ-011 (Playground trading demo), PRJ-016, STRAT-017 |
| Related Documents | TRL-001; `09_AI_Systems/02_Tools/Trading_Lab/TRL_R1_RELEASE_CONTRACT.md` |

---

# 1. Objective

Develop a controlled, paper-only trading research lab. The approved target architecture includes a deterministic research core, governed strategies, independent risk controls, a five-agent research workflow, realistic research testing, a paper simulator, auditable records, and Founder-facing reporting.

PRJ-017 is not an investment product and is not production-ready. Its present implementation is a narrow deterministic demo backtest prototype, not the complete target architecture.

---

# 2. Target Research Roles

These roles are approved architecture but are not implemented in the current prototype.

| Role | Target responsibility |
|------|-----------------------|
| Manager | Frames the research question, synthesizes analyst views, states unknowns, and logs the decision record |
| News Analyst | Summarizes supplied news items with source-reliability labels |
| Strategy Analyst | Maps scenarios and the assumptions each depends on |
| Bull Analyst | Presents the strongest honest positive case |
| Bear Analyst | Presents the strongest honest negative case, including risks the bull case underweights |

---

# 3. Authorized Product Boundary

## 3.1 Allowed

- Local research.
- Deterministic backtesting development.
- Synthetic and historical-data testing.
- Paper/demo simulation.
- Audited strategy analysis.

## 3.2 Prohibited

- Real-money trading or customer funds.
- Live brokerage connections, external order placement, credentials, or network execution.
- Profit promises or claims of proven profitability.
- Autonomous execution.
- Automatic paper-to-live promotion.
- Unrestricted leverage, martingale, or any unbounded-loss strategy.

Any capability outside the allowed boundary requires a new, explicit Founder authorization. Documentation alone does not authorize implementation.

---

# 4. Reconciled Status as of 2026-07-24

| Classification | Current status |
|----------------|----------------|
| Approved target architecture | Documented in TRL-001 and retained as the long-term direction. |
| Implemented prototype | A local, deterministic historical demo backtest, synthetic input-pack generator, decision-log helper, and Markdown performance-report generator exist. There is no broker, credential, network, or live-order capability. |
| Directly tested | Twelve narrow `unittest` tests pass. They exercise selected risk checks, decision-log values, demo labels, marketing-phrase exclusions, and absence of selected execution/credential strings. Five `ResourceWarning` events are emitted because tests leave file handles unclosed. |
| Evidence limit | The tests establish only the behavior they directly assert. They do not establish research validity, profitability, production readiness, realistic execution, or complete enforcement of every architectural rule. |
| Data and reports | Existing tracked data and generated reports are synthetic/demo-only and hypothetical. They do not represent actual trading. |
| Project phase | ACTIVE — DESIGN AND PROTOTYPE PHASE. TRL-R1-002 is the active documentation checkpoint. |

Current demo performance results are unsuitable for investment decisions, real-money trade decisions, or performance and profitability claims.

---

# 5. Known Prototype Defects and Limitations

- The SMA implementation emits an `enter` or `exit` regime state after warm-up; it does not detect a genuine crossing event.
- A signal calculated from bar `t` close fills at that same close, causing look-ahead/same-bar execution bias.
- Open positions are not marked to market. Equity changes only on exit.
- Drawdown is realized-only and can be materially understated.
- Multiple instruments are processed by list index rather than aligned timestamps.
- Transaction costs, commissions, spread, and slippage are absent.
- Caller-supplied risk policy can raise nominal system limits, so the stated hard limits are not system-owned and non-overridable.
- Explicit `NO TRADE` outcomes and stable blocked-reason codes are absent.
- Terminal open-position handling is not explicit in the result contract.
- There is no governed SMA-001 strategy record. FIB-001 is neither specified nor implemented. No strategy is Founder-approved.

---

# 6. Missing or Planned Components

The following are target or planned components, not verified current capabilities:

- Strategy Registry and TRL Strategy Vault.
- Regime detection and FIB-001 specification or implementation.
- Out-of-sample and walk-forward testing.
- Realistic, recorded cost models.
- Independent Risk Guardian.
- Five-agent research workflow.
- Market and news adapters.
- Forward paper-trading simulator.
- Platform-adapter boundary.
- Founder dashboard.
- Local AI and Gemma evaluation.

The existing historical backtest is not a forward paper simulator. The phrase “paper portfolio ledger” in earlier material described a target workflow and a limited historical accounting layer; it did not establish a completed forward simulator.

---

# 7. Project Tasks and Checkpoints

| # | Task | Reconciled status |
|---|------|-------------------|
| 1 | Architecture and design document (TRL-001) | Approved target architecture documented; reconciled under TRL-R1-002 |
| 2 | Input format schemas | Documented target; strict Release 1 validation not implemented |
| 3 | Risk policy design | Documented target; current prototype does not make all maxima non-overridable |
| 4 | Backtest interface and paper-trading workflow | Historical demo backtest partially implemented; forward paper workflow not implemented |
| 5 | Decision log and performance report formats | Formats documented; limited generators implemented; outputs remain demo-only |
| 6 | TRL-R1-001 read-only audit | Completed 2026-07-24 |
| 7 | TRL-R1-002 baseline reconciliation and Release 1 contract | Active documentation checkpoint |
| 8 | TRL-R1-003 validated causal single-instrument research kernel | Proposed next engineering checkpoint; not started and not authorized by this document |

---

# 8. Progress Log

| Date | Update |
|------|--------|
| 2026-07-14 | Project created with design-only scope under PRJ-016 mission Part 9. TRL-001 written. At that date there was no code, data connection, or execution capability. |
| 2026-07-15 | Founder authorized a paper-only prototype. A deterministic synthetic-data historical backtest and limited reporting helpers were added. This superseded the earlier “design phase only” and “no code” status statements without changing the prohibition on live trading. |
| 2026-07-24 | TRL-R1-001 read-only audit completed. It verified the prototype and twelve passing narrow tests, identified five unclosed-file `ResourceWarning` events, and established the defects, missing components, and evidence limits recorded above. The audited worktree was clean after the audit. |
| 2026-07-24 | TRL-R1-002 opened as the active documentation checkpoint to reconcile the baseline and define the Release 1 contract. Corrected implementation work is explicitly deferred. |

---

# 9. Historical Corrections

- “Active — design phase only” and “No code” were accurate on 2026-07-14 but became obsolete after the 2026-07-15 prototype authorization and implementation.
- “All Section 5 risk-policy rules are enforced in code and unit-tested” is superseded. The tests cover selected narrow cases, and caller-controlled policy can weaken nominal hard limits.
- References to a completed “paper portfolio ledger” are qualified as a limited historical backtest/accounting layer. No forward paper simulator exists.
- Any wording implying a complete prototype, validated strategy, research validity, profitability, or production readiness is superseded by the reconciled status and evidence limits in this record.

---

# 10. Deferred Governance Reconciliation

Reconciliation entries in `Project_Register.md` and `Knowledge_Register.md` are intentionally deferred because those registers contain unrelated changes in a separate dirty main working directory. They are not authorized for modification in TRL-R1-002.

---

# 11. Public Wording Rule

Any public reference must carry: **ARCHITECTURE DEMONSTRATION ONLY — NOT FINANCIAL ADVICE — NO LIVE TRADING — NO PROFIT CLAIMS.** It must not present synthetic results as actual or proven performance.

---

# 12. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial design-only project record |
| 1.1 | 2026-07-24 | Reconciled the approved target, verified prototype, tested behavior, defects, planned components, prohibited capabilities, and checkpoint status after TRL-R1-001 |
