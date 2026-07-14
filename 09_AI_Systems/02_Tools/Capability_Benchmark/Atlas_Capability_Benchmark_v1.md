# ALSAKKAF HOLDING GROUP

# Atlas Capability Benchmark v1

> "We do not claim. We measure."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | ACB-001 |
| Document Type | Benchmark Definition |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-014 |
| Related Documents | ACB-REPORT-001, SRS-001, PRT-001 |

---

# 1. Purpose

Measure what Atlas can actually complete across realistic company tasks, honestly, per execution mode. Forbidden phrasing: "Atlas is X% as good as ChatGPT." Required phrasing: "Atlas Local completed X of N benchmark tasks within acceptance criteria."

---

# 2. Benchmark Design

103 realistic tasks across 13 categories: office administration, Excel, Word, files, email drafting, research, reporting, management, HR/policy retrieval, project operations, sales operations, knowledge retrieval, quality control.

Each task defines: ID, category, description, runner, parameters, acceptance criteria. Tasks that genuinely need judgment, negotiation, or generation are marked `requires_ai` (or `requires_ai_and_human`) and count as NOT completed in deterministic mode — by design.

---

# 3. Test Modes

| Mode | Status |
|------|--------|
| DETERMINISTIC LOCAL | Runs today (run_benchmark.py) |
| LOCAL AI | Pending Founder-approved local model server |
| HYBRID | Pending local/cloud adapters enablement |
| CLOUD REFERENCE | Pending Founder approval (env-var keys only) |

---

# 4. Scoring

Recorded per task: completion (True/False/requires-AI), execution time, harness error if any. Cost is $0.00 in deterministic mode. Accuracy, format quality, human-correction counts, and approval compliance are scored per-mode when AI modes are enabled.

---

# 5. First Result (2026-07-14)

Atlas Local (deterministic, offline, standard library only) completed **81 of 103** tasks within acceptance criteria; 0 failed; 22 require an AI model. Full breakdown: `Benchmark_Report_v1.md` (ACB-REPORT-001).

---

# 6. Files

| File | Role |
|------|------|
| benchmark_tasks.py | 103 task definitions |
| benchmark_runners.py | Deterministic runners using the real tools |
| run_benchmark.py | Runner + honest report writer |
| test_capability_benchmark.py | Smoke tests |
| Benchmark_Report_v1.md | First results report |

---

# 7. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial benchmark and first deterministic run |
