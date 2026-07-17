# NESTLYRA — Product Candidate Register (Template)

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Template with EXAMPLE ONLY rows. No real candidate exists yet. Real candidate research notes containing supplier names go to private storage per PODS-001.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-008 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Track every product candidate from first idea through the Product Approval Gate (NAL-007), so each candidate's stage, evidence state, and outcome are always visible.

---

# Scope

Covers: the register structure, column guide, and rules. Does not cover: real candidate data (none exists; when it does, sensitive supplier detail lives privately per PODS-001).

---

# 1. Register Table

| Candidate ID | Date Added | Product Name | Category | Target Collection | Gate Stage (NAL-007) | Specs Complete | Dimensions / Materials | Restrictions Checked | Status | Next Action |
|--------------|------------|--------------|----------|-------------------|----------------------|----------------|------------------------|----------------------|--------|-------------|
| EXAMPLE-PC-001 | 2026-07-17 | [Example Only - Not Real] Sample Storage Item | Home organization | Small-Space Essentials | Stage 1 — Candidate | No | UNKNOWN | No | Candidate | Identify supplier candidates (Stage 2) |
| EXAMPLE-PC-002 | 2026-07-17 | [Example Only - Not Real] Sample Wardrobe Item | Wardrobe | Calm Wardrobe | Stage 1 — Candidate | No | UNKNOWN | No | Candidate | Illustrates a second row only — not a real product |

---

# 2. Column Guide

| Column | Rule |
|--------|------|
| Candidate ID | Sequential PC-xxx once real; EXAMPLE- prefix for template rows |
| Gate Stage | The highest fully-completed NAL-007 stage, never a stage in progress |
| Specs Complete | Yes only when every specification field has evidenced values — no [VERIFY BEFORE LAUNCH] markers remaining |
| Dimensions / Materials | Recorded values or UNKNOWN — never estimated |
| Status | Candidate, In Gate, Rejected (with NAL-015 entry), Approved (Founder), Draft-Published |
| Next Action | One concrete next step, always |

---

# 3. Rules

1. Template rows are EXAMPLE ONLY and must be replaced, never treated as data.
2. A candidate's Gate Stage may only move forward when the stage's evidence exists in the referenced register.
3. Rejected candidates keep their row (marked Rejected) and gain a NAL-015 lessons entry.
4. No column may ever contain an invented value; UNKNOWN is always acceptable, guessing never is.

---

# Related Documents

- NAL-007 / `07_Product_Approval_Gate.md`
- NAL-015 / `15_Rejected_Product_Lessons_Log.md`
- NESTLYRA-018 / `../14_NESTLYRA_Store/18_Product_Verification_Checklist.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial template with EXAMPLE ONLY rows |

---
