# ALSAKKAF HOLDING GROUP

# Partner Creation Lifecycle

> "No Partner becomes official until it is documented, reviewed, and approved."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PCL-001 |
| Document Type | Lifecycle Model |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-006 |
| Related Documents | APFA-001, PREG-001, POM-001 |

---

# 1. Purpose

This document defines the exact stage-by-stage lifecycle that every Partner must pass through, from first idea to eventual retirement.

No official Partner may skip a stage.

---

# 2. The Lifecycle

```text
Idea
    ↓
Partner Request
    ↓
Partner Profile
    ↓
Partner Skills
    ↓
Permission Level
    ↓
Data Access Rules
    ↓
Cost Rules
    ↓
Prompt / Instructions
    ↓
Test Log
    ↓
Founder Approval
    ↓
Registry Update
    ↓
Activation
    ↓
Monitoring
    ↓
Learning Loop
    ↓
Version Update
    ↓
Retirement if needed
```

---

# 3. Stage Definitions

## 3.1 Idea

A need is identified for work that no existing Partner's purpose covers.

Output: A short description of the gap.

## 3.2 Partner Request

The idea is formalized into a request: what type of Partner, what purpose, why an existing Partner cannot cover it.

Output: A Partner Request note, prepared by Atlas or the Founder.

## 3.3 Partner Profile

The Partner's identity is documented: Partner ID, name, type, purpose, owner, related documents, following the Partner Identity Model in APFA-001.

Output: A Partner profile document.

## 3.4 Partner Skills

The specific skills the Partner will hold are listed, each with purpose, permission level required, input requirements, and output format.

Output: A skills table inside the Partner profile or a dedicated skills document.

## 3.5 Permission Level

The Partner's Authority Level is assigned from the Partner Registry's Level 0 through Level 5 scale. Foundation-stage Partners are limited to Level 0 through Level 3.

Output: A stated Authority Level with justification.

## 3.6 Data Access Rules

The Partner's allowed knowledge sources and data boundaries are defined: which AOS documents, registers, or systems it may read, and what it may never access (for example, private student data or credentials).

Output: A data access rules section in the profile.

## 3.7 Cost Rules

The Partner's expected model tier usage and cost ceiling are defined, following the Partner Routing and Cost Control Model.

Output: A cost rules section in the profile.

## 3.8 Prompt / Instructions

The Partner's operating prompt is written: how it should think, respond, and behave, consistent with its purpose, skills, and permission level.

Output: A Partner prompt document.

## 3.9 Test Log

The Partner is tested against realistic tasks before activation. Results, including failures and edge cases, are recorded.

Output: A Partner test log document.

## 3.10 Founder Approval

The Founder reviews the profile, skills, permission level, data access rules, cost rules, prompt, and test log together, and decides whether to approve activation.

Output: A recorded approval decision.

## 3.11 Registry Update

Once approved, the Partner is added to (or updated in) the Partner Registry with status "Active."

Output: An updated Partner Registry row.

## 3.12 Activation

The Partner becomes available for Atlas to route real tasks to.

Output: The Partner operating on real work within its approved scope.

## 3.13 Monitoring

The Partner's task volume, outcomes, cost, and escalations are tracked, following the Partner Performance Monitoring Model in APFA-001.

Output: Ongoing monitoring data.

## 3.14 Learning Loop

Lessons from the Partner's activity are captured and turned into improvement proposals, following the Partner Learning System.

Output: Lessons learned entries and improvement proposals.

## 3.15 Version Update

Approved improvements (skill changes, prompt changes, permission changes) are applied as a new version of the Partner, with the change documented.

Output: An updated Partner profile version and changelog entry.

## 3.16 Retirement if Needed

If the Partner's purpose ends, or it underperforms with no viable improvement path, the Founder retires it. The Partner remains documented in the Partner Registry with status "Retired."

Output: A retirement decision and updated registry status.

---

# 4. Lifecycle Rules

1. No stage may be skipped for an official Partner.
2. No Partner is Active before Founder Approval.
3. No Partner exceeds its approved Permission Level.
4. No Partner accesses data outside its Data Access Rules.
5. No Partner exceeds its Cost Rules without a new approval.
6. Every stage's output must be a documented artifact, not a verbal decision.
7. Retired Partners are never deleted from the record.

---

# 5. Relationship to Atlas

Atlas prepares Partner Requests, drafts profiles, skills, prompts, and test plans, and proposes routing and monitoring data, but Atlas does not grant itself or any Partner authority beyond Founder Approval.

---

# 6. Relationship to The Librarian

The Librarian indexes every artifact produced at each lifecycle stage so it remains discoverable for future Partner Factory work and audits.

---

# 7. Status

Draft.

This lifecycle takes effect for any Partner request going forward, and should be exercised end-to-end with the first Partner built through the Factory (PRJ-006-T011).
