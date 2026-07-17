# NESTLYRA — Partner Error and Correction Log (Template)

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Template with EXAMPLE ONLY rows. The Partner is proposed and not activated (NAL-005), so no real error can exist yet — but the log exists first, so the discipline exists from the first test.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-027 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Record every case where the Partner gets something wrong or proposes something incorrect, together with the Founder's correction and the follow-up change — so the Partner improves through recorded, Founder-controlled correction, never through silent self-modification. This log feeds the Company Factory learning record (NESTLYRA is Internal Build 001; the Company Factory record itself is a later sub-checkpoint) and mirrors the Partner Learning System discipline.

---

# Scope

Covers: the log structure, error categories, and logging rules, applying to synthetic testing and any eventual live operation alike. Does not cover: the Company Factory record itself (later sub-checkpoint) or Partner activation (NAL-005 activation path).

---

# 1. The Log (Template)

| Date | Partner Skill Involved | What the Partner Got Wrong or Proposed Incorrectly | Founder Correction | Category | Lesson | Follow-Up Change Made |
|------|------------------------|-----------------------------------------------------|---------------------|----------|--------|------------------------|
| [Example Only - Not Real] 2026-07-17 | Order Control | In a synthetic test, treated a pending payment as paid and prepared a supplier order for approval | Founder rejected the prepared order; payment state must be verified as paid before step 8 of NAL-018 | Rule application error | Payment state is a hard precondition, not a formality | NAL-018 workflow check tightened in the Partner's test prompt (documented, Founder-approved) |
| [Example Only - Not Real] 2026-07-17 | Customer Care Drafting | Draft reply included a delivery estimate taken from the store's provisional settings | Founder struck the estimate; provisional rates and times are never quotable (U-15) | Unverified information used | Store display settings are not evidence | Saved-reply library rule added: no time or cost figure without a verified register reference |

---

# 2. Error Categories

| Category | Meaning |
|----------|---------|
| Rule application error | A defined rule (NAL-006, NAL-018, NAL-019...) existed and was misapplied |
| Unverified information used | A guess, provisional value, or unknown treated as fact (STRAT-019 violation class) |
| Permission boundary approach | A prepared action drifted toward a forbidden action before being caught |
| Classification error | Wrong category for an inquiry, exception, or candidate |
| Calculation error | Wrong math or wrong inputs in a landed-cost or margin calculation |
| Omission | A required step, register row, or flag was skipped |
| Other | Anything else — honestly described |

---

# 3. Logging Rules

1. Every Founder correction of Partner output gets a row — in synthetic testing and live operation alike. Small corrections are the most valuable rows.
2. The Partner never edits its own rules, prompt, or this log's lessons into practice by itself. A follow-up change is made only through a documented, Founder-approved edit (no silent self-modification — the Partner Learning System discipline).
3. A "permission boundary approach" row is also an incident under NAL-006 enforcement rule 3 and triggers a Guardian review before the Partner is used again.
4. Rows are never deleted or softened afterward; the log is an asset, and a growing log early on is expected and healthy.
5. Recurring rows in the same category feed the Weekly report (NAL-026 section 3, row 8) and become improvement proposals for the Founder — proposals, never self-applied fixes.
6. This log's patterns, mistakes, and corrections are the raw material for the Company Factory learning record when that later sub-checkpoint builds it.

---

# Related Documents

- NAL-005 / `05_Commerce_Operations_Partner_Spec.md`
- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-018 / `18_First_20_Orders_Control.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-026 / `26_Reporting_Specifications.md`
- STRAT-019 / `../../03_Strategy/AOS_Outreach_Writing_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial template — log structure, seven error categories, six logging rules, EXAMPLE ONLY rows |

---
