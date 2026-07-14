"""AOS Skill Router (PRJ-014). Standard library only.

Implements the Skill Routing Standard (SRS-001):

  Atlas → Skill Router → Task Classifier → Local Tools
        → Local Model if needed → Cloud Escalation if allowed

The router classifies a task description to:
  * a role skill (who thinks about it)
  * a local tool (what executes it deterministically, when one exists)
  * an execution mode recommendation (deterministic / local AI / cloud)

Usage:
  py skill_router.py "prepare the weekly pipeline report"
"""

import json
import sys

# Routing table: first matching rule wins. Keep business-idea/architecture
# checks before generic document rules so strategy work gets strategy skills.
ROUTING_RULES = [
    {"skill": "aos-ceo-command-center", "role": "CEO / strategy review",
     "keywords": ("business idea", "should we", "strategy", "priorit",
                  "revenue plan", "decision", "opportunity"),
     "tool": None, "mode": "judgment"},
    {"skill": "aos-cto-architect", "role": "CTO / engineering review",
     "keywords": ("architecture", "system design", "runtime", "integration",
                  "technical design", "infrastructure"),
     "tool": None, "mode": "judgment"},
    {"skill": "aos-policy-retriever", "role": "Policy retrieval",
     "keywords": ("policy", "labour law", "labor law", "leave", "probation",
                  "working hours", "termination", "sick", "gratuity"),
     "tool": "Policy_Knowledge/policy_retriever.py", "mode": "deterministic"},
    {"skill": "aos-people-operations", "role": "People operations",
     "keywords": ("employee", "people operations", "hr ", "onboarding",
                  "staff", "salary question"),
     "tool": "Policy_Knowledge/people_operations_calculator.py",
     "mode": "deterministic"},
    {"skill": "aos-client-acquisition-engine", "role": "Outreach",
     "keywords": ("outreach", "lead", "prospect", "cold email", "proposal"),
     "tool": "Pod_Tools/outreach_composer.py", "mode": "deterministic"},
    {"skill": "aos-reporting", "role": "Reporting",
     "keywords": ("report", "kpi", "metrics", "pipeline", "briefing",
                  "dashboard"),
     "tool": "Pod_Tools/pipeline_reporter.py", "mode": "deterministic"},
    {"skill": "aos-office-operator", "role": "Spreadsheet engineering",
     "keywords": ("spreadsheet", "xlsx", "excel", "workbook", "tracker"),
     "tool": "Office_Toolbelt/spreadsheet_tool.py", "mode": "deterministic"},
    {"skill": "aos-document-engineer", "role": "Document engineering",
     "keywords": ("docx", "word document", "meeting minutes", "letter",
                  "official document", "restructure the document"),
     "tool": "Office_Toolbelt/document_tool.py", "mode": "deterministic"},
    {"skill": "aos-office-operator", "role": "Email drafting",
     "keywords": ("email", "reply", "follow-up", "inbox", "draft a response"),
     "tool": "Office_Toolbelt/email_draft_tool.py", "mode": "deterministic"},
    {"skill": "aos-file-librarian", "role": "File organization",
     "keywords": ("organize", "folder", "filing", "duplicate", "rename",
                  "archive", "index the"),
     "tool": "Office_Toolbelt/file_organizer.py", "mode": "deterministic"},
    {"skill": "aos-task-planner", "role": "Task planning",
     "keywords": ("plan the day", "daily plan", "task plan", "assign tasks",
                  "schedule the team", "backlog"),
     "tool": "Department_Supervisor/department_supervisor.py",
     "mode": "deterministic"},
    {"skill": "aos-office-operator", "role": "Office operations",
     "keywords": ("office", "admin", "clean the data", "csv", "register"),
     "tool": "Office_Toolbelt/data_cleaning_tool.py", "mode": "deterministic"},
]

QA_RULE = {"skill": "aos-qa-auditor", "role": "Quality review",
           "keywords": ("review the output", "final check", "quality"),
           "tool": None, "mode": "judgment"}
RELEASE_RULE = {"skill": "aos-release-manager", "role": "Release",
                "keywords": ("commit", "release", "push", "publish the site"),
                "tool": None, "mode": "judgment"}

FALLBACK = {"skill": "aos-holding-company-operator", "role": "General operator",
            "tool": None, "mode": "needs_ai"}


def classify(task_text):
    """Return the routing decision for a task description."""
    low = " %s " % (task_text or "").lower()
    for rule in [QA_RULE, RELEASE_RULE] + ROUTING_RULES:
        if any(k in low for k in rule["keywords"]):
            return {"task": task_text, "skill": rule["skill"],
                    "role": rule["role"], "local_tool": rule["tool"],
                    "mode": rule["mode"],
                    "escalation": _escalation_note(rule)}
    result = dict(FALLBACK)
    result.update({"task": task_text, "role": FALLBACK["role"],
                   "local_tool": None,
                   "escalation": "No deterministic tool covers this; requires "
                                 "a local model or Founder-approved cloud AI."})
    return result


def _escalation_note(rule):
    if rule["mode"] == "deterministic":
        return ("Deterministic local tool first. Escalate to local model only "
                "for free-text judgment; cloud only if Founder-enabled.")
    if rule["mode"] == "judgment":
        return ("Role-skill judgment task: run through the named skill; "
                "local model or approved cloud model required for full quality.")
    return "Needs AI."


if __name__ == "__main__":
    text = " ".join(sys.argv[1:]) or "prepare the weekly pipeline report"
    print(json.dumps(classify(text), indent=2))
