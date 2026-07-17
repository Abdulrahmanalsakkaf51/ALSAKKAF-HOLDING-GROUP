# NESTLYRA — Product-Claim Verification (Template)

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Template with EXAMPLE ONLY rows. No product page may carry a claim that has not passed this verification.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-013 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Verify, claim by claim, that everything a NESTLYRA product page would say is true and evidenced — including restrictions and safety checks (NAL-007 Stage 6) and post-sample claim confirmation (Stage 13).

---

# Scope

Covers: the claim register format, the restrictions/safety section, and verification rules. Does not cover: writing the product copy (the NESTLYRA-015 to 017 templates own page structure) or inventing claims — removed claims are simply removed.

---

# 1. Claim Register (per candidate)

| Claim ID | Candidate ID | Claim As It Would Appear | Claim Type | Evidence (NAL-010 / NAL-012) | Verified State | Action |
|----------|--------------|--------------------------|------------|------------------------------|----------------|--------|
| EXAMPLE-CL-001 | EXAMPLE-PC-001 | [Example Only - Not Real] "Holds up to N liters" | Capacity | None yet | UNVERIFIED | Cannot appear on any page until verified against the inspected sample |
| EXAMPLE-CL-002 | EXAMPLE-PC-001 | [Example Only - Not Real] "Made of sample material" | Material | None yet | UNVERIFIED | Cannot appear on any page until verified against the inspected sample |

---

# 2. Restrictions and Safety Check (per candidate, Stage 6)

| Check | Entry Rule |
|-------|------------|
| Product category restrictions in target country | Confirmed permitted / restricted / UNKNOWN — with source and date |
| Materials safety concerns | Any flammability, chemical, or child-safety consideration recorded or None Found with the sources checked |
| Shipping restrictions | Any carrier or customs restriction for the product type, or None Found with sources checked |
| Age or usage warnings required | What warnings, if any, the product page and packaging must carry |

UNKNOWN in any row blocks Stage 6 completion. UNKNOWN is recorded honestly and resolved with evidence, never waved through.

---

# 3. Rules

1. Verified State values: VERIFIED (evidence cited), UNVERIFIED (no evidence yet), FAILED (evidence contradicts the claim). Only VERIFIED claims reach a product page.
2. A FAILED claim is removed, not reworded into vagueness. If the honest version of a product is unattractive, that is gate information, not a copywriting problem.
3. Claims are re-verified against the physical sample (NAL-012 claim cross-check) — listing evidence alone completes Stage 6 but not Stage 13.
4. The house rule from the NESTLYRA content package continues to apply: no invented dimensions, materials, weights, delivery dates, discounts, urgency, scarcity, reviews, or testimonials, anywhere, ever.

---

# Related Documents

- NAL-007 / `07_Product_Approval_Gate.md`
- NAL-010 / `10_Supplier_Evidence_Register.md`
- NAL-012 / `12_Sample_Inspection_Record.md`
- NESTLYRA-015 to NESTLYRA-017 / product page templates in `../14_NESTLYRA_Store/`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial template — claim register, restrictions check, four rules |

---
