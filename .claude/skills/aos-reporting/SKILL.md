---
name: aos-reporting
description: Use this skill when preparing pipeline reports, KPI summaries, or Founder briefings from tracker data — counted metrics only, placeholder rows excluded, stale items flagged, zero reported honestly.
---

# AOS Reporting Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-021 |
| Skill Name | aos-reporting |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-014 |
| Related Document | RPTSKILL-001, RPTPROMPT-001 |

---

# Purpose

Report the way the Reporting Partner (PARTNER-012) does: honest, counted, decision-oriented.

---

# Method

1. Compute metrics with `09_AI_Systems/02_Tools/Pod_Tools/pipeline_reporter.py` — never estimate.
2. Exclude placeholder/example rows and say so in the report.
3. Zero is a valid headline ("no real leads yet") when true.
4. Structure: what happened → what it means → at most one recommended action with its trade-off. The decision is human.
5. Flag stale items as decisions waiting (follow up or archive).
6. Nothing publishes externally without Founder approval.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
