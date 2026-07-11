# ALSAKKAF HOLDING GROUP

# Partner Profile Template

> "A Partner is not an online AI instance. A Partner is an approved role with identity, purpose, skills, permissions, memory, routing rules, cost controls, audit behavior, and improvement rules."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PFT-002 |
| Document Type | Partner Factory Template |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-006 |
| Related Documents | APFA-001, PCL-001, PREG-001, POM-001 |

---

# 1. Purpose

This template is used to create the official identity document for a new Partner, following the Partner Identity Model defined in APFA-001 Section 6.

A completed profile is required before any Partner skill, prompt, or test log work begins.

---

# 2. How to Use This Template

1. Copy this file into `09_AI_Systems/01_Partners/01_Partner_Profiles/` and rename it `PARTNER-0XX_[Name].md`.
2. Fill in every field below using the accepted Partner Request as the source.
3. Assign the next available Partner ID from the Partner Registry.
4. Do not mark Status as "Active" until the full lifecycle in PCL-001 is complete and the Founder has approved activation.

---

# 3. Document Information (Profile-Specific)

| Field | Value |
|-------|-------|
| Partner ID | [PARTNER-0XX] |
| Partner Name | [Name] |
| Partner Type | [Knowledge / Research / Strategy / Project / Finance / Operations / Marketing / Technology / Learning / Risk / Company / Supervisor / Manager / Executive] |
| Status | [Draft / Testing / Active / Paused / Retired] |
| Owner | [Human accountable for this Partner — CEO by default] |

---

# 4. Purpose

[One clear sentence describing what this Partner exists to do.]

---

# 5. Responsibilities

| # | Responsibility |
|---|-----------------|
| 1 | [Responsibility 1] |
| 2 | [Responsibility 2] |
| 3 | [Responsibility 3] |

---

# 6. What This Partner May Do

- [Allowed task 1]
- [Allowed task 2]
- [Allowed task 3]

---

# 7. What This Partner Must Not Do

- [Restricted task 1]
- [Restricted task 2]
- [Restricted task 3]
- Approve its own activation or permission increases
- Access data outside its Data Access Rules
- Exceed its Cost Rules without new approval

---

# 8. Required Skills

| Skill Name | Purpose | Related Skill Document |
|------------|---------|-------------------------|
| [Skill 1] | [Purpose] | [Link to Partner_Skill_Template.md instance] |
| [Skill 2] | [Purpose] | [Link to Partner_Skill_Template.md instance] |

---

# 9. Data Access Rules

| Field | Entry |
|-------|-------|
| Approved data sources | [Registers, folders, documents this Partner may read] |
| Explicitly forbidden data | [Credentials, private student/client data, restricted records] |
| Sensitivity level | [Public / Internal / Confidential / Restricted] |

---

# 10. Permission Level

| Field | Entry |
|-------|-------|
| Authority Level | [Level 0–5, per Partner Registry scale] |
| Foundation-stage ceiling | Level 3 (Prepare) unless Founder approves higher |
| Justification | [Why this level fits the Partner's purpose] |

---

# 11. Cost Rules

| Field | Entry |
|-------|-------|
| Expected model tier | [Local tool / Local model / Cheap online / Strong online / Premium] |
| Cost ceiling | [Amount or "no paid usage without Budget Approval"] |
| Routing reference | Partner_Routing_and_Cost_Control_Model.md (PRCC-001) |

---

# 12. Local Tools

[List local tools, scripts, or files this Partner uses before any online AI is invoked, consistent with local-first routing.]

---

# 13. Online AI Usage Rules

[State when online AI may be used, which tier, and what approval gate applies. Restricted data must never be sent to an online AI service.]

---

# 14. Reporting Behavior

[How and to whom this Partner reports status, outputs, and escalations — typically Atlas and/or the Founder directly.]

---

# 15. Relationship to Atlas

[Describe how this Partner receives tasks from Atlas, and what it reports back.]

---

# 16. Relationship to The Librarian

[Describe how this Partner's documents are indexed by The Librarian, and what knowledge sources it depends on.]

---

# 17. Activation Requirements

| Requirement | Complete |
|--------------|----------|
| Profile completed | [Yes / No] |
| Skills defined | [Yes / No] |
| Prompt/instructions completed | [Yes / No] |
| Test log passed | [Yes / No] |
| Permission level assigned | [Yes / No] |
| Data access approved | [Yes / No] |
| Cost rules approved | [Yes / No] |
| Knowledge Register updated | [Yes / No] |
| Partner Registry updated | [Yes / No] |
| Founder approval captured | [Yes / No] |

See `Partner_Activation_Checklist.md` for the full gate.

---

# 18. Related Documents

- APFA-001 — AOS Partner Factory Architecture
- PCL-001 — Partner Creation Lifecycle
- PREG-001 — Partner Registry
- POM-001 — Partner Operating Model
- Partner_Skill_Template.md
- Partner_Test_Log_Template.md
- Partner_Activation_Checklist.md

---

# 19. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-12 | Initial version |
