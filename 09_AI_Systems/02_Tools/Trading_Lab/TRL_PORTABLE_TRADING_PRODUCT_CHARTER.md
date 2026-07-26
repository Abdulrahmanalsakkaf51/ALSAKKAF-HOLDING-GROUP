# ALSAKKAF HOLDING GROUP

# Portable Trading Intelligence and Automation Product Charter

> "LOCAL-FIRST - STANDALONE - GOVERNED BY MODE - NO LIVE TRADING WITHOUT SEPARATE AUTHORIZATION"

---

# 1. Document Control

## Document Information

| Field | Value |
|-------|-------|
| Document ID | TRL-PRODUCT-CHARTER-001 |
| Title | Portable Trading Intelligence and Automation Product Charter |
| Status | CONTROLLED PRODUCT DIRECTION - RELEASE 2 NOT YET IMPLEMENTED |
| Release 1 Status | IMPLEMENTED, EVIDENCE-VALIDATED AND FOUNDER-ACCEPTED AS A PAPER/RESEARCH BASELINE |
| Version | 1.2 |
| Date | 2026-07-26 |
| Owner | Abdulrahman Yaseen Alsakkaf |
| Project | PRJ-017 - ALSAKKAF Trading Research Lab |
| Completed Documentation Checkpoint | TRL-R1-005 — COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT |
| Authority | Product direction only; each implementation, distribution and execution capability requires separate Founder authorization |
| Related Documents | `TRL_R1_RELEASE_CONTRACT.md`; `01_Holding_Company/09_Architecture/Trading_Research_Lab_Architecture.md` |

Changes to this controlled charter require versioned review. This charter does not implement Release 2 and does not grant live-trading, broker, credential, customer-fund or distribution authority.

# 2. Founder Vision

Build a disciplined trading-intelligence product that a supported personal computer can run locally, that explains what it sees and what it does not know, that defaults to safe paper operation, and that may evolve only through explicit evidence and approval gates.

The product should be useful independently, portable in design, optional to Atlas and honest about limits. It must not substitute excitement, disclaimers or automation for governance, security, market evidence or legal responsibility.

# 3. Product Identity

PRJ-017 is defined as:

> A local-first, standalone trading-intelligence platform that can operate independently on a supported personal computer, optionally integrate with Atlas, provide governed strategies and market insights, conduct deterministic paper trading, and - only after separately approved technical, security, legal and regulatory gates - support user-authorized broker execution.

Release 1 is the implemented paper/research kernel. The portable application and all later product layers are targets, not current capabilities.

# 4. Product Purpose

The product's purpose is to help users conduct structured, explainable and auditable trading research; understand governed strategy signals and risk context; rehearse decisions through deterministic paper operation; and retain clear records of data, assumptions, decisions and outcomes.

Its purpose is not to guarantee returns, predict markets with certainty, replace professional advice, operate a fund, hold customer money or evade broker, market-data, consumer, securities or privacy obligations.

# 5. Target Users

Initial target users are the Founder and invited technically capable testers who understand synthetic/hypothetical evidence and can report defects. Later target groups may include independent researchers and self-directed users in approved jurisdictions after usability, security, legal, support and commercial gates.

No current user group is authorized for live execution or customer distribution.

# 6. Supported Use Cases

Planned supported uses are:

- Inspecting governed strategy definitions and their limitations.
- Producing explainable signals, risk context and explicit no-action outcomes.
- Replaying properly sourced historical or synthetic data deterministically.
- Running a future forward paper account without external orders.
- Comparing versioned research evidence without profit claims.
- Exporting attributable audit records.
- Optionally sharing approved context with Atlas through a bounded connector.
- In later separately authorized stages, preparing user-reviewed broker-demo order proposals.

# 7. Explicit Non-Use Cases

The product is not currently for real-money execution, personalized investment advice, custody, pooled funds, copy trading, guaranteed returns, high-frequency trading, market making, unrestricted leverage, shorting, derivatives, tax advice, regulatory evasion or unsupervised operation.

It must not use unlicensed market data, store plaintext secrets, submit an order from `INSIGHT_MODE` or `PAPER_MODE`, accept customer funds, or promote a configuration automatically from paper to execution.

# 8. Standalone-First Principle

The authorized product must be able to install, start, use supported local data, run authorized research/paper capabilities and preserve/export its local records without Atlas or a required cloud service. Core safety, strategy, risk and audit decisions remain local and deterministic where practical.

Optional services may add value but may not become an undocumented prerequisite or weaken safe operation when unavailable.

# 9. Optional Atlas Integration

Atlas may later receive or provide explicitly approved, non-secret context through a versioned adapter. Atlas is not a dependency, strategy authority, risk authority, identity requirement, ledger, credential store, broker gateway or mandatory update channel.

The connector must be off by default unless a checkpoint approves another posture. Users must see what leaves PRJ-017, why, under what consent and with what retention. Connector loss or malformed responses must fail safely and leave standalone operation intact.

# 10. Portability Objective

The architecture should minimize operating-system coupling, keep the deterministic core separate from the user interface and isolate storage, packaging and external adapters behind stable boundaries. Portable means intentionally designed for multiple supported platforms, not currently proven on all computers.

"Works on every PC" is an aspiration, not a claim. Hardware, operating-system, dependency and resource requirements must be published for each supported package.

# 11. Supported-Platform Policy

Windows is the first supported implementation target. Windows support may be claimed only for named versions and tested installation packages. Architecture should avoid unnecessary Windows-only coupling.

macOS and Linux support may be claimed only after separate packaging, security, functional, failure, upgrade and uninstall testing on named versions and architectures. An untested source-code path does not qualify as product support.

# 12. Local-First Data Policy

Default local storage may be used initially. The product must document storage paths, schemas, encryption needs, retention, backup, export, deletion, migration, uninstall and recovery. Data collection must be minimized to what the active feature needs.

User research, strategies, ledgers and personal data must not be uploaded silently. Local analytics or crash collection must be transparent, consented where required and free of secrets.

# 13. Future Cloud Boundary

Cloud identity and subscription services come later, proposed under TRL-R3. Future synchronization, licensing, update, telemetry or support services require explicit schemas, purposes, consent, security, deletion and jurisdiction controls.

A cloud outage or entitlement error must not unlock a more permissive mode, erase audit history or prevent safe shutdown and permitted data export/removal. Cloud services must not be assumed in the deterministic core.

# 14. Insight Mode

`INSIGHT_MODE` provides governed strategies, signals, explanations, risk context and research. It submits no order and has no external-order route.

Outputs must identify data source/quality, strategy/version, assumptions, reason codes, limitations and uncertainty. General research must be clearly distinguished from personalized advice. No output may promise profit, guarantee performance or imply that a tested signal is Founder-approved for real trading.

Status: planned for Release 2; not implemented as a portable product mode.

# 15. Paper Trading Mode

`PAPER_MODE` performs forward simulated execution and sends no broker or external order. It is the intended default product mode and uses the same deterministic risk, cost, accounting, reason-code and audit foundations as the research kernel.

It must distinguish simulation from actual execution on every relevant screen/export. Historical replay does not automatically qualify as forward paper operation. Market data must be synthetic or properly licensed for the intended use.

Status: planned under TRL-R2-005; Release 1 historical replay is implemented, but forward paper mode is not.

# 16. Assisted Execution Mode

`ASSISTED_EXECUTION_MODE` may prepare a proposed order, show instrument, side, type, size, price constraints, estimated costs, risk checks and uncertainty, and require explicit user review and confirmation for each submission.

It must never batch, infer or reuse consent. It remains disabled until broker-demo, security, authentication, audit, legal, regulatory, jurisdiction, strategy, risk and Founder gates pass. A demo evaluation does not authorize real orders.

Status: disabled, prohibited under current authority and proposed only for TRL-R4 evaluation.

# 17. Automated Execution Mode

`AUTOMATED_EXECUTION_MODE` requires explicit user opt-in and may execute only through the user's own approved broker account. PRJ-017 will never accept custody of customer funds.

This mode requires hard exposure/loss/drawdown/frequency limits, independent risk veto, emergency stop, continuous monitoring, broker reconciliation, immutable audit records, secure credentials, jurisdiction gating, incident response and safe failure behavior. "At your own risk" language must never be presented as eliminating operator, developer, platform or regulatory responsibility.

Status: disabled and prohibited until a separately governed TRL-R5 evaluation and later explicit implementation/operation authorization. Roadmap mention grants no permission.

# 18. Capability-Gating Model

Every capability must be gated independently by release version, operating mode, user role, strategy status, data permission/quality, platform support, jurisdiction, account entitlement, security posture, risk state, adapter health and explicit Founder authority.

Default is deny. Missing, stale, inconsistent or unverifiable gate state fails closed. A user interface toggle, license payment, disclaimer acceptance or broker credential must not alone activate an execution capability. Gate decisions and changes must be versioned and audited.

# 19. Strategy Registry and Vault

The planned Registry is the authoritative index of strategy identity, semantic version, family, parameters, rules, evidence, limitations, supported data/modes, owner, review, approval, suspension and retirement. The Vault stores governed immutable strategy artifacts and hashes.

Executable code must not be accepted from an untrusted strategy or data file. Strategy change requires a new attributable version. Approval is mode-specific and may be revoked. No strategy is currently Founder-approved for real trading.

Status: proposed under TRL-R2-002; not implemented.

# 20. Market-Data Adapters

Adapters must isolate providers from the deterministic core and normalize only through documented, testable rules. Every accepted record must retain provider/provenance, instrument identity, timezone, timestamp, adjustments, freshness, quality flags and license classification.

Adapters must detect gaps, duplicates, disorder, stale values, invalid OHLC relationships and symbol ambiguity; unsafe input fails closed. Historical, delayed and real-time rights are distinct. No market-data adapter is currently implemented.

# 21. Explainability and Reason Codes

Every signal, no-action, block, halt, fill proposal and risk veto must expose stable machine-readable reason codes and concise human explanations. Explanations must identify strategy/version, data cutoff, assumptions, relevant limits and material unknowns.

AI-generated language may explain recorded deterministic outputs but may not invent, alter or conceal them. Confidence language must be calibrated and must not become a performance promise or personalized recommendation.

# 22. Independent Risk Guardian

The target Risk Guardian is independent from strategy generation and order preparation. It may veto but never weaken system-owned controls. It must assess mode, strategy approval, exposure, concentration, loss/drawdown, data quality/freshness, market/session constraints, user/broker state and emergency-stop status.

Timeout, failure, uncertain state or missing evidence must deny new risk. Vetoes and supporting policy versions must be immutable audit events. Release 1 risk functions are implemented; the independent guardian service is not.

# 23. Portfolio and Audit Ledger

The target ledger records attributable proposals, decisions, paper/external acknowledgements, fills, rejects, positions, cash, fees, marked values, P&L, limits, overrides, errors and reconciliation. It must distinguish simulated from broker-reported state.

Records should be append-oriented, tamper-evident, versioned, exportable and recoverable. Corrections require linked entries, not silent edits. Secrets must never be stored in ledger content. Release 1 has deterministic in-memory accounting rows, not this persistent portfolio ledger.

# 24. Broker-Adapter Boundary

No broker adapter is implemented or authorized. A future adapter receives only a fully specified, mode-authorized proposal that has passed independent risk and required user confirmation. Strategies and Atlas may not call it directly.

Adapters must handle symbol/order mapping, idempotency, rate limits, rejects, partial fills, cancellations, timeouts, duplicate responses, reconnects and uncertain submission state. Broker state must be reconciled before further risk. Each broker and account type needs separate certification and jurisdiction review.

# 25. Credential and Secret Handling

Release 1 uses no broker, market or customer credentials. Future secrets must be stored in an approved operating-system or managed secret facility, encrypted in transit/at rest, least-privileged, rotatable and revocable.

Secrets must never appear in source, Markdown, ordinary configuration, logs, reports, analytics, crash dumps, screenshots, support bundles, audit exports or Atlas messages. Missing, expired or compromised credentials must fail closed and produce a non-secret incident record.

# 26. Emergency Stop and Failure Behavior

Execution-capable designs require a prominent local emergency stop, a documented remote/operational disable path where legally and technically appropriate, and safe state transitions. The stop must block new submissions immediately and record its activation.

Network loss, stale data, clock error, adapter disagreement, authentication failure, audit failure, risk-service failure or uncertain broker response must fail closed. Recovery must reconcile actual broker state before resuming. An emergency stop does not imply undocumented forced liquidation; any close behavior must be separately specified and approved.

# 27. Authentication and User Accounts

Local paper alpha may use an explicitly scoped local operator profile without cloud identity. Future accounts require strong authentication, secure sessions, recovery, revocation, device and role management, brute-force protection and auditable privilege changes.

Execution requires step-up authentication and clear account/broker identity. Shared accounts and ambiguous operators are not acceptable. Account creation or payment must never imply execution approval.

# 28. Licensing and Subscription Model

Licensing/subscription services are proposed for TRL-R3. Possible tiers must be defined by transparent feature entitlements without misleading performance claims. Paid access may not bypass strategy, risk, legal, jurisdiction or mode gates.

Subscription expiry must preserve safe shutdown, historical audit access/export and legally required data rights. Refund, renewal, taxes, support obligations and consumer terms require commercial/legal approval before sale.

# 29. Customer-Data and Privacy Boundary

Collect the minimum customer data needed for an approved feature. Document purpose, lawful basis, consent where required, retention, access, correction, deletion, export, subprocessors, cross-border transfer and incident notice.

Trading research and account activity may be sensitive. It must not be sold, repurposed for model training, shared with Atlas or used for marketing without a separately approved and clearly disclosed basis. No customer-data service is currently implemented.

# 30. Market-Data Licensing Boundary

Synthetic data may be used for controlled engineering. Historical, delayed, real-time, derived and redistributed data each require documented rights for the exact internal, alpha or commercial use.

The product must not assume that access equals permission to cache, transform, display, export or redistribute. Provider attribution, retention and user-count limits must be enforceable before any distributable stage.

# 31. Security Requirements

Each releasable product needs threat modeling, least privilege, secure defaults, dependency inventory/scanning, signed builds and updates, integrity checks, protected local data, input validation, authorization tests, audit protection, rate limits, backup/recovery and vulnerability/incident processes.

Execution-capable releases additionally require penetration testing appropriate to risk, broker-adapter review, secret lifecycle tests, supply-chain controls, abuse monitoring and emergency exercises. Test passage is evidence, not a security guarantee.

# 32. Regulatory and Legal Review Gates

Separate written review is required before personalized insights, customer distribution, payments, broker integration, assisted submission or automation in each jurisdiction. Review must address investment-advice and broker/dealer characterization, registration/licensing, disclosures, suitability or appropriateness where relevant, record retention, privacy, consumer protection, marketing, market-data rights, tax and incident obligations.

A feature must stay disabled where approval is absent, unclear, expired or jurisdictionally unsupported. Product wording and user consent do not replace legal compliance.

# 33. No-Custody and No-Customer-Funds Policy

PRJ-017 will not receive, pool, hold, transfer, settle, withdraw or control customer funds or assets. Any later execution occurs only through the user's own approved broker account and broker-controlled money movement.

The product must not request deposits, accept trading capital, operate omnibus accounts or expose functionality that effectively creates custody. Any proposed exception would require a new project charter and full legal/regulatory authorization; this charter grants none.

# 34. Marketing and Performance-Claim Policy

Marketing must distinguish synthetic, backtested, forward-paper, demo-broker and actual results. It must disclose material assumptions, costs, periods, data limitations, survivorship/selection risks and whether results are hypothetical.

No guaranteed return, proven-profitability, low-risk-income, market-beating or universal compatibility claim is permitted. Cherry-picked runs, misleading charts and annualized projections presented as expectations are prohibited. Disclaimers cannot cure a misleading overall impression.

## 34.1 Current Release 1 Wording and Future Disclosures

The authoritative implemented and tested Release 1 generated-report wording is:

- Primary disclaimer: **ARCHITECTURE DEMONSTRATION ONLY - NOT FINANCIAL ADVICE - NO LIVE TRADING - NO PROFIT CLAIMS**
- Performance disclaimer: **Hypothetical research results from paper-only processing; they do not represent actual trading, predict future returns, or authorize a trade.**
- Generated Markdown label: **PAPER/RESEARCH ONLY**

These strings are the current internal/generated output contract. Current Release 1 output is not approved for public or customer distribution.

**PLANNED - NOT IMPLEMENTED:** Future customer-facing product disclosures are a separately governed product requirement and must not be substituted for current Release 1 generated wording. Future packaging may add jurisdiction-specific disclosures only after legal and regulatory review. "At your own risk" wording must not be described as eliminating operator, developer, platform or regulatory responsibility.

# 35. Family/Friends Closed-Alpha Policy

The first distributable test stage is:

- Invitation-only.
- Paper-only.
- Synthetic or properly licensed data only.
- No broker credentials.
- No real orders.
- No customer funds.
- No payment required during the earliest technical alpha.
- Explicit feedback and incident reporting.
- A versioned installation package.
- Clear uninstall and data-removal instructions.
- No profitability claims.

Participants must receive supported-platform, known-risk, data-handling and support/incident instructions. Alpha access is testing permission only, not strategy approval, advice or live-trading authority.

# 36. Atlas Connector Policy

The Atlas connector is optional, separately installable/configurable where practical, versioned and permission-bounded. It may exchange only documented fields for approved purposes and must exclude secrets and unauthorized customer/trading data.

The connector cannot place orders, override mode/risk gates, approve strategies, rewrite ledger entries or make Atlas a required service. It must support disablement and safe degradation, and its actions must be visible in the audit record.

# 37. Packaging and Update Policy

Every distributed build must have an immutable version, supported platform list, dependency inventory, integrity/signature mechanism, release notes, known issues, migration plan and reproducible release evidence. Updates must preserve or explicitly migrate strategies, policies and ledgers.

Update failure must be recoverable. Rollback must not silently make data incompatible or activate a capability. Installation, upgrade, rollback, uninstall and local data removal must be documented and tested. Release 1 currently has no distributable application package.

# 38. Cross-Platform Testing Policy

Claims are limited to named operating-system versions, architectures and package versions tested through installation, startup, deterministic core tests, storage, export, update, recovery, uninstall and relevant security/failure cases.

Windows is first. macOS and Linux require their own evidence. Core deterministic fixtures should produce the same canonical results across supported platforms, subject to an explicitly documented numeric/serialization contract. Platform-specific differences must fail visibly, not silently change a decision.

# 39. Release Roadmap

The proposed, not-yet-implemented roadmap is:

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

Each checkpoint requires its own scope, authorized paths/capabilities, tests, risk review, closeout evidence and Founder decision. Roadmap inclusion is not implementation authorization.

The next proposed checkpoint is **TRL-R2-001 — PORTABLE APPLICATION FOUNDATION**. TRL-R2-001 remains proposed, unimplemented, and unauthorized. It may begin only after separate explicit Founder authorization; roadmap inclusion, Founder acceptance of Release 1, and closing TRL-R1-005 do not provide that authorization.

# 40. Definition of Product Readiness

Product readiness is mode-, version-, platform-, data- and jurisdiction-specific. It requires completed requirements, supported packaging, deterministic and functional evidence, failure/recovery evidence, security/privacy review, data rights, usable disclosures, support/incident operations, documented limitations and recorded Founder approval.

`INSIGHT_MODE` and `PAPER_MODE` readiness do not imply execution readiness. Assisted readiness does not imply automated readiness. Release 1 technical completion does not establish customer, commercial, regulatory, production or live-trading readiness.

# 41. Founder Approval Gates

Founder approval must be separately recorded for:

- Each Release 2 implementation checkpoint.
- Strategy admission and every permitted operating mode.
- Use of a market-data provider and its license boundary.
- Invitation-only alpha distribution and its supported package.
- Customer accounts, payments, licensing and commercial release.
- Every Atlas connector capability/data field.
- Broker-demo evaluation and each broker adapter.
- Assisted execution in each jurisdiction.
- Any automated-execution evaluation and any later operational authorization.

No earlier approval automatically grants a later one. No strategy is currently approved for real trading, and no live trading is currently authorized.

## 41.1 Founder Approval History

Implementation completion occurred through commits `05f7ba9` and `4b99789`. Technical evidence includes 132 passing direct tests, the same 132 tests passing through discovery and the deterministic synthetic rehearsal. Those commits and tests did not automatically create Founder acceptance.

Founder acceptance occurred on 2026-07-26 and is limited to the completed technical paper/research baseline. The exact decision is:

> “I, Abdulrahman Yaseen Alsakkaf, formally accept PRJ-017 Release 1 as a completed technical paper/research baseline. This acceptance does not approve SMA-001 or any strategy for investment use, does not validate profitability, and does not authorize customer distribution, investment advice, broker connectivity, automated execution, live trading, customer funds, regulatory status, or Release 2 implementation.”

**TRL-R1-005 — COMPLETED DOCUMENTATION-ONLY RELEASE 1 CLOSEOUT.** Completed by the TRL-R1-005 documentation-only closeout commit; Git history is the authoritative commit reference.

TRL-R1-005 authorizes only its own four-document closeout commit. It authorizes no code change, customer distribution, Release 2 implementation, broker connectivity, assisted execution, automated execution, live trading, investment advice, customer funds, payment handling, or regulatory claim.

TRL-R1-004 remains the latest implemented runtime/kernel checkpoint. TRL-R1-005 is the completed documentation, Founder-acceptance, and Release 1 closeout checkpoint. TRL-R2-001 remains proposed, unimplemented, and unauthorized. TRL-R2-001 may begin only after separate explicit Founder authorization; closing TRL-R1-005 does not provide that authorization.

# 42. Deferred Questions and Risks

The following remain unresolved and must be answered in their governing checkpoints:

- Exact Windows versions, hardware floor, installer technology and update-signing model.
- Local database, encryption, backup, migration and user-controlled deletion design.
- Strategy review methodology, evidence thresholds, suspension and retirement rules.
- Market-data providers, licensing costs, real-time needs and derived-data rights.
- Explainability interface and the boundary between general research and personalized advice.
- Forward simulator clock, session, corporate-action, gap and outage semantics.
- Risk Guardian independence, policy ownership, emergency-stop and recovery rules.
- Portfolio scope, reconciliation, tax-lot and broker-state semantics.
- Authentication, subscription, privacy jurisdictions and support model.
- Broker selection, demo capability, order types, partial-fill/idempotency behavior and certification.
- Legal/regulatory classification by jurisdiction and user type.
- Security threat model, penetration-test scope, incident response and vulnerability intake.
- Alpha participant terms, feedback workflow, data support and exit criteria.
- Atlas connector schema, consent, retention and failure boundary.
- Evidence needed before any strategy, commercial release or execution mode can receive Founder approval.

Until resolved and authorized, these items are deferred, not assumed. Execution modes remain prohibited.

# 43. Documentation Review Resolution

- P2 Founder-acceptance finding: Resolved by the explicit 2026-07-26 Founder decision.
- P2 disclaimer-alignment finding: Resolved by retaining the implemented Release 1 strings as the current output contract and marking future customer wording as planned.
- P2 TRL-R1-005 lifecycle finding: Resolved by making this documentation-only closeout commit the checkpoint’s completion event while preserving all no-code, no-distribution, no-execution, and no-Release-2 boundaries.

---

## Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-25 | Initial controlled portable-product direction created under TRL-R1-005; Release 2 and later roadmap remain unimplemented and unauthorized. |
| 1.1 | 2026-07-26 | Recorded explicit Founder acceptance, corrected the Owner's legal name, aligned current generated wording with planned future disclosures and closed the two P2 documentation findings. |
| 1.2 | 2026-07-26 | Made the TRL-R1-005 documentation-only closeout commit the checkpoint completion event and preserved the separate Release 2 authorization boundary. |
