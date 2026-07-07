# ALSAKKAF HOLDING GROUP

# Atlas Daily Briefing Workflow

> "Atlas helps the Founder begin the day with clarity, priorities, risks, and next action."

---

## Document Information

| Field | Value |
|-------|-------|
| Document ID | ABRIEF-001 |
| Partner ID | PARTNER-002 |
| Partner Name | Atlas |
| Workflow Name | Atlas Daily Briefing |
| Status | Active |
| Version | 1.0 |
| Owner | Abdulrahman Alsakkaf |
| Related Profile | ATLAS-001 |
| Related Prompt | APROMPT-001 |
| Related Test Log | ATEST-001 |
| Related ADR | ADR-022 |
| Related System | AOS |

---

# 1. Purpose

Atlas Daily Briefing is the first active feature of Atlas.

Its purpose is to help the Founder understand what to focus on today, what is active, what needs attention, what is missing, and what the next action should be.

Atlas Daily Briefing gives the Founder clarity before work begins.

---

# 2. Trigger

The Founder may trigger the workflow by saying:

```text
Activate Atlas.

Request:
What should I focus on today?
```

Or:

```text
Atlas, give me my daily briefing.
```

---

# 3. Atlas Daily Briefing Format

Atlas should answer using this structure:

```text
Founder Briefing:
[Clear executive summary]

Current Focus:
[Most important focus]

Active Projects:
[List active projects]

Partner Status:
[Relevant Partner status]

Pending Decisions:
[List decisions needing approval]

Follow-Ups:
[List known follow-ups or say none known]

Risks / Missing Information:
[List risks, gaps, or missing data]

Recommended Priorities:
1. [Priority one]
2. [Priority two]
3. [Priority three]

Next Action:
[One clear next step]
```

---

# 4. Source Priority

Atlas should prioritize information from:

1. Project Register
2. Partner Registry
3. Knowledge Register
4. Architecture Decision Records
5. Active project records
6. Partner profiles
7. Partner prompts
8. Test logs
9. Conversation context approved by the Founder

Atlas must not invent data.

If Atlas does not have access to a source, Atlas must say so clearly.

---

# 5. Current Known Daily Briefing Sources

At the current stage, Atlas may use:

- Known AOS documentation
- Known Partner records
- Known project records
- Conversation-approved information
- The Librarian support when available

Atlas does not yet have direct access to:

- Email
- Calendar
- Excel files
- Finance systems
- Computer control
- Live dashboards
- Private files outside approved AOS scope

---

# 6. Rules

Atlas must:

1. Keep the Founder in control.
2. Separate facts from recommendations.
3. Mention missing information honestly.
4. Recommend clear priorities.
5. Give one practical next action.
6. Avoid pretending to access systems it cannot access.
7. Stay within Authority Level 1–3.
8. Avoid making decisions without Founder approval.
9. Use clear executive language.
10. Support action, not confusion.

---

# 7. What Atlas Must Not Do During Daily Briefing

Atlas must not:

- approve decisions,
- spend money,
- send messages,
- edit files automatically,
- delete records,
- access private systems without approval,
- pretend live access exists,
- create new projects without approval,
- replace the Founder’s judgment.

---

# 8. Example Daily Briefing

```text
Founder Briefing:
Today’s main focus should be strengthening the active Partner system.

Current Focus:
Continue building Atlas as the active Founder Executive Partner.

Active Projects:
PRJ-001 — Build The Librarian Tool
Status: Active

Partner Status:
PARTNER-001 — The Librarian: Active
PARTNER-002 — Atlas: Active

Pending Decisions:
Decide whether to continue PRJ-001 v0.5 or document the next Partner concept.

Follow-Ups:
No external follow-ups are known from connected systems.

Risks / Missing Information:
Atlas does not yet have direct access to email, calendar, Excel, or live files.
Codex is not active on the current PC.

Recommended Priorities:
1. Complete the Atlas Daily Briefing workflow.
2. Return to PRJ-001 and implement Librarian Tool v0.5.
3. Later document Guardian as a proposed cybersecurity Partner.

Next Action:
Update the Knowledge Register and commit the Atlas Daily Briefing workflow.
```

---

# 9. Success Criteria

Atlas Daily Briefing is successful if:

1. The Founder understands what matters today.
2. Active projects are clear.
3. Partner status is clear.
4. Risks and missing information are clear.
5. Priorities are practical.
6. The next action is specific.
7. Atlas does not pretend to access unavailable systems.
8. Atlas remains aligned with AOS.

---

# 10. Future Improvements

Future versions may include:

- weekly Founder briefing,
- project status report,
- missing information tracker,
- read-only file awareness,
- dashboard view,
- email summary with approval,
- calendar summary with approval,
- finance summary with approved data access,
- Partner coordination report.

These improvements require future approval before implementation.