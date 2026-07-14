# ALSAKKAF HOLDING GROUP

# POD-001 — First Internal Operational Partner Pod

> "Atlas supervises. Roles verify, draft, report, and file. Humans approve."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | POD-001 |
| Document Type | Partner Pod Definition |
| Status | Designed — pod activation requires Founder approval of member Partners |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Projects | PRJ-013, PRJ-014 |
| Related Documents | PREG-001, RTASK-001, POD member lifecycle documents |

---

# 1. Purpose

The first internal Partner pod runs ALSAKKAF Systems' own revenue and office operations. It is the reference deployment: what we sell to customers, we run ourselves first.

---

# 2. Pod Structure

```text
Atlas (PARTNER-002, Active) — supervises and routes
    ├── Research Partner (PARTNER-004, Designed) — verify leads
    ├── Client Acquisition Partner (PARTNER-019, Designed) — draft outreach
    ├── Reporting Partner (PARTNER-012, Designed) — pipeline reports, briefings
    └── Office Operations Partner (PARTNER-007, Designed) — files, trackers, documents

Supporting (Active): The Librarian (PARTNER-001) — indexing;
                     Guardian (PARTNER-016) — security and claim review
```

---

# 3. Task Routing (Atlas)

| Incoming work | Routed to |
|---------------|-----------|
| New lead rows | Research Partner (verify first — always) |
| Verified High/Medium leads | Client Acquisition Partner (draft) |
| Drafts ready | Founder (approve and send — human only) |
| Tracker/report requests | Reporting Partner |
| Files, documents, trackers, minutes | Office Operations Partner |
| Anything financial, legal, external, sensitive | Founder directly |

---

# 4. Deterministic Tooling

| Role | Tool |
|------|------|
| Research | 09_AI_Systems/02_Tools/Pod_Tools/research_verifier.py |
| Acquisition | 09_AI_Systems/02_Tools/Pod_Tools/outreach_composer.py |
| Reporting | 09_AI_Systems/02_Tools/Pod_Tools/pipeline_reporter.py |
| Office | 09_AI_Systems/02_Tools/Office_Toolbelt/ (7 tools) |

All tools: Python standard library, offline, tested (13/13 pod tests, 10/10 office tests on 2026-07-14).

---

# 5. Hard Rules

1. No Partner in this pod sends anything externally. Humans send.
2. No pod member is Active until its activation checklist item "Founder approval" is granted.
3. Lead flow is always verify → draft → human approve → human send.
4. Reporting numbers are counted, never estimated.

---

# 6. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial pod definition |
