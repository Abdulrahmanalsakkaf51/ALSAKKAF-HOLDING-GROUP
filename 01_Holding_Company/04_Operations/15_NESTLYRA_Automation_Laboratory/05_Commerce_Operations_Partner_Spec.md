# NESTLYRA Commerce Operations Partner — Design Specification

Status: PROPOSED — NOT ACTIVATED. This is a design-stage document only. Per the Partner Factory rules (CLAUDE-001, OPS-001), no Partner is Active without a profile, prompt, test log, Founder approval, and a Partner Registry update — none of which exist yet for this Partner.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-005 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft — Proposed, not activated |
| Version | 1.1 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Specify one modular AI Partner — the NESTLYRA Commerce Operations Partner — that will eventually operate the NESTLYRA back office under strict Founder control. This specification defines its skills and boundaries so the future Partner Factory build has an approved design to work from.

---

# Scope

Covers: the Partner's proposed skill modules, operating principles, and references to its Permission Matrix (NAL-006). Does not cover: the Partner profile, system prompt, test log, or activation — those are future Partner Factory work and require Founder approval at each step.

---

# 1. Design Principle

One Partner, many controlled skills — not many uncoordinated Partners. Every skill produces drafts, records, calculations, or recommendations. No skill executes an outbound or money-moving action. The Founder is the only actor who publishes, spends, sends, or approves.

---

# 2. Skill Modules

| # | Skill Module | What It Does (design intent) | Key Registers It Uses |
|---|--------------|------------------------------|------------------------|
| 1 | Product and Supplier Verification | Classifies product candidates, checks evidence completeness against the Product Approval Gate, flags missing verification items | NAL-008, NAL-009, NAL-010, NAL-013 |
| 2 | Market Readiness | Compares a candidate country against the Market Activation Gate criteria and prepares pass/fail evidence tables | NAL-016, NAL-017 |
| 3 | Order Control | Runs the First 20 Orders workflow checks (payment state, address, risk flags, Market eligibility) and prepares supplier orders for Founder approval | NAL-018 |
| 4 | Customer Care Drafting | Drafts customer replies for Founder review; never sends | NAL-019 |
| 5 | Supplier and Inventory Exceptions | Detects and registers supplier problems (out of stock, price change, delay) and prepares options for the Founder | NAL-021 |
| 6 | Returns and Resolution | Drafts return-path handling and resolution options; never issues a refund | NAL-020 |
| 7 | Office Clerk Recordkeeping | Keeps every register row current, complete, and honest; owns record hygiene | All NAL registers |
| 8 | Reporting and Cost Analysis | Prepares landed-cost calculations, margin reports, and honest KPI summaries (zero reported as zero) | NAL-011, NAL-014 |
| 9 | Guardian Review | Applies the Guardian-style safety check to every prepared action before it reaches the Founder Approval Queue | NAL-014, NAL-006 |

---

# 3. Operating Principles

1. Every skill module operates inside the Permission Matrix (NAL-006). The matrix wins over any skill description.
2. Every outbound step (customer message, supplier order, refund, publication) stops at a Founder approval gate. No exceptions during the design and early-operation phases.
3. The Partner never approves its own work — Guardian Review is a check, not an approval authority.
4. All real supplier and customer data the Partner would eventually handle lives in private operational storage per PODS-001, never in this public repository.
5. Until activation, this Partner exists only on paper. Any document referring to it must carry the label "Proposed — not activated."

---

# 4. Activation Path (future work, not this project checkpoint)

| Step | Artifact | Status |
|------|----------|--------|
| 1 | Partner profile (PARTNER-xxx) | Not created |
| 2 | Partner prompt | Not created |
| 3 | Partner test log (synthetic acceptance test pack — planned in a later sub-checkpoint) | Not created |
| 4 | Guardian activation review | Not performed |
| 5 | Founder approval (ADR) | Not requested |
| 6 | Partner Registry update | Not made |

---

# Related Documents

- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-027 / `27_Partner_Error_and_Correction_Log.md`
- CLAUDE-001 / `../../../CLAUDE.md` (Partner Factory safety rules)
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial design specification — Proposed, not activated |
| 1.1 | 2026-07-17 | Cross-references renumbered to the final NAL-016..027 file plan (Order Control NAL-018, Customer Care NAL-019, Returns NAL-020, Exceptions NAL-021, error log NAL-027); synthetic test pack noted as later sub-checkpoint work |

---
