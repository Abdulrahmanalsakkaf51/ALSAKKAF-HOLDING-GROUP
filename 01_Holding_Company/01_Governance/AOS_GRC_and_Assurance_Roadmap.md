# ALSAKKAF HOLDING GROUP

# AOS Governance, Risk, Compliance & Assurance Roadmap

> "Guardian protects the system. GRC proves the system is trustworthy."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | GRCA-001 |
| Document Type | Governance Roadmap |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Approved By | Not yet approved |
| Related System | AOS |
| Related Project | PRJ-006 |
| Related Documents | PREG-001, POM-001, KNOW-001, GUARD-001, GREQ-001, APFA-001, PCL-001, ADDA-001, ASAA-001 |

---

# 1. Purpose

This document defines the future Governance, Risk, Compliance & Assurance (GRC) structure for ALSAKKAF HOLDING GROUP.

It exists to plan four future control functions before any of them are built:

- Risk Management Partner
- Compliance Partner
- Internal Audit Partner / Audit Department
- HR / People Partner

This is a roadmap, not an activation. No Partner described in this document is approved, built, tested, or active. All four are Proposed placeholders reserved for future work.

---

# 2. Why AOS Needs Governance, Risk, Compliance & Assurance

AOS already has cybersecurity governance through Guardian (PARTNER-016). Cybersecurity alone is not enough for a holding group that intends to run multiple companies, hire collaborators, serve clients, and operate Partners with real authority levels.

| Pressure | Reason GRC Is Needed |
|----------|----------------------|
| Growing Partner count | More Partners means more decisions being prepared and executed; someone must check whether the rules governing them are still being followed |
| Multiple future companies | Each company under the holding group carries its own operational, financial, and market risks that Guardian does not cover |
| Client-facing work | AI Services and future client work create contractual, reputational, and delivery risk beyond cybersecurity |
| Collaborator growth | Hiring people requires onboarding, role clarity, training, and culture governance that no current function owns |
| Evidence discipline | AOS runs on documentation and approval gates; something must independently confirm the paperwork matches reality |
| Founder bandwidth | As AOS scales, the Founder cannot personally verify every control; assurance functions exist to do this on the Founder's behalf, without replacing the Founder's authority |

Without a GRC structure, AOS risks growing a large Partner and project footprint without an independent mechanism to check that its own rules are being followed.

---

# 3. Relationship to Guardian

Guardian (PARTNER-016) is the cybersecurity and digital trust function. Guardian's scope is deliberately narrow: protecting systems, data, credentials, and integrations from security and trust risk.

The functions in this roadmap are not Guardian expansions. They are separate, future control functions that sit alongside Guardian:

- Guardian answers: "Are our systems, data, and integrations safe?"
- GRC functions answer: "Are we running the business the way we say we are, and can we prove it?"

Guardian and the future GRC functions will eventually share reporting habits (written artifacts, escalation to Atlas and the Founder, no self-approval) but they review different things and must remain organizationally distinct so that no single function marks its own homework.

---

# 4. Difference Between Guardian, Risk Management, Compliance, Internal Audit, and HR / People

| Function | Core Question | Focus |
|----------|---------------|-------|
| Guardian | Are our systems, data, and integrations safe? | Cybersecurity, digital trust, credential and data-sensitivity risk |
| Risk Management | What could go wrong, and how big is the exposure? | Strategic, financial, operational, project, market, and reputation risk identification and monitoring |
| Compliance | Are we following our own rules? | AOS policies, approvals, regulations, and documentation requirements |
| Internal Audit | Is what we claim actually true? | Independent review of whether AOS processes work as intended and whether evidence supports claims |
| HR / People | Are our people supported and clear on their roles? | Collaborator onboarding, role clarity, training, culture, and people governance |

A simple way to hold the distinction: Risk Management looks forward (what might happen), Compliance looks sideways (are we following the rule right now), Internal Audit looks backward (did we actually do what the record says we did), and HR / People looks inward (are the humans in the system supported and clear on their roles). Guardian looks outward and technical (is the system defensible against digital threats).

---

# 5. Proposed GRC & Assurance Structure

```text
Founder / CEO
    ↓
Atlas (Founder Executive Partner)
    ↓
Four parallel control functions, each reporting independently through Atlas:

  - Guardian (PARTNER-016) — cybersecurity and digital trust
  - Risk Management (PARTNER-011, existing "Risk Partner" row) — strategic, financial, operational, project, market, reputation risk
  - Compliance Partner (PARTNER-017) — rules, policies, approvals, regulations, documentation
  - Internal Audit Partner (PARTNER-018) — independent review of process and evidence
  - HR / People (PARTNER-014, existing "HR Partner" row) — collaborators, onboarding, role clarity, training, culture
```

All four future functions report through Atlas to the Founder, in the same pattern already established for Guardian. None of the four functions supervises another at this stage. Internal Audit may later review the work of Risk Management, Compliance, HR / People, and Guardian itself, but only in an independent-review capacity, never as a line manager.

---

# 6. Risk Management Partner Concept — PARTNER-011

## 6.1 Purpose

Identify and monitor strategic, financial, operational, project, market, and reputation risks across ALSAKKAF HOLDING GROUP and its future companies.

## 6.2 Relationship to the Existing PARTNER-011 "Risk Partner"

The Partner Registry already lists PARTNER-011, "Risk Partner," described as identifying risks, assumptions, missing information, and governance concerns, linked to the DNA-001 decision framework (Chapter 6).

This roadmap does not create a new Partner ID for Risk Management. PARTNER-011 is confirmed as the Risk Management function described in this section. Its Partner Registry purpose text has been clarified to include ongoing monitoring of strategic, financial, operational, project, market, and reputation risk, alongside its existing decision-time review role. PARTNER-011 has not been renamed or retyped, and its ID has not changed.

## 6.3 What This Function May Do (Future)

- Maintain a risk register covering strategic, financial, operational, project, market, and reputation risk
- Flag emerging risks for Founder and Atlas review
- Support project risk sections (as already used in PRJ-006 and other project records)
- Recommend risk mitigation options for Founder decision

## 6.4 What This Function Must Not Do (Future)

- Approve its own risk assessments as final
- Make risk-acceptance decisions on behalf of the Founder
- Access Restricted-tier data without approval
- Act on identified risks without Founder or Atlas direction

---

# 7. Compliance Partner Concept — PARTNER-017

## 7.1 Purpose

Ensure AOS follows its own rules, policies, approvals, regulations, and documentation requirements.

## 7.2 What This Function May Do (Future)

- Check that new documents follow AOS documentation standards (Document Information tables, registers, statuses)
- Check that Partner activations followed the required approval gates before being marked Active
- Maintain a compliance checklist referencing CLAUDE.md, OPS-001, and the Partner Registry rules
- Flag missing register updates or skipped approval steps for Founder review

## 7.3 What This Function Must Not Do (Future)

- Approve its own compliance findings as final
- Waive or override an approval gate
- Provide legal advice; external regulatory questions are escalated to the Founder and, if needed, outside counsel
- Change project numbering, Partner IDs, or official folder names

---

# 8. Internal Audit Partner / Audit Department Concept — PARTNER-018

## 8.1 Purpose

Independently review whether AOS processes are working as intended and whether evidence supports claims.

## 8.2 What This Function May Do (Future)

- Sample completed projects and Partner activations against their recorded status (for example, confirming a "Completed" project record actually has the deliverables it claims)
- Review whether Knowledge Register and Partner Registry entries match the underlying documents
- Produce periodic audit findings for the Founder
- Recommend process corrections when evidence does not support a recorded status

## 8.3 What This Function Must Not Do (Future)

- Audit its own work
- Correct records directly; Internal Audit reports findings, it does not silently fix them
- Access Restricted-tier data without approval
- Replace Founder judgment on how to respond to a finding

## 8.4 Relationship to Existing Assurance Habits

AOS already practices lightweight self-audit through required register updates, Markdown Audit, and completion sections on project records. Internal Audit does not replace these habits; it periodically checks that they are actually being followed, rather than assumed to be followed.

---

# 9. HR / People Partner Concept — PARTNER-014

## 9.1 Purpose

Support collaborators, onboarding, role clarity, training, culture, and people governance.

## 9.2 Relationship to the Existing PARTNER-014 "HR Partner"

The Partner Registry already lists PARTNER-014, "HR Partner" (typed as an Operations Partner), described as supporting future collaborator onboarding, role descriptions, learning paths, and culture documents. This is the same functional territory as "HR / People" in this roadmap.

This roadmap does not create a new Partner ID for HR / People. PARTNER-014 is confirmed as the HR / People function described in this section. Its Partner Registry purpose text has been clarified to include role clarity and people governance, alongside its existing onboarding, role description, and culture-document responsibilities. PARTNER-014 has not been renamed or retyped, and its ID has not changed.

## 9.3 What This Function May Do (Future)

- Draft role descriptions, onboarding checklists, and learning paths for future collaborators
- Maintain culture and people-governance documentation
- Support training material alongside AOS University
- Flag role-clarity gaps for Founder review

## 9.4 What This Function Must Not Do (Future)

- Make hiring, termination, or compensation decisions
- Access private collaborator data without approval and a defined sensitivity classification
- Approve its own policy proposals as final
- Handle legal employment matters without Founder involvement and, where needed, outside counsel

---

# 10. Approval Gates

No function described in this roadmap may move past Proposed status without completing the same gate already required of every Partner in the Partner Registry (Section 9, PREG-001):

- Partner name, purpose, type, and authority level defined
- Owner assigned
- Knowledge sources defined
- Allowed and restricted tasks defined
- Testing method defined
- Review cycle defined
- Human approval rules defined
- Partner Request, Profile, Prompt, Test Log, and Activation Checklist completed through the Partner Factory lifecycle (PCL-001), following the same pattern used for Guardian (PARTNER-016)
- Explicit Founder approval captured before any status change from Proposed

This roadmap itself does not grant any approval. It only reserves the placeholders and records the plan.

---

# 11. Reporting to Atlas and CEO

All four future functions follow the same reporting pattern already established for Guardian:

- Each function documents findings, drafts, and escalations as written artifacts rather than verbal judgments.
- Each function reports to Atlas for coordination and routing.
- High-risk or high-significance findings are escalated directly to the Founder.
- No function approves its own findings, its own activation, or an increase in its own authority level.

---

# 12. Relationship to The Librarian

The Librarian indexes every approved document produced under this roadmap, including future Risk Management, Compliance, Internal Audit, and HR / People profiles, prompts, test logs, registers, and checklists, so they remain discoverable institutional knowledge rather than isolated files.

---

# 13. Relationship to Dashboards

Once any of these four functions is active, their outputs (open risks, compliance exceptions, audit findings, people-governance items) should be reportable through local dashboards, consistent with the dashboard and filing principles defined in ASAA-001. This roadmap does not build any dashboard; it defines the future data these functions would eventually provide.

---

# 14. Relationship to Client Acquisition

As AI Services and future modules take on client work, Compliance and Internal Audit become relevant to contractual and delivery obligations, and Risk Management becomes relevant to client and market risk. None of these functions are required before client acquisition begins, but this roadmap should be revisited once client-facing delivery scales beyond what the Founder can personally review.

---

# 15. Relationship to Partner Factory

Every function in this roadmap must be built through the same Partner Factory lifecycle already defined under PRJ-006 (APFA-001, PCL-001), using the same templates used for Guardian: Partner Request, Partner Profile, Partner Prompt, Test Log, and Activation Checklist. This roadmap does not create a separate build process for GRC functions.

---

# 16. Future Activation Order

This is a recommended sequence, not a commitment to a timeline. The Founder decides when any activation work begins.

| Order | Function | Partner ID | Rationale |
|-------|----------|------------|-----------|
| 1 | Compliance Partner | PARTNER-017 | Lowest complexity to start; can begin by checking existing approval-gate and documentation discipline already in use |
| 2 | Risk Management | PARTNER-011 | Builds on the existing PARTNER-011 risk-review habit and existing project risk sections; formalizes it into an ongoing register |
| 3 | HR / People | PARTNER-014 | Becomes necessary once ALSAKKAF HOLDING GROUP brings on its first non-Founder collaborator |
| 4 | Internal Audit Partner / Audit Department | PARTNER-018 | Most effective once there is a meaningful body of completed projects, active Partners, and compliance history to independently review |

Guardian (PARTNER-016) remains its own track under PRJ-006 and is not resequenced by this roadmap.

---

# 17. Status

Status: **Draft**

This roadmap is a planning document only. No function described here is approved, designed, tested, or active. Risk Management (PARTNER-011) and HR / People (PARTNER-014) are existing Proposed Partner Registry rows confirmed by this roadmap, with clarified purpose text only. Compliance (PARTNER-017) and Internal Audit (PARTNER-018) are new Proposed placeholders added to the Partner Registry. All four remain pending future Partner Factory work and Founder approval.

---

# 18. Related Documents

- PREG-001 — Partner Registry
- POM-001 — Partner Operating Model
- GUARD-001 — Guardian Partner Profile
- GREQ-001 — Guardian Partner Request
- APFA-001 — AOS Partner Factory Architecture
- PCL-001 — Partner Creation Lifecycle
- ADDA-001 — AOS Data & Deployment Architecture
- ASAA-001 — Atlas Super Assistant Architecture
- PRJ-006 — Build AOS Partner Factory

---

# 19. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-12 | Initial draft roadmap created |
