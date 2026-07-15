# Communications Inbox Register Template

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | COMMS-002 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Created | 2026-07-16 |
| Last Updated | 2026-07-16 |

---

# Purpose

Log every inbound client or prospect message in one place, so nothing gets missed, every message can be traced back to a lead (if one exists), and every open thread has a visible next step.

---

# Scope

Covers logging of inbound messages only (email, DM, contact-form reply, or any other channel a human receives). It does not cover drafting the reply itself (see `Reply_Draft_Template.md`, COMMS-003) or the Founder approval step (see `Founder_Approval_Queue_Template.md`, COMMS-004).

---

# Companion File

The live version of this register is `Communications_Inbox_Register.csv` in this same folder. Use the CSV for actual logging; this document defines the columns and shows the required format.

---

# Columns

| Column | Meaning |
|--------|---------|
| Message ID | Unique ID, format `MSG-###` |
| Date Received | `YYYY-MM-DD` |
| Channel | Email / LinkedIn DM / Instagram DM / WhatsApp / Contact Form / Other |
| Sender Name | Name as given by the sender |
| Company (if known) | Leave blank if unknown — never invent a company name |
| Subject / Summary | One line: what the message is about |
| Classified Intent | See Escalation Matrix (COMMS-007) categories, plus: Pricing Question, Discovery Interest, Demo Request, General Question, Complaint, Spam/Irrelevant, Other |
| Linked Lead ID | Cross-reference to `Lead_Tracker.csv` Lead ID if this sender already exists there; blank if new |
| Status | New / Classified / Drafted / In Founder Queue / Approved / Sent / Closed / No Reply Needed |
| Assigned Next Step | Plain-language description of what happens next |
| Date Closed | `YYYY-MM-DD`, blank while still open |

---

# Template (Markdown View)

| Message ID | Date Received | Channel | Sender Name | Company (if known) | Subject / Summary | Classified Intent | Linked Lead ID | Status | Assigned Next Step | Date Closed |
|---|---|---|---|---|---|---|---|---|---|---|
| EXAMPLE-001 | 2026-07-16 | Email | [Example Only - Not Real] | [Example Only - Not Real] | Sample row - not a real message - illustrates column usage only | Pricing Question | EXAMPLE-001 | Drafted | Atlas drafts reply, Founder must approve before send | |
| EXAMPLE-002 | 2026-07-16 | Contact Form | [Example Only - Not Real] | [Example Only - Not Real] | Sample row - not a real message - illustrates column usage only | Complaint | | In Founder Queue | Founder-authored reply required - see Escalation Matrix (COMMS-007) | |

---

# How to Use

1. Log every inbound message the same day it is received, even if the classified intent is Spam/Irrelevant.
2. Only Atlas or the Founder adds rows — never invent a message, sender, or company. If a message is real but details are uncertain, mark the uncertain field "Unconfirmed" rather than guessing.
3. "Linked Lead ID" must match an existing row in `Lead_Tracker.csv`; if there is no match, leave it blank rather than creating a placeholder.
4. Status only moves to "Sent" after a human has actually sent the approved reply — see `Founder_Approval_Queue_Template.md` (COMMS-004).
5. Example rows above are placeholders only, using the same "Example Only - Not Real" marking convention as `Lead_Tracker.csv`, so Atlas-style tooling can recognize and skip them. Delete or overwrite example rows once real messages are logged.
6. Never store credentials, passwords, 2FA codes, recovery codes, API keys, or bank details in this register.

---

# Related Documents

- COMMS-001 / `README.md`
- COMMS-003 / `Reply_Draft_Template.md`
- COMMS-004 / `Founder_Approval_Queue_Template.md`
- RLT-001 / `01_Holding_Company/07_Templates/Revenue_Launch/Lead_Tracker_Template.md`
- `01_Holding_Company/04_Operations/03_Revenue_Operations/Lead_Tracker.csv`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-16 | Initial version |

---
