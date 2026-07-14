"""Atlas Capability Benchmark v1 - deterministic runners (PRJ-014). Stdlib only.

Each runner executes one benchmark task with the real local tools and returns
True (acceptance criteria met) or False. Runners named requires_ai* return
None — honestly not completable by deterministic local tools.
"""

import datetime
import os
import shutil
import sys
import tempfile
import zipfile

BASE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.abspath(os.path.join(BASE, ".."))
for sub in ("Office_Toolbelt", "Pod_Tools", "Policy_Knowledge", "Skill_Router",
            "Department_Supervisor"):
    sys.path.insert(0, os.path.join(TOOLS, sub))

import data_cleaning_tool                    # noqa: E402
import department_supervisor as ds           # noqa: E402
import document_tool                         # noqa: E402
import email_draft_tool                      # noqa: E402
import file_organizer                        # noqa: E402
import office_template_tool                  # noqa: E402
import outreach_composer                     # noqa: E402
import people_operations_calculator as poc   # noqa: E402
import pipeline_reporter                     # noqa: E402
import research_verifier                     # noqa: E402
import spreadsheet_tool                      # noqa: E402
import tracker_tool                          # noqa: E402
from policy_freshness_checker import freshness_report  # noqa: E402
from policy_retriever import load_index, search        # noqa: E402
from priority_engine import priority_label, score_task  # noqa: E402
from skill_router import classify as router_classify    # noqa: E402
from task_planner import plan_tasks                      # noqa: E402
from task_queue import TaskQueue                         # noqa: E402
from tool_registry_shim import classify_request, make_checklist, csv_stats, summarize  # noqa: E402

TODAY = datetime.date(2026, 7, 14)

LEAD_VARIANTS = {
    "good": {"Lead ID": "L-1", "Company Name": "Horizon Trading LLC",
             "Industry": "Trading", "Country": "UAE",
             "Website": "https://horizon-trading.example",
             "Email": "info@horizon.example", "Decision Maker": "Sarah M.",
             "Problem Observed": "Leads tracked in a notebook",
             "Offer Match": "AI Workflow Starter Pack"},
}
LEAD_VARIANTS["social"] = dict(LEAD_VARIANTS["good"],
                               Website="https://linkedin.com/company/x")
LEAD_VARIANTS["incomplete"] = dict(LEAD_VARIANTS["good"],
                                   **{"Decision Maker": "", "Industry": ""})
LEAD_VARIANTS["placeholder"] = dict(LEAD_VARIANTS["good"],
                                    **{"Company Name": "[Example Only - Not Real]"})


class _Workspace:
    def __enter__(self):
        self.dir = tempfile.mkdtemp(prefix="acb_")
        return self.dir

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)


def _fixture_workbook(tmp):
    path = os.path.join(tmp, "wb.xlsx")
    spreadsheet_tool.create_workbook(path, [{
        "name": "Data", "headers": ["Client", "Status", "Value"],
        "rows": [["A", "New", 1], ["B", "Won", 2], ["C", "New", 3]]}])
    return path


def _fixture_pipeline(tmp):
    paths = {k: os.path.join(tmp, k + ".csv")
             for k in ("leads", "outreach", "pipeline")}
    with open(paths["leads"], "w", encoding="utf-8") as f:
        f.write("Lead ID,Date Found,Company Name,Status,Notes\n"
                "EXAMPLE-001,2026-07-13,[Example Only - Not Real],New,Template row only\n"
                "L-001,2026-07-01,Horizon LLC,New,\nL-002,2026-07-13,Falcon,Contacted,\n")
    with open(paths["outreach"], "w", encoding="utf-8") as f:
        f.write("Outreach ID,Lead ID,Date Sent,Reply Status\nO-1,L-002,2026-07-13,Replied\n")
    with open(paths["pipeline"], "w", encoding="utf-8") as f:
        f.write("Client ID,Lead ID,Payment Status\n")
    return paths


# ---------------------------------------------------------------------------

def run_task(task):
    """Dispatch one task. Returns True/False, or None when AI is required."""
    runner = RUNNERS.get(task["runner"])
    if runner is None:
        raise KeyError("No runner named %r" % task["runner"])
    return runner(task.get("params", {}), task.get("expected") or {})


def _classify(p, e):
    return classify_request(p)["type"] == e["type"]


def _checklist(p, e):
    return e["contains"] in make_checklist(p)["markdown"]


def _xlsx_tracker(p, e):
    with _Workspace() as tmp:
        result = tracker_tool.create_monthly_tracker(tmp, p["year"], p["month"])
        rows = spreadsheet_tool.read_workbook(result["xlsx"])
        return rows[0][0] == "Date" and result["rows"] > 15


def _xlsx_create(p, e):
    with _Workspace() as tmp:
        path = os.path.join(tmp, "wb.xlsx")
        spreadsheet_tool.create_workbook(path, [{
            "name": "Data", "headers": p["headers"], "rows": p["rows"]}])
        rows = spreadsheet_tool.read_workbook(path)
        return len(rows) == len(p["rows"]) + 1


def _xlsx_edit(p, e):
    with _Workspace() as tmp:
        path = _fixture_workbook(tmp)
        spreadsheet_tool.append_rows(path, p["new_rows"])
        rows = spreadsheet_tool.read_workbook(path)
        return len(rows) == 4 + len(p["new_rows"])  # header + 3 fixture + new


def _xlsx_read(p, e):
    with _Workspace() as tmp:
        rows = spreadsheet_tool.read_workbook(_fixture_workbook(tmp))
        return len(rows) - 1 == e.get("expected_rows", p.get("expected_rows", 3))


def _tracker_summary(p, e):
    with _Workspace() as tmp:
        result = tracker_tool.create_monthly_tracker(tmp, 2026, 7)
        counts = tracker_tool.tracker_summary(result["xlsx"])
        return counts.get("Planned", 0) > 15


def _tracker_stale(p, e):
    with _Workspace() as tmp:
        result = tracker_tool.create_monthly_tracker(tmp, 2026, 7)
        stale = tracker_tool.find_stale(result["xlsx"],
                                        today=datetime.date(2026, 8, 20))
        return len(stale) > 0


def _docx_report(p, e):
    with _Workspace() as tmp:
        path = os.path.join(tmp, "r.docx")
        office_template_tool.management_report(
            path, p.get("title", "Report"), "July 2026",
            sections=[{"heading": "Summary", "text": "All normal."}],
            metrics=[["Requests", 10]])
        text = document_tool.read_text(path)
        return p.get("title", "Report") in text and "Requests" in text


def _docx_minutes(p, e):
    with _Workspace() as tmp:
        path = os.path.join(tmp, "m.docx")
        office_template_tool.meeting_minutes(
            path, "Ops Review", "2026-07-14", ["Founder"], ["Note"],
            ["Decision"], [{"item": "Do it", "owner": "Office", "due": "Fri"}])
        return "Do it" in document_tool.read_text(path)


def _docx_letter(p, e):
    with _Workspace() as tmp:
        path = os.path.join(tmp, "l.docx")
        office_template_tool.business_letter(
            path, "Mr. Hassan", "Example LLC", p.get("subject", "Subject"),
            ["Thank you for your time."])
        return p.get("subject", "Subject") in document_tool.read_text(path)


def _docx_placeholders(p, e):
    with _Workspace() as tmp:
        path = os.path.join(tmp, "t.docx")
        document_tool.create_document(path, [
            {"type": "paragraph", "text": "Dear {{client}}, total {{total}}."}])
        document_tool.replace_placeholders(path, p["mapping"])
        text = document_tool.read_text(path)
        return "{{" not in text and p["mapping"]["client"] in text


def _docx_read(p, e):
    with _Workspace() as tmp:
        path = os.path.join(tmp, "d.docx")
        document_tool.create_document(path, [{"type": "title", "text": "Hello"}])
        return "Hello" in document_tool.read_text(path)


def _file_organize(p, e):
    with _Workspace() as tmp:
        for name in ("a.txt", "b.csv", "c.png"):
            open(os.path.join(tmp, name), "w").write("x " + name)
        report = file_organizer.organize_folder(tmp, date="2026-07-14")
        return (len(report["moved"]) == 3
                and os.path.isdir(os.path.join(tmp, "Documents")))


def _file_convention(p, e):
    name = file_organizer.convention_name(p["name"], p["category"],
                                          date="2026-07-14")
    return name.startswith(e["starts"])


def _file_duplicates(p, e):
    with _Workspace() as tmp:
        open(os.path.join(tmp, "x1.txt"), "w").write("same")
        open(os.path.join(tmp, "x2.txt"), "w").write("same")
        open(os.path.join(tmp, "y.txt"), "w").write("different")
        return len(file_organizer.find_duplicates(tmp)) == 1


def _file_index(p, e):
    with _Workspace() as tmp:
        open(os.path.join(tmp, "doc.txt"), "w").write("hello")
        index = file_organizer.build_index(tmp)
        return "doc.txt" in open(index, encoding="utf-8").read()


def _file_categorize(p, e):
    return file_organizer.categorize(p["name"]) == e["category"]


def _email_draft(p, e):
    draft = email_draft_tool.draft_email(p["kind"], "Ms. Sarah", "the project",
                                         "Details attached.")
    return e.get("contains", "DRAFT") in draft["status"]


def _action_items(p, e):
    items = email_draft_tool.extract_action_items(p["text"])
    return len(items) >= p["min_items"]


def _email_save(p, e):
    with _Workspace() as tmp:
        draft = email_draft_tool.draft_email("reply", "Ms. Sarah", "topic", "Body.")
        path = email_draft_tool.save_draft(draft, tmp)
        return "NOT SENT" in open(path, encoding="utf-8").read()


def _verify_lead(p, e):
    report = research_verifier.verify_lead(LEAD_VARIANTS[p["variant"]])
    return report["confidence"] == e["confidence"]


def _lead_duplicates(p, e):
    lead = LEAD_VARIANTS["good"]
    dup = dict(lead, **{"Lead ID": "L-2"})
    return bool(research_verifier.find_duplicate_leads([lead, dup]))


def _verify_tracker(p, e):
    with _Workspace() as tmp:
        path = os.path.join(tmp, "leads.csv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("Lead ID,Company Name,Industry,Country,Website,Email,"
                    "Decision Maker,Problem Observed,Offer Match\n"
                    "L-1,Horizon LLC,Trading,UAE,https://horizon.example,"
                    "i@h.example,Sarah,Manual tracking,AI Workflow Starter Pack\n")
        result = research_verifier.verify_tracker(path)
        return result["summary"]["total"] == 1


def _pipeline_metrics(p, e):
    with _Workspace() as tmp:
        metrics = pipeline_reporter.compute_metrics(_fixture_pipeline(tmp), TODAY)
        return metrics["leads_total"] == e["leads_total"]


def _pipeline_stale(p, e):
    with _Workspace() as tmp:
        metrics = pipeline_reporter.compute_metrics(_fixture_pipeline(tmp), TODAY)
        return metrics["stale_leads"] == e["stale"]


def _pipeline_report(p, e):
    with _Workspace() as tmp:
        out = pipeline_reporter.write_reports(os.path.join(tmp, "r"),
                                              _fixture_pipeline(tmp), TODAY)
        return os.path.isfile(out["pipeline_report"])


def _founder_briefing(p, e):
    with _Workspace() as tmp:
        out = pipeline_reporter.write_reports(os.path.join(tmp, "r"),
                                              _fixture_pipeline(tmp), TODAY)
        return "Founder Briefing" in open(out["founder_briefing"],
                                          encoding="utf-8").read()


def _csv_stats(p, e):
    out = csv_stats(p)
    return out["counts"].get("New", 0) == e["count_new"]


def _summarize(p, e):
    text = ("The pipeline grew this week. Two leads replied.\n\n"
            "The office cleared its backlog. Filing is current.\n\n"
            "One payment is pending confirmation. Follow-up is scheduled.")
    out = summarize({"text": text, "max_items": p["max_items"]})
    return len(out["summary"]) == p["max_items"]


def _supervisor_inputs():
    return {"deadlines": [
        {"task": "Prepare weekly report", "type": "report",
         "due": TODAY.isoformat()},
        {"task": "Accept supplier quote and book venue", "type": "external",
         "due": TODAY.isoformat()}],
        "recurring_duties": [{"task": "Update tracker", "type": "tracker",
                              "when": "daily"}]}


def _supervisor_plan(p, e):
    plan, _ = ds.build_daily_plan(_supervisor_inputs(), ds.load_policy(), TODAY)
    return 0 < len(plan) <= e["max_tasks"]


def _supervisor_escalation(p, e):
    plan, _ = ds.build_daily_plan(_supervisor_inputs(), ds.load_policy(), TODAY)
    escalated = [t for t in plan if "ESCALATED" in t.get("approval", "")]
    return len(escalated) >= e["escalated_min"]


def _supervisor_followup(p, e):
    queue = TaskQueue()
    queue.add({"title": "Old task", "status": "In Progress",
               "created": (TODAY - datetime.timedelta(days=2)).isoformat()})
    return len(queue.make_follow_ups(TODAY)) == 1


def _priority_check(p, e):
    return priority_label(score_task({"due": TODAY.isoformat()}, TODAY)) == e["label"]


def _supervisor_empty(p, e):
    return len(plan_tasks({}, ds.load_policy(), TODAY)) == e["tasks"]


def _router_route(p, e):
    return router_classify(p["text"])["skill"] == e["skill"]


def _policy_lookup(p, e):
    results = search(query=p["query"], today=TODAY)
    return bool(results) and results[0]["item"]["id"] == e["item_id"]


def _policy_category(p, e):
    results = search(category=p["category"], today=TODAY)
    return bool(results) and results[0]["item"]["id"] == e["item_id"]


def _policy_legal_flag(p, e):
    results = search(query=p["query"], today=TODAY)
    return bool(results) and all(r["legal_review_required"] for r in results)


def _policy_stale_warning(p, e):
    future = TODAY + datetime.timedelta(days=400)
    results = search(query="annual leave", today=future)
    return bool(results) and results[0]["stale"]


def _people_calc(p, e):
    if p["kind"] == "leave":
        return poc.annual_leave_entitlement(p["months"])["days"] == e["days"]
    if p["kind"] == "sick":
        return poc.sick_leave_breakdown(p["days"])["full_pay_days"] == e["full"]
    if p["kind"] == "probation":
        return poc.probation_end(p["start"]).isoformat() == e["end"]
    return False


def _policy_no_guess(p, e):
    return search(query=p["query"], today=TODAY) == []


def _policy_snapshot_date(p, e):
    results = search(query="annual leave", today=TODAY)
    return bool(results) and bool(results[0]["snapshot_date"])


def _choose_offer(p, e):
    lead = dict(LEAD_VARIANTS["good"], **{"Offer Match": "",
                                          "Problem Observed": p["problem"]})
    return outreach_composer.choose_offer(lead) == e["offer"]


def _outreach_draft(p, e):
    drafts = outreach_composer.compose_outreach(LEAD_VARIANTS["good"], "High")
    return e["contains"] in drafts["first_touch"]["body"]


def _outreach_refuse(p, e):
    try:
        outreach_composer.compose_outreach(LEAD_VARIANTS["good"], "Low")
        return False
    except outreach_composer.LeadNotReady:
        return True


def _outreach_followup(p, e):
    drafts = outreach_composer.compose_outreach(LEAD_VARIANTS["good"], "High")
    return e["contains"] in drafts["follow_up"]["body"]


def _csv_clean(p, e):
    _cleaned, report = data_cleaning_tool.clean_csv_text(p["csv_text"])
    return report["duplicates_removed"] == e["duplicates_removed"]


def _csv_validate(p, e):
    _cleaned, report = data_cleaning_tool.clean_csv_text(
        p["csv_text"], required_columns=p["required"])
    return len(report["problems"]) == e["problems"]


def _xlsx_valid(p, e):
    with _Workspace() as tmp:
        path = _fixture_workbook(tmp)
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
        return all(part in names for part in
                   ("[Content_Types].xml", "xl/workbook.xml", "xl/styles.xml"))


def _requires_ai(p, e):
    return None  # honestly not completable deterministically


RUNNERS = {
    "classify_request": _classify, "make_checklist": _checklist,
    "xlsx_tracker": _xlsx_tracker, "xlsx_create": _xlsx_create,
    "xlsx_edit": _xlsx_edit, "xlsx_read": _xlsx_read,
    "tracker_summary": _tracker_summary, "tracker_stale": _tracker_stale,
    "docx_report": _docx_report, "docx_minutes": _docx_minutes,
    "docx_letter": _docx_letter, "docx_placeholders": _docx_placeholders,
    "docx_read": _docx_read, "file_organize": _file_organize,
    "file_convention": _file_convention, "file_duplicates": _file_duplicates,
    "file_index": _file_index, "file_categorize": _file_categorize,
    "email_draft": _email_draft, "action_items": _action_items,
    "email_save": _email_save, "verify_lead": _verify_lead,
    "lead_duplicates": _lead_duplicates, "verify_tracker": _verify_tracker,
    "pipeline_metrics": _pipeline_metrics, "pipeline_stale": _pipeline_stale,
    "pipeline_report": _pipeline_report, "founder_briefing": _founder_briefing,
    "csv_stats": _csv_stats, "summarize": _summarize,
    "supervisor_plan": _supervisor_plan,
    "supervisor_escalation": _supervisor_escalation,
    "supervisor_followup": _supervisor_followup,
    "priority_check": _priority_check, "supervisor_empty": _supervisor_empty,
    "router_route": _router_route, "policy_lookup": _policy_lookup,
    "policy_category": _policy_category, "policy_legal_flag": _policy_legal_flag,
    "policy_stale_warning": _policy_stale_warning, "people_calc": _people_calc,
    "policy_no_guess": _policy_no_guess,
    "policy_snapshot_date": _policy_snapshot_date, "choose_offer": _choose_offer,
    "outreach_draft": _outreach_draft, "outreach_refuse": _outreach_refuse,
    "outreach_followup": _outreach_followup, "csv_clean": _csv_clean,
    "csv_validate": _csv_validate, "xlsx_valid": _xlsx_valid,
    "requires_ai": _requires_ai, "requires_ai_and_human": _requires_ai,
}
