"""AOS Media Tools - Atlas media operations briefing (PRJ-018). Stdlib only.

Summarizes the three YouTube channels from their publishing calendars and
KPI trackers ONLY. Every count is computed; zero stays zero; nothing is
estimated or invented. If a KPI tracker has no snapshot rows, the channel
is reported as "no measured data yet".

Usage (from repo root):
  py 09_AI_Systems\\02_Tools\\Media_Tools\\media_briefing.py
"""

import csv
import datetime
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))

MEDIA_ROOT = os.path.join(ROOT, "01_Holding_Company", "04_Operations",
                          "12_Media_Operations")

CHANNELS = [
    ("ALSAKKAF Systems", "01_ALSAKKAF_Systems"),
    ("Rihlat Aql (Journey of a Mind)", "02_Rihlat_Aql"),
    ("Sand Dunes Stories", "03_Sand_Dunes_Stories"),
]

CALENDAR_STATUSES = ("Idea", "Drafted", "Recorded", "Edited", "Approved",
                     "Published", "Reported")
STALE_DAYS = 14


def _read_csv(path):
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def calendar_summary(folder):
    """Count calendar items by status and format. Honest counts only."""
    rows = _read_csv(os.path.join(MEDIA_ROOT, folder,
                                  "Publishing_Calendar_30_Day.csv"))
    if rows is None:
        return None
    counts = {status: 0 for status in CALENDAR_STATUSES}
    formats = {"Long": 0, "Short": 0}
    unknown = 0
    for row in rows:
        status = (row.get("Status") or "").strip()
        if status in counts:
            counts[status] += 1
        elif status:
            unknown += 1
        fmt = (row.get("Format") or "").strip()
        if fmt in formats:
            formats[fmt] += 1
    return {"total": len(rows), "counts": counts, "formats": formats,
            "unknown_status": unknown}


def latest_snapshot(folder):
    """Latest KPI snapshot row, or None when nothing has been measured."""
    rows = _read_csv(os.path.join(MEDIA_ROOT, folder, "KPI_Tracker.csv"))
    if not rows:
        return None
    dated = [r for r in rows if (r.get("Snapshot_Date") or "").strip()]
    if not dated:
        return None
    dated.sort(key=lambda r: r["Snapshot_Date"].strip())
    return dated[-1]


def _snapshot_age_days(snapshot):
    try:
        taken = datetime.datetime.strptime(
            snapshot["Snapshot_Date"].strip(), "%Y-%m-%d").date()
    except (KeyError, ValueError):
        return None
    return (datetime.date.today() - taken).days


def build_briefing():
    today = datetime.date.today().isoformat()
    lines = ["ATLAS MEDIA OPERATIONS BRIEFING - %s" % today,
             "(computed from calendars and KPI trackers; zero stays zero)",
             ""]
    for name, folder in CHANNELS:
        lines.append("CHANNEL: %s" % name)
        cal = calendar_summary(folder)
        if cal is None:
            lines.append("  Calendar: MISSING - expected Publishing_Calendar_30_Day.csv")
        else:
            counts = cal["counts"]
            lines.append("  Planned items: %d (%d long-form, %d Shorts)" % (
                cal["total"], cal["formats"]["Long"], cal["formats"]["Short"]))
            lines.append("  Progress: Idea %d | Drafted %d | Approved %d | "
                         "Published %d" % (counts["Idea"], counts["Drafted"],
                                           counts["Approved"],
                                           counts["Published"]))
            if cal["unknown_status"]:
                lines.append("  WARNING: %d rows carry a status outside the "
                             "MEDIA-009 status list" % cal["unknown_status"])
        snap = latest_snapshot(folder)
        if snap is None:
            lines.append("  Audience: no measured data yet")
        else:
            lines.append("  Audience (snapshot %s): subscribers %s, views %s" % (
                snap.get("Snapshot_Date", "?").strip(),
                (snap.get("Subscribers_Total") or "not recorded").strip(),
                (snap.get("Views_Total") or "not recorded").strip()))
            age = _snapshot_age_days(snap)
            if age is not None and age > STALE_DAYS:
                lines.append("  STALE: latest snapshot is %d days old" % age)
        lines.append("")
    lines.append("Reporting format: MEDIA-011 Atlas_YouTube_Reporting_Template.md")
    return "\n".join(lines)


def main():
    if not os.path.isdir(MEDIA_ROOT):
        print("ERROR: media operations folder not found: %s" % MEDIA_ROOT)
        return 1
    print(build_briefing())
    return 0


if __name__ == "__main__":
    sys.exit(main())
