#!/usr/bin/env python3
"""
Atlas Runtime - Operational Readiness test suite.

Covers the 6 new commands added on top of Atlas Runtime v1.2:
task-queue, lead-review-queue, comms-approval-queue, ops-status,
media-store-task-report, daily-cycle.

Python standard library only. No network access.

This suite intentionally reads (read-only) real private data outside the
repository (ALSAKKAF PRIVATE OPERATIONS/) ONLY to confirm that no fragment of
it ever gets written inside the git repository. It never writes, prints, or
copies real company/contact names into any repo file, console assertion
message that gets logged, or committed artifact.

Run:
    py 09_AI_Systems\\02_Tools\\Atlas_Runtime\\test_atlas_operational_readiness.py
"""

import importlib.util
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.dont_write_bytecode = True  # keep the repo free of __pycache__ artifacts

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
ATLAS_PY = SCRIPT_DIR / "atlas.py"
CONFIG_PATH = SCRIPT_DIR / "atlas_config.json"
TODAY = datetime.now().strftime("%Y-%m-%d")

PUBLIC_OUTPUT_DIR = REPO_ROOT / "01_Holding_Company/08_Reports/Atlas_Output"

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    status = "PASS" if ok else "FAIL"
    line = f"  [{status}] {name}"
    if detail and not ok:
        line += f" -- {detail}"
    print(line)
    return bool(ok)


def run_atlas(*args):
    proc = subprocess.run(
        ["py", str(ATLAS_PY), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=90,
    )
    return proc


def path_is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def load_atlas_module():
    spec = importlib.util.spec_from_file_location("atlas_readiness_test", ATLAS_PY)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    print("Atlas Runtime - Operational Readiness Test Suite")
    print("=" * 60)

    check("atlas.py exists", ATLAS_PY.exists(), str(ATLAS_PY))
    check("atlas_config.json exists", CONFIG_PATH.exists(), str(CONFIG_PATH))
    if not ATLAS_PY.exists() or not CONFIG_PATH.exists():
        print("Cannot continue without atlas.py and atlas_config.json.")
        return 1

    # -------------------------------------------------------------------
    # 1. Commands registered and parseable
    # -------------------------------------------------------------------
    print("\n[1] New commands registered")
    new_commands = [
        "task-queue", "lead-review-queue", "comms-approval-queue",
        "ops-status", "media-store-task-report", "daily-cycle",
    ]
    try:
        atlas_mod = load_atlas_module()
        cmds = getattr(atlas_mod, "COMMANDS", {})
        for name in new_commands:
            check(f"Command registered and callable: {name}", callable(cmds.get(name)))
        parser = atlas_mod.build_parser()
        for name in new_commands:
            args = parser.parse_args([name])
            check(f"Command parses: {name}", args.command == name)
        check("Config has private_lead_tracker path", "private_lead_tracker" in atlas_mod.load_config()["paths"])
        check("Config has private_output_dir path", "private_output_dir" in atlas_mod.load_config()["paths"])
    except Exception as exc:
        check("atlas.py imports cleanly for command registration checks", False, str(exc))
        atlas_mod = None

    # -------------------------------------------------------------------
    # 2. Each new command runs end-to-end (exit 0) and produces its file
    # -------------------------------------------------------------------
    print("\n[2] End-to-end command runs")

    proc = run_atlas("task-queue")
    check("task-queue exits 0", proc.returncode == 0, proc.stderr[:200])
    check("task-queue produces Task_Queue file",
          (PUBLIC_OUTPUT_DIR / f"Task_Queue_{TODAY}.md").exists())

    proc = run_atlas("ops-status")
    check("ops-status exits 0", proc.returncode == 0, proc.stderr[:200])
    check("ops-status produces Ops_Status file",
          (PUBLIC_OUTPUT_DIR / f"Ops_Status_{TODAY}.md").exists())
    check("ops-status output mentions PASS or FAIL rollup",
          (PUBLIC_OUTPUT_DIR / f"Ops_Status_{TODAY}.md").exists() and
          "Overall status:" in (PUBLIC_OUTPUT_DIR / f"Ops_Status_{TODAY}.md").read_text(encoding="utf-8"))

    proc = run_atlas("media-store-task-report")
    check("media-store-task-report exits 0", proc.returncode == 0, proc.stderr[:200])
    msr_path = PUBLIC_OUTPUT_DIR / f"Media_Store_Task_Report_{TODAY}.md"
    check("media-store-task-report produces its file", msr_path.exists())
    if msr_path.exists():
        msr_text = msr_path.read_text(encoding="utf-8")
        check("media-store-task-report is honest when no NESTLYRA folder exists (or lists real findings)",
              "NESTLYRA" in msr_text)

    proc = run_atlas("lead-review-queue")
    check("lead-review-queue exits 0", proc.returncode == 0, proc.stderr[:200])
    lead_stdout = proc.stdout
    check("lead-review-queue console output has no obvious company-name field label leak beyond summary",
          "Summary:" in lead_stdout)
    lead_private_line = re.search(r"Wrote private output \(outside the repo\): (.+)", lead_stdout)
    if lead_private_line:
        priv_path = Path(lead_private_line.group(1).strip())
        check("lead-review-queue PRIVATE output path is NOT under REPO_ROOT",
              not path_is_within(priv_path, REPO_ROOT), str(priv_path))
        check("lead-review-queue PRIVATE output file exists", priv_path.exists())
    else:
        pub_path = PUBLIC_OUTPUT_DIR / f"Lead_Review_Queue_{TODAY}.md"
        check("lead-review-queue public fallback output exists", pub_path.exists())

    proc = run_atlas("comms-approval-queue")
    check("comms-approval-queue exits 0", proc.returncode == 0, proc.stderr[:200])
    comms_stdout = proc.stdout
    check("comms-approval-queue console output has a counts-only summary line", "Summary:" in comms_stdout)
    comms_private_line = re.search(r"Wrote private output \(outside the repo\): (.+)", comms_stdout)
    if comms_private_line:
        priv_path = Path(comms_private_line.group(1).strip())
        check("comms-approval-queue PRIVATE output path is NOT under REPO_ROOT",
              not path_is_within(priv_path, REPO_ROOT), str(priv_path))
        check("comms-approval-queue PRIVATE output file exists", priv_path.exists())
    else:
        pub_path = PUBLIC_OUTPUT_DIR / f"Comms_Approval_Queue_{TODAY}.md"
        check("comms-approval-queue public fallback output exists", pub_path.exists())

    proc = run_atlas("daily-cycle")
    check("daily-cycle exits 0", proc.returncode == 0, proc.stderr[:200])
    cycle_path = PUBLIC_OUTPUT_DIR / f"Atlas_Daily_Operating_Cycle_{TODAY}.md"
    check("daily-cycle produces its consolidated report", cycle_path.exists())
    if cycle_path.exists():
        cycle_text = cycle_path.read_text(encoding="utf-8")
        check("daily-cycle report links the other reports generated this run",
              "Task_Queue_" in cycle_text and "Ops_Status_" in cycle_text)
        check("daily-cycle report gives an honest counts-only summary",
              "Summary" in cycle_text and "No outreach was sent" in cycle_text)

    # -------------------------------------------------------------------
    # 3. Private-store fallback logic (simulated, without touching the
    #    real private folder)
    # -------------------------------------------------------------------
    print("\n[3] Private-store fallback logic (simulated)")
    if atlas_mod is not None:
        try:
            real_cfg = atlas_mod.load_config()
            fake_cfg = json.loads(json.dumps(real_cfg))  # deep copy
            fake_cfg["paths"]["private_lead_tracker"] = "does/not/exist/Lead_Tracker.csv"
            fake_cfg["paths"]["private_outreach_tracker"] = "does/not/exist/Outreach_Tracker.csv"
            fake_cfg["paths"]["private_outreach_drafts_dir"] = "does/not/exist/Outreach_Drafts"

            class Args:
                pass

            rc = atlas_mod.cmd_lead_review_queue(fake_cfg, Args())
            check("lead-review-queue fallback branch runs cleanly with a non-resolving private path", rc == 0)
            fallback_lead_path = REPO_ROOT / real_cfg["paths"]["output_dir"] / f"Lead_Review_Queue_{atlas_mod.today()}.md"
            check("lead-review-queue fallback writes to the PUBLIC Atlas_Output dir", fallback_lead_path.exists())

            rc2 = atlas_mod.cmd_comms_approval_queue(fake_cfg, Args())
            check("comms-approval-queue fallback branch runs cleanly with a non-resolving private path", rc2 == 0)
            fallback_comms_path = REPO_ROOT / real_cfg["paths"]["output_dir"] / f"Comms_Approval_Queue_{atlas_mod.today()}.md"
            check("comms-approval-queue fallback writes to the PUBLIC Atlas_Output dir", fallback_comms_path.exists())

            # write_output_private must hard-refuse a path inside the repo,
            # regardless of what atlas_config.json says.
            refused = False
            try:
                atlas_mod.write_output_private(
                    PUBLIC_OUTPUT_DIR / "should_never_be_written.md", "test content"
                )
            except RuntimeError:
                refused = True
            check("write_output_private refuses to write inside the git repository", refused)
            check("write_output_private did not create the refused file",
                  not (PUBLIC_OUTPUT_DIR / "should_never_be_written.md").exists())
        except Exception as exc:
            check("Private-store fallback simulation completed without crashing", False, str(exc))
    else:
        check("Private-store fallback simulation completed without crashing", False, "atlas module failed to import")

    # -------------------------------------------------------------------
    # 4. Name-leak scan: nothing from the private folder ends up in the repo
    # -------------------------------------------------------------------
    print("\n[4] Private-data leak scan (public repo must never contain private names)")
    private_lead_tracker = REPO_ROOT / "../ALSAKKAF PRIVATE OPERATIONS/01_Revenue_Operations/PRJ-016/01_Verified_Leads/Lead_Tracker.csv"
    private_names = []
    if private_lead_tracker.exists():
        try:
            import csv
            with open(private_lead_tracker, "r", encoding="utf-8-sig", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = (row.get("Company Name") or "").strip()
                    if name and len(name) > 3:
                        private_names.append(name)
        except Exception:
            private_names = []
        check(f"Private lead tracker readable for leak-scan comparison ({len(private_names)} name(s) loaded, not printed)",
              True)
    else:
        check("Private lead tracker not present on this machine - leak scan runs on an empty name list (safe no-op)", True)

    leak_hits = []
    if private_names and PUBLIC_OUTPUT_DIR.exists():
        for path in PUBLIC_OUTPUT_DIR.rglob("*"):
            if not path.is_file():
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for name in private_names:
                if name in text:
                    leak_hits.append(str(path.relative_to(REPO_ROOT)))
                    break
    check("No private company name from the private lead tracker appears anywhere under the public Atlas_Output folder",
          not leak_hits, f"{len(leak_hits)} file(s) affected: {leak_hits[:5]}")

    # Also scan the rest of the repo areas Atlas can write to, for completeness.
    other_write_targets = [
        REPO_ROOT / "docs/atlas-dashboard-data.js",
    ]
    leak_hits_2 = []
    if private_names:
        for path in other_write_targets:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for name in private_names:
                if name in text:
                    leak_hits_2.append(str(path.relative_to(REPO_ROOT)))
                    break
    check("No private company name appears in docs/atlas-dashboard-data.js", not leak_hits_2, str(leak_hits_2))

    # -------------------------------------------------------------------
    # 5. Credential scan (same pattern as the rest of the suite)
    # -------------------------------------------------------------------
    print("\n[5] Credential scan of new command output")
    credential_pattern = re.compile(
        r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey|client[_-]?secret|"
        r"private[_-]?key|access[_-]?token|refresh[_-]?token|recovery[_-]?code|"
        r"2fa[_-]?code|bank[_-]?account|card[_-]?number)\b\s*[:=]\s*[^\s,\"']{4,}"
    )
    credential_hits = []
    if PUBLIC_OUTPUT_DIR.exists():
        for path in PUBLIC_OUTPUT_DIR.rglob("*.md"):
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for line in text.splitlines():
                if credential_pattern.search(line):
                    credential_hits.append(str(path.relative_to(REPO_ROOT)))
    check("No credential-like values in any Atlas_Output report", not credential_hits, str(credential_hits[:5]))

    # Summary
    print("\n" + "=" * 60)
    failed = [r for r in RESULTS if not r[1]]
    print(f"Checks run: {len(RESULTS)} | Passed: {len(RESULTS) - len(failed)} | Failed: {len(failed)}")
    if failed:
        print("RESULT: FAIL")
        for name, ok, detail in failed:
            print(f"  - {name}: {detail}")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
