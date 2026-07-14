"""AOS Department Supervisor - priority engine (PRJ-013). Stdlib only.

Deterministic scoring. Lower score = higher priority.
P1 <= 20, P2 <= 40, P3 otherwise.
"""

import datetime


def days_until(due, today):
    try:
        return (datetime.date.fromisoformat(str(due)) - today).days
    except (ValueError, TypeError):
        return 999


def score_task(task, today):
    """task: {"title", "due", "source", "kpi_slipping": bool, "goal_aligned": bool}."""
    score = 50
    d = days_until(task.get("due"), today)
    if d <= 0:
        score -= 35
    elif d == 1:
        score -= 25
    elif d <= 3:
        score -= 15
    elif d <= 7:
        score -= 5
    if task.get("kpi_slipping"):
        score -= 12
    if task.get("goal_aligned"):
        score -= 8
    if task.get("source") == "carryover":
        score -= 6
    if task.get("source") == "recurring":
        score += 5
    return max(score, 1)


def priority_label(score):
    if score <= 20:
        return "P1"
    if score <= 40:
        return "P2"
    return "P3"
