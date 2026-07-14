# ALSAKKAF HOLDING GROUP

# PRJ-017 — Five-Agent Trading Research Lab

> "ARCHITECTURE DEMONSTRATION ONLY — NOT FINANCIAL ADVICE — NO LIVE TRADING — NO PROFIT CLAIMS"

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-017 |
| Document Type | Project Record |
| Status | Active — design phase only |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Approved By | Founder (design scope only); any execution capability requires new explicit approval |
| Related System | AOS |
| Related Projects | PRJ-011 (Playground trading demo), PRJ-016, STRAT-017 |
| Related Documents | TRL-001 |

---

# 1. Objective

Design (not deploy) a five-agent trading research architecture as a controlled research lab and architecture showcase, consistent with the No-Hype Revenue Reality rule (STRAT-017: trading systems are research-only).

---

# 2. Roles

| Role | Responsibility |
|------|----------------|
| Manager | Frames the research question, synthesizes all analyst views, states unknowns, logs the decision record |
| News Analyst | Summarizes supplied news items with source-reliability labels |
| Strategy Analyst | Maps scenarios and the assumptions each depends on |
| Bull Analyst | Strongest honest positive case |
| Bear Analyst | Strongest honest negative case, including risks the bull case underweights |

---

# 3. Allowed Scope (this phase)

Architecture; market-data input format; news-summary input format; strategy analysis; bull case; bear case; manager synthesis; risk-policy design; backtest interface definition; paper/demo-trading workflow; decision logging; performance-report format. All defined in TRL-001.

---

# 4. Prohibited (hard limits)

Real-money trades; brokerage credentials; automatic brokerage connection; profit guarantees; live deployment claims; unrestricted leverage; martingale or any unbounded-loss strategy. These prohibitions are design constraints in TRL-001, not just policy text.

---

# 5. Public Wording Rule

Any public reference carries: ARCHITECTURE DEMONSTRATION ONLY — NOT FINANCIAL ADVICE — NO LIVE TRADING — NO PROFIT CLAIMS. The existing Playground trading demo already complies.

---

# 6. Project Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Architecture and design document (TRL-001) | Done |
| 2 | Input format schemas (market data, news) | Done (in TRL-001) |
| 3 | Risk policy design | Done (in TRL-001) |
| 4 | Backtest interface + paper-trading workflow definition | Done (in TRL-001) |
| 5 | Decision log + performance report formats | Done (in TRL-001) |
| 6 | Founder review; decide whether a paper-only prototype is built | Pending Founder |

---

# 7. Progress Log

| Date | Update |
|------|--------|
| 2026-07-14 | Project created with design-only scope under PRJ-016 mission Part 9. TRL-001 written. No code, no data connections, no execution capability. |

---

# 8. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial project record |
