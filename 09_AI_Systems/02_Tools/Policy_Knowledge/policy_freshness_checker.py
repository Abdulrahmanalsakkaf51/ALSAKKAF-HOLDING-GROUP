"""AOS Policy and Law Knowledge System - freshness checker (PRJ-014). Stdlib only.

Reports which knowledge items are overdue for re-verification.

This tool is OFFLINE by design. Checking official sources over the network
requires explicit Founder approval; this tool only reports what must be
re-verified and by whom. It never fetches anything.

Usage:
  py policy_freshness_checker.py
"""

import datetime
import sys

from policy_retriever import load_index, is_stale


def freshness_report(index=None, today=None):
    index = index or load_index()
    today = today or datetime.date.today()
    max_age = int(index.get("max_age_days", 180))
    rows = []
    for item in index.get("items", []):
        try:
            verified = datetime.date.fromisoformat(item["last_verified"])
            age = (today - verified).days
        except (KeyError, ValueError):
            age = None
        rows.append({
            "id": item["id"],
            "title": item["title"],
            "last_verified": item.get("last_verified", "(missing)"),
            "age_days": age,
            "stale": is_stale(item, index, today),
            "official_source_url": item.get("official_source_url", ""),
        })
    return {"snapshot_date": index.get("snapshot_date"),
            "max_age_days": max_age, "checked": len(rows),
            "stale": [r for r in rows if r["stale"]], "rows": rows}


def main():
    report = freshness_report()
    print("Policy knowledge freshness report")
    print("Snapshot date: %s | Max age: %d days | Items: %d"
          % (report["snapshot_date"], report["max_age_days"], report["checked"]))
    if not report["stale"]:
        print("All items are within the verification window.")
    else:
        print("STALE ITEMS — re-verify against the official source:")
        for r in report["stale"]:
            print("  %s — %s (last verified %s) → %s"
                  % (r["id"], r["title"], r["last_verified"],
                     r["official_source_url"]))
    print("\nNote: network verification requires Founder approval. This tool is "
          "offline and only reports what needs human re-verification.")
    return 0 if not report["stale"] else 2


if __name__ == "__main__":
    sys.exit(main())
