# ALSAKKAF HOLDING GROUP

# TRL-R1-CONTRACT-001 - Trading Research Lab Release 1 Contract

> "ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING - NO PROFIT CLAIMS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-R1-CONTRACT-001 |
| Title | Trading Research Lab Release 1 Contract |
| Status | IMPLEMENTED, EVIDENCE-VALIDATED AND FOUNDER-ACCEPTED AS A PAPER/RESEARCH BASELINE |
| Version | 1.3 |
| Original Date | 2026-07-24 |
| Last Validated | 2026-07-26 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Reviewer | ChatGPT acting as Founder/CTO strategic partner |
| Founder Authority | Abdulrahman Yaseen Alsakkaf accepted the Release 1 technical paper/research baseline only; no strategy, distribution or execution capability is approved |
| Project | PRJ-017 - ALSAKKAF Trading Research Lab |
| Completed Documentation Checkpoint | TRL-R1-005 — COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT |

---

# 1. Document ID and Title

**TRL-R1-CONTRACT-001 - Trading Research Lab Release 1 Contract**

# 2. Status

**IMPLEMENTED, EVIDENCE-VALIDATED AND FOUNDER-ACCEPTED AS A PAPER/RESEARCH BASELINE.**

Release 1 meets this contract's scoped engineering definition at committed HEAD `4b99789`. Contract control continues after implementation: later documentation or software may not silently weaken this boundary or reinterpret technical completion as authority for live use.

# 3. Owner and Authority

Abdulrahman Yaseen Alsakkaf is Owner, Founder and final authority. Implementation completion occurred through commits `05f7ba9` and `4b99789`. Technical evidence includes 132 passing direct tests, the same 132 tests passing through discovery and the deterministic synthetic rehearsal. Those commits and tests did not automatically create Founder acceptance.

Founder acceptance occurred on 2026-07-26 and is limited to the completed technical paper/research baseline. The exact decision is:

> “I, Abdulrahman Yaseen Alsakkaf, formally accept PRJ-017 Release 1 as a completed technical paper/research baseline. This acceptance does not approve SMA-001 or any strategy for investment use, does not validate profitability, and does not authorize customer distribution, investment advice, broker connectivity, automated execution, live trading, customer funds, regulatory status, or Release 2 implementation.”

**TRL-R1-005 — COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT.** Completed by the TRL-R1-005 documentation-only closeout commit; Git history is the authoritative commit reference.

TRL-R1-005 authorizes only its own four-document closeout commit. It authorizes no code change, customer distribution, Release 2 implementation, broker connectivity, assisted execution, automated execution, live trading, investment advice, customer funds, payment handling, or regulatory claim.

TRL-R1-004 remains the latest implemented runtime/kernel checkpoint. TRL-R1-005 is the completed documentation, Founder-acceptance, and Release 1 closeout checkpoint. TRL-R2-001 remains proposed, unimplemented, and unauthorized. TRL-R2-001 may begin only after separate explicit Founder authorization; closing TRL-R1-005 does not provide that authorization.

# 4. Historical Purpose Retained

This contract was created under TRL-R1-002 to convert the deficiencies found by the TRL-R1-001 read-only audit into a narrow, testable requirement for a causal, deterministic, single-instrument research kernel. That purpose remains controlling.

The contract separates engineering conformance from research, investment, legal and commercial conclusions. It never authorizes live data, brokerage access, credential use, customer funds, order placement or real-money use.

# 5. Authoritative Checkpoint and Commit History

| Checkpoint | Status | Commit evidence |
|------------|--------|-----------------|
| TRL-R1-001 | Completed read-only baseline audit | Historical audit; no implementation commit |
| TRL-R1-002 | Completed Release 1 documentation contract | `bb3af4e` - `Document PRJ-017 Release 1 contract` |
| TRL-R1-003 | Completed validated causal single-instrument research kernel | `05f7ba9` - `Implement TRL-R1-003 causal research kernel` |
| TRL-R1-004 | Latest implemented runtime/kernel checkpoint: completed behavior-preserving modular kernel refactor | `4b99789` - `Refactor TRL-R1 kernel into focused modules` |
| TRL-R1-005 | COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT | Completed by the TRL-R1-005 documentation-only closeout commit; Git history is the authoritative commit reference. |

The commits establish implementation lineage, not profitability, market realism, production readiness, regulatory approval or live-trading safety.

# 6. Historical Baseline and Superseded Findings

TRL-R1-001 recorded 12 narrow passing tests, five unclosed-file `ResourceWarning` events, regime-state signals, same-close fills, no marked open-position accounting, realized-only drawdown, absent costs, caller-weakenable nominal limits, incomplete outcomes/reason codes and implicit terminal handling.

TRL-R1-003 corrected those scoped kernel findings with direct tests. TRL-R1-004 separated the kernel into focused modules while preserving behavior. The following findings were not "erased": multi-instrument portfolios, realistic market costs, forward simulation, governed strategy workflows, independent Risk Guardian, adapters, user interface, packaging and live execution remain limited, deferred or prohibited.

# 7. Release 1 Objectives and Inclusions

Release 1 implements:

- Strict exact-type validation of one instrument and one ordered OHLCV series.
- One declarative, versioned, long-only SMA crossing research family.
- Genuine entry and exit transitions without repeated signals in one regime.
- Signal calculation through close `t` and hypothetical execution at next validated bar open.
- Cash, position, realized P&L, unrealized P&L and marked equity on every validated bar.
- Explicit open-terminal-position handling without an invented final liquidation.
- Fixed deterministic commission and adverse slippage assumptions.
- System-owned position-size and drawdown safety limits that callers may only tighten.
- Explicit `NO_TRADE`, `BLOCKED`, `HALT`, `NO_FILL` and hypothetical-fill outcomes with stable reason codes.
- Deterministic canonicalization, hashes, engine-source provenance and run identity.
- Deterministic paper-only Markdown reporting.
- 132 behavior-level tests.

# 8. Release 1 Exclusions and Remaining Limitations

- Release 1 is single-instrument, long-only and unlevered.
- It supports only the declared SMA research family; FIB-001 is not specified or implemented.
- It is a historical in-memory replay, not a persistent forward paper simulator.
- Its tracked demonstration data is synthetic.
- Its fixed commission and slippage model is simplified and deterministic, not market-realistic.
- It does not implement multi-asset portfolios, Strategy Vault automation, five-agent orchestration, market/news adapters, local AI/Gemma, a dashboard, packaging, accounts or subscriptions.
- It has no broker/platform adapter, credential store, network dependency, external-order path or live-trading capability.
- It provides no strategy approval, investment advice, research-validity conclusion or profitability evidence.

# 9. Deterministic-Core Rule

All numerical and state-changing Release 1 behavior is deterministic code. Given identical validated input, engine source, strategy definition, starting state, system limits, execution assumptions and cost constants, the kernel returns identical canonical results.

The deterministic core owns validation, stable SMA calculations, crossing events, signal scheduling, hypothetical fills, position sizing, cash, costs, accounting, marked equity, drawdown, hard-risk decisions, outcomes, reason codes and provenance. No AI, Manager, data pack or strategy file may execute code or overwrite these calculations or their audit record.

# 10. Input-Data Contract

Release 1 accepts exactly one instrument with a non-empty pack identifier, symbol, supported asset class, declared source, data-quality note and non-empty OHLCV series. Each bar requires an exact built-in structure, parseable timestamp, finite numeric OHLCV values, positive prices, non-negative volume, valid high/low relationships and strictly increasing unique timestamps.

Invalid structure or content is rejected before evaluation with a stable reason code. The kernel does not silently sort, deduplicate, repair, forward-fill or infer input. Multiple instruments are rejected; timestamp-aligned portfolios remain deferred.

# 11. Causal Signal-and-Execution Contract

For integer periods `1 <= fast < slow`:

- Entry occurs only when the prior completed relationship is `fast_SMA <= slow_SMA` and the current completed relationship is `fast_SMA > slow_SMA`.
- Exit occurs only when the prior completed relationship is `fast_SMA >= slow_SMA` and the current completed relationship is `fast_SMA < slow_SMA`.
- Continuing regimes do not create repeated crossing events.
- Insufficient history yields an explicit no-trade result.

The signal at bar `t` may use data only through its close. It cannot fill at that known close. A hypothetical action becomes eligible at next chronological validated bar `t+1`; the reference is its open and fixed adverse slippage is applied. If no next bar exists, there is no fill. The next-bar open cannot influence the signal at `t`.

# 12. Position, Accounting and Terminal Contract

Release 1 starts with 100.0 research units, is long-only and permits at most one open position. Fractional units are a deterministic research convention. Entry cash decreases by filled notional plus commission; exit cash increases by proceeds minus commission.

Every accounting row records cash, units, position value, realized/unrealized P&L, cumulative costs, total marked equity, high-water mark and drawdown. Total equity equals cash plus position value; drawdown uses marked equity.

An open position at the final validated bar remains open, is marked to the final close and is reported with `OPEN_TERMINAL_POSITION`. The engine does not invent a final fill. This is terminal research accounting, not an external position or real liquidation instruction.

# 13. Transaction-Cost Contract

| Component | Release 1 assumption |
|-----------|----------------------|
| Commission | 5 basis points of filled notional on entry and exit |
| Slippage | 5 basis points adverse on each hypothetical fill |
| Buy fill | Next-bar open multiplied by `1.0005` |
| Sell fill | Next-bar open multiplied by `0.9995` |
| Separate spread | Zero; adverse slippage is the execution-price allowance |
| Minimum fee, taxes, financing, borrow and venue fees | Zero/unsupported and explicitly bounded to Release 1 |

Commission is an explicit cash cost. The model is a deterministic engineering baseline. It is not a claim about an actual instrument, venue, broker, liquidity, latency, spread, market impact or market condition.

# 14. Hard-Risk-Control Contract

Release 1 system limits are a maximum gross position allocation of 5% of marked equity, one open position, no leverage, no increase to a losing position and a -15% marked-equity drawdown halt. A strategy or caller may request a stricter policy but may not raise or weaken the system boundary.

Invalid override attempts are blocked and audited. Drawdown halts block new entries; causally eligible risk-reducing exits remain permitted. Release 1 authorizes no automatic liquidation or real-world action. A future independent Risk Guardian may veto but may never weaken these foundations.

# 15. Outcome and Reason-Code Contract

The kernel provides explicit outcome classes for scheduled signals, hypothetical fills, no-trade cases, blocks, halts and no-fill cases. Stable reasons include invalid input, invalid strategy parameters, position limit, drawdown halt, override attempts, increase-to-loser, insufficient history, no crossing, already positioned, no open position, end of data and terminal position.

Human-readable explanations supplement rather than replace stable codes. Empty trades alone never communicate the whole result.

# 16. Reproducibility and Audit Contract

Each result records project/release/checkpoint identity, engine name/version/source digest and manifest, strategy identity/version/parameters/hash, input pack/hash, configuration hash, validation, starting state, execution/cost/terminal assumptions, effective risk limits, stable run ID and ordered events, decisions, fills, trades and accounting rows.

Canonical results do not depend on dictionary order, locale, wall-clock time, network state or randomness. Deterministic replay is an engineering property; it does not predict real-market outcomes.

# 17. Strategy Identity and Approval Boundary

Release 1 evaluates a declarative SMA-001 identity/version and records its canonical definition. Any changed signal, parameter, fill, cost, accounting or risk rule must remain attributable to a changed definition/version.

No strategy is Founder-approved for real trading. Technical completion does not constitute strategy approval, investment advice, regulatory approval, commercial-release approval or authorization for assisted or automated execution.

# 18. Final Validation Evidence

Evidence was collected on 2026-07-25 at committed HEAD `4b99789` with `PYTHONDONTWRITEBYTECODE=1` and warnings treated as errors.

## 18.1 Test evidence reference E1

```text
python -B -W error 09_AI_Systems/02_Tools/Trading_Lab/test_trading_lab.py
Ran 132 tests
OK

python -B -W error -m unittest discover -s 09_AI_Systems/02_Tools/Trading_Lab -p 'test*.py'
Ran 132 tests
OK
```

Warnings: zero. Tests are behavior-level engineering evidence, not research validity or performance evidence.

## 18.2 Synthetic rehearsal evidence reference E2

The committed `TRL-PACK-DEMO.json` pack and the specified SMA-001 version 1.0.0 strategy (`fast=5`, `slow=20`, `paper_size_pct=5.0`, `symbol=DEMO-EQ-A`) were run twice in memory from independent deep copies with `risk_policy=None`. No `--demo` invocation or saved report was used.

| Field | Value |
|-------|-------|
| Run ID | `TRL-RUN-6922AEA31AE2630B4DA1` |
| Input-data hash | `6cdbca208cd1029b90e5ed3494ab05a3b7042d224ed01293373fc173a85aee56` |
| Configuration hash | `3f4c513f275ca034af9fd2f4bbcb4ec382c361969d7706fbb6fb6d26fd26bbbd` |
| Strategy-definition hash | `e27bd45914df7d9d7c807b73e012b51a45dc5c844f39e22132c48078070e3955` |
| Engine-source digest | `f9f555d37e0820c39eb2afe1156fca4912d255debc23c7ab27c6111c31da3952` |
| Outcome / reason | `HYPOTHETICAL_FILL` / `OPEN_TERMINAL_POSITION` |
| Decisions / fills / trades / accounting rows | 2 / 1 / 0 / 60 |
| Final cash / marked equity | 94.9975 / 100.22673707083118 research units |
| Realized / unrealized P&L | 0.0 / 0.2267370708311804 research units |
| Commission / slippage | 0.0025 / 0.002498750624687196 research units |
| Maximum drawdown | -0.03237704819428881% |
| Terminal status | Open; marked to market and not liquidated |
| Determinism | PASS - both complete results identical |
| Accounting reconciliation | PASS - every row and both final states reconciled |

The engine-source manifest is `trading_lab.py` plus `trading_lab_core/__init__.py`, `canonical.py`, `constants.py`, `execution.py`, `reporting.py`, `risk.py`, `strategy.py` and `validation.py`, each at its repository-relative Trading Lab path.

## 18.3 Boundary inspection reference E3

The 132-test suite includes direct checks that the CLI/reporting boundary remains paper-only, modules use only the local standard library, and execution has no network, AI, broker, credential or external-order dependency. This is a scoped negative-surface check, not a security certification.

# 19. Release 1 Conformance Matrix

| Contract requirement | Implemented | Tested | Evidence reference | Remaining limitation |
|----------------------|-------------|--------|--------------------|----------------------|
| Exact single-instrument input validation | Yes | Yes | E1: input-validation classes | Multi-instrument portfolios are rejected, not supported. |
| Genuine transition-only SMA crossings | Yes | Yes | E1: SMA signal tests | Only SMA long-only research family. |
| Causal close-`t` signal and next-open fill | Yes | Yes | E1: causal timing and future-prefix tests | Historical bar model is simplified. |
| No fill at end of data | Yes | Yes | E1: final-bar no-fill test | No forward pending-order service. |
| Per-bar cash and marked accounting | Yes | Yes | E1 and E2 reconciliation | Research units and fractional units are not broker semantics. |
| Realized and unrealized P&L | Yes | Yes | E1 and E2 | Synthetic demonstration does not validate performance. |
| Marked drawdown and halt | Yes | Yes | E1: drawdown/risk tests | One position; no portfolio risk. |
| Explicit terminal open position | Yes | Yes | E1 and E2 | No forced liquidation or external close. |
| Deterministic commission and slippage | Yes | Yes | E1 and E2 | Fixed model is not market-realistic. |
| System-owned hard limits; stricter caller policies only | Yes | Yes | E1: risk outcome tests | No independent Risk Guardian service. |
| Block increase to losing position | Yes | Yes | E1: martingale/increase test | Long-only, single-position boundary. |
| Explicit outcomes and stable reasons | Yes | Yes | E1 and E2 | Human/product explainability layer is planned. |
| Canonical hashes and deterministic replay | Yes | Yes | E1 and E2 | Determinism does not predict market results. |
| Atomic engine-source digest and manifest | Yes | Yes | E1 and E2 | Provenance covers the Release 1 engine bundle, not future apps/services. |
| Paper-only reporting and CLI | Yes | Yes | E1/E3 | No forward paper application or dashboard. |
| No broker, credential, network or external-order surface | Yes, absent by design | Yes | E1/E3 | Negative evidence is not a security certification. |
| Inputs remain unmodified and no artifact is required | Yes | Yes | E1 and E2 | Saved reports remain optional paper-only outputs outside this rehearsal. |
| Complete Release 1 suite passes without warnings | Yes | Yes | E1 | Test passage is not production, legal or strategy approval. |

# 20. Paper-Only Operating Boundary

Every order, fill, position, cash balance, P&L value and equity value is hypothetical research data. Release 1 has no authority or interface to hold or move money; connect to a broker, venue, platform or data vendor; store or use credentials; place, route, amend or cancel an external order; promote paper configuration to live use; or act autonomously on a market.

No customer funds authority exists. No broker or credential authority exists. No customer distribution or payment authority exists. Any future capability requires a separately scoped and approved checkpoint.

# 21. Performance and Marketing Boundary

Tracked and rehearsed results are synthetic and hypothetical. They are not actual trading, evidence of future returns, an investment recommendation or proof of profitability. No output may promise or guarantee performance or present a deterministic demonstration as realistic market execution.

A disclaimer cannot cure a misleading claim, chart, comparison or omission. "At your own risk" language cannot eliminate operator, developer, platform or regulatory responsibility.

The authoritative implemented and tested Release 1 generated-report wording is:

- Primary disclaimer: **ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING - NO PROFIT CLAIMS**
- Performance disclaimer: **Hypothetical research results from paper-only processing; they do not represent actual trading, predict future returns, or authorize a trade.**
- Generated Markdown label: **PAPER/RESEARCH ONLY**

These strings are the current internal/generated output contract. Current Release 1 output is not approved for public or customer distribution.

**PLANNED - NOT IMPLEMENTED:** Future customer-facing product disclosures are distinct from the current generated-report wording. Future packaging may add jurisdiction-specific disclosures only after legal and regulatory review. "At your own risk" wording must not be described as eliminating operator, developer, platform or regulatory responsibility.

# 22. Definition of Release 1 Done

Release 1 is technically done because the included behaviors are committed, the exclusions remain absent, the contract behaviors have direct tests, both required 132-test invocations pass without warnings, the committed rehearsal is deterministic and accounting-reconciled, and source provenance identifies the committed engine bundle.

Founder acceptance was separately created by the explicit 2026-07-26 decision above, not by implementation commits, tests or rehearsal evidence. It accepts only the technical paper/research baseline.

Technical completion alone does not constitute:

- Founder approval of a strategy.
- Investment advice or research-validity approval.
- Regulatory or legal approval.
- Commercial-release or customer-distribution approval.
- Production or operational readiness.
- Authorization for broker access, assisted execution or automated execution.

# 23. Post-Release Roadmap Boundary

The separate portable-product charter proposes TRL-R2-001 through TRL-R2-008, TRL-R3, TRL-R4 and TRL-R5. No roadmap item is implemented or authorized by this contract. Release 1 remains the paper/research foundation until a separately approved checkpoint changes an expressly identified boundary.

The next proposed checkpoint is **TRL-R2-001 — PORTABLE APPLICATION FOUNDATION**. TRL-R2-001 remains proposed, unimplemented, and unauthorized. It may begin only after separate explicit Founder authorization; roadmap inclusion, Founder acceptance of Release 1, and closing TRL-R1-005 do not provide that authorization.

# 24. Deferred Governance Reconciliation

Reconciliation of `Project_Register.md` and `Knowledge_Register.md` remains intentionally deferred because the separate main working directory previously contained unrelated changes. This checkpoint does not authorize editing, resetting, cleaning, stashing, merging, rebasing or otherwise disturbing those registers or that working directory.

# 25. Documentation Review Resolution

- P2 Founder-acceptance finding: Resolved by the explicit 2026-07-26 Founder decision.
- P2 disclaimer-alignment finding: Resolved by retaining the implemented Release 1 strings as the current output contract and marking future customer wording as planned.
- P2 TRL-R1-005 lifecycle finding: Resolved by making this documentation-only closeout commit the checkpoint’s completion event while preserving all no-code, no-distribution, no-execution, and no-Release-2 boundaries.

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-24 | Initial Release 1 contract created under TRL-R1-002 from the TRL-R1-001 audited baseline. |
| 1.1 | 2026-07-25 | Recorded TRL-R1-003 implementation, TRL-R1-004 modularization, final test/rehearsal evidence, conformance matrix, retained limitations and paper-only technical closeout under TRL-R1-005. |
| 1.2 | 2026-07-26 | Recorded explicit Founder acceptance, corrected the Owner's legal name, aligned current generated wording with planned future disclosures and closed the two P2 documentation findings. |
| 1.3 | 2026-07-26 | Made the TRL-R1-005 documentation-only closeout commit the checkpoint completion event and preserved the separate Release 2 authorization boundary. |
