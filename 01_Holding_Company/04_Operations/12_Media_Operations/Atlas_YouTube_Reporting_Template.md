# ALSAKKAF HOLDING GROUP

# Atlas YouTube Reporting Template

> "Report what was measured. Zero stays zero."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-011 |
| Document Type | Reporting Template |
| Status | Draft — awaiting Founder review |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-001, MEDIA-009, RPTSKILL-001 |

---

# 1. Purpose

This is the fixed format Atlas uses for the weekly media section of the Founder briefing. All numbers come from the channel KPI trackers and publishing calendars — never from memory or estimation. The `media_briefing.py` tool computes the counts; Atlas adds the narrative.

---

# 2. Reporting Rules

1. Only rows that exist in `KPI_Tracker.csv` may be cited as metrics. If a channel has no snapshot yet, report "No measured data yet".
2. Publishing progress counts come from calendar `Status` values, counted, not estimated.
3. Week-over-week deltas are only reported when two real snapshots exist.
4. No projections in this report. Forecasting belongs to the aos-financial-forecast process, clearly labeled.
5. Stale data is flagged: if the latest snapshot is older than 14 days, the report must say so.

---

# 3. Weekly Media Report Format

```text
ATLAS WEEKLY MEDIA REPORT — [date]

1. PUBLISHING PROGRESS (per channel)
   - Channel: [name]
     Planned: [n]  Drafted: [n]  Approved: [n]  Published: [n]
     On calendar this week: [items]
     Behind / on schedule: [honest statement]

2. AUDIENCE (per channel, latest measured snapshot [snapshot date])
   - Subscribers: [n or "no measured data yet"]
   - Total views: [n or "no measured data yet"]
   - Delta vs previous snapshot: [n or "only one snapshot exists"]

3. CONTENT OUTPUT THIS WEEK
   - Scripts drafted: [n]
   - Videos recorded/edited: [n]
   - Shorts produced: [n]

4. BLOCKED / WAITING
   - Items waiting on rights confirmation: [list]
   - Items waiting on Founder approval: [list]

5. ONE LESSON
   - [single observed lesson, fed to aos-learning-loop when a real pattern emerges]
```

---

# 4. Monthly Addendum

Once per month, Atlas appends: total published to date per channel, subscriber trend across all snapshots, the best and worst performing item with one sentence each on why (only if analytics support the statement), and any revenue figures the Founder has recorded (channel monetization is expected to be zero until thresholds are met — report it as zero).

---

# Related Documents

- Media_Operations_Package.md (MEDIA-001)
- Video_Workflow_Operating_Process.md (MEDIA-009)
- 09_AI_Systems/02_Tools/Media_Tools/media_briefing.py
- Channel KPI trackers in each channel folder

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial Atlas YouTube reporting template |
