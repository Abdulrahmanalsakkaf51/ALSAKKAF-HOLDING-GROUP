# ALSAKKAF HOLDING GROUP

# AOS Founder Sales and Technical Q&A

> "Say what works today, what is planned, and what stays human. Nothing else."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | FQA-001 |
| Document Type | Founder Education Package |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-015 |
| Related Documents | CDP-001, EEDC-001, PRT-001, ACB-001, PLK-001, STRAT-017 |

---

# 1. Purpose

Prepare the Founder for professional sales and technical discussions. Every answer is honest, avoids hype, and distinguishes prototype from production and current from planned capability.

---

# 2. The Questions and Answers

## Q1. What is an AI Partner?

A defined role — instructions, knowledge sources, allowed tools, permissions, workflow, memory rules, and approval rules — executed by shared runtime infrastructure. It is a disciplined way to give AI a job description with hard boundaries, not a mystical AI employee.

## Q2. What is Atlas?

Our internal executive Partner: it prepares briefings, routes tasks to other Partners and tools, and keeps the owner in control. Today Atlas runs on a local deterministic runtime plus AI assistance when we work with it interactively; it is the system we use to run our own company.

## Q3. Is this just ChatGPT?

No — and it is also not a replacement for it. The value is the operating system around the model: role definitions, routing, deterministic local tools, approval gates, logs, and cost control. A model (any good one) can plug into that structure. Much of our tooling works with no AI model at all.

## Q4. Can Atlas work offline?

Partially, and measurably. Our deterministic local tools (spreadsheets, documents, filing, trackers, reporting, policy retrieval, planning) run fully offline. In our benchmark, Atlas Local completed 81 of 103 realistic company tasks within acceptance criteria with no model and no network. The other 22 genuinely require an AI model — we say so rather than pretend.

## Q5. Does every Partner require a subscription?

No. A Partner is a role definition, not a seat license. Deterministic Partners cost nothing to run. Partners that need AI share whatever model access you have.

## Q6. Can several Partners share one AI provider?

Yes — that is the default design. The runtime routes all Partner AI calls through one provider adapter, so three or nine Partners can share a single account.

## Q7. Who pays AI usage?

Depends on the deployment option. BRING YOUR OWN AI (available now): you pay your provider directly under your own plan. AOS MANAGED RUNTIME (planned, not yet offered): usage would be metered and billed transparently. PRIVATE/LOCAL (custom quote): you run a local model; usage is your hardware.

## Q8. Can we use our own AI account?

Yes — that is our standard first option. We deliver roles, prompts, routing, and guides that run on your existing account.

## Q9. Where is data stored?

For the Starter Pack: your business information lives in your documents and your AI account; we keep only the engagement deliverables we create for you. We never store credentials. For anything involving private or regulated data, deployment location is scoped explicitly (local/private options exist) — we make no blanket data-location claims.

## Q10. How does the Office Partner work?

It is a role backed by seven local tools that genuinely create and edit real files: native XLSX workbooks, native DOCX reports and minutes, organized folders with duplicate detection and indexes, cleaned CSVs, trackers, and email drafts. All of it passed real task tests. It never sends email — humans send.

## Q11. Can the Supervisor create tasks?

Yes — proactively, within hard boundaries. It reads goals, deadlines, backlog, and KPIs, and proposes a bounded, prioritized daily plan (with a reason on every task). It escalates anything external, financial, legal, or sensitive, and it cannot invent busywork: no input signal, no task. The department lead approves the plan.

## Q12. What decisions remain human?

Sending anything external. Payments and pricing. Hiring, discipline, salaries, termination. Legal interpretations. Policy changes. External commitments. Anything irreversible. This is enforced by approval gates, not just promised.

## Q13. How does labour-law knowledge work?

We index knowledge items — company policy first, then official legal source references — each carrying jurisdiction, source, official URL, effective date, and last-verified date. Managers get summaries with sources, never legal rulings.

## Q14. How do you prevent outdated law?

Every item has a verification window (180 days). A freshness checker reports anything overdue, offline answers always show the SOURCE SNAPSHOT DATE, and stale items carry an explicit warning. Re-verification against the official source is a human task.

## Q15. How do you prevent hallucination?

Three layers: deterministic tools compute facts (numbers are counted, not generated); retrieval answers come only from indexed, sourced knowledge — no match means "not found", never a guess; and sensitive categories are flagged LEGAL / HR REVIEW REQUIRED for humans. AI-generated drafts are always labeled drafts and human-reviewed.

## Q16. What happens when the model is unavailable?

Deterministic tools keep working — trackers, documents, filing, reports, policy lookup, planning. Tasks that need the model are honestly reported as blocked and queue for human attention. Nothing silently degrades into guessing.

## Q17. Can IT inspect the architecture?

Yes. The runtime is readable Python (standard library only in v1), Partner definitions are plain JSON, logs are JSONL, and approval queues are plain files. There is nothing opaque to inspect.

## Q18. Can data remain in our environment?

Yes, as a scoped option: local/private deployment keeps Partner definitions, knowledge, and (with a local model) AI inference inside your infrastructure. That is a custom engagement, not part of the fixed-price pack, and its boundaries are agreed in writing.

## Q19. Can we start with one department?

Yes — that is our recommended path (and the only one we offer for enterprises): discovery, then a one-department proof of concept on low-risk data, then a pilot, then scale. See our education enterprise concept for the phase model.

## Q20. Can we deploy locally?

Architecturally yes — the runtime has a local model adapter and everything else is local-first by design. Honest status: local model deployment is a custom-quoted engagement and depends on your hardware; it is not part of the $450 pack.

## Q21. What does the $450 package include?

Three custom Partner roles (profiles + ready-to-use prompts), a task routing map, a business-specific workflow, a dashboard/reporting template, an implementation guide with approval/safety rules, one revision, and a 30-minute setup session. Delivered in 5-7 business days from complete intake answers.

## Q22. What costs extra?

AI usage/subscriptions (yours), enterprise integrations, private/local infrastructure, nine-Partner department pods, enterprise dashboards, regulated-data deployments, custom software development, and ongoing managed operation. Each is scoped and quoted before any payment.

---

# 3. Standing Language Rules

1. Never claim "Atlas equals ChatGPT" or any percentage comparison.
2. Never promise guaranteed revenue, profits, or outcomes.
3. Never say "guaranteed secure" — describe controls instead.
4. Always distinguish: works today / architecture ready / planned / concept.
5. Trading systems are research/architecture demonstrations only — no live trading, no financial advice, no profit claims.

---

# 4. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial Q&A package |
