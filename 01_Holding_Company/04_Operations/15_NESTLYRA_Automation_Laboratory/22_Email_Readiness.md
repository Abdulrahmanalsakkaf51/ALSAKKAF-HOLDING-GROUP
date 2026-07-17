# NESTLYRA — Email Readiness

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Recommendation only. No email setting has been changed, no email has been sent, and nothing here authorizes either.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-022 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Record why NESTLYRA's email is not launch-ready, lay out the two honest options for making it ready, and leave the choice entirely to the Founder.

---

# Scope

Covers: the current email blockers (from NAL-002 section 6) and two options with trade-offs. Does not cover: execution — no DNS record, sender setting, or mailbox is created or changed by this project checkpoint.

---

# 1. Current Blockers (verified, NAL-002)

| # | Blocker | Why It Blocks |
|---|---------|---------------|
| 1 | Sender-domain authentication incomplete (NEEDS SETUP) | Unauthenticated senders are throttled or spam-foldered; order emails would be unreliable |
| 2 | DMARC incomplete | Weak spoofing protection and reduced deliverability for the sending domain |
| 3 | Current Shopify sender is the Founder's company address (see Founder records — not written here per the PRJ-020 privacy rule) | A personal-pattern address as store sender looks unprofessional and couples store mail to a personal mailbox |
| 4 | Temporary support address (hello@alsakkafsystems.com) differs from the sender address | Customers receive from one address and reply to another — confusing and trust-reducing |
| 5 | Permanent NESTLYRA-branded email not established | The brand has no email identity of its own; every interim choice creates a later migration |

Both email blockers also appear in the Launch Blocker Register (NAL-023) — email cannot be considered ready while any of these stands unresolved.

---

# 2. Option A — Temporarily Authenticate alsakkafsystems.com

Use hello@alsakkafsystems.com as both Shopify sender and support address, after completing domain authentication and DMARC for alsakkafsystems.com.

| Aspect | Honest Assessment |
|--------|-------------------|
| Speed | Fast — the domain already exists and the mailbox is already the intended support address |
| Cost | Minimal — DNS records on an existing domain |
| Deliverability | Solid once authentication and DMARC complete |
| Consistency | Sender and support address finally match |
| Brand fit | Weak — customers of a store called NESTLYRA receive email from alsakkafsystems.com; the mismatch is visible in every message |
| Future cost | A second migration later: when a NESTLYRA domain arrives, sender, templates, and customer expectations move again |

---

# 3. Option B — Establish a NESTLYRA-Branded Domain and Email Before Launch

Register a NESTLYRA domain, create a branded mailbox (for example, a hello@ address on that domain), authenticate it, complete DMARC, and launch with the permanent identity from day one.

| Aspect | Honest Assessment |
|--------|-------------------|
| Speed | Slower — domain purchase, mailbox setup, DNS, and propagation before launch readiness |
| Cost | Domain registration plus a mailbox subscription — recurring, though small |
| Deliverability | Equal to Option A once authenticated; a brand-new domain has no sending reputation and warms up from zero |
| Consistency | Complete — one permanent identity, no later migration |
| Brand fit | Strong — the store and its email match from the first message |
| Future cost | None of the migration kind; the work is done once |

---

# 4. Recommendation (for Founder Decision — nothing actioned)

If launch timing dominates, Option A is the honest interim: it clears blockers 1, 2, and 4 quickly, at the price of a visible brand mismatch and a known second migration. If brand permanence dominates and launch can absorb the setup time, Option B avoids ever sending a customer email from the wrong identity. A pragmatic sequence is also available: complete Option A now so nothing customer-facing depends on an unauthenticated personal-pattern sender, and schedule Option B as the pre-launch upgrade — accepting that this sequence pays both setup costs.

The choice is the Founder's. This document makes no change and sends nothing.

---

# Related Documents

- NAL-002 / `02_Current_State_Audit.md` (section 6, Notifications)
- NAL-003 / `03_Unknowns_Register.md` (U-06, domain readiness; U-07, notification templates)
- NAL-023 / `23_Launch_Blocker_Register.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial readiness assessment — five blockers, two options with trade-offs, recommendation only |

---
