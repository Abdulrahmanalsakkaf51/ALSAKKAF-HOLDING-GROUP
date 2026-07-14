# ALSAKKAF HOLDING GROUP

# Private Operational Data Standard

> "The public repository shows how we work. Private storage holds who we work on."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PODS-001 |
| Document Type | Governance Standard |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Project | PRJ-016 |
| Related Documents | GRCA-001, PAW-004, OPS-001 |

---

# 1. Purpose

The main repository is public: it serves alsakkafsystems.com and showcases AOS architecture. This standard defines exactly what may live there and what must live only in private operational storage.

---

# 2. PUBLIC REPOSITORY — allowed content

| Category | Examples |
|----------|----------|
| Website | docs/ pages, brand assets, Playground |
| Software | Tools, runtimes, tests — code only, no embedded data |
| Templates | Blank trackers, outreach templates, document templates |
| Architecture | System designs, standards, project records, ADRs |
| Blank trackers | CSVs containing headers and clearly-marked fictional template rows only |
| Synthetic demonstrations | Fictional examples labeled as fictional (e.g., PAW-005) |
| Aggregate non-sensitive metrics | "10 prospects verified", "0 messages sent", "$0 revenue" |
| Partner documentation | Profiles, prompts, skills, test logs (sanitized of real third-party names), activation governance |

---

# 3. PRIVATE OPERATIONS — never committed publicly

| Category | Examples |
|----------|----------|
| Real prospects | Company names, websites, queue records |
| Internal assessments | Workflow hypotheses and evaluations about named companies |
| Outreach drafts | Personalized messages, recipient addresses, contact names |
| Pipeline data | Real tracker rows, deal status, quoted prices |
| Client data | Anything a client gives us, always |
| Contact research | Decision-maker names, emails, phone numbers gathered in research |
| Private reports | Founder briefings and checklists naming real third parties |

Location: `ALSAKKAF PRIVATE OPERATIONS/` (outside the repository; not a Git repository). Credentials, passwords, API keys, and recovery codes are stored NOWHERE in either location — they live only in the Founder's password manager.

---

# 4. Hard Rules

1. No private operational data may be committed to the public repository — no exceptions, including "temporary" ones.
2. Public tracker files hold template rows only; real rows live in the private store.
3. Public documents referring to prospects use aggregate counts or fictional examples only.
4. Partner test logs cite evidence by private-storage path, never by third-party name.
5. Before every commit, the privacy test suite and a name-scan must pass (test_revenue_operations_week.py).
6. If private data is ever committed by mistake: treat as an incident — remove, rewrite history if feasible, and log with Guardian.

---

# 5. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial standard, created during PRJ-016 privacy separation |
