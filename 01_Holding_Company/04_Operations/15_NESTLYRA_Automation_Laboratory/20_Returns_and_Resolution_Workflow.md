# NESTLYRA — Returns and Resolution Workflow

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. No order, no return, no refund has ever occurred. The Partner cannot issue a refund — refunds are money movement and belong to the Founder alone (NAL-006).

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-020 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Define how a return request travels from first contact to a Founder-decided resolution, so every return produces a recorded root cause and a supplier-score update instead of an improvised refund.

---

# Scope

Covers: the return workflow, the Returns Register template, and the current-state constraints. Does not cover: the customer-facing returns policy text — a draft exists as NESTLYRA-008 but is unpublished and pending legal review; no return policy exists on the store today (launch blocker, NAL-023).

---

# 1. Current-State Constraints (verified, NAL-002)

| Constraint | State |
|------------|-------|
| Self-service returns | Disabled in Shopify — every return starts as a conversation, not a portal flow |
| Published return policy | None exists — a launch blocker (NAL-023); NESTLYRA-008 is an unpublished draft pending legal review |
| Supplier return route | UNKNOWN — no supplier exists (U-09); no return path can be assumed |

Until a policy is published and a supplier return route is evidenced, no return commitment of any kind can be made to anyone.

---

# 2. The Workflow

| Step | Action | Rule |
|------|--------|------|
| 1 | RETURN REQUEST received | Enters as a customer inquiry (NAL-019 category 6) and gets a Returns Register row |
| 2 | Order and Market check | Confirm the order exists, its Market, and its delivery state |
| 3 | Policy check | Against the policy in force at order time; today no policy exists, so any pre-launch scenario is synthetic only |
| 4 | Reason classification | Damaged, wrong item, not as described, unwanted, delivery failure, other |
| 5 | Necessary evidence only | Photos or details needed to assess — never more than the case requires |
| 6 | Supplier return route checked | From supplier evidence (NAL-010); an unworkable route is itself a finding |
| 7 | Resolution options prepared | Replacement, refund, partial, return-and-refund, decline — each with cost and reasoning; options, not decisions |
| 8 | FOUNDER DECISION | Via the Founder Approval Queue (NAL-014). The Partner cannot issue a refund — no amount, no exception |
| 9 | Manual refund / replacement action | Executed by the Founder (refund in Shopify; replacement follows NAL-018 supplier-order approval if within the first 20) |
| 10 | Outcome recorded | What was done, when, and the customer communication (drafted and approved per NAL-019) |
| 11 | Root cause recorded | Product, supplier, carrier, expectation-setting, or customer-side — honest attribution |
| 12 | Supplier score updated | Root causes attributable to the supplier update the Supplier Register (NAL-009) score |

---

# 3. Returns Register (Template)

| Return ID | Date | Order Ref | Market | Reason Class | Evidence Ref | Return Route | Options Prepared | Founder Decision | Action Taken | Outcome | Root Cause | Supplier Score Updated |
|-----------|------|-----------|--------|--------------|--------------|--------------|------------------|------------------|--------------|---------|------------|------------------------|
| [Example Only - Not Real] EXAMPLE-RET-001 | 2026-07-17 | EXAMPLE-ORD-0001 | UAE | Damaged | EXAMPLE-EVD-001 (photos) | UNKNOWN — supplier route unverified (U-09) | Replacement / refund, costed | PENDING | — | — | — | — |

Real return data, when it exists, lives per PODS-001; this register holds structure and EXAMPLE ONLY rows.

---

# 4. Workflow Rules

1. The Partner may draft, classify, check, and prepare options — it may never issue, confirm, or promise a refund or replacement (NAL-006, forbidden action 6).
2. Every customer-facing message in this workflow follows NAL-019: draft, Guardian where sensitive, Founder approval, manual send.
3. A refund-adjacent conversation uses the COMMS-007 safe-holding-reply pattern until the Founder decides.
4. Root cause and supplier-score steps are mandatory — a closed return without them is not closed.
5. Damaged, wrong-item, and return-refusal cases also open a Supplier Exception (NAL-021) so the supplier-side pattern is tracked.

---

# Related Documents

- NAL-002 / `02_Current_State_Audit.md`
- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-009 / `09_Supplier_Register.md`
- NAL-010 / `10_Supplier_Evidence_Register.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-018 / `18_First_20_Orders_Control.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-021 / `21_Supplier_and_Inventory_Exceptions.md`
- NAL-023 / `23_Launch_Blocker_Register.md`
- NESTLYRA-008 / `../14_NESTLYRA_Store/08_Returns_and_Refunds.md` (unpublished draft policy)
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial workflow — twelve steps, Returns Register template, no-refund-by-Partner rule |

---
