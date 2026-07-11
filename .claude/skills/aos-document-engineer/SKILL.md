---
name: aos-document-engineer
description: Use this skill when creating or restructuring AOS documents so they have correct Document Information, headings, tables, registers, status, and Markdown Audit compliance.
---

# AOS Document Engineer Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-013 |
| Skill Name | aos-document-engineer |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-003, STRAT-004 |

---

# Purpose

This skill helps Claude produce AOS documents that pass the Markdown Audit Tool on the first run and follow the structural conventions already established across the repository (Document Information block, numbered sections, Related Documents, Revision History).

---

# Required Document Structure

Every official AOS document produced under this skill includes, in order:

1. Title line (`# ALSAKKAF HOLDING GROUP`) and document title.
2. Optional one-line epigraph in `>` blockquote style.
3. `## Document Information` table with at minimum: Document ID, Document Type, Status, Version, Owner, and — where applicable — Related Protocol/Document/System.
4. Numbered `# N. Section Title` sections covering Purpose and the document's actual content.
5. `# Related Documents` section listing every document referenced.
6. `# Revision History` table with at least one row (Version, Date, Changes).

Claude skill files (`SKILL.md`) follow this same shape but additionally require YAML frontmatter with `name` and `description`, per the existing skills in `.claude/skills/`.

---

# Required Behavior

1. Before creating a new document, check the Knowledge Register and the relevant folder for an existing Document ID prefix and take the next available number — never reuse or guess an ID that might collide.
2. Every table must have a header row, a separator row, and every data row with the same column count as the header — this is what the Markdown Audit Tool's broken-table check verifies.
3. Every document must contain a `| Status |` row inside its Document Information table, or the Markdown Audit Tool will flag it as missing.
4. Keep files longer than 10 non-empty lines of real content — very short files are flagged as possibly incomplete.
5. After any Markdown edit, hand off to `aos-markdown-audit` (or run the audit directly) and confirm `Issues found: 0` before considering the document complete.
6. When a new document represents official knowledge, note that it needs a Knowledge Register row — but do not add it without following the standard AOS Live Build flow.

---

# Boundaries

Do not, under this skill:

- assign a Document ID that collides with or skips ahead of the next available number without checking existing usage first,
- mark a document `Approved` or `Active` on Claude's own authority — status changes beyond `Draft` require Founder confirmation,
- delete or overwrite an existing official document's history — use Revision History to record changes instead,
- skip the Markdown Audit step after any Markdown edit.

---

# Related Documents

- 09_AI_Systems/02_Tools/Markdown_Audit/markdown_audit.py
- .claude/skills/aos-markdown-audit/SKILL.md
- 01_Holding_Company/01_Governance/Knowledge_Register.md
- 01_Holding_Company/03_Strategy/AOS_Claude_Skill_Roadmap.md
- CLAUDE.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
