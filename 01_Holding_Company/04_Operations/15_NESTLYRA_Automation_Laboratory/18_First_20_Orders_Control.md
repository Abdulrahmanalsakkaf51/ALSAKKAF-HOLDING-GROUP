# NESTLYRA — First 20 Orders Control

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. No real order exists. Founder-confirmed rule: every supplier order for the first 20 real customer orders requires explicit Founder approval — no exceptions.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-018 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Define the fully manual, Founder-gated workflow for the first 20 real customer orders, so NESTLYRA's earliest operations produce verified cost, delivery, and process evidence before any automation is trusted with anything.

---

# Scope

Covers: the order workflow, the hard prohibitions during the control period, and the four register templates the workflow writes to. Does not cover: what happens after order 20 — relaxations require a Founder review of the evidence this control period produces, recorded as a new version of this document.

---

# 1. The Workflow — Every Order, In Order

| Step | Action | Who Acts |
|------|--------|----------|
| 1 | ORDER RECEIVED | Shopify records it; the Partner may only read and register |
| 2 | Payment state verified | Partner checks paid / pending / failed — payment configuration itself is UNVERIFIED (U-05) |
| 3 | Address completeness checked | Missing or doubtful address goes to the Order Exception Register (section 5) |
| 4 | Risk flag assessed | Unusual quantity, mismatched details, or suspicious pattern flagged — flag, never accuse |
| 5 | Supplier availability confirmed | Current stock and price confirmed with the supplier before anything is prepared |
| 6 | Market eligibility confirmed | Destination must be an active, gate-passed Market (NAL-016); anything else is an exception |
| 7 | Office Clerk order record created | Row in the First 20 Orders Register (section 3) |
| 8 | Supplier order PREPARED | Draft only — items, quantities, destination, cost. Nothing sent |
| 9 | FOUNDER APPROVAL | Via the Founder Approval Queue (NAL-014). The order waits here as long as it takes |
| 10 | Manual supplier submission | The Founder (or a Founder-directed manual step) submits — never the Partner |
| 11 | Tracking recorded | Tracking number and carrier into the order record |
| 12 | Customer update DRAFTED | Draft only, using verified information only (NAL-019 rules) |
| 13 | Founder approval of the update | Second approval — messages are gated separately from supplier orders |
| 14 | Manual send | The Founder sends; the Partner never sends (NAL-006, forbidden action 8) |
| 15 | Delivery monitored | Tracking checked; delays become exceptions (section 5) and may involve NAL-021 |
| 16 | Order closed | Delivered and no open issue |
| 17 | Actual cost and lesson recorded | Actual Cost and Margin Record (section 6) plus any lesson — this is the point of the first 20 |

---

# 2. Hard Prohibitions During the First 20 Orders

| # | Never During the Control Period |
|---|--------------------------------|
| 1 | No automatic supplier submission — every submission is manual and Founder-approved |
| 2 | No substitution of items, variants, or suppliers without a new Founder approval |
| 3 | No refund of any kind by the Partner — refunds are Founder-only, always (NAL-006) |
| 4 | No price change |
| 5 | No promise to a customer — no delivery date, no compensation, no outcome commitment |
| 6 | No external message of any kind sent by the Partner — customer or supplier |

These prohibitions restate NAL-006 for the control period; NAL-006 wins over any conflicting text anywhere.

---

# 3. First 20 Orders Register (Template)

| Order # (1-20) | Shopify Order Ref | Date | Payment State | Address Check | Risk Flag | Market | Supplier Confirmed | Founder Approval Ref | Tracking | Customer Update Sent | Status | Closed Date |
|----------------|-------------------|------|---------------|---------------|-----------|--------|--------------------|-----------------------|----------|----------------------|--------|-------------|
| [Example Only - Not Real] 1 | EXAMPLE-ORD-0001 | 2026-07-17 | Paid (example) | Complete | None | UAE | Yes (example) | EXAMPLE-Q-101 | EXAMPLE-TRK-001 | Yes — Founder sent | Delivered (example) | 2026-07-17 |
| [Example Only - Not Real] 2 | EXAMPLE-ORD-0002 | 2026-07-17 | Pending | Incomplete — see EXAMPLE-EX-001 | None | UAE | Not yet | PENDING | — | No | Waiting on exception | — |

---

# 4. Founder Approval Record (Template)

One record per approval step (steps 9 and 13 each get one).

| Approval Ref | Order # | Approval Type | What Was Approved | Evidence Attached | Decision | Decision Date | Executed By |
|--------------|---------|---------------|-------------------|-------------------|----------|---------------|-------------|
| [Example Only - Not Real] EXAMPLE-Q-101 | 1 | Supplier order | Prepared supplier order EXAMPLE-SO-001 | Supplier confirmation, cost breakdown | APPROVE (example) | 2026-07-17 | Founder — manual submission |
| [Example Only - Not Real] EXAMPLE-Q-102 | 1 | Customer update | Drafted dispatch notification | Tracking number, draft text | APPROVE (example) | 2026-07-17 | Founder — manual send |

---

# 5. Order Exception Register (Template)

| Exception ID | Order # | Exception Type | Description | Customer Impact | Options Prepared | Founder Decision | Outcome |
|--------------|---------|----------------|-------------|-----------------|------------------|------------------|---------|
| [Example Only - Not Real] EXAMPLE-EX-001 | 2 | Incomplete address | Building number missing | Delivery impossible as-is | Draft address-confirmation request for Founder approval | PENDING | — |

Exception types include: incomplete address, payment anomaly, risk flag, unsupported destination, supplier unavailability, delivery delay, customer change request. Supplier-side exceptions also enter NAL-021.

---

# 6. Actual Cost and Margin Record (Template)

The control period's core output: real numbers replacing estimates, order by order.

| Order # | Estimated Landed Cost (NAL-011 ref) | Actual Product Cost | Actual Shipping | Actual Fees | Actual Other | Actual Total | Sale Price | Actual Margin | Variance vs. Estimate | Lesson |
|---------|--------------------------------------|---------------------|-----------------|-------------|--------------|--------------|------------|---------------|------------------------|--------|
| [Example Only - Not Real] 1 | EXAMPLE-LC-001 | UNKNOWN until real | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN (U-14) | UNKNOWN | Example row — structure only |

---

# 7. Control Rules

1. The count is 20 real customer orders — test, cancelled-before-approval, and synthetic orders do not count toward the 20.
2. Every register row above is EXAMPLE ONLY until a real order exists; real customer data then lives per PODS-001, with this public register holding structure only.
3. Nothing in steps 1-8 constitutes progress toward approval — step 9 is a genuine decision point, and HOLD or REJECT are normal outcomes.
4. Ending or relaxing this control after order 20 is itself a Founder decision, made against the evidence in section 6 — it does not expire automatically.

---

# Related Documents

- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-011 / `11_Landed_Cost_Calculator_Extension.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-016 / `16_Market_Activation_Gate.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-021 / `21_Supplier_and_Inventory_Exceptions.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial control — 17-step workflow, six prohibitions, four register templates with EXAMPLE ONLY rows |

---
