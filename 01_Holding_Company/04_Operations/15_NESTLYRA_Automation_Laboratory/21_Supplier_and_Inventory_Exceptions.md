# NESTLYRA — Supplier and Inventory Exceptions

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. No supplier exists (U-09), so no real exception can exist. This document defines how supplier-side problems will be handled when they do.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-021 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Define the exception scenarios a dropshipping supplier relationship can produce and the single workflow that turns each one into Founder-decided options, a supplier-score update, and a recorded lesson — never an improvised fix.

---

# Scope

Covers: exception scenarios, the handling workflow, and the Supplier Exception Register template. Does not cover: customer-side conversation handling (NAL-019) or return resolution decisions (NAL-020) — this document owns the supplier side of those events.

---

# 1. Exception Scenarios

| # | Scenario | Typical Consequence |
|---|----------|---------------------|
| 1 | Stock-out | Orders cannot be fulfilled as promised; product pause candidate |
| 2 | Supplier price increase | Landed cost and margin change; NAL-011 recalculation required before any decision |
| 3 | Delayed dispatch | Delivery-range evidence violated; customers need an approved update |
| 4 | Tracking failure | No visibility on an in-flight order; carrier or supplier investigation |
| 5 | Wrong item shipped | Customer-facing failure; NAL-020 return path plus supplier accountability |
| 6 | Damaged item | Same path as wrong item, plus packaging root-cause question |
| 7 | Supplier cancellation | An accepted order the supplier will not fulfill; urgent Founder options |
| 8 | Unsupported destination | Supplier will not ship where a customer ordered; Market-evidence failure (NAL-017) |
| 9 | Product specification mismatch | Delivered product differs from verified specs; claims integrity issue (NAL-013) |
| 10 | Return refusal | Supplier refuses the documented return route; return-path evidence failure |

---

# 2. The Workflow

| Step | Action | Rule |
|------|--------|------|
| 1 | EXCEPTION detected | Register row created immediately (section 3) |
| 2 | Affected products and orders identified | Every affected order and register row listed — no silent partial handling |
| 3 | Customer impact assessed | Who is waiting, what was implied, what changes for them |
| 4 | Available options prepared | Each with cost, time, and consequence — options, never actions |
| 5 | FOUNDER DECISION | Via the Founder Approval Queue (NAL-014) |
| 6 | Product or Market pause recommendation | Where the exception undermines gate evidence, a pause recommendation is prepared — the Founder pauses, the Partner recommends |
| 7 | Approved communication draft | Any customer or supplier message follows NAL-019: draft, approval, manual send |
| 8 | Final outcome recorded | What was decided and what happened |
| 9 | Supplier score and lesson recorded | Supplier Register (NAL-009) score updated; lesson recorded; repeated patterns escalate to a supplier-replacement recommendation |

---

# 3. Supplier Exception Register (Template)

| Exception ID | Date | Scenario | Supplier Ref | Affected Products | Affected Orders | Customer Impact | Options Prepared | Founder Decision | Pause Recommended | Outcome | Score Update | Lesson |
|--------------|------|----------|--------------|-------------------|-----------------|-----------------|------------------|------------------|-------------------|---------|--------------|--------|
| [Example Only - Not Real] EXAMPLE-SX-001 | 2026-07-17 | Stock-out | EXAMPLE-SUP-001 | EXAMPLE-PC-001 | EXAMPLE-ORD-0002 | 1 order waiting | Wait with approved update / cancel and refund (Founder) | PENDING | Product pause recommended | — | — | — |
| [Example Only - Not Real] EXAMPLE-SX-002 | 2026-07-17 | Price increase | EXAMPLE-SUP-001 | EXAMPLE-PC-002 | None in flight | None yet | Recalculate NAL-011; hold new orders pending Founder price decision | PENDING | — | — | — | — |

Real supplier names and correspondence live in private storage per PODS-001; this register holds structure and EXAMPLE ONLY rows.

---

# 4. Exception Rules

1. No exception is resolved by the Partner acting — every resolution path runs through a Founder decision.
2. A price increase never silently changes a store price; prices are Founder decisions informed by a fresh NAL-011 calculation (NAL-006, forbidden action 5).
3. Scenarios 5, 6, 9, and 10 always cross-open the corresponding NAL-020 return case; scenario 8 always writes a finding back to the Market Readiness Register (NAL-017).
4. Every closed exception carries a supplier-score update and a lesson — an exception with no lesson recorded is not closed.

---

# Related Documents

- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-009 / `09_Supplier_Register.md`
- NAL-011 / `11_Landed_Cost_Calculator_Extension.md`
- NAL-013 / `13_Product_Claim_Verification.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-017 / `17_Market_Readiness_Register.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-020 / `20_Returns_and_Resolution_Workflow.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial specification — ten scenarios, nine-step workflow, exception register template |

---
