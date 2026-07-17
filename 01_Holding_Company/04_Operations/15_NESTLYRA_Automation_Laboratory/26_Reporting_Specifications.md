# NESTLYRA — Reporting Specifications

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. No report has been produced. Every metric below reconciles to a register in this folder — zero invented metrics, and every empty state reported honestly as empty.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-026 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Specify the Daily and Weekly reports the Founder receives once operations begin, so reporting is defined before the first order and every number in every report traces to a register row.

---

# Scope

Covers: report sections, sources, and honesty rules for the Daily and Weekly reports. Does not cover: report generation tooling (future work) or dashboards (a later sub-checkpoint).

---

# 1. Reporting Principles

1. Every figure reconciles to a named register in this folder. A number with no register row behind it does not appear.
2. Zero is reported as zero. UNKNOWN is reported as UNKNOWN. An empty register produces an honest "no entries" line, never a padded section.
3. No costs, margins, or delivery times appear until real data exists (U-14, U-15) — estimates are labeled as estimates with their NAL-011 calculation reference, and actuals come only from NAL-018 section 6.
4. Reports never contain customer personal data; they reference register IDs, with real data held per PODS-001.
5. The report is prepared for the Founder; it recommends and flags, it never self-approves anything (NAL-006).

---

# 2. Daily Report Specification

| # | Section | Content | Reconciles To |
|---|---------|---------|---------------|
| 1 | Orders status summary | Count by state: received, awaiting Founder approval, submitted to supplier, in transit, delivered, closed | NAL-018 First 20 Orders Register |
| 2 | Exceptions — open and closed today | Order exceptions and supplier exceptions, each with ID and one-line state | NAL-018 section 5; NAL-021 register |
| 3 | Approval queue state | Items waiting, oldest item age, items decided today | NAL-014 queue |
| 4 | Customer inquiries | Open, answered, follow-ups due | NAL-019 register |
| 5 | Returns in progress | Open return cases and their step | NAL-020 register |
| 6 | Launch-blocker status | OPEN count, any rows changed today | NAL-023 register |
| 7 | Honest empty state | Before launch, most sections read "No entries — store not launched." That is the correct report, not a failure of the report | All registers above |

---

# 3. Weekly Report Specification

| # | Section | Content | Reconciles To |
|---|---------|---------|---------------|
| 1 | Week's orders summary | Totals by state, week over week, within the First 20 control context | NAL-018 registers |
| 2 | Exceptions review | Opened/closed counts, patterns, any repeat scenario per supplier | NAL-018 section 5; NAL-021 register |
| 3 | Approval queue review | Decisions made, average wait, items held over a week | NAL-014 queue |
| 4 | Launch-blocker movement | Rows closed, rows added, rows unchanged — with the full OPEN count restated | NAL-023 register |
| 5 | Supplier score changes | Any score movement and the exception or return that caused it | NAL-009 register; NAL-020/NAL-021 records |
| 6 | Costs where known | Actual cost and margin per closed order; UNKNOWN until real data exists (U-14) — no projections presented as results | NAL-018 section 6 |
| 7 | Market readiness movement | Any change in assessment or deferral rows | NAL-017 register |
| 8 | Partner errors and corrections | New entries this week and follow-up changes made | NAL-027 log |
| 9 | Pending Founder decisions | One consolidated list of everything waiting on the Founder | NAL-014 queue |

---

# 4. Reconciliation Rule

Each report ends with a reconciliation line per section: the register name, the row count used, and the as-of timestamp. If a report figure and its register disagree, the register wins, the report is corrected, and the discrepancy is logged in NAL-027.

---

# Related Documents

- NAL-009 / `09_Supplier_Register.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-017 / `17_Market_Readiness_Register.md`
- NAL-018 / `18_First_20_Orders_Control.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-020 / `20_Returns_and_Resolution_Workflow.md`
- NAL-021 / `21_Supplier_and_Inventory_Exceptions.md`
- NAL-023 / `23_Launch_Blocker_Register.md`
- NAL-027 / `27_Partner_Error_and_Correction_Log.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial specifications — Daily and Weekly reports, reconciliation rule, honest empty states |

---
