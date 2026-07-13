#!/usr/bin/env python3
"""
PRJ-009 First Revenue Acquisition Sprint - release test.

Python standard library only. No network access. Read-only: this test
writes nothing and changes nothing.

Note: the Founder's build order named this test for "PRJ-008", but PRJ-008
was already assigned to AOS v0.7, so the sprint (and this test) use PRJ-009.

Run:
    py 09_AI_Systems\\02_Tools\\Atlas_Runtime\\test_prj_009_revenue_sprint.py
"""

import importlib.util
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True  # keep the repo free of __pycache__ artifacts

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]

PAYPAL_LINK = "https://www.paypal.com/ncp/payment/2AN8FH99X682C"
CONTACT_EMAIL = "atlasos5555@gmail.com"

CREDENTIAL_PATTERN = re.compile(
    r"(?i)\b(password|passwd|pwd|secret|api[_-]?key|apikey|client[_-]?secret|"
    r"private[_-]?key|access[_-]?token|refresh[_-]?token|recovery[_-]?code|"
    r"2fa[_-]?code|bank[_-]?account|card[_-]?number)\b\s*[:=]\s*[^\s,\"']{4,}"
)

RESULTS = []


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    status = "PASS" if ok else "FAIL"
    line = f"  [{status}] {name}"
    if detail and not ok:
        line += f" -- {detail}"
    print(line)


def read_text(rel):
    p = REPO_ROOT / rel
    if not p.exists():
        return None
    return p.read_text(encoding="utf-8", errors="replace")


def main():
    print("PRJ-009 First Revenue Acquisition Sprint - Release Test")
    print("=" * 60)

    # 1. Landing page exists and carries both offers
    print("\n[1] Landing page and offers")
    landing = read_text("docs/index.html")
    check("Landing page exists (docs/index.html)", landing is not None)
    if landing is None:
        landing = ""
    check("$399 offer present", "$399" in landing and "AI Workflow Starter Pack" in landing)
    check("$450 AI Agent offer present", "$450" in landing and "AI Agent Starter Pack" in landing)
    check("Temporary contact email present", CONTACT_EMAIL in landing)
    check("Temporary email labeled as temporary", "Temporary launch contact email" in landing)

    # 2. PayPal link only for the $399 offer
    print("\n[2] Payment link discipline")
    check("Approved PayPal link present on landing page", PAYPAL_LINK in landing)
    agent_start = landing.find('id="agent-offer"')
    check("AI Agent offer section exists on landing page", agent_start != -1)
    if agent_start != -1:
        agent_end = landing.find("</section>", agent_start)
        agent_section = landing[agent_start:agent_end if agent_end != -1 else None]
        check("No PayPal link inside the $450 AI Agent section", PAYPAL_LINK not in agent_section)
        check("$450 section uses Request Custom Quote", "Request Custom Quote" in agent_section)

    ai_proposal_tpl = read_text(
        "01_Holding_Company/07_Templates/Revenue_Launch/AI_Agent_Starter_Pack/AI_Agent_Starter_Proposal_Template.md"
    )
    check("AI Agent proposal template exists", ai_proposal_tpl is not None)
    if ai_proposal_tpl:
        check("No PayPal link in AI Agent proposal template", PAYPAL_LINK not in ai_proposal_tpl)

    config_text = read_text("09_AI_Systems/02_Tools/Atlas_Runtime/atlas_config.json") or ""
    second_block = config_text[config_text.find('"second_offer"'):config_text.find('"active_partners"')]
    check("Config second_offer has no payment link", PAYPAL_LINK not in second_block and second_block != "")

    # 3. AI Agent delivery system
    print("\n[3] AI Agent Starter Pack delivery system")
    delivery_dir = REPO_ROOT / "01_Holding_Company/04_Operations/05_Client_Delivery/AI_Agent_Starter_Pack"
    check("Delivery folder exists", delivery_dir.is_dir())
    expected_delivery = [
        "AI_Agent_Starter_Pack_Delivery_Workflow.md",
        "AI_Agent_Client_Intake_Form.md",
        "AI_Agent_Profile_Template.md",
        "AI_Agent_Prompt_Template.md",
        "AI_Agent_Task_Routing_Template.md",
        "AI_Agent_Implementation_Guide_Template.md",
        "AI_Agent_Safety_and_Approval_Rules.md",
        "AI_Agent_Final_Handover_Template.md",
        "AI_Agent_Revision_Rules.md",
    ]
    missing = [f for f in expected_delivery if not (delivery_dir / f).exists()]
    check("All 9 delivery documents present", not missing, f"missing: {missing}")

    # 4. Sprint folder
    print("\n[4] PRJ-009 sprint execution system")
    sprint_dir = REPO_ROOT / "01_Holding_Company/04_Operations/10_Revenue_Sprints/PRJ-009_First_Revenue_Sprint"
    check("Sprint folder exists", sprint_dir.is_dir())
    expected_sprint = [
        "First_Revenue_Sprint_Master_Plan.md",
        "Day_1_Publish_and_Prepare.md",
        "Day_2_First_25_Leads.md",
        "Day_3_First_5_Outreach.md",
        "Day_4_Follow_Up_and_Proposal.md",
        "Day_5_Content_and_Trust.md",
        "Day_6_Consultation_and_Close.md",
        "Day_7_Review_and_Improve.md",
        "First_25_Leads_Template.csv",
        "First_5_Outreach_Batch_Template.md",
        "First_Client_Proposal_Template.md",
        "First_Payment_Checklist.md",
        "First_Client_Delivery_Start_Checklist.md",
        "Sprint_Lessons_Learned_Template.md",
    ]
    missing = [f for f in expected_sprint if not (sprint_dir / f).exists()]
    check("All 14 sprint files present", not missing, f"missing: {missing}")

    # 5. Atlas commands callable
    print("\n[5] Atlas Runtime commands")
    atlas_path = SCRIPT_DIR / "atlas.py"
    check("atlas.py exists", atlas_path.exists())
    try:
        spec = importlib.util.spec_from_file_location("atlas", atlas_path)
        atlas = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(atlas)
        cmds = getattr(atlas, "COMMANDS", {})
        for name in ("revenue-sprint", "ai-agent-proposal", "ai-agent-delivery", "first-5-outreach"):
            check(f"Command registered and callable: {name}", callable(cmds.get(name)))
        parser = atlas.build_parser()
        for name in ("revenue-sprint", "ai-agent-proposal", "ai-agent-delivery", "first-5-outreach"):
            args = parser.parse_args([name])
            check(f"Command parses: {name}", args.command == name)
    except Exception as exc:
        check("atlas.py imports cleanly", False, str(exc))

    # 6. No secrets in the new PRJ-009 files
    print("\n[6] Credential scan of new PRJ-009 areas")
    scan_dirs = [
        "01_Holding_Company/04_Operations/05_Client_Delivery/AI_Agent_Starter_Pack",
        "01_Holding_Company/07_Templates/Revenue_Launch/AI_Agent_Starter_Pack",
        "01_Holding_Company/04_Operations/10_Revenue_Sprints",
        "01_Holding_Company/04_Operations/06_Market_Intelligence",
        "01_Holding_Company/03_Strategy/AOS_No_Hype_Revenue_Reality.md",
        "docs",
        "09_AI_Systems/02_Tools/Atlas_Runtime",
    ]
    hits = []
    for rel in scan_dirs:
        base = REPO_ROOT / rel
        files = [base] if base.is_file() else list(base.rglob("*")) if base.exists() else []
        for f in files:
            if not f.is_file():
                continue
            if f.suffix.lower() not in (".md", ".js", ".json", ".py", ".ps1", ".bat", ".html", ".css", ".csv"):
                continue
            text = f.read_text(encoding="utf-8", errors="replace")
            for match in CREDENTIAL_PATTERN.finditer(text):
                # Skip regex definitions and policy wording inside the tools/tests themselves
                if f.name in ("atlas.py", "test_prj_009_revenue_sprint.py", "test_atlas_runtime.py", "markdown_audit.py"):
                    continue
                hits.append(f"{f.relative_to(REPO_ROOT)}: {match.group(0)[:40]}")
    check("No credential-like values found", not hits, "; ".join(hits[:5]))

    # 7. Supporting records and tools
    print("\n[7] Records and tools")
    check("Markdown Audit script exists",
          (REPO_ROOT / "09_AI_Systems/02_Tools/Markdown_Audit/markdown_audit.py").exists())
    check("PRJ-009 project record exists",
          (REPO_ROOT / "01_Holding_Company/04_Operations/01_Project_Records/PRJ-009_First_Revenue_Acquisition_Sprint.md").exists())
    register = read_text("01_Holding_Company/04_Operations/Project_Register.md") or ""
    check("PRJ-009 in Project Register", "PRJ-009" in register)
    catalog = read_text("01_Holding_Company/03_Strategy/AOS_Service_Offer_Catalog.md") or ""
    check("AI Agent Starter Pack in Service Offer Catalog",
          "AI Agent Starter Pack" in catalog and "payment link pending Founder approval" in catalog)

    # Summary
    print("\n" + "=" * 60)
    failed = [r for r in RESULTS if not r[1]]
    print(f"Checks run: {len(RESULTS)} | Passed: {len(RESULTS) - len(failed)} | Failed: {len(failed)}")
    if failed:
        print("RESULT: FAIL")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
