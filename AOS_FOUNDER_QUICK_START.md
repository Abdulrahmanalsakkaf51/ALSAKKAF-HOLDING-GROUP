# ALSAKKAF HOLDING GROUP

# AOS Founder Quick Start

> "One page. Everything you need to run today."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RLQS-001 |
| Document Type | Founder Quick Start Guide |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Date | 2026-07-13 |
| Related System | AOS |
| Related Project | PRJ-007 |
| Related Documents | PRJ-007, RLLAUNCH-001, RLOP-005 |

---

# 1. Open the Repo

Open this folder in your editor (e.g. VS Code): the repository root, `ALSAKKAF HOLDING GROUP`.

---

# 2. Run Atlas Health Check

```
py "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" health-check
```

Confirms the required folders/files exist, the payment link is correct, and no credentials are stored.

---

# 3. Run War Room

```
py "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" war-room
```

Or just double-click **`RUN_ATLAS_COMMAND_CENTER.bat`** (or the `.ps1` version) at the repo root. This runs the brief, dashboard update, payment report, and content pack together and writes one combined report.

---

# 4. Open the Landing Page

Open `docs/index.html` directly in a browser. This previews the AOS AI Workflow Starter Pack sales page — it is **not published** yet.

---

# 5. Open the Dashboard

Open `docs/atlas-dashboard.html` directly in a browser. This is your internal, local-only CEO command center — leads, outreach, content, payments, risks, next actions.

---

# 6. Update the Lead Tracker

Edit `01_Holding_Company/04_Operations/03_Revenue_Operations/Lead_Tracker.csv` directly (Excel, Google Sheets import, or a text editor) as you find and qualify real leads. Never invent fake leads — leave rows empty until they're real.

---

# 7. Generate a Briefing

```
py "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" brief
```

Produces a daily CEO briefing from your current tracker data.

---

# 8. Generate a Proposal

```
py "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" proposal
```

Drafts a proposal for the AOS AI Workflow Starter Pack ($399 USD). Review and personalize before sending — Atlas never sends it for you.

---

# 9. Generate a Content Pack

```
py "09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py" content-pack
```

Produces a day's worth of platform-ready draft posts (LinkedIn, Threads, Instagram, TikTok, YouTube Shorts). Review before posting — nothing is published automatically.

---

# 10. Publish the Website (Later)

Do not publish until `AOS_Website_Publishing_and_Contact_Readiness.md` (STRAT-015) checklist is fully complete: copy approved, contact email chosen, Guardian review done, and your explicit go-live approval given.

---

# 11. What Not To Do

- Do not send anything (email, DM, message) without personally reviewing and approving it first.
- Do not create real accounts automatically — you create or approve every account manually.
- Do not store any credential, password, 2FA code, recovery code, API key, or bank detail anywhere in this repository.
- Do not claim or promise guaranteed revenue to anyone.
- Do not spend money or approve ad spend without deciding the exact amount first.

---

# 12. Emergency Rules

If anything looks wrong — a draft feels off, a number looks inflated, a file looks like it might contain something sensitive — **stop and don't force it**. Ask Claude/Atlas to explain what happened, or check the relevant Guardian notes, before proceeding.

Nothing in this system can send a message, publish content, create a real account, or spend a cent without you personally doing it. If something ever appears to have happened without your direct action, that is a bug to report and fix, not something to work around.

---

# 13. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version |
