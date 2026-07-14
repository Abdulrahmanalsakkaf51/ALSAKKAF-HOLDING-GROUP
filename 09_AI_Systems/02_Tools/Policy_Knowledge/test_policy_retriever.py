"""AOS Policy and Law Knowledge System tests (PRJ-014). Stdlib only.

Run: py test_policy_retriever.py
"""

import datetime
import unittest

import people_operations_calculator as poc
from policy_freshness_checker import freshness_report
from policy_retriever import load_index, needs_legal_review, search

TODAY = datetime.date(2026, 7, 14)


class PolicyRetrieverTests(unittest.TestCase):
    def setUp(self):
        self.index = load_index()

    def test_pack_is_labeled_demo(self):
        self.assertIn("DEMO", self.index["pack_status"].upper())

    def test_every_item_has_required_metadata(self):
        required = ("id", "category", "summary", "jurisdiction", "sector",
                    "source", "official_source_url", "effective_date",
                    "last_verified", "scope", "document_version",
                    "approval_status")
        for item in self.index["items"]:
            for field in required:
                self.assertTrue(str(item.get(field, "")).strip(),
                                "%s missing %s" % (item.get("id"), field))

    def test_all_demo_categories_present(self):
        cats = {i["category"] for i in self.index["items"]}
        for cat in ("working hours", "annual leave", "sick leave",
                    "other statutory leaves", "probation",
                    "termination process", "employee records",
                    "manager escalation"):
            self.assertIn(cat, cats)

    def test_search_annual_leave(self):
        results = search(query="annual leave", index=self.index, today=TODAY)
        self.assertTrue(results)
        self.assertEqual(results[0]["item"]["id"], "PLK-UAE-002")
        self.assertEqual(results[0]["snapshot_date"], "2026-07-14")

    def test_search_by_category(self):
        results = search(category="probation", index=self.index, today=TODAY)
        self.assertEqual(len(results), 1)

    def test_termination_flags_legal_review(self):
        results = search(query="termination notice", index=self.index, today=TODAY)
        self.assertTrue(results)
        self.assertTrue(all(r["legal_review_required"] for r in results))

    def test_no_match_returns_empty_not_guess(self):
        self.assertEqual(search(query="crypto trading bonus scheme",
                                index=self.index, today=TODAY), [])

    def test_staleness_warning_after_max_age(self):
        future = TODAY + datetime.timedelta(days=400)
        results = search(query="annual leave", index=self.index, today=future)
        self.assertTrue(results[0]["stale"])

    def test_freshness_report_clean_today(self):
        report = freshness_report(self.index, today=TODAY)
        self.assertEqual(report["stale"], [])
        self.assertEqual(report["checked"], len(self.index["items"]))

    def test_legal_review_marker_detection(self):
        item = {"category": "annual leave"}
        self.assertTrue(needs_legal_review("can we dismiss him during leave", item))
        self.assertFalse(needs_legal_review("how many leave days", item))


class PeopleOpsCalculatorTests(unittest.TestCase):
    def test_annual_leave_full_year(self):
        self.assertEqual(poc.annual_leave_entitlement(14)["days"], 30)

    def test_annual_leave_nine_months(self):
        self.assertEqual(poc.annual_leave_entitlement(9)["days"], 6)

    def test_annual_leave_under_six_months(self):
        self.assertEqual(poc.annual_leave_entitlement(3)["days"], 0)

    def test_probation_end_and_cap(self):
        self.assertEqual(poc.probation_end("2026-01-15", 6),
                         datetime.date(2026, 7, 15))
        with self.assertRaises(ValueError):
            poc.probation_end("2026-01-15", 7)

    def test_sick_leave_tiers(self):
        breakdown = poc.sick_leave_breakdown(50)
        self.assertEqual(breakdown["full_pay_days"], 15)
        self.assertEqual(breakdown["half_pay_days"], 30)
        self.assertEqual(breakdown["unpaid_days"], 5)

    def test_sick_leave_beyond_cap_flags_review(self):
        breakdown = poc.sick_leave_breakdown(100)
        self.assertEqual(breakdown["beyond_entitlement_days"], 10)
        self.assertIn("LEGAL / HR REVIEW", breakdown["note"])

    def test_notice_period_check(self):
        self.assertTrue(poc.notice_period_check(30)["valid"])
        self.assertFalse(poc.notice_period_check(15)["valid"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
