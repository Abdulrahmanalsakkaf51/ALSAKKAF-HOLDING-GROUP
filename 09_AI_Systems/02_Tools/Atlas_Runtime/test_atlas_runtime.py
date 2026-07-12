#!/usr/bin/env python3
"""
Atlas Runtime v1 - automated test suite.

Python standard library only. No network access.

Run: py test_atlas_runtime.py
"""

import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
ATLAS_PY = SCRIPT_DIR / "atlas.py"
CONFIG = SCRIPT_DIR / "atlas_config.json"

PASS = "PASS"
FAIL = "FAIL"

results = []


def check(name, condition, detail=""):
    status = PASS if condition else FAIL
    results.append((name, status, detail))
    print(f"[{status}] {name}" + (f" - {detail}" if detail and status == FAIL else ""))
    return condition


def run_atlas(*args):
    proc = subprocess.run(
        [sys.executable if False else "py", str(ATLAS_PY), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    return proc


def main():
    print("Atlas Runtime - Test Suite")
    print("=" * 60)

    check("atlas.py exists", ATLAS_PY.exists(), str(ATLAS_PY))
    check("atlas_config.json exists", CONFIG.exists(), str(CONFIG))

    required_trackers = [
        "01_Holding_Company/04_Operations/03_Revenue_Operations/Lead_Tracker.csv",
        "01_Holding_Company/04_Operations/03_Revenue_Operations/Outreach_Tracker.csv",
        "01_Holding_Company/04_Operations/03_Revenue_Operations/Client_Pipeline.csv",
        "01_Holding_Company/04_Operations/04_Content_Operations/Content_Calendar.csv",
        "01_Holding_Company/04_Operations/04_Content_Operations/Content_Analytics_Tracker.csv",
    ]
    for rel in required_trackers:
        check(f"tracker exists: {rel}", (REPO_ROOT / rel).exists())

    dashboard_files = [
        "docs/atlas-dashboard.html",
        "docs/atlas-dashboard.css",
        "docs/atlas-dashboard-data.js",
        "docs/index.html",
    ]
    for rel in dashboard_files:
        check(f"docs file exists: {rel}", (REPO_ROOT / rel).exists())

    if ATLAS_PY.exists():
        proc = run_atlas("health-check")
        check("health-check command runs (exit 0 or 1, no crash)", proc.returncode in (0, 1),
              f"exit={proc.returncode} stderr={proc.stderr[:200]}")
        check("health-check prints a result line", "HEALTH CHECK RESULT" in proc.stdout)

        proc = run_atlas("dashboard")
        check("dashboard command runs", proc.returncode == 0, proc.stderr[:200])

        proc = run_atlas("brief")
        check("brief command runs", proc.returncode == 0, proc.stderr[:200])
        brief_path = REPO_ROOT / "01_Holding_Company/08_Reports/Atlas_Output"
        briefs = list(brief_path.glob("Daily_Briefing_*.md")) if brief_path.exists() else []
        check("brief command produces a Daily_Briefing file", len(briefs) > 0)

        proc = run_atlas("payment-report")
        check("payment-report command runs", proc.returncode == 0, proc.stderr[:200])
        pr_path = REPO_ROOT / "01_Holding_Company/08_Reports/Atlas_Output/Revenue_Reports"
        reports = list(pr_path.glob("Payment_Report_*.md")) if pr_path.exists() else []
        check("payment-report command produces a report file", len(reports) > 0)
    else:
        check("health-check command runs", False, "atlas.py missing")
        check("dashboard command runs", False, "atlas.py missing")
        check("brief command runs", False, "atlas.py missing")
        check("payment-report command runs", False, "atlas.py missing")

    credential_pattern = re.compile(
        r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey|client[_-]?secret|"
        r"private[_-]?key|access[_-]?token|refresh[_-]?token|recovery[_-]?code|"
        r"2fa[_-]?code|bank[_-]?account|card[_-]?number)\b\s*[:=]\s*[^\s,\"']{4,}"
    )
    scan_targets = [SCRIPT_DIR] + [REPO_ROOT / "docs"]
    scan_exts = {".py", ".json", ".ps1", ".bat", ".md", ".js", ".html", ".css"}
    credential_hits = []
    for target in scan_targets:
        if not target.exists():
            continue
        for path in target.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in scan_exts:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for line in text.splitlines():
                if credential_pattern.search(line):
                    credential_hits.append(str(path.relative_to(REPO_ROOT)))
    check("no obvious credential strings in Atlas Runtime / docs files", len(credential_hits) == 0,
          f"{len(credential_hits)} hit(s): {credential_hits[:5]}")

    print("=" * 60)
    total = len(results)
    passed = len([r for r in results if r[1] == PASS])
    failed = total - passed
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    if failed == 0:
        print("OVERALL: PASS")
        return 0
    else:
        print("OVERALL: FAIL")
        for name, status, detail in results:
            if status == FAIL:
                print(f"  - {name}: {detail}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
