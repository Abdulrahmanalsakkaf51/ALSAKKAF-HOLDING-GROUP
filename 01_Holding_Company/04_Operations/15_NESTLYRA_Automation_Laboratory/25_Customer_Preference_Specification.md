# NESTLYRA — Customer Preference Specification

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. No customer exists and no preference has ever been collected. This specification defines transparent, editable customer preferences — nothing hidden, nothing inferred, nothing manipulative.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-025 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Define exactly which customer preferences NESTLYRA may hold, where each would live in native Shopify storage, and the rules that keep the whole system transparent and customer-controlled.

---

# Scope

Covers: the preference fields, their native storage mapping (per the NAL-024 catalogue), and the collection rules. Does not cover: implementation — storage definitions and forms are NAL-024 entries (A5, A8, A9, A10), each PROPOSED — NOT INSTALLED — NOT ACTIVE behind its own Founder approval gate.

---

# 1. Preference Fields and Native Storage Mapping

| # | Preference | What It Holds | Native Storage (per NAL-024) | Source |
|---|-----------|----------------|------------------------------|--------|
| 1 | Preferred language | Customer's chosen communication language | Customer metafield (Entry A9) | Declared by the customer |
| 2 | Destination country | Where the customer usually ships to | Customer metafield (Entry A9) | Declared, or from an actual order address |
| 3 | Storage / organization problem | The problem they want solved (declared in their words or picked from options) | Customer tag from taxonomy (Entry A8), captured via form (Entry A5) | Declared |
| 4 | Product categories of interest | Which NESTLYRA categories interest them | Customer tags (Entry A8) | Declared |
| 5 | Wardrobe / storage type | Their storage situation (e.g., small wardrobe, no wardrobe, shared space) | Customer tag from taxonomy (Entry A8) | Declared |
| 6 | Style or colour preference | Declared aesthetic preference | Customer tag or metafield (Entries A8/A9) | Declared |
| 7 | Communication consent | Whether NESTLYRA may contact them beyond order emails — with consent version and date | Customer metafield (Entry A9); gates the consented segment (Entry A10) | Explicit opt-in only |
| 8 | Preferred communication channel | Email or other channel they choose | Customer metafield (Entry A9) | Declared |
| 9 | Order history | Their own past orders | Native Shopify order records — no copy is made | System of record |
| 10 | Support history | Their own past inquiries and resolutions | Customer Inquiry Register (NAL-019) references; real data per PODS-001 | System of record |

---

# 2. Rules

1. No sensitive information is collected — nothing about health, beliefs, finances, family composition, precise location beyond a shipping address, or anything a storage-products store has no business knowing.
2. No hidden profiling. Every stored preference is declared by the customer or is their own order/support record. Nothing is inferred behind their back, and there is no shadow scoring of any kind.
3. No manipulative personalization. Preferences may make the store more useful (relevant categories, right language); they may never be used for pressure, false scarcity, or exploiting a stated problem.
4. No personalized pricing, ever. Every customer sees the same price. Preferences never touch pricing (consistent with NAL-006: prices are Founder decisions).
5. The customer can view, edit, and delete their preferences. Deletion requests are honored fully — tags and metafields removed — with only the legally required order records retained.
6. Consent is recorded with version and date (Entry A9). A consent-text change means re-consent; old consent does not stretch to cover new uses.
7. Collection is always optional. Declining to state any preference costs the customer nothing.
8. Real preference data, when it exists, is operational customer data handled per PODS-001; this public specification holds structure only.

---

# 3. Honest Current State

| Item | State |
|------|-------|
| Preferences collected to date | None — no customer exists |
| Storage defined in Shopify | None — Entries A5/A8/A9/A10 are PROPOSED — NOT INSTALLED — NOT ACTIVE |
| Consent text | Not written — required before any collection, Founder-approved via NAL-014 |
| Customer privacy configuration | UNVERIFIED (U-08) — collection cannot begin before it is verified |

---

# Related Documents

- NAL-003 / `03_Unknowns_Register.md` (U-08)
- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-024 / `24_Shopify_Native_Automation_Catalogue.md` (Entries A5, A8, A9, A10)
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial specification — ten preference fields, native storage mapping, eight rules |

---
