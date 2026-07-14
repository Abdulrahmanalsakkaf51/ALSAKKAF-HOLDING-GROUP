"""AOS Office Toolbelt - tracker tool (PRJ-013). Standard library only.

Builds and maintains business trackers as real XLSX workbooks
(via spreadsheet_tool) with CSV mirrors for easy diffing.

Includes the monthly activity tracker used by Office Partner TEST 1.
"""

import calendar
import csv
import datetime
import os

import spreadsheet_tool

MONTHLY_TRACKER_HEADERS = [
    "Date", "Day", "Activity", "Category", "Owner", "Status", "Notes"
]

TRACKER_STATUSES = ("Planned", "In Progress", "Done", "Blocked", "Cancelled")


def month_skeleton(year, month, owner="Office"):
    """One row per working day (Mon-Fri) of the month."""
    rows = []
    days_in_month = calendar.monthrange(year, month)[1]
    for day in range(1, days_in_month + 1):
        date = datetime.date(year, month, day)
        if date.weekday() >= 5:
            continue
        rows.append([date.isoformat(), date.strftime("%A"), "", "", owner, "Planned", ""])
    return rows


def create_monthly_tracker(out_dir, year, month, owner="Office", entries=None):
    """Create Monthly_Tracker_YYYY-MM.xlsx (+ .csv mirror). Returns paths."""
    os.makedirs(out_dir, exist_ok=True)
    rows = month_skeleton(year, month, owner=owner)
    for entry in entries or []:
        # entry: {"date": "YYYY-MM-DD", "activity": ..., "category": ..., "status": ..., "notes": ...}
        for row in rows:
            if row[0] == entry.get("date"):
                row[2] = entry.get("activity", "")
                row[3] = entry.get("category", "")
                row[5] = entry.get("status", "Planned")
                row[6] = entry.get("notes", "")
                break
    stem = "Monthly_Tracker_%04d-%02d" % (year, month)
    xlsx_path = os.path.join(out_dir, stem + ".xlsx")
    summary_rows = [[s, sum(1 for r in rows if r[5] == s)] for s in TRACKER_STATUSES]
    spreadsheet_tool.create_workbook(xlsx_path, [
        {"name": "Tracker", "headers": MONTHLY_TRACKER_HEADERS, "rows": rows},
        {"name": "Summary", "headers": ["Status", "Count"], "rows": summary_rows},
    ])
    csv_path = os.path.join(out_dir, stem + ".csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(MONTHLY_TRACKER_HEADERS)
        writer.writerows(rows)
    return {"xlsx": xlsx_path, "csv": csv_path, "rows": len(rows)}


def tracker_summary(xlsx_path):
    """Read a tracker workbook back and count statuses honestly."""
    rows = spreadsheet_tool.read_workbook(xlsx_path)
    if not rows:
        return {}
    headers = rows[0]
    try:
        status_idx = headers.index("Status")
    except ValueError:
        return {}
    counts = {}
    for row in rows[1:]:
        status = row[status_idx] if status_idx < len(row) else ""
        counts[status or "(blank)"] = counts.get(status or "(blank)", 0) + 1
    return counts


def find_stale(xlsx_path, date_col="Date", status_col="Status",
               open_statuses=("Planned", "In Progress"), today=None, days=7):
    """Rows still open whose date is more than `days` old."""
    today = today or datetime.date.today()
    rows = spreadsheet_tool.read_workbook(xlsx_path)
    if not rows:
        return []
    headers = rows[0]
    try:
        d_idx, s_idx = headers.index(date_col), headers.index(status_col)
    except ValueError:
        return []
    stale = []
    for row in rows[1:]:
        try:
            date = datetime.date.fromisoformat(str(row[d_idx]))
        except (ValueError, IndexError):
            continue
        status = row[s_idx] if s_idx < len(row) else ""
        if status in open_statuses and (today - date).days > days:
            stale.append(row)
    return stale
