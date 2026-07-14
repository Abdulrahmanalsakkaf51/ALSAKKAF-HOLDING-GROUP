"""AOS Office Toolbelt tests (PRJ-013). Standard library only.

These are the six realistic Office Partner test tasks plus unit checks.
Every test produces or manipulates REAL local files.

Run: py test_office_toolbelt.py
"""

import os
import shutil
import tempfile
import unittest
import zipfile

import data_cleaning_tool
import document_tool
import email_draft_tool
import file_organizer
import office_template_tool
import spreadsheet_tool
import tracker_tool


class OfficeToolbeltTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="aos_office_test_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    # TEST 1 — Create a formatted monthly tracker
    def test_1_create_monthly_tracker(self):
        result = tracker_tool.create_monthly_tracker(
            self.tmp, 2026, 7, owner="Office",
            entries=[{"date": "2026-07-14", "activity": "Prepare client files",
                      "category": "Filing", "status": "In Progress"}])
        self.assertTrue(os.path.isfile(result["xlsx"]))
        self.assertTrue(os.path.isfile(result["csv"]))
        # workbook is a valid zip with the required OOXML parts
        with zipfile.ZipFile(result["xlsx"]) as z:
            names = z.namelist()
        for part in ("[Content_Types].xml", "xl/workbook.xml",
                     "xl/worksheets/sheet1.xml", "xl/styles.xml"):
            self.assertIn(part, names)
        # data reads back correctly
        rows = spreadsheet_tool.read_workbook(result["xlsx"])
        self.assertEqual(rows[0][:3], ["Date", "Day", "Activity"])
        target = [r for r in rows if r and r[0] == "2026-07-14"]
        self.assertEqual(target[0][2], "Prepare client files")

    # TEST 2 — Edit an existing workbook
    def test_2_edit_existing_workbook(self):
        path = os.path.join(self.tmp, "clients.xlsx")
        spreadsheet_tool.create_workbook(path, [{
            "name": "Clients",
            "headers": ["Client", "Status", "Value"],
            "rows": [["Example LLC", "Active", 399]],
        }])
        spreadsheet_tool.append_rows(path, [["Sample Institute", "Proposal", 450],
                                            ["Demo Events Co", "New", 0]])
        rows = spreadsheet_tool.read_workbook(path)
        self.assertEqual(len(rows), 4)  # header + 3
        self.assertEqual(rows[2][0], "Sample Institute")
        self.assertEqual(rows[2][2], 450)

    # TEST 3 — Create a professional management report
    def test_3_management_report(self):
        path = os.path.join(self.tmp, "report.docx")
        office_template_tool.management_report(
            path, "Monthly Operations Report", "June 2026",
            sections=[{"heading": "Summary",
                       "text": "Operations ran normally with 118 requests handled."}],
            metrics=[["Requests handled", 118], ["Average response (days)", 1.4]])
        self.assertTrue(os.path.isfile(path))
        text = document_tool.read_text(path)
        self.assertIn("Monthly Operations Report", text)
        self.assertIn("Requests handled", text)
        self.assertIn("118", text)

    # TEST 4 — Organize a messy sample folder
    def test_4_organize_messy_folder(self):
        messy = os.path.join(self.tmp, "messy")
        os.makedirs(messy)
        samples = ["notes.txt", "budget.csv", "photo.png", "contract.docx",
                   "old contract copy.docx", "misc.xyz"]
        for name in samples:
            with open(os.path.join(messy, name), "w") as f:
                f.write("sample contract" if "copy" in name
                        else "unique content for %s" % name)
        # make a true duplicate pair
        with open(os.path.join(messy, "contract.docx"), "w") as f:
            f.write("sample contract")
        report = file_organizer.organize_folder(messy, date="2026-07-14")
        self.assertEqual(len(report["moved"]), len(samples))
        self.assertTrue(os.path.isdir(os.path.join(messy, "Documents")))
        self.assertTrue(os.path.isdir(os.path.join(messy, "Spreadsheets")))
        self.assertTrue(os.path.isdir(os.path.join(messy, "Other")))
        self.assertEqual(len(report["duplicates"]), 1)  # the two contracts
        index = file_organizer.build_index(messy)
        self.assertTrue(os.path.isfile(index))
        content = open(index, encoding="utf-8").read()
        self.assertIn("2026-07-14_Spreadsheets_budget.csv", content)

    # TEST 5 — Create meeting minutes from sample notes
    def test_5_meeting_minutes(self):
        path = os.path.join(self.tmp, "minutes.docx")
        office_template_tool.meeting_minutes(
            path, "Weekly Operations Review", "2026-07-14",
            attendees=["Abdulrahman (Founder)", "Office Team"],
            notes=["Reviewed last week's client requests",
                   "Discussed filing backlog"],
            decisions=["Adopt new naming convention for client files"],
            actions=[{"item": "Clear filing backlog", "owner": "Office", "due": "2026-07-18"}])
        text = document_tool.read_text(path)
        self.assertIn("Weekly Operations Review", text)
        self.assertIn("Clear filing backlog", text)

    # TEST 6 — Create an email draft and task list (never sent)
    def test_6_email_draft_and_tasks(self):
        draft = email_draft_tool.draft_email(
            "follow_up", "Ms. Sarah", "your workflow starter pack inquiry",
            "We prepared a short summary of the three automations we discussed.")
        self.assertIn("DRAFT", draft["status"])
        path = email_draft_tool.save_draft(draft, self.tmp)
        content = open(path, encoding="utf-8").read()
        self.assertIn("NOT SENT", content)
        items = email_draft_tool.extract_action_items(
            "Please send the proposal by Thursday. The weather is nice. "
            "We need to confirm the meeting room.")
        self.assertEqual(len(items), 2)

    # ---- supporting unit checks ----

    def test_data_cleaning(self):
        cleaned, report = data_cleaning_tool.clean_csv_text(
            "Name,Phone\n  Ali  ,  0501234 \nAli,0501234\nSara,n/a\n",
            required_columns=["Phone"])
        self.assertEqual(report["duplicates_removed"], 1)
        self.assertEqual(cleaned[0]["Name"], "Ali")
        self.assertEqual(cleaned[1]["Phone"], "")
        self.assertEqual(len(report["problems"]), 1)

    def test_tracker_summary_and_stale(self):
        import datetime
        result = tracker_tool.create_monthly_tracker(self.tmp, 2026, 7)
        counts = tracker_tool.tracker_summary(result["xlsx"])
        self.assertGreater(counts.get("Planned", 0), 15)
        stale = tracker_tool.find_stale(result["xlsx"],
                                        today=datetime.date(2026, 8, 15))
        self.assertGreater(len(stale), 0)

    def test_placeholder_replacement(self):
        path = os.path.join(self.tmp, "template.docx")
        document_tool.create_document(path, [
            {"type": "title", "text": "Letter for {{client}}"},
            {"type": "paragraph", "text": "Dear {{client}}, your total is {{total}}."}])
        document_tool.replace_placeholders(path, {"client": "Example LLC", "total": "$399"})
        text = document_tool.read_text(path)
        self.assertIn("Example LLC", text)
        self.assertNotIn("{{client}}", text)

    def test_email_tool_cannot_send(self):
        import email_draft_tool as e
        self.assertFalse(hasattr(e, "send"))
        self.assertFalse(hasattr(e, "send_email"))
        source = open(e.__file__, encoding="utf-8").read()
        self.assertNotIn("smtplib", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
