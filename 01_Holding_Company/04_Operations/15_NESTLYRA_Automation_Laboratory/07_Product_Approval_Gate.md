# NESTLYRA — Product Approval Gate

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. No product exists yet; this gate defines how one would earn draft publication. No product is approved merely because AI considers it attractive.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-007 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.1 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Define the single pipeline every product candidate must pass, in order, before it becomes eligible for draft publication on the NESTLYRA store. This extends the existing Product Verification Checklist (NESTLYRA-018) into a full evidence pipeline with named registers at every stage.

---

# Scope

Covers: the pipeline stages, the register each stage writes to, and the gate rules. Does not cover: the register templates themselves (documents NAL-008 to NAL-015) or live Shopify publication (blocked until the Launch Blocker Register, NAL-023, is clear).

---

# 1. The Pipeline

Every stage must be complete, in order, with evidence, before the next stage begins.

| Stage | Step | Evidence Recorded In |
|-------|------|----------------------|
| 1 | PRODUCT CANDIDATE identified | NAL-008 Product Candidate Register |
| 2 | Supplier identity and evidence | NAL-009 Supplier Register, NAL-010 Supplier Evidence Register |
| 3 | Source URL and evidence date | NAL-010 Supplier Evidence Register |
| 4 | Product specifications | NAL-008 (specification fields) |
| 5 | Dimensions and materials | NAL-008 (specification fields), cross-checked at Stage 12 |
| 6 | Restrictions and safety | NAL-013 Product-Claim Verification (restrictions section) |
| 7 | Target-country shipping confirmed | NAL-017 Market Readiness Register |
| 8 | Tracked-delivery evidence | NAL-010 Supplier Evidence Register |
| 9 | Landed-cost calculation | NAL-011 Landed-Cost Calculator (extends NESTLYRA-020) |
| 10 | Return path confirmed | NAL-020 Returns and Resolution Workflow (return-path section) |
| 11 | Sample order required — placed by Founder | NAL-014 Founder Approval Queue (sample order is a spend) |
| 12 | Sample inspection | NAL-012 Sample Inspection Record (extends NESTLYRA-021) |
| 13 | Claims verification | NAL-013 Product-Claim Verification |
| 14 | Guardian review | NAL-014 Founder Approval Queue (Guardian check recorded) |
| 15 | Founder approval | NAL-014 Founder Approval Queue |
| 16 | Eligible for DRAFT publication | Product record updated; live publication still gated by NAL-023 |

---

# 2. Gate Rules

1. No stage may be skipped, merged, or taken on faith. A missing stage means the candidate waits.
2. No product is approved merely because AI considers it attractive. Attractiveness is not evidence; the pipeline is.
3. A sample order is mandatory (Stage 11). No product reaches Founder approval without a physically inspected sample (Stage 12, per NESTLYRA-021).
4. Every claim that would appear on the product page must pass Stage 13 — claims without evidence are removed, not softened.
5. Failure at any stage sends the candidate to the Rejected Product Lessons Log (NAL-015) with the reason recorded. Rejection is a valid, valuable outcome.
6. Stage 16 grants eligibility for DRAFT publication only. Actual publication requires the store-level Launch Blocker Register (NAL-023) and Launch Readiness Checklist (NESTLYRA-022) to be clear, plus a final Founder decision.
7. Real supplier names, quotes, and correspondence live in private operational storage per PODS-001. The public registers hold structure and EXAMPLE ONLY rows.

---

# Related Documents

- NESTLYRA-018 / `../14_NESTLYRA_Store/18_Product_Verification_Checklist.md`
- NAL-008 to NAL-015 / register and record templates in this folder
- NAL-023 / `23_Launch_Blocker_Register.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial pipeline definition — sixteen stages, seven gate rules |
| 1.1 | 2026-07-17 | Cross-reference renumbered to the final NAL-016..027 file plan (Returns workflow is NAL-020) |

---
