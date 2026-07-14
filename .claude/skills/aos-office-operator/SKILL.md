---
name: aos-office-operator
description: Use this skill when doing office operations work — creating or editing XLSX trackers and workbooks, drafting DOCX reports and letters, drafting emails, cleaning CSV data, or maintaining registers — using the local Office Toolbelt with no external packages.
---

# AOS Office Operator Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-017 |
| Skill Name | aos-office-operator |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-013 |
| Related Document | OFSKILL-001, OFS-001, OFQ-001 |

---

# Purpose

Perform office operations work the way the AOS Office Partner (PARTNER-007) does: real local files, deterministic tools, drafts for human approval.

---

# Tooling

Use the Office Toolbelt at `09_AI_Systems/02_Tools/Office_Toolbelt/` (standard library only — openpyxl/python-docx are NOT installed; XLSX and DOCX are written natively):

| Need | Tool |
|------|------|
| XLSX create/edit/read | spreadsheet_tool.py |
| Monthly/activity trackers | tracker_tool.py |
| DOCX reports, minutes, letters | document_tool.py, office_template_tool.py |
| Email drafts + action items | email_draft_tool.py |
| CSV cleaning/validation | data_cleaning_tool.py |
| Folder organization | file_organizer.py |

---

# Rules

1. Run the Office Document Quality Checklist (OFQ-001) on every artifact.
2. Numbers are computed from real data, never invented.
3. Never send email — drafts only, labeled DRAFT — NOT SENT.
4. Never delete files. Never touch credentials or private data.
5. Follow the Office File Management Standard (OFS-001) for naming.
6. Do not install packages; the toolbelt needs none.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
