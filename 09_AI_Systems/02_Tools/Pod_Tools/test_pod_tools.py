"""AOS Pod Tools tests (PRJ-014 pod). Standard library only.

Run: py test_pod_tools.py
"""

import datetime
import os
import shutil
import tempfile
import unittest

import outreach_composer
import pipeline_reporter
import research_verifier

GOOD_LEAD = {
    "Lead ID": "L-001", "Date Found": "2026-07-01",
    "Company Name": "Horizon Trading LLC", "Industry": "Trading",
    "Country": "UAE", "City": "Dubai", "Website": "https://horizon-trading.example",
    "Email": "info@horizon-trading.example", "Decision Maker": "Sarah M.",
    "Problem Observed": "Leads tracked in a notebook, follow-ups missed weekly",
    "Offer Match": "AI Workflow Starter Pack", "Status": "New",
}


class ResearchVerifierTests(unittest.TestCase):
    def test_complete_lead_high_confidence(self):
        report = research_verifier.verify_lead(GOOD_LEAD)
        self.assertEqual(report["confidence"], "High")
        self.assertTrue(report["official_website"])

    def test_social_only_source_medium(self):
        lead = dict(GOOD_LEAD, Website="https://linkedin.com/company/horizon")
        self.assertEqual(research_verifier.verify_lead(lead)["confidence"], "Medium")

    def test_missing_fields_low(self):
        lead = dict(GOOD_LEAD)
        lead["Decision Maker"] = ""
        lead["Problem Observed"] = ""
        report = research_verifier.verify_lead(lead)
        self.assertEqual(report["confidence"], "Low")
        self.assertIn("Decision Maker", report["missing_fields"])

    def test_placeholder_detected(self):
        lead = dict(GOOD_LEAD, **{"Company Name": "[Example Only - Not Real]"})
        report = research_verifier.verify_lead(lead)
        self.assertEqual(report["confidence"], "Low")

    def test_duplicate_detection(self):
        dup = dict(GOOD_LEAD, **{"Lead ID": "L-002"})
        groups = research_verifier.find_duplicate_leads([GOOD_LEAD, dup])
        self.assertTrue(groups)


class OutreachComposerTests(unittest.TestCase):
    def test_compose_uses_approved_offer_and_never_sends(self):
        drafts = outreach_composer.compose_outreach(GOOD_LEAD, "High")
        self.assertEqual(drafts["first_touch"]["offer"], "AI Workflow Starter Pack")
        self.assertIn("$399 USD", drafts["first_touch"]["body"])
        self.assertIn("NOT SENT", drafts["first_touch"]["status"])
        self.assertIn("NOT SENT", drafts["follow_up"]["status"])

    def test_agent_pain_routes_to_agent_pack(self):
        lead = dict(GOOD_LEAD, **{
            "Offer Match": "",
            "Problem Observed": "Wants an ai assistant to delegate research and automation"})
        self.assertEqual(outreach_composer.choose_offer(lead), "AI Agent Starter Pack")

    def test_low_confidence_lead_refused(self):
        with self.assertRaises(outreach_composer.LeadNotReady):
            outreach_composer.compose_outreach(GOOD_LEAD, "Low")

    def test_no_sending_capability_in_module(self):
        source = open(outreach_composer.__file__, encoding="utf-8").read()
        self.assertNotIn("smtplib", source)
        self.assertNotIn("urllib", source)


class PipelineReporterTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="aos_pod_test_")
        self.paths = {k: os.path.join(self.tmp, k + ".csv")
                      for k in ("leads", "outreach", "pipeline")}
        with open(self.paths["leads"], "w", encoding="utf-8") as f:
            f.write("Lead ID,Date Found,Company Name,Status,Notes\n"
                    "EXAMPLE-001,2026-07-13,[Example Only - Not Real],New,Template row only\n"
                    "L-001,2026-07-01,Horizon Trading LLC,New,\n"
                    "L-002,2026-07-13,Falcon Institute,Contacted,\n")
        with open(self.paths["outreach"], "w", encoding="utf-8") as f:
            f.write("Outreach ID,Lead ID,Date Drafted,Date Sent,Reply Status\n"
                    "O-001,L-002,2026-07-13,2026-07-13,Replied - Interested\n")
        with open(self.paths["pipeline"], "w", encoding="utf-8") as f:
            f.write("Client ID,Lead ID,Company Name,Payment Status\n")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_metrics_exclude_placeholders_and_count_real_rows(self):
        metrics = pipeline_reporter.compute_metrics(
            self.paths, today=datetime.date(2026, 7, 14))
        self.assertEqual(metrics["leads_total"], 2)
        self.assertEqual(metrics["placeholder_rows_excluded"], 1)
        self.assertEqual(metrics["outreach_sent"], 1)
        self.assertEqual(metrics["replies"], 1)

    def test_stale_lead_detection(self):
        metrics = pipeline_reporter.compute_metrics(
            self.paths, today=datetime.date(2026, 7, 14))
        self.assertEqual(metrics["stale_leads"], ["L-001"])

    def test_reports_written(self):
        out = pipeline_reporter.write_reports(
            os.path.join(self.tmp, "reports"), self.paths,
            today=datetime.date(2026, 7, 14))
        self.assertTrue(os.path.isfile(out["pipeline_report"]))
        briefing = open(out["founder_briefing"], encoding="utf-8").read()
        self.assertIn("Founder Briefing", briefing)
        self.assertIn("stale", briefing.lower())

    def test_real_company_trackers_readable(self):
        repo_root = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
        paths = {k: os.path.join(repo_root, v)
                 for k, v in pipeline_reporter.DEFAULT_PATHS.items()}
        if not all(os.path.isfile(p) for p in paths.values()):
            self.skipTest("company trackers not present")
        metrics = pipeline_reporter.compute_metrics(paths)
        self.assertGreaterEqual(metrics["placeholder_rows_excluded"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
