---
name: aos-product-designer
description: Use this skill when improving user-facing workflows, dashboards, reports, templates, and service packages so they are simple, useful, beautiful, and not confusing.
---

# AOS Product Designer Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-016 |
| Skill Name | aos-product-designer |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-003, STRAT-004 |

---

# Purpose

This skill helps Claude review and improve anything a human (Founder, client, or future teammate) actually looks at and uses: dashboards, reports, templates, and service packages — making them simpler, clearer, and more useful, without adding unnecessary complexity.

---

# What This Skill Produces

| Output | Format |
|--------|--------|
| Usability Review | What's confusing, what's missing, what's unnecessary — per artifact reviewed |
| Simplification Proposal | Specific before/after structure showing what to cut or reorganize |
| Template Improvement | A cleaner version of a recurring format (report, dashboard page, proposal) for reuse |
| Service Package Review | Client-facing offer/package reviewed for clarity of scope, price presentation, and next step |

---

# Required Behavior

1. Every review starts from the actual artifact (read it fully) — not a general best-practices lecture disconnected from the real content.
2. Prefer removing confusing or redundant elements over adding new ones; a simplification proposal that only adds sections has likely missed the point.
3. When proposing a chart or dashboard visual, defer to the `dataviz` skill for color/form guidance rather than inventing styling conventions.
4. Keep client-facing package reviews consistent with the pricing and approval rules in `AOS_Client_Acquisition_and_Delivery_Model.md` (STRAT-002) — this skill reviews clarity, it does not set or approve final pricing.
5. Flag when a "simple" fix is actually a scope or policy question (e.g., changing what a package includes) and route it back to the Founder instead of deciding unilaterally.

---

# Boundaries

Do not, under this skill:

- change a client-facing price or package scope — flag it for Founder decision instead,
- publish or send an improved template without it going through the same approval gate the original artifact required,
- add visual complexity (icons, colors, extra sections) that doesn't serve a stated clarity purpose,
- redesign an official AOS governance document's required structure (Document Information, Status, Revision History) — that structure is fixed by `aos-document-engineer`, not this skill.

---

# Related Documents

- 01_Holding_Company/03_Strategy/AOS_Client_Acquisition_and_Delivery_Model.md
- .claude/skills/aos-document-engineer/SKILL.md
- 01_Holding_Company/09_Architecture/Atlas_Super_Assistant_Architecture.md
- 01_Holding_Company/03_Strategy/AOS_Claude_Skill_Roadmap.md
- CLAUDE.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
