---
name: aos-policy-retriever
description: Use this skill when answering company policy or employment-rule questions — retrieving approved policy knowledge with jurisdiction, source, effective date, and staleness warnings, and flagging LEGAL / HR REVIEW REQUIRED where appropriate.
---

# AOS Policy Retriever Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-019 |
| Skill Name | aos-policy-retriever |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-014 |
| Related Document | PLK-001 |

---

# Purpose

Give managers controlled access to policy and employment-rule knowledge without making legal decisions.

---

# Method

1. Retrieve from the Policy Knowledge System (`09_AI_Systems/02_Tools/Policy_Knowledge/policy_retriever.py` and `policy_index.json`) — approved company policy first, then current official legal source references.
2. Every answer includes: jurisdiction, source, official source URL, effective date, last verified date, and SOURCE SNAPSHOT DATE.
3. Warn when information may be stale (past `verify_by` date). Offline answers always show the snapshot date.
4. Never make a final legal decision. Flag LEGAL / HR REVIEW REQUIRED for: termination, discipline, disputes, contract interpretation, anything ambiguous.
5. Never copy long passages of copyrighted legal text — summaries plus source metadata only.
6. Network freshness checks require Founder approval.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
