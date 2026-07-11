# ALSAKKAF HOLDING GROUP

# AOS Live Build Protocol

> "Move fast, but never outside control."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | OPS-001 |
| Document Type | Operating Protocol |
| Status | Active |
| Version | 1.0 |
| Date | 2026-07-10 |
| Owner | Abdulrahman Alsakkaf |
| Related System | AOS |
| Related Tool | Claude Code |
| Related Future Project | PRJ-006 — Build AOS Partner Factory |

---

# 1. Purpose

This protocol defines how the Founder and AI coding assistants should work together to build AOS faster and safer.

The goal is to achieve faster execution without losing control, structure, documentation quality, or Founder approval.

---

# 2. Live Build Flow

The standard live build flow is:

| Step | Action |
|------|--------|
| 1 | Inspect the current files |
| 2 | Understand the requested change |
| 3 | Prepare a short plan |
| 4 | Get Founder approval for significant changes |
| 5 | Edit only required files |
| 6 | Run local checks |
| 7 | Run Markdown Audit for Markdown files |
| 8 | Review changes |
| 9 | Commit only after approval |
| 10 | Push only after approval |

---

# 3. Approval Rules

Approval is required before:

- committing,
- pushing,
- deleting files,
- renaming official folders,
- changing project numbers,
- activating a Partner,
- changing official architecture,
- adding paid API usage,
- accessing sensitive data,
- editing credentials or secrets.

---

# 4. Allowed Fast Work

AI assistants may help quickly with:

- creating Markdown files,
- updating registers,
- fixing formatting,
- running Markdown Audit,
- building local Python tools,
- preparing test logs,
- drafting lessons learned,
- summarizing diffs,
- preparing safe commits.

---

# 5. Restricted Work

AI assistants must not independently:

- spend money,
- send emails,
- message people,
- access student records,
- connect to private accounts,
- control devices,
- publish ads,
- delete files,
- push code,
- create uncontrolled automation.

---

# 6. Audit Rule

Every important documentation update must pass the Markdown Audit Tool before commit.

Expected output:

| Item | Expected Result |
|------|-----------------|
| Issues found | 0 |
| Errors | 0 |
| Warnings | 0 |
| Info | 0 |

---

# 7. Git Rule

The Founder controls Git commits and pushes.

The assistant may prepare suggested commands, but the Founder approves and runs them.

---

# 8. Why This Protocol Matters

AOS is becoming larger.

Speed without control can damage the institution.

This protocol allows AOS to move faster while protecting:

- project history,
- knowledge quality,
- folder structure,
- Founder approval,
- future AI safety.

---

# 9. Status

This protocol is active.

It should guide Claude Code, Codex, future coding assistants, and Atlas technical workflows.