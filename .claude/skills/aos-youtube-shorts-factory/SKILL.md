---
name: aos-youtube-shorts-factory
description: Use this skill when planning legal, original YouTube Shorts content — content calendars, hook ideas, captions, titles, and analytics review — from footage the Founder owns, licenses, or has explicit permission to use.
---

# AOS YouTube Shorts Factory Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-009 |
| Skill Name | aos-youtube-shorts-factory |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-001, STRAT-003, STRAT-004 |

---

# Purpose

This skill helps Claude plan a Shorts content workflow using only content the Founder owns outright, has licensed, or has explicit permission to repurpose. It supports the YouTube/Content Company line described in `AOS_Market_Intelligence_and_Financial_Assumptions.md` (STRAT-001 Section 2) as a long-cycle brand and lead-generation asset.

---

# What This Skill Produces

| Output | Format |
|--------|--------|
| Content Calendar | Date, source footage, planned hook, status (Idea / Drafted / Approved / Published) |
| Hook Ideas | Short list of opening lines/visuals designed to stop the scroll, tied to a specific piece of source footage |
| Captions | Draft on-screen text and description copy per Short |
| Titles | 3–5 title options per Short, ranked by clarity (not clickbait) |
| Analytics Review | Table of published Shorts with views, retention notes, and one lesson per entry |
| Copyright Checklist | Per-Short confirmation of footage/music/clip ownership or license status before it is marked ready to publish |

---

# Required Behavior

1. Before planning content around any piece of footage, confirm (or ask the Founder to confirm) that it is owned, licensed, or permitted. If unconfirmed, mark the item "Rights Unconfirmed" and do not advance it in the Content Calendar.
2. Never propose using another creator's content, music, or clips without a stated license or explicit permission.
3. Titles and hooks must accurately represent the Short's content — no misleading claims.
4. Keep the Content Calendar as a planning artifact; actual publishing is a separate, Founder-approved action, consistent with the Outreach/Publish-style approval pattern used elsewhere in AOS (see STRAT-002 Section 5 for the analogous gate).
5. Analytics Review entries should feed `aos-learning-loop` when a real pattern emerges (e.g., a hook style consistently outperforming others).

---

# Boundaries

Do not, under this skill:

- treat any Short as ready to publish while its Copyright Checklist is incomplete,
- fabricate or assume analytics numbers — only tabulate numbers the Founder provides or that exist in a real export,
- publish, schedule, or upload content directly — this skill plans and drafts only,
- use synthetic voices, likenesses, or AI-generated faces of real people without explicit rights/consent.

---

# Related Documents

- 01_Holding_Company/03_Strategy/AOS_Market_Intelligence_and_Financial_Assumptions.md
- 01_Holding_Company/03_Strategy/AOS_Inspiration_Register.md
- 01_Holding_Company/03_Strategy/AOS_Claude_Skill_Roadmap.md
- 01_Holding_Company/01_Governance/Knowledge_Register.md
- CLAUDE.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
