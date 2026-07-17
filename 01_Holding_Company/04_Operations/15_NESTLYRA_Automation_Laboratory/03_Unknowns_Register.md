# NESTLYRA Automation Laboratory — Unknowns Register

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Everything in this register is NOT known. Nothing here may be assumed, estimated, or invented (STRAT-019 discipline).

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-003 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

List every material fact about the NESTLYRA Shopify store that is currently unverified, so no document, workflow, or automation design in this folder silently treats a guess as a fact.

---

# Scope

Covers: unknowns as of 2026-07-17, following the Current-State Audit (NAL-002). Does not cover: verified facts (those live in NAL-002) or business decisions not yet made (those belong to the Founder).

---

# 1. Register

| # | Unknown | Why It Matters | How It Gets Resolved | Status |
|---|---------|----------------|----------------------|--------|
| U-01 | Which Shopify apps are installed | Apps can change checkout, email, and order behavior; automation design cannot assume a clean slate | Founder screenshot of Apps and sales channels page (NAL-004 item 1) | UNKNOWN |
| U-02 | Exact shipping-zone countries | Two zones exist but their contents are unverified; Market and shipping planning cannot proceed on guesses | Founder screenshot of the open default shipping profile (NAL-004 item 2) | UNKNOWN |
| U-03 | Exact shipping rates | Rates drive landed cost and unit economics; no rate may be assumed | Founder screenshot of the open default shipping profile (NAL-004 item 2) | UNKNOWN |
| U-04 | Taxes and duties setup | Tax treatment affects pricing, margin, and legal exposure | Founder screenshot of Taxes and duties (NAL-004 item 3) | UNKNOWN |
| U-05 | Payment configuration | Payment state gates every order workflow; the store content package records payments as disconnected, but current Shopify payment settings are unverified | Founder screenshot of Payments (NAL-004 item 4) | UNKNOWN |
| U-06 | Domain readiness | Sender authentication and storefront trust depend on domain state | Founder screenshot of Domains (NAL-004 item 5) | UNKNOWN |
| U-07 | Notification-template content | Customer-facing wording must be reviewed before any real order exists | Founder screenshot of Customer notifications (NAL-004 item 7) | UNKNOWN |
| U-08 | Customer privacy configuration | Privacy settings must be verified before any customer data is processed | Founder screenshot of Customer privacy (NAL-004 item 6) | UNKNOWN |
| U-09 | Supplier integration | No supplier or dropshipping integration is confirmed; no integration may be assumed to exist or work | Supplier selection and evidence per the Product Approval Gate (NAL-007) | UNKNOWN |
| U-10 | Shopify plan tier | Plan tier gates which native features (for example Shopify Flow actions) are available | Founder confirmation from Shopify admin billing/plan page | UNKNOWN |
| U-11 | Exact list of the 27 countries/regions in the international shipping zone | Market gating, duties, and returns design need the actual country list, not the count | Founder screenshot of the open shipping profile showing the zone's country list (NAL-004 item 2) | UNKNOWN |
| U-12 | Exact Messaging app identity and behavior | "Messaging" appears on the Apps page but must not be assumed identical to Shopify Inbox; its auto-reply behavior could answer customers with unverified information | Founder screenshot of the Messaging app's own settings/details page | UNKNOWN |
| U-13 | Theme readiness | Storefront theme state is unverified; content-package copy (NESTLYRA-002..017) cannot be assumed installed or rendering correctly | Founder screenshot of current theme and storefront preview (NAL-004 item 9) | UNKNOWN |
| U-14 | Actual profitability of any product/route | No product, supplier, or landed cost exists; every economics figure is unknowable today | Product Approval Gate evidence (NAL-007) + Landed-Cost Calculator (NAL-011) | UNKNOWN |
| U-15 | Actual delivery performance | Displayed 3-5 day domestic / international estimates are provisional store settings, not measured performance; no order has ever shipped | Real tracked deliveries during the First 20 Orders control period | UNKNOWN |

---

# 2. Register Rules

1. An unknown leaves this register only when Founder-verified evidence arrives (screenshot or Founder statement), never by assumption.
2. When an unknown is resolved, the fact moves to the Current-State Audit (NAL-002) with its evidence date, and this row's status becomes RESOLVED with a date — the row itself is never deleted.
3. Any new document in this folder that depends on one of these items must reference the U-number and treat it as UNKNOWN until resolved.
4. Presenting any of these items as known, anywhere, is a violation of STRAT-019.

---

# Related Documents

- NAL-002 / `02_Current_State_Audit.md`
- NAL-004 / `04_Founder_Screenshot_Request_Checklist.md`
- STRAT-019 / `../../03_Strategy/AOS_Outreach_Writing_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial register — ten unknowns recorded, none resolved |
| 1.1 | 2026-07-17 | U-11 to U-15 added after the second Founder screenshot set (27-country zone list, Messaging app identity, theme readiness, actual profitability, actual delivery performance). U-01 partially narrowed by the Apps screenshot (Messaging visible; Flow/Forms not installed) but kept open pending the full apps-page screenshot per NAL-004 item 1. |

---
