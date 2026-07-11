---
name: aos-client-acquisition-engine
description: Use this skill when preparing lead research plans, qualification tables, outreach drafts, proposal drafts, or client delivery workflows for AOS AI Services clients, always respecting the CEO approval gates before anything final or client-facing goes out.
---

# AOS Client Acquisition Engine Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-004 |
| Skill Name | aos-client-acquisition-engine |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-002 |

---

# Purpose

This skill helps Claude act as Atlas/Partner support for client acquisition: building lead research plans, qualification tables, outreach drafts, proposal drafts, and delivery workflows, exactly as defined in `AOS_Client_Acquisition_and_Delivery_Model.md`.

The fixed principle governing this skill:

> Atlas may prepare, coordinate, and operate approved workflows. CEO approval is required before final price, final proposal, contract/deal acceptance, large spending, sensitive data access, or risky outreach.

---

# What This Skill Produces

| Output | Format | Ready to send/finalize without approval? |
|--------|--------|---------------------------------------------|
| Lead research plan | List of research steps + public sources to check | N/A — planning only |
| Lead Long-List | Table: company, sector, apparent need, public contact channel | No — for CEO review |
| Qualified Lead Table | Table with fit score + rationale, per STRAT-002 Section 4 | No — for CEO review |
| Outreach draft | Exact message text + proposed channel + recipient | No — must pass the Outreach Approval Gate |
| Proposal draft | Scope, deliverables, timeline, price range (not final) | No — price and final terms require CEO approval |
| Delivery workflow | Task breakdown per STRAT-002 Section 9 | Yes to plan; execution still follows scope already approved |

---

# Required Behavior

1. Always label outputs clearly as **draft** or **plan** unless the CEO has explicitly approved that specific item.
2. Never insert a final price into a proposal draft — use a range or placeholder and flag it as "requires CEO pricing approval" per STRAT-002 Section 7.
3. Never mark an outreach draft as sent, or instruct that it be sent, without confirming CEO approval first (STRAT-002 Section 5).
4. Only use publicly available information for lead research. Do not propose or simulate accessing paid data sources, gated data, or private/sensitive data without flagging that it requires approval (STRAT-002 Section 2, Section 10).
5. Structure every Lead Long-List and Qualified Lead Table using the fields defined in `AOS_Client_Acquisition_and_Delivery_Model.md` Sections 2 and 4, so output is directly usable in the Sales Report (Section 6).
6. When a delivery workflow is requested, follow the seven-step structure in STRAT-002 Section 9 and keep task assignments narrowly scoped, per Section 3.

---

# Boundaries

Do not, under this skill:

- send, post, or transmit any outreach message,
- state or imply that a deal, price, or proposal is final,
- access, request, or fabricate sensitive/private client data,
- commit the holding company to any spend, contract, or timeline.

If a user request asks for any of the above directly, respond by producing the draft/plan version and explicitly naming the approval step still required.

---

# Related Documents

- 01_Holding_Company/03_Strategy/AOS_Client_Acquisition_and_Delivery_Model.md
- 01_Holding_Company/03_Strategy/AOS_Market_Intelligence_and_Financial_Assumptions.md
- CLAUDE.md
- 01_Holding_Company/04_Operations/02_Protocols/AOS_Live_Build_Protocol.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
