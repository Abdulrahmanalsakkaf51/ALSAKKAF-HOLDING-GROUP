# ALSAKKAF HOLDING GROUP

# Resume Next Claude Session

> "Read this first. Do not restart the master plan from zero."

---

## Document Information

| Field | Value |
|-------|-------|
| Document Type | Session Handoff / Resume Ledger |
| Status | Active — media rebuild in progress |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |

---

# 1. Verify Before Doing Anything

```
git rev-parse --short HEAD        # expect b990605
git status --short                # expect clean
```

If HEAD is not `b990605` or the tree is not clean, re-verify state before continuing.

---

# 2. Context: The Founder Rejected All 8 Rendered Drafts

On 2026-07-15 the Founder reviewed the 4 ALSAKKAF Systems/رحلة عقل drafts and the 4 Sand Dunes Stories launch drafts and rejected all 8 on **creative** grounds (not technical): artificial generic Piper voice, card/slideshow visuals, weak pacing, and reversed Arabic in the رحلة عقل draft. Full record: **MEDIA-017** (`01_Holding_Company/01_Governance/ALSAKKAF_Media_Creative_Quality_Standard.md`). Read that document first — it defines the quality bar every future render must clear.

Rejected MP4s are archived (SHA-256-verified, not deleted) at `ALSAKKAF MEDIA OPERATIONS\99_REJECTED_DRAFTS\Card_Render_v1\`, marked REJECTED BY FOUNDER — DO NOT PUBLISH. The underlying scripts/canon/timing in each production package remain valid.

---

# 3. What Is Fully Done (commits `42e9c01`..`b990605`)

| Commit | What |
|--------|------|
| `42e9c01` | Atlas daily cycle run; fixed stale ADR-status bug in daily_revenue_briefing.py |
| `8db15b5` | PRJ-017 paper-only backtest engine, 12/12 tests passing |
| `941d2b5` | ALSAKKAF Safety Intelligence feasibility study (STRAT-018), 3 candidates scoped |
| `1a17257` | Sand Dunes Stories bible v1.0 (later corrected — see below) |
| `b990605` | MEDIA-017 quality standard, MEDIA-018 Director's Treatment, MEDIA-015 v2.0 canon correction ("Warrior of the Sand Dunes": Telal=capital city, Amir, Malik the hidden heir, Leila, Sultan Feroos, Zara the seer, Jaber), 8 export records corrected to REJECTED, Arabic renderer root-cause fix |

**Root cause fixed:** `render_videos.py`'s footer text skipped Arabic shaping — reversed/broken text resulted. Fixed in a new tested module, `arabic_render.py` (private `Voice_Engine/`, 15/15 tests passing), which also caught and fixed a silent diacritic-dropping default in `arabic_reshaper`. Visual proof frames are public at `01_Holding_Company/01_Governance/Arabic_Renderer_Evidence/`.

**Sand Dunes Stories (MEDIA-016) is fully scripted** — 3 Shorts (SDS-SRT-001/002/003) + Episode 1 (SDS-VID-001), all with real measured scene timing, storyboards, AI image/video prompts, narration manifests, and captions. Their card-render MP4s are REJECTED (same pipeline issue) but the written creative work is valid and ready for whatever replaces the renderer.

---

# 4. What Is In Progress Right Now

**Chatterbox Multilingual voice install/audition.** Per the Founder's pre-authorization (MEDIA-017 Section 7), installed `chatterbox-tts` (official `resemble-ai/chatterbox`, MIT license, native Arabic+English) in an isolated venv: `ALSAKKAF MEDIA OPERATIONS\03_ATLAS_MEDIA_AUTOMATION\Voice_Engine_v2_Auditions\venv_chatterbox\`. **Important:** this installed CPU-only PyTorch (no CUDA) even though the machine has a 6GB GTX 1660 SUPER — `torch.cuda.is_available()` returned False. Audition generation (`gen_chatterbox_auditions.py`, 4 short clips: AR neutral, AR excited, EN neutral, EN confident) was running in the background (CPU inference, slower) when this session ended — check `ALSAKKAF MEDIA OPERATIONS\00_CONTROL\Founder_Voice_Assets\Abdulrahman\08_Voice_Engine_Auditions\Chatterbox_Multilingual_2026-07-15\` for output; if empty, the run needs to be started again or checked for errors.

If you want GPU acceleration, reinstall torch with a CUDA index (`pip install torch --index-url https://download.pytorch.org/whl/cu121` or current equivalent) inside that same venv before regenerating.

Candidate research record (no other engines installed): `ALSAKKAF MEDIA OPERATIONS\00_CONTROL\Voice_Engine_Candidate_Comparison_2026-07-15.md`. Key finding: **OmniVoice (k2-fsa) is on hold** — its pretrained weights are CC-BY-NC (non-commercial), a real licensing blocker for these commercial channels. OpenVoice V2 has no native Arabic.

---

# 5. What Is Not Started

- **Full editing pipeline rebuild** (MEDIA-017 Section 5): the card/slideshow renderer is retired for final output; no replacement (layers, masks, parallax, kinetic typography, etc.) has been built yet. This is the biggest remaining gap before either proof segment can be produced for real.
- **Proof A (رحلة عقل) and Proof B (ALSAKKAF Systems), 20-30s each**: NOT rendered. See `ALSAKKAF MEDIA OPERATIONS\03_ATLAS_MEDIA_AUTOMATION\Proof_Segments_Feasibility_Assessment_2026-07-15.md` for exactly what's confirmed working (screen capture via ffmpeg gdigrab, window-scoped — **never use `-i desktop` full-screen capture, it recorded unrelated open windows/applications in a feasibility test and that file was deleted**) versus what still needs building (avatar design, animated diagrams, sound design, the layered editing step itself).
  - Recommended Proof B source: the real Atlas Runtime CLI producing a real file, not the public Partner Playground (which is an intentional client-side simulation with "fictional data" by its own design — recording it would still be a simulated output, which conflicts with the Founder's "no fake output" requirement).
- Lane D remainder (TRL-001 analyst chain), Lane E remainder (needs Founder's PRJ-019 scope pick — see below), Sand Dunes rebuild under the new voice/editing standard.

---

# 6. PRJ-019 Safety Intelligence — Scope Note

If a later message corrected this to "construction/industrial HSE intelligence using cameras, environmental data, and Atlas reporting" — check whether that correction was actually applied to STRAT-018 in this repo before assuming it's done; as of `b990605` STRAT-018 still has the original three-candidate (A/B/C) framing from `941d2b5`, not yet corrected to a construction-HSE scope.

---

# 7. Hard Constraints Still In Force

- No email sending, no automatic publishing, no credentials stored, no real-money trading.
- No private leads/voice/video recordings committed to Git.
- Never claim an MP4/voice/screen-recording exists unless actually generated and inspected.
- Any real screen capture must be window-scoped, never full-desktop (see Section 5).
- Do not install or expose OmniVoice for commercial use given its CC-BY-NC weights.
- Do not activate additional Partners or approve additional ADRs without explicit instruction.

---

# 8. Immediate Next Action

Check the Chatterbox audition output folder (Section 4). If clips exist, normalize/compare and report to the Founder for a voice decision. If the folder is still empty, re-run `gen_chatterbox_auditions.py` (consider a shorter test line first to validate the pipeline before the full 4-clip run, given CPU inference speed is unproven on this machine).

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial handoff after Lanes A-C, D core engine, E feasibility study, F foundation |
| 2.0 | 2026-07-15 | Full rewrite after Founder's media creative rejection (MEDIA-017), Sand Dunes canon correction, Arabic renderer fix, and in-progress voice engine rebuild |
