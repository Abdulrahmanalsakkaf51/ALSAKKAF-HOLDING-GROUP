# NESTLYRA — Supplier Register (Template)

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Template with EXAMPLE ONLY rows. No supplier is selected. Real supplier identities, quotes, and contacts live in private storage per PODS-001 — never in this file.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-009 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Track supplier candidates by anonymous reference ID, their verification state, and their link to product candidates — complementing the side-by-side Supplier Comparison Sheet (NESTLYRA-019), which compares offers, while this register tracks identity verification and status over time.

---

# Scope

Covers: register structure, column guide, rules. Does not cover: real supplier data (private per PODS-001) or offer-by-offer comparison (NESTLYRA-019 owns that).

---

# 1. Register Table

| Supplier Ref | Date Registered | Private Record Path | Candidate Products | Identity Verified | Business Registration Evidence | Communication Channel Verified | Sample Provided | Status | Next Action |
|--------------|-----------------|---------------------|--------------------|-------------------|-------------------------------|-------------------------------|-----------------|--------|-------------|
| EXAMPLE-SUP-001 | 2026-07-17 | [Example Only - Not Real] private path placeholder | EXAMPLE-PC-001 | No | None on file | No | No | Candidate | Collect identity evidence (NAL-010) |

---

# 2. Column Guide

| Column | Rule |
|--------|------|
| Supplier Ref | Anonymous sequential SUP-xxx; the real name maps to this ref only inside private storage (PODS-001 rule 4) |
| Private Record Path | Path in ALSAKKAF PRIVATE OPERATIONS where the real identity and correspondence live |
| Identity Verified | Yes only when NAL-010 holds dated evidence of who the supplier actually is |
| Business Registration Evidence | What proof of legal existence is on file (described generically here; stored privately) |
| Status | Candidate, Evidence Gathering, Verified, Selected (Founder decision), Rejected, Suspended |
| Next Action | One concrete next step, always |

---

# 3. Rules

1. No supplier is Selected without Founder approval recorded in NAL-014.
2. Supplier names, URLs identifying a specific company, prices, and contact details never appear in this public file — reference IDs only.
3. A supplier with stale evidence (older than the evidence-freshness rule in NAL-010) drops back to Evidence Gathering.
4. One verified supplier is not enough for launch confidence; the Founder decides how many verified options a product needs, using NESTLYRA-019 for comparison.

---

# Related Documents

- NESTLYRA-019 / `../14_NESTLYRA_Store/19_Supplier_Comparison_Sheet.md`
- NAL-010 / `10_Supplier_Evidence_Register.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial template with EXAMPLE ONLY row |

---
