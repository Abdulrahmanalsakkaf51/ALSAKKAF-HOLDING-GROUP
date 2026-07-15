# ALSAKKAF HOLDING GROUP

# ALSAKKAF Media Creative Quality Standard

> "It passed the technical check. It failed the creative one. Both matter."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-017 |
| Document Type | Governance Standard |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-013, MEDIA-014, MEDIA-016, PODS-001 |

---

# 1. Purpose

On 2026-07-15 the Founder reviewed the four rendered draft MP4s produced under MEDIA-013/MEDIA-014's pipeline (SYS-VID-001, SYS-SRT-001, RA-VID-001, RA-SRT-001) plus the four Sand Dunes Stories launch drafts (MEDIA-016) and rejected all eight on creative grounds. This standard records that decision and the quality bar every future media render must meet before it is even offered for Founder review.

**This was not a technical failure.** All eight passed ffprobe stream/format checks and the mid-frame blank-render check. They failed because the render pipeline itself — a card/slideshow renderer with generic synthetic narration — does not produce work worth publishing under the ALSAKKAF Systems or رحلة عقل or Sand Dunes Stories names.

---

# 2. Founder Rejection Record (2026-07-15)

| Dimension | Verdict | Detail |
|-----------|---------|--------|
| Voice | REJECTED | Generic Piper narration sounds artificial and unacceptable for any public-facing video |
| Visuals | REJECTED | Card/slideshow presentation, weak AI-looking imagery, minimal real editing |
| Pacing | REJECTED | Too slow and visually inactive |
| Arabic | REJECTED | Reversed Arabic appeared in the رحلة عقل draft — release-blocking |
| Overall | NOT AN APPROVED DRAFT | Major rebuild required across voice, visuals, editing, and Arabic rendering |

All eight affected export records (MEDIA-013's SYS-VID-001/SYS-SRT-001, MEDIA-014's RA-VID-001/RA-SRT-001, and MEDIA-016's SDS-SRT-001/002/003 and SDS-VID-001) have had their status corrected from "pending review" to **REJECTED — MAJOR CREATIVE REBUILD REQUIRED**. The eight rendered MP4s were archived (SHA-256-verified, not deleted) to `ALSAKKAF MEDIA OPERATIONS\99_REJECTED_DRAFTS\Card_Render_v1\` in private storage, each marked REJECTED BY FOUNDER — DO NOT PUBLISH.

Scripts, canon, storyboards, and measured scene timing in the underlying production packages are **not** rejected — only the render pipeline and narration voice. That written creative work remains valid and is the starting point for the rebuild.

---

# 3. Root Cause: The Reversed-Arabic Defect

Diagnosed by extracting and visually inspecting a frame from the rejected RA-VID-001 draft. The main title and body text rendered correctly (properly shaped and right-to-left ordered); only the footer branding text ("رحلة عقل - DRAFT") was reversed and visually broken, reading as "لقع ةلحر - DRAFT".

**Root cause:** `render_videos.py`'s `make_card()` function drew the footer text directly with PIL's `draw.text()`, without ever calling the existing `shape()` helper that the title/body text correctly used. PIL performs no Arabic contextual joining or bidi reordering on its own — an unshaped logical-order string drawn character-by-character is exactly what produces this reversed, disconnected appearance.

**Fix:** a new, single, tested module (`arabic_render.py`, in the private Voice_Engine folder alongside the existing render tooling) is now the one place Arabic text is shaped and rendered, so this exact bug class — a text field that skips shaping — cannot recur silently. See Section 6.

A second, independent defect was found while building the fix: `arabic_reshaper`'s default configuration silently drops diacritics (tashkeel) such as the shadda in "حرّك" — fixed by explicitly configuring `delete_harakat: False`.

---

# 4. Channel-Specific Quality Rules

## 4.1 رحلة عقل

- Premium Arabic illustrated-documentary style
- New information every 1.5–3.5 seconds
- 20–30 distinct visual beats per minute
- No unchanged background held for more than 8 seconds
- Use maps, scientific diagrams, source cards, cutout animation, and visual metaphors — original art direction, not stock imagery
- Maximum two subtitle lines on screen at once
- Phone-readable Arabic (large enough, high contrast, correct shaping — enforced by `arabic_render.py`)

## 4.2 ALSAKKAF Systems

- Premium product-film standard, not a slideshow
- Real screen recording of the actual system (alsakkafsystems.com, Partner Playground) — no invented UI
- Demonstrate a real automation workflow and a real output (an actual XLSX, DOCX, briefing, or tracker file)
- Show the human-approval gate explicitly — this is the product's core claim and must be visible, not asserted in narration alone
- Dynamic UI motion: callouts, zooms, masks, cursor emphasis, data-flow overlays
- No generic robot imagery, no fake dashboard, no fake customer result

## 4.3 Sand Dunes Stories

- Needs its own cinematic story-film standard, distinct from both channels above
- Must not use the card/slideshow renderer described in Section 5 as a final output — that pipeline is retired for finished work
- Original cinematic desert-fantasy visuals; no imitation of any copyrighted animation studio's house style; no copyrighted music or footage

---

# 5. Editing System Requirements — No More Slideshow Renderer

`render_videos.py`'s card-style output must not be used as a final renderer going forward. Any revised or replacement production pipeline must support:

- Layered assets, masks, and reveals
- Parallax
- Animated maps and diagrams
- Screen recordings
- Cursor emphasis
- Kinetic typography
- Motion blur where appropriate
- Speed ramps
- Audio ducking
- Transitions
- Sound effects
- Compositing
- Shot-level timing
- Reusable branded motion templates

Local, free tools already available (or officially licensed free installations, after a license review) are to be used. A simple FFmpeg assembly step is allowed, but it must follow a real edit decision list with multiple layers and cuts — not a sequence of static cards.

---

# 6. Arabic Rendering Requirement

A reusable Arabic-title/subtitle renderer is required for every future Arabic render. Implemented at `ALSAKKAF MEDIA OPERATIONS\03_ATLAS_MEDIA_AUTOMATION\Voice_Engine\arabic_render.py`, with tests at `test_arabic_render.py` (15/15 passing). Requirements met:

| Requirement | How it's met |
|--------------|--------------|
| Correct RTL shaping | `arabic_reshaper` (contextual joining) + `python-bidi` (UAX#9 reordering), applied via one `shape_arabic()` function |
| Unicode-safe UTF-8 | Native Python 3 str handling throughout; no byte-level string ops |
| Verified shaping engine, not raw unshaped drawtext | Never uses FFmpeg drawtext; PIL drawing only after `shape_arabic()` |
| Transparent PNG/video overlays | `render_arabic_overlay()` returns an RGBA image with a transparent background |
| Automated source checks | `test_module_source_never_calls_draw_text_with_unshaped_arabic` scans the module's own source for the one permitted draw call |
| Visual test frames | Generated for all three Founder-specified validation strings, saved to `arabic_render_test_frames/`, plus a before/after comparison recreating the exact footer bug |
| Logical character order (source) | Tested — source constants stay in typed logical order |
| Correct displayed order | Tested — verified empirically that displayed order equals the reversed shaped form for these pure-RTL strings, then asserted |
| No mojibake | Tested at every stage (input, reshaped, displayed) |
| No disconnected letters | Tested via presentation-form codepoint range check |
| Line wrapping | Tested — forces multiple lines when narrow, single line when wide, word-preserving |
| Subtitle safe area | Tested — text bounding boxes stay within a configurable safe margin |

---

# 7. Voice Requirement

Generic Piper narration is rejected for any public-facing video. Piper may remain as an **internal timing tool only** (e.g., to measure realistic per-line durations for scene planning) — never as the voice in a published or Founder-reviewed-as-final video.

Candidate replacement engines under research (not yet installed — see the companion voice-engine candidate comparison record): Chatterbox Multilingual, OmniVoice, OpenVoice V2. Any installation must be isolated to Media Operations, use only officially-sourced repositories and license-verified model weights, and never expose a public endpoint or upload the Founder's voice anywhere.

---

# 8. Proof-Before-Full-Production Rule

No full video may be rendered under the old standard again. Before any full video is produced under a rebuilt pipeline, a short (20-30 second) proof segment must be produced and pass both a creative QC checklist and a technical QC checklist. Only after Founder proof approval does full-length production proceed.

---

# 9. Publishing Gate (unchanged, reaffirmed)

No video may be published, scheduled, or uploaded under any circumstance covered by this standard without explicit Founder approval, regardless of technical or creative QC status.

---

# Related Documents

- MEDIA-013 (Atlas Media Production Workflow)
- MEDIA-014 (Voice-Over System Plan)
- MEDIA-016 (Sand Dunes Stories Launch Production Package)
- Private_Operational_Data_Standard.md (PODS-001)
- arabic_render.py / test_arabic_render.py (private Voice_Engine)

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial standard, recording the Founder's full creative rejection of the card-render pipeline and the resulting rebuild requirements |
