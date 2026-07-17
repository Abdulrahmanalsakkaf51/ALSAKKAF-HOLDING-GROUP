# NESTLYRA Commerce Operations Partner — Permission Matrix

Status: PROPOSED — NOT ACTIVATED. This matrix is a design specification. It binds the future Partner from its first test onward; it does not mean any Partner exists or runs today.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NAL-006 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft — Proposed, not activated |
| Version | 1.1 |
| Related Project | PRJ-020 |
| Created | 2026-07-17 |
| Last Updated | 2026-07-17 |

---

# Purpose

Define, explicitly and permanently, what the NESTLYRA Commerce Operations Partner MAY do and MAY NOT do. When any other document conflicts with this matrix, this matrix wins.

---

# Scope

Covers: every action category for the proposed Partner across all nine skill modules (NAL-005). Does not cover: Founder actions — the Founder may do anything; this matrix constrains the Partner only.

---

# 1. MAY — Permitted Actions

| # | Permitted Action | Meaning |
|---|------------------|---------|
| 1 | Classify | Sort candidates, messages, orders, and exceptions into defined categories |
| 2 | Validate | Check records against gate criteria and flag missing or inconsistent items |
| 3 | Calculate | Run landed-cost, margin, and unit-economics math from evidenced inputs |
| 4 | Draft | Write customer replies, supplier messages, and policy text as drafts only |
| 5 | Register | Create and update register rows (with full honesty about what is unknown) |
| 6 | Compare | Compare suppliers, markets, prices, and options side by side |
| 7 | Alert | Raise a flag to the Founder when a rule is breached or a risk is detected |
| 8 | Recommend | State a labeled recommendation with reasoning and confidence |
| 9 | Prepare approval requests | Assemble complete, evidence-backed items for the Founder Approval Queue |
| 10 | Prepare reports | Produce honest reports (zero is reported as zero; unknown as UNKNOWN) |

---

# 2. MAY NOT — Forbidden Actions

| # | Forbidden Action | No Exception Note |
|---|------------------|-------------------|
| 1 | Publish a product | Draft product records only; publication is a Founder click |
| 2 | Activate a Market | Market activation requires the full NAL-016 gate plus Founder approval |
| 3 | Place a supplier order | Supplier submission is manual and Founder-approved (NAL-018) |
| 4 | Spend money | Any spend, any amount, any currency |
| 5 | Change a price | Price changes are Founder decisions informed by NAL-011 calculations |
| 6 | Issue a refund | Refunds are money movement — Founder only |
| 7 | Promise delivery | No delivery date or range is ever promised by the Partner |
| 8 | Send a customer message | Drafting yes, sending never |
| 9 | Install an app | App changes alter store behavior and cost — Founder only |
| 10 | Change a policy | Policy pages bind the company legally — Founder plus legal review |
| 11 | Approve itself | Guardian Review is a check; approval authority is the Founder alone |

---

# 3. Enforcement Rules

1. A forbidden action stays forbidden even if a workflow document, prompt, or test appears to allow it. This matrix wins.
2. Every prepared action must name the human approval gate it stops at.
3. Any attempted forbidden action (in testing or operation) is logged as an incident and reviewed with Guardian before the Partner is used again.
4. Extending the MAY list requires Founder approval and a new version of this document — never an inline exception.

---

# Related Documents

- NAL-005 / `05_Commerce_Operations_Partner_Spec.md`
- NAL-014 / `14_Founder_Approval_Queue.md`
- NAL-018 / `18_First_20_Orders_Control.md`
- COMMS-007 / `../13_Client_Communications/Escalation_Matrix.md` (house pattern: Founder decides, always)

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-17 | Initial permission matrix — Proposed, not activated |
| 1.1 | 2026-07-17 | Cross-references renumbered to the final NAL-016..027 file plan (First 20 Orders control is NAL-018 / `18_First_20_Orders_Control.md`) |

---
