# ALSAKKAF HOLDING GROUP

# Skill Routing Standard

> "Every task goes to the role that owns it, the cheapest mode that can do it, and a human where it matters."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | SRS-001 |
| Document Type | Operations Standard |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-014 |
| Related Documents | PRCC-001, PRT-001, POD-001 |

---

# 1. Purpose

Define how AOS routes work across role skills, local tools, and AI modes. Inspired by role-based workflow skill systems (product/CEO reasoning, architecture review, implementation, document engineering, QA, release verification) but AOS-native. No third-party skill packages are installed.

---

# 2. The Routing Chain

```text
Atlas
  ↓
Skill Router (skill_router.py — deterministic keyword rules, first match wins)
  ↓
Task Classifier (role + local tool + mode)
  ↓
Local Tools (Office Toolbelt, Pod Tools, Policy Knowledge, Supervisor, Atlas Runtime)
  ↓
Local Model if needed (Partner Runtime local adapter — Founder-enabled only)
  ↓
Cloud Escalation if allowed (Partner Runtime cloud adapter — env-var keys, Founder-enabled only)
```

---

# 3. Routing Table

| Work | Role skill | Local tool |
|------|-----------|------------|
| Business idea / strategy | aos-ceo-command-center | — (judgment) |
| Architecture / technical design | aos-cto-architect | — (judgment) |
| Document work (DOCX, minutes, letters, official docs) | aos-document-engineer | document_tool.py, office_template_tool.py |
| Spreadsheet work (XLSX, trackers) | aos-office-operator | spreadsheet_tool.py, tracker_tool.py |
| Office work (email drafts, data cleaning, registers) | aos-office-operator | email_draft_tool.py, data_cleaning_tool.py |
| File organization | aos-file-librarian | file_organizer.py |
| People / policy question | aos-people-operations + aos-policy-retriever | policy_retriever.py, people_operations_calculator.py |
| Task planning / daily operations | aos-task-planner | department_supervisor.py |
| Reporting / KPI / briefings | aos-reporting | pipeline_reporter.py |
| Outreach / leads | aos-client-acquisition-engine | outreach_composer.py, research_verifier.py |
| Final output review | aos-qa-auditor | — (judgment) |
| Release / commit / publish | aos-release-manager | — (judgment; Founder approves) |

---

# 4. Mode Selection Rules

1. Deterministic local tool first — always, when one covers the task.
2. Local model second — only if the Founder has enabled a local model server.
3. Economical cloud model for escalation — Founder-enabled, env-var key only.
4. Strong cloud model only for complex tasks (strategy, architecture, long documents).
5. Tasks with no capable enabled mode are reported honestly as blocked — never faked.

---

# 5. Honesty Rule

The router never claims AI capability it does not have. When only deterministic tools are available, outputs are labeled as deterministic. Simulated or scripted outputs are never presented as live AI.

---

# 6. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial standard |
