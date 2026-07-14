"""AOS Skill Router tests (PRJ-014). Run: py test_skill_router.py"""

import unittest

from skill_router import classify


class SkillRouterTests(unittest.TestCase):
    def check(self, text, skill, mode=None):
        result = classify(text)
        self.assertEqual(result["skill"], skill, msg=result)
        if mode:
            self.assertEqual(result["mode"], mode, msg=result)
        return result

    def test_business_idea_routes_to_ceo(self):
        self.check("I have a business idea for a new service line",
                   "aos-ceo-command-center", "judgment")

    def test_architecture_routes_to_cto(self):
        self.check("Review the system design for the runtime",
                   "aos-cto-architect", "judgment")

    def test_spreadsheet_routes_to_office_operator(self):
        result = self.check("Create an xlsx tracker for July",
                            "aos-office-operator", "deterministic")
        self.assertIn("spreadsheet_tool.py", result["local_tool"])

    def test_document_routes_to_document_engineer(self):
        self.check("Prepare meeting minutes as a word document",
                   "aos-document-engineer", "deterministic")

    def test_policy_question_routes_to_policy_retriever(self):
        result = self.check("What is the annual leave policy?",
                            "aos-policy-retriever", "deterministic")
        self.assertIn("policy_retriever.py", result["local_tool"])

    def test_people_question_routes_to_people_operations(self):
        self.check("Employee onboarding checklist for new staff",
                   "aos-people-operations")

    def test_report_routes_to_reporting(self):
        result = self.check("Prepare the weekly pipeline report",
                            "aos-reporting", "deterministic")
        self.assertIn("pipeline_reporter.py", result["local_tool"])

    def test_filing_routes_to_file_librarian(self):
        self.check("Organize the legacy folder and find duplicate files",
                   "aos-file-librarian", "deterministic")

    def test_daily_plan_routes_to_task_planner(self):
        self.check("Build the daily plan and assign tasks",
                   "aos-task-planner", "deterministic")

    def test_outreach_routes_to_acquisition(self):
        self.check("Draft a cold email for this lead",
                   "aos-client-acquisition-engine", "deterministic")

    def test_quality_routes_to_qa(self):
        self.check("Please do a final check and review the output",
                   "aos-qa-auditor", "judgment")

    def test_release_routes_to_release_manager(self):
        self.check("Prepare the commit and release summary",
                   "aos-release-manager", "judgment")

    def test_unknown_falls_back_with_honest_escalation(self):
        result = classify("Write a poem about the desert")
        self.assertEqual(result["skill"], "aos-holding-company-operator")
        self.assertEqual(result["mode"], "needs_ai")
        self.assertIn("No deterministic tool", result["escalation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
