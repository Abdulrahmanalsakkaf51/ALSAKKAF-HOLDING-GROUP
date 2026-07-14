# ALSAKKAF HOLDING GROUP

# PRJ-012 — AOS Partner Runtime v1

> "A Partner is a role with rules. The Runtime is the machine that executes the role inside the rules."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRJ-012 |
| Document Type | Project Record |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Approved By | Founder (build); activation of Partners still requires Founder approval |
| Related System | AOS |
| Related Projects | PRJ-006, PRJ-011, PRJ-013 |
| Related Documents | APFA-001, PCL-001, PRCC-001, PREG-001 |

---

# 1. Objective

Build the first executable AOS Partner Runtime: a local engine that loads Partner definitions (role, instructions, permissions, tools, workflow, memory rules, approval rules) and executes their workflows safely.

A Partner is NOT a separate AI subscription. A Partner is a defined role executed by shared runtime infrastructure.

---

# 2. Architecture

| Layer | File | Responsibility |
|-------|------|----------------|
| Engine / CLI | partner_runtime.py | Entry point, mode selection, command handling |
| Partner loader | partner_loader.py | Load and validate Partner definition files |
| Workflow runner | workflow_runner.py | Execute workflow steps through tools and gates |
| Tool layer | tool_registry.py | Deterministic local tools with safety flags |
| Approval gates | approval_gate.py | Queue approval requests; nothing restricted executes unapproved |
| Logs | runtime_logger.py | JSONL run logs |
| Memory | memory_store.py | SQLite-backed Partner memory with memory rules |
| Provider adapter | provider_adapter.py | Cloud AI adapter — env-var keys only, disabled by default |
| Local model adapter | local_model_adapter.py | Local inference server adapter — no auto-install |
| Task router | task_router.py | Routes tasks to the cheapest capable mode |
| Tests | test_partner_runtime.py | Unit tests for all of the above |

---

# 3. Execution Modes

| Mode | Name | Status | Requires |
|------|------|--------|----------|
| 1 | DETERMINISTIC DEMO | Works today | Nothing — no AI, no network |
| 2 | LOCAL MODEL | Architecture ready | An approved local model server, configured by the Founder |
| 3 | CLOUD PROVIDER | Architecture ready | API key in an environment variable + Founder approval to enable network |
| 4 | HYBRID | Architecture ready | Modes 2/3 configured; deterministic tools always tried first |

Keys are never stored in the repository. Network use is disabled by default.

---

# 4. Success Criteria

1. `py partner_runtime.py demo` runs a full deterministic Partner workflow with logs and approval queue output.
2. Restricted steps never execute without an approval record.
3. All tests pass with the standard library only.
4. No credentials anywhere in the code or config.

---

# 4B. Project Tasks

| # | Task | Status |
|---|------|--------|
| 1 | Build runtime engine, loader, workflow runner, tool registry | Done |
| 2 | Build approval gate, logger, memory store, task router | Done |
| 3 | Build local-model and cloud adapters (disabled by default) | Done |
| 4 | Write sample Partner definitions and 17-test suite | Done |
| 5 | Founder review; enable AI modes when approved | Pending Founder |

---

# 5. Progress Log

| Date | Update |
|------|--------|
| 2026-07-14 | Project created. Runtime engine, loader, tools, gates, memory, adapters, router, sample Partner definitions, and tests built. Awaiting Founder review. |

---

# 6. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial project record |
