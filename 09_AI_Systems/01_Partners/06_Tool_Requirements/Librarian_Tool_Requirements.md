# ALSAKKAF HOLDING GROUP

# Librarian Tool Requirements

> "Do not code the tool before the institution understands what the tool must do."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | LREQ-001 |
| Document Type | Librarian Tool Requirements |
| Status | Draft |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Partner | PARTNER-001 — The Librarian |
| Related Project | PRJ-001 — Build The Librarian Tool |
| Related Workflow | LWORK-001 |
| Related Map | LMAP-001 |

---

# 1. Purpose

This document defines the first requirements for The Librarian Tool.

The goal is to prepare clear requirements before using Claude or any coding tool.

The Librarian Tool should help ALSAKKAF HOLDING GROUP search, understand, and reference institutional knowledge more easily.

---

# 2. Current Stage

The Librarian is currently active as a prompt-based Partner.

This means The Librarian can already be used inside ChatGPT by typing:

```text
Activate The Librarian.

Question:
[Your question]
```

The next step is to make The Librarian easier to reuse, test, and later connect to the project files.

---

# 3. Problem

ALSAKKAF HOLDING GROUP now has many documents, records, lessons, ADRs, Partner files, and project files.

As the institution grows, it will become harder to remember:

- Where each document is located
- Which document is the primary source
- Which ADR approved a decision
- Which Partner is active, designed, or proposed
- Which project records exist
- Which knowledge is approved, draft, designed, proposed, or missing

The Librarian Tool should reduce confusion and help the Founder find institutional knowledge faster.

---

# 4. Tool Goal

The goal of The Librarian Tool is to help users ask questions about AOS and receive answers that include:

- Clear answer
- Primary source
- Related sources
- Status
- Recommended action

The tool should support institutional knowledge discovery.

It should not replace human decision-making.

---

# 5. Users

The first user is:

- Founder / CEO

Future users may include:

- Collaborators
- Managers
- Supervisors
- Partners
- Project owners
- AOS University learners

---

# 6. Version 1 Scope

Version 1 should be simple.

Version 1 may include:

- Manual document map
- Reusable prompt
- Standard answer format
- Source priority rules
- Simple local document search later
- Basic testing questions
- Clear status definitions

Version 1 does not need to be a full AI platform.

---

# 7. Out of Scope for Version 1

Version 1 does not include:

- Full web application
- Customer-facing product
- Multi-user system
- Paid SaaS platform
- Autonomous agents
- Automatic document editing
- Automatic approval of decisions
- Legal or financial decision-making
- Sensitive data automation
- Direct GitHub integration unless specifically approved later

---

# 8. Required Knowledge Sources

The Librarian Tool should be designed around these sources:

| Priority | Source | Purpose |
|----------|--------|---------|
| 1 | Knowledge Register | Master index of institutional knowledge |
| 2 | Librarian Document Map | Map of key documents and locations |
| 3 | Digital DNA | Main AOS architecture |
| 4 | Company Constitution | Purpose and principles |
| 5 | Company Language Standard | Official terminology |
| 6 | Architecture Decision Log | ADR index |
| 7 | ADR Files | Decision reasons |
| 8 | AOS University | Lessons and onboarding |
| 9 | Partner Operating Model | Partner governance |
| 10 | Partner Registry | Partner status and list |
| 11 | Partner Workforce Architecture | Partner company structure |
| 12 | Partner Profiles | Partner definitions |
| 13 | Partner Prompts | Partner instructions |
| 14 | Partner Test Logs | Testing records |
| 15 | Project Operating Model | Project governance |
| 16 | Project Register | Project list |
| 17 | Project Records | Project execution knowledge |

---

# 9. Required Answer Format

The Librarian Tool should answer using this structure:

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

# 10. Status Rules

The tool must clearly distinguish between statuses.

| Status | Meaning |
|--------|---------|
| Approved | Officially accepted institutional knowledge |
| Active | Currently in use |
| Designed | Designed but not fully active or tested |
| Proposed | Idea exists but has not been approved |
| Draft | Work exists but is still being prepared |
| Missing | No official document exists |
| Needs Review | Existing information may need checking or updating |

The tool must not present proposed, draft, or missing knowledge as approved.

---

# 11. Required Features

The first practical version should support these features:

| Feature | Description | Priority |
|---------|-------------|----------|
| Ask a question | User asks a question about AOS knowledge | High |
| Identify source | Tool identifies the best source document | High |
| Identify related sources | Tool lists related documents | High |
| Identify status | Tool identifies whether knowledge is approved, active, designed, proposed, draft, or missing | High |
| Recommend action | Tool suggests what the user should do next | High |
| Use document map | Tool uses the Librarian Document Map | High |
| Use Knowledge Register | Tool uses the Knowledge Register as master index | High |
| Avoid invented approvals | Tool avoids treating undocumented knowledge as approved | High |
| Support testing | Tool can be tested with standard questions | High |
| Prepare for coding | Requirements are clear enough for Claude to help build | High |

---

# 12. Future Features

Later versions may include:

- Local folder search
- Markdown file indexing
- Search by document ID
- Search by Partner ID
- Search by Project ID
- Search by ADR number
- Search by knowledge status
- GitHub repository connection
- Simple command-line interface
- Simple web interface
- Dashboard integration
- Multi-company knowledge search
- Partner-to-Partner knowledge support

---

# 13. Possible Tool Forms

The Librarian Tool may develop through stages.

| Stage | Tool Form | Description |
|------|-----------|-------------|
| Stage 1 | Prompt-based Partner | Used inside ChatGPT |
| Stage 2 | Manual workflow | User follows documented workflow |
| Stage 3 | Local script | Simple Python tool reads local files |
| Stage 4 | Search helper | Tool searches Markdown files |
| Stage 5 | Repository-connected tool | Tool reads GitHub or local repository |
| Stage 6 | Dashboard-connected Partner | Tool becomes part of a larger AOS dashboard |

The current project focuses on preparing Stage 2 and Stage 3.

---

# 14. First Prototype Requirement

The first coded prototype should be simple.

A possible first prototype may:

1. Ask the user for a question.
2. Search a document map.
3. Return likely source documents.
4. Show related records.
5. Show status if available.
6. Recommend what to review next.

The first prototype does not need to answer perfectly.

It needs to help the Founder find the right document faster.

---

# 15. Input Requirements

The tool may accept:

- User question
- Document ID
- Partner ID
- Project ID
- ADR number
- Knowledge ID
- Keyword

Examples:

```text
What is AOS?
Where is The Mind defined?
ADR-017
PARTNER-001
KNOW-024
Project Operating Model
```

---

# 16. Output Requirements

The tool should produce:

- Answer
- Primary source
- Related sources
- Status
- Recommended action

Optional future outputs:

- File path
- Document summary
- Confidence level
- Missing knowledge warning
- Suggested register update

---

# 17. Governance Requirements

The Librarian Tool must follow AOS governance.

It must not:

- Approve decisions
- Change files automatically without approval
- Delete records
- Replace the Knowledge Register
- Replace the Founder / CEO
- Treat guesses as official knowledge
- Present proposed knowledge as approved

---

# 18. Testing Requirements

The tool should be tested using the existing Librarian test questions.

The first test set includes:

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

The tool should pass these tests before being considered reliable.

---

# 19. Claude Build Role

Claude may later help with:

- Writing Python code
- Reading Markdown files
- Creating a simple command-line tool
- Creating a search function
- Creating a document index
- Improving prompts
- Testing the prototype
- Refactoring the tool

Claude should not be asked to build the full system before the requirements are clear.

---

# 20. Success Criteria

This requirements document succeeds if:

1. The tool purpose is clear.
2. The first version is simple.
3. The scope is controlled.
4. The sources are known.
5. The output format is defined.
6. The governance limits are clear.
7. The testing method is defined.
8. Claude can later use this document to help build the first prototype.

---

# 21. Requirements Principle

> The first Librarian Tool should be useful before it becomes advanced.

---

# 22. Requirements Rule

Do not build advanced automation before the manual workflow, source map, and basic requirements are clear.