# ALSAKKAF HOLDING GROUP

# Media Production Structure

> "Every video is a folder. Every claim has a source. Every publish is a Founder action."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-012 |
| Document Type | Media Operations Structure Standard |
| Status | Draft — awaiting Founder review |
| Version | 1.0 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-001, MEDIA-009, CFOS-001, MEDIA-013 |

---

# 1. Purpose

This standard defines where every media production artifact lives, so Atlas, Partners, and the Founder always know where to find and file things. It implements the Founder's required categories: channel identity, content orders, research and sources, scripts, storyboards, AI visual prompts, voice/narration manifests, audio, project files, export records, thumbnails, upload packages, published-content register, analytics reports, and archive.

---

# 2. Channel Folder Layout

Each channel folder under `12_Media_Operations/` contains:

```text
<channel>/
  Channel_Identity.md                    Channel identity record
  Content_Plan_First_Videos_and_Shorts.md
  Publishing_Calendar_30_Day.csv         Plan and status per item
  KPI_Tracker.csv                        Measured audience snapshots
  Production/
    Content_Orders.csv                   Register of all content orders
    Published_Content_Register.csv       Register of everything actually published
    Analytics/                           Dated analytics report files
    <ITEM-ID>_<slug>/                    One folder per content item (Section 4)
  Archive/                               Closed items, per CFOS-001 Station 7
```

---

# 3. Item IDs

| Channel | Main video prefix | Short prefix |
|---------|-------------------|--------------|
| ALSAKKAF Systems | SYS-VID-### | SYS-SRT-### |
| رحلة عقل (@RihlatAqlOfficial) | RA-VID-### | RA-SRT-### |
| Sand Dunes Stories | SDS-VID-### | SDS-SRT-### |

---

# 4. Per-Item Production Package

Every content item folder contains exactly these files:

| File | Contains |
|------|----------|
| 01_Content_Order_and_Research.md | The content order, the research record with sources per claim, and the AI-disclosure review |
| 02_Script.md | The script with scene timing; `[VERIFY]` items must be resolved before Founder review |
| 03_Production_Plan.md | Storyboard/shot list, asset manifest, AI image/video prompts, screen-recording requirements, narration manifest, music and SFX guidance, and the audio / project-file / export record tables |
| 04_Upload_Package.md | Thumbnail brief, upload title, description, tags, captions status, checklist, and the Founder review gate |
| Captions draft (.srt) | Draft subtitles in the video's language |

---

# 5. Where Media Files Live (Not in Git)

Raw and rendered media — audio recordings, project files (video editor projects), exported MP4s, thumbnail source files — stay in local media storage outside the repository, per the PRJ-004 data architecture. The repository stores their **records**: filename, location, duration, checksum where useful, and status. A video may only be called "rendered" when a real MP4 exists at the recorded location and has been inspected by a human.

Recommended local root (outside Git and outside OneDrive public repo):

```text
ALSAKKAF MEDIA STORAGE/<channel>/<ITEM-ID>/
  audio/  project/  exports/  thumbnails/
```

---

# 6. Registers

`Content_Orders.csv` columns: Order_ID, Format, Working_Title, Ordered_By, Order_Date, Target_Length, Status, Package_Folder, Notes.

`Published_Content_Register.csv` columns: Item_ID, Publish_Date, Format, Final_Title, URL, Duration, AI_Disclosure, Notes. Rows are added only after real publication (Founder action) — this register is the source of truth for "what is actually live".

---

# 7. Standing Rules

1. No credentials, cookies, tokens, or account recovery data anywhere in this structure — ever.
2. Uploading and publishing are manual Founder actions; nothing in this structure automates them.
3. Analytics files contain real exported/observed numbers or clearly-labeled mock data for testing — never estimates presented as real.
4. AI-generated visuals and narration must be reflected in the item's AI-disclosure review, and YouTube's altered-content disclosure set accordingly at upload.
5. Private PRJ-016 revenue data never enters Media Operations folders (PODS-001 boundary).

---

# Related Documents

- Media_Operations_Package.md (MEDIA-001)
- Video_Workflow_Operating_Process.md (MEDIA-009)
- Content_Factory_Operating_System.md (CFOS-001)
- Atlas_Media_Workflow_and_Schemas (MEDIA-013) — 09_AI_Systems/02_Tools/Media_Tools/

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial production structure standard |
