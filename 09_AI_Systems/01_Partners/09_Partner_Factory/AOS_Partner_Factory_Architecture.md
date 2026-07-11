# ALSAKKAF HOLDING GROUP

# AOS Partner Factory Architecture

> "A Partner is not an online AI instance. A Partner is an approved role with identity, purpose, skills, permissions, memory, routing rules, cost controls, audit behavior, and improvement rules."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | APFA-001 |
| Document Type | Architecture |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-006 |
| Related Documents | ASAA-001, ADDA-001, POM-001, PREG-001, PWA-001 |

---

# 1. Purpose

This document defines the AOS Partner Factory: the system that creates, tests, approves, activates, assigns, monitors, improves, and retires every Partner inside ALSAKKAF HOLDING GROUP.

The Factory exists so that Partner creation follows one disciplined system, regardless of how many Partners AOS eventually operates.

---

# 2. What the Partner Factory Is

The Partner Factory is:

| It Is | Meaning |
|-------|---------|
| A governance system | Every Partner passes through the same approval stages |
| A structural template | Every Partner has the same required identity, skill, permission, cost, and audit fields |
| A routing layer | Tasks are matched to the right Partner and the right model tier |
| A cost control layer | Partner activity stays inside budget rules from ADDA-001 |
| A learning system | Partner performance and lessons feed back into approved improvements |
| An institutional memory system | Every Partner decision is recorded in the Partner Registry and Knowledge Register |

---

# 3. What the Partner Factory Is Not

| It Is Not | Reason |
|-----------|--------|
| An auto-generation tool that spins up AI agents on demand | Every Partner requires Founder approval before activation |
| A way to run many online AI workers simultaneously | Cost and routing rules keep most work local or on-demand |
| A replacement for the Partner Registry or Partner Operating Model | The Factory builds Partners; the Registry and Model govern them |
| A self-modifying system | Partners cannot change their own identity, permissions, or skills without approval |
| An autonomous hiring system | The Founder decides which Partners get created and activated |

---

# 4. High-Level Architecture

```text
Idea or Need
    ↓
Partner Factory (this system)
    ↓
Partner Profile + Skills + Permissions + Cost Rules + Prompt
    ↓
Test Log
    ↓
Founder Approval
    ↓
Partner Registry Update
    ↓
Active Partner
    ↓
Atlas Routing and Task Assignment
    ↓
Monitoring and Learning Loop
    ↓
Version Update or Retirement
```

The Factory sits between "an idea for a Partner" and "an active, governed Partner doing real work."

---

# 5. Partner Lifecycle

The full lifecycle is defined in detail in `Partner_Creation_Lifecycle.md`.

In summary, every Partner moves through: Idea, Partner Request, Partner Profile, Partner Skills, Permission Level, Data Access Rules, Cost Rules, Prompt/Instructions, Test Log, Founder Approval, Registry Update, Activation, Monitoring, Learning Loop, Version Update, and Retirement if needed.

No stage may be skipped for an official Partner.

---

# 6. Partner Identity Model

Every Partner must have a documented identity consisting of:

| Field | Description |
|-------|-------------|
| Partner ID | Unique identifier from the Partner Registry (for example, PARTNER-016) |
| Partner Name | Human-readable name |
| Partner Type | From the Partner Types table in the Partner Registry (Knowledge, Research, Strategy, Project, Finance, Operations, Marketing, Technology, Learning, Risk, Company, Supervisor, Manager, Executive) |
| Purpose | One clear sentence describing what the Partner exists to do |
| Owner | The human accountable for the Partner (CEO by default at foundation stage) |
| Related Documents | Profile, prompt, test log, and any architecture documents that define the Partner |

Identity does not change without a version update and Founder approval.

---

# 7. Partner Skill Model

Partners gain approved skills, not unlimited abilities, consistent with the Atlas skill-based design in ASAA-001.

Each skill assigned to a Partner must define:

| Field | Description |
|-------|-------------|
| Skill Name | What the skill is called |
| Purpose | What the skill accomplishes |
| Permission Level Required | Minimum authority level needed to use the skill |
| Input Requirements | What information the skill needs |
| Output Format | What the skill produces |
| Test Log | Evidence the skill works as intended |
| Approval Status | Draft, Testing, Approved |

A Partner may only use skills that have been approved for that Partner specifically.

---

# 8. Partner Permission Model

Every Partner operates at an Authority Level defined in the Partner Registry (Level 0 Reference through Level 5 Autonomous Execution).

At the foundation stage:

| Rule | Value |
|------|-------|
| Minimum allowed level | Level 0 |
| Maximum allowed level | Level 3 (Prepare) |
| Level 4 (Execute With Approval) | Reviewed case by case, never default |
| Level 5 (Autonomous Execution) | Not approved |

Permission level determines what a Partner may do without asking, what it must prepare for review, and what it may never do.

---

# 9. Partner Routing Model

Task routing decides which Partner handles a given request, and which model tier that Partner uses to complete it.

The detailed routing and cost logic is defined in `Partner_Routing_and_Cost_Control_Model.md`.

At a high level:

```text
Task arrives
    ↓
Atlas identifies task type
    ↓
Atlas matches task to the Partner whose purpose and skills fit
    ↓
Partner Router selects the Partner
    ↓
Model Router selects the cheapest sufficient model tier
    ↓
Partner executes within its permission level
    ↓
Result and cost are logged
```

---

# 10. Partner Cost Control Model

Partner cost control follows the budget principles already established in ADDA-001, extended to apply across many Partners at once.

Full detail is defined in `Partner_Routing_and_Cost_Control_Model.md`, including the cost estimator, monthly budget ledger, warning levels, and hard stop rules.

The governing rule:

```text
AOS should be Partner-rich, not AI-worker-expensive.
```

---

# 11. Partner Memory and Learning Model

Partners retain role memory (approved knowledge relevant to their purpose) and task outcome history, but do not silently rewrite their own identity, skills, or permissions.

Full detail is defined in `Partner_Learning_System.md`.

---

# 12. Partner Task Assignment Model

Atlas assigns tasks to Partners based on:

| Factor | Description |
|--------|-------------|
| Partner purpose match | Does the task fall inside this Partner's defined purpose? |
| Partner authority level | Can this Partner's permission level handle the task? |
| Partner availability | Is the Partner active and not retired or paused? |
| Cost tier fit | Can this task be done at the lowest sufficient model tier? |

If no existing Partner fits, Atlas prepares a Partner Request for Founder review rather than stretching an existing Partner beyond its purpose.

---

# 13. Partner Performance Monitoring Model

Each active Partner should be monitored for:

| Metric | Purpose |
|--------|---------|
| Task volume | How much work the Partner handles |
| Task outcomes | Success, partial success, failure, escalation |
| Cost consumed | AI spend attributable to the Partner |
| Escalations to Founder | How often the Partner needed human decision |
| Lessons captured | What the Partner's activity has taught AOS |

Monitoring data should be structured so it can be surfaced through local dashboards, consistent with ASAA-001 dashboard principles.

---

# 14. Partner Retirement Model

A Partner is retired when:

| Condition | Example |
|-----------|---------|
| Purpose no longer exists | The project or function the Partner supported has ended |
| Partner is replaced | A better Partner design supersedes it |
| Partner underperforms | Repeated poor outcomes with no viable improvement path |
| Founder decision | Any other reason the Founder determines |

Retired Partners remain documented in the Partner Registry for institutional memory. Retirement never means deletion of Partner history.

---

# 15. Atlas Role

Atlas is the operating Partner that uses the Factory day to day: requesting new Partners, routing tasks, monitoring performance, and reporting Partner status to the Founder.

Atlas does not approve or activate Partners. Atlas prepares; the Founder approves.

---

# 16. The Librarian Role

The Librarian indexes every Partner Factory document: profiles, prompts, test logs, and architecture documents, so Partner knowledge remains discoverable across AOS.

---

# 17. CEO Approval Gates

The Founder (CEO) must approve before:

| Gate | Requirement |
|------|-------------|
| New Partner creation | Partner Request reviewed and accepted |
| Partner activation | Profile, skills, permissions, cost rules, prompt, and test log complete |
| Permission level increase | Any move above Level 3 |
| Premium model usage | Any task routed to a premium-tier model |
| Partner retirement | Founder confirms the Partner should stop operating |

No Partner may skip a CEO approval gate.

---

# 18. Local-First Behavior

The Factory defaults every Partner to local-first execution: local tools and local models before any online AI is used, consistent with ADDA-001.

---

# 19. Online AI Usage Behavior

Online AI is used only when local tools and local models cannot complete a task, and only within the routing and budget rules defined in `Partner_Routing_and_Cost_Control_Model.md`.

---

# 20. Dashboard/Reporting Behavior

The Factory produces structured Partner data (identity, tasks, cost, outcomes) intended for local dashboard reporting, following ASAA-001 dashboard and filing principles. The Factory does not build the dashboards itself.

---

# 21. Client Acquisition Behavior

Any Partner supporting client acquisition or client delivery work must be created through the same Factory lifecycle as internal Partners, with the same identity, permission, and cost discipline, before any client-facing use.

---

# 22. YouTube/Content Factory Behavior

Future content-related Partners (for example, a Content Partner supporting the YouTube Shorts Factory) follow the same Factory lifecycle. No content Partner is activated without an approved profile, prompt, and test log.

---

# 23. Marketing Campaign Behavior

Future marketing or ads Partners are created through the Factory and must respect budget caps defined in campaign planning work, in addition to the Partner-level cost rules in this architecture.

---

# 24. Cybersecurity/Guardian Behavior

A future Guardian or cybersecurity Partner must be created through the Factory with especially strict permission levels. Consistent with the aos-guardian-cybersecurity skill, such a Partner must never perform hacking, exploitation, credential theft, or unauthorized testing, regardless of authority level granted.

---

# 25. Future Customer Deployment Behavior

If Partners are eventually deployed to support external customers, they must first exist as proven, internally-active Partners built through this Factory. Customer deployment is a separate future project requiring its own approval, not an automatic extension of internal activation.

---

# 26. Status

Draft.

This architecture requires Founder review before the first Partner is built end-to-end through the Factory lifecycle.
