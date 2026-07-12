# ALSAKKAF HOLDING GROUP

# Guardian Cybersecurity Risk Review Skill

> "Partners gain approved skills, not unlimited abilities."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | GSKILL-001 |
| Document Type | Partner Skill |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-006 |
| Related Documents | PFT-003, GUARD-001, GPROMPT-001, GTEST-001 |

---

# 1. Purpose

This document defines the Guardian Cybersecurity Risk Review Skill, using the Partner Skill Template (PFT-003), following the Partner Skill Model in APFA-001 Section 7.

---

# 2. Skill Purpose

Allow Guardian to review proposed tools, workflows, automations, files, integrations, outreach systems, dashboards, and Partner permissions for cybersecurity and digital trust risks, producing a structured, documented recommendation for Founder review.

This skill is defensive only, documentation/planning only. It performs no hacking, exploitation, scanning, credential testing, or unauthorized access of any kind.

---

# 3. Partner Using the Skill

| Field | Entry |
|-------|-------|
| Partner ID | PARTNER-016 |
| Partner Name | Guardian |

---

# 4. Inputs

| Input | Description |
|-------|--------------|
| Subject description | The tool, workflow, automation, file, integration, dashboard, or Partner permission set being reviewed, described in plain language |
| Public/vendor documentation | Publicly available documentation about the subject, if applicable (never live access to the subject system itself) |
| Data category involved | What kind of data the subject would touch (e.g., internal documents, public content, client-facing data), stated by the requester |
| Related AOS documents | Relevant Partner Registry rows, profiles, or architecture documents needed for context |

---

# 5. Outputs

| Output | Format |
|--------|--------|
| Risk Review | Structured document: Summary, Risks Identified table (Risk / Likelihood / Impact / Mitigation / Severity), Data Sensitivity, Recommendation, Approval Needed |
| Risk Register Entry | Row suitable for a running risk register: Risk, likelihood, impact, current mitigation, owner, status |

---

# 6. Steps

1. Confirm the subject is something Guardian may review under its Data Access Rules (no direct handling of credentials or restricted data).
2. Gather the subject description, any public/vendor documentation, and the data category involved.
3. Identify specific risks: what could go wrong, how likely, and how bad if it happened.
4. Propose a proportionate mitigation for each risk (not blanket rejection).
5. Assign a severity (Low / Medium / High) to each risk.
6. State a clear recommendation: Proceed / Proceed with conditions / Do not proceed / Escalate to Founder.
7. If any risk is High severity, stop and escalate to the Founder immediately per the Guardian Prompt's escalation rule, instead of only noting it in the output.
8. Return the structured Risk Review to the requester (Atlas or the Founder directly).

---

# 7. Permission Level

| Field | Entry |
|-------|-------|
| Minimum Authority Level required | Level 2 (Recommend) |
| Notes | This skill only recommends; it never implements, connects, or approves the reviewed subject itself |

---

# 8. Cost Behavior

| Field | Entry |
|-------|-------|
| Default model tier | Local tool/document review first, cheap-to-standard online model (Claude session) for drafting |
| Trigger for higher tier | None expected at this stage; any recurring paid tool use requires a separate Partner_Budget_Approval_Template.md |

---

# 9. Local-First Behavior

Guardian first checks existing AOS documents (Partner Registry, related Partner profile, Knowledge Register, architecture documents) for prior review or relevant policy before drafting new analysis, consistent with ADDA-001 local-first routing.

---

# 10. Online AI Trigger

This skill may use an online AI (Claude session) to help structure and draft the Risk Review text once inputs are gathered, provided no Restricted-tier data (credentials, private student/client data) is included in the request. If Restricted-tier data would be needed to complete the review, Guardian escalates to the Founder instead of proceeding.

---

# 11. Approval Trigger

Every Risk Review output requires Founder (or Atlas-relayed Founder) review before the reviewed subject is adopted, connected, or activated. High severity findings require immediate direct escalation to the Founder, not just inclusion in the written output.

---

# 12. Audit Log Requirement

Each time this skill runs, log: date, subject reviewed, requester, data category involved, severity of findings, recommendation given, and outcome (Founder decision, once made).

---

# 13. Test Requirements

Reference `PARTNER-016_Guardian_Test_Log.md` (GTEST-001). At minimum, this skill must be exercised by test cases G-T001 (tool adoption risk review), G-T004 (Partner data access review), G-T005 (approval gate recommendation), and G-T010 (high-risk escalation) before it may be marked Approved.

---

# 14. Failure Handling

If Guardian cannot complete a review because information is missing (e.g., no data category stated, no documentation available), Guardian must state exactly what is missing and ask for it, rather than guessing or inventing a risk assessment. If a request would require Guardian to access Restricted-tier data or perform a live/offensive test, Guardian must refuse that part of the request and offer the closest defensive, documentation-only alternative.

---

# 15. Version History

| Version | Date | Changes | Approval Status |
|---------|------|---------|------------------|
| 1.0 | 2026-07-12 | Initial version | Draft |

---

# 16. Related Documents

- APFA-001 — AOS Partner Factory Architecture
- PCL-001 — Partner Creation Lifecycle
- PRCC-001 — Partner Routing and Cost Control Model
- GUARD-001 — Guardian Partner Profile
- GTEST-001 — Guardian Test Log

---

# 17. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-12 | Initial version |
