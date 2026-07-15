"""AOS Pod Tools - Atlas daily revenue briefing (PRJ-016). Stdlib only.

Produces the daily revenue briefing from tracker data ONLY. Every count is
computed; zero stays zero; nothing is estimated or invented. Placeholder
and example rows are excluded everywhere.

Usage (from repo root):
  py 09_AI_Systems\\02_Tools\\Pod_Tools\\daily_revenue_briefing.py
  py 09_AI_Systems\\02_Tools\\Pod_Tools\\daily_revenue_briefing.py --write
"""

import csv
import datetime
import os
import re
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))

# Real operational data lives in PRIVATE storage outside the repository
# (PODS-001). The public repo holds template trackers only, so without the
# private store this briefing honestly reports zeros.
PRIVATE_ROOT = os.environ.get(
    "AOS_PRIVATE_OPS_ROOT",
    os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop",
                 "ALSAKKAF PRIVATE OPERATIONS", "01_Revenue_Operations",
                 "PRJ-016"))

_PRIVATE_PATHS = {
    "leads": os.path.join(PRIVATE_ROOT, "01_Verified_Leads", "Lead_Tracker.csv"),
    "outreach": os.path.join(PRIVATE_ROOT, "04_Outreach_Tracker", "Outreach_Tracker.csv"),
    "pipeline": os.path.join(PRIVATE_ROOT, "05_Client_Pipeline", "Client_Pipeline.csv"),
    "rejected_log": os.path.join(PRIVATE_ROOT, "02_Rejected_Leads",
                                 "Rejected_Prospects.md"),
}
_PUBLIC_PATHS = {
    "leads": os.path.join(ROOT, "01_Holding_Company", "04_Operations",
                          "03_Revenue_Operations", "Lead_Tracker.csv"),
    "outreach": os.path.join(ROOT, "01_Holding_Company", "04_Operations",
                             "03_Revenue_Operations", "Outreach_Tracker.csv"),
    "pipeline": os.path.join(ROOT, "01_Holding_Company", "04_Operations",
                             "03_Revenue_Operations", "Client_Pipeline.csv"),
    "rejected_log": "",
}

# Use each private file when it exists, else fall back to the public template.
PATHS = {key: (_PRIVATE_PATHS[key] if os.path.isfile(_PRIVATE_PATHS[key])
               else _PUBLIC_PATHS[key])
         for key in _PUBLIC_PATHS}

PLACEHOLDER_MARKERS = ("example only", "sample row", "not real", "not a real",
                       "template row", "illustrates column usage")
POSITIVE_MARKERS = ("interested", "positive", "yes", "call booked", "meeting")
REPLIED_BLANKS = ("", "not sent", "no reply", "awaiting reply", "awaiting")


def _is_placeholder(row):
    blob = " ".join(str(v) for v in row.values()).lower()
    return any(m in blob for m in PLACEHOLDER_MARKERS) or \
        str(row.get(list(row)[0], "")).startswith("EXAMPLE")


def _read(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if not _is_placeholder(r)]


def _count_rejected_from_log(path):
    """Count data rows of the rejection table in PAW-002 (if present)."""
    if not os.path.isfile(path):
        return 0
    text = open(path, encoding="utf-8").read()
    section = text.split("# 1. Rejections", 1)
    if len(section) < 2:
        return 0
    section = re.split(r"^# 2\.", section[1], maxsplit=1, flags=re.M)[0]
    rows = re.findall(r"^\| (?!Candidate|[-: ]+\|)[^|]+\|", section, re.M)
    return len(rows)


def compute_briefing(paths=None, today=None):
    paths = paths or PATHS
    today = today or datetime.date.today()
    leads = _read(paths["leads"])
    outreach = _read(paths["outreach"])
    pipeline = _read(paths["pipeline"])

    sent = [r for r in outreach if (r.get("Date Sent") or "").strip()]
    approved_unsent = [r for r in outreach
                       if (r.get("CEO Approved") or "").strip().lower() == "yes"
                       and not (r.get("Date Sent") or "").strip()]
    drafts_ready = [r for r in outreach
                    if (r.get("CEO Approved") or "").strip().lower() != "yes"
                    and not (r.get("Date Sent") or "").strip()]
    replies = [r for r in outreach
               if (r.get("Reply Status") or "").strip().lower() not in REPLIED_BLANKS]
    positive = [r for r in replies
                if any(m in (r.get("Reply Status") or "").lower()
                       for m in POSITIVE_MARKERS)]

    follow_ups_due = []
    for r in outreach:
        due = (r.get("Follow Up Date") or "").strip()
        try:
            if due and datetime.date.fromisoformat(due) <= today and r not in replies:
                follow_ups_due.append(r)
        except ValueError:
            continue

    proposals = [r for r in pipeline
                 if (r.get("Quoted Price USD") or "").strip()
                 or (r.get("Payment Link Sent") or "").strip().lower() == "yes"]
    paid = [r for r in pipeline
            if (r.get("Payment Status") or "").strip().lower()
            in ("paid", "confirmed", "received")]
    revenue = 0.0
    for r in paid:
        try:
            revenue += float(r.get("Quoted Price USD") or 0)
        except ValueError:
            pass

    rejected = _count_rejected_from_log(paths.get("rejected_log", ""))

    briefing = {
        "date": today.isoformat(),
        "prospects_researched": len(leads) + rejected,
        "prospects_accepted": len(leads),
        "prospects_rejected": rejected,
        "drafts_ready": len(drafts_ready),
        "messages_approved": len(approved_unsent),
        "messages_sent": len(sent),
        "replies": len(replies),
        "positive_replies": len(positive),
        "discovery_calls": 0,  # not yet tracked in any tracker; stays 0 until a tracker field exists
        "proposals": len(proposals),
        "paid_clients": len(paid),
        "revenue_usd": revenue,
        "follow_ups_due": len(follow_ups_due),
    }
    briefing["blockers"] = _blockers(briefing)
    briefing["founder_decisions"] = _decisions(briefing)
    briefing["next_action"] = _next_action(briefing)
    return briefing


def _blockers(b):
    blockers = []
    if b["drafts_ready"] and not b["messages_sent"]:
        blockers.append("%d outreach draft(s) blocked on Founder approval and "
                        "pre-send checks" % b["drafts_ready"])
    if b["prospects_accepted"] == 0:
        blockers.append("No verified prospects in the tracker")
    return blockers or ["None recorded"]


def _open_adrs():
    adr_dir = os.path.join(ROOT, "01_Holding_Company", "01_Governance", "ADR")
    open_ids = []
    for adr_id in ("024", "025", "026", "027"):
        for name in os.listdir(adr_dir) if os.path.isdir(adr_dir) else []:
            if name.startswith("ADR-%s_" % adr_id):
                text = open(os.path.join(adr_dir, name), encoding="utf-8").read()
                match = re.search(r"\|\s*Founder decision\s*\|\s*([A-Z]+)\s*\|", text)
                if match and match.group(1) != "APPROVED":
                    open_ids.append("ADR-%s" % adr_id)
                break
    return open_ids


def _decisions(b):
    decisions = []
    if b["drafts_ready"]:
        decisions.append("Approve or edit %d outreach draft(s) (PAW-003)"
                         % b["drafts_ready"])
    open_adrs = _open_adrs()
    if open_adrs:
        decisions.append("Partner activation decisions still open: %s"
                         % ", ".join(open_adrs))
    return decisions


def _next_action(b):
    if b["drafts_ready"] > 0 and b["messages_sent"] == 0:
        return ("Review PAW-003, complete the pre-send checks, and manually send "
                "the first approved message from abdulrahman@alsakkafsystems.com")
    if b["messages_approved"] > 0:
        return "Manually send the approved message(s) and set follow-up dates"
    if b["follow_ups_due"] > 0:
        return "Send %d due follow-up(s) after review" % b["follow_ups_due"]
    if b["prospects_accepted"] == 0:
        return "Verify the first prospects into the lead tracker"
    return "Continue verification of second outreach batch prospects"


def briefing_md(b):
    lines = ["# Atlas Daily Revenue Briefing", "", "Date: %s" % b["date"], "",
             "All counts are computed from tracker data. Zero means zero.", "",
             "| Metric | Count |", "|--------|-------|"]
    for label, key in [
            ("Prospects researched", "prospects_researched"),
            ("Prospects accepted (verified)", "prospects_accepted"),
            ("Prospects rejected", "prospects_rejected"),
            ("Outreach drafts ready (NOT SENT)", "drafts_ready"),
            ("Messages approved, awaiting manual send", "messages_approved"),
            ("Messages sent", "messages_sent"),
            ("Replies", "replies"),
            ("Positive replies", "positive_replies"),
            ("Discovery calls", "discovery_calls"),
            ("Proposals", "proposals"),
            ("Paid clients", "paid_clients"),
            ("Revenue (USD)", "revenue_usd"),
            ("Follow-ups due", "follow_ups_due")]:
        lines.append("| %s | %s |" % (label, b[key]))
    lines += ["", "## Blockers", ""]
    lines += ["- %s" % x for x in b["blockers"]]
    lines += ["", "## Founder Decisions Required", ""]
    lines += ["- %s" % x for x in b["founder_decisions"]]
    lines += ["", "## Highest-Value Next Action", "", b["next_action"], ""]
    return "\n".join(lines)


def main(argv):
    b = compute_briefing()
    print(briefing_md(b))
    if "--write" in argv:
        # Founder briefings contain operational detail — written to private
        # storage when it exists (PODS-001), else to gitignored Atlas_Output.
        if os.path.isdir(PRIVATE_ROOT):
            out_dir = os.path.join(PRIVATE_ROOT, "06_Founder_Briefings")
        else:
            out_dir = os.path.join(ROOT, "01_Holding_Company", "08_Reports",
                                   "Atlas_Output", "Revenue_Reports")
        os.makedirs(out_dir, exist_ok=True)
        path = os.path.join(out_dir, "Daily_Revenue_Briefing_%s.md" % b["date"])
        with open(path, "w", encoding="utf-8") as f:
            f.write(briefing_md(b))
        print("\nWritten:", path)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
