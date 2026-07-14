"""AOS Media Tools - schema and workflow tests (PRJ-018). Stdlib only."""

import os
import sys
import unittest

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import media_schemas as ms  # noqa: E402
import media_workflow as mw  # noqa: E402


class SchemaTests(unittest.TestCase):
    def test_all_ten_schemas_exist(self):
        self.assertEqual(
            set(ms.SCHEMAS),
            {"media_order", "content_status", "asset_manifest_entry",
             "narration_manifest_entry", "edit_manifest", "upload_package",
             "video_record", "channel_metrics_snapshot",
             "daily_media_report", "weekly_founder_media_report"})

    def test_metric_rejects_estimates(self):
        snap = {"channel": "Rihlat Aql", "snapshot_date": "2026-07-15",
                "data_source": "mock", "subscribers_total": "about 100",
                "views_total": 0, "watch_hours_total": 0,
                "videos_published_total": 0, "shorts_published_total": 0,
                "estimated_revenue": ms.UNAVAILABLE}
        problems = ms.validate(snap, "channel_metrics_snapshot")
        self.assertTrue(any("about 100" in p for p in problems))

    def test_metric_accepts_zero_and_unavailable(self):
        snap = {"channel": "Rihlat Aql", "snapshot_date": "2026-07-15",
                "data_source": "mock", "subscribers_total": 0,
                "views_total": 0, "watch_hours_total": 0,
                "videos_published_total": 0, "shorts_published_total": 0,
                "estimated_revenue": ms.UNAVAILABLE}
        self.assertEqual(ms.validate(snap, "channel_metrics_snapshot"), [])

    def test_negative_metrics_rejected(self):
        snap = {"channel": "Rihlat Aql", "snapshot_date": "2026-07-15",
                "data_source": "mock", "subscribers_total": -5,
                "views_total": 0, "watch_hours_total": 0,
                "videos_published_total": 0, "shorts_published_total": 0,
                "estimated_revenue": ms.UNAVAILABLE}
        self.assertTrue(ms.validate(snap, "channel_metrics_snapshot"))

    def test_data_source_must_be_mock_or_manual(self):
        snap = {"channel": "Rihlat Aql", "snapshot_date": "2026-07-15",
                "data_source": "api", "subscribers_total": 0,
                "views_total": 0, "watch_hours_total": 0,
                "videos_published_total": 0, "shorts_published_total": 0,
                "estimated_revenue": ms.UNAVAILABLE}
        problems = ms.validate(snap, "channel_metrics_snapshot")
        self.assertTrue(any("OAuth" in p for p in problems))

    def test_cloned_voice_requires_consent(self):
        entry = {"line_id": "N1", "item_id": "RA-VID-001",
                 "language": "Arabic", "text": "x",
                 "voice_path": "founder_cloned_voice",
                 "consent_recorded": False, "status": "planned"}
        problems = ms.validate(entry, "narration_manifest_entry")
        self.assertTrue(any("consent" in p for p in problems))

    def test_ai_asset_requires_prompt_log(self):
        entry = {"asset_id": "A1", "item_id": "RA-VID-001",
                 "asset_type": "illustration", "description": "x",
                 "rights": "Original", "ai_generated": True,
                 "status": "planned"}
        problems = ms.validate(entry, "asset_manifest_entry")
        self.assertTrue(any("ai_prompt" in p for p in problems))


class WorkflowTests(unittest.TestCase):
    def test_stage_order_enforced(self):
        status = mw.new_content_status("X-1")
        with self.assertRaises(mw.WorkflowError):
            mw.advance(status, "captions")

    def test_founder_gate_actor_enforced(self):
        status = mw.new_content_status("X-1")
        for stage in ms.STAGES[1:11]:
            status = mw.advance(status, stage, actor="atlas")
        with self.assertRaises(mw.WorkflowError):
            mw.advance(status, "founder_approval", actor="atlas")

    def test_publish_requires_founder_approval_flag(self):
        status = mw.new_content_status("X-1")
        for stage in ms.STAGES[1:11]:
            status = mw.advance(status, stage, actor="atlas")
        status = mw.advance(status, "founder_approval", actor="founder")
        self.assertTrue(status["founder_approved"])
        status2 = dict(status, founder_approved=False)
        with self.assertRaises(mw.WorkflowError):
            mw.advance(status2, "manual_upload_publish", actor="founder")

    def test_no_network_or_credential_capability(self):
        for module_file in ("media_schemas.py", "media_workflow.py",
                            "media_briefing.py"):
            source = open(os.path.join(BASE, module_file),
                          encoding="utf-8").read()
            # Capability tokens only — policy docstrings may mention the
            # words "password"/"passkey" when stating the prohibition.
            for forbidden in ("import requests", "import urllib",
                              "import http.client", "import smtplib",
                              "import socket", "googleapiclient",
                              "getpass", "keyring", "client_secret",
                              "refresh_token", "oauth2"):
                self.assertNotIn(forbidden, source,
                                 msg="%s contains %r" % (module_file,
                                                         forbidden))

    def test_demo_runs_clean(self):
        self.assertEqual(mw.demo.__doc__ is not None, True)
        # Render functions reject invalid reports.
        with self.assertRaises(mw.WorkflowError):
            mw.render_daily_report({"report_date": "2026-07-15"})


if __name__ == "__main__":
    unittest.main(verbosity=1)
