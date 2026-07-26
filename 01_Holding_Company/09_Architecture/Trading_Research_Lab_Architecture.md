# ALSAKKAF HOLDING GROUP

# Trading Research Lab - Architecture

> "ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING - NO PROFIT CLAIMS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-001 |
| Document Type | Current and Target Product Architecture |
| Status | IMPLEMENTED, EVIDENCE-VALIDATED AND FOUNDER-ACCEPTED AS A PAPER/RESEARCH BASELINE |
| Completed Documentation Checkpoint | TRL-R1-005 — COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT |
| Version | 1.5 |
| Original Date | 2026-07-14 |
| Last Reconciled | 2026-07-26 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Founder Authority | Abdulrahman Yaseen Alsakkaf accepted the Release 1 technical paper/research baseline only; future implementation requires a separately authorized checkpoint |
| Related Project | PRJ-017 |
| Related Documents | `09_AI_Systems/02_Tools/Trading_Lab/TRL_R1_RELEASE_CONTRACT.md`; `09_AI_Systems/02_Tools/Trading_Lab/TRL_PORTABLE_TRADING_PRODUCT_CHARTER.md` |

---

# 1. Product Vision

PRJ-017 is intended to become a local-first, standalone trading-intelligence platform. It should operate independently on a supported personal computer, provide governed strategies and explainable market insights, conduct deterministic paper trading and, only after separately approved gates, evaluate user-authorized broker execution.

The product is not an assurance of performance, investment advice, a broker, a custodian or an authorization to trade. Atlas is optional. Release 1 is complete only within its paper/research boundary. Release 2 is proposed and not implemented.

# 2. Currently Implemented Release 1

Release 1 is a deterministic, causal, single-instrument historical research kernel committed through:

- `bb3af4e` - TRL-R1-002 Release 1 documentation contract.
- `05f7ba9` - TRL-R1-003 validated causal single-instrument research kernel.
- `4b99789` - TRL-R1-004 behavior-preserving modular kernel refactor.

At `4b99789`, 132 direct tests and 132 discovery tests pass with Python warnings treated as errors and zero warnings. A two-run independent deep-copy rehearsal of the committed synthetic pack is deterministic and accounting-reconciled. The rehearsal records run `TRL-RUN-6922AEA31AE2630B4DA1` and engine-source digest `f9f555d37e0820c39eb2afe1156fca4912d255debc23c7ab27c6111c31da3952`.

Implemented Release 1 behavior includes strict exact-type validation, genuine SMA crossing events, close-`t` signal timing, next-valid-bar-open hypothetical fills, fixed costs, system-owned risk limits, per-bar marked accounting, terminal open-position handling, stable outcomes/reason codes and reproducibility metadata.

This is behavior-level engineering evidence on synthetic data. It does not prove strategy validity, profitability, market realism, production readiness, regulatory approval or live-trading safety.

## 2.1 Release 1 Governance and Founder Acceptance

Implementation completion occurred through commits `05f7ba9` and `4b99789`. Technical evidence includes 132 passing direct tests, the same 132 tests passing through discovery and the deterministic synthetic rehearsal. Those commits and tests did not automatically create Founder acceptance.

Founder acceptance occurred on 2026-07-26 and is limited to the completed technical paper/research baseline. The exact decision is:

> “I, Abdulrahman Yaseen Alsakkaf, formally accept PRJ-017 Release 1 as a completed technical paper/research baseline. This acceptance does not approve SMA-001 or any strategy for investment use, does not validate profitability, and does not authorize customer distribution, investment advice, broker connectivity, automated execution, live trading, customer funds, regulatory status, or Release 2 implementation.”

Release 1 status is **IMPLEMENTED, EVIDENCE-VALIDATED AND FOUNDER-ACCEPTED AS A PAPER/RESEARCH BASELINE**. **TRL-R1-005 — COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT.** Completed by the TRL-R1-005 documentation-only closeout commit; Git history is the authoritative commit reference.

TRL-R1-005 authorizes only its own four-document closeout commit. It authorizes no code change, customer distribution, Release 2 implementation, broker connectivity, assisted execution, automated execution, live trading, investment advice, customer funds, payment handling, or regulatory claim.

TRL-R1-004 remains the latest implemented runtime/kernel checkpoint. TRL-R1-005 is the completed documentation, Founder-acceptance, and Release 1 closeout checkpoint. TRL-R2-001 remains proposed, unimplemented, and unauthorized. TRL-R2-001 may begin only after separate explicit Founder authorization; closing TRL-R1-005 does not provide that authorization.

# 3. Current Module Map

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

No user interface, installer, persistent database, cloud service, market-data adapter, Strategy Vault, independent Risk Guardian, broker adapter or live execution module is currently implemented.

# 4. Target Portable-Product Architecture

The planned structure separates governed capabilities:

```text
Local Operator Interface
        v
Capability Gate and Mode Controller
        v
Governed Strategy Registry and Vault
        v
Market Data and Data-Quality Boundary
        v
Insights / Forward Paper Simulator
        v
Independent Risk Guardian
        v
Portfolio and Persistent Audit Ledger
        v
Optional adapters: Atlas | cloud identity | broker demo/execution
```

The deterministic core must remain separable from the interface and adapters. Planned layers are architectural targets, not statements of current implementation.

# 5. Operating Modes and Capability Gates

| Mode | Target capability | Current gate |
|------|-------------------|--------------|
| `INSIGHT_MODE` | Strategies, signals, explanations, risk context and research; no order submission. | Planned for Release 2; must distinguish general research from personalized advice and make no profit claims. |
| `PAPER_MODE` | Forward simulated execution without a broker or external order; intended default mode using deterministic risk and accounting foundations. | Planned for Release 2; current Release 1 is historical replay, not forward simulation. |
| `ASSISTED_EXECUTION_MODE` | Prepare a proposed order and require explicit user review and confirmation for each submission. | Disabled until broker-demo, security, legal, regulatory, jurisdiction and Founder gates pass. |
| `AUTOMATED_EXECUTION_MODE` | User-opted execution through the user's own broker account under hard limits, monitoring, emergency stop and audit. | Disabled and prohibited until separately authorized after all required gates. |

Mode selection must never bypass capability gates. "At your own risk" language cannot remove operator, developer, platform or regulatory responsibility, including applicable security, legal, product and consumer-protection obligations.

# 6. Standalone/Atlas Boundary

PRJ-017 must install, start, evaluate supported local data, operate in authorized modes and preserve its local audit evidence without Atlas. Atlas may later provide an optional, versioned connector for approved context or workflow integration.

Atlas must not become a required runtime, identity provider, strategy authority, risk authority, data source, ledger, credential store, update channel or execution dependency. Connector failure must leave the standalone product safe and usable within its authorized local boundary.

# 7. Local and Future Cloud Boundaries

Initial product operation and default storage may be local. Local data must have documented locations, retention behavior, export, backup, deletion and uninstall handling. Sensitive data must not be silently uploaded.

Future cloud identity, subscription, synchronization or update services belong to later releases. Each needs explicit consent, minimization, encryption, availability, privacy, deletion and incident-response controls. A cloud outage must not enable a more permissive trading mode.

# 8. Market-Data Boundary

Release 1 consumes a supplied, validated, single-instrument OHLCV pack; it has no market-data adapter. The committed demonstration pack is synthetic.

Future adapters must be isolated behind stable interfaces and must record provider, license, instrument identity, timestamp/timezone, adjustments, freshness, gaps and quality flags. Invalid, stale, incomplete, out-of-order or ambiguously licensed data must fail closed. Data permission for internal research does not automatically permit redistribution or customer use.

# 9. Strategy Lifecycle

The target lifecycle is: proposed, specified, reviewed, tested, experimental paper-only, approved for a named mode and version, suspended, retired. Every strategy record must include immutable identity/version, parameters, rule references, evidence, data scope, limitations, ownership, review history and allowed modes.

Changing a signal, parameter, fill, cost, accounting or risk rule requires a new attributable version. No strategy is currently Founder-approved for real trading. SMA-001 in Release 1 is an experimental research definition, not an investable recommendation. FIB-001 remains unspecified and unimplemented.

# 10. Risk Guardian Target

The planned independent Risk Guardian is a separate decision boundary that may veto but never weaken system controls. It will evaluate mode, user authority, strategy status, position/concentration limits, loss and drawdown limits, data quality, market/session state, adapter health and emergency-stop state.

Its rules and decisions must be versioned and audited. Failure, timeout, uncertainty or unavailable state must fail closed. Release 1 contains deterministic risk functions and system-owned limits; it does not contain the future independent Risk Guardian service.

# 11. Forward Paper-Simulation Target

The target simulator processes new, validated data over time, schedules causal paper actions, applies the same deterministic risk/accounting foundations, and persists cash, positions, fills, costs, marked equity, drawdown and explicit no-action outcomes. It sends no broker or external order.

Release 1 replays a historical array in one in-memory evaluation. It is not a forward simulator, persistent paper account or claim of market-realistic execution.

# 12. Audit and Reproducibility

Release 1 records canonical input, configuration and strategy hashes; run identity; engine digest and manifest; assumptions; ordered decisions, fills, trades and accounting rows; outcomes and reason codes. Source provenance is captured atomically across the facade and core modules.

The target persistent ledger must be append-oriented, tamper-evident, exportable and attributable to product, engine, strategy, data, policy, mode, user and adapter versions. Secrets must never appear in audit records. Determinism requires identical validated inputs and versioned configuration to yield identical canonical results; it does not imply real-market repeatability.

# 13. Packaging and Distribution

Windows is the first supported implementation target. A distributable build requires a versioned installer/package, integrity verification, dependency inventory, release notes, supported upgrade/rollback behavior, clear uninstall and data-removal instructions and a tested recovery path.

macOS and Linux may be claimed only after separate packaging and testing. "Works on every PC" is an aspiration, not a current claim. No customer distribution is currently authorized.

# 14. Authentication/Subscription Target

Local paper-only alpha may begin without cloud accounts if its authorization and data boundary are explicit. Accounts, licensing and subscriptions are proposed for TRL-R3, not Release 2 implementation by default.

Future identity must support secure authentication, session management, recovery, revocation, least privilege and jurisdiction controls. Entitlement must never silently promote a user into an execution mode. Subscription status must not compromise safe exit, audit export or local data removal.

# 15. Broker-Adapter Boundary

No broker adapter exists or is authorized. A future adapter must be isolated from strategies and the interface by typed proposal, risk, user-confirmation and audit boundaries. It must map instrument and order semantics explicitly, use idempotency, reconcile broker state and handle rejects, partial fills, cancellation, timeouts and uncertain outcomes safely.

TRL-R4 may evaluate broker-demo and assisted execution only after separate authorization. TRL-R5 may evaluate automation only under a separate governance decision. A roadmap entry is not permission to connect a broker.

# 16. Security and Credential Boundary

Release 1 stores or uses no broker, market or customer credential. Future secrets must use an approved operating-system or managed secret store, encryption in transit and at rest, least privilege, rotation and revocation. Secrets must not appear in source, configuration exports, logs, reports, crash data, support bundles or Atlas messages.

Execution-capable components require signed/updateable packages, dependency review, threat modeling, audit protection, safe defaults, rate limits, secure recovery and incident response. Missing or compromised credential state must fail closed.

# 17. Regulatory and Commercial Gates

Before any personalized insight, paid distribution, broker connection, assisted submission or automated execution, the product needs documented legal and regulatory review for each jurisdiction and user class. Review must address investment-advice characterization, licensing/registration, marketing, disclosures, privacy, record retention, market-data rights, consumer protection, taxation and incident obligations.

Technical completion does not equal regulatory or commercial approval. Disclaimers, user consent and "at your own risk" language do not eliminate operator, developer, platform or regulatory responsibility. The product will not accept custody of customer funds.

## 17.1 Release 1 Generated Wording and Future Disclosures

The authoritative implemented and tested Release 1 generated-report wording is:

- Primary disclaimer: **ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING - NO PROFIT CLAIMS**
- Performance disclaimer: **Hypothetical research results from paper-only processing; they do not represent actual trading, predict future returns, or authorize a trade.**
- Generated Markdown label: **PAPER/RESEARCH ONLY**

These strings are the current internal/generated output contract. Current Release 1 output is not approved for public or customer distribution.

**PLANNED - NOT IMPLEMENTED:** Future customer-facing product disclosures are a separate product-layer requirement and must not be substituted for the current generated strings. Future packaging may add jurisdiction-specific disclosures only after legal and regulatory review.

# 18. Release Roadmap

The governed proposal is:

- TRL-R2-001 - Portable Application Foundation.
- TRL-R2-002 - Governed Strategy Registry and Vault.
- TRL-R2-003 - Market-Data and Data-Quality Layer.
- TRL-R2-004 - Insights and Explainability Engine.
- TRL-R2-005 - Forward Paper-Trading Simulator.
- TRL-R2-006 - Independent Risk Guardian and Persistent Audit Ledger.
- TRL-R2-007 - Local Operator Dashboard.
- TRL-R2-008 - Windows Packaging and Closed Paper Alpha.
- TRL-R3 - Accounts, Licensing and Subscription Services.
- TRL-R4 - Broker-Demo and Assisted-Execution Evaluation.
- TRL-R5 - Separately governed automated-execution evaluation.

Release 2 is proposed but not implemented. Every checkpoint requires explicit scope, authorization, evidence and closeout. Inclusion in this roadmap is not implementation authorization.

The next proposed checkpoint is **TRL-R2-001 — PORTABLE APPLICATION FOUNDATION**. TRL-R2-001 remains proposed, unimplemented, and unauthorized. It may begin only after separate explicit Founder authorization; roadmap inclusion, Founder acceptance of Release 1, and closing TRL-R1-005 do not provide that authorization.

# 19. Explicit Exclusions

Current authority excludes live data connections, broker/platform adapters, credentials, external orders, live trading, customer funds, custody, customer distribution, payments, subscriptions, personalized investment advice, leverage, short selling, derivatives, multi-asset portfolios, automatic paper-to-live promotion and performance guarantees.

Release 1 also excludes forward paper simulation, persistent portfolio state, a Strategy Vault workflow, independent Risk Guardian service, market/news adapters, five-agent orchestration, local AI/Gemma, dashboard and packaging. Planned status must not be read as implemented, tested or demonstrated status.

# 20. Definition of Operational Readiness

Operational readiness is not reached. It requires, for the exact supported release and mode:

- Approved scope, architecture, threat model and dependency inventory.
- Complete functional, deterministic, failure, recovery, security, privacy and platform test evidence.
- Licensed data and documented data-quality controls.
- Versioned packaging, installation, upgrade, rollback, uninstall and data-removal procedures.
- Monitoring, emergency stop, incident response, support and audit export.
- Approved strategy and risk records for the named mode.
- Legal, regulatory, jurisdiction, marketing and commercial approvals where applicable.
- Founder approval recorded separately for product distribution and every execution-capable mode.

Passing Release 1 tests meets the Release 1 engineering contract only. It does not make PRJ-017 operationally ready, commercially releasable or safe for live trading.

---

## Historical Reconciliation

TRL-R1-001's 2026-07-24 findings - 12 narrow tests, five warnings, regime signals, same-close fills, missing marked accounting/costs/reason codes and caller-weakenable limits - remain historical evidence. TRL-R1-003 corrected those scoped kernel defects; TRL-R1-004 modularized the behavior without changing it. Multi-instrument portfolios, realistic costs, forward simulation and broader product architecture remain limited, deferred or prohibited as stated above.

## Documentation Review Resolution

- P2 Founder-acceptance finding: Resolved by the explicit 2026-07-26 Founder decision.
- P2 disclaimer-alignment finding: Resolved by retaining the implemented Release 1 strings as the current output contract and marking future customer wording as planned.
- P2 TRL-R1-005 lifecycle finding: Resolved by making this documentation-only closeout commit the checkpoint’s completion event while preserving all no-code, no-distribution, no-execution, and no-Release-2 boundaries.

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial design-only architecture. |
| 1.1 | 2026-07-15 | Recorded the Founder-authorized paper-only historical prototype and unimplemented analyst chain. |
| 1.2 | 2026-07-24 | Reconciled the TRL-R1-001 baseline and defined the Release 1 target boundary. |
| 1.3 | 2026-07-25 | Recorded Release 1 implementation completion and technical evidence, current modules, portable target architecture, capability gates, standalone/Atlas boundary and governed roadmap; Founder acceptance was not yet recorded. |
| 1.4 | 2026-07-26 | Recorded explicit Founder acceptance, corrected the Owner's legal name, aligned current generated wording with planned future disclosures and closed the two P2 documentation findings. |
| 1.5 | 2026-07-26 | Made the TRL-R1-005 documentation-only closeout commit the checkpoint completion event and preserved the separate Release 2 authorization boundary. |
