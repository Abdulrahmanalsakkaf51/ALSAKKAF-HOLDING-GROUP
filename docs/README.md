# ALSAKKAF HOLDING GROUP

# docs — AOS AI Services Landing Page & Atlas Dashboard

> "Nothing in this folder is published until the CEO says so."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RLWEB-001 |
| Owner | Abdulrahman Alsakkaf |
| Status | Active |
| Version | 1.3 |
| Created | 2026-07-13 |
| Related Documents | PRJ-007, STRAT-007, STRAT-012, STRAT-014, STRAT-015 |

---

# Purpose

This folder holds the static ALSAKKAF Systems (AOS AI Services) landing page and the local Atlas CEO dashboard. The landing page is live at https://alsakkafsystems.com; the Atlas dashboard remains internal and local-only. Any change to the landing page is a public action and requires explicit CEO approval before push (per `AOS_Static_Website_and_Free_Hosting_Plan.md`, STRAT-012).

---

# What's Inside

| File | Description |
|------|-------------|
| `index.html` | Public landing page for ALSAKKAF Systems (AOS AI Services) selling the AI Workflow Starter Pack ($399 USD) and the AI Agent Starter Pack ($450 USD), each via its own approved PayPal link, plus the Founder profile, trust section, and Founding Client Program (mailto application only) |
| `styles.css` | Styling for the landing page — plain CSS, no frameworks, no external dependencies |
| `CNAME` | GitHub Pages custom domain file — must contain exactly `alsakkafsystems.com`; do not delete or the custom domain disconnects |
| `atlas-dashboard.html` | Internal, local-only Atlas CEO dashboard (leads, outreach, content, payments, risks, next actions) |
| `atlas-dashboard.css` | Styling for the Atlas dashboard |
| `atlas-dashboard-data.js` | Local static data file feeding the Atlas dashboard — edit values by hand as real numbers come in; no external calls, no tracking |

---

# Publishing Status

The landing page is **live** at https://alsakkafsystems.com (custom domain purchased by the Founder on 2026-07-14; GitHub Pages DNS check passed; originally published 2026-07-13 via GitHub Pages, main branch `/docs`, after explicit CEO approval).

Every update to `index.html` goes live on the next `git push` to main. The pre-update gates remain:

1. CEO review and approval of any copy change
2. Contact email — professional domain addresses active: hello@alsakkafsystems.com (general), sales@alsakkafsystems.com (quotes/pilot applications), services@alsakkafsystems.com (service enquiries), abdulrahman@alsakkafsystems.com (Founder) — see STRAT-015
3. Guardian security review (no exposed secrets, no unsafe embeds, only the two approved payment links: $399 and $450)
4. Explicit CEO approval to push

The Atlas dashboard (`atlas-dashboard.html`) is an internal tool only. It should never be linked from the public landing page and should not be published to a public host in its current form.

---

# Previewing Locally

| To Preview | Do This |
|------------|---------|
| The landing page | Open `docs/index.html` directly in a browser — no server needed |
| The Atlas dashboard | Open `docs/atlas-dashboard.html` directly in a browser — no server needed |

Both are plain static files. Double-clicking them (or using your editor's "Open with Live Preview/Browser") is enough — nothing needs to be installed or run.

---

# What Still Requires CEO Approval Before Publishing

1. Final landing page copy approved (contact email decision is complete — professional domain addresses are active on alsakkafsystems.com)
2. Guardian security review complete
3. Explicit CEO go-live approval

See `AOS_Website_Publishing_and_Contact_Readiness.md` (STRAT-015) for the full publishing checklist and hosting options.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version — landing page and local Atlas dashboard created |
| 1.1 | 2026-07-13 | Added local preview instructions and a pre-publish approval checklist, cross-referencing new STRAT-015 |
| 1.2 | 2026-07-13 | Clarified contact email phrasing: "Contact: atlasos5555@gmail.com" / "Status: Temporary launch contact email approved by Founder" — not labeled permanent |
| 1.3 | 2026-07-14 | Custom domain live (https://alsakkafsystems.com) with CNAME file; professional contact addresses replaced the temporary Gmail address; public brand refined to ALSAKKAF Systems; Founder profile, trust section, and Founding Client Program added to the landing page |
