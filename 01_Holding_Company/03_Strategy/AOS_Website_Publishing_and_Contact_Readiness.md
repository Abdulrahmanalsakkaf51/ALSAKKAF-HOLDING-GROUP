# ALSAKKAF HOLDING GROUP

# AOS Website Publishing and Contact Readiness

> "A page that isn't live yet can still be exactly right when it goes live."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | STRAT-015 |
| Document Type | Strategy — Publishing Readiness |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Date | 2026-07-13 |
| Related System | AOS |
| Related Project | PRJ-007 |
| Related Documents | STRAT-012, STRAT-014, RLWEB-001, GRCA-001, PRJ-007 |

---

# 1. Purpose

This document tracks exactly what stands between the current local landing page (`docs/index.html`) and a real, published, public website — and what the Founder must decide before that happens.

---

# 2. Current Status

**The website is not published yet.** It exists only as local static files in `docs/` inside this repository. No public URL currently serves this content.

---

# 3. Publishing Options

| Host | Cost | Setup Effort | Custom Domain | Notes |
|------|------|---------------|----------------|-------|
| GitHub Pages | Free | Lowest — this repo's `docs/` folder is already in the exact structure GitHub Pages expects | Supported (needs domain + DNS) | Simplest option given this repository's current layout |
| Cloudflare Pages | Free tier | Low — connects to the Git repository, auto-builds | Supported, plus free CDN/HTTPS | Good if faster global delivery is wanted later |
| Netlify | Free tier | Low — Git-connected or drag-and-drop deploy | Supported | Best long-term option if a real contact form (Phase 4) is added later |

All three serve over HTTPS by default. The final choice is a CEO decision, not a technical blocker — any of the three works for Phase 1–2 of `AOS_Static_Website_and_Free_Hosting_Plan.md` (STRAT-012).

---

# 4. Contact Email Decision Needed

No real contact email has been chosen yet. The landing page's "Request Custom Quote" path currently shows the placeholder: **"Contact email to be added after CEO approval."**

This is a CEO decision, consistent with `AOS_Channel_and_Account_Setup_Runbook.md` (STRAT-009) — the Founder chooses and creates the address manually; it is never created or chosen automatically.

---

# 5. Payment Link Status

The PayPal payment link is **already approved and live** on the local landing page copy: `https://www.paypal.com/ncp/payment/2AN8FH99X682C`, for the AOS AI Workflow Starter Pack — $399 USD. This does not change when the site is published — it is the same public checkout link either way, per `AOS_Payment_Portal_Readiness_Plan.md` (STRAT-014).

---

# 6. Custom Quote Placeholder

Every other offer, and any request outside the standard $399 package, shows **"Request Custom Quote"** with the placeholder contact note above. This does not change until the CEO chooses and adds a real contact email.

---

# 7. Contact Form

There is **no contact form yet**. The current "Request Custom Quote" path is a placeholder pending the contact email decision (Section 4).

**Future form options:** Netlify Forms (if Netlify is chosen as host) or an equivalent free/low-cost form backend — this is a Phase 4 item per STRAT-012, not required for initial publishing.

---

# 8. Privacy Note

A simple, honest privacy statement should appear on the published site: what contact information is collected (only what a visitor voluntarily submits — currently nothing, since there is no live form) and how it would be used (only to respond to the inquiry). Formal privacy/terms pages should be reviewed by a real legal professional before publishing, especially once any form or data collection is added.

---

# 9. Legal / Business Status Note

This document does not provide legal or tax advice. Questions about formal business registration, trade license requirements, tax treatment of online payments, or contract terms should be reviewed with a qualified legal/accounting professional before scaling real revenue — this is a caution to raise with the Founder, not a gap this document can close.

---

# 10. Guardian Review Checklist

Before go-live, Guardian confirms:

- [ ] No credentials, API keys, or secrets anywhere in the site's source
- [ ] No unsafe third-party embeds or scripts
- [ ] The payment link matches exactly the one approved link
- [ ] No tracking scripts or analytics have been added without a separate CEO approval
- [ ] HTTPS is active on whichever host is chosen (default on all three options above)

---

# 11. Publishing Checklist

1. [ ] Landing page copy approved by the CEO
2. [ ] Contact email chosen and the "Request Custom Quote" placeholder updated
3. [ ] Guardian security review complete (Section 10)
4. [ ] Hosting option chosen (Section 3)
5. [ ] Explicit CEO approval to publish (Phase 2, per STRAT-012)

No step in this checklist may be skipped. Publishing does not happen until all five are checked.

---

# 12. Related Documents

- STRAT-012 — AOS Static Website and Free Hosting Plan
- STRAT-014 — AOS Payment Portal Readiness Plan
- RLWEB-001 — docs/README.md (landing page + dashboard folder)
- GRCA-001 — AOS Governance, Risk, Compliance & Assurance Roadmap
- PRJ-007 — Launch AOS Revenue Engine

---

# 13. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version |
