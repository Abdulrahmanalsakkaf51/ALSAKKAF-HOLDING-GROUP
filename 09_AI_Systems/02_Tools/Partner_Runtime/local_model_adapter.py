"""AOS Partner Runtime - local model adapter (PRJ-012). Stdlib only.

MODE 2 — LOCAL MODEL (architecture; disabled by default).

Targets an approved local inference server (for example an OpenAI-compatible
endpoint on 127.0.0.1 run by a tool the Founder installed and approved).
This adapter never installs anything and never reaches beyond loopback
unless the Founder explicitly configures a different host.
"""

import json
import urllib.request


class LocalModelUnavailable(Exception):
    pass


class LocalModelAdapter:
    def __init__(self, endpoint="http://127.0.0.1:11434/v1/chat/completions",
                 model="", enabled=False, timeout=120):
        self.endpoint = endpoint
        self.model = model
        self.enabled = enabled
        self.timeout = timeout

    def available(self):
        """Cheap availability probe. Only permitted when enabled by config."""
        if not (self.enabled and self.model):
            return False
        try:
            req = urllib.request.Request(self.endpoint, method="HEAD")
            urllib.request.urlopen(req, timeout=2)
            return True
        except Exception:
            return False

    def complete(self, system_prompt, user_prompt):
        if not self.enabled:
            raise LocalModelUnavailable(
                "Local model adapter is disabled. Founder must enable it in runtime config.")
        if not self.model:
            raise LocalModelUnavailable("No local model name configured.")
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint, data=body, method="POST",
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            raise LocalModelUnavailable("Local model server not reachable: %s" % exc)
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise LocalModelUnavailable("Unexpected local server response shape.")
