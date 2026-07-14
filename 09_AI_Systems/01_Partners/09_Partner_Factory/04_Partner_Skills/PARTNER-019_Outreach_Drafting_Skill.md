# ALSAKKAF HOLDING GROUP

# Outreach Drafting Skill

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CASKILL-001 |
| Document Type | Partner Skill |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Partner | PARTNER-019 |
| Related Documents | CAPROF-001, CATEST-001, PFT-003 |

---

# 1. Skill Purpose

Produce personalized first-touch and follow-up outreach drafts from verified leads, using only approved offers, with zero sending capability.

---

# 2. Inputs / Outputs

| Direction | Item |
|-----------|------|
| Input | Verified lead + confidence label from Research Partner |
| Output | First-touch draft (to, subject, body, offer, DRAFT status) |
| Output | Follow-up draft with 3-day no-reply condition |

---

# 3. Steps

1. Confirm lead confidence is High or Medium; refuse otherwise.
2. `outreach_composer.choose_offer()` selects the approved offer.
3. `outreach_composer.compose_outreach()` builds both drafts.
4. Save drafts for human review; log as Not Sent in the outreach tracker.

---

# 4. Permission, Cost, Local-First

Level 3 (Prepare). Local tool tier, zero cost, fully offline. The module contains no sending capability (no smtplib, no network imports) — enforced by test.

---

# 5. Approval Trigger

Every send is a human action. Template changes are reviewed by Guardian for false claims and approved by the Founder.

---

# 6. Test Requirements

`test_pod_tools.py` — OutreachComposerTests must pass. Status 2026-07-14: passing.

---

# 7. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial skill |
