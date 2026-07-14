"""AOS Department Supervisor - task planner (PRJ-013). Stdlib only.

Builds candidate tasks from real department inputs only:
  deadlines, recurring duties due today, slipping KPIs, open requests,
  and stale backlog items. Every task carries a reason.
It never invents busywork: no input signal, no task.
"""

import datetime

from priority_engine import days_until


class EscalationCheck:
    def __init__(self, policy):
        self.triggers = policy.get("escalation_triggers", {})
        self.scope = [s.lower() for s in policy.get("approved_scope", [])]

    def escalation_reason(self, text):
        low = (text or "").lower()
        for category, markers in self.triggers.items():
            for marker in markers:
                if marker in low:
                    return category
        return None

    def in_scope(self, task_type):
        return any(task_type.lower() in s or s in task_type.lower()
                   for s in self.scope) or task_type in ("follow-up",)


def route_partner(policy, task_type):
    routing = policy.get("task_type_routing", {})
    roster = policy.get("partner_roster", {})
    key = routing.get(task_type, "office")
    return roster.get(key, key)


def plan_tasks(inputs, policy, today=None):
    """inputs: dict with deadlines, recurring_duties, kpis, open_requests, backlog.
    Returns candidate task dicts (unprioritized)."""
    today = today or datetime.date.today()
    check = EscalationCheck(policy)
    tasks = []

    def add(title, task_type, due, reason, source, kpi_slipping=False,
            goal_aligned=False):
        esc = check.escalation_reason(title)
        approval = "No"
        status = "Planned"
        if esc:
            approval = "ESCALATED to human (%s)" % esc
            status = "Awaiting approval"
        elif not check.in_scope(task_type):
            approval = "ESCALATED to human (outside approved scope)"
            status = "Awaiting approval"
        tasks.append({
            "title": title, "type": task_type,
            "partner": "Human decision required" if esc else route_partner(policy, task_type),
            "due": due, "reason": reason, "source": source,
            "kpi_slipping": kpi_slipping, "goal_aligned": goal_aligned,
            "approval": approval, "status": status,
        })

    goals_text = " ".join(g.lower() for g in inputs.get("goals", []))

    for item in inputs.get("deadlines", []):
        if days_until(item.get("due"), today) <= 7:
            add(item["task"], item.get("type", "document"), item.get("due"),
                "Deadline: due %s" % item.get("due"), "deadline",
                goal_aligned=any(w in goals_text for w in item["task"].lower().split()[:3]))

    weekday = today.strftime("%A").lower()
    for duty in inputs.get("recurring_duties", []):
        when = duty.get("when", "daily").lower()
        if when == "daily" or when == weekday:
            add(duty["task"], duty.get("type", "tracker"), today.isoformat(),
                "Recurring duty (%s)" % when, "recurring")

    for kpi in inputs.get("kpis", []):
        target, actual = kpi.get("target"), kpi.get("actual")
        direction = kpi.get("direction", "higher_is_better")
        slipping = (actual < target) if direction == "higher_is_better" else (actual > target)
        if slipping and kpi.get("corrective_task"):
            add(kpi["corrective_task"], kpi.get("type", "report"), today.isoformat(),
                "KPI slipping: %s at %s vs target %s" % (kpi["name"], actual, target),
                "kpi", kpi_slipping=True)

    for req in inputs.get("open_requests", []):
        add(req["task"], req.get("type", "document"), req.get("due", today.isoformat()),
            "Open request from %s" % req.get("from", "department"), "request")

    for item in inputs.get("backlog", []):
        age = days_until(item.get("added"), today)
        if age <= -5:  # added 5+ days ago
            add(item["task"], item.get("type", "filing"), today.isoformat(),
                "Backlog item aging (added %s)" % item.get("added"), "backlog")

    return tasks
