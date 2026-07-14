/* AOS Partner Playground — SAFE DEMONSTRATION MODE.
   Everything below is a scripted, deterministic simulation that runs entirely
   in the browser. No AI model is called. No data is collected, stored, or sent.
   All names, numbers, and messages are fictional example data. */

(function () {
  "use strict";

  /* ---------- Partner catalog (labels match the AOS Partner Registry) ---------- */

  var PARTNERS = {
    atlas: { name: "Atlas", label: "active", role: "Executive coordination Partner — routes work, prepares briefings, keeps the owner in control." },
    librarian: { name: "The Librarian", label: "active", role: "Knowledge Partner — finds and explains approved company knowledge and documents." },
    guardian: { name: "Guardian", label: "active", role: "Risk Partner — reviews security, credentials, and safety rules before anything goes out." },
    office: { name: "AOS Office Partner", label: "proposed", role: "Office operations role — spreadsheets, documents, files, trackers, drafts, and registers." },
    supervisor: { name: "Department Supervisor", label: "concept", role: "Supervisor role — plans the day, assigns tasks to Partners, and escalates anything sensitive." },
    acquisition: { name: "Client Acquisition Partner", label: "proposed", role: "Sales support role — drafts personalized outreach and follow-ups for human approval." },
    reporting: { name: "Reporting Partner", label: "proposed", role: "Reporting role — turns trackers into pipeline reports and management briefings." },
    research: { name: "Research Partner", label: "proposed", role: "Research role — verifies leads, sources, and market information with confidence labels." },
    support: { name: "Customer Support Partner", label: "proposed", role: "Support role — classifies inquiries and drafts responses from approved answers." },
    people: { name: "People Operations Partner", label: "concept", role: "People/policy role — answers policy questions from approved sources and flags anything legal for human review." }
  };

  var LABEL_TEXT = { active: "Active Partner", proposed: "Proposed Partner", concept: "Concept Partner" };

  var INDUSTRIES = ["Education", "Training Center", "Real Estate", "Recruitment", "Events", "Consulting", "Professional Services", "Other"];

  var PAINS = [
    { key: "leads", label: "Lead follow-up", team: ["acquisition", "reporting", "atlas", "guardian"], demo: "lead-followup" },
    { key: "inquiries", label: "Customer inquiries", team: ["support", "office", "librarian", "atlas"], demo: "education-inquiry" },
    { key: "admin", label: "Office administration", team: ["office", "supervisor", "atlas", "guardian"], demo: "office-admin-day" },
    { key: "documents", label: "Document handling", team: ["office", "librarian", "atlas"], demo: "office-admin-day" },
    { key: "reporting", label: "Reporting", team: ["reporting", "office", "atlas"], demo: "management-report" },
    { key: "scheduling", label: "Scheduling", team: ["office", "supervisor", "atlas"], demo: "department-planning" },
    { key: "approvals", label: "Approvals", team: ["supervisor", "atlas", "guardian"], demo: "department-planning" },
    { key: "research", label: "Research", team: ["research", "librarian", "atlas"], demo: "management-report" },
    { key: "operations", label: "Internal operations", team: ["office", "supervisor", "reporting", "atlas"], demo: "office-admin-day" },
    { key: "people", label: "Employee / people operations", team: ["people", "office", "supervisor", "guardian"], demo: "department-planning" }
  ];

  /* ---------- Demo definitions ---------- */

  var DEMOS = [
    {
      id: "education-inquiry",
      title: "Education Inquiry to Response",
      tag: "Education / Training",
      desc: "A parent asks about enrollment. The team classifies the inquiry, pulls approved answers, drafts a reply, and sends it to a human for approval.",
      steps: [
        { actor: "Incoming", text: "New inquiry received: \"Hello, is enrollment for the September intake still open? What documents do we need for a Grade 7 transfer?\" (fictional example)" },
        { actor: "Customer Support Partner", text: "Classifies inquiry: type = Admissions, urgency = Normal, language = English." },
        { actor: "The Librarian", text: "Retrieves the approved Admissions FAQ and the Grade 7 transfer document checklist." },
        { actor: "Customer Support Partner", text: "Drafts a reply using only approved knowledge — no invented dates, no invented fees." },
        { actor: "Guardian", text: "Checks the draft: no private student data included, no commitments beyond approved policy." },
        { actor: "Atlas", text: "Packages the draft and creates one follow-up task for the admissions officer." },
        { actor: "Human — Admissions Officer", human: true, text: "Reviews the draft, edits one sentence, and approves sending. Only a human sends." }
      ],
      outputs: {
        email: {
          subject: "RE: September Intake — Grade 7 Transfer",
          to: "parent@example.com (fictional)",
          body: "Dear Parent,\n\nThank you for contacting us. Yes — enrollment for the September intake is currently open.\n\nFor a Grade 7 transfer we need:\n  1. Previous school reports (last 2 years)\n  2. Transfer certificate from the current school\n  3. A copy of the student's ID / passport\n  4. Completed application form\n\nIf you would like, we can book a short campus visit this week.\n\nBest regards,\nAdmissions Office\n\n[DRAFT — awaiting human approval before sending]"
        },
        tasks: [
          "Follow up with parent if no reply within 3 working days",
          "Confirm Grade 7 seat availability with the registrar",
          "Log inquiry in the admissions tracker"
        ],
        approval: {
          items: [
            "Send the drafted reply to the parent — requires Admissions Officer approval",
            "No other actions are taken automatically"
          ]
        }
      }
    },
    {
      id: "lead-followup",
      title: "Lead to Follow-Up",
      tag: "Sales / Any industry",
      desc: "A verified lead sits in the tracker with no follow-up. The team scores it, drafts a personalized follow-up, and updates the pipeline — a human approves before anything is sent.",
      steps: [
        { actor: "Atlas", text: "Daily pipeline scan: 1 verified lead has had no follow-up for 4 days (fictional example lead)." },
        { actor: "Research Partner", text: "Re-checks the lead record: company website active, contact role confirmed, no duplicate entry. Confidence: High." },
        { actor: "Client Acquisition Partner", text: "Selects the approved offer that fits the lead's stated pain and drafts a personalized follow-up." },
        { actor: "Guardian", text: "Confirms the draft makes no false claims and includes no pricing outside the approved catalog." },
        { actor: "AOS Office Partner", text: "Updates the lead tracker: status, last-contact date, next-action date." },
        { actor: "Human — Founder", human: true, text: "Reviews the follow-up draft and approves sending from the official mailbox. Nothing is sent automatically." }
      ],
      outputs: {
        email: {
          subject: "Following up — the workflow we discussed",
          to: "lead@example-company.com (fictional)",
          body: "Hi Sarah,\n\nLast week you mentioned your team loses track of inquiries once things get busy.\n\nThat is exactly the problem our Workflow Starter Pack fixes: a working lead-tracking system, one documented internal process, and a simple owner dashboard — delivered in 5-7 business days.\n\nWould a 15-minute call this week be useful?\n\nBest regards,\nAbdulrahman\n\n[DRAFT — awaiting human approval before sending]"
        },
        sheet: {
          title: "Lead_Tracker.xlsx — updated row (fictional data)",
          headers: ["Lead", "Company", "Status", "Last Contact", "Next Action", "Owner"],
          rows: [
            ["Sarah M.", "Example Trading LLC", "Follow-up drafted", "2026-07-14", "2026-07-17", "Founder"],
            ["Omar K.", "Sample Institute", "Proposal sent", "2026-07-12", "2026-07-15", "Founder"],
            ["Lina A.", "Demo Events Co", "New", "2026-07-13", "2026-07-14", "Founder"]
          ]
        },
        tasks: [
          "Approve and send follow-up to Sarah M.",
          "Prepare proposal if Sarah replies positively",
          "Review 2 stale leads flagged for re-qualification"
        ],
        approval: {
          items: [
            "Send follow-up email — requires Founder approval",
            "Move lead to 'Contacted' after sending — automatic once approved"
          ]
        }
      }
    },
    {
      id: "management-report",
      title: "Management Report to Decision",
      tag: "Management / Any industry",
      desc: "The team reads real tracker data, computes honest metrics, and prepares a management report with a recommended decision — the decision itself stays human.",
      steps: [
        { actor: "Reporting Partner", text: "Reads the week's trackers: 25 leads, 14 contacted, 3 proposals, 1 payment attempt (fictional example numbers)." },
        { actor: "Reporting Partner", text: "Computes conversion by stage and flags 6 leads as stale (no touch in 7+ days)." },
        { actor: "The Librarian", text: "Attaches the approved offer catalog so recommendations reference real, approved offers only." },
        { actor: "Atlas", text: "Prepares the management briefing: what happened, what it means, and one recommended decision with trade-offs." },
        { actor: "Human — Founder", human: true, text: "Reads the briefing and makes the decision. The system recommends; the human decides." }
      ],
      outputs: {
        report: {
          title: "Weekly Pipeline Briefing (fictional example)",
          body: "WEEK IN NUMBERS\n  Leads researched: 25\n  Outreach sent: 14 (56%)\n  Replies: 5 (36% of contacted)\n  Proposals: 3\n  Payment attempts: 1\n\nWHAT IT MEANS\n  Outreach volume is on target. Drop-off is between reply and proposal:\n  only 3 of 5 replies received a proposal within 48 hours.\n\nRECOMMENDED DECISION\n  Prioritize proposal turnaround over new lead volume next week.\n  Trade-off: fewer new leads researched (15 instead of 25).\n\nDECISION REQUIRED BY: Founder"
        },
        dashboard: {
          kpis: [
            { label: "Leads", value: "25" },
            { label: "Contacted", value: "14" },
            { label: "Replies", value: "5" },
            { label: "Proposals", value: "3" },
            { label: "Stale leads", value: "6" }
          ],
          insight: "Bottleneck detected: reply-to-proposal turnaround (currently > 48h for 2 of 5 replies). Recommendation: shift effort from new-lead research to proposal preparation next week."
        },
        approval: {
          items: [
            "Adopt 'proposal-first' plan for next week — Founder decision",
            "Archive 6 stale leads or schedule one final follow-up — Founder decision"
          ]
        }
      }
    },
    {
      id: "office-admin-day",
      title: "Office Administration Day",
      tag: "Operations / Any industry",
      desc: "A morning of mixed requests lands in the office inbox. The Office Partner classifies everything, updates trackers, drafts the documents, and queues approvals.",
      steps: [
        { actor: "Incoming", text: "6 requests arrive overnight: 2 client questions, 1 meeting to schedule, 1 report request, 1 invoice query, 1 supplier document (all fictional)." },
        { actor: "AOS Office Partner", text: "Classifies all 6 requests by type and urgency; nothing is left unfiled." },
        { actor: "AOS Office Partner", text: "Updates the activity tracker spreadsheet with all 6 items and their owners." },
        { actor: "AOS Office Partner", text: "Drafts the requested monthly summary report as a formatted document." },
        { actor: "AOS Office Partner", text: "Creates task entries and drafts 2 reply emails for human review." },
        { actor: "Department Supervisor", text: "Reviews the batch: approves the routine items, escalates the invoice query to the Founder (money-related = human decision)." },
        { actor: "Human — Office Manager", human: true, text: "Approves the 2 drafted replies and the report. The invoice query goes to the Founder." }
      ],
      outputs: {
        email: {
          subject: "RE: Meeting request — proposed times",
          to: "client@example.com (fictional)",
          body: "Dear Mr. Hassan,\n\nThank you for your message. We would be glad to meet.\n\nProposed times (this week):\n  - Wednesday 10:00\n  - Thursday 14:00\n\nPlease let us know which works best, and we will send a calendar confirmation.\n\nBest regards,\nOffice Team\n\n[DRAFT — awaiting human approval before sending]"
        },
        sheet: {
          title: "Office_Activity_Tracker.xlsx (fictional data)",
          headers: ["#", "Request", "Type", "Urgency", "Owner", "Status"],
          rows: [
            ["1", "Client question — delivery date", "Client", "High", "Office", "Reply drafted"],
            ["2", "Client question — document copy", "Client", "Normal", "Office", "Reply drafted"],
            ["3", "Meeting request — Mr. Hassan", "Scheduling", "Normal", "Office", "Times proposed"],
            ["4", "Monthly summary report", "Reporting", "Normal", "Office", "Draft ready"],
            ["5", "Invoice query — Supplier X", "Finance", "High", "Founder", "Escalated"],
            ["6", "Supplier compliance document", "Filing", "Low", "Office", "Filed"]
          ]
        },
        report: {
          title: "Monthly_Office_Summary.docx — draft preview (fictional)",
          body: "MONTHLY OFFICE SUMMARY — JUNE (EXAMPLE)\n\n1. Requests handled: 118 (up 9% from May)\n2. Average response time: 1.4 working days\n3. Meetings scheduled: 22\n4. Documents filed: 64\n5. Open items carried to July: 7\n\nPrepared by: AOS Office Partner (draft)\nReviewed by: [pending human review]"
        },
        tasks: [
          "Approve 2 drafted client replies",
          "Review monthly summary report draft",
          "Founder: decide on Supplier X invoice query",
          "Confirm Wednesday/Thursday meeting slot when client responds"
        ],
        approval: {
          items: [
            "Send 2 client replies — Office Manager approval",
            "Issue monthly report — Office Manager approval",
            "Invoice query — escalated to Founder (financial decision)"
          ]
        }
      }
    },
    {
      id: "department-planning",
      title: "Department Daily Planning",
      tag: "Supervisor / Any industry",
      desc: "A Department Supervisor reads goals, deadlines, backlog, and KPIs — then proposes today's task plan with Partner assignments and approval requests.",
      steps: [
        { actor: "Department Supervisor", text: "Reads department inputs: 2 goals, 9 open work items, 3 deadlines this week, KPI status, yesterday's unfinished tasks (fictional)." },
        { actor: "Department Supervisor", text: "Builds today's plan: 7 tasks, priority-ordered, each with a reason — no invented busywork." },
        { actor: "Department Supervisor", text: "Assigns tasks to Partners within approved scope; flags 1 task as requiring human approval (external commitment)." },
        { actor: "Department Supervisor", text: "Creates 2 follow-up tasks for work unfinished yesterday, instead of silently dropping it." },
        { actor: "Atlas", text: "Adds the plan to the morning briefing for the department lead." },
        { actor: "Human — Department Lead", human: true, text: "Approves 6 of 7 tasks, reschedules 1, and handles the flagged external commitment personally." }
      ],
      outputs: {
        sheet: {
          title: "Daily Department Plan (fictional example)",
          headers: ["Partner", "Task", "Priority", "Deadline", "Reason", "Approval", "Status"],
          rows: [
            ["Office Partner", "Update client tracker with 4 new records", "P1", "Today 12:00", "Deadline: weekly report depends on it", "No", "Planned"],
            ["Office Partner", "Prepare meeting pack for Thursday review", "P1", "Wed 17:00", "Deadline this week", "No", "Planned"],
            ["Reporting Partner", "Draft weekly KPI report", "P2", "Thu 10:00", "Recurring duty", "No", "Planned"],
            ["Research Partner", "Verify 5 new leads", "P2", "Today 17:00", "Goal: pipeline growth", "No", "Planned"],
            ["Acquisition Partner", "Draft 3 follow-ups for stale leads", "P2", "Today 17:00", "KPI: response time slipping", "Human approves sending", "Planned"],
            ["Office Partner", "Finish yesterday's filing backlog (12 docs)", "P3", "Fri", "Carried over — unfinished", "No", "Follow-up"],
            ["Supervisor", "Confirm venue quote with supplier", "P1", "Today 15:00", "External commitment", "ESCALATED to human", "Awaiting approval"]
          ]
        },
        dashboard: {
          kpis: [
            { label: "Planned tasks", value: "7" },
            { label: "Escalated", value: "1" },
            { label: "Carried over", value: "2" },
            { label: "On-track KPIs", value: "4 / 5" }
          ],
          insight: "Response-time KPI is slipping (2.1 days vs 1.5 target) — today's plan weights follow-up drafting to correct it. The supplier commitment is escalated because external commitments always require a human."
        },
        approval: {
          items: [
            "Approve today's 7-task plan — Department Lead",
            "Supplier venue commitment — human only, Supervisor may not commit externally",
            "Any change to task priorities — Department Lead"
          ]
        },
        tasks: [
          "Department Lead: approve daily plan (2 minutes)",
          "Department Lead: handle supplier commitment call",
          "Supervisor: monitor unfinished work and roll follow-ups into tomorrow's plan"
        ]
      }
    },
    {
      id: "trading-architecture",
      title: "Five-Agent Trading Architecture",
      tag: "Architecture demonstration",
      warn: true,
      warning: "ARCHITECTURE DEMONSTRATION ONLY — NOT FINANCIAL ADVICE — NO LIVE TRADING — NO PROFIT CLAIMS. This demo never connects to any brokerage or market data. All content is fictional and illustrates multi-agent structure only.",
      desc: "How a five-role analysis team debates a question from both sides before a human sees a synthesis. Shown to demonstrate multi-agent architecture — not to trade.",
      steps: [
        { actor: "Manager", text: "Frames a fictional research question: \"Summarize the arguments around Example Sector X this week.\" No live data is used." },
        { actor: "News Analyst", text: "Summarizes fictional example headlines relevant to Sector X and labels each by source reliability." },
        { actor: "Strategy Analyst", text: "Maps 3 fictional scenarios (expansion, stagnation, contraction) with the assumptions each depends on." },
        { actor: "Bull Analyst", text: "Argues the strongest honest positive case, citing the scenario assumptions it relies on." },
        { actor: "Bear Analyst", text: "Argues the strongest honest negative case, including risks the bull case underweights." },
        { actor: "Manager", text: "Synthesizes both cases, states what remains unknown, and prepares a briefing. No recommendation to buy or sell anything is made." },
        { actor: "Human", human: true, text: "Reads the synthesis. Any real-world decision — financial or otherwise — belongs entirely to humans and licensed professionals." }
      ],
      outputs: {
        report: {
          title: "Manager Synthesis (fictional demonstration content)",
          body: "RESEARCH QUESTION\n  Arguments around Example Sector X this week (fictional).\n\nNEWS SUMMARY (fictional)\n  - Two example reports suggest rising demand; one is from a low-reliability source.\n  - One regulatory consultation opened; outcome unknown.\n\nSCENARIOS\n  A. Expansion — depends on demand reports being accurate.\n  B. Stagnation — likely if regulation introduces delays.\n  C. Contraction — if both demand is overstated and regulation tightens.\n\nBULL CASE\n  Demand signals are broad-based across two independent sources.\n\nBEAR CASE\n  The strongest demand claim comes from the weakest source; the\n  regulatory consultation is unresolved and could reverse the trend.\n\nWHAT WE DO NOT KNOW\n  Regulatory outcome, real demand data quality.\n\nThis is an architecture demonstration. It is not financial advice,\nno live data was used, and no trading action exists in this system."
        },
        approval: {
          items: [
            "There is nothing to approve — this architecture produces analysis for humans, never trades",
            "Any real deployment of a multi-agent research team is scoped with explicit human-only decision gates"
          ]
        }
      }
    }
  ];

  /* ---------- Rendering ---------- */

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  var state = { industry: null, pain: null, timer: null };

  function renderChips() {
    var irow = document.getElementById("industry-row");
    INDUSTRIES.forEach(function (ind) {
      var chip = el("button", "chip", ind);
      chip.type = "button";
      chip.setAttribute("role", "option");
      chip.addEventListener("click", function () {
        state.industry = ind;
        Array.prototype.forEach.call(irow.children, function (c) { c.classList.remove("selected"); });
        chip.classList.add("selected");
        renderTeam();
      });
      irow.appendChild(chip);
    });
    var prow = document.getElementById("pain-row");
    PAINS.forEach(function (pain) {
      var chip = el("button", "chip", pain.label);
      chip.type = "button";
      chip.setAttribute("role", "option");
      chip.addEventListener("click", function () {
        state.pain = pain;
        Array.prototype.forEach.call(prow.children, function (c) { c.classList.remove("selected"); });
        chip.classList.add("selected");
        renderTeam();
      });
      prow.appendChild(chip);
    });
  }

  function renderTeam() {
    if (!state.pain) return;
    var panel = document.getElementById("team-panel");
    panel.hidden = false;
    var industry = state.industry || "your business";
    document.getElementById("team-title").textContent =
      "Recommended team for " + state.pain.label.toLowerCase() + " — " + industry;
    document.getElementById("team-note").textContent =
      "This is the Partner structure we would design for this pain. Every team keeps a human in charge of approvals and final decisions.";
    var grid = document.getElementById("team-grid");
    grid.innerHTML = "";
    state.pain.team.forEach(function (key) {
      var p = PARTNERS[key];
      var card = el("div", "team-member");
      card.appendChild(el("h4", null, p.name));
      card.appendChild(el("span", "p-label p-" + p.label, LABEL_TEXT[p.label]));
      card.appendChild(el("p", null, p.role));
      grid.appendChild(card);
    });
    var suggested = DEMOS.filter(function (d) { return d.id === state.pain.demo; })[0];
    if (suggested) {
      var hint = el("p", null, "Suggested demo for this pain: \"" + suggested.title + "\" — find it below.");
      hint.style.color = "var(--cyan-soft)";
      grid.appendChild(hint);
    }
  }

  function renderDemoCards() {
    var grid = document.getElementById("demo-grid");
    DEMOS.forEach(function (demo) {
      var card = el("div", "demo-card");
      card.appendChild(el("div", "demo-tag" + (demo.warn ? " warn" : ""), demo.tag));
      card.appendChild(el("h3", null, demo.title));
      card.appendChild(el("p", null, demo.desc));
      var btn = el("button", "btn btn-primary", "Run demo");
      btn.type = "button";
      btn.addEventListener("click", function () { playDemo(demo); });
      card.appendChild(btn);
      grid.appendChild(card);
    });
  }

  var OUTPUT_LABELS = {
    email: "Email draft",
    sheet: "Spreadsheet",
    report: "Report",
    dashboard: "Dashboard",
    tasks: "Task checklist",
    approval: "Approvals"
  };

  function renderOutput(kind, data) {
    var panel = document.getElementById("output-panel");
    panel.innerHTML = "";
    if (kind === "email") {
      panel.appendChild(el("h4", null, "Subject: " + data.subject));
      panel.appendChild(el("p", null, "To: " + data.to));
      var pre = el("pre", null, data.body);
      panel.appendChild(pre);
    } else if (kind === "sheet") {
      panel.appendChild(el("h4", null, data.title));
      var table = el("table");
      var thead = el("thead");
      var hr = el("tr");
      data.headers.forEach(function (h) { hr.appendChild(el("th", null, h)); });
      thead.appendChild(hr);
      table.appendChild(thead);
      var tbody = el("tbody");
      data.rows.forEach(function (row) {
        var tr = el("tr");
        row.forEach(function (cell) { tr.appendChild(el("td", null, cell)); });
        tbody.appendChild(tr);
      });
      table.appendChild(tbody);
      panel.appendChild(table);
    } else if (kind === "report") {
      panel.appendChild(el("h4", null, data.title));
      panel.appendChild(el("pre", null, data.body));
    } else if (kind === "dashboard") {
      var row = el("div", "kpi-row");
      data.kpis.forEach(function (k) {
        var box = el("div", "kpi");
        box.appendChild(el("div", "k-label", k.label));
        box.appendChild(el("div", "k-value", k.value));
        row.appendChild(box);
      });
      panel.appendChild(row);
      panel.appendChild(el("h4", null, "Insight"));
      panel.appendChild(el("p", null, data.insight));
    } else if (kind === "tasks") {
      panel.appendChild(el("h4", null, "Task checklist"));
      var ul = el("ul");
      data.forEach(function (t) { ul.appendChild(el("li", null, t)); });
      panel.appendChild(ul);
    } else if (kind === "approval") {
      var box2 = el("div", "approval-box");
      box2.appendChild(el("div", "a-head", "Approval requests — humans decide"));
      var ul2 = el("ul");
      data.items.forEach(function (t) { ul2.appendChild(el("li", null, t)); });
      box2.appendChild(ul2);
      panel.appendChild(box2);
    }
  }

  function renderOutputTabs(demo) {
    var tabs = document.getElementById("output-tabs");
    tabs.innerHTML = "";
    var kinds = Object.keys(OUTPUT_LABELS).filter(function (k) { return demo.outputs[k]; });
    kinds.forEach(function (kind, i) {
      var tab = el("button", "output-tab" + (i === 0 ? " selected" : ""), OUTPUT_LABELS[kind]);
      tab.type = "button";
      tab.setAttribute("role", "tab");
      tab.addEventListener("click", function () {
        Array.prototype.forEach.call(tabs.children, function (t) { t.classList.remove("selected"); });
        tab.classList.add("selected");
        renderOutput(kind, demo.outputs[kind]);
      });
      tabs.appendChild(tab);
    });
    if (kinds.length) renderOutput(kinds[0], demo.outputs[kinds[0]]);
  }

  function playDemo(demo) {
    if (state.timer) { clearInterval(state.timer); state.timer = null; }
    var section = document.getElementById("stage-section");
    section.hidden = false;
    document.getElementById("stage-eyebrow").textContent = demo.tag;
    document.getElementById("stage-title").textContent = demo.title;
    document.getElementById("stage-desc").textContent = demo.desc;
    var warning = document.getElementById("stage-warning");
    if (demo.warning) {
      warning.hidden = false;
      warning.textContent = demo.warning;
    } else {
      warning.hidden = true;
      warning.textContent = "";
    }
    var log = document.getElementById("stage-log");
    log.innerHTML = "";
    renderOutputTabs(demo);
    section.scrollIntoView({ behavior: "smooth", block: "start" });

    var i = 0;
    function addStep() {
      if (i >= demo.steps.length) { clearInterval(state.timer); state.timer = null; return; }
      var step = demo.steps[i];
      var li = el("li", step.human ? "human" : null);
      li.appendChild(el("span", "actor", step.actor));
      li.appendChild(document.createTextNode(step.text));
      log.appendChild(li);
      window.requestAnimationFrame(function () {
        window.requestAnimationFrame(function () { li.classList.add("shown"); });
      });
      log.scrollTop = log.scrollHeight;
      i += 1;
    }
    addStep();
    state.timer = window.setInterval(addStep, 1400);
    document.getElementById("stage-replay").onclick = function () { playDemo(demo); };
  }

  renderChips();
  renderDemoCards();
})();
