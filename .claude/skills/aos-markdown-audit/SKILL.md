---
name: aos-markdown-audit
description: Use this skill after editing Markdown files in the ALSAKKAF HOLDING GROUP repository to run and interpret the Markdown Audit Tool.
---

# AOS Markdown Audit Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-002 |
| Skill Name | aos-markdown-audit |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-10 |
| Owner | Abdulrahman Alsakkaf |
| Related Tool | Markdown Audit Tool |
| Related Project | PRJ-003 |

---

# Instructions

Use this skill after Markdown files are created or edited.

## Audit Command

Run the Markdown Audit Tool from the repository root using:

`py 09_AI_Systems\02_Tools\Markdown_Audit\markdown_audit.py`

## Expected Result

The expected clean result is:

| Item | Expected |
|------|----------|
| Issues found | 0 |
| Errors | 0 |
| Warnings | 0 |
| Info | 0 |

## If Issues Appear

If issues appear:

1. List the affected files.
2. Identify whether each issue is an error, warning, or info item.
3. Fix errors first.
4. Fix warnings only when they are real.
5. Run the audit again.
6. Do not commit until the audit result is clean or the Founder approves an exception.

## Important Rule

The Markdown Audit Tool is read-only.

It must not edit, delete, commit, or push files.