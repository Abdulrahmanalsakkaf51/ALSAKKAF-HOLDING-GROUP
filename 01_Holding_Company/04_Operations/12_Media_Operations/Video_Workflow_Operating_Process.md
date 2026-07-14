# ALSAKKAF HOLDING GROUP

# Video Workflow Operating Process

> "Every video moves through the same gates, or it does not move."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-009 |
| Document Type | Media Operating Process |
| Status | Draft — awaiting Founder review |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-001, MEDIA-010, CFOS-001 |

---

# 1. Purpose

This is the single operating process every long-form video and Short follows, on all three channels. It assigns each step to a role so Atlas and future Partners can support production without taking over decisions that belong to the Founder.

---

# 2. Status Values

Every content item carries exactly one status in its channel's `Publishing_Calendar_30_Day.csv`:

| Status | Meaning |
|--------|---------|
| Idea | Listed on the calendar, nothing produced |
| Drafted | Script and asset list exist; rights confirmed |
| Recorded | Footage/voiceover captured |
| Edited | Cut, graphics, and thumbnail ready |
| Approved | Founder approved video + title + description + thumbnail |
| Published | Live on YouTube (Founder action) |
| Reported | Performance snapshot recorded in KPI_Tracker.csv |

An item may not skip a status. Rights confirmation is the gate between Idea and Drafted.

---

# 3. The Process

| # | Step | Who | Output |
|---|------|-----|--------|
| 1 | Topic intake | Founder or Partner proposes; Founder accepts onto calendar | Calendar row (Idea) |
| 2 | Rights check | Founder confirms footage/music/image rights | Rights_Status = Confirmed |
| 3 | Script draft | Partner drafts per CFOS-001 script standard | Script file in channel archive |
| 4 | Founder script review | Founder edits and accepts the script | Status = Drafted |
| 5 | Record | Founder records voice/screen/footage | Raw assets in archive |
| 6 | Edit | Founder (or editor later) cuts the video | Status = Recorded, then Edited |
| 7 | Packaging | Partner drafts title options, description, tags, thumbnail brief | Packaging block in archive |
| 8 | Review checklist | Run Content_Review_Checklist.md (MEDIA-010) — every item | Completed checklist |
| 9 | Founder approval | Founder approves the complete package | Status = Approved |
| 10 | Publish | Founder publishes or schedules on YouTube | Status = Published |
| 11 | Short-form conversion | Per CFOS-001, eligible long-form gets 1-3 Shorts derived | New calendar rows |
| 12 | Report | Real numbers added to KPI_Tracker.csv on the weekly cadence | Status = Reported |

---

# 4. Role Boundaries

1. Partners and Atlas draft scripts, titles, descriptions, briefs, and reports. They never publish, upload, or schedule.
2. The Founder is the only publishing authority and the only person who touches the YouTube account.
3. No tool or Partner stores YouTube credentials anywhere in the repository.
4. Analytics enter the system only as real exported or hand-copied numbers in KPI_Tracker.csv.

---

# 5. Weekly Operating Rhythm

| Day | Action |
|-----|--------|
| Sunday | Review calendar week ahead; confirm rights for upcoming items |
| Monday-Thursday | Draft, record, edit per calendar |
| Friday | Founder approval session for finished packages |
| Saturday | Update KPI trackers with real numbers; run media_briefing.py; Atlas prepares the weekly media report (MEDIA-011) |

---

# Related Documents

- Media_Operations_Package.md (MEDIA-001)
- Content_Review_Checklist.md (MEDIA-010)
- Atlas_YouTube_Reporting_Template.md (MEDIA-011)
- 01_Holding_Company/04_Operations/04_Content_Operations/Content_Factory_Operating_System.md (CFOS-001)

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial video workflow operating process |
