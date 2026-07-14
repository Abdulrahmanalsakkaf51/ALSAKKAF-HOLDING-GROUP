"""AOS Policy and Law Knowledge System - retriever (PRJ-014). Stdlib only.

Retrieves approved policy/legal knowledge items with full source metadata.
It never makes legal decisions and flags LEGAL / HR REVIEW REQUIRED for
sensitive categories. Offline mode always shows the SOURCE SNAPSHOT DATE
and warns when items may be stale.

Usage:
  py policy_retriever.py "annual leave"
  py policy_retriever.py --category probation
"""

import datetime
import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INDEX_PATH = os.path.join(BASE_DIR, "policy_index.json")

REVIEW_REQUIRED_CATEGORIES = ("termination process", "manager escalation")
REVIEW_REQUIRED_MARKERS = ("terminat", "dismiss", "discipline", "dispute",
                           "lawsuit", "salary decision", "medical")


def load_index(path=INDEX_PATH):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def is_stale(item, index, today=None):
    today = today or datetime.date.today()
    try:
        verified = datetime.date.fromisoformat(item["last_verified"])
    except (KeyError, ValueError):
        return True
    return (today - verified).days > int(index.get("max_age_days", 180))


def needs_legal_review(query, item):
    if item.get("category") in REVIEW_REQUIRED_CATEGORIES:
        return True
    low = (query or "").lower()
    return any(m in low for m in REVIEW_REQUIRED_MARKERS)


def search(query=None, category=None, index=None, today=None):
    """Return matching items with metadata, staleness, and review flags."""
    index = index or load_index()
    today = today or datetime.date.today()
    results = []
    q = (query or "").lower()
    for item in index.get("items", []):
        hit = False
        if category and item.get("category", "").lower() == category.lower():
            hit = True
        elif q:
            blob = " ".join([item.get("category", ""), item.get("title", ""),
                             item.get("summary", "")]).lower()
            hit = all(word in blob for word in q.split())
        if not hit:
            continue
        results.append({
            "item": item,
            "stale": is_stale(item, index, today),
            "legal_review_required": needs_legal_review(query, item),
            "snapshot_date": index.get("snapshot_date"),
        })
    return results


def format_result(result):
    item = result["item"]
    lines = ["%s — %s" % (item["id"], item["title"]),
             "  Category: %s | Jurisdiction: %s | Sector: %s"
             % (item["category"], item["jurisdiction"], item["sector"]),
             "  Summary: %s" % item["summary"],
             "  Source: %s" % item["source"],
             "  Official source URL: %s" % item["official_source_url"],
             "  Effective: %s | Last verified: %s | Version: %s"
             % (item["effective_date"], item["last_verified"],
                item["document_version"]),
             "  Approval status: %s" % item["approval_status"],
             "  SOURCE SNAPSHOT DATE: %s (offline copy)" % result["snapshot_date"]]
    if result["stale"]:
        lines.append("  WARNING: this item may be STALE — re-verify against the "
                     "official source before relying on it.")
    if result["legal_review_required"]:
        lines.append("  FLAG: LEGAL / HR REVIEW REQUIRED — this topic requires a "
                     "human decision; this system does not make legal decisions.")
    return "\n".join(lines)


def main(argv):
    if len(argv) >= 3 and argv[1] == "--category":
        results = search(category=argv[2])
        label = "category '%s'" % argv[2]
    else:
        query = " ".join(argv[1:]) or "annual leave"
        results = search(query=query)
        label = "query '%s'" % query
    if not results:
        print("No approved knowledge found for %s." % label)
        print("Do not guess. Consult the official source or escalate to HR/legal.")
        return 1
    print("Results for %s (offline retrieval, demo pack):\n" % label)
    for r in results:
        print(format_result(r))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
