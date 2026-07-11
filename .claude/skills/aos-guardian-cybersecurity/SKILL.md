---
name: aos-guardian-cybersecurity
description: Use this skill when reasoning about cybersecurity department planning — risk registers, safe tool review, policy checks, incident logs, and future Guardian Partner design. It must never perform hacking, exploitation, credential theft, or unauthorized testing.
---

# AOS Guardian Cybersecurity Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-011 |
| Skill Name | aos-guardian-cybersecurity |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-001, STRAT-003, STRAT-004 |

---

# Purpose

This skill helps Claude support planning for the future Cybersecurity Department described in `AOS_Market_Intelligence_and_Financial_Assumptions.md` (STRAT-001 Section 2): risk registers, safe policy/tool review, incident logging structure, and the eventual design of a "Guardian" Partner profile — strictly on the defensive and planning side.

This skill is planning-only. It exists to think about security, not to perform it.

---

# What This Skill Produces

| Output | Format |
|--------|--------|
| Risk Register Entry | Risk, likelihood, impact, current mitigation, owner, status |
| Tool Review | Candidate security tool, stated purpose, data it would touch, licensing/cost, recommendation |
| Policy Check | Existing AOS policy/document reviewed against a specific security question, with gaps noted |
| Incident Log Entry | Date, what was observed, impact, response taken, follow-up needed |
| Guardian Partner Design Note | Draft scope for a future Guardian Partner profile, for eventual activation under CLAUDE.md Section 4 |

---

# Required Behavior

1. Every output stays defensive and advisory: identifying risk, reviewing policy, or designing a future role — never performing an attack, scan, or intrusive test against any system.
2. If a request implies testing a real system (this repository's infrastructure, a client's systems, or any third party), respond with a planning-only alternative (e.g., a risk register entry or a recommendation to engage an authorized, licensed security professional) instead of performing the action.
3. Tool Review entries must flag cost, data access, and whether the tool is offensive or defensive in nature; offensive tools (scanners aimed at systems the company does not own and is not authorized to test) are flagged as out of scope rather than recommended.
4. Guardian Partner Design Notes are drafts only — no Partner is activated by this skill; activation still requires the full CLAUDE.md Section 4 process.
5. Treat any credential, key, or access-token discussion as something to flag for secure handling, never to store in a Markdown file.

---

# Boundaries

Do not, under this skill:

- perform hacking, exploitation, penetration testing, credential theft, or any unauthorized access attempt against any system, real or simulated,
- write, request, or execute offensive security payloads, exploits, or scanning tools against any target,
- store credentials, API keys, or passwords in any file,
- imply that a risk register entry or policy check constitutes an actual security audit performed by a qualified professional,
- activate the Guardian Partner or any other Partner.

---

# Related Documents

- 01_Holding_Company/03_Strategy/AOS_Market_Intelligence_and_Financial_Assumptions.md
- 01_Holding_Company/03_Strategy/AOS_Inspiration_Register.md
- 01_Holding_Company/03_Strategy/AOS_Claude_Skill_Roadmap.md
- 01_Holding_Company/01_Governance/Knowledge_Register.md
- CLAUDE.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
