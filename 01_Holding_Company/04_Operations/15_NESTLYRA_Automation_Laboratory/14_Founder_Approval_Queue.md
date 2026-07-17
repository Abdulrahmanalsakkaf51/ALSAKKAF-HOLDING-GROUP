# NESTLYRA — Founder Approval Queue (Template)

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Template with an EXAMPLE ONLY row. Every action that spends money, publishes, activates, sends, or commits NESTLYRA to anything passes through this queue and waits for the Founder.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-014 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.1 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Give the Founder one place where every pending NESTLYRA decision waits, fully prepared with evidence and a Guardian check, following the same pattern as the Client Communications Founder Approval Queue (COMMS-004).

---

# Scope

Covers: queue format, the decision types that must use it, and queue rules. Does not cover: the decisions themselves — the queue prepares, the Founder decides.

---

# 1. Decision Types That Must Enter This Queue

| Type | Source Workflow |
|------|-----------------|
| Sample order (a spend) | NAL-007 Stage 11 |
| Product approval | NAL-007 Stage 15 |
| Market activation | NAL-016 / NAL-017 |
| Supplier order for a customer order | NAL-018 (every one of the first 20 orders) |
| Customer message (any outbound) | NAL-019 |
| Return / refund resolution | NAL-020 |
| Supplier-exception resolution | NAL-021 |
| Price set or change | NAL-011 calculation attached |
| Any policy, app, or settings change | NAL-024 (catalogue items, if ever implemented) |

---

# 2. Queue Table

| Queue ID | Date Queued | Type | Subject Ref | Evidence Attached | Guardian Check | Founder Decision | Decision Date | Notes |
|----------|-------------|------|-------------|-------------------|----------------|------------------|---------------|-------|
| EXAMPLE-Q-001 | 2026-07-17 | Sample order | EXAMPLE-PC-001 / EXAMPLE-SUP-001 | [Example Only - Not Real] landed-cost record EXAMPLE-LC-001, evidence EXAMPLE-EV-001 | Passed (example) | PENDING | — | Template row only — not a real request |

---

# 3. Queue Rules

1. An item enters the queue only when complete: evidence attached, calculation current (not Stale), Guardian check recorded. Incomplete items are returned to the preparing workflow, not queued.
2. Guardian check is a safety review (permission matrix compliance, no invented facts, no risk flags ignored) — it is never an approval. Only the Founder approves.
3. Founder decisions: APPROVE / EDIT AND APPROVE / HOLD / REJECT. A rejection reason is recorded; product rejections also go to NAL-015.
4. Nothing executes on APPROVE by itself — the Founder (or a Founder-directed manual step) executes. Approval authorizes; it does not automate.
5. Queue rows are never deleted; decided rows keep their outcome permanently.

---

# Related Documents

- COMMS-004 / `../13_Client_Communications/Founder_Approval_Queue_Template.md` (house pattern)
- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-015 / `15_Rejected_Product_Lessons_Log.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial queue template with EXAMPLE ONLY row |
| 1.1 | 2026-07-17 | Cross-references renumbered to the final NAL-016..027 file plan (Market readiness NAL-017, orders NAL-018, customer care NAL-019, returns NAL-020, exceptions NAL-021, catalogue NAL-024) |

---
