# Reply Draft Template

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | COMMS-003 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Created | 2026-07-16 |
| Last Updated | 2026-07-16 |

---

# Purpose

Define the fixed shape every Atlas-drafted reply must follow before it can enter the Founder Approval Queue (COMMS-004). No reply skips a field in this template.

---

# Scope

Covers the drafting of a reply to an inbound message already logged in the Communications Inbox Register (COMMS-002). Does not cover first-contact cold outreach — see `01_Holding_Company/07_Templates/Revenue_Launch/Outreach/`.

---

# Template

```text
REPLY DRAFT
===========

>>> FOUNDER APPROVAL REQUIRED — THIS DRAFT HAS NOT BEEN SENT <<<

Message ID (from Communications Inbox Register): [MSG-###]
Recipient: [First Name / Company, as known — leave blank rather than guess]
Channel: [Email / LinkedIn DM / Instagram DM / WhatsApp / Contact Form]

Original Message (quoted or summarized):
[Paste the original message verbatim, or summarize it in one or two
plain sentences if it is long. Do not add anything the sender did not
actually say.]

Drafted Reply Body:
[The proposed reply text, in plain, honest, non-pushy language. Uses
only facts and figures already confirmed — see Approved Wording
Library, COMMS-008.]

Tone Check:
[ ] Plain, respectful, no fake urgency
[ ] No guaranteed-results language
[ ] No invented social proof (client names, numbers, testimonials)
[ ] Matches the live website wording for pricing/offers if pricing is mentioned

Sender Identity (must be a named human, never "Atlas" or "AI System"):
[abdulrahman@alsakkafsystems.com (Founder), or the relevant role inbox
per atlas_config.json's contact_email_note: hello@ (general),
sales@ (quotes/pilot applications), services@ (service enquiries),
support@ (support) — a human still authors and sends from this address]

Payment Link / Price / Promise Confirmation:
[ ] No payment link, price, or delivery promise added in this draft, OR
[ ] Payment link/price included — confirmed appropriate because the
    thread already shows confirmed interest at [stage/date], per the
    rule that the PayPal link never appears in a first cold reply

>>> FOUNDER APPROVAL REQUIRED — THIS DRAFT HAS NOT BEEN SENT <<<
```

---

# Field Notes

| Field | Rule |
|-------|------|
| Recipient | Use only names/details already known from the inbound message or an existing tracker row. Never invent a title, company size, or role. |
| Original Message | Quote or summarize accurately. Do not paraphrase in a way that changes meaning. |
| Drafted Reply Body | Draw language only from the Approved Wording Library (COMMS-008). Escalation categories (COMMS-007) must not be answered here — acknowledge and route to the Founder instead. |
| Sender Identity | Must always be a named human inbox, per `atlas_config.json`'s `contact_email_note`. A reply must never appear to come from "Atlas" or any AI system name. |
| Payment Link / Price / Promise Confirmation | This checkbox exists specifically to stop the PayPal link (`https://www.paypal.com/ncp/payment/2AN8FH99X682C` / `https://www.paypal.com/ncp/payment/2WXPECSR3UH68`) or a locked-in price from appearing in a first cold reply. It must be filled in every time, with no exceptions. |

---

# How to Use

1. Every reply, without exception, is drafted using this template and carries the visible "FOUNDER APPROVAL REQUIRED" marker at both the top and bottom.
2. A completed draft moves to the Founder Approval Queue (COMMS-004) — it is never sent directly from this document.
3. If the message intent matches any Escalation Matrix (COMMS-007) or Forbidden Auto-Send Categories (COMMS-009) item, the Drafted Reply Body must only acknowledge and route to the Founder — it must not attempt to answer the substantive question.
4. No credentials, passwords, 2FA codes, recovery codes, API keys, or bank details may appear anywhere in a drafted reply.
5. No revenue figure, delivery date, or outcome is ever stated as guaranteed — use cautious, ranged, or clearly-labeled planning language only.

---

# Related Documents

- COMMS-001 / `README.md`
- COMMS-002 / `Communications_Inbox_Register_Template.md`
- COMMS-004 / `Founder_Approval_Queue_Template.md`
- COMMS-007 / `Escalation_Matrix.md`
- COMMS-008 / `Approved_Wording_Library.md`
- COMMS-009 / `Forbidden_Auto_Send_Categories.md`
- `09_AI_Systems/02_Tools/Atlas_Runtime/atlas_config.json`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-16 | Initial version |

---
