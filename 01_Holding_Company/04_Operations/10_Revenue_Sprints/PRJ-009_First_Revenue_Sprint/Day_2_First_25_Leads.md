# ALSAKKAF HOLDING GROUP

# Day 2 — First 25 Leads

> "A lead is a real business with a real name, a real contact path, and a real problem you observed."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RSP-003 |
| Document Type | Sprint Day Plan |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-13 |
| Owner | Founder / CEO |
| Related System | AOS |
| Related Project | PRJ-009 |
| Related Documents | RSP-001, RLOP-002, STRAT-016, First_25_Leads_Template.csv |

---

# 1. Target

25 real leads in your chosen market by end of day, logged in `First_25_Leads_Template.csv` (working file), then copied into `Lead_Tracker.csv` (official tracker). Never invent, never guess emails, never log a business you didn't actually look at.

# 2. Method — 5 Batches of 5 (about 45 min per batch)

For each lead:

1. Find the business (Google Maps, directories, Instagram, LinkedIn — your Day 1 bookmarks)
2. Open their website/profile for 2-3 minutes
3. Write the Problem Observed in one honest sentence — what you actually saw (no online booking trail, no visible follow-up system, owner answering everything personally, inconsistent posting, etc.)
4. Record a contact path: email, contact form, or DM handle
5. Pick the Offer Match: $399 Workflow Pack, $450 AI Agent Pack, or Custom
6. Fill the row completely before moving on

Batch rhythm: 5 leads, then 10-minute break. Quality bar: if you can't name a real observed problem, it's not a lead — skip it.

# 3. Scoring (30 min, after all 25)

- [ ] Copy completed rows into `01_Holding_Company\04_Operations\03_Revenue_Operations\Lead_Tracker.csv`
- [ ] Run `py 09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py score-leads`
- [ ] Read the scoring report; mark your top 5 leads for tomorrow's outreach

# 4. End of Day — Log It

- [ ] 25 rows complete (or the honest number you reached — log the real count)
- [ ] Top 5 outreach candidates chosen with one-line reasons
- [ ] Run `py 09_AI_Systems\02_Tools\Atlas_Runtime\atlas.py dashboard` to refresh the numbers

---

# 5. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-13 | Initial version (PRJ-009) |
