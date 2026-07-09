# ALSAKKAF HOLDING GROUP

# PRJ-003 — Build Markdown Audit Tool

> "AOS documents must be readable, complete, and safe before automation touches them."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-003 |
| Project Name | Build Markdown Audit Tool |
| Project Type | Quality / Technology Project |
| Status | Active |
| Version | 1.0 |
| Date Created | 2026-07-10 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Model | PRJMODEL-001 |

---

# 1. Purpose

PRJ-003 exists to build a simple Markdown Audit Tool for ALSAKKAF HOLDING GROUP.

The tool will help check important Markdown files for formatting problems before they are committed to GitHub.

This project was created because several documents had broken formatting caused by unclosed code blocks and incomplete tables.

---

# 2. Project Goal

The goal of PRJ-003 is to create a simple local tool that can scan `.md` files and report possible documentation problems.

The first version should check for:

| Check | Purpose |
|------|---------|
| Unclosed code blocks | Detect when a Markdown code block starts but does not close |
| Broken tables | Detect table rows that may not match the table header |
| Missing Document Information | Detect documents that may not have a document information section |
| Duplicate Knowledge IDs | Detect repeated Knowledge Register IDs |
| Empty or very short files | Detect files that may be incomplete |
| Project record completeness | Detect whether project records include tasks and progress log sections |

---

# 3. Why This Project Matters

AOS depends on documentation.

If documents break, the institution becomes confused.

The Markdown Audit Tool will help protect:

| Area | Protection |
|------|------------|
| AOS documents | Keeps files readable |
| Knowledge Register | Helps avoid duplicate or broken records |
| Project records | Helps detect incomplete project files |
| Partner records | Helps protect Partner documentation |
| GitHub commits | Reduces mistakes before pushing |
| Future AI tools | Gives Codex, Claude, and future Partners cleaner files to work with |

---

# 4. Scope

PRJ-003 includes:

| Scope Item | Description |
|-----------|-------------|
| Tool plan | Define what the audit tool should check |
| Python prototype | Build a simple local Python audit tool |
| Test folder scan | Scan all `.md` files in the repository |
| Report output | Show file paths and detected issues |
| Test log | Record whether the tool works |
| Lessons learned | Capture what the company learns |

---

# 5. Out of Scope

PRJ-003 does not include:

| Out of Scope Item | Reason |
|-------------------|--------|
| Auto-fixing files | Too risky for the first version |
| Editing official documents automatically | Requires future approval rules |
| Codex automation | Codex is not active on current PC |
| Claude integration | Not needed for the first version |
| Dashboard development | Should be a future project |
| Microsoft Teams or email automation | Not related to Markdown quality |

---

# 6. Authority Rules

The Markdown Audit Tool may:

| Allowed Action | Meaning |
|---------------|---------|
| Read Markdown files | Scan `.md` files for possible issues |
| Report problems | Show file path, issue type, and line number if possible |
| Suggest review | Recommend which files need manual checking |

The Markdown Audit Tool may not:

| Restricted Action | Reason |
|-------------------|--------|
| Edit files automatically | Founder approval is required before changes |
| Delete files | Protects institutional records |
| Commit or push changes | Git actions remain manual |
| Decide official status | Human review is required |

---

# 7. Deliverables

| Deliverable | Description | Status |
|-------------|-------------|--------|
| Markdown Audit Tool Requirements | Defines what the tool should check | Completed |
| Markdown Audit Tool Prototype | Local Python tool | Not Started |
| Markdown Audit Test Log | Records tool test results | Not Started |
| Markdown Audit Lessons Learned | Captures what the company learns | Not Started |
| Project Completion Decision | Decides whether PRJ-003 is complete | Not Started |

---

# 8. Project Tasks

| Task ID | Task | Status |
|---------|------|--------|
| PRJ-003-T001 | Create PRJ-003 project record | Completed |
| PRJ-003-T002 | Add PRJ-003 to Project Register | Completed |
| PRJ-003-T003 | Create Markdown Audit Tool Requirements | Completed |
| PRJ-003-T004 | Build Markdown Audit Tool prototype | Not Started |
| PRJ-003-T005 | Test Markdown Audit Tool | Not Started |
| PRJ-003-T006 | Record test results | Not Started |
| PRJ-003-T007 | Capture lessons learned | Not Started |
| PRJ-003-T008 | Complete PRJ-003 or plan next version | Not Started |

---

# 9. Success Criteria

PRJ-003 is successful if:

| Criteria No. | Success Criteria |
|-------------|------------------|
| 1 | The tool can scan Markdown files |
| 2 | The tool can detect unclosed code blocks |
| 3 | The tool can identify possible broken tables |
| 4 | The tool can report files with missing Document Information |
| 5 | The tool can detect duplicate Knowledge IDs |
| 6 | The tool does not edit files automatically |
| 7 | The tool gives clear output |
| 8 | The tool helps the Founder review files faster |
| 9 | Test results are documented |
| 10 | Lessons learned are captured |

---

# 10. Risks

| Risk | Response |
|------|----------|
| Tool may report false positives | Treat results as review suggestions, not final truth |
| Tool may miss some formatting problems | Improve in future versions |
| Tool may become too complex | Start simple |
| Founder may rely on tool too much | Human review remains required |
| Auto-fixing may be tempting | Keep v1 read-only only |

---

# 11. Progress Log

| Date | Progress |
|------|----------|
| 2026-07-10 | PRJ-003 created to build the Markdown Audit Tool. |
| 2026-07-10 | Markdown Audit Tool Requirements created as MAREQ-001. |


---

# 12. Recommended Next Action

Create the Markdown Audit Tool Requirements document.

This requirements document will define exactly what the tool should check before coding begins.