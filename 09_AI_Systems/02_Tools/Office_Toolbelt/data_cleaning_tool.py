"""AOS Office Toolbelt - data cleaning tool (PRJ-013). Standard library only.

Cleans tabular data (CSV or list-of-dicts):
  * trims whitespace, collapses inner spaces
  * normalizes empty markers ("-", "n/a", "null") to ""
  * removes exact duplicate rows (reported, original order kept)
  * validates required columns and flags rows with missing values
"""

import csv
import io

EMPTY_MARKERS = {"-", "n/a", "na", "none", "null", "nil", "?"}


def _clean_value(value):
    text = " ".join(str(value or "").split())
    if text.lower() in EMPTY_MARKERS:
        return ""
    return text


def clean_rows(rows):
    """rows: list of dicts. Returns (cleaned_rows, report)."""
    cleaned = []
    seen = set()
    duplicates = 0
    for row in rows:
        crow = {k: _clean_value(v) for k, v in row.items()}
        key = tuple(sorted(crow.items()))
        if key in seen:
            duplicates += 1
            continue
        seen.add(key)
        cleaned.append(crow)
    return cleaned, {"input_rows": len(rows), "output_rows": len(cleaned),
                     "duplicates_removed": duplicates}


def validate_required(rows, required_columns):
    """Flag rows missing required values. Returns list of problem dicts."""
    problems = []
    for i, row in enumerate(rows, start=2):  # +1 for header line in CSV terms
        for col in required_columns:
            if not _clean_value(row.get(col, "")):
                problems.append({"row": i, "column": col, "issue": "missing value"})
    return problems


def clean_csv_file(in_path, out_path, required_columns=None):
    with open(in_path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    cleaned, report = clean_rows(rows)
    problems = validate_required(cleaned, required_columns or [])
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(cleaned)
    report["problems"] = problems
    return report


def clean_csv_text(csv_text, required_columns=None):
    reader = csv.DictReader(io.StringIO(csv_text))
    rows = list(reader)
    cleaned, report = clean_rows(rows)
    report["problems"] = validate_required(cleaned, required_columns or [])
    return cleaned, report
