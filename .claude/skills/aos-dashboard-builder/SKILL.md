---
name: aos-dashboard-builder
description: Use this skill when building local dashboard-style reports, KPI tables, chart plans, source notes, or CEO reporting pages from existing AOS data, without requiring any online AI service for basic numbers.
---

# AOS Dashboard Builder Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-008 |
| Skill Name | aos-dashboard-builder |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-003, STRAT-004 |

---

# Purpose

This skill helps Claude produce local, file-based dashboard reports — KPI tables, chart plans, and CEO reporting pages — built entirely from data already recorded inside AOS (registers, strategy documents, project records). It does not require network access or a paid AI/data service to compute basic numbers, tables, or plans.

---

# What This Skill Produces

| Output | Format |
|--------|--------|
| KPI Table | Metric, current value, source document, last-updated date, trend note |
| Chart Plan | Chart type, axes/series definition, data source, and (if using the `dataviz` skill) styling notes — not a rendered chart by itself |
| Source Notes | Explicit list of where every number came from, so nothing looks more authoritative than it is |
| Missing-Data Warning | Explicit callout when a KPI cannot be computed because the underlying record doesn't exist yet |
| CEO Reporting Page | Combined page: KPI Table + short narrative + Missing-Data Warnings, formatted per `aos-document-engineer` structure |

---

# Required Behavior

1. Every number in a dashboard must trace to a specific file/section in the repository. If it can't, it goes in the Missing-Data Warning list instead of being estimated silently.
2. When an actual chart/visualization is being built (not just planned), invoke the `dataviz` skill for form and color guidance before writing chart code.
3. Prefer local computation (reading and tabulating existing Markdown/data files) over assuming a live data feed exists — AOS has no live feeds configured as of this version.
4. Label every dashboard page with a "data as of" date so staleness is visible.
5. Keep KPI tables small and readable — a dashboard that tries to show everything shows nothing clearly.

---

# Boundaries

Do not, under this skill:

- fabricate a KPI value when the source data doesn't exist,
- call any paid or online data/AI service without Founder approval of that specific tool (CLAUDE.md Section 5, "New tool" row),
- present a chart plan as a finished, validated report — it is a plan until rendered and reviewed,
- store credentials or API keys for any data source inside a dashboard file.

---

# Related Documents

- 01_Holding_Company/09_Architecture/Atlas_Super_Assistant_Architecture.md
- 01_Holding_Company/03_Strategy/AOS_Claude_Skill_Roadmap.md
- 01_Holding_Company/03_Strategy/AOS_Inspiration_Register.md
- 01_Holding_Company/01_Governance/Knowledge_Register.md
- CLAUDE.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
