# ALSAKKAF HOLDING GROUP

# Partner Request — Research Partner (Market Intelligence)

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | RSREQ-001 |
| Document Type | Partner Request |
| Status | Submitted for Founder review |
| Version | 1.0 |
| Date | 2026-07-14 |
| Owner | Abdulrahman Alsakkaf |
| Related Partner | PARTNER-004 |
| Related Project | PRJ-014 |

---

# 1. Partner Request Summary

| Field | Entry |
|-------|-------|
| Requested By | Founder (First Internal Operational Pod build) |
| Date of Request | 2026-07-14 |
| Related Project | PRJ-009, PRJ-014 |
| Urgency | High |

---

# 2. Problem This Partner Solves

PRJ-009 requires 25 verified leads, but no role owns lead verification quality: required fields, official-source checking, duplicate detection, and honest confidence labels. PARTNER-004 (Research Partner) already exists in the registry as Proposed — this request activates its lifecycle with a Market Intelligence focus rather than creating a duplicate role.

---

# 3. Proposed Role

Verify and enrich lead and market records so that outreach only ever runs on real, evidenced, non-duplicate leads.

---

# 4. Company or Department Served

ALSAKKAF Systems — AOS AI Services (revenue operations).

---

# 5. Expected Tasks

| Task | Frequency | Notes |
|------|-----------|-------|
| Verify new leads in Lead_Tracker.csv | Daily during sprints | research_verifier.py |
| Detect duplicate leads | Daily | By email, domain, company name |
| Flag missing evidence | Per lead | Problem Observed / Offer Match |
| Classify confidence (High/Medium/Low) | Per lead | Deterministic rules |

---

# 6. Data Needed

Lead_Tracker.csv and market intelligence documents (MKTI-001). No private client data, no credentials, no student data.

---

# 7. Sensitivity Level

Public/Internal: Yes. Confidential: No. Restricted: No.

---

# 8. Local/Online Behavior

Local-first: verification is fully deterministic and offline. Live website checks would require network approval and are out of scope for v1.

---

# 9. Estimated Cost Behavior

Local tool tier. Zero recurring cost.

---

# 10. Approval Needed

Founder review of this request: Yes. Budget approval: No (no paid tools).

---

# 11. Next Step

Proceed to Partner Profile (RSPROF-001). Activation only after Founder approval.

---

# 12. Revision History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-14 | Initial request |
