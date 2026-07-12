# ALSAKKAF HOLDING GROUP

# AOS Revenue Dashboard Spec

> "If it is not tracked, AOS cannot tell whether the revenue engine is working."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | STRAT-013 |
| Document Type | Strategy Document |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-007 |
| Related Documents | STRAT-005, STRAT-006, STRAT-008, STRAT-010, STRAT-011, PRJ-007 |

---

# 1. Purpose

This document specifies a local, file-based dashboard (CSV/Excel/Markdown) for tracking Revenue Launch performance. It is not a request to build or deploy any online analytics tool or paid dashboard service. Any future paid dashboard tool would require separate CEO approval per CLAUDE.md Section 5 ("New tool" row).

---

# 2. KPIs

| KPI | Definition |
|-----|------------|
| Leads found | Number of candidate leads identified in the period |
| Leads qualified | Number of leads that passed qualification criteria (STRAT-008) |
| Outreach drafted | Number of outreach messages drafted by Atlas, awaiting CEO approval |
| Outreach approved | Number of drafted messages the CEO approved for sending |
| Outreach sent | Number of approved messages actually sent |
| Replies | Number of responses received from sent outreach |
| Meetings booked | Number of calls/meetings scheduled from replies |
| Proposals sent | Number of CEO-approved proposals delivered to prospects |
| Deals closed | Number of proposals converted into signed/agreed deals |
| Revenue | Total confirmed revenue for the period (AED) |
| Expenses | Total confirmed spend for the period (AED) |
| Profit | Revenue minus expenses for the period (AED) |
| Content produced | Number of content pieces drafted/edited, any platform |
| Content posted | Number of content pieces CEO-approved and actually published |
| Views | Total views across posted content |
| Followers | Total follower/subscriber count across active channels |
| Website visits | Number of visits to the live landing page (once published) |
| Ecommerce tests | Number of dropshipping/marketplace product tests currently active (STRAT-011) |
| Ad spend | Total CEO-approved ad spend for the period (AED) |

---

# 3. Local Dashboard Data Model

The dashboard is a single local spreadsheet workbook (Excel or CSV set), stored inside this repository or an approved local folder — no cloud database, no third-party analytics account, consistent with the local-first principle in `AOS_Data_and_Deployment_Architecture.md` (ADDA-001).

The workbook has five named tables (tabs, or separate CSV files if using plain CSV):

1. **Leads** — one row per lead
2. **Outreach** — one row per outreach message
3. **Deals** — one row per proposal/deal
4. **Content** — one row per content piece
5. **Finance** — one row per revenue/expense entry

A sixth summary tab/table (**KPI_Summary**) aggregates the above into the KPI list in Section 2, updated manually or via a simple local formula/script — no external service required.

---

# 4. Excel/CSV Fields

| Table | Columns |
|-------|---------|
| Leads | Lead ID, Name, Company, Source, Score, Status, Date Found, Last Contact Date, Next Follow-Up Date, Notes |
| Outreach | Outreach ID, Lead ID, Channel (Email/DM), Draft Date, CEO Approval (Yes/No), Approval Date, Sent Date, Reply (Yes/No), Reply Date, Notes |
| Deals | Deal ID, Lead ID, Offer Name (ref STRAT-007), Proposal Sent Date, Price Proposed (AED), CEO Price Approval (Yes/No), Status (Open/Won/Lost), Close Date, Revenue (AED) |
| Content | Content ID, Date, Platform, Pillar (ref STRAT-010), Format, Status (Idea/Draft/Ready/Awaiting Approval/Posted), Post Date, Views, Notes |
| Finance | Entry ID, Date, Type (Revenue/Expense), Category, Amount (AED), CEO Approval (Yes/No, required for all Expense entries), Notes |

---

# 5. Charts to Generate Locally

All charts are generated with local, no-cost tools (e.g. spreadsheet built-in charting, or a local Python/matplotlib script) — no paid analytics tool required.

| Chart | Data Source | Purpose |
|-------|-------------|---------|
| Weekly leads funnel (bar) | Leads → Qualified → Outreach Sent → Replies → Meetings → Proposals → Deals Closed | Shows pipeline drop-off by stage |
| Revenue vs. expense (line, weekly) | Finance table | Tracks progress toward STRAT-005 revenue targets and expense caps |
| Content output vs. views (scatter or dual bar) | Content table | Shows whether content volume is translating into reach |
| Follower growth (line, weekly) | Content table follower snapshots | Tracks channel growth trend |
| Deal conversion rate (bar, by offer) | Deals table | Shows which STRAT-007 offer converts best |

---

# 6. CEO Briefing Format

A short weekly summary pulled from the KPI_Summary table:

```text
AOS Revenue Launch — Weekly Briefing (Week of [date])

Pipeline: [leads found] found → [leads qualified] qualified → [outreach sent] sent → [replies] replies → [meetings booked] meetings → [proposals sent] proposals → [deals closed] closed
Revenue: AED [revenue] | Expenses: AED [expenses] | Profit: AED [profit]
Content: [content produced] produced, [content posted] posted, [views] views, [followers] followers
Website: [website visits] visits
Ecommerce: [ecommerce tests] active tests, AED [ad spend] ad spend
Flags: [any missing-data warnings, see Section 7]
```

---

# 7. Missing-Data Warnings

- Any KPI field not updated for more than **3 days** during an active sprint week is flagged with a "Stale data — needs update" warning in the CEO Briefing.
- Any Expense or Ad Spend entry without a recorded "CEO Approval: Yes" is flagged as "Unapproved spend — review immediately."
- Any Deal marked "Won" without a recorded Revenue amount is flagged as "Incomplete deal record."

---

# 8. Atlas Daily Report Format

A short daily template Atlas fills using the current KPI values:

```text
Atlas Daily Revenue Update — [date]

Leads added today: [n]
Outreach drafted, awaiting CEO approval: [n]
Replies to review: [n]
Follow-ups due today: [n]
Content awaiting CEO approval: [n]
Any stale-data or unapproved-spend flags: [list or "None"]
```

---

# 9. Related Documents

- STRAT-005 — AOS Revenue Launch Master Plan
- STRAT-006 — AOS 14-Day Revenue Sprint
- STRAT-008 — AOS Client Lead Pipeline and Outreach System
- STRAT-010 — AOS Multi-Platform Content Factory
- STRAT-011 — AOS Dropshipping and Marketplace Experiment
- PRJ-007 — Launch AOS Revenue Engine
- RLT-012 — Revenue Dashboard Data Template

---

# 10. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-12 | Initial version |
