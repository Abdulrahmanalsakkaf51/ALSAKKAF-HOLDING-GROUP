# ALSAKKAF HOLDING GROUP

# TRL-R1-CONTRACT-001 — Trading Research Lab Release 1 Contract

> "ARCHITECTURE DEMONSTRATION ONLY — NOT FINANCIAL ADVICE — NO LIVE TRADING — NO PROFIT CLAIMS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-R1-CONTRACT-001 |
| Title | Trading Research Lab Release 1 Contract |
| Status | CONTROLLED CONTRACT — RELEASE 1 NOT YET IMPLEMENTED |
| Version | 1.0 |
| Date | 2026-07-24 |
| Owner | Abdulrahman Khalid Alsakkaf |
| Reviewer | ChatGPT acting as Founder/CTO strategic partner |
| Founder Authority | Abdulrahman Khalid Alsakkaf is final authority; this contract authorizes documentation only under TRL-R1-002 |
| Project | PRJ-017 — ALSAKKAF Trading Research Lab |
| Active Checkpoint | TRL-R1-002 — Baseline Reconciliation and Release 1 Contract |
| Proposed Engineering Checkpoint | TRL-R1-003 — Validated Causal Single-Instrument Research Kernel |

---

# 1. Document ID and Title

**TRL-R1-CONTRACT-001 — Trading Research Lab Release 1 Contract**

---

# 2. Status

**CONTROLLED CONTRACT — RELEASE 1 NOT YET IMPLEMENTED.** TRL-R1-002 authorizes this documentation only. Contract changes require documented review; implementation may not silently diverge from the approved contract.

---

# 3. Owner

Abdulrahman Khalid Alsakkaf.

---

# 4. Reviewer

ChatGPT acting as Founder/CTO strategic partner.

---

# 5. Founder Authority

Abdulrahman Khalid Alsakkaf is Founder and final authority. This contract approves no strategy and does not authorize engineering, trading, or any broader checkpoint.

---

# 6. Purpose

This contract defines the narrow, testable boundary for Release 1 of the Trading Research Lab. It reconciles the verified demo baseline with the requirements for a causal, deterministic, single-instrument research kernel.

This document does not authorize implementation, live data, brokerage access, order placement, or real-money use. Engineering may begin only through a separately authorized checkpoint.

---

# 7. Verified Baseline as of 2026-07-24

TRL-R1-001 verified that:

- A deterministic local demo prototype exists.
- Twelve narrow `unittest` tests pass.
- Five `ResourceWarning` events occur from unclosed test file handles.
- The tests do not establish research validity, profitability, production readiness, or complete architectural compliance.
- Current SMA output identifies a regime, not a genuine crossing event.
- Signals use close `t` and fill at that same close, creating same-bar/look-ahead execution bias.
- Open-position profit and loss is not marked to market; drawdown is realized-only and may be materially understated.
- Multi-instrument data is aligned by list index rather than timestamp.
- Transaction costs, commission, spread, and slippage are absent.
- Caller-controlled risk policy can weaken nominal hard limits.
- Explicit `NO TRADE` outcomes and stable reason codes are absent.
- There is no governed SMA-001 strategy record. FIB-001 is not specified or implemented.
- Strategy Registry, TRL Strategy Vault, independent Risk Guardian, market/news adapters, forward paper simulator, Founder dashboard, local AI, and Gemma evaluation are absent.
- The five-agent research workflow is documented only.
- No broker, credential, network, external-order, or live-trading capability exists.
- Existing tracked data and reports are synthetic/demo-only and hypothetical.
- The audited worktree was clean after the audit.

Current demo results cannot support investment decisions, real-money trades, performance claims, or profitability claims.

---

# 8. Release 1 Objectives

Release 1 will provide a research kernel that is:

- Strictly single-instrument.
- Deterministic and reproducible.
- Causal from data through signal and hypothetical fill.
- Correctly marked to market on every validated bar.
- Explicit about transaction costs, terminal positions, blocked actions, and `NO TRADE` outcomes.
- Protected by system-owned hard-risk maxima that callers, strategies, managers, and AI components cannot weaken.
- Supported by tests that directly demonstrate each contracted behavior.

Release 1 is an engineering-quality research baseline, not evidence that a strategy is valid or profitable.

---

# 9. Release 1 Inclusions

- Strict validation of one instrument and one ordered OHLCV series.
- A declarative, versioned, long-only SMA research rule.
- Genuine SMA entry and exit crossing events.
- Signal calculation after close `t` using information available through `t` only.
- Explicit hypothetical execution at the next validated bar open.
- Cash, position, realized profit and loss, unrealized profit and loss, and mark-to-market equity on every bar.
- Explicit handling of an open terminal position.
- Fixed deterministic Release 1 commission and slippage assumptions.
- System-owned position-size and drawdown safety maxima.
- Explicit `NO TRADE`, blocked, halt, and no-fill reason codes.
- Reproducibility and audit metadata.
- Expanded unit and integration tests using synthetic fixtures.

---

# 10. Release 1 Exclusions

- FIB-001.
- Multi-asset or multi-instrument portfolios.
- Strategy Vault automation.
- Automated Strategy Registry workflows beyond the minimum immutable strategy identity recorded in results.
- Five-agent research workflow.
- News or market adapters.
- Local AI or Gemma.
- Founder or operational dashboards.
- Broker or platform adapters.
- Credentials, networks, external orders, live data, or live trading.
- Real-money trading, customer funds, leverage, short selling, derivatives, and automatic paper-to-live promotion.
- Claims of strategy approval, research validity, production readiness, or proven profitability.

These exclusions may remain in the approved long-term architecture, but they are outside Release 1 and TRL-R1-003.

---

# 11. Deterministic-Core Rule

All numerical and state-changing behavior must be implemented in deterministic code. Given identical validated input bytes, engine version, strategy identity, parameters, starting state, risk constants, execution assumptions, and cost constants, the kernel must return identical canonical results.

The deterministic core owns:

- Validation.
- SMA calculation and crossing-event detection.
- Signal scheduling and hypothetical fills.
- Position sizing, cash, costs, and accounting.
- Mark-to-market equity and drawdown.
- Hard-risk enforcement.
- Outcome and reason-code assignment.
- Result metadata and hashes.

No AI or Manager component may alter these calculations or overwrite their audit record. Release 1 will not execute code supplied inside a strategy or data file.

---

# 12. Input-Data Contract

Release 1 accepts exactly one instrument. The input must contain:

- A non-empty pack identifier.
- One non-empty symbol and one declared asset class.
- A non-empty OHLCV series.
- For every bar: a parseable timestamp, finite numeric `open`, `high`, `low`, and `close`, plus finite non-negative `volume`.
- Strictly increasing, unique timestamps.
- Positive prices.
- `high >= max(open, close)` and `low <= min(open, close)`.
- `high >= low`.
- A data-source identifier and a data-quality note, even for synthetic data.

The whole run must be rejected before strategy evaluation if the pack contains zero or multiple instruments, missing fields, booleans in numeric fields, non-finite values, duplicate or unordered timestamps, invalid price relationships, or unsupported types. Rejection must return a stable blocked reason code and must not silently repair, sort, deduplicate, forward-fill, or infer values.

Release 1 has no multi-instrument alignment behavior. Timestamp alignment is deferred until a separately governed multi-asset release.

---

# 13. Causal Signal-and-Execution Contract

For configured integer periods where `1 <= fast < slow`:

- An entry event occurs only when the prior completed bar has `fast_SMA <= slow_SMA` and bar `t` has `fast_SMA > slow_SMA`.
- An exit event occurs only when the prior completed bar has `fast_SMA >= slow_SMA` and bar `t` has `fast_SMA < slow_SMA`.
- A continuing above/below regime is not a new crossing event.
- Insufficient history produces `NO TRADE`, not an inferred signal.

The causal sequence is fixed:

1. Bar `t` closes and becomes available.
2. The signal is calculated from validated data at or before `t`.
3. A signal calculated with bar `t` information cannot fill at bar `t`’s already-known close.
4. The hypothetical order becomes eligible at the next chronological validated bar, `t+1`.
5. The unadjusted Release 1 reference price is the `open` of bar `t+1`.
6. The deterministic adverse slippage rule in Section 15 produces the hypothetical fill price.
7. Bar `t+1` data, including its open, may determine the fill but may not influence the signal at `t`.
8. If `t+1` does not exist or is invalid, no fill occurs and the result records `NO_FILL_END_OF_DATA` or the applicable validation code.

Every result must record `signal_information_cutoff=BAR_CLOSE_T`, `execution_bar=NEXT_VALIDATED_BAR`, `reference_price=NEXT_BAR_OPEN`, and the applied cost/slippage assumptions.

---

# 14. Position, Cash, and Mark-to-Market Accounting Contract

Release 1 is long-only, unlevered, and permits at most one open position in its single instrument.

- Starting cash is a positive configured research value and must be recorded. The default demonstration base is `100.0` units, not real currency.
- The entry target gross notional equals the lower of the strategy-requested allocation and the 5% system maximum, multiplied by mark-to-market equity at signal close `t`.
- Fractional units are permitted for deterministic research accounting.
- At entry, cash decreases by filled notional plus commission.
- At exit, cash increases by filled proceeds minus commission.
- Realized and unrealized profit and loss must be reported separately.
- On every validated bar, position value equals open units multiplied by that bar’s close; total equity equals cash plus position value.
- High-water mark and drawdown must use total mark-to-market equity, not realized cash alone.
- Cash, units, position value, realized profit and loss, unrealized profit and loss, costs, total equity, high-water mark, and drawdown must reconcile for every bar.

Terminal-position policy is fixed for Release 1: an open position remains open and is marked to the final validated close. The engine must not invent a forced final fill. The result must report the position, unrealized profit and loss, and `terminal_position_policy=MARK_TO_MARKET_OPEN`. An exit signal on the final bar cannot fill and must record `NO_FILL_END_OF_DATA`.

---

# 15. Transaction-Cost Contract

Release 1 uses a deliberately simple, fixed, deterministic research cost model:

| Component | Release 1 assumption |
|-----------|----------------------|
| Commission | 5 basis points of filled notional on every entry and exit |
| Slippage | 5 basis points adverse to the position on every fill |
| Buy fill | Next-bar open multiplied by `1.0005` |
| Sell fill | Next-bar open multiplied by `0.9995` |
| Separate spread charge | 0 basis points; the fixed adverse slippage adjustment is the Release 1 execution-price allowance |
| Minimum fee | None |
| Taxes, financing, borrow, and venue fees | 0 in Release 1; unsupported and explicitly recorded |

Commission is an explicit cash cost and must not be hidden inside price. All constants and actual applied amounts must appear in result metadata and accounting rows.

This simplified model is a deterministic engineering baseline, not a claim that it represents any real instrument, venue, broker, or market condition. More realistic instrument-specific cost models remain planned beyond Release 1.

---

# 16. Hard-Risk-Control Contract

Release 1 system hard maxima are:

- Maximum gross position allocation: 5% of current mark-to-market equity.
- Maximum open positions: one, because Release 1 is single-instrument.
- Leverage: none.
- Increase to a losing open position: prohibited.
- Drawdown halt: -15% from the mark-to-market high-water mark.

Ownership rules are mandatory:

- Strategy input may request a lower position or drawdown limit.
- Strategy input may never raise a system maximum or weaken a system halt.
- Public caller arguments may not override hard maxima with weaker values.
- Tests must exercise hard limits through controlled fixtures or internal test seams that cannot exist as a public weakening path.
- Manager and AI components may not override hard limits.
- A future Risk Guardian may veto an action but may not weaken a control.
- Any invalid attempt to raise or bypass a limit must be rejected and audited.

When the mark-to-market drawdown halt is reached, new entries are blocked. Risk-reducing exits remain eligible under the causal next-bar rule. Release 1 does not authorize automatic liquidation or live action.

---

# 17. NO TRADE and Blocked-Reason Contract

Every evaluated bar/run must produce an explicit research outcome rather than relying on an empty trade list. Allowed outcome classes are:

- `SIGNAL_SCHEDULED`
- `HYPOTHETICAL_FILL`
- `NO_TRADE`
- `BLOCKED`
- `HALT`
- `NO_FILL`

Release 1 must define a stable, documented enumeration including at least:

- `NO_TRADE_INSUFFICIENT_HISTORY`
- `NO_TRADE_NO_CROSS`
- `NO_TRADE_ALREADY_POSITIONED`
- `NO_TRADE_NO_OPEN_POSITION`
- `BLOCKED_INVALID_INPUT`
- `BLOCKED_INVALID_STRATEGY_PARAMETERS`
- `BLOCKED_POSITION_LIMIT`
- `BLOCKED_DRAWDOWN_HALT`
- `BLOCKED_RISK_OVERRIDE_ATTEMPT`
- `BLOCKED_INCREASE_TO_LOSER`
- `NO_FILL_END_OF_DATA`

Each record must include outcome class, reason code, timestamp, strategy identity, and relevant non-sensitive context. Human-readable text may supplement but must not replace the stable code.

---

# 18. Reproducibility and Audit-Metadata Contract

Every result must record at least:

- Unique run identifier.
- Project, release, and checkpoint identifiers.
- Engine name, semantic version, and source revision identifier.
- Strategy identifier, version, parameters, and canonical strategy-definition hash.
- Input pack identifier and canonical input-data hash.
- Validation outcome and reason codes.
- Starting cash and accounting currency/unit label.
- Signal timing, next-bar reference-price, slippage, commission, and terminal-position assumptions.
- System hard limits and any stricter strategy requests.
- Run start/end timestamps and deterministic timezone convention.
- Output schema version.
- Ordered outcome events, hypothetical fills, accounting rows, and their stable identifiers.

Hashes must be computed from documented canonical serialization. Generated wall-clock timestamps may identify the run but must not change deterministic financial outputs. Results must not depend on dictionary iteration order, locale, current date, network state, or unseeded randomness.

---

# 19. Strategy Identity and Versioning Requirements

Release 1 may evaluate only a declarative strategy definition with an immutable identity and version in the result. The minimum record includes:

- Strategy identifier and human-readable name.
- Semantic version.
- Lifecycle status such as `EXPERIMENTAL_RESEARCH_ONLY`.
- Exact fast and slow SMA periods.
- Requested position allocation.
- Entry, exit, timing, cost, risk, and terminal-position rules by reference.
- Canonical definition hash.
- Author and review metadata.
- Explicit statement that Founder approval and profitability validation are absent unless separately evidenced.

No governed SMA-001 record exists at the verified baseline. If TRL-R1-003 creates an SMA-001 research record, its status must be experimental and not Founder-approved. FIB-001 is outside Release 1 and TRL-R1-003.

A changed parameter, signal rule, fill rule, cost rule, accounting rule, or risk rule requires a new strategy or contract version; prior results must remain attributable to their original version.

---

# 20. Testing and Evidence Gates

Release 1 cannot be marked done until tests directly demonstrate:

- Acceptance of valid single-instrument data and rejection of every contracted invalid-data class.
- Strictly ordered unique timestamps and OHLC relationship checks.
- Genuine upward and downward crossing events, including equality boundaries.
- No repeated event during a continuing regime.
- No use of future data in signal calculation.
- Signal at close `t` and hypothetical fill at the next bar open, including gaps.
- No fill when no next bar exists.
- Deterministic commission and adverse slippage on entry and exit.
- Per-bar cash, units, realized/unrealized profit and loss, total equity, high-water mark, and drawdown reconciliation.
- Mark-to-market drawdown halt while a position remains open.
- Explicit terminal open-position handling.
- Strategy requests below system maxima and rejection of attempts to raise/bypass maxima.
- Stable `NO TRADE`, blocked, halt, and no-fill reason codes.
- Identical canonical results and hashes for repeated identical runs.
- No broker, credential, network, external-order, or live-execution surface.

The complete unchanged and expanded test suites must pass with bytecode disabled. Tests must close their file handles; Release 1 validation must have no unexpected warnings. Test names, counts, commands, output, and limitations must be recorded. Passing tests are engineering evidence only and do not prove research validity or profitability.

---

# 21. Paper-Only Operating Boundary

All orders, fills, positions, cash, profit and loss, and equity are hypothetical research records. Release 1 has no authority or interface to:

- Hold or move money.
- Connect to a broker, venue, data vendor, or platform.
- Store or use credentials.
- Place, route, amend, or cancel an external order.
- Promote a paper configuration to live use.
- Act autonomously on a market.

Any future forward paper simulator remains paper-only and requires separate authorization. Any live capability requires a new Founder-governed project decision.

---

# 22. Performance-Claim Prohibition

Current tracked demo results:

- Are synthetic and hypothetical.
- Do not represent actual trading.
- Are not evidence of future returns.
- Must not be used to decide a real-money trade.
- Must not be presented as proven performance.

Release 1 results remain hypothetical even if historical market data is later supplied. No result may be described as validated, profitable, production-ready, investable, or Founder-approved without separate, explicit evidence and authority. Required disclaimers do not cure a misleading headline, chart, comparison, or omission.

---

# 23. Checkpoint Sequence

| Checkpoint | Status | Boundary |
|------------|--------|----------|
| TRL-R1-001 — Trading Foundation Audit | Completed 2026-07-24 | Read-only audit of code, tests, data, reports, and documentation; no implementation change |
| TRL-R1-002 — Baseline Reconciliation and Release 1 Contract | Active documentation checkpoint | Reconcile project/architecture records and create this contract; no code change |
| TRL-R1-003 — Validated Causal Single-Instrument Research Kernel | Proposed next engineering checkpoint | Implement only the narrow scope in Section 23.1 after explicit authorization |
| Later checkpoints | Unscheduled and unauthorized | Require separate scope, evidence, review, and Founder authorization |

No checkpoint automatically authorizes the next one.

## 23.1 Proposed TRL-R1-003 Scope

**TRL-R1-003 — Validated Causal Single-Instrument Research Kernel** is proposed, not started, and not authorized by this contract to begin.

Its future scope includes only:

- Strict single-instrument input validation.
- Deterministic genuine SMA crossing events.
- Signal at close `t`.
- Explicit next-bar execution.
- Per-bar mark-to-market equity.
- Explicit terminal-position handling.
- Fixed deterministic transaction-cost assumptions.
- System-owned non-overridable safety maxima.
- Explicit `NO TRADE` and blocked reason codes.
- Reproducibility metadata.
- Expanded tests.

TRL-R1-003 explicitly excludes:

- FIB-001.
- Multi-asset portfolios.
- Strategy Vault automation.
- Five-agent workflow.
- Local AI.
- Gemma.
- Dashboards.
- Broker or platform adapters.
- Live trading.

---

# 24. Definition of Release 1 Done

Release 1 is done only when all of the following are true:

- Every inclusion in Section 9 is implemented within the authorized code boundary.
- Every exclusion in Section 10 remains absent.
- Contracts in Sections 11 through 19 are implemented and mutually consistent.
- All evidence gates in Section 20 have direct tests and recorded passing results with no unexpected warnings.
- Complete diff review finds no unauthorized capability or unrelated change.
- Synthetic fixtures and reports are clearly labeled hypothetical.
- Documentation describes implemented behavior accurately and retains known limitations.
- An audit can reproduce the same canonical result from the recorded inputs and metadata.
- Founder acceptance is recorded for the Release 1 checkpoint. Technical completion alone does not imply strategy approval, investment approval, or live-trading authority.

---

# 25. Deferred Governance Reconciliation

Reconciliation of `01_Holding_Company/04_Operations/Project_Register.md` and `01_Holding_Company/01_Governance/Knowledge_Register.md` is explicitly deferred. Those registers contain unrelated changes in a separate dirty main working directory and are outside TRL-R1-002 authorization.

This deferral must remain visible until a clean, separately authorized reconciliation is performed. It does not permit this checkpoint to edit, reset, clean, stash, merge, rebase, or otherwise disturb either register or the separate working directory.

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-24 | Initial Release 1 contract created under TRL-R1-002 from the verified TRL-R1-001 baseline |
