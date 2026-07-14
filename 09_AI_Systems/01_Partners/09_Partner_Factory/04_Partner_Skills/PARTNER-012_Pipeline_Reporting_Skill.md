# ALSAKKAF HOLDING GROUP

# Pipeline Reporting Skill

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RPTSKILL-001 |
| Document Type | Partner Skill |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Partner | PARTNER-012 |
| Related Documents | RPTPROF-001, RPTTEST-001, PFT-003 |

---

# 1. Skill Purpose

Produce the weekly pipeline report and Founder briefing from tracker data with computed metrics only.

---

# 2. Inputs / Outputs

| Direction | Item |
|-----------|------|
| Input | Lead, Outreach, and Client Pipeline CSV trackers |
| Output | Pipeline_Report_DATE.md (metrics table, status breakdown, stale leads) |
| Output | Founder_Briefing_DATE.md (headline + decisions waiting) |

---

# 3. Steps

1. `pipeline_reporter.compute_metrics()` reads the trackers and excludes placeholder rows.
2. `write_reports()` writes both Markdown files to the approved output folder.
3. Hand the briefing to Atlas for the morning briefing.

---

# 4. Permission, Cost, Local-First

Level 3 (Prepare). Local tool tier, zero cost, fully offline. No online AI trigger.

---

# 5. Approval Trigger

External publication of any report requires Founder approval.

---

# 6. Test Requirements

`test_pod_tools.py` — PipelineReporterTests must pass (including reading the real company trackers). Status 2026-07-14: passing.

---

# 7. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
