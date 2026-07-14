"""Atlas Capability Benchmark v1 - runner (PRJ-014). Stdlib only.

Runs the benchmark in DETERMINISTIC LOCAL mode and writes an honest report.

We do NOT report claims like "Atlas is 50% as good as ChatGPT."
We report: "Atlas Local completed X of N benchmark tasks within acceptance
criteria", plus the category breakdown and what requires AI or humans.

Other modes (LOCAL AI, HYBRID, CLOUD REFERENCE) require Founder-enabled
adapters and are not run by default.

Usage:
  py run_benchmark.py            Run and print summary
  py run_benchmark.py --write    Also write Benchmark_Report_v1.md
"""

import datetime
import sys
import time

from benchmark_runners import run_task
from benchmark_tasks import build_tasks


def run_all():
    tasks = build_tasks()
    results = []
    for task in tasks:
        start = time.perf_counter()
        try:
            outcome = run_task(task)
            error = None
        except Exception as exc:  # honest failure, not a crash of the harness
            outcome = False
            error = "%s: %s" % (type(exc).__name__, exc)
        elapsed_ms = (time.perf_counter() - start) * 1000
        results.append({"task": task, "outcome": outcome,
                        "elapsed_ms": elapsed_ms, "error": error})
    return results


def summarize_results(results):
    completed = sum(1 for r in results if r["outcome"] is True)
    failed = sum(1 for r in results if r["outcome"] is False)
    requires_ai = sum(1 for r in results if r["outcome"] is None)
    by_category = {}
    for r in results:
        cat = r["task"]["category"]
        row = by_category.setdefault(cat, {"total": 0, "completed": 0,
                                           "failed": 0, "requires_ai": 0})
        row["total"] += 1
        if r["outcome"] is True:
            row["completed"] += 1
        elif r["outcome"] is False:
            row["failed"] += 1
        else:
            row["requires_ai"] += 1
    total_ms = sum(r["elapsed_ms"] for r in results)
    return {"total": len(results), "completed": completed, "failed": failed,
            "requires_ai": requires_ai, "by_category": by_category,
            "total_ms": total_ms}


def report_md(results, summary):
    date = datetime.date.today().isoformat()
    lines = [
        "# ALSAKKAF HOLDING GROUP", "",
        "# Atlas Capability Benchmark v1 — Deterministic Local Results", "",
        "## Document Information", "",
        "| Field | Value |", "|-------|-------|",
        "| Document ID | ACB-REPORT-001 |",
        "| Document Type | Benchmark Report |",
        "| Status | Active |",
        "| Version | 1.0 |",
        "| Date | %s |" % date,
        "| Owner | Abdulrahman Alsakkaf |",
        "| Related Project | PRJ-014 |",
        "", "---", "",
        "# 1. Headline Result", "",
        "Atlas Local (deterministic tools, no AI model, no network) completed "
        "**%d of %d** benchmark tasks within acceptance criteria."
        % (summary["completed"], summary["total"]), "",
        "%d task(s) failed their acceptance criteria. %d task(s) honestly "
        "require an AI model (or an AI model plus a human) and are counted as "
        "not completed in this mode." % (summary["failed"],
                                         summary["requires_ai"]), "",
        "Total execution time: %.1f seconds. Cost: $0.00 (local, offline)."
        % (summary["total_ms"] / 1000.0), "",
        "This report makes no comparison claims against any AI product. "
        "It measures task completion against defined acceptance criteria only.",
        "", "---", "",
        "# 2. Results by Category", "",
        "| Category | Completed | Failed | Requires AI | Total |",
        "|----------|-----------|--------|-------------|-------|",
    ]
    for cat in sorted(summary["by_category"]):
        row = summary["by_category"][cat]
        lines.append("| %s | %d | %d | %d | %d |"
                     % (cat, row["completed"], row["failed"],
                        row["requires_ai"], row["total"]))
    failures = [r for r in results if r["outcome"] is False]
    lines += ["", "---", "", "# 3. Failed Tasks", ""]
    if failures:
        lines += ["| Task | Description | Error |", "|------|-------------|-------|"]
        for r in failures:
            lines.append("| %s | %s | %s |" % (
                r["task"]["id"], r["task"]["description"],
                (r["error"] or "acceptance criteria not met").replace("|", "/")))
    else:
        lines.append("No failed tasks in this run.")
    lines += ["", "---", "",
              "# 4. Modes Not Run", "",
              "LOCAL AI, HYBRID, and CLOUD REFERENCE modes require "
              "Founder-enabled model adapters (Partner Runtime) and were not "
              "run. Their columns will be added when the Founder approves a "
              "model configuration.", "",
              "# 5. Revision History", "",
              "| Version | Date | Changes |", "|---------|------|---------|",
              "| 1.0 | %s | First deterministic-local run |" % date, ""]
    return "\n".join(lines)


def main(argv):
    results = run_all()
    summary = summarize_results(results)
    print("Atlas Capability Benchmark v1 — DETERMINISTIC LOCAL mode")
    print("Completed %d / %d within acceptance criteria "
          "(%d failed, %d require AI). %.1fs total."
          % (summary["completed"], summary["total"], summary["failed"],
             summary["requires_ai"], summary["total_ms"] / 1000.0))
    for cat in sorted(summary["by_category"]):
        row = summary["by_category"][cat]
        print("  %-22s %d/%d completed (%d require AI)"
              % (cat, row["completed"], row["total"], row["requires_ai"]))
    if "--write" in argv:
        import os
        out = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "Benchmark_Report_v1.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(report_md(results, summary))
        print("Report written:", out)
    failures = [r for r in results if r["outcome"] is False]
    for r in failures:
        print("FAILED:", r["task"]["id"], r["task"]["description"], r["error"] or "")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
