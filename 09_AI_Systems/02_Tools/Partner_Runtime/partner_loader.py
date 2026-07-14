"""AOS Partner Runtime - Partner definition loader (PRJ-012). Stdlib only.

A Partner definition is a JSON file in the partners/ folder:

{
  "id": "PARTNER-007",
  "name": "AOS Office Partner",
  "type": "Operations Partner",
  "authority_level": 3,
  "instructions": "...",
  "knowledge": ["relative/paths/the/partner/may/read"],
  "tools": ["classify_request", "write_draft"],
  "restricted_actions": ["send_email", "external_commitment"],
  "memory_rules": {"remember_outcomes": true, "retention_days": 90},
  "workflows": {
    "workflow-name": [
      {"step": "...", "tool": "classify_request", "input": {...},
       "approval_action": null}
    ]
  }
}

A Partner is a role definition — not an AI subscription.
"""

import json
import os

REQUIRED_FIELDS = ("id", "name", "type", "authority_level", "instructions",
                   "tools", "workflows")
MAX_AUTHORITY = 3  # Foundation-stage ceiling per Partner Registry (PREG-001)


class PartnerDefinitionError(Exception):
    pass


class PartnerDefinition:
    def __init__(self, data, source_path):
        self.data = data
        self.source_path = source_path

    def __getattr__(self, item):
        try:
            return self.data[item]
        except KeyError:
            raise AttributeError(item)

    def get(self, key, default=None):
        return self.data.get(key, default)


def validate(data, source_path):
    for field in REQUIRED_FIELDS:
        if field not in data:
            raise PartnerDefinitionError(
                "%s: missing required field '%s'" % (source_path, field))
    if not isinstance(data["authority_level"], int):
        raise PartnerDefinitionError("%s: authority_level must be int" % source_path)
    if data["authority_level"] > MAX_AUTHORITY:
        raise PartnerDefinitionError(
            "%s: authority_level %d exceeds foundation ceiling %d (PREG-001)"
            % (source_path, data["authority_level"], MAX_AUTHORITY))
    if not isinstance(data["workflows"], dict) or not data["workflows"]:
        raise PartnerDefinitionError("%s: workflows must be a non-empty dict" % source_path)
    return data


def load_partner(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return PartnerDefinition(validate(data, path), path)


def load_all(partners_dir):
    """Load every *.json Partner definition; refuse duplicate Partner IDs."""
    partners = {}
    if not os.path.isdir(partners_dir):
        return partners
    for name in sorted(os.listdir(partners_dir)):
        if not name.endswith(".json"):
            continue
        p = load_partner(os.path.join(partners_dir, name))
        if p.id in partners:
            raise PartnerDefinitionError(
                "Duplicate Partner ID %s (%s and %s)"
                % (p.id, partners[p.id].source_path, p.source_path))
        partners[p.id] = p
    return partners
