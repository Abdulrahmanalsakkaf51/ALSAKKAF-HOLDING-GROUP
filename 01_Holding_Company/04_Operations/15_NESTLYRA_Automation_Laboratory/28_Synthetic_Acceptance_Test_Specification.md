# NESTLYRA — Synthetic Acceptance-Test Specification

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. This is a test **specification** only. No live Shopify simulator or integration is built during Checkpoint A. Every record described below is fictional and labeled SYNTHETIC.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-028 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Define exactly how the PRJ-020 workflows and registers will be exercised with fictional data before any live automation, order, or customer exists — so approval gates, exception handling, and honesty rules are proven on paper first.

---

# Scope

Covers: the synthetic scenario set, the pass criteria, and how results are recorded. Does not cover: running the tests (a later checkpoint, after Founder review of this specification) or any live Shopify behavior.

---

# 1. Synthetic Scenario Register

Every scenario uses clearly-fictional data (SYNTHETIC- prefixed IDs, fictional names like "Synthetic Customer 01", no real addresses, no real supplier). Each scenario names the workflow it exercises and the register rows it must produce.

| # | Scenario | Count | Exercises | Must Produce |
|---|----------|-------|-----------|--------------|
| S-01 | Normal synthetic orders | 10 | First 20 Orders Control (NAL-018) end to end | 10 order records, 10 Founder-approval entries, 10 closed orders with cost-and-lesson rows |
| S-02 | Customer inquiries (one per category sample) | 5 | Customer Care Workflow (NAL-019) | 5 inquiry records, 5 drafted responses awaiting Founder approval, 0 sent messages |
| S-03 | Return requests | 3 | Returns and Resolution (NAL-020) | 3 return records with reason classes, resolution options, Founder decisions; 0 automatic refunds |
| S-04 | Stock-outs | 2 | Supplier Exceptions (NAL-021) | 2 exception records with customer-impact assessment and Founder decision |
| S-05 | Incomplete addresses | 2 | Order Control address check (NAL-018) | 2 held orders with drafted (unsent) clarification requests |
| S-06 | Delayed shipment | 1 | Exceptions + customer care | 1 exception record + 1 drafted (unsent) customer update |
| S-07 | Suspicious order | 1 | Order Control risk flag (NAL-018) | 1 flagged order held for Founder decision — no automatic cancellation |
| S-08 | Supplier price increase | 1 | Supplier Exceptions + Landed-Cost recalculation (NAL-011) | 1 exception with margin recalculation and pause recommendation |
| S-09 | Unsupported destination | 1 | Market gate check (NAL-016/017) | 1 rejected-at-eligibility order with recorded reason |
| S-10 | Customer preference update | 1 | Customer Preference spec (NAL-025) | 1 preference change with consent version and audit entry |
| S-11 | Customer preference removal | 1 | Customer Preference spec (NAL-025) | 1 removal honored and recorded |
| S-12 | Damaged product | 1 | Returns + supplier score (NAL-020/021) | 1 resolution record + supplier score update |
| S-13 | Wrong product | 1 | Returns + supplier score | 1 resolution record + root cause + supplier score update |
| S-14 | Tracking failure | 1 | Supplier Exceptions (NAL-021) | 1 exception with escalation path and Founder decision |

---

# 2. Pass Criteria

The synthetic run passes only if ALL of the following hold:

1. No unauthorized external action occurred or was simulated as automatic — every send, order, refund, and publish step stopped at a Founder gate.
2. No invented product claim appeared anywhere in any draft.
3. No invented shipping claim appeared — provisional rates stayed marked PROVISIONAL (U-03) and unverified estimates stayed UNKNOWN (U-15).
4. No cross-customer exposure — no synthetic customer's record referenced another's data.
5. Every exception has an owner and a status.
6. Financial, publishing, and refund actions remained Founder-controlled in every scenario.
7. Every event produced a log/register entry.
8. Synthetic reports (NAL-026/NAL-029) reconcile exactly to the register rows — no unexplained numbers.
9. Missing facts remained UNKNOWN or PENDING — zero fabricated values.
10. Partner mistakes and Founder corrections were recorded in NAL-027.

A single violated criterion fails the run; the failure is recorded in NAL-027 and NAL-030, corrected, and the affected scenarios re-run.

---

# 3. Execution Rules (for the later checkpoint that runs this)

1. Founder reviews and approves this specification before any run.
2. Runs are paper/spreadsheet exercises against the register templates — no Shopify connection, no live app, no real email.
3. Results are recorded per scenario: PASS / FAIL / BLOCKED, with evidence rows.
4. The completed run report goes to the Founder Approval Queue (NAL-014) before Checkpoint B planning.

---

# Related Documents

- NAL-018 / `18_First_20_Orders_Control.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-020 / `20_Returns_and_Resolution_Workflow.md`
- NAL-021 / `21_Supplier_and_Inventory_Exceptions.md`
- NAL-025 / `25_Customer_Preference_Specification.md`
- NAL-026 / `26_Reporting_Specifications.md`
- NAL-027 / `27_Partner_Error_and_Correction_Log.md`
- NAL-029 / `29_Extended_Report_Specifications.md`
- NAL-030 / `30_Lessons_and_Improvement_Register.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial synthetic acceptance-test specification — 14 scenario groups, 10 pass criteria |

---
