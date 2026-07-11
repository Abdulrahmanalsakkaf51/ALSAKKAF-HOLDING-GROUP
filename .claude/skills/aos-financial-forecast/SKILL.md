---
name: aos-financial-forecast
description: Use this skill when preparing revenue, expense, profit, or scenario forecasts for ALSAKKAF HOLDING GROUP or any of its modules, keeping assumptions cautious, ranged, and traceable to AOS_Market_Intelligence_and_Financial_Assumptions.md.
---

# AOS Financial Forecast Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-005 |
| Skill Name | aos-financial-forecast |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-001 |

---

# Purpose

This skill helps Claude prepare cautious, ranged financial forecasts (revenue, expense, profit, scenario) for ALSAKKAF HOLDING GROUP, consistent with the baseline assumptions in `AOS_Market_Intelligence_and_Financial_Assumptions.md`.

Forecasts produced under this skill are planning references for the Founder, not commitments, guarantees, or accounting/tax advice.

---

# Forecasting Rules

1. **Always give a range, not a single number.** Use at minimum: expected, target, and stretch (or expected and worst-case), matching the pattern in STRAT-001 Section 5.
2. **Anchor to the baseline document.** Any new forecast must state whether it aligns with, updates, or deviates from the figures in `AOS_Market_Intelligence_and_Financial_Assumptions.md`, and why.
3. **Separate one-time from recurring costs.** Legal/setup costs are one-time and wide-range; subscriptions and tools are recurring and should be itemized where possible.
4. **State the assumption behind every number.** A forecast line without a stated assumption ("why do we think this") is incomplete.
5. **Default to the cautious end** when evidence is missing. Do not round up to make a scenario look better.
6. **Flag concentration and timing risk** explicitly when a forecast depends heavily on one client, one channel, or one month's performance — consistent with STRAT-001 Section 9.
7. **Never assume paid API usage, ad spend, or legal/setup spend is already approved.** Forecasts may model the cost of these items; they may not treat them as already committed.

---

# Standard Forecast Structure

When producing a forecast, use this structure unless the Founder asks for something different:

1. Period covered
2. Revenue assumptions (by module, with range)
3. Expense assumptions (one-time vs. recurring, with range)
4. Net position (range, not a single figure)
5. Key assumptions and what would change them
6. Risks that could move the forecast outside its stated range

---

# Boundaries

This skill does not:

- authorize any spend, purchase, or contract based on a forecast,
- replace professional accounting, tax, or legal advice,
- treat a stretch scenario as an expected outcome,
- silently overwrite the baseline assumptions document — proposed updates to STRAT-001 go through the standard AOS Live Build flow (plan, Founder approval, edit, audit).

---

# Related Documents

- 01_Holding_Company/03_Strategy/AOS_Market_Intelligence_and_Financial_Assumptions.md
- 01_Holding_Company/03_Strategy/AOS_Client_Acquisition_and_Delivery_Model.md
- CLAUDE.md
- 01_Holding_Company/04_Operations/02_Protocols/AOS_Live_Build_Protocol.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
