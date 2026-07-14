---
name: aos-file-librarian
description: Use this skill when organizing folders, applying the AOS file naming convention, detecting duplicate files, archiving, or building folder indexes — never deleting anything.
---

# AOS File Librarian Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-022 |
| Skill Name | aos-file-librarian |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-013 |
| Related Document | OFS-001 |

---

# Purpose

Organize business files per the Office File Management Standard (OFS-001) safely.

---

# Method

1. Use `09_AI_Systems/02_Tools/Office_Toolbelt/file_organizer.py`: classify by category, apply `YYYY-MM-DD_Category_Description.ext`, detect duplicates by content hash, generate INDEX.md.
2. Never delete files. Duplicates are reported to a human, never auto-removed.
3. Moves stay inside the folder being organized.
4. Official AOS records, registers, and numbered folders are never reorganized by tools — humans only.
5. Report what moved, what is duplicated, and what needs a human decision.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
