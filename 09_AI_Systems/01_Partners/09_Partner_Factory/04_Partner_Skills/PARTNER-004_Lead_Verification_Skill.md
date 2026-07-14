# ALSAKKAF HOLDING GROUP

# Lead Verification Skill

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RSSKILL-001 |
| Document Type | Partner Skill |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Partner | PARTNER-004 |
| Related Documents | RSPROF-001, RSTEST-001, PFT-003 |

---

# 1. Skill Purpose

Turn raw lead rows into verified, confidence-labeled, duplicate-free records ready for human-approved outreach.

---

# 2. Inputs / Outputs

| Direction | Item |
|-----------|------|
| Input | Lead rows (Lead_Tracker.csv schema) |
| Output | Verification report per lead: confidence, missing fields, evidence gaps, duplicate groups |
| Output | Tracker-level summary: totals by confidence, duplicate count |

---

# 3. Steps

1. Run `research_verifier.verify_tracker()` on the lead tracker.
2. Flag Low-confidence and placeholder rows for human attention.
3. List duplicate groups with the lead IDs involved.
4. Hand High/Medium leads to Atlas for outreach routing.

---

# 4. Permission, Cost, Local-First

Level 3 (Prepare). Local tool tier, zero cost, fully offline. No online AI trigger in v1. Live URL checking requires Founder network approval (future version).

---

# 5. Approval Trigger

None for verification itself. Any change to verification rules is a Founder decision.

---

# 6. Test Requirements

`09_AI_Systems/02_Tools/Pod_Tools/test_pod_tools.py` — ResearchVerifierTests must pass. Status 2026-07-14: passing (13/13 module tests).

---

# 7. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
