"""Atlas Capability Benchmark v1 - task definitions (PRJ-014). Stdlib only.

Defines 100+ realistic company tasks across 13 categories. Each task names a
runner (implemented in benchmark_runners.py) plus parameters and an expected
outcome. Tasks marked runner="requires_ai" cannot be completed by
deterministic local tools — in DETERMINISTIC LOCAL mode they are honestly
counted as NOT completed.
"""


def _t(task_id, category, description, runner, params=None, expected=None):
    return {"id": task_id, "category": category, "description": description,
            "runner": runner, "params": params or {}, "expected": expected}


def build_tasks():
    tasks = []
    n = [0]

    def add(category, description, runner, params=None, expected=None):
        n[0] += 1
        tasks.append(_t("ACB-%03d" % n[0], category, description, runner,
                        params, expected))

    # --- office administration (8) ---
    for text, rtype in [
            ("URGENT: client asks for invoice copy and payment status", "finance"),
            ("Please schedule a meeting with the supplier next week", "scheduling"),
            ("Need the monthly KPI report for management", "reporting"),
            ("Customer complaint about late delivery", "client"),
            ("Archive last year's contract documents", "filing"),
            ("Employee asks about sick leave balance", "people")]:
        add("office administration",
            "Classify the request: '%s'" % text, "classify_request",
            {"text": text}, {"type": rtype})
    add("office administration", "Build a 4-item task checklist for the morning intake",
        "make_checklist", {"items": ["Log requests", "Update tracker",
                                     "Draft replies", "Escalate finance items"]},
        {"contains": "- [ ] Log requests"})
    add("office administration", "Answer a phone inquiry with judgment and empathy",
        "requires_ai")

    # --- Excel (9) ---
    for month in (1, 3, 7):
        add("excel", "Create the %d/2026 monthly tracker workbook" % month,
            "xlsx_tracker", {"year": 2026, "month": month})
    add("excel", "Create a client register workbook with 3 records", "xlsx_create",
        {"headers": ["Client", "Status", "Value"],
         "rows": [["A LLC", "Active", 399], ["B Ltd", "New", 450], ["C Co", "Won", 399]]})
    add("excel", "Append 2 rows to an existing workbook and verify", "xlsx_edit",
        {"new_rows": [["D Corp", "New", 0], ["E Inc", "Proposal", 450]]})
    add("excel", "Read a workbook back and count its data rows", "xlsx_read",
        {"expected_rows": 3})
    add("excel", "Summarize tracker statuses from a workbook", "tracker_summary",
        {})
    add("excel", "Find stale open items in a tracker", "tracker_stale", {})
    add("excel", "Build a financial model with scenario formulas", "requires_ai")

    # --- Word (8) ---
    add("word", "Create a management report with metrics table", "docx_report",
        {"title": "Quarterly Operations Report"})
    add("word", "Create meeting minutes with decisions and actions", "docx_minutes", {})
    add("word", "Create a professional business letter", "docx_letter",
        {"subject": "Engagement confirmation"})
    add("word", "Replace placeholders in a document template", "docx_placeholders",
        {"mapping": {"client": "Horizon LLC", "total": "$399"}})
    add("word", "Extract plain text from a generated document", "docx_read", {})
    add("word", "Create a policy document draft from a template", "docx_report",
        {"title": "Leave Policy Draft"})
    add("word", "Write a persuasive one-page proposal narrative", "requires_ai")
    add("word", "Edit a complex third-party contract preserving format", "requires_ai")

    # --- files (8) ---
    add("files", "Organize a messy folder into category subfolders", "file_organize", {})
    add("files", "Apply the AOS naming convention to loose files", "file_convention",
        {"name": "budget report.xlsx", "category": "Spreadsheets"},
        {"starts": "2026-"})
    add("files", "Detect duplicate files by content", "file_duplicates", {})
    add("files", "Generate a folder INDEX.md", "file_index", {})
    for ext, cat in [("report.pdf", "Documents"), ("data.csv", "Spreadsheets"),
                     ("logo.png", "Images")]:
        add("files", "Categorize file '%s'" % ext, "file_categorize",
            {"name": ext}, {"category": cat})
    add("files", "Decide which old records are safe to destroy", "requires_ai")

    # --- email drafting (8) ---
    for kind in ("reply", "follow_up", "meeting_confirmation", "internal_update"):
        add("email drafting", "Draft a %s email (never sent)" % kind, "email_draft",
            {"kind": kind}, {"contains": "DRAFT"})
    add("email drafting", "Extract action items from a message", "action_items",
        {"text": "Please send the proposal by Thursday. Weather is nice. "
                 "We need to confirm the room. Thanks!", "min_items": 2})
    add("email drafting", "Save a draft for human review", "email_save", {})
    add("email drafting", "De-escalate an angry customer thread", "requires_ai")
    add("email drafting", "Negotiate payment terms by email", "requires_ai")

    # --- research (8) ---
    add("research", "Verify a complete lead → High confidence", "verify_lead",
        {"variant": "good"}, {"confidence": "High"})
    add("research", "Detect social-only source → Medium confidence", "verify_lead",
        {"variant": "social"}, {"confidence": "Medium"})
    add("research", "Detect missing fields → Low confidence", "verify_lead",
        {"variant": "incomplete"}, {"confidence": "Low"})
    add("research", "Detect placeholder rows", "verify_lead",
        {"variant": "placeholder"}, {"confidence": "Low"})
    add("research", "Detect duplicate leads across a tracker", "lead_duplicates", {})
    add("research", "Verify a full lead tracker file", "verify_tracker", {})
    add("research", "Research a new market's competitors online", "requires_ai")
    add("research", "Judge the credibility of conflicting sources", "requires_ai")

    # --- reporting (8) ---
    add("reporting", "Compute pipeline metrics excluding placeholders",
        "pipeline_metrics", {}, {"leads_total": 2})
    add("reporting", "Identify stale leads needing a decision", "pipeline_stale",
        {}, {"stale": ["L-001"]})
    add("reporting", "Write the pipeline report file", "pipeline_report", {})
    add("reporting", "Write the Founder briefing file", "founder_briefing", {})
    add("reporting", "Count CSV rows by status", "csv_stats",
        {"csv_text": "Lead,Status\nA,New\nB,New\nC,Won\n", "count_by": "Status"},
        {"count_new": 2})
    add("reporting", "Summarize a long update into key lines", "summarize",
        {"max_items": 3})
    add("reporting", "Explain WHY numbers moved this week", "requires_ai")
    add("reporting", "Present results persuasively to a client", "requires_ai")

    # --- management (8) ---
    add("management", "Build a bounded daily department plan", "supervisor_plan",
        {}, {"max_tasks": 8})
    add("management", "Escalate an external commitment to a human",
        "supervisor_escalation", {}, {"escalated_min": 1})
    add("management", "Create follow-ups for unfinished work", "supervisor_followup", {})
    add("management", "Prioritize a due-today task as P1", "priority_check",
        {}, {"label": "P1"})
    add("management", "Refuse to invent busywork with no inputs", "supervisor_empty",
        {}, {"tasks": 0})
    add("management", "Route a strategy question to CEO review", "router_route",
        {"text": "Should we enter a new market with this business idea?"},
        {"skill": "aos-ceo-command-center"})
    add("management", "Coach an underperforming team member", "requires_ai")
    add("management", "Make the final call on a trade-off", "requires_ai")

    # --- HR / policy retrieval (8) ---
    add("hr policy", "Retrieve annual leave policy with sources", "policy_lookup",
        {"query": "annual leave"}, {"item_id": "PLK-UAE-002"})
    add("hr policy", "Retrieve probation rules by category", "policy_category",
        {"category": "probation"}, {"item_id": "PLK-UAE-005"})
    add("hr policy", "Flag termination questions for legal review", "policy_legal_flag",
        {"query": "termination notice"})
    add("hr policy", "Warn when policy knowledge is stale", "policy_stale_warning", {})
    add("hr policy", "Compute annual leave for 9 months service", "people_calc",
        {"kind": "leave", "months": 9}, {"days": 6})
    add("hr policy", "Compute sick leave tiers for 50 days", "people_calc",
        {"kind": "sick", "days": 50}, {"full": 15})
    add("hr policy", "Compute probation end date", "people_calc",
        {"kind": "probation", "start": "2026-01-15"}, {"end": "2026-07-15"})
    add("hr policy", "Give a final legal opinion on a dismissal", "requires_ai_and_human")

    # --- project operations (8) ---
    add("project operations", "Create a project folder index", "file_index", {})
    add("project operations", "Build a project meeting pack document", "docx_minutes", {})
    add("project operations", "Create a project deadline tracker", "xlsx_tracker",
        {"year": 2026, "month": 8})
    add("project operations", "Checklist a delivery workflow", "make_checklist",
        {"items": ["Intake", "Build", "QA", "Deliver", "Follow-up"]},
        {"contains": "- [ ] QA"})
    add("project operations", "Classify an incoming project request", "classify_request",
        {"text": "Please prepare the project report for Friday"},
        {"type": "reporting"})
    add("project operations", "Route document work to the document engineer",
        "router_route", {"text": "Restructure the document into an official document"},
        {"skill": "aos-document-engineer"})
    add("project operations", "Scope an ambiguous new project", "requires_ai")
    add("project operations", "Resolve conflicting stakeholder needs", "requires_ai")

    # --- sales operations (8) ---
    add("sales operations", "Choose the right offer for a workflow pain", "choose_offer",
        {"problem": "manual tracking and lost follow-ups"},
        {"offer": "AI Workflow Starter Pack"})
    add("sales operations", "Choose the agent pack for an AI pain", "choose_offer",
        {"problem": "wants an ai assistant to delegate research"},
        {"offer": "AI Agent Starter Pack"})
    add("sales operations", "Draft personalized outreach for a verified lead",
        "outreach_draft", {}, {"contains": "$399 USD"})
    add("sales operations", "Refuse outreach for an unverified lead",
        "outreach_refuse", {})
    add("sales operations", "Draft a follow-up with an easy out", "outreach_followup",
        {}, {"contains": "no problem"})
    add("sales operations", "Route lead work to the acquisition skill", "router_route",
        {"text": "Draft a cold email for this lead"},
        {"skill": "aos-client-acquisition-engine"})
    add("sales operations", "Handle a live pricing objection", "requires_ai")
    add("sales operations", "Close a deal on a call", "requires_ai_and_human")

    # --- knowledge retrieval (7) ---
    add("knowledge retrieval", "Route a policy question to the retriever",
        "router_route", {"text": "What is the annual leave policy?"},
        {"skill": "aos-policy-retriever"})
    add("knowledge retrieval", "Return empty result instead of guessing",
        "policy_no_guess", {"query": "crypto trading bonus scheme"})
    add("knowledge retrieval", "Show SOURCE SNAPSHOT DATE on offline answers",
        "policy_snapshot_date", {})
    add("knowledge retrieval", "Retrieve working hours rules", "policy_lookup",
        {"query": "working hours"}, {"item_id": "PLK-UAE-001"})
    add("knowledge retrieval", "Retrieve employee records rules", "policy_lookup",
        {"query": "employee records"}, {"item_id": "PLK-UAE-007"})
    add("knowledge retrieval", "Answer from unindexed tribal knowledge", "requires_ai")
    add("knowledge retrieval", "Synthesize across many long documents", "requires_ai")

    # --- quality control (7) ---
    add("quality control", "Clean a CSV and remove duplicates", "csv_clean",
        {"csv_text": "Name,Phone\n  Ali ,0501\nAli,0501\nSara,n/a\n"},
        {"duplicates_removed": 1})
    add("quality control", "Validate required columns in data", "csv_validate",
        {"csv_text": "Name,Phone\nAli,\n", "required": ["Phone"]},
        {"problems": 1})
    add("quality control", "Verify a workbook has required OOXML parts", "xlsx_valid", {})
    add("quality control", "Confirm drafts carry the NOT SENT label", "email_draft",
        {"kind": "reply"}, {"contains": "DRAFT"})
    add("quality control", "Route final output review to QA skill", "router_route",
        {"text": "Please do a final check and review the output"},
        {"skill": "aos-qa-auditor"})
    add("quality control", "Judge whether a report reads professionally", "requires_ai")
    add("quality control", "Review code for subtle logic bugs", "requires_ai")

    return tasks


if __name__ == "__main__":
    tasks = build_tasks()
    cats = {}
    for t in tasks:
        cats[t["category"]] = cats.get(t["category"], 0) + 1
    print("Total tasks:", len(tasks))
    for c, k in sorted(cats.items()):
        print("  %-22s %d" % (c, k))
