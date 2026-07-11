---
name: aos-holding-company-operator
description: Use this skill when reasoning about ALSAKKAF HOLDING GROUP as a whole — cross-module priorities, resource allocation, launch sequencing, or how AI Services, YouTube, Dropshipping, Marketing, Cybersecurity, and dashboards relate to each other as an AI-native synergy-driving holding company.
---

# AOS Holding Company Operator Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-003 |
| Skill Name | aos-holding-company-operator |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-001 |

---

# Purpose

This skill helps Claude reason about ALSAKKAF HOLDING GROUP as a single AI-native, synergy-driving holding company rather than a set of unrelated ideas.

Use it whenever a question or task touches more than one module (AI Services, YouTube, Dropshipping, Marketing, Cybersecurity, Local Dashboards/Reporting) or asks about holding-company-level priority, sequencing, or resource conflict.

---

# Operating Model

Treat the holding company as one Founder, one AOS system, one Atlas, one Partner workforce, and multiple modules — per `AOS_Market_Intelligence_and_Financial_Assumptions.md` Section 3.

When reasoning about any module-level request, check for synergy and conflict:

- **Synergy check**: Does this module's output feed another module? (e.g., AI Services delivery becomes YouTube content; dashboards serve every module at once.)
- **Conflict check**: Does this request compete with another module for the same scarce resource — Founder time, budget, or Partner capacity?
- **Sequencing check**: Does this request match the recommended launch order in `AOS_Market_Intelligence_and_Financial_Assumptions.md` Section 8, or does it ask to skip ahead?

---

# Required Reasoning Steps

1. Identify which module(s) the request touches.
2. Check the request against the financial assumptions (`AOS_Market_Intelligence_and_Financial_Assumptions.md`) and the launch order — flag if it contradicts either.
3. Check whether the request implies spending, contracts, hiring, or data access — if so, route it through the appropriate approval gate (CLAUDE.md Section 4; `AOS_Client_Acquisition_and_Delivery_Model.md` for client-facing items).
4. Surface synergy opportunities explicitly (e.g., "this dashboard build could double as an AI Services case study for YouTube") rather than treating modules as silos.
5. If a request would overextend the holding company (too many modules active at once relative to Founder/Partner capacity), say so directly and recommend a narrower scope.

---

# Boundaries

This skill informs reasoning and recommendations only. It does not:

- authorize spending, contracts, or Partner activation,
- override the approval gates defined in CLAUDE.md, OPS-001, or the Strategy documents,
- create a new module, project, or Partner on its own — that still requires the standard AOS flow (Project Register, Knowledge Register, Founder approval).

---

# Related Documents

- CLAUDE.md
- 01_Holding_Company/04_Operations/02_Protocols/AOS_Live_Build_Protocol.md
- 01_Holding_Company/03_Strategy/AOS_Market_Intelligence_and_Financial_Assumptions.md
- 01_Holding_Company/03_Strategy/AOS_Client_Acquisition_and_Delivery_Model.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
