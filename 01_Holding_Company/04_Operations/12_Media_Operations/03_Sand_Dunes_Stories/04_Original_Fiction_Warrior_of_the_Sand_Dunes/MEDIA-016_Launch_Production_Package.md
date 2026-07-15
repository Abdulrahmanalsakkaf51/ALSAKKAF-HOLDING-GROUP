# ALSAKKAF HOLDING GROUP

# Sand Dunes Stories — "Warrior of the Sand Dunes" Launch Production Package

> "Original Fiction — Sand Dunes Stories."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-016 |
| Document Type | Media Production Package (launch package, 4 items) |
| Status | REJECTED — MAJOR CREATIVE REBUILD REQUIRED (creative rejection of the card-render pipeline + generic Piper voice; scripts/canon remain valid — see MEDIA-017) |
| Version | 1.0 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-015 (Character and World Bible, v2.0), MEDIA-004 (Channel Identity), MEDIA-007 (Content Plan) |

---

# 1. Package Contents

| # | Item ID | Title | Format | Measured duration | Status |
|---|---------|-------|--------|--------------------|--------|
| 1 | SDS-SRT-001 | The Night Telal Fell | Short (vertical 1080x1920) | 31.1s | REJECTED — creative rebuild required |
| 2 | SDS-SRT-002 | The Secret Potion | Short (vertical 1080x1920) | 30.7s | REJECTED — creative rebuild required |
| 3 | SDS-SRT-003 | Zara's Prophecy | Short (vertical 1080x1920) | 25.0s | REJECTED — creative rebuild required |
| 4 | SDS-VID-001 | Episode 1: The Fall of Telal | Long-form (landscape 1920x1080) | 4:08.8 (248.8s) | REJECTED — creative rebuild required |

**Founder creative rejection (2026-07-15):** all four used GENERIC Piper narration and the card-style slideshow renderer that the Founder rejected on creative grounds for the ALSAKKAF Systems and رحلة عقل drafts (artificial voice, slideshow presentation, weak pacing). This package inherits the same rejection — it is not exempt. All four MP4s were archived to `99_REJECTED_DRAFTS\Card_Render_v1\` in private storage, marked REJECTED BY FOUNDER — DO NOT PUBLISH, not deleted. The scripts, canon, and scene timing in each item's `02_Script.md` remain valid creative work; only the render and voice need to be rebuilt, per MEDIA-017 (ALSAKKAF Media Creative Quality Standard) — Sand Dunes Stories needs its own cinematic story-film standard, not the card renderer.

---

# 2. Canon Compliance

All four scripts were written against MEDIA-015 v2.0 (corrected Founder canon: "Warrior of the Sand Dunes," Telal as capital city, Amir/Malik/Leila/Sultan Feroos/Zara/Jaber). None reference the incorrect v1.0 invented universe. Open items flagged in MEDIA-015 Section 4 (the King's name, Jaber's specific role, Amir/Malik's relationship dynamic, the potion's mechanical nature) were deliberately left unresolved in these scripts rather than invented.

---

# 3. Per-Item Production Folders

Each item has its own folder under `Production/` with the same structure used for the ALSAKKAF Systems and رحلة عقل channels:

- `01_Content_Order_and_Research.md` — content order, target duration, canon-continuity check
- `02_Script.md` — final narration/dialogue, exact scene timing (measured, not estimated), storyboard beats
- `03_Production_Plan.md` — character appearance guide reference, location guide reference, asset manifest, AI image prompts, AI video prompts, narration manifest, sound and music plan, AI-disclosure recommendation, Founder approval gate
- `04_Upload_Package.md` — title, description, keywords, thumbnail concept, inspection summary
- `Captions_EN.srt` — real captions with per-line timestamps measured from the actual synthesized narration audio (not estimated)

---

# 4. Technical Inspection Summary

All four MP4s were rendered via the same card-render pipeline used for the ALSAKKAF Systems / رحلة عقل first videos (`render_videos.py`, reused via `gen_and_render_sand_dunes.py`), and inspected the same way: ffprobe stream/format check (codec, resolution, duration) plus a mid-timestamp frame extraction with luminance check to rule out a blank render (blank if mean < 2 or > 253). All four passed. Full results are in each item's `04_Upload_Package.md` and in the private `Video_Render_Inspection_Report` alongside the other channels' reports.

MP4s themselves stay in private Media Operations storage (`ALSAKKAF MEDIA OPERATIONS\04_SAND_DUNES_STORIES\05_Exports\`) per PODS-001 — the public repository holds scripts, plans, and captions, not rendered video files.

---

# 5. Publishing Gate

Nothing in this package is published, scheduled, or uploaded. Every item requires Founder listening/viewing approval first (see each item's Founder Approval Gate in `03_Production_Plan.md`).

---

# Related Documents

- Character_and_World_Bible.md (MEDIA-015, v2.0)
- Channel_Identity.md (MEDIA-004)
- Content_Plan_First_Videos_and_Shorts.md (MEDIA-007)

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial launch production package: 3 Shorts + Episode 1 scripted, rendered as card-style drafts, and technically inspected |
