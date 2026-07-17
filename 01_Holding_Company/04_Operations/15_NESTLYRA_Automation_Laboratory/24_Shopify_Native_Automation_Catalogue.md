# NESTLYRA — Shopify Native Automation Catalogue

Status: PROPOSED — NOT INSTALLED — NOT ACTIVE. Every entry below is a design on paper. Shopify Flow and Shopify Forms are not currently installed (NAL-002 section 4a). Nothing may be installed, enabled, or configured without Founder approval, and every entry's plan requirement is UNKNOWN until the Shopify plan tier is verified (U-10).

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-024 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft — Proposed, not installed, not active |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Catalogue an AED 0, native-first automation plan built only from Shopify's own capabilities — Flow, Forms, Customer Accounts, Messaging/Inbox, customer tags, customer metafields, customer segments, order triggers, fulfillment triggers, and Markets — so that when automation is eventually approved, it uses free native tools before any paid app is even discussed.

---

# Scope

Covers: the proposed automation entries and the mandatory specification fields each must carry. Does not cover: installation, activation, or testing — every entry stops at its Founder approval gate, and live activation additionally requires the Launch Blocker Register (NAL-023) context to permit it.

---

# 1. Catalogue Rules

1. Every entry is PROPOSED — NOT INSTALLED — NOT ACTIVE, permanently, until a Founder approval record says otherwise per entry.
2. Expected cost for every entry is AED 0 — native features only. Any future entry that would cost money is out of scope for this catalogue.
3. Shopify plan requirement is UNKNOWN (U-10) for every entry until the plan tier is verified; an entry that turns out to need a higher plan is re-costed and re-queued, never silently upgraded.
4. No automation ever performs a forbidden action from NAL-006 — no sending, spending, publishing, pricing, refunding, or Market activation. Native automations here tag, record, segment, and notify the Founder/staff only.
5. Every entry must pass its synthetic test (on fake data, store unlaunched) before its live activation gate is even eligible for the queue.

---

# 2. Entry A1 — Flow: New-Order Control Tag

| Field | Specification |
|-------|---------------|
| Automation name | New-Order Control Tag |
| Purpose | Tag every incoming order for the First 20 Orders control so none slips past manual handling |
| Trigger | Order created |
| Conditions | Order count within control period (first 20 real orders, tracked via NAL-018 register) |
| Actions | Add order tag `first-20-control` |
| Data used | Order ID, order tags |
| Owner | Founder (Partner may monitor the tag, PROPOSED) |
| Founder approval gate | Flow installation + this workflow's activation, each a separate NAL-014 item |
| Failure mode | Tag not applied — order handled manually anyway; NAL-018 register remains the source of truth |
| Rollback | Deactivate the workflow; remove tags |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Fake order created in test conditions receives the tag; register cross-check matches |
| Live activation gate | Founder approval after synthetic pass; store launch state per NAL-023 |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 3. Entry A2 — Flow: High-Risk Order Alert

| Field | Specification |
|-------|---------------|
| Automation name | High-Risk Order Alert |
| Purpose | Surface Shopify's own risk assessment to the Founder immediately (NAL-018 step 4) |
| Trigger | Order risk analyzed |
| Conditions | Risk level medium or high |
| Actions | Add order tag `risk-review`; send internal staff notification to the Founder |
| Data used | Order ID, Shopify risk level |
| Owner | Founder |
| Founder approval gate | Activation via NAL-014; internal notification only — never a customer message |
| Failure mode | Alert missed — NAL-018 step 4 manual check still runs on every order |
| Rollback | Deactivate workflow; remove tags |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Simulated risk condition produces tag and internal notification, nothing customer-facing |
| Live activation gate | Founder approval after synthetic pass |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 4. Entry A3 — Flow: Unfulfilled-Order Aging Alert

| Field | Specification |
|-------|---------------|
| Automation name | Unfulfilled-Order Aging Alert |
| Purpose | Flag orders still unfulfilled after a Founder-set number of days, feeding the delayed-dispatch exception (NAL-021 scenario 3) |
| Trigger | Scheduled/wait step after order creation |
| Conditions | Order unfulfilled after N days (N set by Founder; no value proposed — supplier dispatch evidence does not exist yet, U-09) |
| Actions | Add order tag `aging-unfulfilled`; internal staff notification |
| Data used | Order ID, fulfillment status, order age |
| Owner | Founder |
| Founder approval gate | Activation via NAL-014 |
| Failure mode | Missed alert — NAL-018 step 15 manual monitoring continues regardless |
| Rollback | Deactivate workflow; remove tags |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Backdated fake order crosses threshold and produces tag plus internal notification |
| Live activation gate | Founder approval after synthetic pass |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 5. Entry A4 — Fulfillment Trigger: Tracking-Recorded Checkpoint

| Field | Specification |
|-------|---------------|
| Automation name | Tracking-Recorded Checkpoint |
| Purpose | When fulfillment is created with tracking, tag the order as ready for a customer-update draft (NAL-018 steps 11-12) |
| Trigger | Fulfillment created |
| Conditions | Tracking number present |
| Actions | Add order tag `tracking-recorded`; internal staff notification prompting a draft — the draft and send remain fully manual per NAL-019 |
| Data used | Order ID, fulfillment and tracking fields |
| Owner | Founder |
| Founder approval gate | Activation via NAL-014; explicitly does NOT enable any automatic customer notification beyond Shopify's standard order emails, which are themselves gated by email readiness (NAL-022) |
| Failure mode | Tag missed — manual NAL-018 step 11 still records tracking |
| Rollback | Deactivate workflow; remove tags |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Fake fulfillment with tracking produces the tag and internal prompt only |
| Live activation gate | Founder approval after synthetic pass |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 6. Entry A5 — Forms: Storage-Problem Preference Form

| Field | Specification |
|-------|---------------|
| Automation name | Storage-Problem Preference Form |
| Purpose | Let customers voluntarily state their storage/organization problem and interests (NAL-025 preferences 3-5), transparently |
| Trigger | Customer submits the form (Shopify Forms, not currently installed) |
| Conditions | Explicit consent checkbox ticked; form states exactly what is stored and why |
| Actions | Apply customer tags from the declared answers; record consent metafield with version and date |
| Data used | Declared preferences only — no inferred data (NAL-025 rules) |
| Owner | Founder |
| Founder approval gate | Forms installation + form content + tag taxonomy, each via NAL-014 |
| Failure mode | Form unavailable — nothing is lost; preferences are optional by design |
| Rollback | Unpublish form; remove tags/metafields on request per NAL-025 deletion right |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Fake submission produces correct tags, consent metafield, and nothing else |
| Live activation gate | Founder approval after synthetic pass; consent wording reviewed first |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 7. Entry A6 — Customer Accounts: Self-Service Order Status

| Field | Specification |
|-------|---------------|
| Automation name | Self-Service Order Status |
| Purpose | Let signed-in customers see their own order status natively, reducing order-status inquiries (NAL-019 category 3) |
| Trigger | Customer signs into the Shopify-hosted account (sign-in links already enabled per NAL-002 section 2) |
| Conditions | None beyond Shopify's own authentication |
| Actions | Native display of the customer's own orders — no configuration adds any data exposure |
| Data used | The customer's own orders only |
| Owner | Founder |
| Founder approval gate | Any settings change to customer accounts via NAL-014; current settings stay untouched until then |
| Failure mode | Customer cannot see status — falls back to a NAL-019 inquiry |
| Rollback | Revert account settings |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Test account sees only its own synthetic orders |
| Live activation gate | Founder approval; customer privacy verification (U-08) must be resolved first |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 8. Entry A7 — Messaging/Inbox: Reviewed Saved Replies (Verification-Gated)

| Field | Specification |
|-------|---------------|
| Automation name | Reviewed Saved Replies |
| Purpose | Speed up Founder-sent replies with pre-approved snippets — only after the Messaging app's exact identity and behavior are verified (U-12) |
| Trigger | Manual — the Founder selects a saved reply while answering |
| Conditions | Only NAL-019-approved wording; every fact in a snippet traces to a verified register |
| Actions | Insert text for the Founder to review and send manually — no auto-reply, no instant answers |
| Data used | Approved wording library only |
| Owner | Founder |
| Founder approval gate | U-12 verification first, then snippet library approval via NAL-014. Any auto-reply or "instant answer" feature stays OFF — this entry explicitly excludes autonomous responses (NAL-019 rule 2) |
| Failure mode | Snippet outdated — snippets carry a review date and expire from use when stale |
| Rollback | Delete snippets; disable nothing else because nothing else was enabled |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Snippet content audit against verified registers; confirmation no auto-send path exists in the verified app |
| Live activation gate | Founder approval after U-12 resolves |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 9. Entry A8 — Customer Tags: Preference Tag Taxonomy

| Field | Specification |
|-------|---------------|
| Automation name | Preference Tag Taxonomy |
| Purpose | One controlled tag vocabulary for declared preferences (NAL-025), so segments stay clean and auditable |
| Trigger | Applied by Entry A5 form submissions or manually by the Founder |
| Conditions | Tags only from the approved taxonomy; only from declared, consented preferences |
| Actions | Add/remove customer tags |
| Data used | Declared preferences only |
| Owner | Founder |
| Founder approval gate | Taxonomy approval via NAL-014 before any tag is used |
| Failure mode | Tag drift — quarterly taxonomy audit reconciles tags against NAL-025 |
| Rollback | Remove tags; customer deletion requests honored per NAL-025 |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Fake customers tagged and untagged; audit report reconciles exactly |
| Live activation gate | Founder approval of the taxonomy |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 10. Entry A9 — Customer Metafields: Preference and Consent Storage

| Field | Specification |
|-------|---------------|
| Automation name | Preference and Consent Storage |
| Purpose | Store structured preference values (language, destination country, consent version/date per NAL-025) where tags are too coarse |
| Trigger | Written on consented form submission (Entry A5) or Founder edit |
| Conditions | Only NAL-025-defined fields; consent metafield mandatory before any preference metafield |
| Actions | Create/update customer metafield values |
| Data used | Declared preferences and consent records only — no sensitive data, ever |
| Owner | Founder |
| Founder approval gate | Metafield definitions approved via NAL-014 before creation |
| Failure mode | Stale values — customers can view/edit/delete per NAL-025; staleness is surfaced, not guessed around |
| Rollback | Delete metafield definitions and values |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Fake customer's values written, edited, and deleted cleanly; consent recorded with version and date |
| Live activation gate | Founder approval; customer privacy verification (U-08) resolved first |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 11. Entry A10 — Customer Segments: Consented-Contact Segment

| Field | Specification |
|-------|---------------|
| Automation name | Consented-Contact Segment |
| Purpose | A segment containing only customers with recorded, current communication consent — the only population any future outbound campaign could even be drafted for |
| Trigger | Segment membership updates automatically from tags/metafields (Entries A8/A9) |
| Conditions | Consent metafield present and current; no consent, no membership |
| Actions | Segment membership only — sending anything remains a separate, Founder-approved act that does not exist in this catalogue |
| Data used | Consent status, declared preference tags |
| Owner | Founder |
| Founder approval gate | Segment definition via NAL-014; any use of the segment is a further, separate approval |
| Failure mode | Wrong membership — segment audited against consent records before any use |
| Rollback | Delete segment |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Fake consented and non-consented customers land on the correct side of the segment |
| Live activation gate | Founder approval after synthetic pass |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 12. Entry A11 — Flow: Out-of-Stock Product Alert

| Field | Specification |
|-------|---------------|
| Automation name | Out-of-Stock Product Alert |
| Purpose | Internal alert when a product variant's inventory reaches zero, opening a NAL-021 stock-out exception early |
| Trigger | Product/inventory quantity changed |
| Conditions | Available quantity equals zero |
| Actions | Internal staff notification; add product tag `stock-out-review` |
| Data used | Product ID, variant, inventory quantity |
| Owner | Founder |
| Founder approval gate | Activation via NAL-014 — and this entry only becomes meaningful once real inventory logic exists (no products exist today, NAL-023 blocker 1) |
| Failure mode | Missed alert — supplier availability is still confirmed per order (NAL-018 step 5) |
| Rollback | Deactivate workflow; remove tags |
| Expected cost | AED 0 |
| Shopify plan requirement | UNKNOWN (U-10) |
| Synthetic test | Fake inventory decrement to zero produces notification and tag |
| Live activation gate | Founder approval after synthetic pass |
| Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |

---

# 13. Markets — Deliberately Not Automated

Markets appear in this catalogue only to record a decision: no automation touches Market state. Market activation, deactivation, and configuration are Founder-only acts governed by the Market Activation Gate (NAL-016). Any future proposal to automate anything Market-adjacent (even reporting) enters this catalogue as a new entry with the full field set and its own approval gate.

---

# 14. Catalogue Summary

| Entry | Native Feature | Name | Status |
|-------|----------------|------|--------|
| A1 | Shopify Flow (order trigger) | New-Order Control Tag | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A2 | Shopify Flow (order trigger) | High-Risk Order Alert | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A3 | Shopify Flow (scheduled condition) | Unfulfilled-Order Aging Alert | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A4 | Fulfillment trigger | Tracking-Recorded Checkpoint | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A5 | Shopify Forms | Storage-Problem Preference Form | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A6 | Customer Accounts | Self-Service Order Status | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A7 | Messaging/Inbox (U-12 gated) | Reviewed Saved Replies | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A8 | Customer tags | Preference Tag Taxonomy | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A9 | Customer metafields | Preference and Consent Storage | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A10 | Customer segments | Consented-Contact Segment | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| A11 | Shopify Flow (inventory trigger) | Out-of-Stock Product Alert | PROPOSED — NOT INSTALLED — NOT ACTIVE |
| — | Markets | Deliberately not automated | DECISION RECORDED |

---

# Related Documents

- NAL-002 / `02_Current_State_Audit.md` (section 4a — Flow and Forms not installed)
- NAL-003 / `03_Unknowns_Register.md` (U-08, U-10, U-12)
- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-016 / `16_Market_Activation_Gate.md`
- NAL-018 / `18_First_20_Orders_Control.md`
- NAL-019 / `19_Customer_Care_Workflow.md`
- NAL-021 / `21_Supplier_and_Inventory_Exceptions.md`
- NAL-025 / `25_Customer_Preference_Specification.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial catalogue — eleven proposed native automations plus a recorded Markets non-automation decision; all PROPOSED — NOT INSTALLED — NOT ACTIVE |

---
