# TRL Strategy Authoring Guide

## Document Information

| Field | Value |
|---|---|
| Document | TRL Strategy Authoring Guide |
| Project | PRJ-017 — ALSAKKAF Trading Research Lab |
| Checkpoint | TRL-R2-002 |
| Status | IMPLEMENTED — LOCAL PAPER/RESEARCH FOUNDATION |
| Date | 2026-07-26 |
| Owner and Founder Authority | Abdulrahman Yaseen Alsakkaf |
| Product boundary | LOCAL-ONLY — NO CLOUD — NO BROKER — NO EXTERNAL ORDERS |

> **A proposal is not an implementation, validation result, investment approval, or profitability claim.**

## Purpose

This guide defines how a future strategy idea can enter PRJ-017 governance while the application remains local, deterministic, paper/research-only, and fail-closed. The current executable registry contains only SMA-001 version 1.0.0. A future idea belongs in the separate research backlog until its implementation and evidence are independently approved.

## Start with a research proposal

A proposal should state:

- a unique `BACKLOG-...` identifier, plain-language name, and research question;
- intended markets and timeframes without claiming compatibility;
- future data, timestamp, licensing, quality, and provenance needs;
- causal-information constraints and potential look-ahead paths;
- principal risks such as overfitting, costs, gaps, selection bias, survivorship bias, latency, or regime sensitivity;
- known exclusions and what evidence could falsify the hypothesis.

Do not add formulas, code fragments, imports, paths, callable names, supposed optimal parameters, profit claims, or invented results merely to make the proposal appear complete. A backlog entry must remain `PLANNED_NOT_IMPLEMENTED` and `execution_eligible: false`.

## Governed lifecycle

Every future strategy must pass separately governed stages in this order:

```text
PROPOSED
→ SPECIFIED
→ IMPLEMENTED
→ UNIT_TESTED
→ HISTORICALLY_VALIDATED
→ OUT_OF_SAMPLE_VALIDATED
→ FORWARD_PAPER_VALIDATED
→ FOUNDER_REVIEWED
```

These stages are evidence gates, not automatic fields in the current executable schema.

### PROPOSED

Record the falsifiable question, intended scope, future data needs, limitations, risks, and conflicts. The item remains backlog-only.

### SPECIFIED

Produce a separately reviewed causal specification: exact inputs, event timing, parameter types and bounds, risk interaction, expected reason codes, invalid-input behavior, and reproducibility requirements. Specification still does not mean implemented.

### IMPLEMENTED

Implement only through an authorized checkpoint. Code must remain locally inspectable, deterministic, standard-library compatible where the product boundary requires it, and free of dynamic definition loading. A JSON record never supplies executable code.

### UNIT_TESTED

Test every rule transition, equality boundary, causality boundary, invalid type, numeric edge, status transition, identity, deterministic repeat, and failure state. Passing unit tests is engineering evidence, not market evidence.

### HISTORICALLY_VALIDATED

Evaluate governed historical data with declared costs, limitations, data provenance, and bias controls. Do not use a favorable historical result as proof of future performance.

### OUT_OF_SAMPLE_VALIDATED

Freeze the specification and parameters before evaluation against held-out data. Record negative and unstable outcomes as evidence rather than selecting only favorable periods.

### FORWARD_PAPER_VALIDATED

Use only a separately approved future forward-paper capability. TRL-R2-002 does not provide that capability. Forward paper results remain hypothetical and do not authorize an order.

### FOUNDER_REVIEWED

Present the complete evidence, limitations, conflicts, failure behavior, and identity chain for an explicit Founder decision. Founder review does not by itself create investment approval, live approval, profitability, customer distribution approval, or execution authority.

## Admission to the executable registry

Admission requires a separate authorized checkpoint that:

1. approves the implementation and exact ID/version;
2. adds a strict data-only record satisfying the then-current schema;
3. updates the exact catalog allowlist and code-owned digest trust anchors;
4. proves the implementation identity matches its registry description;
5. adds deterministic unit, integrity, eligibility, API, dashboard, and regression tests;
6. documents approval status honestly and retains all known limitations;
7. proves Release 1 and all existing strategy semantics remain unchanged unless an explicit migration checkpoint authorizes otherwise.

Never copy a backlog item into the executable registry merely because research is interesting. Never use registry ordering, a backtest score, or recent performance to label a strategy as best. The registry records governance facts; it does not optimize or select.

## Versioning and identity

Use canonical semantic versions. Any definition change that can affect behavior, declared requirements, parameters, risk characteristics, eligibility, or limitations requires a governed version decision and new deterministic identities. Do not edit an installed definition silently.

Keep these identities distinct:

- the implementation/kernel strategy-definition hash;
- the canonical registry-record digest;
- the normalized vault file digest;
- the complete vault bundle digest.

All must be lowercase SHA-256 values. Catalog files must be strict UTF-8 JSON with deterministic content and no duplicate fields. The catalog has no loader for Python or any other executable format.

## Approval language

Allowed registry approval states are deliberately narrow: `EXPERIMENTAL_RESEARCH_ONLY`, `PAPER_ELIGIBLE`, `FOUNDER_REJECTED`, and `RETIRED`. Do not create or imply `INVESTMENT_APPROVED`, `LIVE_APPROVED`, or `PROFITABLE`.

Completing every lifecycle stage cannot guarantee profitability, future performance, market validity, suitability for any person, investment approval, or permission to trade. Any later execution-related authority requires a separate explicit product and governance decision.
