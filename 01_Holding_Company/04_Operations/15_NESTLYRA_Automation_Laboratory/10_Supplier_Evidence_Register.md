# NESTLYRA — Supplier Evidence Register (Template)

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Template with EXAMPLE ONLY rows. Evidence descriptions only appear here in generic form; the evidence itself (screenshots, quotes, correspondence) lives in private storage per PODS-001.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-010 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Record every piece of supplier evidence with its source URL type, capture date, and what it proves — so Gate Stages 2, 3, and 8 of NAL-007 (supplier identity, source and date, tracked-delivery evidence) rest on dated evidence, never on memory.

---

# Scope

Covers: evidence register structure and freshness rules. Does not cover: the evidence artifacts themselves (private per PODS-001).

---

# 1. Register Table

| Evidence ID | Supplier Ref | Evidence Type | What It Proves | Source Type | Evidence Date | Private Storage Path | Freshness Status |
|-------------|--------------|---------------|----------------|-------------|---------------|----------------------|------------------|
| EXAMPLE-EV-001 | EXAMPLE-SUP-001 | Product listing capture | [Example Only - Not Real] listed specifications and price at capture date | Supplier platform listing URL | 2026-07-17 | [Example Only - Not Real] private path placeholder | Fresh (example) |
| EXAMPLE-EV-002 | EXAMPLE-SUP-001 | Tracked-delivery proof | [Example Only - Not Real] a tracked shipment reached the target country within a stated range | Carrier tracking record | 2026-07-17 | [Example Only - Not Real] private path placeholder | Fresh (example) |

---

# 2. Evidence Types Required by the Product Approval Gate

| Gate Stage | Required Evidence Type |
|------------|------------------------|
| 2 | Supplier identity: business registration or verified platform storefront record |
| 3 | Source URL and capture date for every specification and price used anywhere |
| 8 | Tracked-delivery evidence: at least one tracked shipment to the target country with real transit time |

---

# 3. Rules

1. Every evidence row carries a date. Undated evidence is not evidence.
2. Freshness rule: price and availability evidence older than 30 days is Stale and must be re-captured before any calculation or approval uses it. Identity evidence older than 12 months is Stale.
3. Evidence proves only what it proves. A listing screenshot proves what was listed on that date — not that the product matches the listing (that is what samples are for, NAL-012).
4. Source URLs that identify a specific supplier company are recorded in the private evidence file, not here — this register holds the source type and date only (PODS-001).

---

# Related Documents

- NAL-007 / `07_Product_Approval_Gate.md`
- NAL-009 / `09_Supplier_Register.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial template with EXAMPLE ONLY rows and freshness rules |

---
