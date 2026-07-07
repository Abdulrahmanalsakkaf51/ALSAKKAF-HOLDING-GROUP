# ALSAKKAF HOLDING GROUP

# Librarian Tool v0.5 Plan

> "Before improving a tool, define what improvement means."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | LPLAN-001 |
| Document Type | Prototype Improvement Plan |
| Tool | Librarian Tool |
| Planned Version | v0.5 |
| Status | Draft |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Project | PRJ-001 — Build The Librarian Tool |
| Related Prototype | Librarian Tool v0.4 |
| Related Test Log | LPROTO-TEST-001 |

---

# 1. Purpose

This document defines the improvement plan for Librarian Tool v0.5.

The goal is to improve Markdown file search quality before making the tool more advanced.

Version 0.4 successfully added Markdown file search.

Version 0.5 should improve how search results are ranked.

---

# 2. Why v0.5 Is Needed

During v0.4 testing, the command:

```text
search The Mind
```

successfully returned relevant files.

However, it also returned test logs as high-ranking results.

Test logs are useful, but they should not usually appear above primary institutional sources unless the user specifically asks about testing.

The Librarian should prioritize official knowledge sources first.

---

# 3. Main Problem

The current search finds matching text, but it does not fully understand document priority.

For example, when searching for institutional knowledge, the tool should usually prioritize:

1. Knowledge Register
2. Digital DNA
3. Governance documents
4. ADR files
5. Partner documents
6. Project records
7. AOS University lessons
8. Test logs

Test logs should be lower priority unless the user searches for:

- test
- testing
- log
- prototype test
- regression

---

# 4. v0.5 Goal

Librarian Tool v0.5 should improve search results by ranking official sources higher than support records.

The tool should still search all Markdown files, but it should show more useful results first.

---

# 5. v0.5 Scope

Version 0.5 may include:

- File path priority scoring
- Document type priority scoring
- Lower priority for test logs during normal searches
- Higher priority for test logs when the query mentions testing
- Cleaner search result ranking
- Updated README documentation
- Updated prototype test log

---

# 6. Out of Scope

Version 0.5 should not include:

- Full AI model integration
- Paid APIs
- Web application
- Database system
- Auto-editing official documents
- GitHub API connection
- Multi-user dashboard
- Autonomous decision-making

v0.5 should remain simple, local, and testable.

---

# 7. Proposed Search Priority

The tool should rank files using priority groups.

| Priority | Source Type | Example |
|----------|-------------|---------|
| Highest | Knowledge Register | Knowledge_Register.md |
| Highest | Digital DNA | Digital_DNA.md |
| High | Governance records | Company_Constitution.md, Company_Language_Standard.md |
| High | ADR files | ADR-016_Partner_Registry.md |
| High | Partner core documents | Partner_Operating_Model.md, Partner_Registry.md |
| Medium | Project records | PRJ-001_Build_The_Librarian_Tool.md |
| Medium | AOS University lessons | AOS-008_The_Mind.md |
| Medium | Prototype README / plan files | README.md, v0.5 plan |
| Lower | Test logs | Prototype_Test_Log.md, Librarian Test Log |

---

# 8. Test Log Rule

Test logs should be included normally only when the user asks about testing.

Examples that should prioritize test logs:

```text
search Librarian test
search prototype test
search regression test
search Test 010
```

Examples that should not prioritize test logs:

```text
search The Mind
search PRJ-001
search Partner Registry
```

---

# 9. Success Criteria

v0.5 is successful if:

1. `search The Mind` returns Digital DNA and official The Mind records before test logs.
2. `search PRJ-001` returns project records and Knowledge Register before test logs.
3. `search Librarian test` returns test logs when testing is the user's intent.
4. Normal knowledge-map questions still work.
5. Missing knowledge handling still works.
6. The tool remains simple and local.
7. No official documents are edited automatically.

---

# 10. Required Tests

After v0.5 is built, test:

```text
help
search The Mind
search PRJ-001
search Librarian test
What is AOS?
Tell me about something not documented yet
```

---

# 11. v0.5 Decision

The next code improvement should focus only on search ranking.

Do not add advanced features until search quality is more reliable.

---

# 12. v0.5 Principle

> Better search is not about finding more files.
>
> Better search is about finding the right files first.

---

# 13. v0.5 Rule

Do not connect The Librarian Tool to more systems until search ranking is reliable enough to guide users to the best institutional sources first.