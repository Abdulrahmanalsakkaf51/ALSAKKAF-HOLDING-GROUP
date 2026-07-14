"""AOS Partner Runtime - JSONL run logger (PRJ-012). Standard library only."""

import datetime
import json
import os


class RuntimeLogger:
    """Appends structured events to a JSONL log file per run day.

    Never log secrets: callers must not pass credentials; as a guard,
    values of keys that look like secrets are redacted.
    """

    SECRET_MARKERS = ("key", "token", "password", "secret", "credential")

    def __init__(self, log_dir):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def _redact(self, obj):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if any(m in str(k).lower() for m in self.SECRET_MARKERS):
                    out[k] = "[REDACTED]"
                else:
                    out[k] = self._redact(v)
            return out
        if isinstance(obj, list):
            return [self._redact(v) for v in obj]
        return obj

    def log(self, event, **fields):
        now = datetime.datetime.now()
        record = {"ts": now.isoformat(timespec="seconds"), "event": event}
        record.update(self._redact(fields))
        path = os.path.join(self.log_dir, "runtime_%s.jsonl" % now.strftime("%Y%m%d"))
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record
