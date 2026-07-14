# ALSAKKAF HOLDING GROUP

# AOS Partner Runtime v1

> "A Partner is a role with rules. The Runtime is the machine that executes the role inside the rules."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PRT-001 |
| Document Type | Tool README |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-012 |
| Related Documents | APFA-001, PCL-001, PRCC-001, PREG-001 |

---

# 1. What This Is

The first executable AOS Partner Runtime. It loads Partner definitions (role, instructions, tools, permissions, workflows, memory rules, approval rules) from `partners/*.json` and executes their workflows locally.

A Partner is NOT a separate AI subscription. A Partner is a role definition executed by this shared runtime.

Python 3.12 standard library only. No packages. No API keys in files, ever.

---

# 2. Quick Start

Run from this folder:

```text
py partner_runtime.py list
py partner_runtime.py demo
py partner_runtime.py run PARTNER-007 morning-intake
py partner_runtime.py approvals
py partner_runtime.py modes
py test_partner_runtime.py
```

---

# 3. Execution Modes

| Mode | Name | Status today |
|------|------|--------------|
| 1 | DETERMINISTIC DEMO | Working — no AI, no network |
| 2 | LOCAL MODEL | Adapter ready; requires a Founder-approved local model server and `runtime_config.json` enablement |
| 3 | CLOUD PROVIDER | Adapter ready; requires an API key in an environment variable and Founder enablement |
| 4 | HYBRID | Router ready; deterministic tools first, then local, then economical cloud, strong cloud last |

To enable AI modes, the Founder creates `runtime_config.json` (see `DEFAULT_CONFIG` in `partner_runtime.py`). Keys live only in environment variables such as `AOS_CLOUD_API_KEY`.

---

# 4. Safety Model

1. Approval gate: restricted actions (send email, publish, external commitments) never execute without an approval record in `Runtime_State/approvals_queue.json`. The gate never auto-approves.
2. Tool allowlists: a Partner may only call tools listed in its own definition.
3. Authority ceiling: definitions above Level 3 are rejected at load time (PREG-001 foundation rule).
4. Output sandbox: draft-writing tools cannot escape the runtime output folder.
5. Memory guard: memory refuses values that look like credentials.
6. Log redaction: secret-looking fields are redacted in logs.
7. Duplicate Partner IDs are rejected at load time.

---

# 5. Folder Layout

| Path | Purpose |
|------|---------|
| partners/ | Partner definition JSON files |
| Runtime_State/ | Local state: approvals queue, memory DB, logs, outputs (not official records) |
| partner_runtime.py | CLI and engine assembly |
| workflow_runner.py | Step execution with approval gates |
| tool_registry.py | Deterministic tool layer |
| approval_gate.py | Human approval queue |
| memory_store.py | SQLite Partner memory |
| provider_adapter.py / local_model_adapter.py | AI adapters (disabled by default) |
| task_router.py | Hybrid mode routing |
| test_partner_runtime.py | Test suite |

---

# 6. Relationship to the Partner Factory

Definitions in `partners/` mirror Partners documented in the Partner Registry (PREG-001) and follow the Partner Creation Lifecycle (PCL-001). A definition here does not make a Partner Active — activation still requires the full lifecycle and Founder approval.

---

# 7. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial runtime |
