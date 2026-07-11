# ALSAKKAF HOLDING GROUP

# Partner Routing and Cost Control Model

> "AOS should be Partner-rich, not AI-worker-expensive."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRCC-001 |
| Document Type | Routing and Cost Model |
| Status | Draft |
| Version | 1.0 |
| Date | 2026-07-12 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-006 |
| Related Documents | APFA-001, ADDA-001, PCL-001 |

---

# 1. Purpose

This document defines how tasks are routed to the correct Partner and the correct AI model tier, and how AOS keeps cost controlled as the number of Partners grows.

It extends the budget rules already established in the AOS Data & Deployment Architecture (ADDA-001) so they apply across many Partners at once, not just Atlas alone.

---

# 2. Partner Router

The Partner Router decides which Partner should handle an incoming task.

```text
Task arrives
    ↓
Match task to Partner purpose (from Partner Registry)
    ↓
Check Partner status is Active
    ↓
Check Partner Authority Level covers the task
    ↓
If a fitting Partner exists, assign the task
    ↓
If no fitting Partner exists, prepare a Partner Request instead of stretching an existing Partner
```

The Partner Router never assigns a task to a Partner whose purpose or permission level does not cover it.

---

# 3. Model Router

Once a Partner is selected, the Model Router decides which AI model tier that Partner uses to complete the task, reusing the tiers defined in ADDA-001:

| Tier | Model Type | Use Case |
|------|------------|----------|
| Tier 0 | No AI / local logic | File checks, audits, simple rules, Markdown Audit style tasks |
| Tier 1 | Local model (Ollama) | Basic summaries, drafts, and offline support |
| Tier 2 | Cheap online model | Simple drafts, classification, short summaries |
| Tier 3 | Strong online model | Strategy, planning, technical design, important writing |
| Tier 4 | Premium online model | Critical decisions, complex architecture, high-value work |

---

# 4. Local Tool First

Before any model is used, the router checks whether the task can be completed with a local tool (a script, an audit, a lookup, a template) with no AI involved.

```text
Can a local tool do this?
    ↓ yes → use the local tool. Done.
    ↓ no  → continue to local model.
```

---

# 5. Local Model Through Ollama When Possible

If a local tool cannot complete the task, the router checks whether a local model (running through Ollama) can.

```text
Can a local model do this well enough?
    ↓ yes → use the local model. Done.
    ↓ no  → continue to cheap online model.
```

Local models are free to run repeatedly and are the default for routine, low-stakes Partner work.

---

# 6. Cheap Online Model

If local capability is insufficient, the router considers a cheap online model for simple, low-risk online tasks (short drafts, classification, simple summaries).

```text
Is the task simple enough for a cheap model?
    ↓ yes → use the cheap model. Log cost. Done.
    ↓ no  → continue to strong online model.
```

---

# 7. Strong Online Model

For strategy, planning, technical design, or important writing, a strong online model may be used.

```text
Is the task important enough to justify a strong model?
    ↓ yes → use the strong model. Log cost. Done.
    ↓ no  → reconsider whether the task truly needs AI at all.
```

---

# 8. Premium Model Only With Approval

Premium models are reserved for critical decisions or high-value work, and require Founder approval before use, every time.

```text
Is this task critical or high-value enough for a premium model?
    ↓ yes → ask Founder for approval.
    ↓ approved → use premium model. Log cost.
    ↓ not approved → fall back to strong model or defer the task.
```

---

# 9. Cost Estimator

Before routing a task to any paid tier (2 through 4), the router estimates expected cost using:

| Factor | Consideration |
|--------|----------------|
| Task size | Short task versus long, multi-step task |
| Model tier | Cheap, strong, or premium pricing |
| Expected frequency | One-time task versus a recurring Partner duty |

The estimate is compared against the remaining monthly budget before the task proceeds.

---

# 10. Monthly Budget Ledger

AOS maintains a single monthly AI cost ledger shared across all Partners, not a separate budget per Partner.

| Budget Rule | Value |
|------------|-------|
| Target monthly AI cost | 5 to 20 USD |
| Maximum early monthly cost | 50 USD |
| Ledger scope | Combined across all active Partners |
| Ledger owner | Atlas maintains it; Founder reviews it |

This reuses the budget figures already approved in ADDA-001, applied at the whole-Partner-system level.

---

# 11. Cost Warning Levels

| Level | Trigger | Behavior |
|-------|---------|----------|
| Green | Below 50% of monthly budget | Normal operation |
| Yellow | 50% to 80% of monthly budget | Atlas favors local and cheap tiers more strictly; flags spend to Founder |
| Orange | 80% to 100% of monthly budget | Only Tier 0 to Tier 2 tasks proceed without explicit approval |
| Red | At or above monthly budget | Hard stop, see Section 12 |

---

# 12. Hard Stop Rules

```text
At the monthly budget limit:
    ↓
All Tier 2, 3, and 4 tasks pause.
    ↓
Only local tools and local models continue operating.
    ↓
Atlas notifies the Founder.
    ↓
Founder may approve an increased limit, or tasks wait until next month.
```

No Partner, including Atlas, may override the hard stop without Founder approval.

---

# 13. When Atlas Must Ask Approval

Atlas must ask the Founder before:

- routing any task to a premium model (Tier 4),
- exceeding the Orange warning level with a Tier 3 task,
- creating a new Partner Request,
- increasing any Partner's Authority Level,
- continuing paid AI usage past the monthly hard stop.

---

# 14. When Atlas May Act Silently

Atlas may act without asking, within approved bounds, for:

- Tier 0 and Tier 1 tasks (local tools and local models),
- routine Tier 2 tasks that are clearly inside an active Partner's approved purpose and within budget,
- monitoring and logging activity,
- preparing (not activating) drafts, plans, and reports for later review.

Acting silently never means acting outside an approved Partner's purpose or permission level.

---

# 15. How Many Partners Can Exist Without Many Online Workers Running All Day

The key principle: Partners are roles and rule sets, not always-on processes.

```text
50 Partners can exist as documented roles.
    ↓
Most Partner work is triggered on demand, not continuously.
    ↓
Most triggered work resolves at Tier 0 or Tier 1 (local, free).
    ↓
Only a small fraction of tasks need Tier 2 or above.
    ↓
Shared monthly budget keeps total online cost bounded regardless of Partner count.
```

Because a Partner only "activates" compute when a real task is routed to it, having many Partners does not mean having many simultaneous paid AI processes. It means having many well-defined roles that share a small, controlled pool of online AI usage.

---

# 16. Status

Draft.

This model should be re-validated once the first Partner is routed real tasks through the Factory (PRJ-006-T011), and updated with observed cost data.
