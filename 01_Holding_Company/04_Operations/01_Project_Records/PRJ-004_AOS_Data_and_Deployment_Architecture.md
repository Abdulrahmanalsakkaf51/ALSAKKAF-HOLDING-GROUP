# ALSAKKAF HOLDING GROUP

# PRJ-004 — AOS Data & Deployment Architecture

> "Atlas must be useful offline, powerful online, and controlled by permission, privacy, and budget."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-004 |
| Project Name | AOS Data & Deployment Architecture |
| Project Type | Architecture / Technology Project |
| Status | Completed |
| Version | 1.0 |
| Date Created | 2026-07-10 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Partner | PARTNER-002 — Atlas |
| Related Projects | PRJ-001, PRJ-002, PRJ-003 |

---

# 1. Purpose

PRJ-004 exists to define how AOS data, Atlas, online AI models, local tools, device agents, and future deployments should work together safely.

This project answers an important Founder concern:

```text
Where does the data live?
Can Atlas work offline?
Can Atlas become powerful online without uncontrolled cost?
How do we protect privacy, permissions, and company knowledge?
```

---

# 2. Project Goal

The goal of PRJ-004 is to create the official AOS Data & Deployment Architecture.

The architecture should define:

| Area | Purpose |
|------|---------|
| Local Data | What stays on the Founder’s computer or company server |
| Cloud Data | What can be stored online |
| GitHub Data | What belongs in the public or private repository |
| Sensitive Data | What must never be placed in public repositories |
| Offline Mode | What Atlas can do without internet |
| Online Mode | What Atlas can do using online AI services |
| Budget Control | How Atlas prevents uncontrolled AI spending |
| Device Agents | How Windows, Mac, Android, iPhone, and other devices may connect |
| Skills | How Atlas gains approved capabilities |
| Approval Rules | What actions require Founder approval |
| Audit Logs | How actions and decisions are recorded |

---

# 3. Why This Project Matters

Atlas should not become a random uncontrolled AI agent.

Atlas should become an AOS-controlled operating Partner.

This means Atlas must be designed with:

| Principle | Meaning |
|----------|---------|
| Data first | Know where information is stored |
| Intelligence second | Use AI only when needed |
| Permission always | Sensitive actions require approval |
| Local resilience | Work should continue during internet outages |
| Online power | Strong AI can be used when valuable |
| Budget control | Atlas must not secretly spend money |
| Auditability | Important actions must be recorded |

---

# 4. Scope

PRJ-004 includes:

| Scope Item | Description |
|-----------|-------------|
| Data architecture | Define storage levels and data separation |
| Offline architecture | Define what works locally without internet |
| Online architecture | Define how Atlas connects to cloud AI |
| Cost architecture | Define budget limits and model selection rules |
| Deployment architecture | Define future deployment across devices and systems |
| Permission architecture | Define approval levels and restricted actions |
| Security notes | Define early privacy and safety rules |
| Lessons learned | Capture what the company learns |

---

# 5. Out of Scope

PRJ-004 does not include:

| Out of Scope Item | Reason |
|-------------------|--------|
| Building Atlas Super Assistant | This belongs to PRJ-005 |
| Building Partner Factory | This belongs to PRJ-006 |
| Connecting to Microsoft Teams | Needs future integration project |
| Connecting to student data | Requires strict privacy and official systems |
| Installing Agent Zero | Not part of AOS direction |
| Giving any AI full control | Unsafe before permission architecture |
| Paid API deployment | Needs budget and approval system first |
| Mobile app development | Future technical project |

---

# 6. Key Architecture Direction

The preferred architecture is:

```text
Local Atlas Core
↓
AOS Knowledge Vault
↓
Local Tools
↓
Online AI Gateway
↓
Cost Control Layer
↓
Permission Layer
↓
Device Agents
↓
Audit Log
```

This means:

| Layer | Role |
|------|------|
| Local Atlas Core | Keeps Atlas useful even without internet |
| AOS Knowledge Vault | Stores approved company knowledge |
| Local Tools | Runs safe tools like Markdown Audit |
| Online AI Gateway | Connects to powerful online models when needed |
| Cost Control Layer | Controls token/API spending |
| Permission Layer | Requires approval for sensitive actions |
| Device Agents | Allow future action on Windows, Mac, Android, iOS |
| Audit Log | Records important actions and decisions |

---

# 7. Budget Principle

Atlas must not use paid AI without control.

The early budget principle is:

```text
Local first.
Cheap model second.
Premium model only when needed.
Founder approval for expensive tasks.
Monthly spending limit always active.
```

Suggested early budget rule:

| Budget Item | Rule |
|------------|------|
| Target monthly cost | 5 to 20 USD |
| Maximum early cost | 50 USD |
| Warning level | 50% of monthly budget |
| Approval required | Before premium or heavy tasks |
| Hard stop | At monthly limit unless Founder approves |

---

# 8. Offline Principle

Atlas should continue working during internet outages.

Offline Atlas should be able to:

| Offline Capability | Status |
|-------------------|--------|
| Search local AOS documents | Required |
| Run local Python tools | Required |
| Audit Markdown files | Required |
| Prepare templates | Required |
| Track projects from local files | Required |
| Generate basic reports from local data | Required |
| Use local AI model later | Future |
| Send messages or emails | Not available offline unless queued |
| Search live web | Not available offline |
| Use cloud AI | Not available offline |

---

# 9. Online Principle

When internet is available, Atlas may connect to online AI services.

Online Atlas may help with:

| Online Capability | Purpose |
|------------------|---------|
| Deep reasoning | Strategy, architecture, planning |
| Research | Web and market research |
| Advanced writing | Proposals, ads, scripts, reports |
| Coding help | Tools, debugging, automation |
| Executive assistant tasks | Drafting, scheduling support, follow-ups |
| Future integrations | Teams, email, calendar, dashboards |

Online Atlas must remain controlled by:

- budget limits,
- privacy rules,
- permission levels,
- approved data access,
- audit logging.

---

# 10. Device Agent Principle

Atlas should not directly become one uncontrolled agent on every device.

The future architecture should use device agents.

| Device / Platform | Future Approach |
|-------------------|-----------------|
| Windows | Local desktop agent and tools |
| macOS | Local desktop agent and tools |
| Linux | Local server or workstation agent |
| Android | Controlled mobile agent with strict permissions |
| iPhone / iPad | Shortcuts, app actions, approved integrations |
| Web apps | APIs first, browser automation only when needed |
| Microsoft 365 | Microsoft Graph / official APIs first |

Device agents should:

- act only with permission,
- report back to Atlas,
- log important actions,
- not store sensitive data unnecessarily,
- never get unlimited access.

---

# 11. Data Separation Rule

AOS must separate data by sensitivity.

| Data Level | Example | Storage Direction |
|-----------|---------|------------------|
| Level 1 — Public AOS Knowledge | Blueprints, public philosophy, general documents | GitHub or public repository |
| Level 2 — Private Company Knowledge | Strategy, finance, private plans | Private local or private cloud |
| Level 3 — Personal Work Data | ASC tasks, training plans, drafts | Separate work storage |
| Level 4 — Sensitive Records | Student IDs, student names, employee records | Official approved systems only |
| Level 5 — Credentials | API keys, passwords, tokens | Secure vault only |

---

# 12. Success Criteria

PRJ-004 is successful if it produces an architecture that clearly defines:

| Criteria No. | Success Criteria |
|-------------|------------------|
| 1 | Where AOS data should be stored |
| 2 | What should remain local |
| 3 | What can connect online |
| 4 | How Atlas controls AI cost |
| 5 | What Atlas can do offline |
| 6 | What Atlas can do online |
| 7 | How device agents should work |
| 8 | What sensitive data must be protected |
| 9 | What requires Founder approval |
| 10 | How this architecture prepares PRJ-005 and PRJ-006 |

---

# 13. Deliverables

| Deliverable | Description | Status |
|-------------|-------------|--------|
| AOS Data & Deployment Architecture | Main architecture document | Completed |
| AOS Data Levels | Defines public, private, personal, sensitive, and credential data | Completed |
| Atlas Offline / Online Model | Defines local and online modes | Completed |
| Atlas Budget Control Rules | Defines cost-control system | Completed |
| Device Agent Architecture | Defines future device deployment approach | Completed |
| PRJ-004 Lessons Learned | Captures what the company learns | Completed |
| Project Completion Decision | Decides whether PRJ-004 is complete | Completed |

---

# 14. Project Tasks

| Task ID | Task | Status |
|---------|------|--------|
| PRJ-004-T001 | Create PRJ-004 project record | Completed |
| PRJ-004-T002 | Add PRJ-004 to Project Register | Completed |
| PRJ-004-T003 | Create AOS Data & Deployment Architecture document | Completed |
| PRJ-004-T004 | Define data levels and storage rules | Completed |
| PRJ-004-T005 | Define offline and online Atlas modes | Completed |
| PRJ-004-T006 | Define budget control rules | Completed |
| PRJ-004-T007 | Define device agent architecture | Completed |
| PRJ-004-T008 | Run Markdown Audit Tool | Not Started |
| PRJ-004-T009 | Capture lessons learned | Completed |
| PRJ-004-T010 | Complete PRJ-004 | Completed |

---

# 15. Risks

| Risk | Response |
|------|----------|
| Atlas becomes too broad too early | Keep PRJ-004 as architecture only |
| Sensitive data gets mixed with public repo | Enforce data separation rules |
| AI API costs become uncontrolled | Require budget layer |
| Offline mode is overpromised | Define realistic offline capabilities |
| Device agents become unsafe | Require permission and audit rules |
| Market pressure creates panic | Move fast, but through AOS discipline |

---

# 16. Progress Log

| Date | Progress |
|------|----------|
| 2026-07-10 | PRJ-004 created to define AOS Data & Deployment Architecture. |
| 2026-07-10 | Main AOS Data & Deployment Architecture document created as ADDA-001. |
| 2026-07-10 | PRJ-004 lessons learned were documented in PRJLESSON-004. |
| 2026-07-10 | PRJ-004 was completed after the AOS Data & Deployment Architecture and lessons learned were documented. |

---

# 17. Recommended Next Action

Create the main architecture document:

```text
AOS_Data_and_Deployment_Architecture.md
```

This document will become the official foundation for Atlas offline mode, online mode, cost control, data storage, and future device agents.

---

# Project Completion

## Completion Date

2026-07-10

## Final Status

Completed

## Completion Summary

PRJ-004 — AOS Data & Deployment Architecture is completed.

The purpose of PRJ-004 was to define how AOS data, Atlas, online AI models, local tools, device agents, and future deployments should work together safely.

This purpose was achieved.

PRJ-004 produced the first approved architecture for:

- AOS data storage,
- offline Atlas mode,
- online Atlas mode,
- AI cost control,
- device agents,
- permission levels,
- sensitive data protection,
- credential protection,
- audit logging,
- future Atlas Super Assistant architecture,
- future AOS Partner Factory.

---

## Final Deliverables

| Deliverable | Status |
|-------------|--------|
| AOS Data & Deployment Architecture | Completed |
| AOS Data Levels | Completed |
| Atlas Offline / Online Model | Completed |
| Atlas Budget Control Rules | Completed |
| Device Agent Architecture | Completed |
| PRJ-004 Lessons Learned | Completed |
| Project Completion Decision | Completed |

---

## Completion Decision

PRJ-004 is completed.

The AOS Data & Deployment Architecture is approved as the foundation for future Atlas deployment work.

Future Atlas Super Assistant work should become a separate project:

```text
PRJ-005 — Atlas Super Assistant Architecture
```

Future Partner creation and management work should become:

```text
PRJ-006 — Build AOS Partner Factory
```

---

## Reason for Completion

PRJ-004 is complete because:

1. The main architecture document was created.
2. Data levels were defined.
3. Offline Atlas mode was defined.
4. Online Atlas mode was defined.
5. AI model usage tiers were defined.
6. Budget control rules were defined.
7. Device agent principles were defined.
8. Permission levels were defined.
9. Sensitive data and credential rules were defined.
10. Audit log rules were defined.
11. Lessons learned were documented.
12. The architecture prepares PRJ-005 and PRJ-006.

---

## Future Work

Future work should not keep PRJ-004 open forever.

Future work should become separate projects, such as:

- PRJ-005 — Atlas Super Assistant Architecture
- PRJ-006 — Build AOS Partner Factory
- Atlas Online AI Gateway
- Atlas Budget Monitor
- Atlas Device Agent Prototype
- Microsoft Teams Integration
- AOS Secure Vault Architecture
- AOS Audit Log System

---

## Final Lesson

PRJ-004 proved that Atlas must not be built as a random uncontrolled AI agent.

The final architecture principle is:

```text
Atlas must be useful offline,
powerful online,
controlled by budget,
protected by permissions,
and trusted through audit logs.
```

PRJ-004 is now completed.