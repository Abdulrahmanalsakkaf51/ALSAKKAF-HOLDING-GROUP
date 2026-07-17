# NESTLYRA — Sample Inspection Record (Template)

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Template with an EXAMPLE ONLY record. No sample has been ordered or inspected. The inspection checklist itself is NESTLYRA-021 — this document is the record format that captures each inspection's results.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-012 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Give every physical sample inspection (NAL-007 Stage 12) a permanent, structured record: what arrived, what was checked per NESTLYRA-021, what passed, what failed, and the resulting decision.

---

# Scope

Covers: the per-sample record format and rules. Does not cover: the checklist content (NESTLYRA-021 owns what to check) or the sample-order approval (that is a spend — NAL-014).

---

# 1. Record Template (one per sample)

| Field | Entry Rule |
|-------|------------|
| Sample Record ID | Sequential SIR-xxx |
| Date Received | Actual arrival date |
| Candidate ID | From NAL-008 |
| Supplier Ref | From NAL-009 |
| Order Date and Transit Time | Real dates — this is also tracked-delivery evidence (log in NAL-010) |
| NESTLYRA-021 Checklist Result | Item-by-item pass/fail from the Sample Inspection Checklist |
| Dimensions Measured | Actual measured values, compared against listed specifications |
| Materials Observed | What the item is actually made of, as observable |
| Claim Cross-Check | Each listing claim marked Matches / Does Not Match / Cannot Verify (feeds NAL-013) |
| Photos Taken | Yes/No and private storage path (photos may reveal supplier packaging — PODS-001) |
| Defects Found | Listed plainly, or None |
| Inspector | Founder (solo operation) |
| Decision | Pass / Fail / Re-sample Required |

---

# 2. EXAMPLE ONLY Record

| Field | Example Value |
|-------|---------------|
| Sample Record ID | EXAMPLE-SIR-001 |
| Date Received | 2026-07-17 |
| Candidate ID | EXAMPLE-PC-001 |
| Supplier Ref | EXAMPLE-SUP-001 |
| Order Date and Transit Time | [Example Only - Not Real] illustrates format only |
| NESTLYRA-021 Checklist Result | [Example Only - Not Real] not a real inspection |
| Decision | None — template row |

---

# 3. Rules

1. A sample inspection cannot pass with any checklist item unanswered — Cannot Verify is an answer, but it pushes the related claim out of the product page (NAL-013).
2. Measured dimensions win over listed dimensions everywhere, including the product page and shipping-cost inputs.
3. A failed sample sends the candidate to NAL-015 with the failure reason, or to Re-sample if the Founder decides the supplier deserves a second attempt.
4. Every inspection record is kept permanently, including failures.

---

# Related Documents

- NESTLYRA-021 / `../14_NESTLYRA_Store/21_Sample_Inspection_Checklist.md` (authoritative checklist)
- NAL-007 / `07_Product_Approval_Gate.md`
- NAL-013 / `13_Product_Claim_Verification.md`
- NAL-015 / `15_Rejected_Product_Lessons_Log.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial record template with EXAMPLE ONLY record |

---
