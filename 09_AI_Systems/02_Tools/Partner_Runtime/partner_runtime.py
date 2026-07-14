"""AOS Partner Runtime v1 (PRJ-012). Standard library only.

Usage (run from this folder):

  py partner_runtime.py list                 List loaded Partner definitions
  py partner_runtime.py demo                 Run the deterministic demo workflow
  py partner_runtime.py run PARTNER-007 morning-intake
  py partner_runtime.py approvals            Show pending approval requests
  py partner_runtime.py modes                Show execution mode availability

A Partner is a role definition (instructions, tools, permissions, workflows,
memory rules, approval rules) executed by this shared runtime — not a
separate AI subscription. MODE 1 (deterministic) works with no AI and no
network. AI modes are disabled until the Founder configures them.
"""

import json
import os
import sys

from approval_gate import ApprovalGate
from local_model_adapter import LocalModelAdapter
from memory_store import MemoryStore
from partner_loader import load_all
from provider_adapter import CloudProviderAdapter
from runtime_logger import RuntimeLogger
from task_router import TaskRouter
from tool_registry import build_default_registry
from workflow_runner import WorkflowRunner

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARTNERS_DIR = os.path.join(BASE_DIR, "partners")
STATE_DIR = os.path.join(BASE_DIR, "Runtime_State")
OUTPUT_DIR = os.path.join(STATE_DIR, "Output")
LOG_DIR = os.path.join(STATE_DIR, "Logs")
CONFIG_PATH = os.path.join(BASE_DIR, "runtime_config.json")

DEFAULT_CONFIG = {
    "local_model": {"enabled": False, "endpoint": "http://127.0.0.1:11434/v1/chat/completions", "model": ""},
    "cloud_economy": {"enabled": False, "endpoint": "", "model": "", "api_key_env": "AOS_CLOUD_API_KEY"},
    "cloud_strong": {"enabled": False, "endpoint": "", "model": "", "api_key_env": "AOS_CLOUD_API_KEY"},
}


def load_config():
    if os.path.isfile(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_CONFIG


def build_runtime():
    config = load_config()
    registry = build_default_registry(OUTPUT_DIR)
    gate = ApprovalGate(os.path.join(STATE_DIR, "approvals_queue.json"))
    logger = RuntimeLogger(LOG_DIR)
    memory = MemoryStore(os.path.join(STATE_DIR, "partner_memory.sqlite3"))
    runner = WorkflowRunner(registry, gate, logger, memory)
    local = LocalModelAdapter(**config.get("local_model", DEFAULT_CONFIG["local_model"]))
    economy = CloudProviderAdapter(**config.get("cloud_economy", DEFAULT_CONFIG["cloud_economy"]))
    strong = CloudProviderAdapter(**config.get("cloud_strong", DEFAULT_CONFIG["cloud_strong"]))
    router = TaskRouter(registry, local, economy, strong)
    partners = load_all(PARTNERS_DIR)
    return {"registry": registry, "gate": gate, "logger": logger, "memory": memory,
            "runner": runner, "router": router, "partners": partners,
            "local": local, "economy": economy, "strong": strong}


def print_results(results):
    for r in results:
        print("  [%s] step %d: %s" % (r["status"], r["step"], r["name"]))
        if r["output"]:
            summary = json.dumps(r["output"], ensure_ascii=False)
            if len(summary) > 140:
                summary = summary[:137] + "..."
            print("        %s" % summary)


def main(argv):
    rt = build_runtime()
    cmd = argv[1] if len(argv) > 1 else "help"

    if cmd == "list":
        for pid, p in sorted(rt["partners"].items()):
            print("%s  %s (%s) — workflows: %s"
                  % (pid, p.name, p.type, ", ".join(sorted(p.workflows))))
    elif cmd == "demo":
        partner = rt["partners"]["PARTNER-007"]
        print("MODE 1 — DETERMINISTIC DEMO")
        print("Partner: %s — workflow: morning-intake" % partner.name)
        results = rt["runner"].run(partner, "morning-intake")
        print_results(results)
        pending = rt["gate"].pending()
        print("Pending approvals: %d (humans decide these)" % len(pending))
    elif cmd == "run":
        if len(argv) < 4:
            print("usage: py partner_runtime.py run <PARTNER-ID> <workflow>")
            return 2
        partner = rt["partners"].get(argv[2])
        if partner is None:
            print("Unknown Partner: %s" % argv[2])
            return 2
        results = rt["runner"].run(partner, argv[3])
        print_results(results)
    elif cmd == "approvals":
        pending = rt["gate"].pending()
        if not pending:
            print("No pending approvals.")
        for rec in pending:
            print("%s  partner=%s action=%s detail=%s"
                  % (rec["id"], rec["partner"], rec["action"], rec["detail"]))
        print("To approve: edit Runtime_State/approvals_queue.json, set status to"
              " \"approved\" and decided_by to your name.")
    elif cmd == "modes":
        print("MODE 1 deterministic : available (always)")
        print("MODE 2 local model   : %s" % ("available" if rt["local"].available() else "not configured/enabled"))
        print("MODE 3 cloud economy : %s" % ("available" if rt["economy"].available() else "not configured/enabled"))
        print("MODE 3 cloud strong  : %s" % ("available" if rt["strong"].available() else "not configured/enabled"))
        print("MODE 4 hybrid        : routes deterministic-first across whatever is enabled")
    else:
        print(__doc__)
    rt["memory"].close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
