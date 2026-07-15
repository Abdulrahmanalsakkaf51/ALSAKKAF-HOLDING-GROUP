# ALSAKKAF HOLDING GROUP

# Higgsfield AI Visual Support Package

> "One AI-generated clip is a test, not a video."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-019 |
| Document Type | Media Operations Support Package |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-16 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |
| Related Documents | MEDIA-012, MEDIA-015, MEDIA-017, PODS-001 |

---

# 0. What This Is and Isn't

The Founder generates Higgsfield images/video manually on the Higgsfield website (unlimited-generation mode is website-only). **This package does not generate, submit, or install anything.** It exists so every Higgsfield trial the Founder runs gets tested, logged, and scored the same disciplined way — instead of loose files with no record.

**Standing rule, no exceptions:** no single AI-generated image or clip is ever a finished video or a launch-ready asset. It is raw material, subject to the same creative bar the Founder already set in MEDIA-017 after rejecting the first full render pipeline. A Higgsfield still that looks good is a candidate for the next production stage, not a publish-ready deliverable.

---

# 1. Five-Test Prompt Library

Each prompt below is written to satisfy the channel-specific quality rules already set in **MEDIA-017 Section 4** — not generic prompt-writing. Read that section before using any prompt here. Every prompt is a starting point the Founder edits before generating, not a literal paste.

## 1.1 NESTLYRA — Commercial Product Image

**Context:** Today's Test 01 (Wardrobe) and Test 02 (Unlimited Bedroom Closet) were both scored "reference asset only" — Test 02 specifically flagged as **still weak product focus, not clear enough for direct e-commerce conversion** (see the private NESTLYRA generation log). This prompt is written to directly counter that weakness.

```text
A single [PRODUCT NAME — e.g., vacuum-sealed storage bag / drawer divider set]
as the clear hero subject, filling 40-60% of the frame, in sharp focus,
placed inside a calm, minimalist, small-space wardrobe/closet setting.
Soft, even, premium natural light. Neutral, uncluttered background —
no competing objects. Composition reads instantly as a product photo,
not a lifestyle scene the product is buried inside. Muted, calm color
palette (warm neutrals, soft whites). No text, no logos, no invented
brand marks baked into the image.
```

**Why:** addresses the exact Test 02 gap — product must be the unmistakable subject, not an ambient detail in a room shot.

## 1.2 NESTLYRA — Product / Ad Video (short motion test)

```text
Subtle, slow camera motion only — a gentle push-in or soft pan across
the hero product from 1.1, product remaining in sharp focus throughout.
No fast cuts, no dramatic camera moves, no invented on-screen text.
Calm, premium pacing consistent with a small-space home-organization
brand — motion should feel like a still photo that breathes, not an
action clip.
```

**Why:** matches NESTLYRA's calm-minimalist positioning (see `01_Holding_Company/04_Operations/14_NESTLYRA_Store/13_Collection_Calm_Wardrobe.md`) — fast or busy motion would contradict the brand's own copy.

## 1.3 رحلة عقل — Science Visual

**Context:** MEDIA-017 §4.1 requires: illustrated-documentary style, maps/diagrams/cutout animation/visual metaphors, original art direction — explicitly **not stock imagery**, and no unchanged background held more than 8 seconds in the final edit.

```text
Original illustrated-documentary style diagram/visual metaphor
explaining [SPECIFIC SCIENTIFIC CONCEPT FROM THE SCRIPT — pull from the
episode's 02_Script.md, do not invent a concept]. Editorial-illustration
style, not photorealistic, not stock-photo style. Rich but limited color
palette, clear visual hierarchy, works as a single explanatory frame.
No text baked into the image — captions and labels are added separately
via the tested Arabic-rendering pipeline (arabic_render.py), never
generated as image text.
```

**Why the no-baked-text rule matters:** MEDIA-017 §3 documented a release-blocking reversed-Arabic bug from text drawn without proper shaping. Any Arabic (or English) label must go through the existing tested `shape_arabic()` pipeline as a separate overlay — never trust an AI image generator to render correct Arabic typography.

## 1.4 Sand Dunes Stories — Telal (the City) Cinematic Visual

**Correction before use:** per the Character and World Bible (MEDIA-015), **Telal is the capital city of the desert kingdom, not a character.** Do not generate a character portrait and label it "Telal." Pull any character appearance details (Zara, Amir, Malik, Leila, Sultan Feroos) from MEDIA-015 directly — never invent physical descriptions here.

```text
Wide cinematic establishing shot of Telal, a desert kingdom's capital
city — original fantasy architecture consistent with a fallen/betrayed
royal city, sandstone and desert-toned palette, dramatic but not
photorealistic lighting (illustrated-cinematic, not a real-world photo
style). No recognizable real-world landmark. No visual resemblance to
any existing copyrighted animated-film city or studio house style
(MEDIA-017 §4.3 — this is a hard requirement, not a preference).
```

**Why:** this is an establishing/world-building shot, not a character asset — matches what "cinematic visual" actually means for this series per its own bible.

## 1.5 ALSAKKAF Systems — Product-Film Visual

**Hard constraint — read before using this prompt:** MEDIA-017 §4.2 requires the ALSAKKAF Systems channel to use **real screen recordings** of the actual system (alsakkafsystems.com, Partner Playground) as the product demonstration — "no invented UI," "no fake dashboard." A Higgsfield-generated image must never be used as a stand-in for that real screen recording. This prompt is scoped only to supplementary brand motion-graphic material (title cards, transition backgrounds, abstract data-flow textures) that sits *around* real screen-capture footage, never replacing it.

```text
Abstract, premium, dark-mode tech brand background — subtle geometric
data-flow motif, clean and minimal, suitable as a title-card or
transition background behind real product screen-recording footage.
No literal robot, no humanoid AI imagery, no fake dashboard UI, no
invented software interface (MEDIA-017 §4.2 — never generate a stand-in
UI). Dark neutral palette consistent with a professional B2B software
brand.
```

---

# 2. Naming Convention and Private Folder Structure

Raw Higgsfield outputs (images/video) are **binary media, not private-data-by-content** — NESTLYRA, رحلة عقل, ALSAKKAF Systems, and Sand Dunes Stories are all ALSAKKAF's own brands, not third-party prospect data, so PODS-001 does not apply to them. They stay out of Git for the same reason all rendered media stays out of Git per **MEDIA-012 §5**: binary asset size and the "not in Git" architecture already established for exports/thumbnails/project files — not a privacy rule.

**Location (private, outside the repository):**

```text
ALSAKKAF MEDIA OPERATIONS\<Line>\Higgsfield_Trials\<YYYY-MM-DD>\Test_<NN>_<Slug>\
```

Where `<Line>` matches the existing top-level Media Operations folders:
- `01_ALSAKKAF_SYSTEMS`
- `02_RIHLAT_AQL`
- `04_SAND_DUNES_STORIES`
- `05_COMMERCE\NESTLYRA` (already in use today — see `Higgsfield_Trial_2026-07-16\Test_01_Wardrobe\`)

**File naming:** `<LINE>_Test_<NN>_<Slug>_<Status>_v<N>.<ext>`

- `<Status>` is one of: `RAW` (ungraded), `REFERENCE` (kept for direction, not launch-approved), `REJECTED`, or `HERO_APPROVED` (Founder-approved final asset only — never self-assigned by Atlas or Claude).
- Example, corrected from today's actual files: `NESTLYRA_Test_02_Unlimited_Bedroom_Closet_REFERENCE_v1.png` (today's real file was saved as `NESTLYRA_TEST_02_Unlimited_Bedroom_Closet.png.png` — inconsistent casing and no status tag; this convention fixes that going forward. Existing files are left as-is, not renamed, since reorganizing files wasn't requested.)
- Each `Test_<NN>_<Slug>` folder holds every version generated for that test plus its entry in the generation log below.

---

# 3. Generation Log — Schema

Every Higgsfield trial gets one row, in the per-line private log (e.g. `05_COMMERCE\NESTLYRA\Higgsfield_Trial_<date>\NESTLYRA_Generation_Log.md`, already started today). Columns:

| Column | Notes |
|--------|-------|
| Test | Test number and short label |
| File | Exact filename |
| Prompt | Full prompt text used — record it at generation time; do not reconstruct from memory afterward |
| Model | Which Higgsfield model/engine was used |
| Mode | Image / video / motion mode used |
| Ratio | Aspect ratio |
| Resolution | Output resolution |
| Generation Time | How long the generation took |
| Result Path | Private file path |
| Score | Per the scorecard in Section 4 |
| Rejection Reason | If not approved, why — specific, not "didn't like it" |

**Honesty rule:** if a field wasn't captured at generation time, write "Not recorded — capture manually next time," never a guess. This is the same discipline Atlas Runtime already applies to tracker data — no invented values.

---

# 4. Creative Review Scorecard

Score every Higgsfield still or clip against these dimensions before deciding its status. This extends MEDIA-017's existing quality bar into a repeatable per-asset checklist rather than a one-time rejection record.

| Dimension | Question | Fail condition |
|-----------|----------|-----------------|
| Realism | Does it look premium and intentional, not obviously AI-generated/uncanny? | Warped anatomy, nonsensical geometry, obvious artifacting |
| Brand fit | Does it match the channel's MEDIA-017 §4 rules for that line? | Generic robot imagery (ALSAKKAF Systems), stock-photo look (رحلة عقل), copyrighted-studio resemblance (Sand Dunes Stories) |
| Subject focus | For product work: is the product unmistakably the hero of the frame? | Product buried in a scene, unclear what's for sale |
| Conversion readiness | For commerce work: could this alone justify a purchase click? | Beautiful but ambiguous — this was Test 02's exact failure |
| Text/typography | Any baked-in text correctly rendered? | Any Arabic text present at all (never accept — must be a separate overlay per Section 1.3) |
| Hero status | Is this Founder-approved as final? | Default is NO — only the Founder marks `HERO_APPROVED` |

**Verdict scale:** `REJECTED` / `REFERENCE ONLY` / `PROMISING — NEXT ROUND` / `HERO_APPROVED (Founder only)`. Claude and Atlas may propose `REJECTED`, `REFERENCE ONLY`, or `PROMISING — NEXT ROUND` — only the Founder assigns `HERO_APPROVED`.

---

# 5. Image-to-Video Motion Prompts — After Image Approval Only

Do not write a motion prompt for a still that hasn't at least reached `PROMISING — NEXT ROUND`. Once a still clears that bar:

1. State what should move and what must stay static (e.g., "only the fabric folds shift gently; the product outline stays fixed").
2. State pacing explicitly (slow/premium vs. energetic) — match the channel rule (NESTLYRA: calm/slow per Section 1.2; رحلة عقل: MEDIA-017 §4.1 demands new information every 1.5–3.5 seconds, so a single motion clip is only ever one beat among many, not a whole sequence).
3. State duration expectation (a Higgsfield motion test is a short proof clip, per MEDIA-017 §8's proof-before-full-production rule — not a finished Short or long-form video).
4. Never request generated speech/voice from Higgsfield for any ALSAKKAF-branded video — narration is Founder-voice-cloned per MEDIA-014, a separate pipeline.

---

# 6. Sound-Design Briefs

Briefs only — no audio is generated by this package. For use once real editing begins per MEDIA-017 §5's requirement for audio ducking, transitions, and SFX in the rebuilt pipeline.

| Line | Sound direction | Avoid |
|------|------------------|-------|
| ALSAKKAF Systems | Modern, minimal, confident B2B tech underscore; light UI-click/whoosh SFX synced to real screen-recording actions | Generic "corporate stock" music beds, cliché sci-fi robot sounds |
| رحلة عقل | Documentary-scientific score — curious, warm, builds tension for reveals; subtle Foley for diagrams/maps animating in | Overly dramatic trailer-style music that oversells small facts |
| Sand Dunes Stories | Cinematic desert-fantasy orchestral/ambient score; wind and sand Foley for Telal establishing shots | Music or instrumentation that imitates a specific existing copyrighted franchise's identifiable theme |
| NESTLYRA | Calm, minimal ambient/lifestyle underscore, soft and unobtrusive; no voiceover needed for short product motion tests | Upbeat "sale" energy, countdown/urgency stingers — contradicts the brand's calm positioning |

All music/SFX must be owned, licensed, or verified public-domain before any use in a published video — per the existing Content Review Checklist (MEDIA-010) rights check, unchanged by this package.

---

# 7. Standing Rules (restated, not new)

1. No CLI credits used, no Higgsfield jobs submitted, no skills installed by Claude or Atlas — the Founder generates manually on the website (unchanged from today's session rules).
2. No image or clip is ever presented as a finished video (Section 0).
3. No `HERO_APPROVED` status without explicit Founder review (Section 4).
4. No Arabic (or any) text baked into a generated image — always a separate, tested overlay pass (Section 1.3, MEDIA-017 §3/§6).
5. ALSAKKAF Systems visuals never substitute for the required real screen recording (Section 1.5, MEDIA-017 §4.2).
6. Nothing in this package is published, scheduled, or uploaded — that remains a manual Founder action under MEDIA-017 §9.

---

# Related Documents

- Media_Production_Structure.md (MEDIA-012)
- Character_and_World_Bible.md (MEDIA-015)
- ALSAKKAF_Media_Creative_Quality_Standard.md (MEDIA-017)
- Private_Operational_Data_Standard.md (PODS-001)
- `ALSAKKAF PRIVATE OPERATIONS...05_COMMERCE\NESTLYRA\Higgsfield_Trial_2026-07-16\NESTLYRA_Generation_Log.md` (private, today's working example)

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-16 | Initial package: five-test prompt library, naming/folder convention, generation log schema, creative review scorecard, motion-prompt rules, sound-design briefs |
