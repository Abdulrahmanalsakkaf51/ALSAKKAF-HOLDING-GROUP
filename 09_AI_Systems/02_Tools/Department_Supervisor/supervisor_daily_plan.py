"""AOS Department Supervisor - daily plan renderer (PRJ-013). Stdlib only."""


COLUMNS = ["Partner", "Task", "Priority", "Deadline", "Reason", "Approval required", "Status"]


def plan_to_rows(plan):
    rows = []
    for t in plan:
        rows.append([
            t.get("partner", ""), t.get("title", ""), t.get("priority", ""),
            str(t.get("due", "")), t.get("reason", ""), t.get("approval", "No"),
            t.get("status", "Planned"),
        ])
    return rows


def render_text(plan, department, date_iso):
    lines = ["DAILY DEPARTMENT PLAN", "Department: %s" % department,
             "Date: %s" % date_iso, ""]
    widths = [len(c) for c in COLUMNS]
    rows = plan_to_rows(plan)
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = min(max(widths[i], len(str(cell))), 44)

    def fmt(row):
        return " | ".join(str(c)[:44].ljust(widths[i]) for i, c in enumerate(row))

    lines.append(fmt(COLUMNS))
    lines.append("-+-".join("-" * w for w in widths))
    for row in rows:
        lines.append(fmt(row))
    escalated = sum(1 for t in plan if "ESCALATED" in t.get("approval", ""))
    lines.append("")
    lines.append("Tasks: %d | Escalated to human: %d" % (len(plan), escalated))
    lines.append("This plan is a proposal. The Department Lead approves, edits, or rejects it.")
    return "\n".join(lines)


def render_markdown(plan, department, date_iso):
    lines = ["# Daily Department Plan", "",
             "Department: %s" % department, "", "Date: %s" % date_iso, "",
             "| " + " | ".join(COLUMNS) + " |",
             "|" + "|".join("---" for _ in COLUMNS) + "|"]
    for row in plan_to_rows(plan):
        lines.append("| " + " | ".join(str(c).replace("|", "/") for c in row) + " |")
    lines.append("")
    lines.append("This plan is a proposal prepared by the Department Supervisor. "
                 "The Department Lead approves, edits, or rejects it.")
    return "\n".join(lines) + "\n"
