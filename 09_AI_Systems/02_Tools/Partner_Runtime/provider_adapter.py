"""AOS Partner Runtime - cloud provider adapter (PRJ-012). Stdlib only.

MODE 3 — CLOUD PROVIDER (architecture; disabled by default).

Rules enforced here:
  * API keys come ONLY from environment variables — never files, never repo.
  * Network use requires BOTH: the env key present AND enabled=True passed
    explicitly by configuration the Founder controls.
  * Keys are never logged and never returned in results.
"""

import json
import os
import urllib.request


class ProviderUnavailable(Exception):
    pass


class CloudProviderAdapter:
    """Provider-independent adapter. Endpoint and env-var name are config;
    the shape follows the common chat-completions pattern so any compatible
    provider can be configured without code changes."""

    def __init__(self, endpoint=None, api_key_env="AOS_CLOUD_API_KEY",
                 model=None, enabled=False, timeout=60):
        self.endpoint = endpoint
        self.api_key_env = api_key_env
        self.model = model
        self.enabled = enabled
        self.timeout = timeout

    def available(self):
        return bool(self.enabled and self.endpoint and self.model
                    and os.environ.get(self.api_key_env))

    def complete(self, system_prompt, user_prompt):
        if not self.enabled:
            raise ProviderUnavailable(
                "Cloud provider is disabled. Founder must enable it in runtime config.")
        api_key = os.environ.get(self.api_key_env)
        if not api_key:
            raise ProviderUnavailable(
                "No API key in environment variable %s. Keys are never stored in files."
                % self.api_key_env)
        if not self.endpoint or not self.model:
            raise ProviderUnavailable("Endpoint/model not configured.")
        body = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint, data=body, method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer %s" % api_key})
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        try:
            return payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError):
            raise ProviderUnavailable("Unexpected provider response shape.")
