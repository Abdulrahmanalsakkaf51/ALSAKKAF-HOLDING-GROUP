# Follow-Up Scheduler

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | COMMS-006 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Created | 2026-07-16 |
| Last Updated | 2026-07-16 |

---

# Purpose

Give Atlas or the Founder a fixed, rule-based way to know exactly when a follow-up is due on any open thread — calculated from the cadence rule, never guessed.

---

# Scope

Applies to both first-contact outreach threads (per STRAT-008) and inbound-reply threads that have gone quiet after a reply was sent from this folder's workflow (COMMS-003/COMMS-004). Does not itself draft follow-up content — see the Follow-Up 1 and Follow-Up 2 templates in `01_Holding_Company/07_Templates/Revenue_Launch/Outreach/`.

---

# 1. The Cadence Rule (Reused From STRAT-008 / Follow-Up 1 & 2 Templates)

This is the single existing cadence rule for the whole revenue operation — this scheduler does not invent a new one, it reuses `AOS_Client_Lead_Pipeline_and_Outreach_System.md` (STRAT-008) Section 18:

| Day (from last message sent) | Action |
|---|---|
| Day 0 | Message sent (after Founder approval) |
| Day 3 (working days) | First follow-up if no reply, using `Follow_Up_1_Template.md` (after Founder approval of the follow-up content) |
| Day 7 (working days, i.e. ~4 working days after the first follow-up) | Second follow-up if still no reply, using `Follow_Up_2_Template.md` (after Founder approval) |
| Day 14 | Close the thread as "No Response." No further contact without a new, specific reason and fresh Founder approval. |

Rules that apply at every step:

- One follow-up message per scheduled step — never send a follow-up twice for the same due date.
- Every follow-up always includes an easy out (e.g., "no worries at all," "I'll leave it here") — never pressure, never fake urgency.
- A reply at any point pauses this schedule immediately. The thread moves into an active conversation handled through the Reply Draft Template (COMMS-003) and Founder Approval Queue (COMMS-004) instead.
- The PayPal payment link may only appear starting at the second follow-up (Follow-Up 2), and only as a closing-the-loop reference — never as the first thing offered, per `Follow_Up_2_Template.md`.

---

# 2. Schedule Table Format (Fill In Per Thread)

| Message ID / Lead ID | Date Sent (Day 0) | Follow-Up 1 Due (Day 3) | Follow-Up 1 Sent | Follow-Up 2 Due (Day 7) | Follow-Up 2 Sent | Close-Out Due (Day 14) | Status |
|---|---|---|---|---|---|---|---|
| EXAMPLE-001 | 2026-07-16 | 2026-07-21 | | 2026-07-27 | | 2026-08-03 | Example Only - Not Real - illustrates column usage only |

Due dates are calculated by adding working days to "Date Sent," not by guessing — weekends do not count toward the 3/7/14-day cadence.

---

# 3. Companion File

The live version of this table is `Follow_Up_Schedule.csv` in this same folder. Use the CSV for actual scheduling.

---

# How to Use

1. Every time an outreach message or a reply is sent with no immediate response expected, add one row here with "Date Sent" filled in and the due dates calculated per the cadence rule above.
2. Check this scheduler (or run the equivalent Atlas Runtime command, if available) daily to see which threads have a follow-up due today.
3. Follow-up content itself always comes from the approved templates (`Follow_Up_1_Template.md`, `Follow_Up_2_Template.md`) and always requires Founder approval before sending — this scheduler only tracks timing, it does not authorize a send.
4. After Day 14 with no reply, mark Status "No Response — Closed" and stop. Do not re-contact without a new, specific reason and fresh Founder approval.
5. The example row above is a placeholder only, marked "Example Only - Not Real." Delete or overwrite once real threads are scheduled.

---

# Related Documents

- COMMS-001 / `README.md`
- COMMS-003 / `Reply_Draft_Template.md`
- COMMS-004 / `Founder_Approval_Queue_Template.md`
- STRAT-008 / `01_Holding_Company/03_Strategy/AOS_Client_Lead_Pipeline_and_Outreach_System.md`
- RLOUT-005 / `01_Holding_Company/07_Templates/Revenue_Launch/Outreach/Follow_Up_1_Template.md`
- RLOUT-006 / `01_Holding_Company/07_Templates/Revenue_Launch/Outreach/Follow_Up_2_Template.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-16 | Initial version |

---
