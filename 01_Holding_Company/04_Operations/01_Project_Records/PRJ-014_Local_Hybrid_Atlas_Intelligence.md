# ALSAKKAF HOLDING GROUP

# PRJ-014 — Local / Hybrid Atlas Intelligence

> "Atlas must be measurably useful with the network cable unplugged."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-014 |
| Document Type | Project Record |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Approved By | Founder (build); Partner activations remain gated |
| Related System | AOS |
| Related Projects | PRJ-012, PRJ-013 |
| Related Documents | SRS-001, POD-001, PLK-001, ACB-001 |

---

# 1. Objective

Make Atlas meaningfully useful offline and honestly measurable, through four connected pieces:

1. First Internal Operational Partner Pod (POD-001) with deterministic tools.
2. AOS-native skill system and Skill Routing Standard (SRS-001) with a runnable skill router.
3. AOS Policy and Law Knowledge System (PLK-001) — controlled, source-referenced policy retrieval.
4. Atlas Capability Benchmark v1 (ACB-001) — 100+ realistic tasks, honest scoring.

We do NOT claim "Atlas is equal to ChatGPT". We measure what Atlas Local completes.

---

# 2. Architecture

```text
Atlas
  ↓
Skill Router (skill_router.py)
  ↓
Task Classifier (deterministic rules)
  ↓
Local Tools (Office Toolbelt, Pod Tools, Policy Retriever, Atlas Runtime)
  ↓
Local Model if needed (adapter, disabled by default)
  ↓
Cloud Escalation if allowed (adapter, env-var keys, disabled by default)
```

This system is inspired by role-based workflow skill systems (for example Gstack) but is AOS-native. No third-party skill packages are installed.

---

# 3. Scope

| Deliverable | Location |
|-------------|----------|
| Skill router + task classifier + tests | 09_AI_Systems/02_Tools/Skill_Router/ |
| Skill Routing Standard | 09_AI_Systems/02_Tools/Skill_Router/Skill_Routing_Standard.md |
| New AOS-native Claude skills (CSKILL-017..022) | .claude/skills/ |
| Policy and Law Knowledge System | 09_AI_Systems/02_Tools/Policy_Knowledge/ |
| Capability Benchmark v1 | 09_AI_Systems/02_Tools/Capability_Benchmark/ |
| Pod tooling (POD-001) | 09_AI_Systems/02_Tools/Pod_Tools/ |

---

# 4. Success Criteria

1. Skill router classifies representative tasks to the correct skill and mode, tested.
2. Policy retriever answers demo policy questions offline with source metadata and staleness warnings, tested.
3. Benchmark defines 100+ tasks and the deterministic-local mode produces an honest scored report.
4. All tests pass with the standard library only.

---

# 4B. Project Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Build pod tools and lifecycle documents (POD-001) | Done |
| 2 | Build skill router, routing standard, and six new AOS skills | Done |
| 3 | Build policy/law knowledge system with UAE demo pack | Done |
| 4 | Build and run the 103-task capability benchmark | Done |
| 5 | Founder review; pod activation decisions | Pending Founder |

---

# 5. Progress Log

| Date | Update |
|------|--------|
| 2026-07-14 | Project created. Pod tools, skill router, routing standard, new skills, policy system, and benchmark built. Awaiting Founder review. |

---

# 6. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial project record |
