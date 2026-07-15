# ALSAKKAF HOLDING GROUP

# Client Communications — Folder Overview

> "Every reply is drafted before it is sent. Every send is a Founder decision."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | COMMS-001 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Created | 2026-07-16 |
| Last Updated | 2026-07-16 |

---

# Purpose

This folder is the template and workflow system for handling inbound client communication (email, DM, form reply, or any other channel) once ALSAKKAF Systems starts receiving messages from real prospects and clients.

It exists under **PRJ-016 — Partner Activation and Revenue Operations Week**, which already sets the hard rules this folder inherits: no automatic sending, no invented leads or replies, and zero is reported as zero. See `01_Holding_Company/04_Operations/01_Project_Records/PRJ-016_Partner_Activation_and_Revenue_Operations_Week.md`.

---

# Scope

This folder covers:

- How an inbound message gets logged, classified, drafted, checked, approved, sent, and closed out.
- The templates a human or Atlas uses at each stage.
- The categories of content that must always go to the Founder and must never be auto-answered.

This folder does **not** cover:

- Any live email/Gmail connection. No connection exists today. Nothing in this folder sends, receives, or automates a message.
- Pricing or contract decisions — those remain Founder-only regardless of what any draft proposes.
- Outreach (first-contact, cold) templates — those already live in `01_Holding_Company/07_Templates/Revenue_Launch/Outreach/`. This folder is about replying to messages that have already come in, not about starting new ones.

---

# 1. Current Status — Design Only

**This is a template/design system only today.** There is no Gmail connection, no inbox integration, and no automated send path anywhere in this repository. Every file in this folder is a paper form waiting to be filled in by a human or by Atlas under supervision — nothing here executes on its own. Building or wiring an actual email connection is a separate, future, explicitly-approved project.

---

# 2. End-to-End Workflow (Diagram as Text)

```text
1. Inbound message arrives
   (email / DM / contact form reply — received by a human, not by Atlas)
        v
2. Atlas classifies intent
   (pricing question / discovery interest / demo request / complaint /
    scope question / spam / other — see Escalation Matrix, COMMS-007)
        v
3. Atlas extracts facts and questions
   (what was actually asked, what company/lead this belongs to, what
    facts are already known from the trackers)
        v
4. Atlas checks company records
   (Lead_Tracker.csv, Client_Pipeline.csv, Outreach_Tracker.csv —
    has this contact been seen before? what stage are they at?)
        v
5. Atlas drafts a response
   (using Reply Draft Template, COMMS-003, and Approved Wording
    Library, COMMS-008 — never inventing facts, prices, or promises)
        v
6. Guardian checks privacy / security / claims
   (no credentials, no data-security guarantees, no unverified
    deadlines, no invented social proof, no forbidden content —
    see Forbidden Auto-Send Categories, COMMS-009)
        v
7. Founder approves
   (via Founder Approval Queue, COMMS-004 — approve, reject, or edit;
    nothing moves past this step without an explicit Founder decision)
        v
8. Human sends
   (the Founder, or someone the Founder has explicitly authorized,
    sends the approved reply manually — no tool in this system sends
    anything automatically)
        v
9. Reply and outcome logged
   (Communications Inbox Register, COMMS-002, updated with status
    and date closed; Conversation Summary, COMMS-005, written if the
    thread is complete)
        v
10. Follow-up task created
    (if the thread stays open, a follow-up is scheduled using the
     cadence rule in the Follow-up Scheduler, COMMS-006)
```

Every arrow in this diagram is a handoff between a system step and a human decision point. Steps 2–6 can be drafted by Atlas (with Guardian review at step 6). Steps 1, 7, and 8 must always involve a human — Atlas never receives a message, never approves its own draft, and never sends anything.

---

# 3. Files in This Folder

| # | File | Document ID | What It Is |
|---|------|--------------|------------|
| 1 | `README.md` | COMMS-001 | This overview and workflow diagram |
| 2 | `Communications_Inbox_Register_Template.md` + `Communications_Inbox_Register.csv` | COMMS-002 | Log of every inbound message |
| 3 | `Reply_Draft_Template.md` | COMMS-003 | Shape of every Atlas-drafted reply |
| 4 | `Founder_Approval_Queue_Template.md` + `Founder_Approval_Queue.csv` | COMMS-004 | Register of items awaiting Founder sign-off |
| 5 | `Conversation_Summary_Template.md` | COMMS-005 | One-page close-out for a finished thread |
| 6 | `Follow_Up_Scheduler.md` + `Follow_Up_Schedule.csv` | COMMS-006 | Cadence rule and per-thread schedule |
| 7 | `Escalation_Matrix.md` | COMMS-007 | Who decides what, and what a draft may safely say while waiting |
| 8 | `Approved_Wording_Library.md` | COMMS-008 | Reusable, honest phrase blocks |
| 9 | `Forbidden_Auto_Send_Categories.md` | COMMS-009 | Content that always requires a Founder-authored reply |

---

# 4. Hard Rules Inherited From PRJ-016 and Existing AOS Policy

- No automatic sending. Nothing in this folder, or built from it, may send an email, DM, or message without a human physically doing so after Founder approval.
- No invented leads, contacts, companies, replies, or outcomes. Every register row that is not real data is marked "Example Only - Not Real," the same convention used in `Lead_Tracker.csv`.
- No credentials, passwords, 2FA codes, recovery codes, API keys, or bank details in any file in this folder.
- Every reply or outreach-adjacent draft carries a visible "Founder Approval Required" (or "CEO Approval Required") marker.
- The PayPal payment link (`https://www.paypal.com/ncp/payment/2AN8FH99X682C` for the $399 pack; `https://www.paypal.com/ncp/payment/2WXPECSR3UH68` for the $450 pack) may only appear in a reply after the lead has shown confirmed interest — never in a first reply to a cold or ambiguous inbound message.
- No revenue figure, delivery promise, or outcome is ever guaranteed. Use cautious, ranged, or clearly-labeled planning language.

---

# Related Documents

- PRJ-016 / `01_Holding_Company/04_Operations/01_Project_Records/PRJ-016_Partner_Activation_and_Revenue_Operations_Week.md`
- STRAT-007 / `01_Holding_Company/03_Strategy/AOS_Service_Offer_Catalog.md`
- STRAT-008 / `01_Holding_Company/03_Strategy/AOS_Client_Lead_Pipeline_and_Outreach_System.md`
- PODS-001 / `01_Holding_Company/01_Governance/Private_Operational_Data_Standard.md`
- ARPROMPT-001 / `09_AI_Systems/01_Partners/02_Partner_Prompts/PARTNER-002_Atlas_Revenue_Operator_Prompt.md`
- `09_AI_Systems/02_Tools/Atlas_Runtime/atlas_config.json`
- `01_Holding_Company/07_Templates/Revenue_Launch/Outreach/` (first-contact outreach templates)

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-16 | Initial version — folder overview and end-to-end workflow |

---
