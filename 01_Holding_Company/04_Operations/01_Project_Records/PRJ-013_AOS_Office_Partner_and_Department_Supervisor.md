# ALSAKKAF HOLDING GROUP

# PRJ-013 — AOS Office Partner and Department Supervisor

> "A digital office professional and the supervisor who plans its day — real files, real tests, human approvals."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-013 |
| Document Type | Project Record |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Approved By | Founder (build); Partner activation requires separate Founder approval |
| Related System | AOS |
| Related Projects | PRJ-006, PRJ-012, PRJ-014 |
| Related Documents | PREG-001, PCL-001, PRT-001 |

---

# 1. Objective

1. Turn the existing Proposed PARTNER-007 (Operations Partner) into the AOS Office Partner — a digital office operations professional that genuinely creates and edits real XLSX workbooks, DOCX documents, organized folders, trackers, and email drafts on this machine, with no external packages.
2. Build the AOS Department Supervisor — a bounded planning engine that reads department goals, deadlines, backlog, and KPIs, and proposes a prioritized daily task plan with Partner assignments and human approval gates.

---

# 2. Key Environment Fact

openpyxl, python-docx, and Pillow are NOT installed, and packages are not installed without Founder approval. Therefore the Office Toolbelt writes native XLSX and DOCX files directly (both are ZIP + XML formats) using only the Python standard library. This is honest, dependency-free, and repeatable.

---

# 3. Scope

| Deliverable | Location |
|-------------|----------|
| Office Toolbelt (7 tools + tests) | 09_AI_Systems/02_Tools/Office_Toolbelt/ |
| Office Operations Partner Skill | 09_AI_Systems/01_Partners/09_Partner_Factory/04_Partner_Skills/ |
| Office File Management Standard | 09_AI_Systems/02_Tools/Office_Toolbelt/Office_File_Management_Standard.md |
| Office Document Quality Checklist | 09_AI_Systems/02_Tools/Office_Toolbelt/Office_Document_Quality_Checklist.md |
| Department Supervisor prototype | 09_AI_Systems/02_Tools/Department_Supervisor/ |
| PARTNER-007 lifecycle documents | Partner Factory folders (see PRJ-014 pod records) |

---

# 4. Office Partner Test Plan (all local, all real files)

| Test | Proves |
|------|--------|
| 1. Create a formatted monthly tracker | Real XLSX creation with headers, styling, columns |
| 2. Edit an existing workbook | Reading and appending rows to XLSX |
| 3. Create a professional management report | Real DOCX with headings, paragraphs, tables |
| 4. Organize a messy sample folder | Classification, naming convention, index |
| 5. Create meeting minutes from sample notes | DOCX from structured notes |
| 6. Create an email draft and task list | Draft + action items, never sent |

---

# 5. Supervisor Autonomy Rule

The Supervisor may autonomously create and assign tasks only when the task is inside approved department scope, within policy and permissions, within budget, reversible, and not legally sensitive. It must escalate: termination, discipline, salary decisions, legal interpretations, external commitments, policy changes, sensitive data access, high-cost activity, and irreversible actions. It must not invent busywork.

---

# 5B. Project Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Build the seven-tool Office Toolbelt (native XLSX/DOCX, stdlib only) | Done |
| 2 | Pass the six realistic Office Partner task tests | Done |
| 3 | Write skill, file standard, and quality checklist | Done |
| 4 | Build Department Supervisor prototype with policy and tests | Done |
| 5 | PARTNER-007 lifecycle documents | Done |
| 6 | Founder prompt-level tests and activation decision | Pending Founder |

---

# 6. Progress Log

| Date | Update |
|------|--------|
| 2026-07-14 | Project created. Office Toolbelt, standards, skill, Supervisor prototype, and tests built. Awaiting Founder review. |

---

# 7. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial project record |
