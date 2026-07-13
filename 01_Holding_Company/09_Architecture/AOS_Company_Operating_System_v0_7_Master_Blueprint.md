# ALSAKKAF HOLDING GROUP

# AOS Company Operating System v0.7 — Master Blueprint

> "One Founder, one assistant, one dashboard, one payment link, one clear next action — every day."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | AOS7-001 |
| Document Type | Master Architecture / Target Operating Blueprint |
| Status | Active — Target Architecture (not yet fully built) |
| Version | 1.1 |
| Date | 2026-07-13 |
| Owner | Founder / CEO |
| Related System | AOS |
| Related Project | PRJ-008, PRJ-009 |
| Related Documents | PRJ-007, ARUN-001, STRAT-005, GRCA-001, OPS-001, ARPROMPT-001 |

---

# 1. Purpose

This is the master integration map for AOS Company Operating System v0.7. It defines what the company operating system should be, which engines it needs, how they connect, what exists today, what does not, and how the Founder executes over the next 7, 30, and 90 days.

This document is a target map, not a completion report. Version 1.0 overstated what was built; version 1.1 corrects every claim against the actual file system.

---

# 2. Founder Vision

ALSAKKAF HOLDING GROUP is built as an AI-native holding company: a small number of humans (initially one Founder) operating multiple business cells through documented systems, AI Partners, and disciplined approval gates. Revenue funds growth; growth funds new cells; every cell inherits AOS governance from day one.

---

# 3. What v0.7 Means

v0.7 is the 70% operational foundation target:

- Every core engine (revenue, website, leads, outreach, delivery, content, dashboard, payment, clients, cells) is documented and usable by the Founder.
- Atlas Runtime turns the documents into runnable commands with generated reports.
- Nothing sends, publishes, spends, or connects to external services autonomously.

v0.7 is not full autonomous company management. The missing 30% is real-world proof: real leads, real clients, real payments, real published channels, and the lessons they produce.

---

# 4. What Actually Exists Today

| Area | Real Asset (verified on disk) |
|------|-------------------------------|
| Offer | AOS AI Workflow Starter Pack — $399 USD, 3 automations for the price of one |
| Payment | Active PayPal payment link for the $399 offer (public checkout URL, USD) |
| Website | Landing page v2 built in docs/, publishable via GitHub Pages when approved |
| Dashboard | Local Atlas dashboard (docs/atlas-dashboard.html) driven by tracker data |
| Runtime | Atlas Runtime v1 with 10 working commands: health-check, brief, score-leads, dashboard, proposal, outreach, content-pack, delivery-checklist, payment-report, war-room |
| Leads | Lead research playbooks and trackers (RLOP series, Lead_Tracker.csv) from PRJ-007 |
| Delivery | Client delivery workflow and template pack (RLCD series) in 05_Client_Delivery |
| Outreach | Approved outreach template pack (RLOUT series) in 07_Templates/Revenue_Launch |
| Content | Content operations documents and trackers in 04_Content_Operations |
| Governance | AOS governance: registers, ADRs, approval gates, credential protection policy |

---

# 5. What Is Not Built Yet

| Gap | Why |
|-----|-----|
| Lead Intelligence System v1 (06_Market_Intelligence) | Planned under v0.7; build only when revenue work requires it |
| Sales Operations System v1 (07_Sales_Operations) | Planned; not built |
| Website Operations System v1 (08_Website_Operations) | Planned; not built |
| Finance Operations System v1 (09_Finance_Operations) | Planned; not built |
| Company Cells System v1 (Company_Cells) | Planned; not built |
| Fast Execution Governance policy set | Planned; not built |
| Atlas Runtime v0.7 commands (next-actions, publish-check, launch-day, etc.) | Planned; not implemented |
| Real leads | Lead_Tracker.csv holds no real leads; research is a manual Founder task |
| Published website | Built but unpublished; publish requires explicit CEO approval |
| Live channels | No real social/content accounts created yet (manual CEO action) |
| Revenue history | $0 collected; all revenue figures are planning ranges, never guarantees |
| Permanent contact email | atlasos5555@gmail.com is a temporary launch address; domain-based email pending |
| Additional Partners | Only Librarian, Atlas, and Guardian are active |
| Legal entities | Company cells are concepts, not registered companies |

---

# 6. Target System Architecture

```text
FOUNDER / CEO (all approvals)
    -> Atlas Super Assistant (Claude session + Atlas Runtime)
        -> Lead Engine
        -> Outreach Engine
        -> Delivery Engine
        -> Content Engine
        -> Finance Engine
        -> Cells Engine
            (all six write to)
        -> CSV Trackers + Markdown (single source of truth)
            -> Dashboard Engine (docs/, local)
                -> Website Engine (docs/, GitHub Pages later)
```

Local-first: all data lives as Markdown and CSV inside this Git repository. Atlas Runtime (Python standard library only) reads trackers and writes reports. Nothing calls the network.

---

# 7. Atlas Role

Atlas (PARTNER-002) is the company operator layer:

- Runs the daily war room, briefing, and dashboard refresh.
- Generates proposals, outreach drafts, content packs, and delivery checklists with today's real commands.
- Surfaces blockers and CEO decisions; never makes them.
- Operates under ARPROMPT-001 (Revenue Operator) task mode; a Company Operator prompt is planned but not yet written.

---

# 8. Partner Roles

| Partner | Role in v0.7 |
|---------|--------------|
| PARTNER-002 Atlas | Primary operator: planning, drafting, reporting, routing, dashboards |
| PARTNER-001 The Librarian | Indexing and retrieval of approved knowledge; Knowledge Register discipline |
| PARTNER-016 Guardian | Credential protection, risk review, publish/security escalations |
| Proposed Partners | Marketing, Client Acquisition, Content, Reporting, Finance — proposed only, not active |

---

# 9. The Engines (current tools in parentheses)

## 9.1 Revenue Engine

Active offers plus one payment link plus the pipeline trackers (Lead_Tracker.csv, Outreach_Tracker.csv, Client_Pipeline.csv). (`atlas.py payment-report`, `atlas.py score-leads`)

## 9.2 Website Engine

docs/ holds the landing page and dashboard. Publishing follows the STRAT-015 checklist and requires CEO approval. (manual checklist today; a publish-check command is planned)

## 9.3 Lead Engine

STRAT-016 pain-point-first targeting plus the RLOP research playbooks drive the first 25 leads into Lead_Tracker.csv. Atlas never invents leads. (`atlas.py score-leads`)

## 9.4 Outreach Engine

Approved RLOUT templates plus `atlas.py outreach` produce drafts. Every message is personalized, CEO-approved, and sent manually. The payment link never appears in first cold contact.

## 9.5 Delivery Engine

RLCD delivery workflow: onboarding, the 3-Automations method, acceptance checklist, and refund/revision rules. (`atlas.py delivery-checklist`)

## 9.6 Content Engine

Content operations documents, calendar, and analytics trackers. Nothing publishes automatically. (`atlas.py content-pack`)

## 9.7 Dashboard Engine

`atlas.py dashboard` recomputes docs/atlas-dashboard-data.js from real tracker counts. The dashboard is local-only until the website is approved for publishing.

## 9.8 Payment Engine

Manual by design: the PayPal link is sent (after approval), payment status is manually updated in Client_Pipeline.csv. No PayPal API, no stored credentials, ever.

## 9.9 Client Management Engine

Client folder structure, communication rules, scope control, acceptance, feedback, testimonial, and archive processes in 05_Client_Delivery.

## 9.10 Future Company / Cell Engine

Planned: register candidate businesses as concepts, score them, and gate launches behind CEO approval. Not built yet.

---

# 10. Governance and Risk Gates

- CEO Approval Gates: nothing is sent, published, spent, signed, or activated without explicit Founder approval.
- Guardian escalation for anything touching credentials, security setup, or data sensitivity.
- Atlas may draft, compute, and report alone; sending, publishing, and spending always need the Founder.

---

# 11. Core Principles

| Principle | Meaning |
|-----------|---------|
| Local-first | All company data is Markdown/CSV in this repo; tools are offline, standard library only |
| No credentials | No password, API key, 2FA code, recovery code, or bank detail is ever stored |
| CEO approval gates | Human-in-the-loop for every external-facing or irreversible action |
| Honest numbers | Real tracker counts only; targets are labeled as planning estimates |
| Honest records | No record may claim a component exists until it is verified on disk |
| Documentation first | Every official asset is registered in the Knowledge Register |

---

# 12. Execution Focus

Execution now runs through PRJ-009 — First Revenue Acquisition Sprint (see the sprint plan in 04_Operations/10_Revenue_Sprints). The 7-day, 30-day, and 90-day sequences below remain the strategic frame.

## 12.1 First 7 Days (via PRJ-009 sprint)

| Day | Focus |
|-----|-------|
| 1 | Publish readiness: review site, approve copy, prepare channels |
| 2 | Research first 25 real leads (manual, never invented) |
| 3 | Personalize and send first 5 outreach messages (manual, after approval) |
| 4 | Follow up; prepare first proposal |
| 5 | Content and trust assets |
| 6 | Consultation and close attempt |
| 7 | Review, lessons, plan week 2 |

## 12.2 First 30 Days

| Week | Focus |
|------|-------|
| 1 | Website published, first 25 leads, first outreach batch |
| 2 | 25 more leads, follow-ups, first discovery calls, first proposal sent |
| 3 | Close attempt on first client; if paid, run delivery workflow |
| 4 | Deliver, collect acceptance and testimonial, log lessons, refine offer |

## 12.3 First 90 Days

| Month | Focus |
|-------|-------|
| 1 | First paying client(s); website and channels live |
| 2 | Repeatable delivery (3+ clients), testimonial-driven content, pricing review |
| 3 | Evaluate second company cell; consider domain purchase, permanent email, next Partner activation |

Planning reference (STRAT-005): all revenue target ranges are planning-only and never a guarantee.

---

# 13. Release Criteria for a True v0.7

1. Every component in Section 5 verifiably exists on disk.
2. A v0.7 release test passes.
3. Atlas Runtime test suite passes.
4. Markdown Audit: Issues found: 0.
5. No credential-like values anywhere in scanned folders.
6. All new official documents indexed in the Knowledge Register.

---

# 14. Known Limitations

- All numbers stay at zero until the Founder does the manual work (research, send, deliver, collect).
- Payment tracking is manual; there is no reconciliation against PayPal.
- The dashboard is a static local page, not a live web app.
- Content ideas are drafts requiring Founder voice, review, and recording.
- One Founder is the throughput limit; the system reduces friction but does not remove the work.

---

# 15. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version — overstated built components |
| 1.1 | 2026-07-13 | Integrity correction: reframed as target architecture; every "exists" claim verified against the file system; execution routed through PRJ-009 |
