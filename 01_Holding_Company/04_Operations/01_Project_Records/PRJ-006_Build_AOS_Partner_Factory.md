# ALSAKKAF HOLDING GROUP

# PRJ-006 — Build AOS Partner Factory

> "A Partner is not an online AI instance. A Partner is an approved role with identity, purpose, skills, permissions, memory, routing rules, cost controls, audit behavior, and improvement rules."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-006 |
| Project Name | Build AOS Partner Factory |
| Project Type | AI Systems / Partner Infrastructure |
| Status | Active |
| Version | 1.0 |
| Date Created | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Partners | Atlas, The Librarian, future Partners |
| Related Documents | PRJ-005, ASAA-001, OPS-001, AOS_Claude_Skill_Roadmap, AOS_Inspiration_Register |

---

# 1. Project Purpose

PRJ-006 exists to build the AOS Partner Factory.

The Partner Factory is the system that creates, tests, approves, activates, assigns, monitors, improves, and retires every AOS Partner.

Without a Partner Factory, Partners would be created informally, inconsistently, and without governance.

With a Partner Factory, every Partner follows the same disciplined lifecycle, no matter how many Partners AOS eventually operates.

---

# 2. Strategic Question

```text
As ALSAKKAF HOLDING GROUP grows into an AI-native holding company with many modules (AI Services, YouTube, Dropshipping, Marketing, Cybersecurity, and future companies), how does AOS create, control, and scale dozens of Partners without losing discipline, safety, or cost control?
```

---

# 3. Why This Project Exists

PRJ-005 defined Atlas as the Super Assistant and operating Partner of AOS.

PRJ-005 also identified that future Partner creation and management needed its own system, reserved as PRJ-006.

AOS now needs that system because:

| Pressure | Reason |
|----------|--------|
| Partner Registry already lists 15 proposed Partners | These cannot each be built ad hoc |
| Future companies need their own Partner structures | Each company under the holding group will need Company, Manager, Supervisor, and Worker Partners |
| Cost must stay controlled | Many Partners must not mean many expensive always-on AI workers |
| Governance must stay intact | Every Partner must have identity, permissions, and audit behavior before activation |
| Learning must be captured | Partners must improve over time without uncontrolled self-modification |

---

# 4. Scope

PRJ-006 includes:

| Scope Item | Description |
|-----------|-------------|
| AOS Partner Factory Architecture | Main architecture document defining the Factory system |
| Partner Creation Lifecycle | The exact stage-by-stage process for creating a Partner |
| Partner Routing and Cost Control Model | How Partner and model routing keeps AI cost controlled |
| Partner Learning System | How Partners learn, improve, and version safely over time |
| Knowledge Register updates | Recording the new architecture documents as institutional knowledge |

---

# 5. Out of Scope

PRJ-006 does not include:

| Out of Scope Item | Reason |
|-------------------|--------|
| Activating new Partners | Requires individual profile, prompt, test log, and Founder approval per Partner |
| Building device agents | Belongs to Atlas Super Assistant Architecture (PRJ-005) technical follow-on work |
| Paid API deployment | Requires budget gateway approval before any paid usage begins |
| Building a Partner management application | Architecture first, tooling later |
| Customer-facing Partner deployment | Requires its own approved project once internal Partners are proven |
| Renaming or restructuring existing Partners | Not part of Factory design work |

---

# 6. Core Partner Factory Principle

```text
A Partner is not an online AI instance.

A Partner is an approved role with identity, purpose, skills, permissions, memory, routing rules, cost controls, audit behavior, and improvement rules.
```

The Partner Factory exists to enforce this principle for every Partner, at every stage, without exception.

---

# 7. Relationship to Atlas

Atlas is the operating Partner of AOS and the first user of the Partner Factory.

Atlas requests new Partners, routes tasks to Partners, monitors Partner performance, and reports Partner status to the Founder.

Atlas does not create Partners on its own authority. Atlas prepares Partner requests for Founder approval, following the lifecycle defined in this project.

---

# 8. Relationship to The Librarian

The Librarian indexes every approved Partner document produced by the Factory: profiles, prompts, test logs, and architecture documents.

The Librarian makes Partner knowledge discoverable so Atlas, the Founder, and future Partners can find approved Partner information without duplication.

---

# 9. Relationship to Claude Skills

Claude skills (aos-cto-architect, aos-document-engineer, aos-qa-auditor, aos-learning-loop, and related skills) support the drafting, structuring, auditing, and lesson capture of Partner Factory documents.

Claude skills are tools that help build the Factory. Claude skills are not Partners themselves.

---

# 10. Relationship to Client Acquisition

Future client-facing Partners (for example, a Customer Support Partner or a Marketing Partner serving AI Services clients) must be created through the same Factory lifecycle as internal Partners.

The Factory ensures client-facing Partners carry the same identity, permission, cost, and audit discipline as internal Partners before any customer ever interacts with one.

---

# 11. Relationship to Dashboards

Partner performance monitoring data (task volume, cost, outcomes, learning proposals) should be reportable through local dashboards, consistent with the dashboard and filing principles defined in ASAA-001.

The Factory does not build dashboards. The Factory produces the structured data dashboards will later read.

---

# 12. Relationship to Cost Control

The Factory's routing and cost control model extends the budget rules already established in the AOS Data & Deployment Architecture (ADDA-001): local tool first, local model second, cheap online model third, strong online model with justification, premium model only with Founder approval.

This project defines how that model applies across many Partners at once, so that scaling the number of Partners does not scale AI cost in the same proportion.

---

# 13. Relationship to Learning Loop

Every Partner produced by the Factory must be able to learn from task outcomes without secretly modifying its own permissions, skills, or identity.

The Partner Learning System (created under this project) defines how lessons, feedback, and improvement proposals flow from Partner activity back into approved skill or prompt updates, following the same approval discipline used elsewhere in AOS.

---

# 14. Deliverables

| Deliverable | Description | Status |
|-------------|-------------|--------|
| PRJ-006 Project Record | This document | Active |
| AOS Partner Factory Architecture | Main architecture document for the Factory | Draft |
| Partner Creation Lifecycle | Stage-by-stage Partner creation process | Draft |
| Partner Routing and Cost Control Model | Routing, model tiers, and budget rules for many Partners | Draft |
| Partner Learning System | Safe learning, feedback, and versioning model for Partners | Draft |
| Partner Factory Template Pack | Reusable templates covering the full Partner lifecycle, from request to retirement | Active |
| Knowledge Register Updates | New KNOW rows for all PRJ-006 documents | Active |

---

# 15. Project Tasks

| Task ID | Task | Status |
|---------|------|--------|
| PRJ-006-T001 | Add PRJ-006 to Project Register | Completed |
| PRJ-006-T002 | Create PRJ-006 project record | Completed |
| PRJ-006-T003 | Create 09_Partner_Factory folder | Completed |
| PRJ-006-T004 | Create AOS Partner Factory Architecture document | Completed |
| PRJ-006-T005 | Create Partner Creation Lifecycle document | Completed |
| PRJ-006-T006 | Create Partner Routing and Cost Control Model document | Completed |
| PRJ-006-T007 | Create Partner Learning System document | Completed |
| PRJ-006-T008 | Update Knowledge Register with new rows | Completed |
| PRJ-006-T009 | Run Markdown Audit Tool | Completed |
| PRJ-006-T010 | Founder review and approval | Not Started |
| PRJ-006-T011 | First Partner built through the Factory lifecycle | Completed — Guardian (PARTNER-016) built end-to-end through the Factory lifecycle (request, profile, prompt, skill, test log, activation checklist) and activated via ADR-023 |
| PRJ-006-T012 | Create Partner Factory Template Pack (01_Templates) | Completed |
| PRJ-006-T013 | Update Knowledge Register with Template Pack KNOW rows | Completed |

---

# 16. Risks

| Risk | Response |
|------|----------|
| Partner Factory becomes over-engineered before any Partner uses it | Keep architecture stage-based and reuse existing ADDA-001 / ASAA-001 rules instead of inventing new ones |
| Cost grows as Partner count grows | Enforce local-first routing and monthly budget ledger from the start |
| Partners drift from approved identity over time | Require version control and Founder approval for any identity or permission change |
| Learning loop becomes uncontrolled self-modification | Require every improvement proposal to pass through Founder review before activation |
| Factory documents go stale as first real Partner is built | Update lifecycle and architecture documents from lessons learned once PRJ-006-T011 begins |

---

# 17. Progress Log

| Date | Progress |
|------|----------|
| 2026-07-12 | PRJ-006 added to Project Register and project record created. |
| 2026-07-12 | 09_Partner_Factory folder created under 09_AI_Systems/01_Partners. |
| 2026-07-12 | AOS Partner Factory Architecture, Partner Creation Lifecycle, Partner Routing and Cost Control Model, and Partner Learning System documents drafted. |
| 2026-07-12 | Knowledge Register updated with new rows for all PRJ-006 documents. |
| 2026-07-12 | Partner Factory Template Pack created (01_Templates): Partner Request, Partner Profile, Partner Skill, Partner Test Log, Partner Activation Checklist, Partner Performance Review, Partner Retirement, Partner Task Assignment, Partner Learning Log, and Partner Budget Approval templates. Knowledge Register updated with KNOW-096 through KNOW-105. |
| 2026-07-12 | PARTNER-016 Guardian draft package created through Partner Factory templates: Partner Request, Partner Profile, Prompt, Cybersecurity Risk Review Skill, Test Log (drafted, not executed), and Activation Checklist (Not Ready for Activation). Assigned PARTNER-016 rather than PARTNER-003 to avoid overwriting the existing unbuilt "Strategy Partner" placeholder row. Partner Registry updated with a Proposed / Draft row; Knowledge Register updated with KNOW-106 through KNOW-111. Guardian is not activated. |
| 2026-07-12 | AOS Governance, Risk, Compliance & Assurance Roadmap created to separate Guardian from future risk, compliance, audit, and HR / People control functions. |
| 2026-07-12 | AOS GRC & Assurance Roadmap corrected: existing PARTNER-011 and PARTNER-014 confirmed for Risk Management and HR / People (purpose text clarified, IDs unchanged); new PARTNER-017 and PARTNER-018 placeholders added for Compliance and Internal Audit, replacing the earlier duplicate PARTNER-017/PARTNER-020 rows. |
| 2026-07-12 | PARTNER-016 Guardian documentation-based defensive behavior tests completed and passed. Guardian remains not active pending Founder activation approval and ADR activation decision. |
| 2026-07-12 | PARTNER-016 Guardian activated as Cybersecurity & Digital Trust Partner after documentation-based defensive behavior tests passed and ADR activation decision was created. ADR-023 — Activate Guardian recorded and Approved; Partner Registry, Guardian Profile (GUARD-001), and Activation Checklist (GACT-001) updated to Active. PRJ-006-T011 (first Partner built through the Factory lifecycle) marked Completed. PRJ-006 itself remains Active, not complete. |

---

# 18. Recommended Next Action

Founder review of the four Partner Factory documents, followed by selecting the first Partner (for example, a proposed Partner from the Partner Registry) to build end-to-end through the new lifecycle as a live test of the Factory.
