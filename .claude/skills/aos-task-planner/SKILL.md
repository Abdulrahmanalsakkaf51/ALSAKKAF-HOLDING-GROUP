---
name: aos-task-planner
description: Use this skill when planning a working day or week — building bounded, prioritized task plans with Partner assignments, reasons, deadlines, and approval flags — following the Department Supervisor autonomy and escalation rules.
---

# AOS Task Planner Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-018 |
| Skill Name | aos-task-planner |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-013 |
| Related Document | SUPPOL-001, SRS-001 |

---

# Purpose

Plan tasks the way the AOS Department Supervisor does: from real signals only, bounded, prioritized, with every sensitive item escalated to a human.

---

# Method

1. Gather real inputs: goals, deadlines, recurring duties, KPIs, open requests, backlog, unfinished work. No input signal, no task — never invent busywork.
2. Use (or mirror) `09_AI_Systems/02_Tools/Department_Supervisor/` — task_planner.py, priority_engine.py, task_queue.py.
3. Every task gets: Partner, Task, Priority (P1–P3), Deadline, Reason, Approval required, Status.
4. Cap the day (default 8 tasks); defer the rest explicitly.
5. Create follow-up tasks for unfinished work instead of dropping it.

---

# Escalation (always to a human)

Termination, discipline, salary, legal interpretation, external commitments, policy changes, sensitive data access, high-cost activity, irreversible actions.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
