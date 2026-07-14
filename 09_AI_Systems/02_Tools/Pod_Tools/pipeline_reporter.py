"""AOS Pod Tools - pipeline reporter (PRJ-014 pod). Standard library only.

Deterministic reporting for the Reporting role (PARTNER-012):
  * reads the real revenue trackers (Lead, Outreach, Client Pipeline CSVs)
  * counts real metrics — never invents numbers
  * identifies stale leads (no next action / old dates)
  * prepares a pipeline report and a Founder briefing as Markdown text

Placeholder/example rows are excluded from all counts and clearly reported.
"""

import csv
import datetime
import os

from research_verifier import is_placeholder

DEFAULT_PATHS = {
    "leads": "01_Holding_Company/04_Operations/03_Revenue_Operations/Lead_Tracker.csv",
    "outreach": "01_Holding_Company/04_Operations/03_Revenue_Operations/Outreach_Tracker.csv",
    "pipeline": "01_Holding_Company/04_Operations/03_Revenue_Operations/Client_Pipeline.csv",
}


def _read(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _count_by(rows, column):
    counts = {}
    for row in rows:
        key = (row.get(column) or "").strip() or "(blank)"
        counts[key] = counts.get(key, 0) + 1
    return counts


def compute_metrics(paths=None, today=None, stale_days=7):
    paths = paths or DEFAULT_PATHS
    today = today or datetime.date.today()
    leads_all = _read(paths["leads"])
    outreach_all = _read(paths["outreach"])
    pipeline_all = _read(paths["pipeline"])

    leads = [r for r in leads_all if not is_placeholder(r)]
    outreach = [r for r in outreach_all if not is_placeholder(r)]
    pipeline = [r for r in pipeline_all if not is_placeholder(r)]

    stale = []
    for lead in leads:
        status = (lead.get("Status") or "").strip().lower()
        if status in ("won", "closed", "rejected", "archived"):
            continue
        try:
            found = datetime.date.fromisoformat((lead.get("Date Found") or "").strip())
        except ValueError:
            continue
        if (today - found).days > stale_days and status in ("new", "", "researching"):
            stale.append(lead)

    return {
        "date": today.isoformat(),
        "leads_total": len(leads),
        "leads_by_status": _count_by(leads, "Status"),
        "outreach_total": len(outreach),
        "outreach_sent": sum(1 for r in outreach
                             if (r.get("Date Sent") or "").strip()),
        "replies": sum(1 for r in outreach
                       if (r.get("Reply Status") or "").strip().lower()
                       not in ("", "not sent", "no reply", "awaiting reply")),
        "pipeline_total": len(pipeline),
        "payments_confirmed": sum(1 for r in pipeline
                                  if (r.get("Payment Status") or "").strip().lower()
                                  in ("paid", "confirmed", "received")),
        "stale_leads": [l.get("Lead ID", "?") for l in stale],
        "placeholder_rows_excluded": (len(leads_all) - len(leads))
                                     + (len(outreach_all) - len(outreach))
                                     + (len(pipeline_all) - len(pipeline)),
    }


def pipeline_report_md(metrics):
    lines = ["# Pipeline Report", "", "Date: %s" % metrics["date"], "",
             "| Metric | Value |", "|--------|-------|",
             "| Leads (real) | %d |" % metrics["leads_total"],
             "| Outreach records | %d |" % metrics["outreach_total"],
             "| Outreach actually sent | %d |" % metrics["outreach_sent"],
             "| Replies | %d |" % metrics["replies"],
             "| Pipeline records | %d |" % metrics["pipeline_total"],
             "| Payments confirmed | %d |" % metrics["payments_confirmed"],
             "| Stale leads (%s) | %d |" % ("no touch, aging", len(metrics["stale_leads"])),
             "| Placeholder rows excluded | %d |" % metrics["placeholder_rows_excluded"],
             ""]
    if metrics["leads_by_status"]:
        lines += ["## Leads by Status", ""]
        for status, count in sorted(metrics["leads_by_status"].items()):
            lines.append("- %s: %d" % (status, count))
        lines.append("")
    if metrics["stale_leads"]:
        lines += ["## Stale Leads Needing a Decision", ""]
        for lead_id in metrics["stale_leads"]:
            lines.append("- %s — follow up or archive" % lead_id)
        lines.append("")
    lines.append("All numbers are counted from the trackers. Nothing is estimated.")
    return "\n".join(lines) + "\n"


def founder_briefing_md(metrics):
    total = metrics["leads_total"]
    if total == 0:
        headline = ("The pipeline currently holds no real leads — the trackers "
                    "contain only template rows. The single highest-value action "
                    "is logging the first real leads.")
    elif metrics["outreach_sent"] == 0:
        headline = ("%d real lead(s) are logged but no outreach has been sent yet. "
                    "The next action is approving and sending the first drafts."
                    % total)
    else:
        headline = ("%d lead(s), %d outreach sent, %d repl(ies), %d payment(s) "
                    "confirmed." % (total, metrics["outreach_sent"],
                                    metrics["replies"], metrics["payments_confirmed"]))
    lines = ["# Founder Briefing — Pipeline", "", "Date: %s" % metrics["date"], "",
             headline, "", "## Decisions Waiting", ""]
    if metrics["stale_leads"]:
        lines.append("- %d stale lead(s): follow up or archive (%s)"
                     % (len(metrics["stale_leads"]), ", ".join(metrics["stale_leads"])))
    else:
        lines.append("- No stale leads today.")
    lines += ["", "Prepared deterministically by the Reporting role from tracker data.", ""]
    return "\n".join(lines)


def write_reports(out_dir, paths=None, today=None):
    metrics = compute_metrics(paths, today)
    os.makedirs(out_dir, exist_ok=True)
    p1 = os.path.join(out_dir, "Pipeline_Report_%s.md" % metrics["date"])
    p2 = os.path.join(out_dir, "Founder_Briefing_%s.md" % metrics["date"])
    with open(p1, "w", encoding="utf-8") as f:
        f.write(pipeline_report_md(metrics))
    with open(p2, "w", encoding="utf-8") as f:
        f.write(founder_briefing_md(metrics))
    return {"metrics": metrics, "pipeline_report": p1, "founder_briefing": p2}
