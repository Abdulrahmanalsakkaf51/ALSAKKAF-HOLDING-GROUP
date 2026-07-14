# ALSAKKAF HOLDING GROUP

# AOS Policy and Law Knowledge System

> "Managers get controlled access to policy knowledge. Humans make the legal decisions."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | PLK-001 |
| Document Type | System Definition |
| Status | Active (demo knowledge pack) |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-014 |
| Related Documents | CSKILL-019, CSKILL-020, SRS-001 |

---

# 1. Purpose

Give managers (and the future Manager Partner) controlled access to company policies, employment rules, leave policies, working-hours rules, procedures, and jurisdiction-specific law references — with full source metadata, staleness warnings, and hard human-review gates.

This system does not "memorize one labour law". It indexes knowledge items, each carrying its own jurisdiction, source, and verification dates.

---

# 2. Metadata Contract

Every legal/policy knowledge item includes: Jurisdiction, Sector, Source, Official source URL, Effective date, Last verified date, Scope, Document version, Approval status. Items without complete metadata are rejected by the test suite.

---

# 3. Decision Rules

1. Approved company policy is preferred first, then the current official legal source reference.
2. The system NEVER makes final legal decisions.
3. LEGAL / HR REVIEW REQUIRED is flagged for: termination, discipline, disputes, salary decisions, medical/sensitive matters, and anything ambiguous.
4. No excessive copyrighted legal text is stored — summaries plus source metadata only.
5. Offline mode always displays SOURCE SNAPSHOT DATE and warns when items exceed the verification window (180 days).
6. Network freshness checks require Founder approval; the freshness checker is offline and only reports what humans must re-verify.

---

# 4. Components

| File | Role |
|------|------|
| policy_index.json | Demo knowledge pack (UAE private sector, 8 categories) |
| policy_retriever.py | Search with metadata, staleness, and review flags |
| policy_freshness_checker.py | Offline re-verification report |
| people_operations_calculator.py | Deterministic leave/probation/notice calculators |
| test_policy_retriever.py | Test suite |

---

# 5. Demo Pack Honesty

The included UAE private-sector pack is a DEMO KNOWLEDGE PACK: summaries referencing Federal Decree-Law No. 33 of 2021 (as amended) with MOHRE as the official source. Every item is marked "pending HR/legal verification" and must be verified against the official source before production use. Free-zone rules may differ and are out of demo scope.

---

# 6. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial system with UAE demo pack |
