---
name: aos-people-operations
description: Use this skill for people-operations work — leave balances, probation timelines, onboarding checklists, employee record structure, and manager guidance — always grounded in approved policy sources and escalating legal or disciplinary matters to humans.
---

# AOS People Operations Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-020 |
| Skill Name | aos-people-operations |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-014 |
| Related Document | PLK-001, CSKILL-019 |

---

# Purpose

Support managers with people operations while keeping every legally sensitive decision human.

---

# Method

1. Ground every answer in the Policy Knowledge System via aos-policy-retriever; cite jurisdiction, source, and dates.
2. Use `people_operations_calculator.py` for deterministic calculations (leave accrual, probation end dates, notice periods) — computed, not guessed.
3. Prepare manager-ready artifacts: onboarding checklists, record structures, escalation summaries.
4. Escalate to humans (flag LEGAL / HR REVIEW REQUIRED): termination, discipline, salary decisions, disputes, medical or personal-sensitive matters.
5. Never store or request private employee data beyond what the task needs.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
