# ALSAKKAF HOLDING GROUP

# Atlas Media Production Workflow

> "The pipeline drafts. The Founder publishes. The report never guesses."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-013 |
| Document Type | Media Workflow and Reporting Standard |
| Status | Draft — awaiting Founder review |
| Version | 1.0 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-011, MEDIA-012, MEDIA-014, CFOS-001 |

---

# 1. Purpose

This standard documents the Atlas media production pipeline, its record schemas, its safety boundaries, and the daily and weekly report formats. The executable scaffold lives in `09_AI_Systems/02_Tools/Media_Tools/` (`media_schemas.py`, `media_workflow.py`) with its own test suite.

---

# 2. Pipeline Stages

```text
Content Order -> Research -> Script Validation -> Scene Plan
-> Asset Manifest -> Visual Generation Queue -> Narration Queue
-> Edit Manifest -> Captions -> Thumbnail Brief -> Upload Package
-> FOUNDER APPROVAL -> MANUAL UPLOAD/PUBLISH (Founder only)
-> Metrics Collection -> Daily and Weekly Reports
```

Rules enforced by the scaffold and its tests:

1. Stages cannot be skipped.
2. Founder Approval and Manual Upload/Publish are human-only stages — the scaffold rejects any non-Founder actor.
3. Publish cannot occur without `founder_approved = True`.
4. The scaffold has no upload, network, or authentication capability at all; the test suite scans the source for forbidden capability tokens.
5. Metrics enter only as `mock` (labeled test data) or `manual_export` (real numbers the Founder provides). Future API integration requires a separate Founder approval and must use OAuth — never account passwords, passkeys, 2FA codes, or recovery codes.

---

# 3. The Ten Record Schemas

| Schema | Purpose |
|--------|---------|
| media_order | A content order: what, for which channel, ordered by whom |
| content_status | Where an item is in the pipeline, its blockers, its approval flag |
| asset_manifest_entry | Every visual/audio asset with rights and AI-prompt logging |
| narration_manifest_entry | Every narration line, voice path, and consent flag |
| edit_manifest | Project file, duration, music licenses, captions, human inspector |
| upload_package | Final metadata, AI disclosure, Founder approval flag and date |
| video_record | What was actually published, by a human, with URL and date |
| channel_metrics_snapshot | Measured audience numbers per channel per date |
| daily_media_report | Production status + daily metrics |
| weekly_founder_media_report | The weekly Founder media report |

Honest-value semantics apply to every metric field: a value is a measured integer, a real zero, or the literal `unavailable`. Estimates are rejected by the validator. Revenue is `unavailable` until it is genuinely available.

---

# 4. Daily Media Report Format

Produced each working day (rendered by `media_workflow.render_daily_report`):

```text
ATLAS DAILY MEDIA REPORT - [date]
Data source: [mock | manual_export]

In production: [item @ stage, ...]
Blockers: [...]
Videos published today: [n]
Views delta: [n | unavailable]
Subscribers delta: [n | unavailable]
Comments requiring attention: [n | unavailable]
```

---

# 5. Weekly Founder Media Report Format

Produced every Saturday (rendered by `media_workflow.render_weekly_report`), covering: uploads, Shorts, total views, watch time, subscribers gained/lost, top video, retention observations, traffic sources when available, website clicks when measurable, estimated revenue only when genuinely available (otherwise `unavailable`), and next-seven-day recommendations. The narrative wrapper follows MEDIA-011.

---

# 6. Current Honest Status

| Component | Works today | Still manual / future |
|-----------|-------------|------------------------|
| Pipeline state machine + gates | Yes — tested | — |
| Schema validation, honest-value rules | Yes — tested | — |
| Daily/weekly report rendering | Yes — from records provided | Numbers must be typed in from YouTube Studio until an approved OAuth integration exists |
| Metrics collection | Mock + manual entry only | YouTube API (OAuth) requires separate Founder approval |
| Visual/narration generation | Prompt and manifest records only | Actual generation and editing are manual tool work |
| Upload/publish | Never automated | Founder-only, by design — permanent |

---

# Related Documents

- 09_AI_Systems/02_Tools/Media_Tools/media_schemas.py
- 09_AI_Systems/02_Tools/Media_Tools/media_workflow.py
- 09_AI_Systems/02_Tools/Media_Tools/test_media_workflow.py
- Atlas_YouTube_Reporting_Template.md (MEDIA-011)
- Media_Production_Structure.md (MEDIA-012)

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial workflow and reporting standard |
