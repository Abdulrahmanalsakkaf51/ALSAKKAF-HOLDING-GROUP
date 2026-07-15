# NESTLYRA — Landed Cost Calculator Specification

Status: DRAFT — not yet live. This is a specification document only, not a working spreadsheet or tool.

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | NESTLYRA-020 |
| Owner | Abdulrahman Alsakkaf |
| Department | Holding Company |
| Status | Draft |
| Version | 1.0 |
| Created | 2026-07-16 |
| Last Updated | 2026-07-16 |

---

# Purpose

Describes the calculation a future Landed Cost Calculator needs to perform for NESTLYRA products, so that pricing decisions are based on real math rather than guesswork. Building the actual spreadsheet or tool is separate, future work and is explicitly out of scope for this document.

---

# Scope

Covers: the inputs, formula, and outputs the calculator must support. Does not cover: the actual spreadsheet file, software implementation, or any real cost figures (none exist yet — no supplier is selected).

---

# 1. Core Calculation

```text
Landed Cost per Unit =
    Unit Cost
  + Shipping Cost per Unit
  + Duty / Import Fees per Unit
  + Platform / Payment Processing Fees per Unit
  + Packaging Cost per Unit

Margin =
    Target Retail Price − Landed Cost per Unit

Margin % =
    (Target Retail Price − Landed Cost per Unit) / Target Retail Price × 100
```

---

# 2. Required Input Fields

| Field | Description |
|-------|-------------|
| Unit Cost | Supplier's quoted per-unit cost (from Supplier Comparison Sheet) |
| Order Quantity | Number of units in the order, used to allocate shipping/duty per unit |
| Total Shipping Cost | Freight cost for the shipment (to be divided by order quantity) |
| Duty / Import Fee Rate or Amount | Applicable duty rate or flat fee, dependent on RAKEZ/legal entity and import jurisdiction — not yet known |
| Platform Fee % | Shopify transaction fee, if applicable |
| Payment Processing Fee % | Payment processor's per-transaction fee, once a processor is reconnected |
| Packaging Cost per Unit | Cost of any additional packaging/inserts beyond what the supplier includes |
| Target Retail Price | The price NESTLYRA is considering charging |

All fields above are currently unset for every NESTLYRA product. `[VERIFY BEFORE LAUNCH: no real value exists for any field until a supplier is selected, RAKEZ/legal entity status is resolved, and a payment processor is reconnected.]`

---

# 3. Worked Example (Symbolic Only — Not Real Figures)

This example uses placeholder variables to illustrate how the formula works. It does not represent any real NESTLYRA cost and must not be copied into a product page or pricing decision.

```text
Let:
  Unit Cost               = A
  Shipping Cost per Unit  = B
  Duty per Unit           = C
  Platform Fee per Unit   = D
  Payment Fee per Unit    = E
  Packaging per Unit      = F

Landed Cost per Unit = A + B + C + D + E + F

If Target Retail Price = R, then:
  Margin   = R − (A + B + C + D + E + F)
  Margin % = Margin / R × 100
```

---

# 4. Required Outputs

- Landed cost per unit (currency amount).
- Margin per unit (currency amount) at a given target retail price.
- Margin percentage at a given target retail price.
- A simple sensitivity check: margin at two or three candidate retail prices, so pricing decisions can be compared side by side.

---

# 5. Out of Scope for This Document

- Building the actual spreadsheet, workbook, or software tool. That is separate future work.
- Any real cost figures. None exist because no supplier is selected.
- Currency conversion logic, tax remittance calculations, or accounting-system integration.

---

# Related Documents

- NESTLYRA-018 / `18_Product_Verification_Checklist.md`
- NESTLYRA-019 / `19_Supplier_Comparison_Sheet.md`

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-16 | Initial specification, no implementation |

---
