---
name: aos-learning-loop
description: Use this skill when capturing outcomes, feedback, patterns, or lessons from AOS work, or when proposing process improvements — it defines how AOS learns over time without uncontrolled self-modification.
---

# AOS Learning Loop Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-006 |
| Skill Name | aos-learning-loop |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-002 |

---

# Purpose

This skill defines how AOS captures outcomes, feedback, patterns, and lessons from completed work (projects, client deals, deliveries, experiments), and how improvement is proposed — without any AI Partner or skill modifying AOS rules, registers, or its own instructions on its own authority.

---

# The Loop

1. **Capture the outcome.** What happened, compared to what was planned or assumed (e.g., STRAT-001 forecasts, STRAT-002 deal stages)?
2. **Capture the gap.** Where did reality diverge from the assumption, and by how much?
3. **Identify the pattern.** Is this a one-off, or does it resemble something seen in a prior project/lesson (check `Knowledge_Register.md` and existing `*_Lessons_Learned.md` files)?
4. **Draft the lesson.** State it plainly: what we now believe, and what evidence supports it.
5. **Propose the improvement.** If the lesson implies a process, pricing, or workflow change, write it as a proposal, not an edit.
6. **Route for approval.** Any change to an official AOS document, register, protocol, or skill goes through the standard AOS Live Build flow: inspect, plan, Founder approval, edit, Markdown Audit, review — per CLAUDE.md and OPS-001.
7. **Record the decision.** Whether approved or rejected, the outcome of the proposal is itself worth recording so the same idea isn't re-debated from zero later.

---

# Where Lessons Live

- Project-specific lessons: `01_Holding_Company/04_Operations/01_Project_Records/PRJ-XXX_Lessons_Learned.md`, following the existing pattern (e.g., PRJ-001 through PRJ-005).
- Client acquisition/delivery lessons: the Lessons Learned Loop defined in `AOS_Client_Acquisition_and_Delivery_Model.md` Section 13.
- Cross-cutting institutional knowledge: `01_Holding_Company/01_Governance/Knowledge_Register.md`, once a lesson is approved and documented.

---

# Hard Boundary: No Uncontrolled Self-Modification

This skill explicitly does not permit:

- editing this skill file, another skill file, CLAUDE.md, or OPS-001 without going through the standard AOS Live Build flow and Founder approval,
- creating new Partners, registers, or protocols as a side effect of "learning" — that still requires the activation steps in CLAUDE.md Section 4,
- silently changing pricing, qualification criteria, or approval gates based on a single data point — patterns require more than one instance before being proposed as a rule change,
- auto-applying a proposed improvement. A proposal is always a draft for Founder review, never a live change.

---

# Related Documents

- 01_Holding_Company/03_Strategy/AOS_Client_Acquisition_and_Delivery_Model.md
- 01_Holding_Company/03_Strategy/AOS_Market_Intelligence_and_Financial_Assumptions.md
- CLAUDE.md
- 01_Holding_Company/04_Operations/02_Protocols/AOS_Live_Build_Protocol.md
- 01_Holding_Company/01_Governance/Knowledge_Register.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
