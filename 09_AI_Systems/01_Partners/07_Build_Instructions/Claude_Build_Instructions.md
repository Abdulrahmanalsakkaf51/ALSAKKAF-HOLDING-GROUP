# ALSAKKAF HOLDING GROUP

# Claude Build Instructions

> "Claude should help build the tool, not redesign the institution."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | LBUILD-001 |
| Document Type | Claude Build Instructions |
| Status | Draft |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Partner | PARTNER-001 — The Librarian |
| Related Project | PRJ-001 — Build The Librarian Tool |
| Related Requirements | LREQ-001 |
| Related Workflow | LWORK-001 |
| Related Map | LMAP-001 |

---

# 1. Purpose

This document provides instructions for using Claude to help build the first practical version of The Librarian Tool.

The goal is to make Claude useful without allowing it to redesign AOS randomly.

Claude should follow the existing AOS documents, Partner rules, project requirements, and governance limits.

---

# 2. Build Goal

Claude should help build a simple first prototype of The Librarian Tool.

The first prototype should help the Founder find institutional knowledge faster.

The prototype should not be a full AI platform.

The prototype should begin simple, useful, and testable.

---

# 3. Current Project

The current project is:

```text
PRJ-001 — Build The Librarian Tool
```

The current Partner is:

```text
PARTNER-001 — The Librarian
```

The Librarian is already active as a prompt-based Partner.

This project aims to improve The Librarian into a practical working tool.

---

# 4. Claude Role

Claude should act as a software development assistant.

Claude may help with:

- Python code
- File reading
- Markdown parsing
- Local search
- Command-line tools
- Simple user input
- Simple output formatting
- Testing logic
- Code cleanup
- Documentation

Claude should not act as the CEO.

Claude should not approve decisions.

Claude should not change AOS architecture without instruction.

Claude should not create unnecessary complexity.

---

# 5. Required Source Documents

Claude should understand that these documents guide the build:

| Document ID | Document |
|------------|----------|
| LIB-001 | The Librarian Partner Profile |
| LPROMPT-001 | The Librarian Prompt |
| LTEST-001 | The Librarian Test Log |
| LMAP-001 | Librarian Document Map |
| LWORK-001 | Librarian Workflow |
| LREQ-001 | Librarian Tool Requirements |
| PRJ-001 | Build The Librarian Tool project record |
| POM-001 | Partner Operating Model |
| PREG-001 | Partner Registry |
| PWA-001 | Partner Workforce Architecture |
| PRJMODEL-001 | Project Operating Model |

---

# 6. Version 0.1 Prototype Scope

The first prototype should be called:

```text
Librarian Tool v0.1
```

It should be a simple local tool.

Preferred first form:

```text
Python command-line script
```

The prototype should:

1. Ask the user a question.
2. Search a basic document map.
3. Identify likely source documents.
4. Show related sources.
5. Show status when known.
6. Recommend what to review next.

---

# 7. Version 0.1 Out of Scope

Claude should not build these yet:

- Full web application
- Database system
- User login system
- Cloud deployment
- GitHub API connection
- Autonomous AI agent network
- Automatic document editing
- Automatic approval workflow
- Payment system
- Customer-facing product
- Multi-company dashboard

These may come later.

---

# 8. Required Output Format

The tool should produce answers in this format:

```text
Answer:
[Clear answer]

Primary Source:
[Main document or file]

Related Sources:
[Other related records]

Status:
[Approved / Active / Designed / Proposed / Draft / Missing / Needs Review]

Recommended Action:
[Next action]
```

---

# 9. First Prototype Behavior

The first prototype does not need to understand everything perfectly.

It should begin with a simple searchable knowledge map.

Example user input:

```text
Where is The Mind defined?
```

Expected output:

```text
Answer:
The Mind is defined in Digital DNA Chapter 9.

Primary Source:
DNA-001 / 01_Holding_Company/02_Digital_DNA/Digital_DNA.md — Chapter 9

Related Sources:
ADR-003
ADR-004
ADR-013
AOS-008
LANG-001
KNOW-020

Status:
Approved

Recommended Action:
Review Digital DNA Chapter 9 first, then check ADR-013.
```

---

# 10. First Data Source

The first coded prototype may begin by using a manually defined dictionary or JSON-like structure based on:

```text
LMAP-001 / Librarian_Document_Map.md
```

Claude may create a file such as:

```text
librarian_data.py
```

or:

```text
knowledge_map.json
```

The first version can be simple.

Accuracy and clarity are more important than advanced automation.

---

# 11. Suggested Prototype Files

Claude may create files such as:

```text
09_AI_Systems/01_Partners/08_Prototype/
```

Inside that folder:

```text
librarian.py
knowledge_map.json
README.md
```

Possible purpose:

| File | Purpose |
|------|---------|
| librarian.py | Main command-line script |
| knowledge_map.json | Structured knowledge map |
| README.md | How to run and test the prototype |

---

# 12. Suggested Command

The user should eventually be able to run:

```bash
python librarian.py
```

The tool should then ask:

```text
Ask The Librarian:
```

The user can type:

```text
What is AOS?
```

The tool returns a source-based answer.

---

# 13. Testing Questions

Claude should test the prototype using these questions:

1. What is AOS?
2. Where is Digital DNA documented?
3. Where is The Mind defined?
4. What is the Partner Operating Model?
5. Which ADR approved the Partner Registry?
6. Where is the 30-Partner Company Cell explained?
7. What is The Librarian allowed to do?
8. What is The Librarian not allowed to do?
9. Which document should be updated when a new Partner is created?
10. Is The Librarian active, designed, proposed, or approved?

These questions come from LTEST-001.

---

# 14. Coding Rules for Claude

Claude must follow these rules:

1. Keep the first version simple.
2. Do not redesign AOS.
3. Do not create extra folders without explaining why.
4. Do not use unnecessary frameworks.
5. Do not require paid APIs for version 0.1.
6. Do not delete or overwrite official documents.
7. Do not make the tool approve decisions.
8. Do not present guesses as official knowledge.
9. Use clear file paths.
10. Explain how to run the prototype.

---

# 15. Human Approval Rule

Claude may propose code.

Claude may write code.

Claude may suggest improvements.

But the Founder / CEO must approve:

- New tool behavior
- New Partner status changes
- New official documents
- Any automation that changes files
- Any integration with external services

Human accountability remains required.

---

# 16. First Claude Prompt

When ready to use Claude, paste this into Claude:

```text
You are helping build PRJ-001 — Build The Librarian Tool for ALSAKKAF HOLDING GROUP.

Do not redesign the company or AOS.

Your role is to help create a simple Python command-line prototype called Librarian Tool v0.1.

The tool should help users ask questions about institutional knowledge and return:

Answer:
Primary Source:
Related Sources:
Status:
Recommended Action:

The first version should use a simple local knowledge map based on the Librarian Document Map.

Do not build a web app.
Do not use paid APIs.
Do not create autonomous agents.
Do not edit official documents automatically.
Keep the prototype simple, local, and testable.

Suggested files:
- librarian.py
- knowledge_map.json
- README.md

The prototype should support these test questions:
1. What is AOS?
2. Where is Digital DNA documented?
3. Where is The Mind defined?
4. What is the Partner Operating Model?
5. Which ADR approved the Partner Registry?
6. Where is the 30-Partner Company Cell explained?
7. What is The Librarian allowed to do?
8. What is The Librarian not allowed to do?
9. Which document should be updated when a new Partner is created?
10. Is The Librarian active, designed, proposed, or approved?

Before writing code, propose the simplest file structure and explain why.
```

---

# 17. Claude Build Principle

> Claude should help turn approved requirements into working tools.

---

# 18. Claude Build Rule

Do not ask Claude to build advanced automation until the simple local prototype works and passes tests.