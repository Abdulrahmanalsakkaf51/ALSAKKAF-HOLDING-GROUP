# ALSAKKAF HOLDING GROUP

# Production Plan — SDS-SRT-002: The Secret Potion

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-016 / SDS-SRT-002 |
| Document Type | Production Plan |
| Status | Draft rendered — pending Founder approval |
| Version | 1.0 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |

---

# 1. Character Appearance Guide (reference)

Shared across the launch package — see MEDIA-015 v2.0 Section 7. Characters appearing: Leila, Malik.

---

# 2. Location Guide (reference)

Shared across the launch package — see MEDIA-015 v2.0 Section 8. Location used: the desert camp (days later).

---

# 3. Asset Manifest (this item)

| Asset | Type | Status |
|-------|------|--------|
| 8 card compositions (Section 2 of 02_Script.md) | Original graphic (draft: text cards; final: illustrated/AI art) | Draft placeholder only |
| The vial (recurring prop) | Original prop design | Not yet designed — first appearance of this object, should be finalized before SDS-VID-001's later references if vial appears there too |
| Narration audio (8 lines, concatenated) | Audio | Generated |

---

# 4. AI Image Prompts (not executed — for future use)

1. "Quiet desert campsite at dusk, warm dying firelight, two figures sitting slightly apart from the rest of a small camp, intimate framing, original fantasy setting."
2. "Close-up composition on a small hand-sized clay vial passing between a mother's hands and a young boy's hands, warm firelight, no visible faces required."
3. "Reaction close-up on a young boy's face, confused but not afraid, warm rim-lighting from a campfire."
4. "Close-up on a woman's face, serious and direct, warm low firelight, desert night background softly out of focus."
5. "A young boy looking down at a small object held in both hands, contemplative framing, campfire glow."

---

# 5. AI Video Prompts (not executed — for future use)

1. "Slow fade-in on a firelit desert campsite at dusk, gentle ember particle drift, 4 seconds."
2. "Macro-style slow motion of a small vial passing between two sets of hands, warm light, 5 seconds."
3. "Subtle facial micro-expression shift from confusion to focus, slow push-in, 4 seconds."
4. "Static close-up with natural firelight flicker only, no camera movement, 6 seconds, to hold weight on the dialogue."
5. "Slow zoom on a hand closing around a small object, 4 seconds."

---

# 6. Narration Manifest

| Field | Value |
|-------|-------|
| Voice engine | Piper 1.4.2 (piper1-gpl), local, offline |
| Voice model | `en_US-lessac-medium` — GENERIC voice, single voice for narrator and both dialogue lines in this draft |
| Synthesis method | 8 lines synthesized individually, concatenated via ffmpeg concat demuxer |
| Output file | `ALSAKKAF MEDIA OPERATIONS\00_CONTROL\Founder_Voice_Assets\Abdulrahman\06_Production_Narrations\Sand_Dunes_Stories\SDS-SRT-002_narration_GENERIC_PENDING_APPROVAL.wav` |
| Status | Generated; PENDING FOUNDER LISTENING APPROVAL |
| Open item | Leila and Malik currently share the narrator's voice; distinct character voices (still generic, not the Founder's) are a future upgrade to flag for Founder decision before wider production |

---

# 7. Sound and Music Plan

Draft render has narration + cards only. Final cut suggestion: quiet ambient desert-night sound (wind, distant insects) under the whole piece, a soft emotional string or low-drone cue under Leila's warning (line 5), and near-silence under Malik's final reaction (line 7) to let the moment land. No music sourced yet — must be Founder-owned, properly licensed, or verified public domain before use.

---

# 8. AI-Disclosure Recommendation

Same recommendation as SDS-SRT-001: disclose AI-generated narration and any AI-assisted visuals in the description and via platform disclosure tools at time of publish. Not yet applied — Founder to confirm.

---

# 9. Founder Approval Gate

- [ ] Watches the rendered draft MP4 in full
- [ ] Confirms the "Original Fiction — Sand Dunes Stories" label will appear in the description
- [ ] Decides whether shared-voice dialogue (Section 6 open item) is acceptable for this draft or needs distinct voices before publish
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
