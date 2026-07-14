"""AOS Media Tools - Atlas media production workflow scaffold (PRJ-018).

Stdlib only. This is a LOCAL planning scaffold:
  - it models the pipeline Content Order -> ... -> Reports,
  - it enforces the Founder-approval gate before publish,
  - it produces daily/weekly reports from records it is given.

It deliberately has NO capability to upload, publish, authenticate, or
talk to any network service. It never asks for or stores credentials,
passwords, passkeys, 2FA codes, or recovery codes. Publishing is a
manual Founder action recorded after the fact.

Usage (from repo root):
  py 09_AI_Systems\\02_Tools\\Media_Tools\\media_workflow.py demo
"""

import sys

import media_schemas as ms

# Stages that only a human may complete.
HUMAN_ONLY_STAGES = {"founder_approval", "manual_upload_publish"}


class WorkflowError(Exception):
    pass


def new_content_status(item_id):
    return {
        "item_id": item_id,
        "stage": ms.STAGES[0],
        "status": "Idea",
        "updated": "",
        "blockers": [],
        "founder_approved": False,
    }


def advance(status_record, to_stage, actor="atlas", date=""):
    """Advance a content item to the next stage, enforcing order + gates."""
    problems = ms.validate(status_record, "content_status")
    if problems:
        raise WorkflowError("invalid content_status: %s" % "; ".join(problems))
    current = ms.STAGES.index(status_record["stage"])
    target = ms.STAGES.index(to_stage)
    if target != current + 1:
        raise WorkflowError(
            "stages cannot be skipped: %s -> %s"
            % (status_record["stage"], to_stage))
    if to_stage in HUMAN_ONLY_STAGES and actor != "founder":
        raise WorkflowError(
            "stage %r is a human/Founder-only action; actor was %r"
            % (to_stage, actor))
    if to_stage == "manual_upload_publish" and not status_record.get(
            "founder_approved"):
        raise WorkflowError("cannot publish without founder_approved=True")
    status_record = dict(status_record)
    status_record["stage"] = to_stage
    status_record["updated"] = date
    if to_stage == "founder_approval" and actor == "founder":
        status_record["founder_approved"] = True
    return status_record


def _fmt_metric(value):
    if value == ms.UNAVAILABLE:
        return "unavailable (not measured - never estimated)"
    return str(value)


def render_daily_report(report):
    problems = ms.validate(report, "daily_media_report")
    if problems:
        raise WorkflowError("invalid daily report: %s" % "; ".join(problems))
    lines = ["ATLAS DAILY MEDIA REPORT - %s" % report["report_date"],
             "Data source: %s" % report["data_source"], ""]
    lines.append("In production:")
    for entry in report["in_production"] or ["(none)"]:
        lines.append("  - %s" % entry)
    lines.append("Blockers:")
    for entry in report["blockers"] or ["(none)"]:
        lines.append("  - %s" % entry)
    lines.append("Videos published today: %s"
                 % _fmt_metric(report["videos_published_today"]))
    lines.append("Views delta: %s" % _fmt_metric(report["views_delta"]))
    lines.append("Subscribers delta: %s"
                 % _fmt_metric(report["subscribers_delta"]))
    lines.append("Comments requiring attention: %s"
                 % _fmt_metric(report["comments_requiring_attention"]))
    return "\n".join(lines)


def render_weekly_report(report):
    problems = ms.validate(report, "weekly_founder_media_report")
    if problems:
        raise WorkflowError("invalid weekly report: %s" % "; ".join(problems))
    lines = ["ATLAS WEEKLY FOUNDER MEDIA REPORT - week ending %s"
             % report["week_ending"],
             "Data source: %s" % report["data_source"], ""]
    for label, key in [
            ("Uploads", "uploads"), ("Shorts", "shorts"),
            ("Total views", "views_total"), ("Watch hours", "watch_hours"),
            ("Subscribers gained", "subscribers_gained"),
            ("Subscribers lost", "subscribers_lost"),
            ("Website clicks", "website_clicks"),
            ("Estimated revenue", "estimated_revenue")]:
        lines.append("%s: %s" % (label, _fmt_metric(report[key])))
    lines.append("Top video: %s" % report["top_video"])
    lines.append("Retention observations: %s"
                 % report["retention_observations"])
    lines.append("Traffic sources: %s" % report["traffic_sources"])
    lines.append("Next 7 days:")
    for rec in report["next_7_day_recommendations"]:
        lines.append("  - %s" % rec)
    return "\n".join(lines)


def demo():
    """Run the scaffold end-to-end on clearly-labeled MOCK data."""
    print("=== MEDIA WORKFLOW SCAFFOLD DEMO (mock data only) ===\n")

    status = new_content_status("RA-VID-001")
    for stage in ms.STAGES[1:12]:
        actor = "founder" if stage in HUMAN_ONLY_STAGES else "atlas"
        status = advance(status, stage, actor=actor, date="2026-07-15")
    print("Pipeline advanced to: %s (founder_approved=%s)"
          % (status["stage"], status["founder_approved"]))

    try:
        advance(new_content_status("SYS-VID-001"), "research",
                actor="atlas", date="2026-07-15")
        bad = dict(new_content_status("SYS-VID-001"), stage="upload_package")
        advance(bad, "founder_approval", actor="atlas")
        print("GATE FAILURE: atlas approved its own content")
    except WorkflowError as err:
        print("Founder gate enforced: %s" % err)

    snapshot = {
        "channel": "Rihlat Aql", "snapshot_date": "2026-07-15",
        "data_source": "mock", "subscribers_total": 0, "views_total": 0,
        "watch_hours_total": 0, "videos_published_total": 0,
        "shorts_published_total": 0, "estimated_revenue": ms.UNAVAILABLE,
    }
    problems = ms.validate(snapshot, "channel_metrics_snapshot")
    print("Mock snapshot valid: %s" % ("yes" if not problems else problems))

    daily = {
        "report_date": "2026-07-15", "data_source": "mock",
        "in_production": ["RA-VID-001 @ upload_package",
                          "SYS-VID-001 @ script_validation"],
        "blockers": ["Voice path decision (MEDIA-014)",
                     "Music licenses unconfirmed"],
        "videos_published_today": 0, "views_delta": 0,
        "subscribers_delta": 0,
        "comments_requiring_attention": ms.UNAVAILABLE,
    }
    print("\n" + render_daily_report(daily))

    weekly = {
        "week_ending": "2026-07-19", "data_source": "mock",
        "uploads": 0, "shorts": 0, "views_total": 0,
        "watch_hours": 0, "subscribers_gained": 0, "subscribers_lost": 0,
        "top_video": ms.UNAVAILABLE,
        "retention_observations": "no published content yet",
        "traffic_sources": ms.UNAVAILABLE, "website_clicks": ms.UNAVAILABLE,
        "estimated_revenue": ms.UNAVAILABLE,
        "next_7_day_recommendations": [
            "Founder review of the four drafted packages",
            "Confirm music/visual licenses for RA-VID-001",
            "Decide narration path (MEDIA-014)"],
    }
    print("\n" + render_weekly_report(weekly))
    print("\n=== END DEMO — no uploads occurred; no network was touched ===")
    return 0


def main(argv):
    if len(argv) > 1 and argv[1] == "demo":
        return demo()
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
