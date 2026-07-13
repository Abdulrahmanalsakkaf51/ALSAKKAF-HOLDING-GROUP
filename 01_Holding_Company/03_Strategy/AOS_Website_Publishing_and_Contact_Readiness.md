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
| Version | 1.3 |
| Owner | Abdulrahman Alsakkaf |
| Date | 2026-07-13 |
| Related System | AOS |
| Related Project | PRJ-007 |
| Related Documents | STRAT-012, STRAT-014, STRAT-016, RLWEB-001, GRCA-001, PRJ-007 |

---

# 1. Purpose

This document tracks exactly what stands between the current local landing page (`docs/index.html`) and a real, published, public website — and what the Founder must decide before that happens.

---

# 2. Current Status

**The website is live at https://alsakkafsystems.com.** It was published 2026-07-13 via GitHub Pages (main branch, `/docs` folder) after explicit CEO approval, and connected to the Founder-purchased custom domain alsakkafsystems.com on 2026-07-14 (GitHub Pages DNS check passed). The `docs/CNAME` file holds the custom domain and must not be deleted. The public operating brand on the site is **ALSAKKAF Systems**, with **AOS AI Services** as the service line and ALSAKKAF HOLDING GROUP as the long-term parent vision.

---

# 3. Publishing Options

| Host | Cost | Setup Effort | Custom Domain | Notes |
|------|------|---------------|----------------|-------|
| GitHub Pages | Free | Lowest — this repo's `docs/` folder is already in the exact structure GitHub Pages expects | Supported (needs domain + DNS) | Simplest option given this repository's current layout |
| Cloudflare Pages | Free tier | Low — connects to the Git repository, auto-builds | Supported, plus free CDN/HTTPS | Good if faster global delivery is wanted later |
| Netlify | Free tier | Low — Git-connected or drag-and-drop deploy | Supported | Best long-term option if a real contact form (Phase 4) is added later |

All three serve over HTTPS by default. The final choice is a CEO decision, not a technical blocker — any of the three works for Phase 1–2 of `AOS_Static_Website_and_Free_Hosting_Plan.md` (STRAT-012).

---

# 4. Contact Email — Professional Addresses Active

The contact email decision is complete. Professional domain-based email is active on alsakkafsystems.com (activated by the Founder on 2026-07-14):

| Address | Use |
|---------|-----|
| hello@alsakkafsystems.com | General public contact |
| sales@alsakkafsystems.com | Sales, quote requests, Founding Client Pilot applications |
| services@alsakkafsystems.com | Service enquiries |
| support@alsakkafsystems.com | Support |
| abdulrahman@alsakkafsystems.com | Founder contact |
| atlas@alsakkafsystems.com | Atlas |

The previous temporary launch address (atlasos5555@gmail.com, approved by the Founder on 2026-07-13) is retired from all live public-facing use; it remains in historical records as the documented launch-phase decision. All addresses were created manually by the Founder, consistent with `AOS_Channel_and_Account_Setup_Runbook.md` (STRAT-009). Guardian should confirm each mailbox uses a strong unique password and 2FA.

No credentials, passwords, or recovery details are stored anywhere in this repository.

---

# 4A. Permanent Business Email — Complete

This milestone is complete: the Founder purchased alsakkafsystems.com and activated the professional email system on 2026-07-14 (Phase 3 of `AOS_Static_Website_and_Free_Hosting_Plan.md`, STRAT-012). The live addresses are listed in Section 4 — the plan's placeholder `contact@[future-domain]` was realized as `hello@alsakkafsystems.com`, plus sales@, services@, support@, abdulrahman@, and atlas@. The domain purchase and every email account creation were manual, CEO-only actions — never automated, and never delegated to Atlas or any Partner.

---

# 5. Payment Link Status

The PayPal payment link is **already approved and live** on the local landing page copy: `https://www.paypal.com/ncp/payment/2AN8FH99X682C`, for the AOS AI Workflow Starter Pack — $399 USD. This does not change when the site is published — it is the same public checkout link either way, per `AOS_Payment_Portal_Readiness_Plan.md` (STRAT-014).

---

# 6. Custom Quote Routing

Every other offer, and any request outside the two standard packages, shows **"Request Custom Quote"** routed by mailto link to **sales@alsakkafsystems.com** with a pre-filled subject. General questions route to hello@alsakkafsystems.com and service enquiries to services@alsakkafsystems.com.

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

1. [x] Landing page copy approved by the CEO (Version 2, premium/dark redesign; published 2026-07-13)
2. [x] Contact email in place — permanent professional addresses active on alsakkafsystems.com (2026-07-14; the temporary Gmail launch address is retired from live use)
3. [x] Guardian security review complete for the launch release (Section 10; re-run for every later copy change)
4. [x] Hosting option chosen — GitHub Pages, main branch `/docs`, custom domain alsakkafsystems.com
5. [x] Explicit CEO approval to publish given 2026-07-13 (every later change still requires explicit CEO approval to push)

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
| 1.1 | 2026-07-13 | Temporary contact email (atlasos5555@gmail.com) approved and now live on the landing page; publishing checklist updated; cross-referenced STRAT-016 |
| 1.2 | 2026-07-13 | Corrected phrasing to "Contact: atlasos5555@gmail.com" / "Status: Temporary launch contact email approved by Founder" — explicitly not labeled permanent; added Section 4A documenting the future domain-based email plan (contact@/services@/atlas@[future-domain]), pending domain purchase |
| 1.3 | 2026-07-14 | Domain milestone: Founder purchased alsakkafsystems.com, professional email activated (hello@/sales@/services@/support@/abdulrahman@/atlas@), custom domain connected to GitHub Pages (DNS check passed); temporary Gmail address retired from live use; publishing checklist completed; public brand recorded as ALSAKKAF Systems |
