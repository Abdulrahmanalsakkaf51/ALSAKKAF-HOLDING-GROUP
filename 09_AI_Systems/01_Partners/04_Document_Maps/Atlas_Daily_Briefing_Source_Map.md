# ALSAKKAF HOLDING GROUP

# Atlas Daily Briefing Source Map

> "Atlas can only brief the Founder well if it knows which sources matter."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | ASMAP-001 |
| Partner ID | PARTNER-002 |
| Partner Name | Atlas |
| Document Type | Source Map |
| Related Workflow | ABRIEF-001 |
| Related Project | PRJ-002 |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-09 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |

---

# 1. Purpose

This document defines the sources Atlas should use when preparing the Atlas Daily Briefing.

Atlas Daily Briefing helps the Founder understand:

- what is active,
- what needs attention,
- what is delayed,
- what is missing,
- what needs approval,
- what should be done next.

Atlas must not invent information.

Atlas must use known AOS records, approved context, and clear source priority.

---

# 2. Source Priority

Atlas should prioritize sources in this order:

| Priority | Source | Purpose |
|----------|--------|---------|
| 1 | Project Register | Identify active, completed, paused, or future projects |
| 2 | Active Project Records | Understand current project tasks, progress, risks, and next action |
| 3 | Partner Registry | Identify active, designed, proposed, or future Partners |
| 4 | Knowledge Register | Confirm official institutional knowledge |
| 5 | Architecture Decision Records | Confirm approved decisions |
| 6 | Partner Profiles | Understand Partner role and authority |
| 7 | Partner Workflows | Understand active Partner routines |
| 8 | Test Logs | Confirm testing status |
| 9 | Lessons Learned | Learn from completed projects |
| 10 | Founder-approved conversation context | Use recent approved updates from the Founder |

---

# 3. Core Briefing Sources

Atlas should check these sources first.

| Source ID | Source Name | File Location | Use in Daily Briefing |
|-----------|-------------|---------------|------------------------|
| PRJREG-001 | Project Register | 01_Holding_Company/04_Operations/Project_Register.md | Identify active projects |
| PREG-001 | Partner Registry | 09_AI_Systems/01_Partners/Partner_Registry.md | Identify active Partners |
| KNOW-001 | Knowledge Register | 01_Holding_Company/01_Governance/Knowledge_Register.md | Confirm official knowledge status |
| ADR Log | Architecture Decision Log | 01_Holding_Company/01_Governance/Architecture_Decision_Log.md | Confirm recent approved decisions |
| PRJ-002 | Atlas Daily Briefing Project Record | 01_Holding_Company/04_Operations/01_Project_Records/PRJ-002_Build_Atlas_Daily_Briefing_System.md | Track current project progress |
| ABRIEF-001 | Atlas Daily Briefing Workflow | 09_AI_Systems/01_Partners/05_Workflows/Atlas_Daily_Briefing_Workflow.md | Define briefing format |
| ATLAS-001 | Atlas Partner Profile | 09_AI_Systems/01_Partners/01_Partner_Profiles/PARTNER-002_Atlas.md | Confirm Atlas role and restrictions |
| APROMPT-001 | Atlas Prompt | 09_AI_Systems/01_Partners/02_Partner_Prompts/PARTNER-002_Atlas_Prompt.md | Confirm Atlas behavior |
| ATEST-001 | Atlas Test Log | 09_AI_Systems/01_Partners/03_Test_Logs/PARTNER-002_Atlas_Test_Log.md | Confirm Atlas passed foundation tests |
| PRJLESSON-001 | PRJ-001 Lessons Learned | 01_Holding_Company/04_Operations/01_Project_Records/PRJ-001_Lessons_Learned.md | Use lessons from completed Librarian project |

---

# 4. Current Known Project Status Rules

Atlas should classify projects as:

| Status | Meaning |
|--------|---------|
| Active | Project currently needs work |
| Completed | Project achieved its purpose and was closed |
| Paused | Project is temporarily stopped |
| Proposed | Project is suggested but not active |
| Future | Idea is known but not approved as a project |

Atlas must not call a concept an active project unless it appears in the Project Register as Active.

---

# 5. Current Known Partner Status Rules

Atlas should classify Partners as:

| Status | Meaning |
|--------|---------|
| Active | Partner is approved for use within its authority level |
| Designed | Partner has documentation but is not active yet |
| Proposed | Partner idea exists but is not fully designed |
| Future | Partner may be created later |
| Retired | Partner is no longer active |

Atlas must not treat proposed or future Partners as active.

---

# 6. What Atlas Should Extract

For each daily briefing, Atlas should extract:

## From Project Register

- active projects,
- completed projects,
- project owner,
- related Partners,
- project purpose.

## From Active Project Records

- current tasks,
- progress log,
- next recommended action,
- risks,
- missing items.

## From Partner Registry

- active Partners,
- designed Partners,
- proposed Partners,
- Partner authority level,
- related documents.

## From Knowledge Register

- latest approved knowledge,
- active records,
- completed records,
- missing or draft knowledge.

## From ADRs

- recent approved decisions,
- activation decisions,
- governance changes,
- Partner decisions.

## From Workflows

- active routines,
- trigger phrases,
- output format,
- operating rules.

---

# 7. Current Safe Access Position

At this stage, Atlas does not have automatic file access.

Atlas may use:

- Founder-provided updates,
- approved conversation context,
- manual summaries,
- known AOS document structure,
- The Librarian support when available.

Atlas must say clearly when it does not have direct access.

---

# 8. Missing Sources

Atlas does not yet have access to:

- email,
- calendar,
- Excel finance sheets,
- live dashboards,
- website analytics,
- bank data,
- client data,
- supplier data,
- private computer files outside approved AOS scope.

These sources require future access policies and Guardian/security rules.

---

# 9. Daily Briefing Source Checklist

Before preparing a briefing, Atlas should check:

```text
1. What is the active project?
2. What was recently completed?
3. Which Partners are active?
4. What decision was recently approved?
5. What task is next?
6. What information is missing?
7. What risks should the Founder know?
8. What should the Founder focus on today?
```

---

# 10. Source Integrity Rules

Atlas must:

1. Prefer official records over memory.
2. Prefer approved documents over drafts.
3. Prefer active project records over casual ideas.
4. Mention uncertainty clearly.
5. Never invent project status.
6. Never invent revenue, deadlines, or commitments.
7. Never pretend to access systems it cannot access.
8. Recommend source updates when information is missing.

---

# 11. Example Source Use

If the Founder asks:

```text
Atlas, what should I focus on today?
```

Atlas should check:

```text
Project Register
→ Active project is PRJ-002

PRJ-002 record
→ Next task is source map, template, or test log

Partner Registry
→ Atlas and The Librarian are active

Knowledge Register
→ Confirm latest knowledge records

ADR Log
→ Confirm Atlas activation
```

Then Atlas should answer with:

```text
Founder Briefing
Current Focus
Active Projects
Partner Status
Pending Decisions
Follow-Ups
Risks / Missing Information
Recommended Priorities
Next Action
```

---

# 12. Status

Atlas Daily Briefing Source Map is active.

This source map supports PRJ-002 and should be used before creating the Atlas Daily Briefing Template.