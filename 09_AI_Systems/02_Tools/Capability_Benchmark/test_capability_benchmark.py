"""Atlas Capability Benchmark v1 smoke tests (PRJ-014). Stdlib only.

Run: py test_capability_benchmark.py
"""

import unittest

from benchmark_runners import RUNNERS, run_task
from benchmark_tasks import build_tasks


class BenchmarkSmokeTests(unittest.TestCase):
    def setUp(self):
        self.tasks = build_tasks()

    def test_at_least_100_tasks(self):
        self.assertGreaterEqual(len(self.tasks), 100)

    def test_unique_task_ids(self):
        ids = [t["id"] for t in self.tasks]
        self.assertEqual(len(ids), len(set(ids)))

    def test_all_required_categories_present(self):
        cats = {t["category"] for t in self.tasks}
        for cat in ("office administration", "excel", "word", "files",
                    "email drafting", "research", "reporting", "management",
                    "hr policy", "project operations", "sales operations",
                    "knowledge retrieval", "quality control"):
            self.assertIn(cat, cats)

    def test_every_runner_exists(self):
        for t in self.tasks:
            self.assertIn(t["runner"], RUNNERS, msg=t["id"])

    def test_sample_tasks_run(self):
        # one representative executable task per category
        seen = set()
        for t in self.tasks:
            if t["category"] in seen or t["runner"].startswith("requires_ai"):
                continue
            seen.add(t["category"])
            outcome = run_task(t)
            self.assertIs(outcome, True, msg="%s (%s)" % (t["id"], t["description"]))
        self.assertEqual(len(seen), 13)

    def test_requires_ai_tasks_report_none(self):
        ai_tasks = [t for t in self.tasks if t["runner"].startswith("requires_ai")]
        self.assertTrue(ai_tasks)
        self.assertIsNone(run_task(ai_tasks[0]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
