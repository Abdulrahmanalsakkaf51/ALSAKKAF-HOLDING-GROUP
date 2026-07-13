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
| Version | 1.1 |
| Created | 2026-07-13 |
| Related Documents | PRJ-007, STRAT-007, STRAT-012, STRAT-014, STRAT-015 |

---

# Purpose

This folder holds the static AOS AI Workflow Starter Pack landing page and the local Atlas CEO dashboard. **Neither is published yet.** Publishing the landing page is a public action and requires explicit CEO approval (GitHub Pages or another host, per `AOS_Static_Website_and_Free_Hosting_Plan.md`, STRAT-012, Phase 2).

---

# What's Inside

| File | Description |
|------|-------------|
| `index.html` | Public landing page selling the AOS AI Workflow Starter Pack ($399 USD) and the AOS AI Agent Starter Pack ($450 USD), each via its own approved PayPal link |
| `styles.css` | Styling for the landing page — plain CSS, no frameworks, no external dependencies |
| `atlas-dashboard.html` | Internal, local-only Atlas CEO dashboard (leads, outreach, content, payments, risks, next actions) |
| `atlas-dashboard.css` | Styling for the Atlas dashboard |
| `atlas-dashboard-data.js` | Local static data file feeding the Atlas dashboard — edit values by hand as real numbers come in; no external calls, no tracking |

---

# Publishing Status

The landing page is **live** at https://abdulrahmanalsakkaf51.github.io/ALSAKKAF-HOLDING-GROUP/ (published 2026-07-13 via GitHub Pages, main branch `/docs`, after explicit CEO approval).

Every update to `index.html` goes live on the next `git push` to main. The pre-update gates remain:

1. CEO review and approval of any copy change
2. Contact email — **Contact: atlasos5555@gmail.com** (Status: Temporary launch contact email approved by Founder; not a permanent address — see STRAT-015 for the future domain-based email plan)
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

1. Contact email — **Contact: atlasos5555@gmail.com** (Status: Temporary launch contact email approved by Founder; permanent domain-based addresses still pending domain purchase)
2. Final landing page copy approved
3. Guardian security review complete
4. Explicit CEO go-live approval

See `AOS_Website_Publishing_and_Contact_Readiness.md` (STRAT-015) for the full publishing checklist and hosting options.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version — landing page and local Atlas dashboard created |
| 1.1 | 2026-07-13 | Added local preview instructions and a pre-publish approval checklist, cross-referencing new STRAT-015 |
| 1.2 | 2026-07-13 | Clarified contact email phrasing: "Contact: atlasos5555@gmail.com" / "Status: Temporary launch contact email approved by Founder" — not labeled permanent |
