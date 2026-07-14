"""AOS Department Supervisor - task queue (PRJ-013). Stdlib only.

Holds the department's task state and creates follow-up tasks for
unfinished work instead of silently dropping it.
"""

import datetime
import json
import os

OPEN_STATUSES = ("Planned", "In Progress", "Awaiting approval")


class TaskQueue:
    def __init__(self, path=None):
        self.path = path
        self.tasks = []
        if path and os.path.isfile(path):
            with open(path, encoding="utf-8") as f:
                self.tasks = json.load(f)

    def add(self, task):
        task.setdefault("status", "Planned")
        task.setdefault("created",
                        datetime.date.today().isoformat())
        self.tasks.append(task)
        return task

    def open_tasks(self):
        return [t for t in self.tasks if t.get("status") in OPEN_STATUSES]

    def mark(self, title, status):
        for t in self.tasks:
            if t.get("title") == title:
                t["status"] = status
                return t
        return None

    def unfinished_from(self, date_iso):
        """Open tasks created on/before a given date — candidates for follow-up."""
        return [t for t in self.open_tasks()
                if t.get("created", "9999") <= date_iso]

    def make_follow_ups(self, today):
        """Create follow-up tasks for yesterday-or-older unfinished work.
        Marks the stale original as 'Rolled over' so follow-ups never duplicate."""
        cutoff = (today - datetime.timedelta(days=1)).isoformat()
        follow_ups = []
        for stale in self.unfinished_from(cutoff):
            if stale.get("source") == "carryover":
                continue  # don't chain follow-ups of follow-ups
            stale["status"] = "Rolled over"
            follow_ups.append(self.add({
                "title": "Follow up: %s" % stale["title"],
                "partner": stale.get("partner", "office"),
                "due": today.isoformat(),
                "reason": "Carried over — unfinished on %s" % stale.get("created"),
                "source": "carryover",
            }))
        return follow_ups

    def save(self):
        if self.path:
            os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.tasks, f, indent=2, ensure_ascii=False)
