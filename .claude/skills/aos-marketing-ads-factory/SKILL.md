---
name: aos-marketing-ads-factory
description: Use this skill when planning campaigns — ad angles, hooks, landing page ideas, testing plans, budget caps, performance review, and campaign lessons learned — for AOS-owned brands or, later, clients.
---

# AOS Marketing Ads Factory Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-010 |
| Skill Name | aos-marketing-ads-factory |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-001, STRAT-003, STRAT-004 |

---

# Purpose

This skill helps Claude draft campaign plans for the Marketing and Dropshipping/Ecommerce lines described in `AOS_Market_Intelligence_and_Financial_Assumptions.md` (STRAT-001 Section 2): ad angles, hooks, landing page ideas, testing plans, budget caps, and performance review — all as drafts for Founder approval, never as live spend.

---

# What This Skill Produces

| Output | Format | Ready to run without approval? |
|--------|--------|----------------------------------|
| Campaign Plan | Objective, audience, channel, angle summary, proposed budget cap | No — budget requires Founder approval |
| Ad Angles / Hooks | Short list of distinct value propositions and opening lines, each tagged to an audience segment | No — for review |
| Landing Page Ideas | Structure/section outline + key messages, not final copy or a built page | No — draft only |
| Testing Plan | What variable is being tested (angle, audience, creative), sample size/spend needed, and success metric | No — budget requires Founder approval |
| Performance Review | Table: campaign, spend, result, metric vs. target, one-line takeaway | Yes to compile from provided data |
| Lessons Learned | Pattern identified across one or more campaigns, routed via `aos-learning-loop` | N/A — proposal only |

---

# Required Behavior

1. Every Campaign Plan and Testing Plan must include an explicit proposed budget cap and be marked "requires Founder approval before spend," consistent with the Pricing/Spend approval discipline in STRAT-002 Section 7.
2. Do not assume access to any specific ad platform, analytics tool, or AI ad-generation tool — if one is needed, flag it as a new tool requiring the Tool Requirements + prototype + test log process (CLAUDE.md Section 5).
3. Ad angles and landing page copy must not misrepresent the product/service or imply claims that cannot be substantiated.
4. Performance Review must use only real, provided figures — never estimate or interpolate missing spend/result data.
5. When a Performance Review reveals a repeatable pattern (an angle or audience that works), draft the lesson and route it through `aos-learning-loop` rather than silently changing future plans.

---

# Boundaries

Do not, under this skill:

- launch, schedule, or pay for any ad campaign,
- exceed or omit a proposed budget cap on any campaign or test plan,
- generate or imply synthetic/AI ad video content without flagging the tool-approval and rights requirements (see `AOS_Inspiration_Register.md` Section 8),
- present a Campaign Plan or Testing Plan as approved when it has not been explicitly approved by the Founder.

---

# Related Documents

- 01_Holding_Company/03_Strategy/AOS_Market_Intelligence_and_Financial_Assumptions.md
- 01_Holding_Company/03_Strategy/AOS_Client_Acquisition_and_Delivery_Model.md
- 01_Holding_Company/03_Strategy/AOS_Inspiration_Register.md
- 01_Holding_Company/03_Strategy/AOS_Claude_Skill_Roadmap.md
- 01_Holding_Company/01_Governance/Knowledge_Register.md
- CLAUDE.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
