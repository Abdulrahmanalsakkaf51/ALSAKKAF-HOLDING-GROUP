"""AOS Media Tools - PRJ-018 Media Operations integrity tests. Stdlib only.

Verifies the Media Operations package structure and the media briefing
tool: required documents exist, CSV headers match the spec, calendars use
only MEDIA-009 statuses, KPI trackers contain no fabricated numbers on
day one, and the briefing runs cleanly.

Usage (from repo root):
  py 09_AI_Systems\\02_Tools\\Media_Tools\\test_media_operations.py
"""

import csv
import os
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(BASE, "..", "..", ".."))
MEDIA_ROOT = os.path.join(ROOT, "01_Holding_Company", "04_Operations",
                          "12_Media_Operations")

sys.path.insert(0, BASE)
import media_briefing  # noqa: E402

CHANNEL_FOLDERS = ["01_ALSAKKAF_Systems", "02_Rihlat_Aql",
                   "03_Sand_Dunes_Stories"]
SHARED_DOCS = ["Media_Operations_Package.md", "Thumbnail_Style_Guide.md",
               "Video_Workflow_Operating_Process.md",
               "Content_Review_Checklist.md",
               "Atlas_YouTube_Reporting_Template.md"]
CHANNEL_DOCS = ["Channel_Identity.md",
                "Content_Plan_First_Videos_and_Shorts.md"]
CALENDAR_HEADER = ["Day", "Date", "Format", "Working_Title", "Pillar",
                   "Status", "Rights_Status", "Notes"]
KPI_HEADER = ["Snapshot_Date", "Subscribers_Total", "Views_Total",
              "Watch_Hours_Total", "Videos_Published_Total",
              "Shorts_Published_Total", "Top_Item_This_Period", "Notes"]

RESULTS = []


def check(label, passed, detail=""):
    RESULTS.append((label, bool(passed), detail))


def _header(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as handle:
        return next(csv.reader(handle), [])


def run_checks():
    for doc in SHARED_DOCS:
        check("shared doc exists: %s" % doc,
              os.path.isfile(os.path.join(MEDIA_ROOT, doc)))

    cfos = os.path.join(ROOT, "01_Holding_Company", "04_Operations",
                        "04_Content_Operations",
                        "Content_Factory_Operating_System.md")
    check("Content Factory Operating System exists", os.path.isfile(cfos))

    for folder in CHANNEL_FOLDERS:
        base = os.path.join(MEDIA_ROOT, folder)
        for doc in CHANNEL_DOCS:
            check("%s/%s exists" % (folder, doc),
                  os.path.isfile(os.path.join(base, doc)))

        cal_path = os.path.join(base, "Publishing_Calendar_30_Day.csv")
        kpi_path = os.path.join(base, "KPI_Tracker.csv")
        check("%s calendar exists" % folder, os.path.isfile(cal_path))
        check("%s KPI tracker exists" % folder, os.path.isfile(kpi_path))
        if not (os.path.isfile(cal_path) and os.path.isfile(kpi_path)):
            continue

        check("%s calendar header matches spec" % folder,
              _header(cal_path) == CALENDAR_HEADER,
              "got %s" % _header(cal_path))
        check("%s KPI header matches spec" % folder,
              _header(kpi_path) == KPI_HEADER, "got %s" % _header(kpi_path))

        with open(cal_path, "r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        check("%s calendar has at least 20 planned items" % folder,
              len(rows) >= 20, "got %d" % len(rows))
        bad_status = [r["Working_Title"] for r in rows
                      if r.get("Status") not in media_briefing.CALENDAR_STATUSES]
        check("%s calendar uses only MEDIA-009 statuses" % folder,
              not bad_status, ", ".join(bad_status))
        longs = sum(1 for r in rows if r.get("Format") == "Long")
        shorts = sum(1 for r in rows if r.get("Format") == "Short")
        check("%s calendar has at least 10 long + 10 Shorts" % folder,
              longs >= 10 and shorts >= 10,
              "got %d long, %d short" % (longs, shorts))

        snap = media_briefing.latest_snapshot(folder)
        summary = media_briefing.calendar_summary(folder)
        published = summary["counts"]["Published"] if summary else -1
        check("%s KPI tracker honest (no snapshots while nothing published)"
              % folder, not (snap is not None and published == 0),
              "snapshot exists but 0 items are Published")

    briefing = media_briefing.build_briefing()
    check("briefing generates without error", bool(briefing))
    check("briefing covers all three channels",
          all(name in briefing for name, _ in media_briefing.CHANNELS))
    check("briefing reports honest zero-data state",
          "no measured data yet" in briefing or "snapshot" in briefing)


def main():
    run_checks()
    failed = [r for r in RESULTS if not r[1]]
    for label, passed, detail in RESULTS:
        mark = "PASS" if passed else "FAIL"
        line = "[%s] %s" % (mark, label)
        if detail and not passed:
            line += " -- " + detail
        print(line)
    print()
    print("Checks: %d  Passed: %d  Failed: %d" % (
        len(RESULTS), len(RESULTS) - len(failed), len(failed)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
