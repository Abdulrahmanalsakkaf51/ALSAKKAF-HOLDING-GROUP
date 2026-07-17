# NESTLYRA — Extended Report Specifications

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Report specifications only — no report contains real data until real, Founder-approved operations exist. Every metric reconciles to a named register; invented numbers are forbidden.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-029 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Extend the Daily and Weekly operations reports (NAL-026) with the six domain reports required for Checkpoint A, each with a fixed source-register mapping so every number is traceable.

---

# Scope

Covers: report structure, fields, sources, frequency, and honesty rules for six report types. Does not cover: report generation tooling (later checkpoint) or the Daily/Weekly reports already specified in NAL-026.

---

# 1. Product Verification Report

| Field | Source |
|-------|--------|
| Candidates by stage (candidate → evidence → sample → verified → rejected) | Product Candidate Register (NAL-008) |
| Evidence gaps per candidate | Supplier Evidence Register (NAL-010) |
| Samples ordered/inspected/passed/failed | Sample Inspection Record (NAL-012) |
| Claims verified vs pending | Product Claim Verification (NAL-013) |
| Founder decisions pending | Founder Approval Queue (NAL-014) |
| Rejections and reasons | Rejected Product Lessons Log (NAL-015) |

Frequency: weekly, and on demand before any Founder product decision. Empty state: "No product candidates exist." — currently true.

# 2. Market Readiness Report

| Field | Source |
|-------|--------|
| Countries assessed / passed / failed / deferred | Market Readiness Register (NAL-017) |
| Criteria failing most often | NAL-017 gate results |
| Active Markets (verified) | Current-State Audit (NAL-002) — UAE only |
| Activation requests awaiting Founder | Market Activation Approval Record (NAL-017) |

Frequency: on change; reviewed before any Market discussion. Empty state: "No country has been assessed — no supplier evidence exists (U-09)." — currently true.

# 3. First 20 Orders Report

| Field | Source |
|-------|--------|
| Orders received / approved / submitted to supplier / delivered / closed | First 20 Orders Register (NAL-018) |
| Founder approvals pending | Founder Approval Record (NAL-018) |
| Exceptions open by type | Order Exception Register (NAL-018) |
| Actual cost vs calculated landed cost per order | Actual Cost and Margin Record (NAL-018) |
| Lessons captured | NAL-018 lesson rows |

Frequency: daily while any of the first 20 orders is open. Empty state: "No real orders exist — store not launched." — currently true.

# 4. Customer Inquiry Report

| Field | Source |
|-------|--------|
| Inquiries by category / status / age | Customer Inquiry Register (NAL-019) |
| Drafts awaiting Founder approval | NAL-019 + Founder Approval Queue (NAL-014) |
| Sent (manually, after approval) vs pending | NAL-019 outcome rows |
| Follow-ups due | NAL-019 follow-up fields |

Frequency: daily once any inquiry exists. Empty state: "No inquiries — store not launched."

# 5. Returns and Exceptions Report

| Field | Source |
|-------|--------|
| Returns by reason class and status | Returns Register (NAL-020) |
| Supplier exceptions by scenario type | Supplier Exception Register (NAL-021) |
| Supplier score changes | NAL-020/NAL-021 score rows |
| Pause recommendations awaiting Founder | NAL-021 + NAL-014 |

Frequency: weekly, and immediately on any new exception. Empty state: "No returns or exceptions — store not launched."

# 6. Cost and Credit Usage Report

| Field | Source |
|-------|--------|
| AI/tool credit usage for PRJ-020 work | UNKNOWN — measurement mechanism not yet chosen; recorded as PENDING until the Founder selects one (candidate: session-level manual log) |
| Shopify subscription cost | UNKNOWN (U-10 — plan tier unverified) |
| Per-order actual costs | Actual Cost and Margin Record (NAL-018) — empty until real orders |
| App costs | None — no app installed or approved |

Frequency: monthly. Honesty rule: this report may currently contain only UNKNOWN/PENDING rows and the zero-cost confirmations — that is the correct, expected state.

---

# 7. Common Rules (all six reports)

1. Every number cites its register row(s); a number with no source row may not appear.
2. Zero is reported as zero; UNKNOWN is reported as UNKNOWN — never estimated.
3. Reports never trigger actions — they inform Founder decisions only.
4. Synthetic-run reports (NAL-028) are labeled SYNTHETIC in the title and never mixed with real data.

---

# Related Documents

- NAL-026 / `26_Reporting_Specifications.md` (Daily and Weekly operations reports)
- NAL-008, NAL-010, NAL-012, NAL-013, NAL-014, NAL-015, NAL-017, NAL-018, NAL-019, NAL-020, NAL-021
- NAL-028 / `28_Synthetic_Acceptance_Test_Specification.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial six extended report specifications with source-register mappings |

---
