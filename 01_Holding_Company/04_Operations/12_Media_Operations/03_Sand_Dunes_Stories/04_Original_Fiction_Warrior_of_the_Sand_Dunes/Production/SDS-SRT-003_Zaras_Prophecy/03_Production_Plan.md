# ALSAKKAF HOLDING GROUP

# Production Plan — SDS-SRT-003: Zara's Prophecy

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-016 / SDS-SRT-003 |
| Document Type | Production Plan |
| Status | Draft rendered — pending Founder approval |
| Version | 1.0 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |

---

# 1. Character Appearance Guide (reference)

Shared across the launch package — see MEDIA-015 v2.0 Section 7. Characters appearing: Zara, Malik.

---

# 2. Location Guide (reference)

Shared across the launch package — see MEDIA-015 v2.0 Section 8. Location used: Zara's fire / seer's camp.

---

# 3. Asset Manifest (this item)

| Asset | Type | Status |
|-------|------|--------|
| 7 card compositions (Section 2 of 02_Script.md) | Original graphic (draft: text cards; final: illustrated/AI art) | Draft placeholder only |
| Zara's design (pale blue-grey shawl motif) | Original character design | Placeholder motif only, per MEDIA-015 Section 7 — full design not yet commissioned |
| Zara's seer-mechanic (what she reads: sand/palm/fire) | Story/visual decision | Undetermined — flagged as an open item for the Founder |
| Narration audio (7 lines, concatenated) | Audio | Generated |

---

# 4. AI Image Prompts (not executed — for future use)

1. "A modest desert campfire at night, isolated from any settlement, one seated cloaked figure tending it, original fantasy setting, no real-world reference."
2. "A woman in layered desert clothing with a distinctive pale blue-grey shawl, seated by firelight, absorbed in some form of divination gesture left intentionally ambiguous (sand, palm, or flame — not fixed yet)."
3. "A boy in a plain, unremarkable traveler's cloak sitting across a campfire, deliberately ordinary framing, no visual cues suggesting hidden importance."
4. "Close-up on a woman's face by firelight shifting from calm routine focus to sudden stillness and recognition."
5. "The same woman lowering her head in a gesture of respect, firelight catching the motion."
6. "A young boy's brief startled laugh, warm firelight, genuine disbelief rather than mockery."
7. "Close two-shot: the woman looking directly and firmly at the boy across the fire, final beat before the end card."

---

# 5. AI Video Prompts (not executed — for future use)

1. "Slow fade-in on an isolated desert campfire at night, gentle ember drift, 4 seconds."
2. "Subtle hand/gesture animation loop over a divination surface (left undefined pending Founder decision), firelight flicker, 5 seconds."
3. "Static shot of a cloaked figure sitting down across a fire, minimal motion, 4 seconds."
4. "Slow push-in on a face shifting from calm to still recognition, 4 seconds."
5. "Slow head-lowering animation, respectful gesture, firelight catching motion, 3 seconds."
6. "Brief natural laugh animation, warm lighting, 3 seconds."
7. "Static held two-shot with firelight flicker only, no camera movement, 6 seconds, to hold weight on the final line."

---

# 6. Narration Manifest

| Field | Value |
|-------|-------|
| Voice engine | Piper 1.4.2 (piper1-gpl), local, offline |
| Voice model | `en_US-lessac-medium` — GENERIC voice, single voice for narrator, Zara, and Malik in this draft |
| Synthesis method | 7 lines synthesized individually, concatenated via ffmpeg concat demuxer |
| Output file | `ALSAKKAF MEDIA OPERATIONS\00_CONTROL\Founder_Voice_Assets\Abdulrahman\06_Production_Narrations\Sand_Dunes_Stories\SDS-SRT-003_narration_GENERIC_PENDING_APPROVAL.wav` |
| Status | Generated; PENDING FOUNDER LISTENING APPROVAL |
| Open item | Same shared-voice limitation as SDS-SRT-002; distinct generic voices per character would strengthen this Short in particular, since it hinges on a two-character exchange |

---

# 7. Sound and Music Plan

Draft render has narration + cards only. Final cut suggestion: a sparse, single-instrument motif (e.g., a solitary string or reed tone, not a full score) that swells slightly under Zara's declaration (line 4) and resolves under her final line (line 6) — reinforcing the "recognition" beat without music that oversells the moment. No music sourced yet; must be Founder-owned, licensed, or public domain before use.

---

# 8. AI-Disclosure Recommendation

Same recommendation as the other launch items: disclose AI-generated narration and any AI-assisted visuals in the description and via platform tools at time of publish. Not yet applied — Founder to confirm.

---

# 9. Founder Approval Gate

- [ ] Watches the rendered draft MP4 in full
- [ ] Confirms the "Original Fiction — Sand Dunes Stories" label will appear in the description
- [ ] Decides Zara's seer-mechanic (Section 3 open item) before further production deepens it
- [ ] Confirms no real place, real person, or real historical claim is implied
- [ ] Confirms the AI-disclosure approach before upload

---

# Related Documents

- Character_and_World_Bible.md (MEDIA-015 v2.0)
- 02_Script.md
- 04_Upload_Package.md

---

# Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-15 | Initial production plan |
