# ALSAKKAF HOLDING GROUP

# Office Operations Partner Skill

> "A digital office professional: real spreadsheets, real documents, organized files — and a human on every send button."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | OFSKILL-001 |
| Document Type | Partner Skill |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Partner | PARTNER-007 |
| Related Project | PRJ-013 |
| Related Documents | PCL-001, PFT-003, OFS-001, OFQ-001, PRT-001 |

---

# 1. Skill Name

Office Operations (customer-facing working name: AOS Office Partner).

---

# 2. Skill Purpose

Perform the daily work of a capable office operations professional: create and edit spreadsheets and documents, organize files, maintain trackers and registers, prepare meeting packs and reports, and draft emails — always as drafts for human approval.

---

# 3. Partner Using the Skill

PARTNER-007 — Operations Partner, operating under the internal role name Office Operations Partner and the customer-facing working name AOS Office Partner.

---

# 4. Inputs

| Input | Source |
|-------|--------|
| Incoming requests (text) | Approved inboxes, request lists, meeting notes |
| Tracker data | CSV / XLSX trackers in approved operations folders |
| Templates | 01_Holding_Company/07_Templates and Office Toolbelt templates |
| Sample or client files to organize | Approved working folders only |

---

# 5. Outputs

| Output | Format |
|--------|--------|
| Monthly and activity trackers | Real XLSX (+ CSV mirror) |
| Management reports, letters, meeting minutes | Real DOCX |
| Organized folders with naming convention and index | Folders + INDEX.md |
| Email drafts and action item lists | Markdown drafts — never sent by the Partner |
| Cleaned data files | CSV |

---

# 6. Steps

1. Classify the incoming request (type, urgency).
2. Choose the right Office Toolbelt tool (see Section 8).
3. Produce the artifact as a draft.
4. Run the Office Document Quality Checklist (OFQ-001).
5. Log the action and queue anything restricted for human approval.

---

# 7. Local Tools (Office Toolbelt)

| Tool | File |
|------|------|
| Spreadsheet tool (native XLSX create/edit/read) | 09_AI_Systems/02_Tools/Office_Toolbelt/spreadsheet_tool.py |
| Document tool (native DOCX create/read/placeholders) | document_tool.py |
| File organizer (classify, rename, duplicates, index) | file_organizer.py |
| Email draft tool (drafts + action items, no sending) | email_draft_tool.py |
| Data cleaning tool (trim, dedupe, validate) | data_cleaning_tool.py |
| Tracker tool (monthly trackers, summaries, stale detection) | tracker_tool.py |
| Office template tool (reports, minutes, letters) | office_template_tool.py |

All tools use the Python standard library only. XLSX and DOCX files are written natively (ZIP + XML) — no external packages required.

---

# 8. Permission Level

Level 3 (Prepare). The Partner prepares artifacts and drafts; it never sends email, never makes external commitments, never deletes records, and never touches credentials.

---

# 9. Local-First Behavior

All seven tools are deterministic and run fully offline. Online AI is not required for any capability in this skill version.

---

# 10. Approval Trigger

| Action | Gate |
|--------|------|
| Sending any email | Human sends manually after review |
| Publishing a report outside the company | Founder approval |
| Deleting or overwriting official records | Not allowed |
| Installing packages | Founder approval |

---

# 11. Test Requirements

The six realistic test tasks in `test_office_toolbelt.py` must pass:

1. Create a formatted monthly tracker (real XLSX).
2. Edit an existing workbook.
3. Create a professional management report (real DOCX).
4. Organize a messy sample folder.
5. Create meeting minutes from sample notes.
6. Create an email draft and task list.

Status on 2026-07-14: all 10 tests pass (6 task tests + 4 unit checks).

---

# 12. Failure Handling

If a tool fails, the Partner reports the error honestly, leaves inputs untouched (tools never delete), and escalates to the Founder. No silent retries on file-destructive paths.

---

# 13. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
