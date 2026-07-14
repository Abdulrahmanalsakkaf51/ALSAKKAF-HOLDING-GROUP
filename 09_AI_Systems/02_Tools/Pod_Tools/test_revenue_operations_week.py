"""PRJ-016 Revenue Operations Week integrity + privacy tests. Stdlib only.

Two test families:
  * Public-scope tests — always run; enforce PODS-001: template-only trackers,
    no real prospect names anywhere in tracked files, honest public artifacts.
  * Private-data tests — run only when the private operational store exists
    on this machine; verify real counts and approval gates.

Run: py test_revenue_operations_week.py
"""

import csv
import datetime
import glob
import os
import re
import subprocess
import unittest

import daily_revenue_briefing as drb

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
PRIVATE = drb.PRIVATE_ROOT
HAVE_PRIVATE = os.path.isfile(os.path.join(PRIVATE, "01_Verified_Leads",
                                           "Lead_Tracker.csv"))

# Name fragments that must never appear in public commit scope (PODS-001).
# Kept as split fragments so this test file itself never contains a joined name.
FORBIDDEN_FRAGMENTS = [
    "fi" + "tie" + "du", "pe" + "ergr" + "owth", "inci" + "rcled" + "xb",
    "ne" + "xconsul" + "tants", "za" + "be" + "elinstitute",
    "tr" + "eo-ho" + "mes", "da" + "ch" + "a.ae", "irw" + "inand" + "dow",
    "ca" + "lib" + "erly", "lear" + "nersp" + "oint", "ab" + "hish" + "ek",
    "ka" + "dav" + "an", "theca" + "pitald" + "ubai", "pur" + "rpleor" + "ryx",
]


def p(*parts):
    return os.path.join(ROOT, *parts)


def read_csv(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def commit_scope_files():
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                         text=True)
    tracked = out.stdout.splitlines()
    out = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"],
                         cwd=ROOT, capture_output=True, text=True)
    return tracked + out.stdout.splitlines()


class PublicPrivacyTests(unittest.TestCase):
    """PODS-001 enforcement — always runs."""

    def test_no_real_prospect_names_in_commit_scope(self):
        text_ext = (".md", ".csv", ".py", ".js", ".json", ".html", ".css",
                    ".txt", ".svg", ".webmanifest", ".ps1", ".bat")
        offenders = []
        for rel in commit_scope_files():
            if not rel.lower().endswith(text_ext):
                continue
            path = os.path.join(ROOT, rel)
            if not os.path.isfile(path) or os.path.samefile(path, __file__):
                continue
            blob = open(path, encoding="utf-8", errors="ignore").read().lower()
            for frag in FORBIDDEN_FRAGMENTS:
                if frag in blob:
                    offenders.append("%s contains %r" % (rel, frag))
        self.assertEqual(offenders, [])

    def test_public_lead_tracker_is_template_only(self):
        rows = read_csv(p("01_Holding_Company", "04_Operations",
                          "03_Revenue_Operations", "Lead_Tracker.csv"))
        for row in rows:
            self.assertTrue(row["Lead ID"].startswith("EXAMPLE"),
                            msg="real lead row in public tracker: %s" % row["Lead ID"])

    def test_public_outreach_tracker_is_template_only(self):
        rows = read_csv(p("01_Holding_Company", "04_Operations",
                          "03_Revenue_Operations", "Outreach_Tracker.csv"))
        for row in rows:
            self.assertTrue(row["Outreach ID"].startswith("EXAMPLE"),
                            msg="real outreach row in public tracker")

    def test_public_summary_is_aggregate_only(self):
        text = open(p("01_Holding_Company", "04_Operations",
                      "11_Partner_Activation_Week",
                      "PRJ-016_Operations_Summary.md"), encoding="utf-8").read()
        self.assertIn("| Prospects verified into the private queue | 10 |", text)
        self.assertIn("| Messages sent | 0 |", text)
        self.assertIn("$0", text)

    def test_fictional_demo_is_labeled_fictional(self):
        text = open(p("01_Holding_Company", "04_Operations",
                      "11_Partner_Activation_Week",
                      "Outreach_Demonstration_Fictional.md"), encoding="utf-8").read()
        self.assertIn("FICTIONAL", text)
        self.assertIn("does not exist", text)
        self.assertNotIn("paypal.com", text.lower())

    def test_gitignore_has_private_protection_rules(self):
        gi = open(p(".gitignore"), encoding="utf-8").read()
        for rule in ("/Private_Operations/", "/**/Private_Operations/",
                     "/**/Real_Leads/", "/**/Real_Outreach/", "/**/Client_Data/"):
            self.assertIn(rule, gi)

    def test_private_data_standard_exists(self):
        text = open(p("01_Holding_Company", "01_Governance",
                      "Private_Operational_Data_Standard.md"), encoding="utf-8").read()
        self.assertIn("PODS-001", text)
        self.assertIn("never committed publicly", text.lower())


class PartnerStatusIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.registry = open(p("09_AI_Systems", "01_Partners",
                               "Partner_Registry.md"), encoding="utf-8").read()

    def test_active_partner_set(self):
        # Founder approved ADR-024..027 on 2026-07-15: the four pod
        # Partners joined the original three Active Partners.
        rows = re.findall(r"^\| (PARTNER-\d+) \|.*?\| (\w[\w –-]*?) \| CEO \|",
                          self.registry, re.M)
        active = {pid for pid, status in rows if status.strip() == "Active"}
        self.assertEqual(active, {"PARTNER-001", "PARTNER-002", "PARTNER-016",
                                  "PARTNER-004", "PARTNER-007", "PARTNER-012",
                                  "PARTNER-019"})

    def test_pod_partners_active_with_adr(self):
        for pid, adr in (("PARTNER-004", "ADR-024"), ("PARTNER-019", "ADR-025"),
                         ("PARTNER-012", "ADR-026"), ("PARTNER-007", "ADR-027")):
            row = re.search(r"^\| %s \|.*$" % pid, self.registry, re.M).group(0)
            self.assertRegex(row, r"\| Active \|", msg=pid)
            self.assertIn(adr, row, msg=pid)

    def test_supervisor_not_active(self):
        # PARTNER-020 (Department Supervisor) has no activation ADR.
        row = re.search(r"^\| PARTNER-020 \|.*$", self.registry, re.M).group(0)
        self.assertNotRegex(row, r"\| Active \|")


class GovernanceGateTests(unittest.TestCase):
    def test_guardian_review_exists_and_does_not_activate(self):
        gar = open(p("09_AI_Systems", "01_Partners", "09_Partner_Factory",
                     "05_Guardian_Reviews", "GAR-001_Pod_Activation_Risk_Review.md"),
                   encoding="utf-8").read()
        self.assertEqual(gar.count("READY FOR FOUNDER ACTIVATION"), 4)
        self.assertIn("Guardian does not activate", gar)

    def test_activation_adrs_approved_with_conditions(self):
        for adr in ("ADR-024_Activate_Research_Partner.md",
                    "ADR-025_Activate_Client_Acquisition_Partner.md",
                    "ADR-026_Activate_Reporting_Partner.md",
                    "ADR-027_Activate_Office_Operations_Partner.md"):
            text = open(p("01_Holding_Company", "01_Governance", "ADR", adr),
                        encoding="utf-8").read()
            self.assertIn("| Status | Approved |", text, msg=adr)
            self.assertIn("| Founder decision | APPROVED |", text, msg=adr)
            self.assertIn("Level 3 — Bounded Internal Operation", text, msg=adr)
            self.assertIn("may not independently activate", text, msg=adr)
            self.assertIn("No credential access", text, msg=adr)


class NoAutomaticSendingTests(unittest.TestCase):
    def test_no_smtplib_in_operational_modules(self):
        for folder in ("Pod_Tools", "Office_Toolbelt", "Department_Supervisor"):
            for path in glob.glob(p("09_AI_Systems", "02_Tools", folder, "*.py")):
                if os.path.basename(path).startswith("test_"):
                    continue
                self.assertNotIn("smtplib",
                                 open(path, encoding="utf-8").read(), msg=path)


class PublicSiteIntegrityTests(unittest.TestCase):
    def test_paypal_links_unchanged(self):
        html = open(p("docs", "index.html"), encoding="utf-8").read()
        links = sorted(set(re.findall(
            r"https://www\.paypal\.com/ncp/payment/[A-Z0-9]+", html)))
        self.assertEqual(links, [
            "https://www.paypal.com/ncp/payment/2AN8FH99X682C",
            "https://www.paypal.com/ncp/payment/2WXPECSR3UH68"])

    def test_professional_emails_preserved(self):
        html = open(p("docs", "index.html"), encoding="utf-8").read()
        for email in ("abdulrahman@alsakkafsystems.com", "hello@alsakkafsystems.com",
                      "sales@alsakkafsystems.com", "services@alsakkafsystems.com"):
            self.assertIn(email, html)

    def test_450_wording_patched(self):
        html = open(p("docs", "index.html"), encoding="utf-8").read()
        self.assertNotIn("three working AI assistants", html)
        self.assertIn("three configured AI Partner roles", html)

    def test_playground_badges_honest(self):
        js = open(p("docs", "partner-playground.js"), encoding="utf-8").read()
        self.assertEqual(len(re.findall(r'label: "active"', js)), 3)
        self.assertIn('designed: "Designed Partner"', js)


@unittest.skipUnless(HAVE_PRIVATE, "private operational store not on this machine")
class PrivateDataTests(unittest.TestCase):
    """Run only where the private store exists (Founder's machine)."""

    def test_private_store_holds_ten_real_leads(self):
        rows = read_csv(os.path.join(PRIVATE, "01_Verified_Leads",
                                     "Lead_Tracker.csv"))
        real = [r for r in rows if not r["Lead ID"].startswith("EXAMPLE")]
        self.assertEqual(len(real), 10)
        for lead in real:
            self.assertIn("verified 2026-07-14", lead["Problem Observed"],
                          msg=lead["Lead ID"])

    def test_private_outreach_all_unsent_and_unapproved(self):
        rows = read_csv(os.path.join(PRIVATE, "04_Outreach_Tracker",
                                     "Outreach_Tracker.csv"))
        real = [r for r in rows if not r["Outreach ID"].startswith("EXAMPLE")]
        self.assertEqual(len(real), 5)
        for r in real:
            self.assertEqual(r["Date Sent"], "")
            self.assertNotEqual(r["CEO Approved"].lower(), "yes")

    def test_private_drafts_have_no_payment_link(self):
        batch = open(os.path.join(PRIVATE, "03_Outreach_Drafts",
                                  "Outreach_Batch_1.md"), encoding="utf-8").read()
        self.assertNotIn("paypal.com", batch.lower())
        self.assertGreaterEqual(batch.count("NOT SENT"), 5)

    def test_briefing_reads_private_data_accurately(self):
        b = drb.compute_briefing(today=datetime.date(2026, 7, 14))
        self.assertEqual(b["prospects_accepted"], 10)
        self.assertEqual(b["prospects_rejected"], 8)
        self.assertEqual(b["prospects_researched"], 18)
        self.assertEqual(b["drafts_ready"], 5)
        for key in ("messages_sent", "replies", "positive_replies",
                    "discovery_calls", "proposals", "paid_clients"):
            self.assertEqual(b[key], 0, msg=key)
        self.assertEqual(b["revenue_usd"], 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
