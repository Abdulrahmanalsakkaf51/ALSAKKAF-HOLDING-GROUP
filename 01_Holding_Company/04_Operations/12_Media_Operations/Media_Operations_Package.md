# ALSAKKAF HOLDING GROUP

# Media Operations Package

> "Three channels, one factory, one honest report."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-001 |
| Document Type | Media Operations Package Overview |
| Status | Draft — awaiting Founder review |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-018 |
| Related Documents | RLCONTENT-001, CFOS-001, MEDIA-002..011 |

---

# 1. Purpose

This package is the official operating structure for ALSAKKAF HOLDING GROUP media operations on YouTube.

It covers three channels, their identities, their first content plans, their publishing calendars, their quality rules, and the reporting system that lets Atlas summarize views, subscribers, publishing progress, and content output honestly.

Nothing in this package authorizes publishing. Every video, Short, description, and thumbnail requires explicit Founder approval before it goes live.

---

# 2. Channel Portfolio

| # | Channel | Language | Focus | Business Role |
|---|---------|----------|-------|---------------|
| 1 | ALSAKKAF Systems (@ALSAKKAFSystems) | English | AI systems, Partners, and workflows for small business | Lead generation and credibility for AOS AI Services |
| 2 | رحلة عقل (@RihlatAqlOfficial) | Arabic | Knowledge storytelling: science, history, thought, strategy, nature, humanity | Arabic-audience knowledge brand |
| 3 | Sand Dunes Stories | English | Original storytelling: Arabian desert history, culture, and folklore | Standalone media asset with its own monetization path |

---

# 3. Package Contents

| Item | Location |
|------|----------|
| This overview | Media_Operations_Package.md (MEDIA-001) |
| Channel identity, description, and About copy | 01_ALSAKKAF_Systems/Channel_Identity.md (MEDIA-002), 02_Rihlat_Aql/Channel_Identity.md (MEDIA-003), 03_Sand_Dunes_Stories/Channel_Identity.md (MEDIA-004) |
| First 10 videos + first 10 Shorts per channel | Content_Plan_First_Videos_and_Shorts.md in each channel folder (MEDIA-005, MEDIA-006, MEDIA-007) |
| 30-day publishing calendar per channel | Publishing_Calendar_30_Day.csv in each channel folder |
| KPI tracker per channel | KPI_Tracker.csv in each channel folder |
| Thumbnail style guide | Thumbnail_Style_Guide.md (MEDIA-008) |
| Video workflow operating process | Video_Workflow_Operating_Process.md (MEDIA-009) |
| Content review checklist | Content_Review_Checklist.md (MEDIA-010) |
| Atlas YouTube reporting template | Atlas_YouTube_Reporting_Template.md (MEDIA-011) |
| Atlas media briefing tool | 09_AI_Systems/02_Tools/Media_Tools/media_briefing.py |
| Media production structure standard | Media_Production_Structure.md (MEDIA-012) |
| Atlas media production workflow and schemas | Atlas_Media_Production_Workflow.md (MEDIA-013) + Media_Tools scaffold |
| Voice-over system plan | Voice_Over_System_Plan.md (MEDIA-014) |

---

# 4. Standing Rules

1. Original content only. Footage, music, images, and clips must be owned, licensed, or explicitly permitted before an item advances past Idea status. Unconfirmed items are marked "Rights Unconfirmed" and do not move forward.
2. Titles and thumbnails must accurately represent the content. No misleading claims.
3. No student, client, or private data appears in any video, screen recording, or thumbnail.
4. Publishing is a Founder-approved action. The calendars in this package are planning artifacts, not publishing authority.
5. Analytics numbers are never fabricated. If a metric has not been measured, it is reported as zero or "not yet measured".
6. Content that mentions AOS capabilities must stay within what testing has demonstrated, consistent with CDP-001 scope-honesty rules.

---

# 5. How Atlas Reports on Media Operations

The reporting system is deliberately simple and file-based, consistent with PRJ-004 data architecture:

1. Each channel folder holds `Publishing_Calendar_30_Day.csv` (the plan) and `KPI_Tracker.csv` (measured snapshots).
2. When a video is drafted, approved, or published, its `Status` column in the calendar is updated by hand or by a Partner under approval rules.
3. When the Founder exports or reads real YouTube analytics, a dated snapshot row is added to `KPI_Tracker.csv`. Only real numbers enter the tracker.
4. `media_briefing.py` reads all three channels and prints an honest briefing: planned items, drafted, approved, published, plus the latest measured subscribers and views per channel. Zero stays zero.
5. Atlas uses `Atlas_YouTube_Reporting_Template.md` (MEDIA-011) to turn the tool output into the weekly media section of the Founder briefing.

This gives Atlas everything needed to later summarize views, subscribers, publishing progress, and content output without guessing.

---

# 6. Relationship to the Content Factory

The Content Factory Operating System (CFOS-001) defines the production line: topic intake, script drafting, short-form conversion, thumbnail briefs, publishing checklist, reporting checklist, and archive structure. This package defines what the three channels are; CFOS-001 defines how content moves from idea to published and archived. Every item on a channel calendar is expected to pass through the CFOS-001 pipeline.

---

# Related Documents

- 01_Holding_Company/04_Operations/04_Content_Operations/Multi_Platform_Content_Execution_Plan.md (RLCONTENT-001)
- 01_Holding_Company/04_Operations/04_Content_Operations/Content_Factory_Operating_System.md (CFOS-001)
- 01_Holding_Company/04_Operations/01_Project_Records/PRJ-018_Media_Operations_and_Content_Factory.md
- 09_AI_Systems/02_Tools/Media_Tools/media_briefing.py
- 01_Holding_Company/04_Operations/05_Client_Delivery/AOS_Three_Partner_Customer_Deployment_Process.md (CDP-001)

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial Media Operations package |
| 1.1 | 2026-07-15 | Official handles recorded; رحلة عقل direction updated; MEDIA-012..014 added to package |
