# Conversation Summary Template

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | COMMS-005 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Created | 2026-07-16 |
| Last Updated | 2026-07-16 |

---

# Purpose

Close out a completed communication thread in one page: what was asked, what was answered, the outcome, and what should be learned or followed up on.

---

# Scope

Covers a single closed (or paused) thread with one lead/company. Does not cover ongoing threads still in the Communications Inbox Register (COMMS-002) as "open."

---

# Template

```text
CONVERSATION SUMMARY
=====================

Message ID(s) covered: [MSG-###, MSG-###, ...]
Lead / Company: [Name, or "Unknown" if never identified]
Linked Lead ID: [Lead Tracker ID, or blank]
Channel(s): [Email / LinkedIn DM / Instagram DM / WhatsApp / Contact Form]
Date Opened: [YYYY-MM-DD]
Date Closed: [YYYY-MM-DD]

What Was Asked:
[One or two plain sentences — the actual question(s) or request(s)
the sender raised, in their own terms, not embellished.]

What Was Answered:
[One or two plain sentences — what was actually sent back, and when.
Reference the specific approved reply/replies if useful.]

Outcome: [Won / Lost / No Decision / Still Open]

Outcome Detail:
[If Won: what was purchased/agreed, and confirm payment status is
tracked separately in Client_Pipeline.csv — do not restate a revenue
figure here as guaranteed if it has not been confirmed received.
If Lost: the stated or inferred reason, if known — never guess a
reason the sender did not give.
If No Decision: what is unresolved.
If Still Open: this summary should not have been written yet — move
back to the Communications Inbox Register instead.]

Lessons:
[What, if anything, should change in the wording library, the
escalation matrix, or the process, based on this thread. "None" is
a valid answer.]

Follow-Up Needed: [Yes / No]
If Yes: [What follow-up, and by when — use the Follow-up Scheduler,
COMMS-006, cadence rule rather than guessing a date.]
```

---

# How to Use

1. Write one Conversation Summary per closed thread — not per message.
2. Only complete this once the thread has actually reached Won, Lost, No Decision (closed for now), or a deliberate pause. A thread that is still actively going back and forth stays in the Communications Inbox Register (COMMS-002) instead.
3. "Outcome Detail" for a Won thread must not restate revenue as guaranteed or already banked — cross-check actual payment status in `01_Holding_Company/04_Operations/03_Revenue_Operations/Client_Pipeline.csv` and the Revenue Reports under `01_Holding_Company/08_Reports/Atlas_Output/Revenue_Reports/`.
4. Once written, update the corresponding row's "Status" and "Date Closed" in the Communications Inbox Register (COMMS-002).
5. Never invent an outcome, a reason for loss, or a lesson that was not actually observed in the thread.

---

# Related Documents

- COMMS-001 / `README.md`
- COMMS-002 / `Communications_Inbox_Register_Template.md`
- COMMS-006 / `Follow_Up_Scheduler.md`
- `01_Holding_Company/04_Operations/03_Revenue_Operations/Client_Pipeline.csv`
- `01_Holding_Company/08_Reports/Atlas_Output/Revenue_Reports/`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-16 | Initial version |

---
