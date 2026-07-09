# ALSAKKAF HOLDING GROUP

# Markdown Audit Tool Requirements

> "Before AOS can automate documents, AOS must be able to trust its documents."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MAREQ-001 |
| Tool Name | Markdown Audit Tool |
| Document Type | Tool Requirements |
| Related Project | PRJ-003 |
| Status | Approved |
| Version | 1.0 |
| Date | 2026-07-10 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |

---

# 1. Purpose

This document defines the requirements for the Markdown Audit Tool.

The tool will scan Markdown files inside ALSAKKAF HOLDING GROUP and report possible formatting or documentation problems.

The tool must be read-only in its first version.

The tool must not edit, delete, commit, or push files.

---

# 2. Reason for the Tool

During AOS documentation work, some Markdown files had formatting issues caused by unclosed code blocks, incomplete tables, and long pasted sections.

These issues can make official documents difficult to read and can damage the quality of AOS records.

The Markdown Audit Tool will help the Founder review files before committing them to GitHub.

---

# 3. Tool Scope

The Markdown Audit Tool should scan Markdown files with the `.md` extension.

The tool should check files inside the repository folder.

The tool should ignore technical folders that should not be scanned.

| Folder / Item | Reason to Ignore |
|---------------|------------------|
| .git | Git internal files |
| __pycache__ | Python cache files |
| .venv | Python virtual environment |
| venv | Python virtual environment |
| node_modules | JavaScript dependency files |

---

# 4. Required Checks

The first version of the Markdown Audit Tool should check for the following issues.

| Check ID | Check Name | Purpose | Required |
|---------|------------|---------|----------|
| MD-AUDIT-001 | Unclosed Code Blocks | Detect code blocks that start but do not close | Yes |
| MD-AUDIT-002 | Possible Broken Tables | Detect table rows that may have inconsistent column counts | Yes |
| MD-AUDIT-003 | Missing Document Information | Detect files missing a Document Information section | Yes |
| MD-AUDIT-004 | Duplicate Knowledge IDs | Detect repeated KNOW IDs inside Knowledge Register | Yes |
| MD-AUDIT-005 | Empty or Very Short Files | Detect files that may be incomplete | Yes |
| MD-AUDIT-006 | Missing Project Tasks | Detect project records missing a Project Tasks section | Yes |
| MD-AUDIT-007 | Missing Progress Log | Detect project records missing a Progress Log section | Yes |
| MD-AUDIT-008 | Missing Status Field | Detect important documents missing a Status field | Yes |

---

# 5. Output Requirements

The tool should show clear output in PowerShell.

For each issue, the tool should show:

| Output Item | Description |
|-------------|-------------|
| File Path | Which file has the issue |
| Issue Type | What kind of issue was detected |
| Line Number | Where the issue may exist, if possible |
| Message | Clear explanation of the issue |
| Severity | Info, Warning, or Error |

---

# 6. Severity Levels

The tool should classify issues using three severity levels.

| Severity | Meaning |
|----------|---------|
| Info | Something to review but not urgent |
| Warning | Possible issue that should be checked |
| Error | Serious issue that may break the document |

---

# 7. First Version Rules

The first version must follow these rules:

| Rule | Requirement |
|------|-------------|
| Read-only | The tool must not edit files |
| Local only | The tool runs locally on the Founder’s PC |
| No auto-fix | The tool only reports issues |
| No Git actions | The tool does not commit or push |
| Simple output | Results appear clearly in PowerShell |
| Safe by default | The tool should not damage documents |

---

# 8. Tool Location

The tool should be stored inside:

| Item | Location |
|------|----------|
| Tool Folder | 09_AI_Systems/02_Tools/Markdown_Audit |
| Requirements File | 09_AI_Systems/02_Tools/Markdown_Audit/Markdown_Audit_Tool_Requirements.md |
| Future Prototype | 09_AI_Systems/02_Tools/Markdown_Audit/markdown_audit.py |
| Future Test Log | 09_AI_Systems/02_Tools/Markdown_Audit/Markdown_Audit_Test_Log.md |

---

# 9. Success Criteria

The Markdown Audit Tool requirements are successful if they clearly define:

| Criteria No. | Success Criteria |
|-------------|------------------|
| 1 | What the tool should check |
| 2 | What the tool must not do |
| 3 | Where the tool should be stored |
| 4 | What output the tool should produce |
| 5 | Which issues are most important |
| 6 | How severity should be classified |
| 7 | Why the tool matters to AOS |
| 8 | How the first version remains safe |

---

# 10. Future Improvements

Future versions may include:

| Future Feature | Purpose |
|----------------|---------|
| Markdown preview validation | Check if files render correctly |
| Auto-fix suggestions | Suggest exact fixes without applying them |
| Link checking | Detect broken internal file references |
| Knowledge Register validation | Check ID sequence and missing records |
| Project Register validation | Check project statuses and related files |
| Partner Registry validation | Check Partner IDs and status consistency |
| HTML report | Generate a readable audit report |
| Git pre-commit check | Run audit before commits |

These future improvements require separate approval.

---

# 11. Status

The Markdown Audit Tool Requirements are approved.

Recommended next action:

Build the first read-only Python prototype.