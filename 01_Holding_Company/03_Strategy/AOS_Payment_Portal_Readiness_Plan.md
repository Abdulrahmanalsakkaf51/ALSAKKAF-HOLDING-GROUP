# ALSAKKAF HOLDING GROUP

# AOS Payment Portal Readiness Plan

> "A payment link is not a credential. Store the link. Never store the login."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | STRAT-014 |
| Document Type | Strategy — Payment Readiness |
| Status | Active |
| Version | 1.1 |
| Date | 2026-07-13 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-007, PRJ-009 |
| Related Documents | STRAT-005, STRAT-007, STRAT-008, STRAT-009, STRAT-012, GRCA-001, PRJ-007 |

---

# 1. Purpose

This document defines how ALSAKKAF HOLDING GROUP collects payment for AOS AI Services offers during the Revenue Launch (PRJ-007): which payment link is approved and active, what must never be stored, how other offers are presented until they have an approved link, and the Guardian security note governing this arrangement.

---

# 2. Current Approved Payment Methods

| Field | Offer 1 | Offer 2 |
|-------|---------|---------|
| Offer | AOS AI Workflow Starter Pack | AOS AI Agent Starter Pack |
| Price | $399 USD | $450 USD |
| Payment method | PayPal public payment link | PayPal public payment link |
| Link | https://www.paypal.com/ncp/payment/2AN8FH99X682C | https://www.paypal.com/ncp/payment/2WXPECSR3UH68 |
| Approved by | Abdulrahman Alsakkaf (Founder/CEO) | Abdulrahman Alsakkaf (Founder/CEO) |
| Status | Active | Active |
| Date approved | 2026-07-13 | 2026-07-13 |

These are the **only two active payment links** across AOS. No other offer has an approved payment link at this time. Both were created by the Founder in PayPal and provided as public checkout URLs, per the Section 8 approval gate.

---

# 3. What These Links Are — and Are Not

These are **public PayPal payment/checkout links** — the same kind of link a business shares to let a customer pay for a specific item. They are safe to store in AOS Markdown documents and on the public website, because they do not grant access to any account.

It is explicitly **not** a credential. The following must never be stored in this repository, in any AOS Markdown file, or anywhere Atlas or any Partner can read:

- PayPal login email/username or password
- Two-factor authentication (2FA) codes or backup codes
- Recovery codes
- API keys or secret keys (PayPal or any other service)
- Bank account or card details

If any task, request, or workflow would require entering or storing any of the above, it must stop and escalate to the Founder instead of proceeding, consistent with Guardian's credential-handling rule (`PARTNER-016_Guardian.md`, GUARD-001) and CLAUDE.md Section 4.

---

# 4. Other Offers — Payment Status

Every other offer in `AOS_Service_Offer_Catalog.md` (STRAT-007) — Custom AOS Build, Small Business Dashboard Starter Pack, Social Content Factory Setup, Website / Landing Page Starter, AI Executive Assistant Setup, Client Operations Cleanup, Training Material Builder, and Marketing Campaign Starter — has **no active payment link**.

These offers must display **"Request Custom Quote"** instead of a payment button, on the website and in any client-facing material, until the CEO approves a separate payment link for each.

---

# 5. Currency Rule

The landing page and all client-facing payment references use **USD**, matching the approved PayPal link.

The landing page must state plainly: **"Payments are processed in USD."**

Internal planning ranges elsewhere in AOS (e.g. the AED ranges in STRAT-007) remain the Founder's internal cost/quote reference and are not contradicted by this rule — they are simply not the currency shown at the point of payment for this offer.

---

# 6. Consultation-First Language Rule

Where a client's need is not clearly a standard, unscoped AI Workflow Starter Pack, client-facing copy should invite a short consultation before pointing the client to the payment link — for example: *"Not sure this is the right fit? Book a free 15-minute call first."*

The payment link should be presented as the direct path for a client who already understands and wants the standard $399 package, not as the only path in. This keeps scope-creep risk (already flagged in STRAT-007's risk notes for this offer) from turning into a mismatched paid engagement.

---

# 7. Guardian Security Note

Guardian's review of this arrangement: the approved link is a public PayPal checkout URL and carries no credential risk on its own. The residual risk is procedural, not technical — the Founder must ensure the PayPal account itself uses a strong unique password, 2FA, and a CEO-controlled recovery email, consistent with the account security rules in `AOS_Channel_and_Account_Setup_Runbook.md` (STRAT-009). AOS itself stores and touches only the public link, never the account's login, 2FA, recovery codes, or keys.

---

# 8. CEO Approval Gate for Future Payment Links

Before any additional offer receives an active payment link:

1. The CEO approves the specific offer, price, and currency.
2. The CEO provides the public payment link directly (Atlas/Claude never generates, requests, or configures a payment link itself).
3. This document is updated to add the new link under Section 2, and the offer's "Request Custom Quote" status in STRAT-007 and the website copy is changed to reflect the new active link.

No Partner or Claude session may propose, create, or activate a payment link on its own authority.

---

# 9. Where This Link Appears

| Document | Reference |
|----------|-----------|
| `AOS_Service_Offer_Catalog.md` (STRAT-007) | AI Workflow Starter Pack offer entry — Payment Status field |
| `AOS_Static_Website_and_Free_Hosting_Plan.md` (STRAT-012) | Service Offers / Pricing website sections |
| `Website_Copy_Template.md` (RLT-010) | Service Offers and Pricing Ranges template sections |
| `AOS_Revenue_Launch_CEO_Briefing.md` (RLBRIEF-001) | Payment Readiness section |

---

# 10. Related Documents

- STRAT-005 — AOS Revenue Launch Master Plan
- STRAT-007 — AOS Service Offer Catalog
- STRAT-008 — AOS Client Lead Pipeline and Outreach System
- STRAT-009 — AOS Channel and Account Setup Runbook
- STRAT-012 — AOS Static Website and Free Hosting Plan
- GRCA-001 — AOS Governance, Risk, Compliance & Assurance Roadmap
- PRJ-007 — Launch AOS Revenue Engine

---

# 11. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version — approved PayPal public payment link recorded for AOS AI Workflow Starter Pack ($399 USD) |
| 1.1 | 2026-07-13 | Second approved PayPal public payment link recorded for AOS AI Agent Starter Pack ($450 USD), provided by the Founder per the Section 8 gate (PRJ-009) |
