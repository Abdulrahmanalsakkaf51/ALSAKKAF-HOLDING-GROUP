# Librarian Tool v0.2

This is the first local prototype of PARTNER-001 — The Librarian.

The tool helps users ask questions about AOS institutional knowledge and receive:

- Answer
- Primary Source
- Related Sources
- Status
- Recommended Action

---

## How to Run

Open PowerShell in this folder:

```text
09_AI_Systems/01_Partners/08_Prototype
```

Run:

```bash
python librarian.py
```

If `python librarian.py` does not work on Windows, use:

```bash
py librarian.py
```

Then ask a question, such as:

```text
What is AOS?
```

To close the tool, type:

```text
exit
```

---

## Current Scope

This version uses a simple local knowledge map:

```text
knowledge_map.json
```

It does not yet read all Markdown files automatically.

It does not edit documents.

It does not approve decisions.

---

## Version 0.2 Improvement

Version 0.2 improves the search logic.

It adds:

- Better keyword matching
- Match score
- Help command
- Suggested related topics when no strong match is found

To see example questions, run the tool and type:

```text
help