# ALSAKKAF HOLDING GROUP

# Atlas Super Assistant v1 Acceleration Plan

> "Not the six-to-twelve-month dream system. The first version that actually chases the first $399."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | ASAP-001 |
| Document Type | Architecture — Acceleration Plan |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-13 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-007 |
| Related Documents | ASAA-001, PRJ-007, PREG-001, GRCA-001 |

---

# 1. Purpose

This plan turns AOS Launch Version v1 — a set of well-organized documents — into a working local Atlas assistant, fast, without breaking AOS discipline. It accelerates the existing Atlas Super Assistant Architecture (ASAA-001) into a usable v1 runtime, scoped tightly to the AOS Revenue Launch (PRJ-007).

---

# 2. What Atlas v1 Will Do

Atlas v1 can, on the Founder's machine, with no network access:

1. Brief the CEO from real tracker data
2. Read Lead_Tracker.csv, Outreach_Tracker.csv, Client_Pipeline.csv, Content_Calendar.csv, Content_Analytics_Tracker.csv
3. Score leads using the columns already in Lead_Tracker.csv
4. Generate outreach drafts (never sent — drafts only)
5. Generate proposal drafts for the AI Workflow Starter Pack
6. Generate client delivery checklists
7. Update local dashboard data (`docs/atlas-dashboard-data.js`) from real tracker counts
8. Generate revenue and payment status reports
9. Generate daily content packs across LinkedIn, Threads, Instagram, TikTok, and YouTube Shorts
10. Route work to the three active Partners (Atlas, The Librarian, Guardian) per the existing task routing document
11. Warn about risks (no real leads yet, website not published, credentials never stored)
12. Prepare a concrete next-actions list every time it runs

---

# 3. What Atlas v1 Will Not Do

- Send outreach, email, or social messages of any kind
- Publish content or the website
- Spend money or process a payment
- Create real accounts of any kind
- Store credentials, passwords, 2FA codes, recovery codes, API keys, secret keys, or bank details
- Guarantee any revenue outcome
- Invent real leads, real clients, or real contact data
- Call any network or paid API
- Activate a new Partner, change a Partner ID, or change Partner Registry status

---

# 4. Build Waves

| Wave | Contents |
|------|----------|
| Wave 1 | Claude Code subagent definitions + this Acceleration Plan |
| Wave 2 | Atlas Runtime core (`atlas.py`, config, launchers) |
| Wave 3 | Atlas_Output folder tree + Dashboard v2 |
| Wave 4 | Revenue templates, service delivery engine, First 72 Hours Playbook, publishing readiness, Founder Quick Start |
| Wave 5 | Automated tests, register updates, safety checks, release |

---

# 5. Safety Gates

The following always require explicit CEO approval before they happen, regardless of which command or document prepares them:

| Action | Gate |
|--------|------|
| Sending outreach | CEO approves message + recipient |
| Publishing content or the website | CEO approves final copy and go-live |
| Spending money | CEO approves specific amount and purpose |
| Creating a real account | CEO creates or approves manually; Guardian reviews security first |
| Agreeing pricing / closing a deal | CEO approves final price and terms |
| Activating a new Partner | Full Partner Factory lifecycle (PCL-001) completed |

---

# 6. Tool Architecture

- `09_AI_Systems/02_Tools/Atlas_Runtime/atlas.py` — a single-file, Python-standard-library-only CLI with 10 subcommands
- `atlas_config.json` — paths and settings the CLI reads (tracker locations, output locations, active offer/link)
- `run_atlas.ps1` / `run_atlas.bat` — thin launchers for the Founder
- `test_atlas_runtime.py` — a stdlib-only automated test suite verifying the tool's structural integrity and safe behavior
- `docs/atlas-dashboard.html/.css/.js` — the local, static, no-dependency dashboard the CLI's `dashboard` command updates

---

# 7. Data Flow

```text
CSV trackers (Revenue_Operations, Content_Operations)
  leads to atlas.py commands
    which write to 01_Holding_Company/08_Reports/Atlas_Output/ (Markdown reports, drafts)
    and update docs/atlas-dashboard-data.js (dashboard numbers)
```

No step in this flow touches the network or writes outside the repository.

---

# 8. Dashboard Flow

`atlas.py dashboard` reads the trackers, counts rows/statuses, and rewrites `docs/atlas-dashboard-data.js` with the current real numbers (or honest zeros with "No real leads entered yet" if trackers are still empty). `docs/atlas-dashboard.html` renders that data file. The dashboard remains entirely local and is never published — it is a separate file from the public `index.html` landing page.

---

# 9. Revenue Flow

```text
Lead found -> logged in Lead_Tracker.csv -> scored (atlas.py score-leads)
   -> outreach drafted (atlas.py outreach) -> CEO approves -> sent manually
   -> reply -> proposal drafted (atlas.py proposal) -> PayPal link sent only
   after interest confirmed -> Client_Pipeline.csv updated -> payment-report
```

---

# 10. Lead Flow

`Lead_Tracker.csv` is the single source of truth for leads. `atlas.py score-leads` reads it, scores whatever rows exist using the tracker's own columns (fit/urgency/reachability-style signals already defined in STRAT-008), and writes a scored report. It never invents a row — if the tracker holds only the example/placeholder row, the output says so honestly.

---

# 11. Proposal Flow

`atlas.py proposal` fills `Proposal_AI_Workflow_Starter_Template.md` with either supplied client details or leaves it blank/templated if none are given, always at $399 USD with consultation-first wording, and writes the result to `Atlas_Output/Proposal_Drafts/`.

---

# 12. Content Flow

`atlas.py content-pack` reads the Content Operations files (calendar, script bank, service content posts) and assembles a daily pack — one item per platform (LinkedIn, Threads, Instagram, TikTok, YouTube Shorts) — into `Atlas_Output/Content_Packs/`. No fake claims, no guaranteed-income claims, draft only.

---

# 13. Partner Routing

Only three Partners are active: Atlas (PARTNER-002), The Librarian (PARTNER-001), and Guardian (PARTNER-016). Atlas Runtime's outputs route to them per `Atlas_Revenue_Task_Routing_v1.md` (RTASK-001): Atlas drafts and reports, Guardian reviews security/credential/payment risk, The Librarian indexes new reports and templates. No other Partner is activated by this plan or by Atlas Runtime.

---

# 14. Testing Plan

`test_atlas_runtime.py` checks: `atlas.py` and its config exist; required tracker files exist; the dashboard files exist; `health-check`, `dashboard`, `brief`, and `payment-report` commands run without error; no obvious credential strings appear in any Atlas Runtime, config, or docs file. Before release, `health-check` and `war-room` are also run manually end-to-end.

---

# 15. Release Criteria

- `test_atlas_runtime.py` reports PASS
- `markdown_audit.py` reports `Issues found: 0`
- Secret/credential scan finds no actual credential values
- `git diff --stat` shows only the files intended for this build
- No Partner ID or Partner Registry status changed incorrectly

---

# 16. Next Version Roadmap

Not built now — flagged honestly for a later, separately-approved version:

- Real lead ingestion once the CEO approves a specific research method
- A published, form-connected website (Phase 3/4 of STRAT-012) once the CEO approves going live
- Richer lead scoring once real outcomes exist to calibrate against
- Any paid tool or API integration, only with explicit CEO budget approval

---

# 17. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version |
