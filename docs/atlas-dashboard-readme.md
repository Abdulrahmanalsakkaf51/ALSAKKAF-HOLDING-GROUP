# ALSAKKAF HOLDING GROUP

# Atlas Dashboard — README

> "Local, static, and honest. Zero until it's real."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RLWEB-002 |
| Owner | Abdulrahman Alsakkaf |
| Status | Active |
| Version | 1.0 |
| Created | 2026-07-13 |
| Related Documents | PRJ-007, ASAP-001, RLWEB-001 |

---

# How to Open the Dashboard Locally

Open `docs/atlas-dashboard.html` directly in any browser — double-click it, or use your editor's "Open with Live Preview/Browser." No server, no build step, no installation needed.

---

# How to Refresh Dashboard Data Using Atlas Runtime

The dashboard reads from `docs/atlas-dashboard-data.js`, which is auto-generated. To refresh it with current tracker counts, from the repository root run:

```text
py "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" dashboard
```

Or run the full war-room report (which refreshes the dashboard as one step among several):

```text
py "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" war-room
```

Then reload `atlas-dashboard.html` in your browser to see the updated numbers.

**Do not hand-edit the numeric fields in `atlas-dashboard-data.js`** — edit the source trackers (`Lead_Tracker.csv`, `Outreach_Tracker.csv`, `Client_Pipeline.csv`, `Content_Calendar.csv`, `Content_Analytics_Tracker.csv`) instead, then re-run the `dashboard` command.

---

# What the Dashboard Can Do

- Show real counts pulled from the CSV trackers (leads, outreach, pipeline, content, payments)
- Show the active offer and the one approved PayPal payment link
- Show honest zeros with "No real leads entered yet" until real data exists
- Show CEO decisions needed, risks, Guardian notes, and next actions
- Show a last-updated timestamp for the data it's displaying

---

# What the Dashboard Cannot Do

- It cannot send anything, publish anything, or spend anything
- It cannot connect to PayPal, email, or any social platform — it has no network access
- It cannot create real accounts
- It cannot store or display credentials of any kind
- It does not auto-refresh — you must re-run `atlas.py dashboard` (or `war-room`) and reload the page

---

# Publishing Warning

This dashboard is an **internal CEO tool only**. It must never be linked from the public landing page (`docs/index.html`) and must never be published to a public host in its current form. It carries a `noindex, nofollow` meta tag as a baseline precaution, but that is not a substitute for simply not publishing it. See `AOS_Website_Publishing_and_Contact_Readiness.md` (STRAT-015) for the landing page's own publishing checklist — the dashboard is out of scope for that checklist entirely.

---

# Related Documents

- ASAP-001 — Atlas Super Assistant v1 Acceleration Plan
- RLWEB-001 — docs/README.md
- STRAT-015 — AOS Website Publishing and Contact Readiness

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version |
