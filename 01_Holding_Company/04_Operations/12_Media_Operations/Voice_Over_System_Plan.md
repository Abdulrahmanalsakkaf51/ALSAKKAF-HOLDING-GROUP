# ALSAKKAF HOLDING GROUP

# Voice-Over System Plan

> "The voice is the channel's signature. We choose it deliberately — and legally."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-014 |
| Document Type | Voice-Over System Plan (plan only — nothing installed) |
| Status | Draft — awaiting Founder decision |
| Version | 1.0 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-013, MEDIA-003, MEDIA-012 |

---

# 1. Purpose and Boundaries

Two supported narration paths are planned. Nothing in this document installs software, downloads models, or records anyone. Explicitly forbidden: using any third party's voice, storing voice samples in the public repository, and any installation before a separate Founder go-ahead.

- PATH A — Generic local/offline TTS: fast production without recording every line.
- PATH B — Founder-consented voice cloning: only Abdulrahman's own voice, with an explicit written consent record.

Important dating note: the assessments below are from documented knowledge as of early 2026, gathered without network access. Licenses and project status MUST be re-verified on the official repositories on the day of any install decision (that verification is itself a Founder-approved network action).

---

# 2. Option Comparison

| Dimension | Piper (and successor) | Coqui XTTS v2 | F5-TTS | OpenVoice V2 |
|-----------|------------------------|----------------|--------|--------------|
| Project / source | rhasspy/piper; active successor repo (piper1-gpl under OHF-Voice) — verify current home | coqui-ai/TTS — company shut down Jan 2024; community forks (e.g. Idiap coqui-ai fork) | SWivid/F5-TTS | myshell-ai/OpenVoice (V2) + MeloTTS |
| License — code | MIT (original); successor GPL-3.0 — verify | MPL-2.0 | MIT | MIT (V2) |
| License — model weights | Per-voice licenses, mostly permissive — check each voice | Coqui Public Model License: NON-COMMERCIAL — a blocker for monetized channel content | Base checkpoints trained on Emilia data, released CC-BY-NC — NON-COMMERCIAL | MIT (V2) — commercial allowed |
| Commercial use for our videos | Generally yes (verify per voice model) | NO under CPML — do not use for channel content | NO for base weights | Yes |
| Windows install difficulty | Easy (pip / standalone binaries) | Moderate-hard (torch stack; aging package) | Moderate (torch + GPU strongly advised) | Moderate |
| Arabic support | Weak — few Arabic voices, robotic quality, diacritics (tashkeel) problem | Yes — among the best open Arabic cloning of its generation | Not in base model (EN/ZH); community Arabic finetunes exist, unverified quality and unclear licenses | No — MeloTTS has no Arabic |
| English support | Good | Good | Very good | Good |
| CPU/GPU needs | CPU real-time — lightest option | GPU strongly recommended; CPU is painfully slow | GPU effectively required | GPU recommended |
| Speed | Fastest | Slow without GPU | Slow without GPU | Moderate |
| Privacy | Fully local | Fully local | Fully local | Fully local |
| Quality risks | Flat/robotic long-form narration; fine for drafts | License risk outweighs quality; project unmaintained | Very natural EN; Arabic path unproven | Tone cloning good, but no Arabic ends it for رحلة عقل |
| Maintenance risk | Low-medium (active successor) | High (abandoned upstream) | Medium (research-grade) | Medium |
| Recommended use | Scratch narration + timing tracks; possible English utility voice | Not recommended (license) | Watch-list for future EN cloning if commercially-licensed weights appear | English tone cloning candidate, PATH B, English only |

---

# 3. Honest First Recommendation

1. Fastest workable option for the first videos: the Founder records his own narration (PATH B without any cloning — zero install, zero license risk, and it matches the رحلة عقل promise of "صوت عربي أصيل"). SYS-VID-001 is 90 seconds and RA-VID-001 is ~5 minutes of narration — under an hour of recording total including retakes.
2. Best long-term local Atlas option: Piper (or its maintained successor) as the local utility TTS for scratch tracks, timing drafts, and internal tooling — with the successor's GPL license reviewed at install time. For final published narration, Founder voice remains the standard until a commercially-licensed Arabic cloning option with real quality exists.
3. Fallback if Arabic cloning quality is weak (it currently is, in the open-source commercial-safe space): permanent fallback is Founder-recorded Arabic. For English only, OpenVoice V2 (MIT) is the legitimate cloning candidate using the Founder's consented sample.
4. What we will NOT do: use XTTS v2 or F5-TTS base weights for monetized channel content while their weights are non-commercial; use anyone else's voice; put voice samples in the public repository.

---

# 4. Founder Recording Specification (prepare now, record when ready)

| Item | Specification |
|------|---------------|
| Total material | 10-15 minutes of clean speech preferred (minimum 5) |
| Room | Quiet room, soft furnishings, no fan/AC hum, phone silenced |
| Format | WAV preferred, 48 kHz, 24-bit, mono |
| Microphone | Any decent mic held/mounted at a consistent 15-20 cm, slightly off-axis; record 10 seconds of room silence first |
| Delivery | Natural storytelling pace — not reading-flat, not performing |
| Content | Arabic samples: read 2-3 minutes of the RA-VID-001 script + free speech about any topic. English samples: read 2-3 minutes of the SYS-VID-001 script + free speech |
| Test sentences (AR) | "رحلة عقل — رحلة في العلم والفكر والتاريخ." / "سنة ألف وتسعمئة واثني عشر، لاحظ ألفريد فيغنر شيئًا غريبًا." / "الطبيعة لا تجامل أحدًا." |
| Test sentences (EN) | "AI drafts. Humans decide." / "This is an AI Partner — a role with a written job description." / "Welcome to ALSAKKAF Systems." |
| Consent record | A signed dated note: "I, Abdulrahman Alsakkaf, consent to the use of these recordings of my own voice to build a narration voice used only for ALSAKKAF HOLDING GROUP content under my approval." Stored with the samples |
| Storage | PRIVATE operational storage only, per PODS-001 pattern: `ALSAKKAF PRIVATE OPERATIONS/03_Media_Private/Voice_Samples/` — never in the public repository |

---

# 5. Decision Gate

| Decision | Owner | Status |
|----------|-------|--------|
| Approve PATH A tool (Piper/successor) install for scratch narration | Founder + CTO | PENDING — requires separate install approval |
| Record Founder voice samples per Section 4 | Founder | PENDING |
| Approve any PATH B cloning experiment (English, OpenVoice V2) | Founder + CTO | PENDING — only after samples + consent exist |
| Any Arabic cloning adoption | Founder + CTO | PENDING — blocked on a commercially-licensed, quality-verified option |

---

# Related Documents

- Atlas_Media_Production_Workflow.md (MEDIA-013)
- Channel_Identity.md رحلة عقل (MEDIA-003)
- 01_Holding_Company/01_Governance/Private_Operational_Data_Standard.md (PODS-001)

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial voice-over system plan — comparison, recommendation, recording spec; nothing installed |
