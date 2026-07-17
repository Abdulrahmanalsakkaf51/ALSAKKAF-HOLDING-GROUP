# NESTLYRA Automation Laboratory — Current-State Audit

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. This document records only what was verified from Founder screenshots on 2026-07-17. Nothing here was changed, and nothing here authorizes a change.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-002 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Record the verified current configuration of the NESTLYRA Shopify store exactly as observed, so every later design decision in this folder traces to an evidenced starting point rather than an assumption.

---

# Scope

Covers: only the settings listed below, verified from Founder screenshots, 2026-07-17. No Shopify access by Claude or any AI system occurred; every fact below comes from screenshots the Founder personally captured and shared.

Does not cover: anything not listed below. Every unlisted setting is treated as UNKNOWN and lives in `03_Unknowns_Register.md` (NAL-003). This document must never be extended by inference — only by new Founder-verified evidence.

---

# 1. Verification Basis

| Field | Value |
|-------|-------|
| Evidence source | Founder screenshots |
| Evidence date | 2026-07-17 |
| Verified by | Abdulrahman Alsakkaf (Founder) |
| Shopify accessed by AI | No — at no point |
| Changes made | None |

---

# 2. Customer Accounts (verified from Founder screenshots, 2026-07-17)

| Setting | Verified State |
|---------|----------------|
| Sign-in links | Enabled |
| Sign-in required before checkout | No — customers are not required to sign in |
| Self-service returns | Disabled |
| Store credit | Appears enabled |
| Account URL | Shopify-hosted account URL |

No changes are to be made to customer accounts yet.

---

# 3. Markets (verified from Founder screenshots, 2026-07-17)

| Setting | Verified State |
|---------|----------------|
| Active Markets | United Arab Emirates only |
| EU | Appears only as suggested — not active |
| US | Appears only as suggested — not active |
| Other Markets | No other Market confirmed active |

Hard rule: do not create or activate another Market. Market activation is governed by `16_Market_Activation_Gate.md` (NAL-016) and requires Founder approval.

---

# 4. Shipping (verified from Founder screenshots, 2026-07-17 — second screenshot set)

| Setting | Verified State |
|---------|----------------|
| Shipping profiles | One general/default profile applying to all products |
| Fulfillment location | United Arab Emirates |
| Domestic UAE rate | Appears to be AED 25 — PROVISIONAL / UNVERIFIED |
| Free shipping | Appears configured for orders AED 200 and above — PROVISIONAL / UNVERIFIED |
| Displayed domestic estimate | Appears to be 3-5 business days — PROVISIONAL / UNVERIFIED |
| International zone | One zone containing 27 countries or regions — the exact country list is UNKNOWN |
| International rate | Appears to be AED 70 — PROVISIONAL / UNVERIFIED |
| Shopify warning | Those countries must be included in a Market; since UAE is the only active Market, international checkout availability is NOT confirmed |
| Estimated delivery dates (feature) | Otherwise disabled |
| Shipping-label provider | None |
| Connected carrier accounts | None |
| Local delivery | Disabled |
| Store pickup | Disabled |
| Products | None exist |

**Provisional rule:** every shipping rate and delivery time above is PROVISIONAL — UNVERIFIED. None can be approved until supplier, product dimensions, weight, tracking, duties, returns, and landed costs are verified through the product approval gate (NAL-007).

---

# 4a. Apps (verified from Founder screenshots, 2026-07-17)

| Setting | Verified State |
|---------|----------------|
| Apps shown on Apps page | Messaging only |
| Shopify Flow | Not shown as installed |
| Shopify Forms | Not shown as installed |
| Supplier / dropshipping apps | None shown |

Caution: do not assume "Messaging" is identical to Shopify Inbox until its exact app details are inspected in a later Founder screenshot.

---

# 4b. Sales Channels (verified from Founder screenshots, 2026-07-17)

| Setting | Verified State |
|---------|----------------|
| Online Store | Installed |
| Point of Sale | Installed |
| POS Pro trial | A notification states the trial will end and automatically switch to POS Lite |
| Founder position | POS Pro was not requested; no physical retail sales are currently intended |

Hard rule: do not purchase, continue, configure, or remove POS during Checkpoint A. Later recommendation (recorded, not actioned): after the trial ends, verify the automatic downgrade to POS Lite occurred, then consider removing the POS sales channel entirely since no physical retail is planned.

---

# 5. Checkout (verified from Founder screenshots, 2026-07-17)

| Setting | Verified State |
|---------|----------------|
| Contact method | Email |
| Shop order-tracking link | Enabled |
| Sign-in required before checkout | Not required |
| Customer name | First and last name required |
| Company name | Not collected |
| Address line 2 | Optional |
| Shipping-address phone | Optional |

---

# 6. Notifications (verified from Founder screenshots, 2026-07-17)

| Setting | Verified State |
|---------|----------------|
| Current sender email | The Founder's personal company address (generalized here per the PRJ-020 privacy rule — exact address held in Founder records) |
| Intended temporary support address | hello@alsakkafsystems.com |
| Email-domain authentication | NEEDS SETUP |
| DMARC | Incomplete |
| Fallback sender | Shopify may currently fall back to its shopifyemail.com sender |

Hard rule: do not change the sender. A safe recommendation only is prepared in `22_Email_Readiness.md` (NAL-022).

---

# 7. Products and Suppliers (verified from Founder screenshots, 2026-07-17)

| Setting | Verified State |
|---------|----------------|
| Products | None exist |
| Supplier integration | No supplier or dropshipping integration confirmed |

---

# 8. Policies (verified from Founder screenshots, 2026-07-17)

| Policy | Verified State |
|--------|----------------|
| Return / refund policy | None |
| Terms of Service | None |
| Shipping policy | None |
| Legal notice | None |
| Return and cancellation rules | None |
| Privacy policy | Automated (Shopify-generated) |
| Contact information | Marked required / incomplete |

Draft policy text already exists in the NESTLYRA content package (NESTLYRA-007 to NESTLYRA-010) but has not been published to Shopify and requires legal review before publication.

---

# 9. Audit Rule

1. This document records observations, not intentions. Plans live in the other NAL documents.
2. Anything not listed above is UNKNOWN and must be treated as UNKNOWN — see `03_Unknowns_Register.md` (NAL-003).
3. This audit is refreshed only from new Founder screenshots (see `04_Founder_Screenshot_Request_Checklist.md`, NAL-004), never from memory or assumption.

---

# Related Documents

- NAL-003 / `03_Unknowns_Register.md`
- NAL-004 / `04_Founder_Screenshot_Request_Checklist.md`
- NAL-023 / `23_Launch_Blocker_Register.md`
- NESTLYRA-001 / `../14_NESTLYRA_Store/README.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial audit from Founder screenshots dated 2026-07-17 |
| 1.1 | 2026-07-17 | Second Founder screenshot set incorporated: Apps (Messaging only; Flow/Forms not installed), Sales Channels (Online Store + POS, POS Pro trial ending to POS Lite, later-review recommendation recorded), detailed shipping (UAE fulfillment, provisional AED 25 domestic / free at AED 200+ / 3-5 day estimate / 27-country international zone at provisional AED 70, international checkout unconfirmed since UAE is the only active Market). Sender email generalized per the PRJ-020 privacy rule. |

---
