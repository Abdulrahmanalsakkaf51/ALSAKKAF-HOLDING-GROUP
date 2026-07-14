"""AOS Partner Runtime - approval gate (PRJ-012). Standard library only.

Rule: nothing restricted executes without a human approval record.
The gate never auto-approves. Approvals are granted by the Founder editing
(or a future UI writing) the approvals queue file with status "approved".
"""

import datetime
import json
import os


class ApprovalGate:
    def __init__(self, queue_path):
        self.queue_path = queue_path
        os.makedirs(os.path.dirname(queue_path), exist_ok=True)

    def _load(self):
        if not os.path.isfile(self.queue_path):
            return []
        with open(self.queue_path, encoding="utf-8") as f:
            return json.load(f)

    def _save(self, queue):
        with open(self.queue_path, "w", encoding="utf-8") as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)

    def request(self, partner_id, action, detail):
        """File an approval request. Returns the request record."""
        queue = self._load()
        req_id = "APR-%s-%03d" % (
            datetime.datetime.now().strftime("%Y%m%d"), len(queue) + 1)
        record = {
            "id": req_id,
            "partner": partner_id,
            "action": action,
            "detail": detail,
            "status": "pending",
            "requested_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "decided_by": None,
        }
        queue.append(record)
        self._save(queue)
        return record

    def is_approved(self, partner_id, action):
        """True only if a matching request exists with status 'approved'."""
        for rec in self._load():
            if (rec["partner"] == partner_id and rec["action"] == action
                    and rec["status"] == "approved"):
                return True
        return False

    def pending(self):
        return [r for r in self._load() if r["status"] == "pending"]
