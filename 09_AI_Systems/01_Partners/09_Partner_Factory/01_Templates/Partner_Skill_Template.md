# ALSAKKAF HOLDING GROUP

# Partner Skill Template

> "Partners gain approved skills, not unlimited abilities."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PFT-003 |
| Document Type | Partner Factory Template |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-006 |
| Related Documents | APFA-001, PCL-001, PRCC-001 |

---

# 1. Purpose

This template is used to define a single reusable Partner skill, following the Partner Skill Model in APFA-001 Section 7.

Each skill assigned to a Partner must have its own completed version of this template, or a skills table entry inside the Partner Profile.

---

# 2. How to Use This Template

1. Copy this file for each new skill, or add a row to the Partner Profile's skills table and expand into this format when the skill is complex.
2. Fill in every field below.
3. Test the skill using `Partner_Test_Log_Template.md` before it is marked Approved.

---

# 3. Skill Name

[Short, descriptive skill name]

---

# 4. Skill Purpose

[What this skill accomplishes, in one or two sentences.]

---

# 5. Partner Using the Skill

| Field | Entry |
|-------|-------|
| Partner ID | [PARTNER-0XX] |
| Partner Name | [Name] |

---

# 6. Inputs

| Input | Description |
|-------|--------------|
| [Input 1] | [Description] |
| [Input 2] | [Description] |

---

# 7. Outputs

| Output | Format |
|--------|--------|
| [Output 1] | [Text / Table / Document / Report] |

---

# 8. Steps

1. [Step 1]
2. [Step 2]
3. [Step 3]

---

# 9. Permission Level

| Field | Entry |
|-------|-------|
| Minimum Authority Level required | [Level 0–5] |
| Notes | [Any constraint specific to this skill] |

---

# 10. Cost Behavior

| Field | Entry |
|-------|-------|
| Default model tier | [Local tool / Local model / Cheap online / Strong online / Premium] |
| Trigger for higher tier | [Condition that would require a more expensive model, if any] |

---

# 11. Local-First Behavior

[Describe how this skill attempts local tools or local models before using any online AI, per ADDA-001.]

---

# 12. Online AI Trigger

[State exactly when this skill is allowed to call an online AI service, and which tier. If never, state "This skill does not use online AI."]

---

# 13. Approval Trigger

[State what output of this skill requires Founder or Atlas review before being acted on, if any.]

---

# 14. Audit Log Requirement

[State what must be logged each time this skill runs: date, input, output summary, cost tier used, and outcome.]

---

# 15. Test Requirements

[Reference `Partner_Test_Log_Template.md`. State the minimum number and type of test cases required before this skill is Approved.]

---

# 16. Failure Handling

[Describe what the Partner should do if this skill fails, produces an uncertain result, or cannot complete: escalate, report the gap, or ask for clarification — never invent a result.]

---

# 17. Version History

| Version | Date | Changes | Approval Status |
|---------|------|---------|------------------|
| 1.0 | [YYYY-MM-DD] | Initial version | [Draft / Testing / Approved] |

---

# 18. Related Documents

- APFA-001 — AOS Partner Factory Architecture
- PCL-001 — Partner Creation Lifecycle
- PRCC-001 — Partner Routing and Cost Control Model
- Partner_Profile_Template.md
- Partner_Test_Log_Template.md

---

# 19. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-12 | Initial version |
