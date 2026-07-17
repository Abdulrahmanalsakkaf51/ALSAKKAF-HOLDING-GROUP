# NESTLYRA — Launch Blocker Register

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. Every blocker below is OPEN. The store cannot launch, and nothing in this folder may be read as launch progress while any row is OPEN.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-023 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Hold, in one place, every condition that blocks NESTLYRA from launching, each with an owner and a defined clearing condition — so launch readiness is a matter of record, never of mood.

---

# Scope

Covers: launch blockers, their owners, and how each clears. Does not cover: the step-by-step go-live procedure — the existing Launch Readiness Checklist (NESTLYRA-022) is the companion go-live checklist and is not duplicated here. This register says what blocks launch; NESTLYRA-022 walks the Founder through go-live once nothing does.

---

# 1. Blocker Register

| # | Blocker | Why It Blocks Launch | Owner | How It Clears | Status |
|---|---------|----------------------|-------|---------------|--------|
| 1 | No products | A store with nothing to sell cannot launch | Founder | A product passes all 16 stages of NAL-007 | OPEN |
| 2 | No supplier | Nothing can be fulfilled (U-09) | Founder | Supplier selected with evidence in NAL-009/NAL-010 | OPEN |
| 3 | No samples | Mandatory sample stage never performed | Founder | Sample ordered (NAL-014 spend approval) and received | OPEN |
| 4 | No verified specifications | Product pages would state unverified claims | Founder | Specifications evidenced in NAL-008; no [VERIFY BEFORE LAUNCH] markers remain | OPEN |
| 5 | No product evidence | No claim on any page is currently supportable | Founder | NAL-013 claim verification passed for every published claim | OPEN |
| 6 | No verified shipping | Routes, times, and tracking are unevidenced (U-15) | Founder | Tracked-delivery evidence in NAL-010 for every live Market | OPEN |
| 7 | No verified landed cost | Selling blind on cost risks loss per order (U-14) | Founder | NAL-011 calculation with evidenced inputs per product and Market | OPEN |
| 8 | No refund policy | Legally and commercially required; none published | Founder + legal review | NESTLYRA-008 legally reviewed and published | OPEN |
| 9 | No shipping policy | Same | Founder + legal review | NESTLYRA-007 legally reviewed and published | OPEN |
| 10 | No Terms of Service | Same | Founder + legal review | NESTLYRA-010 legally reviewed and published | OPEN |
| 11 | No legal notice | Required legal identity page absent | Founder + legal review | Legal notice prepared after entity selection and published | OPEN |
| 12 | Incomplete contact information | Shopify marks contact info required/incomplete (NAL-002 section 8) | Founder | Contact information completed in Shopify | OPEN |
| 13 | Email authentication incomplete | Order emails unreliable (NAL-022 blocker 1) | Founder | Sender domain authenticated per the option chosen from NAL-022 | OPEN |
| 14 | DMARC incomplete | Spoofing exposure and deliverability risk (NAL-022 blocker 2) | Founder | DMARC completed for the chosen sending domain | OPEN |
| 15 | Shipping rates provisional | AED 25 / AED 70 / free-over-200 are PROVISIONAL — UNVERIFIED (U-03) | Founder | Rates re-set from verified route costs and approved | OPEN |
| 16 | International Market inactive | 27-country zone without a Market — international checkout unconfirmed (U-11) | Founder | Either international Markets pass NAL-016, or international scope is explicitly deferred at launch | OPEN |
| 17 | Taxes / duties unverified | Tax treatment unknown (U-04) | Founder | Taxes and duties configuration verified by Founder screenshot and recorded in NAL-002 | OPEN |
| 18 | Payments unverified | Payment state unknown; package records payments disconnected (U-05) | Founder | Payment configuration verified, connected, and test-transaction confirmed | OPEN |
| 19 | Customer privacy configuration unverified | Privacy settings unconfirmed (U-08) | Founder | Customer privacy settings verified by Founder screenshot and recorded in NAL-002 | OPEN |
| 20 | App inventory not fully verified | Unknown apps could alter checkout or email behavior (U-01) | Founder | Full apps-page verification recorded in NAL-002 | OPEN |
| 21 | Messaging behavior unverified | Unknown auto-replies could answer customers with unverified facts (U-12) | Founder | Messaging app identity and behavior verified; configuration Founder-approved | OPEN |
| 22 | POS channel not needed and pending later review | An unreviewed sales channel should not ride into launch (NAL-002 section 4b) | Founder | Post-trial downgrade verified, then keep-or-remove decision recorded | OPEN |
| 23 | No customer-support knowledge base | Support would answer from memory, violating NAL-019 verified-information rule | Founder | Verified-facts knowledge base assembled from evidenced registers | OPEN |
| 24 | No synthetic workflow test completed | The designed workflows have never been exercised end to end | Founder | Synthetic acceptance test pack (later sub-checkpoint) executed and passed | OPEN |
| 25 | No Founder launch approval | Launch is a Founder decision, recorded, never implied | Founder | Founder records launch approval after rows 1-24 close and NESTLYRA-022 completes | OPEN |

---

# 2. Register Rules

1. A blocker closes only with evidence and a Founder-confirmed record — never because time passed or work happened nearby.
2. Closed rows keep their row with status CLOSED and a closure date; rows are never deleted.
3. New blockers may be added at any time; discovering a blocker late is a win for the register, not a failure.
4. Row 25 is always the last to close. No partial launch, soft launch, or "just unlock the password" bypasses this register.
5. This register and NESTLYRA-022 travel together: this register gates whether launch may proceed; NESTLYRA-022 governs how go-live is executed when it may.

---

# Related Documents

- NAL-002 / `02_Current_State_Audit.md`
- NAL-003 / `03_Unknowns_Register.md`
- NAL-007 / `07_Product_Approval_Gate.md`
- NAL-016 / `16_Market_Activation_Gate.md`
- NAL-022 / `22_Email_Readiness.md`
- NESTLYRA-022 / `../14_NESTLYRA_Store/22_Launch_Readiness_Checklist.md` (companion go-live checklist)

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial register — twenty-five blockers, all OPEN |

---
