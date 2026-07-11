---
name: aos-live-build
description: Use this skill when making structured AOS repository changes that require planning, editing, auditing, and Founder approval.
---

# AOS Live Build Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-001 |
| Skill Name | aos-live-build |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-10 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |

---

# Instructions

When using this skill, follow the AOS Live Build Protocol.

## Required Flow

1. Inspect the relevant files first.
2. Explain the proposed change briefly.
3. Do not edit unrelated files.
4. Make the smallest safe change.
5. Keep AOS numbering consistent.
6. Update required registers when official records are created.
7. Run Markdown Audit after Markdown changes.
8. Summarize changed files.
9. Do not commit unless the Founder approves.
10. Do not push unless the Founder approves.

## Required Safety

Do not:

- delete files,
- rename official folders,
- commit automatically,
- push automatically,
- add credentials,
- expose sensitive data,
- change project numbering without approval,
- activate Partners without AOS activation rules.

## AOS Quality Rule

Official AOS work is not complete until:

- the file is saved,
- the relevant register is updated,
- the Markdown Audit passes,
- the Founder approves the change.