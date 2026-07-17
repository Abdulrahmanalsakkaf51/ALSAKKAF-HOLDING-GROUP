# NESTLYRA — Market Readiness Register (Template)

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Template with EXAMPLE ONLY rows. No country has been assessed; no supplier evidence exists (U-09), so no real row can exist yet.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-017 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Hold the per-country evidence that the Market Activation Gate (NAL-016) requires, so every gate decision — pass, fail, or defer — traces to recorded evidence and a Founder decision.

---

# Scope

Covers: the register structure, the pass/fail criteria checklist, the Deferred Market Register, the Market Activation Approval Record format, and the Market Risk Register. Does not cover: the gate rules themselves (NAL-016 owns those) or real country data (none exists).

---

# 1. Market Readiness Register Table

| Country | Supplier-Delivery Evidence | Tracking Evidence | Delivery Range | Shipping Cost | Duties / Tax Treatment | Restrictions | Return Route / Cost | Support Readiness | Unit Economics | Gate Result | Founder Approval |
|---------|----------------------------|-------------------|----------------|---------------|------------------------|--------------|----------------------|-------------------|----------------|-------------|------------------|
| [Example Only - Not Real] Sampleland | UNKNOWN — no supplier exists (U-09) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN (U-04) | Not checked | UNKNOWN | Not assessed | UNKNOWN (U-14) | DEFERRED | PENDING |
| [Example Only - Not Real] Examplia | UNKNOWN — no supplier exists (U-09) | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN (U-04) | Not checked | UNKNOWN | Not assessed | UNKNOWN (U-14) | DEFERRED | PENDING |

Gate Result values: PASS / FAIL / DEFERRED. A row may show PASS only when all ten NAL-016 criteria have evidence; UNKNOWN in any evidence column forces FAIL or DEFERRED.

---

# 2. Country Pass/Fail Gate Criteria

Each country row is scored against the ten NAL-016 criteria. Record one line per criterion when assessing:

| # | Criterion (NAL-016) | Result Options | Rule |
|---|----------------------|----------------|------|
| 1 | Supplier ships there | PASS / FAIL / UNKNOWN | UNKNOWN counts as FAIL |
| 2 | Tracking exists | PASS / FAIL / UNKNOWN | UNKNOWN counts as FAIL |
| 3 | Delivery range verified | PASS / FAIL / UNKNOWN | Store display estimates are not evidence (U-15) |
| 4 | Shipping cost known | PASS / FAIL / UNKNOWN | Provisional store rates are not evidence (U-03) |
| 5 | Duties / tax documented | PASS / FAIL / UNKNOWN | UNKNOWN counts as FAIL (U-04) |
| 6 | Restrictions checked | PASS / FAIL / UNKNOWN | Must be checked per product category (NAL-013) |
| 7 | Return route and cost known | PASS / FAIL / UNKNOWN | "No returns possible" is FAIL (NAL-020) |
| 8 | Support readiness | PASS / FAIL / UNKNOWN | Assessed against NAL-019 capacity |
| 9 | Unit economics acceptable | PASS / FAIL / UNKNOWN | Per-Market NAL-011 calculation required (U-14) |
| 10 | Founder approval | APPROVED / PENDING / REJECTED | Only the Founder fills this line |

---

# 3. Deferred Market Register

Countries that fail or are consciously postponed are recorded here, never silently dropped.

| Country | Deferral Reason | Revisit Trigger |
|---------|-----------------|-----------------|
| [Example Only - Not Real] Sampleland | No supplier evidence for the route (U-09) | A supplier with tracked delivery to this country enters NAL-010 |
| [Example Only - Not Real] Examplia | Return route cost made unit economics unacceptable | Supplier or carrier change that lowers the return cost |

---

# 4. Market Activation Approval Record Format

One record per activated Market, created only after a PASS and a Founder approval. No record of this type can exist today.

| Field | Rule |
|-------|------|
| Country | The single country activated — one record per country |
| Gate evidence reference | Row in section 1 plus the ten criterion lines from section 2 |
| Landed-cost reference | The per-Market NAL-011 calculation ID used for criterion 9 |
| Approval Queue reference | NAL-014 queue ID and decision date |
| Founder decision | APPROVE / EDIT AND APPROVE / HOLD / REJECT |
| Activated by | The Founder personally, in Shopify — never the Partner (NAL-006) |
| Activation date | Date the Market went live |
| Post-activation review date | A set date to compare actual delivery and cost against the evidence |

---

# 5. Market Risk Register

| Risk ID | Market | Risk | Impact | Mitigation | Status |
|---------|--------|------|--------|------------|--------|
| [Example Only - Not Real] MR-001 | Sampleland | Duties charged to customer at delivery, causing refusals | Refused parcels, refund pressure, return cost | Document duty treatment before activation (criterion 5); state it on the store | OPEN (example) |
| [Example Only - Not Real] MR-002 | Examplia | Actual delivery time exceeds the verified range | Complaints, claims, trust damage | Post-activation review compares actual vs. evidence; pause recommendation if breached | OPEN (example) |

Risk rows are created during assessment and reviewed at the post-activation review date. A materialized risk can trigger a Market pause recommendation to the Founder (via NAL-021 exception handling where supplier-driven).

---

# 6. Register Rules

1. EXAMPLE ONLY rows are structure demonstrations, never data.
2. Every evidence cell holds a reference to recorded evidence (NAL-010, NAL-011, NAL-013) or UNKNOWN — never a guess.
3. Rows are never deleted; failed and deferred countries keep their history.
4. Real supplier names and quotes live in private storage per PODS-001; this public register holds structure and references.

---

# Related Documents

- NAL-010 / `10_Supplier_Evidence_Register.md`
- NAL-011 / `11_Landed_Cost_Calculator_Extension.md`
- NAL-013 / `13_Product_Claim_Verification.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-016 / `16_Market_Activation_Gate.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-020 / `20_Returns_and_Resolution_Workflow.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial template — register, gate criteria checklist, deferred register, approval record format, risk register |

---
