# NESTLYRA — Customer Care Workflow

Status: DESIGN + SYNTHETIC TESTING — STORE NOT LAUNCHED. No customer exists and no message has ever been sent. The Partner drafts; only the Founder sends. No autonomous customer response, ever.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-019 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Define how every customer inquiry is classified, answered from verified information only, and released only by the Founder — following the same escalation discipline as the Client Communications house pattern (COMMS-007).

---

# Scope

Covers: inquiry categories, the handling workflow, the Customer Inquiry Register, and the non-negotiable response rules. Does not cover: returns resolution (NAL-020 owns the resolution path once a return is requested) or supplier-side problems (NAL-021).

---

# 1. Inquiry Categories

| # | Category | Notes |
|---|----------|-------|
| 1 | Product question | Answer only from verified specifications (NAL-013); unverified means "let me confirm and come back to you" |
| 2 | Delivery question | No delivery promise — displayed estimates are PROVISIONAL / UNVERIFIED (U-15) |
| 3 | Order status | Verified tracking data only |
| 4 | Address change | Feeds the Order Exception Register (NAL-018 section 5) |
| 5 | Cancellation | Founder decision — timing against supplier submission matters |
| 6 | Return | Hands off to the Returns and Resolution Workflow (NAL-020) |
| 7 | Refund | Founder-only category — the Partner never confirms, promises, or issues a refund (NAL-006) |
| 8 | Damaged item | Evidence gathering per NAL-020, supplier exception per NAL-021 |
| 9 | Wrong item | Same path as damaged item |
| 10 | General | Anything else — classified honestly, not forced into a category |

---

# 2. The Workflow

| Step | Action | Rule |
|------|--------|------|
| 1 | INQUIRY received | Logged immediately in the Customer Inquiry Register (section 3) |
| 2 | Identify customer / order where appropriate | Only when the inquiry concerns an order; never demand data a general question does not need |
| 3 | Classify | One category from section 1 |
| 4 | Retrieve verified information only | Registers, verified tracking, approved policy text. UNKNOWN facts are stated as "being confirmed" — never filled with a guess |
| 5 | Draft response | Draft only. Honest, plain, no promise the evidence does not support |
| 6 | Guardian review where uncertain or sensitive | Refund-adjacent, complaint, legal, or any uncertainty — Guardian checks the draft (pattern of COMMS-007: sensitive categories get a safe holding reply, not an attempted answer) |
| 7 | Founder approval | Every outbound message queues in NAL-014 — including holding replies |
| 8 | Manual send | The Founder sends. The Partner never sends (NAL-006, forbidden action 8) |
| 9 | Follow-up | Promised follow-ups are tracked in the register until done |
| 10 | Outcome recorded | Resolution, category confirmation, and any lesson recorded |

---

# 3. Customer Inquiry Register (Template)

| Inquiry ID | Date | Channel | Category | Order Ref (if any) | Verified Info Used | Draft Ref | Guardian Check | Founder Decision | Sent Date | Follow-Up Due | Outcome |
|------------|------|---------|----------|--------------------|--------------------|-----------|----------------|------------------|-----------|---------------|---------|
| [Example Only - Not Real] EXAMPLE-INQ-001 | 2026-07-17 | Email | Product question | — | NAL-013 verified spec (example) | EXAMPLE-DR-001 | Passed (example) | APPROVE (example) | 2026-07-17 | — | Answered (example) |
| [Example Only - Not Real] EXAMPLE-INQ-002 | 2026-07-17 | Email | Delivery question | EXAMPLE-ORD-0001 | Tracking EXAMPLE-TRK-001 | EXAMPLE-DR-002 | Required — delivery sensitivity | PENDING | — | 2026-07-17 | — |

Real customer data, when it exists, lives in private storage per PODS-001; this public register holds structure and EXAMPLE ONLY rows.

---

# 4. Non-Negotiable Rules

1. No autonomous customer responses. Every message — including "safe" holding replies — passes Founder approval and is sent manually.
2. The Messaging app (identity unverified, U-12) must never answer customer questions using unverified shipping, product, or policy information. Until U-12 is resolved and the Founder approves a configuration, any auto-reply capability it has stays untrusted and unused.
3. Where a category matches a COMMS-007 sensitive row (refund, complaint, legal), the draft may only be a safe holding reply — it must not attempt the substantive answer; that answer is Founder-authored.
4. No response ever invents a delivery date, spec, discount, or policy position. "I need to confirm that and will come back to you" is always an acceptable draft.
5. Every inquiry gets a register row, even ones the Founder answers directly — the record is the point.

---

# Related Documents

- COMMS-007 / `../13_Client_Communications/Escalation_Matrix.md` (house escalation pattern)
- COMMS-009 / `../13_Client_Communications/Forbidden_Auto_Send_Categories.md`
- NAL-006 / `06_Partner_Permission_Matrix.md`
- NAL-013 / `13_Product_Claim_Verification.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-018 / `18_First_20_Orders_Control.md`
- NAL-020 / `20_Returns_and_Resolution_Workflow.md`
- PODS-001 / `../../01_Governance/Private_Operational_Data_Standard.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial workflow — ten categories, ten-step flow, inquiry register template, five non-negotiable rules |

---
