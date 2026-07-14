"""AOS Department Supervisor v1 (PRJ-013). Standard library only.

An intelligent department supervisor prototype. It reads department inputs
(goals, responsibilities, recurring duties, deadlines, backlog, KPIs, open
requests) and PROPOSES a bounded daily task plan with Partner assignments.

AUTONOMY RULE (supervisor_policy.json):
  It may create/assign tasks only inside approved scope, within policy,
  within permissions, within budget, reversible, and not legally sensitive.
  Everything else is escalated to a human. It never invents busywork.

Usage:
  py department_supervisor.py demo          Run DEMO MODE with sample data
  py department_supervisor.py demo --md     Also write the plan as Markdown
"""

import datetime
import json
import os
import sys

from priority_engine import priority_label, score_task
from supervisor_daily_plan import render_markdown, render_text
from task_planner import plan_tasks
from task_queue import TaskQueue

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POLICY_PATH = os.path.join(BASE_DIR, "supervisor_policy.json")
STATE_DIR = os.path.join(BASE_DIR, "Supervisor_State")

DEMO_INPUTS = {
    "department": "Operations (demo scope)",
    "goals": [
        "Grow the qualified lead pipeline",
        "Keep client response time under 1.5 days",
    ],
    "deadlines": [
        {"task": "Prepare weekly KPI report", "type": "report", "due": None},
        {"task": "Prepare meeting pack for Thursday review", "type": "meeting", "due": None},
        {"task": "Accept supplier quote and book venue", "type": "external", "due": None},
    ],
    "recurring_duties": [
        {"task": "Update client tracker with new records", "type": "tracker", "when": "daily"},
        {"task": "File yesterday's incoming documents", "type": "filing", "when": "daily"},
    ],
    "kpis": [
        {"name": "Response time (days)", "target": 1.5, "actual": 2.1,
         "direction": "lower_is_better", "type": "follow-up",
         "corrective_task": "Draft follow-ups for 3 stale client threads"},
        {"name": "Verified leads per week", "target": 10, "actual": 11,
         "direction": "higher_is_better", "type": "verify",
         "corrective_task": "Verify additional leads"},
    ],
    "open_requests": [
        {"task": "Prepare client file for new engagement", "type": "document",
         "from": "Founder"},
    ],
    "backlog": [
        {"task": "Organize legacy project folder", "type": "filing", "added": None},
    ],
}


def load_policy():
    with open(POLICY_PATH, encoding="utf-8") as f:
        return json.load(f)


def build_daily_plan(inputs, policy, today=None, queue=None):
    """Plan, prioritize, cap, and add follow-ups for unfinished work."""
    today = today or datetime.date.today()
    tasks = plan_tasks(inputs, policy, today)

    if queue is not None:
        follow_ups = queue.make_follow_ups(today)
        for f in follow_ups:
            f.setdefault("type", "follow-up")
            f.setdefault("approval", "No")
            tasks.append(f)

    for t in tasks:
        t["score"] = score_task(t, today)
        t["priority"] = priority_label(t["score"])
    tasks.sort(key=lambda t: (t["score"], t["title"]))

    cap = int(policy.get("max_tasks_per_day", 8))
    plan, deferred = tasks[:cap], tasks[cap:]
    for t in deferred:
        t["status"] = "Deferred (daily cap)"

    if queue is not None:
        for t in plan:
            if t.get("source") != "carryover":
                queue.add(dict(t))
    return plan, deferred


def demo(write_md=False):
    today = datetime.date.today()
    inputs = json.loads(json.dumps(DEMO_INPUTS))
    # give the demo dates relative to today so it always behaves the same
    inputs["deadlines"][0]["due"] = (today + datetime.timedelta(days=2)).isoformat()
    inputs["deadlines"][1]["due"] = (today + datetime.timedelta(days=3)).isoformat()
    inputs["deadlines"][2]["due"] = today.isoformat()
    inputs["backlog"][0]["added"] = (today - datetime.timedelta(days=6)).isoformat()

    policy = load_policy()
    queue = TaskQueue()  # in-memory for the demo
    # seed one unfinished task from "yesterday" to show follow-up creation
    queue.add({"title": "Finish filing backlog (12 documents)", "partner":
               policy["partner_roster"]["office"], "type": "filing",
               "created": (today - datetime.timedelta(days=1)).isoformat(),
               "status": "In Progress", "source": "recurring"})

    plan, deferred = build_daily_plan(inputs, policy, today, queue)
    print("DEMO MODE — sample data, deterministic, no AI, no network\n")
    print(render_text(plan, inputs["department"], today.isoformat()))
    if deferred:
        print("\nDeferred beyond daily cap (%d): %s"
              % (len(deferred), "; ".join(t["title"] for t in deferred)))
    if write_md:
        os.makedirs(STATE_DIR, exist_ok=True)
        out = os.path.join(STATE_DIR, "daily_plan_%s.md" % today.isoformat())
        with open(out, "w", encoding="utf-8") as f:
            f.write(render_markdown(plan, inputs["department"], today.isoformat()))
        print("\nMarkdown plan written: %s" % out)
    return plan


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo(write_md="--md" in sys.argv)
    else:
        print(__doc__)
