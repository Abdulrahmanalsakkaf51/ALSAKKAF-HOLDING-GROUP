---
name: aos-qa-auditor
description: Use this skill when reviewing changed files for AOS quality — Markdown issues, missing register updates, unsafe permissions, broken numbering, and incomplete completion logic — before Founder review.
---

# AOS QA Auditor Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-014 |
| Skill Name | aos-qa-auditor |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-003, STRAT-004 |

---

# Purpose

This skill helps Claude review a set of changed files (from a build session or `git status`/`git diff`) for AOS-specific quality issues before the Founder reviews them — catching problems the Markdown Audit Tool doesn't check, such as missing register updates or numbering conflicts.

---

# QA Checklist

For every changed or new file, check:

| Check | What It Catches |
|-------|------------------|
| Markdown Audit clean | Run `markdown_audit.py`; confirm `Issues found: 0` |
| Register updated | If a new official document/skill/Partner was created, is there a corresponding Knowledge Register row (and Partner Registry row, if applicable)? |
| Document ID uniqueness | Does the new Document ID collide with, or skip, an existing one? |
| Numbering consistency | Does any project, ADR, or KNOW number conflict with an existing entry? |
| Status field present and honest | Is Status set to `Draft` unless the Founder has actually approved it? |
| Approval gates intact | Does any new document/skill remove or weaken an existing Founder-approval requirement? |
| Unsafe permissions | Does any change touch credentials, API keys, or expose private/student data into the public repo? |
| Completion logic | For project records marked complete: are Lessons Learned and a Completion section actually present (per CLAUDE.md Section 5)? |

---

# What This Skill Produces

| Output | Format |
|--------|--------|
| QA Report | Table: file, check, result (Pass/Fail/Warning), note |
| Register Gap List | Specific missing register rows, with the exact row content proposed for Founder review |
| Risk Flags | Any unsafe-permission or approval-gate issue, called out separately and first |

---

# Required Behavior

1. Always run the actual Markdown Audit Tool rather than guessing whether a file would pass.
2. Cross-check every new official document against the Knowledge Register table currently in the file — not from memory — to catch ID collisions.
3. Report findings, don't fix them silently — this skill produces a QA Report for Founder/engineer review, consistent with the AOS Live Build flow's "show the result" step.
4. Rank findings with safety/approval-gate issues first, register gaps second, formatting issues last.
5. If no issues are found, say so plainly rather than manufacturing minor nitpicks.

---

# Boundaries

Do not, under this skill:

- edit files to fix findings without being asked to — report first,
- approve, commit, or push anything,
- treat a clean Markdown Audit result as proof the content is correct — it only proves formatting compliance; register/numbering/logic checks still apply.

---

# Related Documents

- 09_AI_Systems/02_Tools/Markdown_Audit/markdown_audit.py
- .claude/skills/aos-markdown-audit/SKILL.md
- .claude/skills/aos-document-engineer/SKILL.md
- 01_Holding_Company/01_Governance/Knowledge_Register.md
- 01_Holding_Company/03_Strategy/AOS_Claude_Skill_Roadmap.md
- CLAUDE.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
