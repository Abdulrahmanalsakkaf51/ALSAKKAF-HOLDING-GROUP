# ALSAKKAF HOLDING GROUP

# Atlas Revenue Task Routing v1

> "Every task has an owner, a support Partner, and an approval gate. Nothing routes itself around the CEO."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RTASK-001 |
| Document Type | Partner Task Routing |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Date | 2026-07-13 |
| Related System | AOS |
| Related Project | PRJ-007 |
| Related Documents | PRJ-007, PREG-001, POM-001, STRAT-008, GRCA-001 |

---

# 1. Purpose

This document defines which Partner does which task type during the AOS Revenue Launch (PRJ-007), what input each task needs, what output it produces, and — most importantly — exactly which tasks require explicit CEO approval before they happen.

No task in this document authorizes sending, publishing, pricing, spending, or real account creation on its own. Those actions stay CEO-approval-gated regardless of which Partner prepared the work.

---

# 2. Active Partners

| Partner | Role in Revenue Launch |
|---------|--------------------------|
| Atlas (PARTNER-002) | CEO command, planning, lead scoring, outreach/content drafting, reporting, task routing coordination |
| The Librarian (PARTNER-001) | Indexing, knowledge retrieval, filing, document classification for every Revenue Launch document and record |
| Guardian (PARTNER-016) | Security, compliance, credential protection, account-security review, risk review |

These three Partners are the only active Partners performing Revenue Launch work today.

---

# 3. Proposed Future Partners — Not Activated

The following Partners are referenced in planning documents (STRAT-005 through STRAT-014) as intended future owners of specific work, but **none of them is active**. No task in this document may be assigned to them as a real execution owner; they appear here only as forward-looking labels.

| Partner | Eventual Intended Role |
|---------|--------------------------|
| Marketing Partner | Future owner of campaign execution and paid ad management, once activated through the Partner Factory (PRJ-006) |
| Client Acquisition Partner | Future owner of lead research and outreach batch execution at scale |
| Content Partner | Future owner of day-to-day content production and posting across platforms |
| Reporting Partner | Future owner of recurring revenue/expense/content KPI reporting |
| Ecommerce Partner | Future owner of the dropshipping/marketplace experiment (STRAT-011), if it scales |
| Finance Partner | Future owner of budgeting, invoicing, and financial tracking beyond the current CSV-based system |
| Legal/Compliance Partner | Future owner of contract review, terms/privacy pages, and regulatory compliance checks |

Activating any of these Partners requires the full Partner Factory lifecycle (PCL-001) and explicit Founder approval — this document does not activate, imply activation of, or change the Partner Registry status of any of them.

---

# 4. Task Routing Table

| Task Type | Task Owner | Support Partner | Input Needed | Output Produced | CEO Approval Required | Risk Level | Payment/Cost Status | Audit/Logging Requirement |
|-----------|------------|------------------|---------------|-------------------|-------------------------|------------|------------------------|------------------------------|
| Lead Research | Atlas | The Librarian (filing) | Manual/public business information provided or found by the Founder; no scraping or automated network tools | Draft rows in `Lead_Tracker.csv` | No — research and drafting only | Low | No cost | Logged in `Lead_Tracker.csv`; summarized in Atlas daily report |
| Lead Scoring | Atlas | — | Lead Tracker row with available fields | Lead Score and Status per STRAT-008 scoring model | No — scoring is a recommendation, not a commitment | Low | No cost | Logged in `Lead_Tracker.csv` |
| Outreach Drafting | Atlas | Guardian (if any data-sensitivity question arises) | Approved outreach template, lead detail | Draft message in `Outreach_Tracker.csv` with CEO Approved = No | No — drafting only | Low | No cost | Logged in `Outreach_Tracker.csv` |
| Outreach Sending | Founder (CEO) | Atlas prepares the batch only | CEO-approved message template and CEO-approved recipient list | Sent message, tracked reply status | **Yes — always.** CEO approves the exact message and recipient before any send | Medium | No cost unless a paid outreach tool is later approved | Logged in `Outreach_Tracker.csv` with Date Sent and CEO Approved = Yes |
| Content Drafting | Atlas | The Librarian (filing into content calendar) | Content pillar, platform, format | Draft post/script in `Content_Calendar.csv` or script bank | No — drafting only | Low | No cost | Logged in `Content_Calendar.csv` |
| Content Publishing | Founder (CEO) | Atlas prepares the queued draft only | CEO-approved final copy and platform | Published post | **Yes — always.** No content is posted by Atlas or any Partner on its own authority | Medium | No cost unless paid promotion is separately approved | Logged in `Content_Analytics_Tracker.csv` after publish |
| Proposal Drafting | Atlas | — | Client scope discussion notes, STRAT-007 offer reference | Draft proposal from `Proposal_Template.md` | No — drafting only | Low | No cost | Logged in `Client_Pipeline.csv` |
| Pricing / Deal Close | Founder (CEO) | Atlas documents the close, does not negotiate | Client discussion, proposal draft | Final agreed price and terms | **Yes — always.** No price is finalized and no deal is accepted without explicit CEO sign-off | High | Determines actual revenue — CEO must confirm before commitment | Logged in `Client_Pipeline.csv` and `Atlas_Decision_Log.md` |
| Client Delivery Work | Founder (CEO), Atlas assists with drafting deliverables | The Librarian (filing finished deliverables) | Confirmed scope from the closed deal | Delivered workflow/dashboard/checklist package per STRAT-007 | No for drafting; **Yes** before final handoff to the client | Medium | No cost beyond time unless a paid tool is required (separately approved) | Logged in `Client_Pipeline.csv` Delivery Status |
| Payment Link Handling | Founder (CEO) | Atlas may reference the approved link in drafts only after client confirms interest | Client confirmation of intent to pay | Payment link shared with client; payment confirmation noted | **Yes — always.** Only the one approved link (STRAT-014) may ever be shared, and only after the CEO/Atlas has confirmed the client wants to proceed | Medium | Payment collected in USD via the approved PayPal link only | Logged in `Client_Pipeline.csv` Payment Status; no credential ever logged |
| Account Security Review | Guardian | Atlas routes the request | Proposed account or existing account details (metadata only, never credentials) | Security review note (2FA, recovery email, password manager checklist) | **Yes** before any real account is used for business activity | Medium–High | No cost | Logged in `Atlas_Decision_Log.md` |
| Document Filing / Indexing | The Librarian | Atlas hands off finished documents | Approved, finished document | Indexed entry, discoverable reference | No — indexing is not a public or spend action | Low | No cost | Logged via Knowledge Register update |
| Dashboard / KPI Updates | Atlas | The Librarian (source-of-truth filing) | Current tracker data (Lead/Outreach/Client Pipeline/Content CSVs) | Updated `Atlas_Revenue_Dashboard.md` and `docs/atlas-dashboard-data.js` placeholder values | No — internal reporting only | Low | No cost | Logged as a dashboard update note in `Atlas_Decision_Log.md` |
| Risk / Compliance Review | Guardian | Atlas routes the request | Any proposed tool, workflow, or client data-handling question | Risk review note, recommendation, escalation if High severity | No to review itself; **Yes** on whatever action the review is about (e.g. adopting a tool, sharing data) | Varies by finding | No cost | Logged in `Atlas_Decision_Log.md` |

---

# 5. Standing Rule

Atlas may research, score, draft, summarize, recommend, prepare batches, and track progress across every task type above. Atlas may never send, publish, price, close, spend, or create a real account on its own authority. Guardian reviews security and risk questions but does not itself execute the underlying action. The Librarian indexes finished, approved material — it does not originate outreach, content, or pricing decisions.

---

# 6. Related Documents

- PRJ-007 — Launch AOS Revenue Engine
- PREG-001 — Partner Registry
- POM-001 — Partner Operating Model
- STRAT-008 — AOS Client Lead Pipeline and Outreach System
- GRCA-001 — AOS Governance, Risk, Compliance & Assurance Roadmap
- PARTNER-002_Atlas_Revenue_Operator_Prompt.md (ARPROMPT-001)

---

# 7. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version — task routing table created for AOS Launch Version v1 |
