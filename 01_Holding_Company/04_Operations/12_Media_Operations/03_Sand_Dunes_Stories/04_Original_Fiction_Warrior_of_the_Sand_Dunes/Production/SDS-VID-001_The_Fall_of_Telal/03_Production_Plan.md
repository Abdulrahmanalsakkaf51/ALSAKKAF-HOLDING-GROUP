# ALSAKKAF HOLDING GROUP

# Production Plan — SDS-VID-001: Episode 1 — The Fall of Telal

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | MEDIA-016 / SDS-VID-001 |
| Document Type | Production Plan |
| Status | Draft rendered — pending Founder approval |
| Version | 1.0 |
| Date | 2026-07-15 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-018 |

---

# 1. Character Appearance Guide (reference)

Shared across the launch package — see MEDIA-015 v2.0 Section 7. Characters appearing: Leila, Amir, Malik, Sultan Feroos, the King (brief, non-focal).

---

# 2. Location Guide (reference)

Shared across the launch package — see MEDIA-015 v2.0 Section 8. Locations used: Telal (before the fall), Telal (the night it falls), the desert road out.

---

# 3. Asset Manifest (this item)

| Asset | Type | Status |
|-------|------|--------|
| 15 card compositions (Section 3-4 of 02_Script.md) | Original graphic (draft: text cards; final: illustrated/AI art) | Draft placeholder only |
| Series title lockup | Typography asset | Placeholder font (Segoe UI Bold) used in draft render |
| Opening/closing disclaimer cards | Graphic + text | Present in draft |
| Narration audio (26 lines, concatenated) | Audio | Generated |

---

# 4. AI Image Prompts (not executed — for future use)

1. "Wide golden-hour shot of a prosperous desert capital city, warm sandstone towers, trade caravans faintly visible at the city edge, original fantasy architecture."
2. "Two boys of different ages in a palace courtyard, one dressed slightly more formally and composed, the other more playful and unguarded, warm daylight."
3. "A King seated among trusted commanders in a warm, sunlit court setting, atmosphere of trust and ease, no tension visible yet."
4. "A decorated military commander standing prominently but not yet ominously in a formal court setting."
5. "Palace gates at night, torches lit, guards present but lit in a cooler, shifted color temperature suggesting divided loyalty."
6. "A composed, resolved-looking mother figure in a palace interior at night, urgency implied through posture rather than panic."
7. "A narrow, unglamorous servants' passage or hidden doorway, practical rather than grand, warm torchlight."
8. "Desert capital skyline at night, now lit orange-red with rising smoke from the towers."
9. "A commanding figure addressing an implied crowd from a balcony or platform, declarative posture, no visible violence."
10. "Extreme wide shot: three small silhouetted figures crossing a vast dune landscape at dawn."
11. "Close composition on a small wrapped clay vial being carried carefully in a woman's hands."
12. "A distant, softly out-of-focus campfire silhouette on the horizon at dusk, suggesting an unseen figure — restrained, not a full character reveal."

---

# 5. AI Video Prompts (not executed — for future use)

1. "Slow establishing push-in on a golden desert city skyline, warm ambient light shimmer, 6 seconds."
2. "Static two-shot of two boys in a courtyard, subtle ambient motion (fabric, light), 5 seconds."
3. "Gentle ambient court scene, characters engaged in quiet conversation, minimal camera movement, 6 seconds."
4. "Slow color-temperature shift across a palace gate scene, warm to cool, suggesting divided loyalty over time, 6 seconds."
5. "Urgent but readable motion through a narrow passage, tracking shot, 6 seconds."
6. "Skyline shot transitioning from calm to fire and smoke, slow push-in, matching the establishing shot's camera angle, 5 seconds."
7. "Extremely slow wide pan across a dawn desert landscape with three small figures walking, 6 seconds."
8. "Macro slow-motion on hands carefully carrying a small wrapped object, 4 seconds."
9. "Very subtle distant campfire flicker on the horizon at dusk, minimal motion, 4 seconds."
10. "Static end-card hold with subtle sand-particle drift, 3 seconds."

---

# 6. Narration Manifest

| Field | Value |
|-------|-------|
| Voice engine | Piper 1.4.2 (piper1-gpl), local, offline |
| Voice model | `en_US-lessac-medium` — GENERIC voice, single narrator voice throughout, not the Founder's |
| Synthesis method | 26 lines synthesized individually (for accurate per-line timing), concatenated via ffmpeg concat demuxer into one narration track |
| Output file | `ALSAKKAF MEDIA OPERATIONS\00_CONTROL\Founder_Voice_Assets\Abdulrahman\06_Production_Narrations\Sand_Dunes_Stories\SDS-VID-001_narration_GENERIC_PENDING_APPROVAL.wav` |
| Status | Generated; PENDING FOUNDER LISTENING APPROVAL |
| Open item | This episode currently uses one narrator voice for all lines, including implied dialogue ("We are leaving. Now.") — distinct character voices are a future upgrade to flag for Founder decision |

---

# 7. Sound and Music Plan

Draft render has narration + cards only, no music or sound effects. Final cut suggestion, scene by scene:

- Establishing Telal (cards 1-4): warm, hopeful ambient score, distant market/city ambience
- The betrayal build (cards 5-7): score shifts to a lower, tenser register, no sudden stings
- The escape (cards 8-9): a rising, urgent but not action-movie-scale cue
- The burning towers (card 10): the score's most intense point, brief
- Into the desert (cards 11-13): the score drops away almost entirely, replaced by wind and near-silence, emphasizing isolation
- Title/disclaimer close (cards 14-15): a quiet resolving musical button

No music has been sourced yet. Any music or sound effect used must be Founder-owned, properly licensed royalty-free, or verified public domain — no copyrighted music or footage.

---

# 8. AI-Disclosure Recommendation

Recommend disclosing in the video description (and via YouTube's AI-content disclosure toggle at time of publish, if applicable under current platform policy) that narration is AI-generated speech (Piper, generic voice) and that visuals may be AI-assisted per the prompts in Sections 4-5. This is a recommendation for Founder confirmation, not an applied disclosure — platform policy should be re-checked at time of publish since it changes.

---

# 9. Founder Approval Gate

This item may not be published until the Founder:

- [ ] Watches the rendered draft MP4 in full
- [ ] Confirms the "Original Fiction — Sand Dunes Stories" opening card appears within the first 15 seconds (currently present as card 1)
- [ ] Confirms no real place, real person, or real historical claim is implied
- [ ] Decides on the open items flagged across this package (the King's name, Jaber's role, Amir/Malik's relationship dynamic, the potion's mechanics, Zara's seer-mechanic, and single-vs-distinct narration voices) before any further episodes are produced
- [ ] Approves or requests changes to narration, pacing, or card text
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
