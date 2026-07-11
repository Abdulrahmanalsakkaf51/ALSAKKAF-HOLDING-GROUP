---
name: aos-release-manager
description: Use this skill when preparing safe release summaries — git status reviews, diff summaries, commit message suggestions, and push-readiness checks. It must never commit or push without explicit Founder approval.
---

# AOS Release Manager Skill

## Document Information

| Field | Value |
|-------|-------|
| Document ID | CSKILL-015 |
| Skill Name | aos-release-manager |
| Document Type | Claude Skill |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Protocol | OPS-001 |
| Related Document | STRAT-003, STRAT-004 |

---

# Purpose

This skill helps Claude prepare everything needed for the Founder to decide whether to commit and push — status review, diff summary, a drafted commit message, and a push-readiness check — without ever executing the commit or push itself.

---

# What This Skill Produces

| Output | Format |
|--------|--------|
| Status Review | Summary of `git status`: staged, unstaged, untracked files, grouped by area |
| Diff Summary | Plain-language summary of what changed and why, file by file or by logical group |
| Commit Message Draft | Conventional, concise message (what changed and why), ready for Founder approval |
| Push-Readiness Check | Checklist: Markdown Audit clean, register updated, no credentials/secrets staged, branch correct |

---

# Required Behavior

1. Always run `git status` and review it before summarizing — never assume what changed.
2. Flag any file that looks like it could contain a secret (`.env`, `credentials`, API key patterns) before it's included in a commit summary, and recommend it be excluded.
3. Commit message drafts should explain *why*, not just *what*, consistent with the repository's commit style.
4. Push-Readiness Check must confirm the Markdown Audit was run (if Markdown changed) and that any new official document has its register row, before saying "ready."
5. Present the final summary clearly enough that the Founder can approve with a simple yes/no.

---

# Boundaries

Do not, under this skill:

- run `git commit` or `git push` — ever, regardless of how confident the readiness check looks,
- run any destructive git command (`reset --hard`, `push --force`, `checkout --`, `clean -f`, `branch -D`) without explicit, separate Founder instruction,
- stage or recommend staging a file containing credentials or secrets,
- mark a release "ready" while the Markdown Audit shows any issues on changed files.

---

# Related Documents

- 09_AI_Systems/02_Tools/Markdown_Audit/markdown_audit.py
- .claude/skills/aos-qa-auditor/SKILL.md
- .claude/skills/aos-live-build/SKILL.md
- 01_Holding_Company/03_Strategy/AOS_Claude_Skill_Roadmap.md
- CLAUDE.md

---

# Revision History

| Version | Date | Changes |
|----------|------|----------|
| 1.0 | 2026-07-12 | Initial version |

---
