# ALSAKKAF HOLDING GROUP

# Content Factory Operating System

> "Ideas enter one door. Published, archived, reported content leaves the other."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CFOS-001 |
| Document Type | Operating System — Content Production |
| Status | Draft — awaiting Founder review |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-001, MEDIA-009, MEDIA-010, RLCONTENT-001, STRAT-010 |

---

# 1. Purpose

The Content Factory is the production line every piece of content passes through, on any channel or platform. It is designed so Atlas and Partners can operate most stages as drafting roles, while the Founder holds every publish decision.

It has seven stations: topic intake, script drafting, short-form conversion, thumbnail brief, publishing checklist, reporting checklist, and the content archive.

---

# 2. Station 1 — Topic Intake

Every idea enters as an intake record before any work happens.

Intake record format (one block per idea, filed in the channel archive under `00_Intake/`):

```text
TOPIC INTAKE
ID:            [channel prefix]-[running number], e.g. SYS-011
Channel:       [ALSAKKAF Systems | رحلة عقل | Sand Dunes Stories | other platform]
Working title: [one line]
Core promise:  [what the viewer gets, one sentence]
Pillar:        [channel pillar]
Format:        [Long | Short | Both]
Rights plan:   [what footage/music/images are needed and how they will be owned/licensed]
Source needs:  [claims that will need real sources, if any]
Proposed by:   [Founder | Atlas | Partner name]
Decision:      [Accepted onto calendar | Parked | Rejected] — Founder only
```

Rules: a rejected topic keeps its record (rejections teach); an accepted topic gets a calendar row with status Idea.

---

# 3. Station 2 — Script Drafting

A Partner or Atlas drafts from the intake record. The script standard:

1. Hook first: the opening 20 seconds are written word-for-word.
2. One core promise, delivered — no detours that break the title's promise.
3. Claims that need sources carry an inline `[source: ...]` note; unsourced claims are marked `[VERIFY]` and must be resolved or removed before review.
4. Written for the ear: short sentences, spoken rhythm, the channel's tone (see the channel identity record).
5. Ends with one honest CTA.
6. Draft is filed in the archive under `01_Scripts/` and the calendar row moves to Drafted only after Founder review and rights confirmation.

---

# 4. Station 3 — Short-Form Conversion

Every approved long-form script is scanned for derivable Shorts before it is even recorded:

1. Identify 1-3 self-contained moments (a fact, a demo, a single argument).
2. Each becomes its own mini-script: hook line, 30-45 seconds of substance, CTA back to the long-form video.
3. Derived Shorts get their own calendar rows and intake IDs (suffix -S1, -S2), inheriting the parent's rights confirmation only where they use the same assets.
4. A Short must stand alone — a viewer who never sees the long-form video still gets full value.

---

# 5. Station 4 — Thumbnail Brief

For every long-form video, a Partner generates a thumbnail brief:

```text
THUMBNAIL BRIEF
Video ID:      [intake ID]
Focal subject: [one subject]
Text:          [max 4 words]
Palette/style: [per Thumbnail_Style_Guide.md channel column]
Image claim:   [what the image promises — must appear in the video]
Source images: [owned / licensed / to produce — with license note]
```

The brief goes to the archive under `02_Packaging/`. Production follows MEDIA-008.

---

# 6. Station 5 — Publishing Checklist

Run per item, after editing, before Founder approval:

1. Content Review Checklist (MEDIA-010) completed — all 18 checks.
2. Title chosen from 3-5 drafted options; describes actual content.
3. Description drafted: hook in first two lines, honest links only.
4. Tags and category set; language setting correct (Arabic for رحلة عقل).
5. Thumbnail final and per style guide.
6. Calendar row status set to Approved only after the Founder approves the full package.
7. Publishing itself is done by the Founder on the YouTube account. No Partner, tool, or script uploads or schedules anything.

---

# 7. Station 6 — Reporting Checklist

Weekly (Saturday, per MEDIA-009 rhythm):

1. Update each published item's calendar status.
2. Add one real snapshot row per channel to `KPI_Tracker.csv` (only measured numbers; skip the row rather than estimate).
3. Run `py 09_AI_Systems\02_Tools\Media_Tools\media_briefing.py`.
4. Atlas fills the Atlas YouTube Reporting Template (MEDIA-011) from the tool output.
5. One lesson per week is recorded; real patterns go to the aos-learning-loop process.

---

# 8. Station 7 — Content Archive Structure

Each channel folder in `12_Media_Operations` gains an `Archive/` tree as production starts (created when first used, not as empty placeholders):

```text
[channel]/Archive/
  00_Intake/        Topic intake records (accepted, parked, and rejected)
  01_Scripts/       Script drafts and final scripts with source notes
  02_Packaging/     Titles, descriptions, thumbnail briefs, checklists
  03_Published/     Final published record per item: date, URL, final title
  04_Lessons/       Weekly lessons and analytics observations
```

Raw video/audio files stay outside the Git repository (local media storage per PRJ-004 data architecture); the archive stores text records only.

---

# 9. Roles Summary

| Station | Atlas / Partners | Founder |
|---------|------------------|---------|
| Topic intake | Propose, format records | Accept / park / reject |
| Script drafting | Draft, mark [VERIFY] items | Review, resolve, approve |
| Short-form conversion | Identify and draft | Approve |
| Thumbnail brief | Generate brief | Approve image |
| Publishing checklist | Run checks, prepare package | Final approval and the publish action |
| Reporting | Compute and draft reports | Read, decide |
| Archive | File everything | Spot-check |

---

# Related Documents

- 01_Holding_Company/04_Operations/12_Media_Operations/Media_Operations_Package.md (MEDIA-001)
- Video_Workflow_Operating_Process.md (MEDIA-009)
- Content_Review_Checklist.md (MEDIA-010)
- Multi_Platform_Content_Execution_Plan.md (RLCONTENT-001)
- 09_AI_Systems/02_Tools/Media_Tools/media_briefing.py

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial Content Factory Operating System |
