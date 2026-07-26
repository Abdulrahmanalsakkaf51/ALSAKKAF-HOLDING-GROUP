# ALSAKKAF HOLDING GROUP

# PRJ-017 - Five-Agent Trading Research Lab

> "ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING - NO PROFIT CLAIMS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-017 |
| Document Type | Project Record |
| Status | IMPLEMENTED, EVIDENCE-VALIDATED AND FOUNDER-ACCEPTED AS A PAPER/RESEARCH BASELINE |
| Completed Documentation Checkpoint | TRL-R1-005 — COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT |
| Version | 1.4 |
| Original Date | 2026-07-14 |
| Last Reconciled | 2026-07-26 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Approved By | Abdulrahman Yaseen Alsakkaf, Founder, for the Release 1 technical paper/research baseline only; no strategy, distribution or execution capability is approved |
| Related System | AOS; Atlas is an optional integration, not a dependency |
| Related Projects | PRJ-011 (Playground trading demo), PRJ-016, STRAT-017 |
| Related Documents | TRL-001; `09_AI_Systems/02_Tools/Trading_Lab/TRL_R1_RELEASE_CONTRACT.md`; `09_AI_Systems/02_Tools/Trading_Lab/TRL_PORTABLE_TRADING_PRODUCT_CHARTER.md` |

---

# 1. Objective and Current Direction

PRJ-017 develops a controlled trading-intelligence product from a deterministic research foundation. Release 1 is implemented, evidence-validated and Founder-accepted as a causal, single-instrument, paper/research-only baseline. The current phase defines a local-first, standalone, portable product without implementing Release 2.

The future product direction includes governed insights, deterministic paper trading and, only after separate technical, security, legal, regulatory and Founder approval gates, possible user-authorized assisted or automated execution. Atlas may be connected through an optional adapter; PRJ-017 must remain usable without Atlas.

Implementation completion and technical evidence alone do not create Founder acceptance. Founder acceptance is recorded separately below and does not establish profitability, market realism, production readiness, regulatory approval, commercial approval, strategy approval or live-trading safety.

# 2. Current Authority Boundary

## 2.1 Implemented and authorized in Release 1

- Local, deterministic, single-instrument research evaluation.
- Strict validated synthetic or supplied OHLCV input.
- One declarative long-only SMA crossing strategy family.
- Causal next-bar hypothetical fills.
- Deterministic costs, positions, accounting, profit and loss, drawdown and terminal handling.
- Stable research outcomes, reason codes, hashes and source provenance.
- Deterministic paper-only Markdown reporting.

## 2.2 Planned or deferred

- A portable application shell, operator interface and Windows package.
- Governed Strategy Registry and Vault.
- Market-data adapters and data-quality services.
- Insights and explainability services.
- Forward paper-trading simulation.
- Independent Risk Guardian and persistent audit ledger.
- Accounts, licensing and subscription services.
- Broker-demo and assisted-execution evaluation.
- Separately governed automated-execution evaluation.
- Five-agent research workflow, local AI, Gemma and dashboards.

These items are not implemented by TRL-R1-005. Roadmap inclusion is not implementation authorization.

## 2.3 Prohibited at the current checkpoint

- Live or external order submission, amendment, cancellation or routing.
- Broker connections, broker credentials or customer credentials.
- Custody, acceptance, storage, movement or control of customer funds.
- Real-money trading, leverage, short selling or derivatives.
- Autonomous execution or automatic paper-to-live promotion.
- Customer distribution or commercial release.
- Profit promises, guaranteed-performance language or claims of proven profitability.
- Claims of market realism, regulatory approval, production readiness or universal PC compatibility.

No live trading is authorized. No customer distribution is authorized. No broker credentials or customer funds are supported. No strategy is Founder-approved for real trading.

# 3. Release 1 Closeout Status

**IMPLEMENTED, EVIDENCE-VALIDATED AND FOUNDER-ACCEPTED AS A PAPER/RESEARCH BASELINE.**

Implementation completion occurred through commits `05f7ba9` and `4b99789`. Technical evidence includes 132 passing direct tests, the same 132 tests passing through discovery and the deterministic synthetic rehearsal. Those commits and tests did not automatically create Founder acceptance.

Founder acceptance occurred on 2026-07-26 and is limited to the completed technical paper/research baseline. The exact decision is:

> “I, Abdulrahman Yaseen Alsakkaf, formally accept PRJ-017 Release 1 as a completed technical paper/research baseline. This acceptance does not approve SMA-001 or any strategy for investment use, does not validate profitability, and does not authorize customer distribution, investment advice, broker connectivity, automated execution, live trading, customer funds, regulatory status, or Release 2 implementation.”

**TRL-R1-005 — COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT.** Completed by the TRL-R1-005 documentation-only closeout commit; Git history is the authoritative commit reference.

TRL-R1-005 authorizes only its own four-document closeout commit. It authorizes no code change, customer distribution, Release 2 implementation, broker connectivity, assisted execution, automated execution, live trading, investment advice, customer funds, payment handling, or regulatory claim.

TRL-R1-004 remains the latest implemented runtime/kernel checkpoint. TRL-R1-005 is the completed documentation, Founder-acceptance, and Release 1 closeout checkpoint. TRL-R2-001 remains proposed, unimplemented, and unauthorized. TRL-R2-001 may begin only after separate explicit Founder authorization; closing TRL-R1-005 does not provide that authorization.

| Classification | Closeout status |
|----------------|-----------------|
| Implemented | Validated causal single-instrument kernel and its compatibility facade, then behavior-preserving modularization. |
| Tested | 132 direct tests and the same 132 tests through discovery passed on 2026-07-25 with `-W error`; zero Python warnings. |
| Demonstrated | The committed synthetic pack and SMA-001 definition produced identical in-memory results across two independent deep-copy runs. |
| Planned | Release 2 portable-product roadmap in the product charter. |
| Deferred | Forward simulation, external data, broader strategies, portfolio support, user accounts, distribution and any execution evaluation. |
| Prohibited | Live trading, external orders, credentials, customer funds, unauthorized distribution and unsupported claims. |

# 4. Authoritative Implementation History

| Checkpoint | Status and evidence |
|------------|---------------------|
| TRL-R1-001 | Read-only baseline audit completed 2026-07-24. It recorded the original narrow prototype, 12 passing tests, five `ResourceWarning` events and material causal, accounting, cost and control limitations. |
| TRL-R1-002 | Release 1 documentation contract. Commit `bb3af4e` - `Document PRJ-017 Release 1 contract`. |
| TRL-R1-003 | Validated causal single-instrument research kernel. Commit `05f7ba9` - `Implement TRL-R1-003 causal research kernel`. |
| TRL-R1-004 | Latest implemented runtime/kernel checkpoint: behavior-preserving modular kernel refactor. Commit `4b99789` - `Refactor TRL-R1 kernel into focused modules`. |
| TRL-R1-005 | COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT. Completed by the TRL-R1-005 documentation-only closeout commit; Git history is the authoritative commit reference. |

These commits evidence scoped implementation history. They do not prove profitability, realistic market execution, production readiness, regulatory approval or live-trading safety.

# 5. Verified Release 1 Evidence

## 5.1 Test evidence

On 2026-07-25 at committed HEAD `4b99789`, with `PYTHONDONTWRITEBYTECODE=1` and Python warnings treated as errors:

- Direct command: 132 tests passed.
- Discovery command: 132 tests passed.
- Python warnings: zero.
- Test boundary: behavior-level engineering evidence for the committed kernel; not investment or performance evidence.

## 5.2 Committed synthetic rehearsal

The committed `sample_data/TRL-PACK-DEMO.json` pack was evaluated twice in memory using independent deep copies, the specified SMA-001 version 1.0.0 parameters and the system-owned risk limits (`risk_policy=None`). The demo CLI, report saving, network and external orders were not used.

| Evidence field | Final committed value |
|----------------|-----------------------|
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
| Terminal position | Open; marked to market and not liquidated |
| Determinism | PASS - complete results were identical across the two independent deep-copy runs |
| Accounting reconciliation | PASS - both runs reconciled cash, position value, equity and cumulative costs on every row and at final state |

Engine-source manifest:

- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab.py`
- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/__init__.py`
- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/canonical.py`
- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/constants.py`
- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/execution.py`
- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/reporting.py`
- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/risk.py`
- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/strategy.py`
- `09_AI_Systems/02_Tools/Trading_Lab/trading_lab_core/validation.py`

The result is synthetic and hypothetical. Its positive marked value is not evidence of profitability or future performance.

# 6. Current Modular Implementation Map

| Path | Implemented responsibility |
|------|----------------------------|
| `trading_lab.py` | Compatibility facade and paper-only CLI. |
| `trading_lab_core/constants.py` | Release identity, constants, reason codes and system limits. |
| `trading_lab_core/canonical.py` | Canonicalization, deterministic hashing, numeric safety and atomic source provenance. |
| `trading_lab_core/validation.py` | Exact-type pack, instrument, OHLCV, timestamp, strategy and policy validation. |
| `trading_lab_core/strategy.py` | Stable SMA calculations and genuine transition-only crossing signals. |
| `trading_lab_core/risk.py` | System-owned limits, stricter policies and risk decisions. |
| `trading_lab_core/execution.py` | Causal fills, costs, positions, accounting, P&L, drawdown and terminal handling. |
| `trading_lab_core/reporting.py` | Deterministic paper-only Markdown reporting. |
| `test_trading_lab.py` | 132 behavior-level tests. |

No module listed in the Release 2 roadmap is represented here as implemented.

# 7. Known Limitations

- Release 1 supports exactly one instrument and one long-only SMA strategy family.
- It replays historical arrays in one call; it is not a forward paper simulator.
- The committed demonstration data is synthetic.
- The fixed commission and slippage model is deliberately simplified and does not claim market realism.
- Fractional units and 100 starting research units are deterministic research conventions, not brokerage behavior.
- There is no Strategy Registry/Vault workflow, independent Risk Guardian service, persistent ledger, portfolio engine, market/news adapter, user interface, installer, authentication or subscription service.
- There is no out-of-sample, walk-forward or live-market validation supporting strategy approval.
- There is no broker adapter, credential store, external-order surface or live execution.
- The five-agent workflow remains a target concept, not an implemented Release 1 capability.

# 8. Target Research Roles

The Manager, News Analyst, Strategy Analyst, Bull Analyst and Bear Analyst roles remain planned research architecture. They are not implemented in Release 1 and may not alter deterministic calculations, hard limits or audit records if later implemented.

# 9. Historical Findings and Corrections

Historical statements are retained here as dated evidence rather than silently erased.

| Historical finding | Current reconciliation |
|--------------------|------------------------|
| On 2026-07-14 the project was design-only with no code. | Superseded on 2026-07-15 by the authorized prototype. |
| TRL-R1-001 found regime-state signals rather than genuine crossings. | Corrected by TRL-R1-003 and covered by transition/equality/no-repeat tests. |
| TRL-R1-001 found same-close fills and look-ahead/same-bar bias. | Corrected by TRL-R1-003 with close-`t` signals and next-valid-bar-open fills. |
| TRL-R1-001 found no mark-to-market open-position accounting and realized-only drawdown. | Corrected by TRL-R1-003 with per-bar marked equity and drawdown. |
| TRL-R1-001 found multi-instrument list-index processing. | Superseded by strict rejection of multi-instrument packs; portfolio alignment remains deferred. |
| TRL-R1-001 found no commission or slippage. | Corrected by the fixed deterministic Release 1 model; realism remains explicitly unclaimed. |
| TRL-R1-001 found caller-weakenable nominal limits. | Corrected by system-owned maxima and rejection of weaker overrides. |
| TRL-R1-001 found absent explicit outcomes, stable reason codes and terminal handling. | Corrected by TRL-R1-003 and directly tested. |
| TRL-R1-001 recorded 12 tests and five `ResourceWarning` events. | Superseded by 132 direct and 132 discovery tests passing with warnings treated as errors and zero warnings. |
| Earlier wording suggested a completed paper portfolio ledger. | Still qualified: Release 1 has historical per-bar accounting, not a forward paper simulator. |

# 10. Portable Product Direction

The controlled product direction is a local-first, standalone trading-intelligence platform that runs independently on a supported personal computer. Its deterministic core remains separate from the user interface. Windows is the first implementation target; macOS and Linux support may be claimed only after separate packaging and testing. "Works on every PC" remains an aspiration, not a current claim.

Default local storage may be used initially. Cloud identity and subscription services are deferred. Atlas remains an optional adapter and must not become a runtime, identity, data, audit or distribution dependency.

# 11. Proposed Roadmap

Release 2 is proposed but not implemented: TRL-R2-001 Portable Application Foundation; TRL-R2-002 Governed Strategy Registry and Vault; TRL-R2-003 Market-Data and Data-Quality Layer; TRL-R2-004 Insights and Explainability Engine; TRL-R2-005 Forward Paper-Trading Simulator; TRL-R2-006 Independent Risk Guardian and Persistent Audit Ledger; TRL-R2-007 Local Operator Dashboard; and TRL-R2-008 Windows Packaging and Closed Paper Alpha.

Later proposals are TRL-R3 Accounts, Licensing and Subscription Services; TRL-R4 Broker-Demo and Assisted-Execution Evaluation; and TRL-R5 separately governed automated-execution evaluation. Roadmap inclusion is not implementation authorization.

The next proposed checkpoint is **TRL-R2-001 — PORTABLE APPLICATION FOUNDATION**. TRL-R2-001 remains proposed, unimplemented, and unauthorized. It may begin only after separate explicit Founder authorization; roadmap inclusion, Founder acceptance of Release 1, and closing TRL-R1-005 do not provide that authorization.

# 12. Project Tasks and Checkpoints

| Task | Current state |
|------|---------------|
| TRL-R1-001 baseline audit | Completed; historical findings retained. |
| TRL-R1-002 Release 1 contract | Completed and committed at `bb3af4e`. |
| TRL-R1-003 causal kernel | Completed and committed at `05f7ba9`. |
| TRL-R1-004 modular refactor | Latest implemented runtime/kernel checkpoint; completed and committed at `4b99789`. |
| TRL-R1-005 Release 1 closeout and product charter | COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT; Git history is the authoritative closeout-commit reference. |
| TRL-R2-001 through TRL-R2-008 | Proposed; not implemented or authorized by this record. |
| TRL-R3 through TRL-R5 | Deferred proposals requiring separate governance. |

# 13. Progress Log

| Date | Update |
|------|--------|
| 2026-07-14 | Project and design architecture created; no code existed at that date. |
| 2026-07-15 | Founder-authorized paper-only prototype added, superseding the design-only status without changing the live-trading prohibition. |
| 2026-07-24 | TRL-R1-001 audited the baseline; TRL-R1-002 established the controlled Release 1 contract. |
| 2026-07-25 | TRL-R1-003 implementation and TRL-R1-004 modularization were verified at `4b99789`; TRL-R1-005 recorded Release 1 closeout evidence and portable-product direction. |
| 2026-07-26 | Abdulrahman Yaseen Alsakkaf explicitly accepted Release 1 as a completed technical paper/research baseline; the acceptance granted no strategy, distribution, execution or Release 2 authority. |

# 14. Deferred Governance Reconciliation

Reconciliation entries in `Project_Register.md` and `Knowledge_Register.md` remain intentionally deferred because the separate main working directory previously contained unrelated changes. TRL-R1-005 does not authorize changes to those registers or that working directory.

# 15. Release 1 Generated-Report Wording and Future Disclosures

The authoritative implemented and tested Release 1 generated-report wording is:

- Primary disclaimer: **ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING - NO PROFIT CLAIMS**
- Performance disclaimer: **Hypothetical research results from paper-only processing; they do not represent actual trading, predict future returns, or authorize a trade.**
- Generated Markdown label: **PAPER/RESEARCH ONLY**

These strings define the current internal/generated output contract. They do not approve Release 1 output for public or customer distribution.

**PLANNED - NOT IMPLEMENTED:** Future customer-facing product wording may add disclosures appropriate to a separately authorized product and jurisdiction, but it must not be treated as current generated-report wording. Jurisdiction-specific disclosures may be added only after legal and regulatory review. Synthetic or historical results must not be presented as actual, realistic, approved or proven performance. "At your own risk" wording does not eliminate operator, developer, platform or regulatory responsibility.

# 16. Documentation Review Resolution

- P2 Founder-acceptance finding: Resolved by the explicit 2026-07-26 Founder decision.
- P2 disclaimer-alignment finding: Resolved by retaining the implemented Release 1 strings as the current output contract and marking future customer wording as planned.
- P2 TRL-R1-005 lifecycle finding: Resolved by making this documentation-only closeout commit the checkpoint’s completion event while preserving all no-code, no-distribution, no-execution, and no-Release-2 boundaries.

# 17. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial design-only project record. |
| 1.1 | 2026-07-24 | Reconciled the TRL-R1-001 audited prototype baseline and opened TRL-R1-002. |
| 1.2 | 2026-07-25 | Recorded Release 1 implementation completion and technical evidence, reconciled superseded findings, and established the portable-product definition phase under TRL-R1-005; Founder acceptance was not yet recorded. |
| 1.3 | 2026-07-26 | Recorded explicit Founder acceptance, corrected the Owner's legal name, aligned the generated-report wording contract and closed the two P2 documentation findings. |
| 1.4 | 2026-07-26 | Made the TRL-R1-005 documentation-only closeout commit the checkpoint completion event and preserved the separate Release 2 authorization boundary. |
