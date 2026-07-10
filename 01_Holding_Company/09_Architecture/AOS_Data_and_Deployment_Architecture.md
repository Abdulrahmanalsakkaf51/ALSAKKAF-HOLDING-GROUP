# ALSAKKAF HOLDING GROUP

# AOS Data & Deployment Architecture

> "Atlas must be useful offline, powerful online, and controlled by permission, privacy, and budget."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | ADDA-001 |
| Document Type | Architecture Document |
| Related Project | PRJ-004 |
| Status | Approved |
| Version | 1.0 |
| Date | 2026-07-10 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Partner | PARTNER-002 — Atlas |
| Related Future Project | PRJ-005 — Atlas Super Assistant Architecture |

---

# 1. Purpose

This document defines the first official AOS Data & Deployment Architecture.

Its purpose is to explain:

- where AOS data should live,
- what Atlas can do offline,
- what Atlas can do online,
- how Atlas should control AI cost,
- how future device agents should connect,
- how sensitive data should be protected,
- how Atlas can become powerful without becoming unsafe.

---

# 2. Core Architecture Principle

The core architecture principle is:

```text
Local first.
Online when valuable.
Budget controlled.
Permission protected.
Audit logged.
Founder approved.
```

This means Atlas should not depend on constant internet access.

Atlas should remain useful locally, but become more powerful when connected to approved online AI services.

---

# 3. High-Level Architecture

The preferred AOS architecture is:

```text
Founder / CEO
↓
Atlas Core
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

---

# 4. Architecture Layers

| Layer | Purpose |
|------|---------|
| Founder / CEO | Final authority and approval |
| Atlas Core | Main executive operating Partner |
| AOS Knowledge Vault | Approved documents, decisions, projects, and lessons |
| Local Tools | Safe local tools such as Markdown Audit and Librarian |
| Online AI Gateway | Controlled connection to powerful cloud AI |
| Cost Control Layer | Prevents uncontrolled AI spending |
| Permission Layer | Controls what Atlas can read, draft, send, edit, or execute |
| Device Agents | Future controlled agents for Windows, Mac, Android, iOS, and other systems |
| Audit Log | Records important actions, decisions, and system behavior |

---

# 5. Data Levels

AOS data must be separated by sensitivity.

| Data Level | Name | Example | Storage Direction |
|-----------|------|---------|------------------|
| Level 1 | Public AOS Knowledge | Public philosophy, general blueprints, non-sensitive documents | GitHub public or shareable repository |
| Level 2 | Private Company Knowledge | Strategy, business plans, financial planning, private roadmaps | Private local storage or private cloud |
| Level 3 | Personal Work Data | ASC tasks, training plans, drafts, non-sensitive work materials | Separate work storage |
| Level 4 | Sensitive Records | Student IDs, student names, employee records, private communications | Official approved systems only |
| Level 5 | Credentials | API keys, passwords, tokens, secrets | Secure vault only |

---

# 6. GitHub Storage Rule

GitHub should only store approved AOS documentation and safe project files.

GitHub may store:

- public blueprints,
- project records,
- Partner profiles,
- workflows,
- non-sensitive architecture,
- lessons learned,
- local tool code that does not expose secrets.

GitHub must not store:

- passwords,
- API keys,
- private student data,
- employee records,
- confidential finance data,
- sensitive customer data,
- private institutional records,
- personal identity records.

---

# 7. Offline Atlas Mode

Atlas should remain useful even when the internet is unavailable.

Offline Atlas should be able to:

| Offline Capability | Requirement |
|-------------------|-------------|
| Search AOS documents | Required |
| Run local tools | Required |
| Audit Markdown files | Required |
| Read local project records | Required |
| Prepare templates | Required |
| Generate basic reports from saved data | Required |
| Track project status from local files | Required |
| Queue messages for later review | Future |
| Use a local AI model | Future |
| Send live messages | Not available offline |
| Search the live web | Not available offline |
| Use cloud AI | Not available offline |

Offline Atlas is the resilience layer.

It keeps the company working during internet outages.

---

# 8. Online Atlas Mode

When internet is available, Atlas may connect to approved online AI services.

Online Atlas may support:

| Online Capability | Purpose |
|------------------|---------|
| Deep reasoning | Strategy, architecture, analysis |
| Research | Web, market, technical, and competitive research |
| Advanced writing | Reports, ads, scripts, training content |
| Coding help | Tools, debugging, automation |
| Executive assistance | Drafting, planning, coordination |
| Integrations | Teams, Outlook, Calendar, dashboards, business systems |
| Model routing | Choosing cheap or powerful models based on task importance |

Online Atlas must be controlled by:

- budget limits,
- privacy rules,
- approved data access,
- Founder approval,
- audit logging.

---

# 9. AI Model Usage Tiers

Atlas should not use one expensive model for every task.

Atlas should use tiers.

| Tier | Model Type | Use Case |
|------|------------|----------|
| Tier 0 | No AI / local logic | File checks, audits, simple rules |
| Tier 1 | Local model | Basic summaries and offline support |
| Tier 2 | Cheap online model | Simple drafts, classification, short summaries |
| Tier 3 | Strong online model | Strategy, planning, technical design, important writing |
| Tier 4 | Premium online model | Critical decisions, complex architecture, high-value work |

---

# 10. Budget Control Rules

Atlas must never spend money secretly.

Early budget rules:

| Budget Rule | Value |
|------------|-------|
| Target monthly AI cost | 5 to 20 USD |
| Maximum early monthly cost | 50 USD |
| Warning level | 50% of monthly budget |
| Approval required | Before premium or heavy tasks |
| Hard stop | At monthly limit unless Founder approves |
| Default mode | Local or cheap model first |

The core budget rule is:

```text
Atlas should be online-capable, not online-wasteful.
```

---

# 11. Cost Control Behavior

Atlas should follow this decision path before using paid AI:

```text
Can this be done locally?
↓
If yes, do it locally.
↓
If no, can a cheap model do it?
↓
If yes, use cheap model.
↓
If no, is the task important enough for a strong model?
↓
If yes, ask for approval when needed.
↓
If approved, use strong model.
↓
Record cost and result.
```

---

# 12. Device Agent Architecture

Atlas should not become one uncontrolled agent on every device.

The future architecture should use controlled device agents.

| Device / Platform | Future Approach |
|-------------------|-----------------|
| Windows | Local desktop agent and tools |
| macOS | Local desktop agent and tools |
| Linux | Local server or workstation agent |
| Android | Controlled mobile agent with strict permissions |
| iPhone / iPad | Shortcuts, app actions, approved integrations |
| Web apps | APIs first, browser automation only when needed |
| Microsoft 365 | Official APIs first, especially Microsoft Graph |
| Company server | Future central Atlas deployment |

Device agents should:

- act only with permission,
- report back to Atlas,
- log important actions,
- avoid storing sensitive data unnecessarily,
- never receive unlimited access.

---

# 13. Skills Architecture

Atlas should gain abilities through approved skills.

A skill is a reusable capability.

Examples:

| Skill | Purpose |
|------|---------|
| Markdown Audit Skill | Check Markdown quality |
| Librarian Skill | Search approved knowledge |
| Daily Briefing Skill | Prepare Founder briefing |
| Meeting Skill | Prepare meeting agenda and notes |
| Teams Announcement Skill | Draft Teams channel posts |
| Training Program Skill | Create training plans and materials |
| Travel Coordination Skill | Prepare travel plans and checklists |
| Marketing Campaign Skill | Prepare ads, scripts, and campaigns |
| Research Skill | Research a topic and summarize findings |
| Git Support Skill | Help prepare safe commits |

No skill should become active until it has:

- purpose,
- requirements,
- permission level,
- test log,
- approval,
- audit behavior.

---

# 14. Permission Levels

Atlas actions must be controlled by permission levels.

| Permission Level | Description | Example |
|------------------|-------------|---------|
| Level 0 | Read-only | Read approved documents |
| Level 1 | Draft only | Draft emails, posts, reports |
| Level 2 | Suggest action | Recommend schedule, task, or message |
| Level 3 | Execute with approval | Send message after Founder approves |
| Level 4 | Limited automation | Run approved workflows with logs |
| Level 5 | Restricted / not allowed yet | Financial actions, sensitive records, uncontrolled device control |

Early Atlas should stay mostly within Levels 0 to 3.

---

# 15. Sensitive Data Rules

Sensitive data must be protected.

Atlas must not copy sensitive data into public AOS files.

Sensitive data includes:

- student IDs,
- student names connected to private records,
- employee records,
- passwords,
- API keys,
- financial secrets,
- personal identity documents,
- private communications,
- customer confidential data.

Atlas may help create drafts and workflows, but sensitive records should remain in approved systems.

---

# 16. Credential Rules

Credentials must never be written into normal Markdown files.

Credentials include:

- API keys,
- passwords,
- tokens,
- private keys,
- database secrets,
- service account files.

Credential storage direction:

| Credential Type | Storage Direction |
|-----------------|------------------|
| API keys | Secure vault or environment variables |
| Passwords | Password manager |
| Tokens | Secure vault |
| Private keys | Secure secret storage |
| Test placeholder keys | Allowed only if clearly fake |

---

# 17. Audit Log Rule

Important Atlas actions must be recorded.

The audit log should record:

| Item | Meaning |
|------|---------|
| Date | When the action happened |
| Actor | Atlas, device agent, tool, or Founder |
| Action | What happened |
| Data used | What source was accessed |
| Permission level | Approval level |
| Approval status | Approved, rejected, automatic, or draft |
| Result | Success, failed, pending |
| Notes | Important observations |

The audit log protects trust.

---

# 18. Deployment Stages

AOS deployment should happen in stages.

| Stage | Name | Description |
|------|------|-------------|
| Stage 1 | Local Foundation | Documents, Git, Python tools, local files |
| Stage 2 | Manual Atlas | Atlas works through prompts and approved documents |
| Stage 3 | Local Tooling | Librarian, Markdown Audit, future local tools |
| Stage 4 | Controlled Online AI | Atlas connects to online AI through budget and permission rules |
| Stage 5 | Device Agents | Controlled agents for Windows, Mac, Android, and iOS |
| Stage 6 | Organization Deployment | Atlas and Partners support teams and companies |
| Stage 7 | Partner Factory | AOS creates and manages approved Partners |

---

# 19. What Atlas Must Never Do Early

Atlas must not:

- spend money without approval,
- access sensitive data without permission,
- send messages without approval,
- delete files automatically,
- edit official records without review,
- control devices without logs,
- store credentials in plain text,
- mix ADU/student data with public company files,
- pretend unavailable data exists,
- become a fully autonomous uncontrolled agent.

---

# 20. Strategic Direction

Atlas should become more than a chatbot.

Atlas should become the operating Partner for AOS.

The strategic direction is:

```text
Atlas Core
↓
AOS Skills
↓
Device Agents
↓
Partner Factory
↓
AI-Driven Organizations
```

This architecture prepares the way for:

- PRJ-005 — Atlas Super Assistant Architecture,
- PRJ-006 — AOS Partner Factory,
- future Microsoft Teams integrations,
- future mobile agents,
- future customer deployments.

---

# 21. Final Architecture Rule

The final rule is:

```text
Atlas must be always available locally,
powerful online when needed,
safe by permission,
limited by budget,
and trusted through audit logs.
```

---

# 22. Status

This architecture is approved as the first version of the AOS Data & Deployment Architecture.

Future projects may expand it, but all future Atlas deployment work should respect this foundation.