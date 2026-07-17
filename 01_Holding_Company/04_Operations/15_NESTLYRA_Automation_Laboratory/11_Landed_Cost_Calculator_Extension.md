# NESTLYRA — Landed-Cost Calculator: Gate Integration Extension

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. This document extends the existing Landed Cost Calculator Specification (NESTLYRA-020). It does not repeat or replace it — read NESTLYRA-020 first. No real cost figure exists for any product.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-011 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.1 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Connect the NESTLYRA-020 calculation (inputs, formula, outputs — defined there, not here) to the Product Approval Gate (NAL-007 Stage 9) and the Market Activation Gate (NAL-016), and add the evidence and record-keeping requirements those gates need.

---

# Scope

Covers: what NAL-007/NAL-016 additionally require of a landed-cost calculation beyond the NESTLYRA-020 math. Does not cover: the core formula, input fields, or outputs — NESTLYRA-020 owns those and remains authoritative.

---

# 1. What NESTLYRA-020 Already Defines (referenced, not duplicated)

- The core calculation: landed cost per unit, margin, margin percentage.
- The eight required input fields (unit cost through target retail price).
- The symbolic worked example and the required outputs including the sensitivity check.

---

# 2. Gate Extensions

| # | Extension | Requirement |
|---|-----------|-------------|
| 1 | Evidence-linked inputs | Every input value must cite an Evidence ID from NAL-010 (supplier quotes, shipping quotes) or a Founder-verified fact from NAL-002 (fees). An input without an evidence link is UNKNOWN and blocks the calculation from being used for approval |
| 2 | Per-Market calculation | The calculation runs once per candidate Market, because shipping, duty, and return cost differ by country. A UAE-only calculation says nothing about any other Market (NAL-016 criterion 9) |
| 3 | Return-cost line | Add the expected per-unit cost of the return path (from NAL-020 return-path data) as a named input when comparing Markets — a Market with an unaffordable return path fails unit economics even with good margin |
| 4 | Calculation record | Every calculation used in an approval request is saved as a dated record (candidate ID, Market, all inputs with Evidence IDs, all outputs) so the Founder approves numbers with a traceable origin |
| 5 | Staleness rule | A calculation is Stale when any cited evidence is Stale per NAL-010 rule 2; Stale calculations cannot support an approval |
| 6 | Honest-unknown rule | If duty rate, payment fee, or any input is UNKNOWN (see NAL-003 U-04, U-05), the calculation output is labeled INCOMPLETE — it may inform discussion but never approval |

---

# 3. Calculation Record Template (EXAMPLE ONLY)

| Field | Example Value |
|-------|---------------|
| Calculation ID | EXAMPLE-LC-001 |
| Date | 2026-07-17 |
| Candidate ID | EXAMPLE-PC-001 |
| Market | [Example Only - Not Real] Sample Country |
| Inputs with Evidence IDs | [Example Only - Not Real] Unit cost per EXAMPLE-EV-001; shipping per EXAMPLE-EV-002; duty UNKNOWN (U-04) |
| Outputs | INCOMPLETE — duty input UNKNOWN, not usable for approval |
| Used in approval request | No |

---

# Related Documents

- NESTLYRA-020 / `../14_NESTLYRA_Store/20_Landed_Cost_Calculator_Spec.md` (authoritative core spec)
- NAL-007 / `07_Product_Approval_Gate.md`
- NAL-010 / `10_Supplier_Evidence_Register.md`
- NAL-016 / `16_Market_Activation_Gate.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial extension — six gate requirements added on top of NESTLYRA-020 |
| 1.1 | 2026-07-17 | Cross-reference renumbered to the final NAL-016..027 file plan (return-path data lives in NAL-020) |

---
