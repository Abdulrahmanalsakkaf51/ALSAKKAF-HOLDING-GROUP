"""AOS Partner Runtime v1 tests (PRJ-012). Standard library only.

Run: py test_partner_runtime.py
"""

import json
import os
import shutil
import tempfile
import unittest

from approval_gate import ApprovalGate
from local_model_adapter import LocalModelAdapter, LocalModelUnavailable
from memory_store import MemoryStore, MemoryError_
from partner_loader import load_all, load_partner, PartnerDefinitionError
from provider_adapter import CloudProviderAdapter, ProviderUnavailable
from runtime_logger import RuntimeLogger
from task_router import TaskRouter
from tool_registry import build_default_registry
from workflow_runner import WorkflowRunner

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARTNERS_DIR = os.path.join(BASE_DIR, "partners")


class RuntimeTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="aos_runtime_test_")
        self.registry = build_default_registry(os.path.join(self.tmp, "out"))
        self.gate = ApprovalGate(os.path.join(self.tmp, "approvals.json"))
        self.logger = RuntimeLogger(os.path.join(self.tmp, "logs"))
        self.memory = MemoryStore(os.path.join(self.tmp, "mem.sqlite3"))
        self.runner = WorkflowRunner(self.registry, self.gate, self.logger, self.memory)

    def tearDown(self):
        self.memory.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    # ---- loader ----

    def test_load_all_partners(self):
        partners = load_all(PARTNERS_DIR)
        self.assertIn("PARTNER-007", partners)
        self.assertIn("PARTNER-012", partners)

    def test_no_duplicate_partner_ids(self):
        partners = load_all(PARTNERS_DIR)
        self.assertEqual(len(partners), len(set(partners)))

    def test_authority_ceiling_enforced(self):
        bad = os.path.join(self.tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as f:
            json.dump({"id": "PARTNER-099", "name": "X", "type": "Operations Partner",
                       "authority_level": 5, "instructions": "x", "tools": [],
                       "workflows": {"w": []}}, f)
        with self.assertRaises(PartnerDefinitionError):
            load_partner(bad)

    # ---- tools ----

    def test_classify_request(self):
        out = self.registry.run("classify_request",
                                {"text": "URGENT invoice payment missing"})
        self.assertEqual(out["type"], "finance")
        self.assertEqual(out["urgency"], "high")

    def test_csv_stats(self):
        out = self.registry.run("csv_stats", {
            "csv_text": "Lead,Status\nA,New\nB,New\nC,Won\n", "count_by": "Status"})
        self.assertEqual(out["rows"], 3)
        self.assertEqual(out["counts"]["New"], 2)

    def test_write_draft_cannot_escape_output_dir(self):
        out = self.registry.run("write_draft",
                                {"filename": "..\\..\\evil.txt", "content": "x"})
        self.assertIn(os.path.join(self.tmp, "out"), out["written"])

    # ---- approval gate ----

    def test_restricted_step_blocks_without_approval(self):
        partners = load_all(PARTNERS_DIR)
        results = self.runner.run(partners["PARTNER-007"], "morning-intake")
        blocked = [r for r in results if r["status"] == "blocked_awaiting_approval"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(len(self.gate.pending()), 1)

    def test_gate_never_auto_approves(self):
        self.gate.request("PARTNER-007", "send_email", "test")
        self.assertFalse(self.gate.is_approved("PARTNER-007", "send_email"))

    def test_approved_action_executes(self):
        rec = self.gate.request("PARTNER-007", "send_email", "test")
        # simulate the Founder approving in the queue file
        with open(self.gate.queue_path, encoding="utf-8") as f:
            queue = json.load(f)
        for r in queue:
            if r["id"] == rec["id"]:
                r["status"] = "approved"
                r["decided_by"] = "Founder (test)"
        with open(self.gate.queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f)
        partners = load_all(PARTNERS_DIR)
        results = self.runner.run(partners["PARTNER-007"], "morning-intake")
        blocked = [r for r in results if r["status"] == "blocked_awaiting_approval"]
        self.assertEqual(len(blocked), 0)

    # ---- workflow ----

    def test_workflow_denies_unlisted_tool(self):
        partners = load_all(PARTNERS_DIR)
        p = partners["PARTNER-012"]
        p.data["workflows"]["bad"] = [{"step": "x", "tool": "classify_request",
                                       "input": {"text": "hello"}}]
        results = self.runner.run(p, "bad")
        self.assertEqual(results[0]["status"], "denied_tool_not_allowed")

    # ---- memory ----

    def test_memory_refuses_secrets(self):
        with self.assertRaises(MemoryError_):
            self.memory.remember("PARTNER-007", "api_key", "sk-fake")

    def test_memory_roundtrip(self):
        self.memory.remember("PARTNER-007", "note", "hello")
        self.assertEqual(self.memory.recall("PARTNER-007", "note"), "hello")

    # ---- adapters / router ----

    def test_cloud_adapter_disabled_by_default(self):
        adapter = CloudProviderAdapter()
        self.assertFalse(adapter.available())
        with self.assertRaises(ProviderUnavailable):
            adapter.complete("s", "u")

    def test_local_adapter_disabled_by_default(self):
        adapter = LocalModelAdapter()
        self.assertFalse(adapter.available())
        with self.assertRaises(LocalModelUnavailable):
            adapter.complete("s", "u")

    def test_router_prefers_deterministic(self):
        router = TaskRouter(self.registry, LocalModelAdapter(),
                            CloudProviderAdapter(), CloudProviderAdapter())
        route = router.route({"tool": "classify_request"})
        self.assertEqual(route["mode"], 1)

    def test_router_reports_unavailable_when_nothing_enabled(self):
        router = TaskRouter(self.registry, LocalModelAdapter(),
                            CloudProviderAdapter(), CloudProviderAdapter())
        route = router.route({"text": "please write a poem"})
        self.assertEqual(route["mode"], 0)

    # ---- logging ----

    def test_logger_redacts_secret_looking_fields(self):
        rec = self.logger.log("test", api_key="sk-fake", note="ok")
        self.assertEqual(rec["api_key"], "[REDACTED]")
        self.assertEqual(rec["note"], "ok")


if __name__ == "__main__":
    unittest.main(verbosity=2)
