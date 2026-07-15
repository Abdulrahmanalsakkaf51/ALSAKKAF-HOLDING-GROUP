# Founder Approval Queue Template

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | COMMS-004 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Created | 2026-07-16 |
| Last Updated | 2026-07-16 |

---

# Purpose

Hold every drafted reply, outreach message, or proposal in one visible queue until the Founder makes an explicit approve, reject, or edit decision. Nothing leaves this queue and gets sent by a human without a recorded decision here.

---

# Scope

Covers the approval gate between "drafted" and "sent" for any client-facing content produced under this folder or under `01_Holding_Company/08_Reports/Atlas_Output/`. Does not cover the drafting itself (see COMMS-003) or the logging of the original inbound message (see COMMS-002).

---

# Companion File

The live version of this queue is `Founder_Approval_Queue.csv` in this same folder. Use the CSV for actual tracking; this document defines the columns.

---

# Columns

| Column | Meaning |
|--------|---------|
| Item ID | Unique ID, format `APQ-###` |
| Item Type | Reply / Outreach / Proposal / Follow-Up |
| Date Submitted | `YYYY-MM-DD` |
| Lead / Company | Cross-reference to Lead ID in `Lead_Tracker.csv` if one exists; blank if none |
| Drafted Content Location | File path to the actual draft (e.g., a Reply Draft under this folder, or a file under `Atlas_Output/Outreach_Drafts/` or `Atlas_Output/Proposal_Drafts/`) |
| Risk Flags Raised | Any concern noted during drafting or a Guardian-style review (e.g., "mentions pricing," "borderline complaint," "none") |
| Decision | Approve / Reject / Edit Requested / Pending |
| Decision Notes | Free text — what changed, why rejected, or conditions on approval |
| Date Decided | `YYYY-MM-DD`, blank while Pending |

---

# Template (Markdown View)

| Item ID | Item Type | Date Submitted | Lead / Company | Drafted Content Location | Risk Flags Raised | Decision | Decision Notes | Date Decided |
|---|---|---|---|---|---|---|---|---|
| EXAMPLE-001 | Reply | 2026-07-16 | [Example Only - Not Real] | Sample path - not a real draft location - illustrates column usage only | None | Pending | | |
| EXAMPLE-002 | Outreach | 2026-07-16 | [Example Only - Not Real] | Sample path - not a real draft location - illustrates column usage only | Mentions $399 price - confirm interest first | Pending | | |

---

# How to Use

1. Every completed Reply Draft (COMMS-003), outreach draft, or proposal draft is added here before anyone sends it — no exceptions.
2. "Risk Flags Raised" should note anything a Guardian-style review would look for: PayPal link in a first message, guaranteed-results language, pricing mentioned too early, complaint content, or anything matching the Escalation Matrix (COMMS-007) or Forbidden Auto-Send Categories (COMMS-009).
3. Decision is recorded by the Founder only. "Approve" means the Founder has personally reviewed the drafted content and authorizes a human to send it as-is. "Edit Requested" means it returns to drafting with the Founder's notes. "Reject" means it is not sent.
4. Only after "Decision" = Approve and a human has actually sent the message does the linked row in the Communications Inbox Register (COMMS-002) move to "Sent."
5. Example rows above are placeholders only, using the "Example Only - Not Real" convention from `Lead_Tracker.csv`. Delete or overwrite once real items are logged.
6. This queue is a record of decisions, not a sending mechanism — nothing in this file or its companion CSV sends anything.

---

# Related Documents

- COMMS-001 / `README.md`
- COMMS-002 / `Communications_Inbox_Register_Template.md`
- COMMS-003 / `Reply_Draft_Template.md`
- COMMS-007 / `Escalation_Matrix.md`
- COMMS-009 / `Forbidden_Auto_Send_Categories.md`
- GUARD-001 / `09_AI_Systems/01_Partners/01_Partner_Profiles/PARTNER-016_Guardian.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-16 | Initial version |

---
