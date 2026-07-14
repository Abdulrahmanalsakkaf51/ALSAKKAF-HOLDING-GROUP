"""AOS Department Supervisor tests (PRJ-013). Standard library only.

Run: py test_department_supervisor.py
"""

import datetime
import json
import os
import unittest

import department_supervisor as ds
from priority_engine import priority_label, score_task
from task_planner import EscalationCheck, plan_tasks
from task_queue import TaskQueue

TODAY = datetime.date(2026, 7, 14)  # a Tuesday


def load_policy():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "supervisor_policy.json"), encoding="utf-8") as f:
        return json.load(f)


class SupervisorTests(unittest.TestCase):
    def setUp(self):
        self.policy = load_policy()

    def test_no_inputs_no_busywork(self):
        tasks = plan_tasks({}, self.policy, TODAY)
        self.assertEqual(tasks, [])

    def test_deadline_creates_task_with_reason(self):
        tasks = plan_tasks({"deadlines": [
            {"task": "Prepare weekly report", "type": "report",
             "due": TODAY.isoformat()}]}, self.policy, TODAY)
        self.assertEqual(len(tasks), 1)
        self.assertIn("Deadline", tasks[0]["reason"])
        self.assertIn("Reporting Partner", tasks[0]["partner"])

    def test_far_future_deadline_not_planned_today(self):
        tasks = plan_tasks({"deadlines": [
            {"task": "Annual review", "type": "report",
             "due": (TODAY + datetime.timedelta(days=60)).isoformat()}]},
            self.policy, TODAY)
        self.assertEqual(tasks, [])

    def test_recurring_daily_duty_planned(self):
        tasks = plan_tasks({"recurring_duties": [
            {"task": "Update client tracker", "type": "tracker", "when": "daily"}]},
            self.policy, TODAY)
        self.assertEqual(len(tasks), 1)

    def test_slipping_kpi_creates_corrective_task(self):
        tasks = plan_tasks({"kpis": [
            {"name": "Response time", "target": 1.5, "actual": 2.5,
             "direction": "lower_is_better", "type": "follow-up",
             "corrective_task": "Draft follow-ups for stale threads"}]},
            self.policy, TODAY)
        self.assertEqual(len(tasks), 1)
        self.assertTrue(tasks[0]["kpi_slipping"])

    def test_healthy_kpi_creates_nothing(self):
        tasks = plan_tasks({"kpis": [
            {"name": "Leads", "target": 10, "actual": 12,
             "direction": "higher_is_better",
             "corrective_task": "Verify more leads"}]}, self.policy, TODAY)
        self.assertEqual(tasks, [])

    # ---- escalation ----

    def test_external_commitment_escalates(self):
        tasks = plan_tasks({"deadlines": [
            {"task": "Accept supplier quote and book venue", "type": "external",
             "due": TODAY.isoformat()}]}, self.policy, TODAY)
        self.assertIn("ESCALATED", tasks[0]["approval"])
        self.assertEqual(tasks[0]["partner"], "Human decision required")

    def test_salary_and_termination_escalate(self):
        check = EscalationCheck(self.policy)
        self.assertEqual(check.escalation_reason("Review salary adjustment"), "salary")
        self.assertEqual(check.escalation_reason("Prepare termination letter"),
                         "termination")
        self.assertIsNone(check.escalation_reason("Update the client tracker"))

    # ---- priorities ----

    def test_due_today_is_p1(self):
        score = score_task({"due": TODAY.isoformat()}, TODAY)
        self.assertEqual(priority_label(score), "P1")

    def test_recurring_far_duty_is_lower_priority(self):
        due_today = score_task({"due": TODAY.isoformat()}, TODAY)
        recurring = score_task({"due": (TODAY + datetime.timedelta(days=10)).isoformat(),
                                "source": "recurring"}, TODAY)
        self.assertLess(due_today, recurring)

    # ---- queue / follow-ups ----

    def test_follow_up_created_for_unfinished_work(self):
        queue = TaskQueue()
        queue.add({"title": "Finish filing backlog", "status": "In Progress",
                   "created": (TODAY - datetime.timedelta(days=1)).isoformat()})
        follow_ups = queue.make_follow_ups(TODAY)
        self.assertEqual(len(follow_ups), 1)
        self.assertIn("Follow up:", follow_ups[0]["title"])
        # running again must not duplicate follow-ups
        self.assertEqual(queue.make_follow_ups(TODAY), [])

    # ---- full plan ----

    def test_daily_cap_enforced(self):
        inputs = {"recurring_duties": [
            {"task": "Duty %d" % i, "type": "tracker", "when": "daily"}
            for i in range(12)]}
        plan, deferred = ds.build_daily_plan(inputs, self.policy, TODAY)
        self.assertLessEqual(len(plan), self.policy["max_tasks_per_day"])
        self.assertEqual(len(plan) + len(deferred), 12)

    def test_demo_runs_and_escalates_supplier_task(self):
        plan = ds.demo(write_md=False)
        self.assertTrue(plan)
        escalated = [t for t in plan if "ESCALATED" in t.get("approval", "")]
        self.assertGreaterEqual(len(escalated), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
