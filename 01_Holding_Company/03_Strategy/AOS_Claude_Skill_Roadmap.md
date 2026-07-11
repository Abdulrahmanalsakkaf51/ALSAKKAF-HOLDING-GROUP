# ALSAKKAF HOLDING GROUP

# AOS Claude Skill Roadmap

> "A skill is a role with discipline built in."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | STRAT-004 |
| Document Type | Strategy Document |
| Status | Draft |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Created | 2026-07-12 |
| Last Updated | 2026-07-12 |
| Related System | AOS |
| Related Protocol | OPS-001 |
| Related Project | PRJ-006 |
| Related Document | STRAT-003 |

---

# 1. Purpose

This document defines why ALSAKKAF HOLDING GROUP builds Claude skills, what separates an AOS skill from a generic third-party skill, the current active skill set, the newly proposed "AOS Command Center" skill pack, and the rules governing how any skill is approved, tested, secured, and eventually retired.

This document does not activate any skill by itself. A skill listed here becomes usable only once its `SKILL.md` file exists, has been reviewed, and follows the rules in this document.

---

# 2. Why AOS Needs Claude Skills

AOS work is repeatable: documents follow the same Document Information structure, registers follow the same indexing rule, approval gates follow the same pattern (draft → Founder review → approval → action). Claude skills encode that repeatable discipline so that:

- every session of work starts from the same rules instead of being re-explained,
- Claude's output is predictable and audit-friendly across sessions,
- the Founder can review a change against a known standard instead of a blank page,
- future Partners (PRJ-006 AOS Partner Factory) can be built on top of proven skill patterns.

---

# 3. AOS Skills vs. Random Third-Party Skills

| | AOS Skill | Generic Third-Party Skill |
|---|-----------|----------------------------|
| Language | Uses AOS vocabulary (Atlas, Partners, The Librarian, Knowledge Register, Founder) | Uses whatever vocabulary the author chose |
| Approval gates | Always defers final/sent/spent/committed actions to Founder approval | May assume full autonomy |
| Document format | Follows Document Information, Status, Revision History structure | No fixed structure |
| Registers | Updates Knowledge Register and other registers when it creates official knowledge | No concept of a register |
| Security posture | Explicit boundaries section; no hacking, no credentials, no unauthorized data access | Often unstated |
| Origin | Purpose-built for this repository and this company | Imported wholesale from an external source |

A skill inspired by an outside idea (see `AOS_Inspiration_Register.md`) only becomes an AOS skill once it has been rewritten to satisfy every row in the table above.

---

# 4. Current Active Claude Skills

| Skill | Document ID | Purpose |
|-------|-------------|---------|
| `aos-live-build` | CSKILL-001 | Structured repository changes: inspect, plan, edit, audit, Founder approval |
| `aos-markdown-audit` | CSKILL-002 | Run and interpret the Markdown Audit Tool after Markdown edits |
| `aos-holding-company-operator` | CSKILL-003 | Cross-module holding company reasoning and priority setting |
| `aos-client-acquisition-engine` | CSKILL-004 | Lead research, qualification, outreach/proposal drafts, delivery workflow |
| `aos-financial-forecast` | CSKILL-005 | Revenue/expense/profit/scenario forecasts, traceable to STRAT-001 |
| `aos-learning-loop` | CSKILL-006 | Capture outcomes and lessons; propose (not auto-apply) improvements |

---

# 5. New Proposed AOS Command Center Skills

Inspired by the Founder's uploaded videos and a GStack-style role-skill model (see `AOS_Inspiration_Register.md` Section 13), translated into AOS language:

| Skill | Proposed ID | Role It Replaces/Represents |
|-------|-------------|------------------------------|
| `aos-ceo-command-center` | CSKILL-007 | CEO-level briefings, priorities, approvals, decision logs |
| `aos-dashboard-builder` | CSKILL-008 | Local KPI tables, chart plans, source notes, CEO reporting pages |
| `aos-youtube-shorts-factory` | CSKILL-009 | Legal, original Shorts content workflow from owned/licensed footage |
| `aos-marketing-ads-factory` | CSKILL-010 | Campaign plans, ad angles, budget caps, performance review |
| `aos-guardian-cybersecurity` | CSKILL-011 | Defensive security planning, risk registers, future Guardian Partner design |
| `aos-cto-architect` | CSKILL-012 | Folder structure, system design, Partner architecture, safe automation |
| `aos-document-engineer` | CSKILL-013 | Clean AOS documents, correct structure, Markdown Audit compliance |
| `aos-qa-auditor` | CSKILL-014 | Review changed files for AOS quality, register gaps, unsafe patterns |
| `aos-release-manager` | CSKILL-015 | Safe release summaries, diff review, commit message drafts, push readiness |
| `aos-product-designer` | CSKILL-016 | Simple, useful, non-confusing user-facing workflows and templates |

Together these ten skills form the **AOS Command Center Skill Pack**.

---

# 6. Skill Priority Table

| Priority | Skill | Reason |
|----------|-------|--------|
| 1 | `aos-document-engineer` | Every other skill produces documents; this one keeps them audit-clean |
| 1 | `aos-qa-auditor` | Catches register/quality gaps across all other skill output before Founder review |
| 2 | `aos-ceo-command-center` | Directly supports the Founder's daily decision load |
| 2 | `aos-cto-architect` | Needed before PRJ-006 Partner Factory architecture work begins |
| 3 | `aos-dashboard-builder` | High reuse across every module (per STRAT-001 Section 2) |
| 3 | `aos-release-manager` | Reduces risk on every future commit/push cycle |
| 4 | `aos-marketing-ads-factory` | Supports Marketing and Dropshipping lines once activated |
| 4 | `aos-youtube-shorts-factory` | Supports YouTube/Content line once activated |
| 5 | `aos-guardian-cybersecurity` | Longer-term per STRAT-001 Section 2; planning-only for now |
| 5 | `aos-product-designer` | Cross-cutting polish; most valuable once other skills produce output to refine |

Priority reflects build order, not business importance. All ten are created in this build; priority guides which the Founder exercises/tests first.

---

# 7. Skill Approval Rules

1. A skill file may be created following the AOS Live Build flow (inspect, plan, edit, audit) without separate pre-approval, provided it stays inside the boundaries in this document and CLAUDE.md.
2. A skill is **Draft** until the Founder has reviewed its `SKILL.md` content at least once.
3. A skill moves to **Active** only after: it exists, is reviewed, is added to the Knowledge Register, and the Founder has confirmed it may be used.
4. Any change to an existing skill's boundaries, approval logic, or security rules requires the same review — it is treated as a new approval event, not a silent edit.
5. No skill may activate a new Partner as a side effect of being used. Partner activation still follows CLAUDE.md Section 4 in full (profile, prompt, test log, approval, registry update).

---

# 8. Skill Testing Rules

1. Before a skill is treated as reliable, the Founder should exercise it on at least one real (or realistic) task and confirm the output matches AOS structure and tone.
2. Skills that touch registers (`aos-qa-auditor`, `aos-document-engineer`) should be tested against an existing document to confirm they correctly detect known-good and known-bad cases.
3. Skills that touch release/commit workflow (`aos-release-manager`) must be tested to confirm they never execute `git commit` or `git push` themselves — only draft/summarize.
4. Test outcomes worth keeping (a skill caught a real gap, or a skill produced a wrong recommendation) should be captured through `aos-learning-loop`, not left undocumented.

---

# 9. Skill Security Rules

Every AOS Command Center skill must:

- avoid network access and paid API usage unless the Founder has explicitly approved that specific tool (CLAUDE.md Section 4, "New tool" row),
- never store or request credentials, API keys, or passwords in any file it produces,
- never mix private/sensitive data into public-repository files,
- treat any action that is hard to reverse (commit, push, send, spend, delete, rename an official folder) as requiring explicit Founder approval, with no exceptions,
- stay inside its stated purpose — a marketing skill does not perform security tasks, a dashboard skill does not draft outreach messages, etc.

`aos-guardian-cybersecurity` carries an additional, absolute rule: it must never perform hacking, exploitation, credential theft, or unauthorized testing of any system, real or simulated, inside this repository or elsewhere.

---

# 10. How Skills Support PRJ-006 AOS Partner Factory

PRJ-006 is reserved for building the AOS Partner Factory — the system that turns a validated role into a formally activated Partner (profile, prompt, test log, approval, registry update).

The AOS Command Center skills are a proving ground for that factory:

- each skill is a role definition in miniature (purpose, required behavior, boundaries) — the same shape a future Partner profile needs,
- `aos-qa-auditor` and `aos-document-engineer` establish the quality bar a Partner Factory output must meet,
- `aos-cto-architect` is expected to directly inform the Partner Factory's technical design,
- lessons captured via `aos-learning-loop` while using these skills become input to PRJ-006 requirements once that project is opened.

No skill in this document activates PRJ-006 or any Partner. This section only records the intended relationship for future planning.

---

# 11. Related Documents

- CLAUDE.md
- 01_Holding_Company/04_Operations/02_Protocols/AOS_Live_Build_Protocol.md
- 01_Holding_Company/03_Strategy/AOS_Inspiration_Register.md
- 01_Holding_Company/03_Strategy/AOS_Market_Intelligence_and_Financial_Assumptions.md
- 01_Holding_Company/01_Governance/Knowledge_Register.md

---

# 12. Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial draft defining the AOS Command Center skill pack and governing rules |

---
