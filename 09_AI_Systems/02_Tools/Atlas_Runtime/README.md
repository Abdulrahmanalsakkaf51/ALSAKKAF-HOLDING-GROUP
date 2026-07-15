# ALSAKKAF HOLDING GROUP

# Atlas Runtime

> "Atlas reads trackers and drafts output. It never sends, publishes, or spends anything."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | ARUN-001 |
| Owner | Abdulrahman Alsakkaf |
| Status | Active |
| Version | 1.0 |
| Created | 2026-07-13 |
| Related Documents | PRJ-007, RTASK-001, ARPROMPT-001, ASAP-001 |

---

# 1. Purpose

Atlas Runtime is a local, Python-standard-library-only command-line tool that turns the AOS Launch Version v1 documents and trackers into a working, usable local assistant. It reads the CSV trackers, generates drafts and reports, and keeps `docs/atlas-dashboard-data.js` current — all without network access, external packages, paid APIs, or credentials of any kind.

---

# 2. Requirements

- Python 3 (accessed via the `py` launcher on Windows). No external packages — standard library only.
- No internet connection required or used.
- No API keys, no `.env` file, no configuration beyond `atlas_config.json`.

---

# 3. Commands

Run from the repository root (or use `run_atlas.ps1` / `run_atlas.bat`, which resolve their own location):

| Command | What It Does |
|---------|---------------|
| `health-check` | Verifies required files/folders exist, the payment link is present in key files, no credential-like values are stored, and trackers are readable. Prints PASS/FAIL. |
| `brief` | Reads all trackers and writes a daily CEO briefing to `Atlas_Output/`. |
| `score-leads` | Scores real (non-placeholder) rows in `Lead_Tracker.csv`. Never invents leads. |
| `dashboard` | Recomputes tracker counts and rewrites `docs/atlas-dashboard-data.js`. |
| `proposal [--client "Name"]` | Generates a proposal draft for the AI Workflow Starter Pack ($399 USD). |
| `outreach` | Generates a batch of personalized outreach drafts. Nothing is sent. |
| `content-pack` | Generates a daily multi-platform content draft pack. |
| `delivery-checklist [--client "Name"]` | Generates a client delivery checklist. |
| `payment-report` | Reads `Client_Pipeline.csv` and reports paid/unpaid/link-sent status. Never connects to PayPal. |
| `war-room` | Runs `brief` + `dashboard` + `payment-report` + `content-pack` together and writes `Atlas_War_Room_Report.md`. |
| `revenue-sprint` | Generates the PRJ-009 revenue sprint status report (offers, publish status, leads, outreach, proposals, payments). |
| `ai-agent-proposal [--client "Name"]` | Generates a proposal draft for the AI Agent Starter Pack ($450 USD). |
| `ai-agent-delivery [--client "Name"]` | Generates the AI Agent Starter Pack delivery checklist. |
| `first-5-outreach` | Generates the first-5 outreach execution pack from the top-scored real leads. Never invents leads. |
| `task-queue` | Builds a prioritized task queue (pipeline > outreach > leads > content) from the public trackers only. Every line is tagged `[FACT]`, `[DRAFT]`, or `[INFERENCE]` with a Source note. Never invents a task. |
| `lead-review-queue` | Builds a lead review queue. Uses the private lead tracker (`ALSAKKAF PRIVATE OPERATIONS`, outside the repo) if it exists, and writes that report only to the private output folder. Falls back to the public template-only tracker and `Atlas_Output/` if the private store isn't present. Console output is counts only, never a name. |
| `comms-approval-queue` | Builds a CEO comms approval queue (every outreach item not yet approved and not yet sent). Same private/public fallback pattern as `lead-review-queue`. |
| `ops-status` | Operations status rollup: re-runs `health-check`, lists active Partners from `atlas_config.json`, reports the dashboard's `lastUpdated` timestamp, and gives a plain PASS/FAIL. |
| `media-store-task-report` | Public-repo-only checklist of standard store/media pages, based on searching for a NESTLYRA folder under `01_Holding_Company`. Reports honestly if none is found. |
| `daily-cycle` | Runs the full daily operating cycle (`health-check` → `brief` → `dashboard` → `payment-report` → `content-pack` → `task-queue` → `lead-review-queue` → `comms-approval-queue` → `ops-status` → `media-store-task-report`) and writes one consolidated `Atlas_Daily_Operating_Cycle_{date}.md` linking every report by path. Does not replace `war-room`. |

Examples:

```text
py atlas.py health-check
py atlas.py war-room
py atlas.py proposal --client "Example Co"
```

---

# 4. Safety Rules

- Atlas Runtime never sends an email, DM, or message.
- Atlas Runtime never publishes anything.
- Atlas Runtime never spends money or connects to PayPal, a bank, or any payment processor.
- Atlas Runtime never requests, reads, or writes a password, 2FA code, recovery code, API key, secret key, or bank detail. Its credential scan (`health-check`) actively checks for these appearing anywhere in the repo.
- Atlas Runtime never invents a real lead. If a tracker only contains example/placeholder rows, commands report zero and say so honestly.
- Every generated outreach or proposal draft is explicitly marked "CEO Approval Required."

---

# 5. Files in This Folder

| File | Purpose |
|------|---------|
| `atlas.py` | The runtime tool itself. |
| `atlas_config.json` | Paths, active offer, payment link, and scan settings. Edit this, not the code, to change file locations. |
| `run_atlas.ps1` / `run_atlas.bat` | Thin launchers that forward arguments to `atlas.py`. |
| `test_atlas_runtime.py` | Automated test suite — run after any change to `atlas.py`. |
| `test_prj_009_revenue_sprint.py` | PRJ-009 revenue sprint release test (offers, payment link discipline, delivery system, sprint files). |
| `test_atlas_operational_readiness.py` | Operational readiness test suite for the 6 newer commands (`task-queue`, `lead-review-queue`, `comms-approval-queue`, `ops-status`, `media-store-task-report`, `daily-cycle`), including the private/public fallback logic and a private-data leak scan. |
| `Atlas_Runtime_Test_Log.md` | Record of test runs and results. |

---

# 6. How Output Is Organized

All generated files go to `01_Holding_Company/08_Reports/Atlas_Output/` (see that folder's own `README.md` for the full breakdown by subfolder) — with one exception: `lead-review-queue` and `comms-approval-queue` write to the private, non-Git folder `ALSAKKAF PRIVATE OPERATIONS/01_Revenue_Operations/PRJ-016/06_Founder_Briefings/` whenever the private lead/outreach trackers exist there, per the Private Operational Data Standard (PODS-001). This keeps real company and contact names out of the repository entirely. Console output for those two commands is always counts-only. `write_output_private()` hard-refuses to write anywhere inside the repository, regardless of configuration.

---

# 7. Related Documents

- ASAP-001 — Atlas Super Assistant v1 Acceleration Plan
- RTASK-001 — Atlas Revenue Task Routing v1
- ARPROMPT-001 — Atlas Revenue Operator Prompt v1
- PRJ-007 — Launch AOS Revenue Engine
- PODS-001 — Private Operational Data Standard

---

# 8. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version — 10 commands implemented and tested |
| 1.2 | 2026-07-16 | Added 6 commands — `task-queue`, `lead-review-queue`, `comms-approval-queue`, `ops-status`, `media-store-task-report`, `daily-cycle` (14 → 20 total). Added private/public fallback pattern and `write_output_private()` hard guard for PODS-001 compliance. |
