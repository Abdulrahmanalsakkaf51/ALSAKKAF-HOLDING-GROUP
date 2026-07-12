# ALSAKKAF HOLDING GROUP

# AOS Static Website and Free Hosting Plan

> "A landing page does not need a server. It needs clarity, proof, and a way to get in touch."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | STRAT-012 |
| Document Type | Strategy Document |
| Status | Active |
| Version | 1.1 |
| Date | 2026-07-13 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-007 |
| Related Documents | STRAT-005, STRAT-006, STRAT-009, STRAT-013, STRAT-014, PRJ-007 |

---

# 1. Purpose

This document defines the plan for a simple, low-cost/free static website and landing page to support AOS AI Services client acquisition. No website is published under this document — it defines the plan only. Publishing (Phase 2 below) is a public action and requires explicit CEO approval per PRJ-007's CEO Approval Gates.

---

# 2. Recommended Free/Low-Cost Hosting

| Host | Cost | Ease | Custom Domain | Notes |
|------|------|------|----------------|-------|
| GitHub Pages | Free | Simple; serves static files directly from a repository | Supported (needs domain purchase + DNS setup) | Best fit for a single static landing page tied to this repository's workflow |
| Cloudflare Pages | Free tier | Simple; connects to a Git repository, auto-builds | Supported, plus free CDN/HTTPS | Good option if faster global delivery or built-in analytics is wanted later |
| Netlify | Free tier | Simple; drag-and-drop or Git-connected deploys | Supported | Good option for form-handling add-ons later (Phase 4) |

Any of the three is acceptable for Phase 1–2. The choice is a CEO decision at publish time, not a technical blocker now.

---

# 3. Why Amazon/Noon/eBay Are Not Website Hosting Channels

Amazon, Noon, and eBay (covered in `AOS_Dropshipping_and_Marketplace_Experiment.md`, STRAT-011) are **product marketplaces** — they host individual product listings inside their own marketplace pages, not an independent company website or landing page. They cannot replace a general-purpose website: they do not support custom service pages, company branding pages, or a client-facing service catalog. The website plan in this document and the marketplace plan in STRAT-011 are separate systems that may later cross-link, but neither substitutes for the other.

---

# 4. Website Sections

| Section | Purpose |
|---------|---------|
| Hero | One clear headline stating what AOS AI Services does and for whom |
| Problem | Names the specific small-business problem the offers solve |
| Service offers | Summarized versions of the offers in `AOS_Service_Offer_Catalog.md` (STRAT-007) |
| Proof/demo | Placeholder for case studies, screenshots, or a short demo once available; honest "new but capable" framing until real proof exists |
| Process | Simple 3–4 step delivery process (e.g. Discovery → Proposal → Delivery → Support) |
| Pricing ranges | Entry/Standard/Premium ranges from STRAT-007, not final fixed prices; the AI Workflow Starter Pack additionally shows its active $399 USD payment link (Section 4A) |
| Contact form alternative | No paid form backend yet — use a `mailto:` link or a clearly stated manual contact method (e.g. WhatsApp Business number once CEO-approved) instead of a hosted form |
| FAQ | 3–5 short, honest answers to likely client questions |
| Privacy/legal basics | A simple, honest privacy note (what contact info is collected and why); recommend real legal review before publishing formal privacy/terms pages |

---

# 4A. Payment Link Integration

The landing page carries **one** active payment button: the AI Workflow Starter Pack, $399 USD, linking to the approved public PayPal payment link (`AOS_Payment_Portal_Readiness_Plan.md`, STRAT-014):

```text
https://www.paypal.com/ncp/payment/2AN8FH99X682C
```

Rules for this section of the site:

- **Currency.** The page states plainly: **"Payments are processed in USD."**
- **Only one active button.** Every other service offer shows a **"Request Custom Quote"** button (linking to the contact method in Section 4), not a payment button, until the CEO approves a separate payment link for it.
- **Consultation-first.** Copy near the payment button should invite a short call first if the visitor isn't sure the standard package fits — e.g. *"Not sure this is the right fit? Book a free 15-minute call first."* — before pointing to the payment link.
- **No credentials on the site.** The site's source contains only the public payment link. It never contains a PayPal login, password, 2FA code, recovery code, API key, or bank detail — consistent with Section 7 below and STRAT-014 Section 3.

---

# 5. Website Build Phases

| Phase | What Happens | CEO Approval Needed |
|-------|---------------|----------------------|
| Phase 1 — Static HTML | Build the page content and layout locally as plain HTML/CSS files inside this repository; nothing is public yet | No (local file creation only) |
| Phase 2 — GitHub Pages (or chosen host) | Publish the static files to a live, public URL | Yes — this is a public action; requires explicit CEO approval of final copy and go-live |
| Phase 3 — Domain | Purchase and connect a custom domain | Yes — this is a spend action; requires CEO budget approval for the domain cost |
| Phase 4 — Form/CRM | Add a real form backend (e.g. Netlify Forms or similar) connected to the lead pipeline (STRAT-008) | Yes — if the tool involves any paid tier or third-party data handling, requires CEO approval per CLAUDE.md Section 5 |

No phase after Phase 1 proceeds without its stated approval.

---

# 6. Local-First Dashboard Link Concept

Once the Revenue Dashboard (`AOS_Revenue_Dashboard_Spec.md`, STRAT-013) exists as a local file-based system, the website could later surface a small, read-only, manually-updated summary (e.g. "X clients served" or general capability statements) — this is a planning concept only, not a build item in this phase. No live data connection, API, or automated sync is proposed here; any future version of this concept would need its own CTO architecture review and CEO approval before build.

---

# 7. Security Notes

- No credentials, API keys, or payment data are ever placed in the website's source code or repository. The one exception — because it is not a credential — is the public PayPal payment link itself (Section 4A), which is safe to embed as plain text/HTML.
- All three recommended hosts (GitHub Pages, Cloudflare Pages, Netlify) serve over HTTPS by default — do not disable this.
- Keep any published contact information spam-resistant (e.g. a dedicated company email rather than a personal one, per `AOS_Channel_and_Account_Setup_Runbook.md`, STRAT-009).
- Guardian reviews the site's security posture (no exposed secrets, no unsafe third-party embeds, and confirmation that only the public payment link — never PayPal login, password, 2FA, recovery codes, or bank details — appears anywhere in the source) before Phase 2 go-live.

---

# 8. Related Documents

- STRAT-005 — AOS Revenue Launch Master Plan
- STRAT-006 — AOS 14-Day Revenue Sprint
- STRAT-009 — AOS Channel and Account Setup Runbook
- STRAT-013 — AOS Revenue Dashboard Spec
- STRAT-014 — AOS Payment Portal Readiness Plan
- PRJ-007 — Launch AOS Revenue Engine

---

# 9. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-12 | Initial version |
| 1.1 | 2026-07-13 | Added Section 4A Payment Link Integration for the approved PayPal public payment link (AI Workflow Starter Pack, $399 USD); updated Website Sections, Security Notes, and Related Documents to reference STRAT-014 |
