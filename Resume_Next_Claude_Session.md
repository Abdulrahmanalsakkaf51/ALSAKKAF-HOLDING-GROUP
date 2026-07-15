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
git rev-parse --short HEAD        # expect ed917c3
git status --short                # expect clean
```

If HEAD is not `ed917c3` or the tree is not clean, re-verify state before continuing.

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

# 4. Chatterbox Voice Audition — Founder Voice APPROVED FOR CONTROLLED PRODUCTION USE

Update (2026-07-15, later same day): the Founder listened to and approved
all four generic auditions below as the engine direction, then approved
all four **Founder-voice-clone** auditions (Chatterbox's audio-prompt
cloning workflow using Abdulrahman Alsakkaf's own private reference
clips). Status recorded at
`ALSAKKAF MEDIA OPERATIONS\00_CONTROL\Founder_Voice_Assets\Abdulrahman\Voice_Approval_Status.md`:
**APPROVED FOR CONTROLLED PRODUCTION USE** for ALSAKKAF Systems narration,
رحلة عقل narration, and Founder-approved internal demonstrations. 48kHz/
24-bit production copies exist at
`09_Founder_Clone_Auditions\Chatterbox_Founder_Clone_2026-07-15\*_48K.wav`.
Two 20-30s premium proof segments were then built using this voice - see
Section 5 below, which replaces the "not started" status this section
previously carried.

Original generic-audition record, preserved below for history:

Per the Founder's pre-authorization (MEDIA-017 Section 7), installed `chatterbox-tts` (official `resemble-ai/chatterbox`, MIT license, native Arabic+English) in an isolated venv: `ALSAKKAF MEDIA OPERATIONS\03_ATLAS_MEDIA_AUTOMATION\Voice_Engine_v2_Auditions\venv_chatterbox\`.

Hit and fixed a real bug along the way: `resemble-perth`'s watermarker failed to import (`pkg_resources` missing under setuptools 83) — fixed by pinning `setuptools<81` in that venv.

**All 4 auditions generated and technically verified** (real duration, no clipping, normal speech silence ratios) at `ALSAKKAF MEDIA OPERATIONS\00_CONTROL\Founder_Voice_Assets\Abdulrahman\08_Voice_Engine_Auditions\Chatterbox_Multilingual_2026-07-15\`:
- AR_neutral (6.2s), AR_excited_storytelling (7.2s), EN_neutral (7.4s), EN_confident_product_demo (4.7s) — all normalized to -16 LUFS
- **One caveat to listen for:** the generator logged a repetition/long-tail warning on AR_excited_storytelling that forced an early stop — check that clip for a possible cutoff or repeated word before treating it as representative.
- This ran on CPU only — `torch.cuda.is_available()` returned False even though the machine has a 6GB GTX 1660 SUPER (default pip install pulls CPU-only torch). Fine for short auditions; reinstall with a CUDA index before any larger-scale generation if speed matters.

Next: Founder listens and picks a winner (or requests OpenVoice V2 installed for comparison) before any full narration is generated.

Candidate research record (no other engines installed): `ALSAKKAF MEDIA OPERATIONS\00_CONTROL\Voice_Engine_Candidate_Comparison_2026-07-15.md`. Key finding: **OmniVoice (k2-fsa) is on hold** — its pretrained weights are CC-BY-NC (non-commercial), a real licensing blocker for these commercial channels. OpenVoice V2 has no native Arabic.

---

# 5. Proof Segments — BUILT, then REJECTED BY FOUNDER (creative grounds)

**Update (2026-07-15, end of day): both proofs were rejected by the
Founder on creative grounds.** Both MP4s are preserved (not deleted),
renamed with a `REJECTED_` prefix, and marked
`REJECTED — PIPELINE TEST ONLY — DO NOT PUBLISH` in their filenames, QC
reports, production packages, and a `REJECTED_BY_FOUNDER_DO_NOT_PUBLISH.txt`
marker (with SHA-256) in each output folder:

- `Proof_Pipeline\Proof_A_Output\REJECTED_SDS_PROOF_A_Rihlat_Aql_1080x1920.mp4`
- `Proof_Pipeline\Proof_B_Output\REJECTED_SYS_PROOF_B_ALSAKKAF_Systems_1920x1080.mp4`

**Not rejected / still valid:** the approved scripts (MEDIA-001/MEDIA-002),
Founder voice approval (still APPROVED FOR CONTROLLED PRODUCTION USE -
see Section 4), the tested Arabic renderer, both narration WAVs, and the
real Atlas workflow evidence (`Daily_Briefing_2026-07-15.md`). Only the
proof videos' creative output was rejected - the pipeline itself proved
technically sound (see each `Proof_*_Output\*_QC_Report.md`).

**The Media Studio rebuild (a proper layered editor / illustration
pipeline that could clear the creative bar) is explicitly NOT started.**
Per the Founder's end-of-day instruction, do not start it without a new
task. See Section 8 for the exact first task tomorrow.

Original build record, preserved below for history:

Update (2026-07-15): a real layered edit pipeline was built (procedural
per-frame PIL rendering + ffmpeg encode/mux, not the retired card
renderer) at `ALSAKKAF MEDIA OPERATIONS\03_ATLAS_MEDIA_AUTOMATION\Proof_Pipeline\`.
Both proofs are built, technically QC'd (ffprobe, blackdetect, audio
peak/clipping - all clean), and use the approved Founder-clone narration:

- **Proof A (رحلة عقل)**, 1080x1920, 17.56s: `Proof_Pipeline\Proof_A_Output\SDS_PROOF_A_Rihlat_Aql_1080x1920.mp4`
- **Proof B (ALSAKKAF Systems)**, 1920x1080, 26.52s: `Proof_Pipeline\Proof_B_Output\SYS_PROOF_B_ALSAKKAF_Systems_1920x1080.mp4`

**Two real, honestly-documented gaps, not hidden:**
1. No AI image-generation tool exists in this environment - visuals are
   original procedural motion graphics (gradients, flat shapes, kinetic
   type), not painterly/photorealistic illustration. This is the main
   remaining gap before either proof reads as truly "premium illustrated."
2. **Real window-scoped screen recording was attempted for Proof B and
   technically failed** - `ffmpeg gdigrab` located the target window with
   no error but returned a solid-black frame; this session has no actual
   rendered desktop surface to capture pixels from (confirmed by direct
   frame inspection, not assumed). See
   `Proof_Pipeline\Proof_B_Output\Proof_B_Screen_Recording_Plan.md` for
   the full finding and the one manual action that would resolve it (the
   Founder recording their own screen running `atlas.py brief` and
   handing over the clip).
3. Also flagged: a `long_tail` early-EOS warning on Proof A's narration
   and a more serious `token_repetition` warning on Proof B's narration -
   both need a careful Founder listen before full production use (see
   each proof's QC report).

Full deliverables (Director's treatment, narration text, shot timeline,
asset manifest, music/SFX register, SRT, EDL, thumbnail concept, creative
+ technical QC) are in each `Proof_*_Output\` folder as markdown files.
No music/SFX bed exists yet in either proof (no licensed library
available) - narration only.

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

# 8. Immediate Next Action (as of end of day 2026-07-15)

**Exact first task for tomorrow:** do NOT start the Media Studio rebuild
or any new rendering without the Founder explicitly requesting it. Wait
for direction on one of:
(a) a decision on how to close the illustration gap (approved
AI image-generation tool vs. commissioned/licensed illustration assets)
before attempting a new creative pass, or
(b) the Founder's own screen recording of `atlas.py brief` (see
`Proof_Pipeline\Proof_B_Output\Proof_B_Screen_Recording_Plan.md` for the
exact single action needed), or
(c) a different priority entirely (PRJ-019 scope correction, Sand Dunes
rebuild, Lane D/E work - see Sections 6 and 3).

Do not re-attempt a third proof segment on the same rejected creative
approach without new creative direction from the Founder.

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial handoff after Lanes A-C, D core engine, E feasibility study, F foundation |
| 2.0 | 2026-07-15 | Full rewrite after Founder's media creative rejection (MEDIA-017), Sand Dunes canon correction, Arabic renderer fix, and in-progress voice engine rebuild |
| 3.0 | 2026-07-15 | End-of-day checkpoint: Founder voice (Chatterbox clone) APPROVED FOR CONTROLLED PRODUCTION USE; two 20-30s proof segments built, technically QC'd, then REJECTED BY FOUNDER on creative grounds and marked/preserved; Media Studio rebuild explicitly not started |
