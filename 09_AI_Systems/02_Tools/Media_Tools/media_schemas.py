"""AOS Media Tools - Atlas media production schemas (PRJ-018). Stdlib only.

Defines the ten record schemas of the Atlas media production workflow and
the honest-value semantics used everywhere in media reporting:

  - a REAL value is a measured number (int >= 0),
  - ZERO is a real measured zero and is always reported as 0,
  - UNAVAILABLE means "not measured / not provided" and must never be
    replaced by an estimate. Revenue especially is never estimated.

Each schema is a dict: field name -> (type or tuple of types, required).
`validate(record, schema_name)` returns a list of problems (empty = valid).
No network access, no credentials, no upload capability exists here.
"""

UNAVAILABLE = "unavailable"

# Workflow stages, in pipeline order (MEDIA-013).
STAGES = [
    "content_order", "research", "script_validation", "scene_plan",
    "asset_manifest", "visual_generation_queue", "narration_queue",
    "edit_manifest", "captions", "thumbnail_brief", "upload_package",
    "founder_approval", "manual_upload_publish", "metrics_collection",
    "reporting",
]

CONTENT_STATUSES = ["Idea", "Drafted", "Recorded", "Edited", "Approved",
                    "Published", "Reported"]

CHANNELS = ["ALSAKKAF Systems", "Rihlat Aql", "Sand Dunes Stories"]

FORMATS = ["Long", "Short"]

_S = str
_I = int


def _metric():
    # A metric is a measured int or the literal "unavailable".
    return ((int, str), True)


SCHEMAS = {
    "media_order": {
        "order_id": (_S, True),
        "channel": (_S, True),
        "format": (_S, True),
        "working_title": (_S, True),
        "ordered_by": (_S, True),
        "order_date": (_S, True),
        "target_length": (_S, True),
        "package_folder": (_S, True),
        "notes": (_S, False),
    },
    "content_status": {
        "item_id": (_S, True),
        "stage": (_S, True),           # one of STAGES
        "status": (_S, True),          # one of CONTENT_STATUSES
        "updated": (_S, True),
        "blockers": (list, False),
        "founder_approved": (bool, True),
    },
    "asset_manifest_entry": {
        "asset_id": (_S, True),
        "item_id": (_S, True),
        "asset_type": (_S, True),
        "description": (_S, True),
        "rights": (_S, True),          # "Original" | "Licensed: <id>" | "Rights Unconfirmed"
        "ai_generated": (bool, True),
        "ai_prompt": (_S, False),      # required when ai_generated
        "local_path": (_S, False),     # media stays outside the repo
        "status": (_S, True),
    },
    "narration_manifest_entry": {
        "line_id": (_S, True),
        "item_id": (_S, True),
        "language": (_S, True),
        "text": (_S, True),
        "voice_path": (_S, True),      # "founder_recording" | "tts" | "founder_cloned_voice" | "undecided"
        "consent_recorded": (bool, True),
        "status": (_S, True),
    },
    "edit_manifest": {
        "item_id": (_S, True),
        "editor_project_file": (_S, True),   # local path record or "unavailable"
        "timeline_duration_seconds": ((int, str), True),
        "music_license_ids": (list, True),
        "captions_file": (_S, True),
        "inspected_by": (_S, True),          # human name or "unavailable"
        "status": (_S, True),
    },
    "upload_package": {
        "item_id": (_S, True),
        "title": (_S, True),
        "description": (_S, True),
        "tags": (list, True),
        "thumbnail_ref": (_S, True),
        "captions_ref": (_S, True),
        "ai_disclosure": (_S, True),   # "none" | "ai_narration" | "ai_visuals" | "ai_narration_and_visuals"
        "founder_approved": (bool, True),
        "approval_date": (_S, False),
    },
    "video_record": {
        "item_id": (_S, True),
        "channel": (_S, True),
        "format": (_S, True),
        "final_title": (_S, True),
        "publish_date": (_S, True),
        "url": (_S, True),
        "duration_seconds": ((int, str), True),
        "published_by": (_S, True),    # always a human
    },
    "channel_metrics_snapshot": {
        "channel": (_S, True),
        "snapshot_date": (_S, True),
        "data_source": (_S, True),     # "mock" | "manual_export" (API needs separate Founder approval + OAuth)
        "subscribers_total": _metric(),
        "views_total": _metric(),
        "watch_hours_total": _metric(),
        "videos_published_total": _metric(),
        "shorts_published_total": _metric(),
        "estimated_revenue": _metric(),  # stays "unavailable" unless genuinely available
    },
    "daily_media_report": {
        "report_date": (_S, True),
        "data_source": (_S, True),
        "in_production": (list, True),   # item_id + stage pairs
        "blockers": (list, True),
        "videos_published_today": ((int, str), True),
        "views_delta": _metric(),
        "subscribers_delta": _metric(),
        "comments_requiring_attention": _metric(),
    },
    "weekly_founder_media_report": {
        "week_ending": (_S, True),
        "data_source": (_S, True),
        "uploads": ((int, str), True),
        "shorts": ((int, str), True),
        "views_total": _metric(),
        "watch_hours": _metric(),
        "subscribers_gained": _metric(),
        "subscribers_lost": _metric(),
        "top_video": (_S, True),         # title or "unavailable"
        "retention_observations": (_S, True),
        "traffic_sources": (_S, True),   # text or "unavailable"
        "website_clicks": _metric(),
        "estimated_revenue": _metric(),  # never estimated; "unavailable" until real
        "next_7_day_recommendations": (list, True),
    },
}


def validate(record, schema_name):
    """Return a list of problems with `record` against the named schema."""
    problems = []
    schema = SCHEMAS.get(schema_name)
    if schema is None:
        return ["unknown schema: %s" % schema_name]
    if not isinstance(record, dict):
        return ["record must be a dict"]
    for field, (types, required) in schema.items():
        if field not in record:
            if required:
                problems.append("missing required field: %s" % field)
            continue
        value = record[field]
        if not isinstance(value, types):
            problems.append("field %s has wrong type %s" % (
                field, type(value).__name__))
    for field in record:
        if field not in schema:
            problems.append("unknown field: %s" % field)

    # Honest-value semantics: string metrics may only be "unavailable";
    # int metrics may not be negative.
    for field, (types, _req) in schema.items():
        if field in record and isinstance(types, tuple) and int in types \
                and str in types:
            value = record[field]
            if isinstance(value, str) and value != UNAVAILABLE:
                problems.append(
                    "field %s must be a measured int or %r, got %r"
                    % (field, UNAVAILABLE, value))
            if isinstance(value, bool):
                problems.append("field %s must not be boolean" % field)
            elif isinstance(value, int) and value < 0:
                problems.append("field %s must not be negative" % field)

    # Cross-field rules.
    if schema_name == "content_status":
        if record.get("stage") not in STAGES:
            problems.append("stage must be one of STAGES")
        if record.get("status") not in CONTENT_STATUSES:
            problems.append("status must be one of CONTENT_STATUSES")
    if schema_name == "asset_manifest_entry":
        if record.get("ai_generated") and not record.get("ai_prompt"):
            problems.append("ai_generated assets must record ai_prompt")
    if schema_name == "narration_manifest_entry":
        if record.get("voice_path") == "founder_cloned_voice" \
                and not record.get("consent_recorded"):
            problems.append("cloned voice requires consent_recorded = True")
    if schema_name == "upload_package":
        if record.get("founder_approved") and not record.get("approval_date"):
            problems.append("approved package must record approval_date")
    if schema_name in ("channel_metrics_snapshot", "daily_media_report",
                       "weekly_founder_media_report"):
        if record.get("data_source") not in ("mock", "manual_export"):
            problems.append(
                "data_source must be 'mock' or 'manual_export' "
                "(API integration requires separate Founder approval "
                "and OAuth — never account passwords)")
    return problems
