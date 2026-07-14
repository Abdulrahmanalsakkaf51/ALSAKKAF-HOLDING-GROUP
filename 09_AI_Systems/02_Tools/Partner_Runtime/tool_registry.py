"""AOS Partner Runtime - deterministic tool layer (PRJ-012). Standard library only.

Tools are plain Python callables registered with a safety class:
  read      - reads approved data, no side effects
  produce   - creates draft artifacts in the output folder
  restricted- anything with outside-world or destructive effect; requires approval
"""

import csv
import datetime
import io
import os


class ToolError(Exception):
    pass


class Tool:
    def __init__(self, name, fn, description, safety="read"):
        if safety not in ("read", "produce", "restricted"):
            raise ToolError("Unknown safety class: %s" % safety)
        self.name = name
        self.fn = fn
        self.description = description
        self.safety = safety


class ToolRegistry:
    def __init__(self):
        self._tools = {}

    def register(self, name, fn, description, safety="read"):
        if name in self._tools:
            raise ToolError("Duplicate tool name: %s" % name)
        self._tools[name] = Tool(name, fn, description, safety)

    def get(self, name):
        if name not in self._tools:
            raise ToolError("Unknown tool: %s" % name)
        return self._tools[name]

    def names(self):
        return sorted(self._tools)

    def run(self, name, payload):
        return self.get(name).fn(payload)


# ---------------------------------------------------------------------------
# Built-in deterministic tools (MODE 1 - no AI, no network)
# ---------------------------------------------------------------------------

CLASSIFY_RULES = [
    ("finance", ("invoice", "payment", "refund", "quote", "price", "salary")),
    ("scheduling", ("meeting", "schedule", "calendar", "appointment", "reschedule")),
    ("reporting", ("report", "summary", "kpi", "metrics", "dashboard")),
    ("client", ("client", "customer", "inquiry", "enquiry", "complaint", "lead")),
    ("filing", ("document", "file", "archive", "record", "certificate")),
    ("people", ("leave", "vacation", "sick", "probation", "employee", "hr")),
]

URGENT_MARKERS = ("urgent", "asap", "today", "immediately", "overdue")


def tool_classify_request(payload):
    """Classify a request line into a type and urgency using keyword rules."""
    text = str(payload.get("text", "")).lower()
    rtype = "general"
    for name, words in CLASSIFY_RULES:
        if any(w in text for w in words):
            rtype = name
            break
    urgency = "high" if any(w in text for w in URGENT_MARKERS) else "normal"
    return {"type": rtype, "urgency": urgency}


def tool_summarize_extractive(payload):
    """Deterministic extractive summary: first sentence of each paragraph."""
    text = str(payload.get("text", ""))
    max_items = int(payload.get("max_items", 5))
    lines = []
    for para in text.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        first = para.split(". ")[0].strip()
        if first:
            lines.append(first.rstrip(".") + ".")
        if len(lines) >= max_items:
            break
    return {"summary": lines}


def tool_csv_stats(payload):
    """Count rows and per-column value counts for a CSV text or file."""
    if "csv_text" in payload:
        stream = io.StringIO(payload["csv_text"])
    else:
        path = payload["path"]
        if not os.path.isfile(path):
            raise ToolError("CSV not found: %s" % path)
        stream = open(path, encoding="utf-8-sig", newline="")
    with stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    count_by = payload.get("count_by")
    counts = {}
    if count_by:
        for row in rows:
            key = (row.get(count_by) or "").strip() or "(blank)"
            counts[key] = counts.get(key, 0) + 1
    return {"rows": len(rows), "columns": list(rows[0].keys()) if rows else [], "counts": counts}


def tool_make_checklist(payload):
    """Turn a list of items into a Markdown checklist."""
    items = payload.get("items", [])
    return {"markdown": "\n".join("- [ ] %s" % i for i in items)}


def tool_timestamp(_payload):
    return {"now": datetime.datetime.now().isoformat(timespec="seconds")}


def make_write_draft_tool(output_dir):
    """Factory: a 'produce' tool that writes draft text files into the runtime
    output folder only. Filenames are sanitized; paths cannot escape."""
    def tool_write_draft(payload):
        name = str(payload.get("filename", "draft.txt"))
        name = os.path.basename(name).replace("..", "_")
        os.makedirs(output_dir, exist_ok=True)
        path = os.path.join(output_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(payload.get("content", "")))
        return {"written": path}
    return tool_write_draft


def build_default_registry(output_dir):
    reg = ToolRegistry()
    reg.register("classify_request", tool_classify_request,
                 "Classify a request into type and urgency (keyword rules)", "read")
    reg.register("summarize_extractive", tool_summarize_extractive,
                 "Deterministic extractive summary", "read")
    reg.register("csv_stats", tool_csv_stats,
                 "Row counts and value counts for a CSV", "read")
    reg.register("make_checklist", tool_make_checklist,
                 "Build a Markdown checklist", "read")
    reg.register("timestamp", tool_timestamp, "Current local time", "read")
    reg.register("write_draft", make_write_draft_tool(output_dir),
                 "Write a draft file into the runtime output folder", "produce")
    return reg
