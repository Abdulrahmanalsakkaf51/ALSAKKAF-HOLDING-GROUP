"""AOS Partner Runtime - task router (PRJ-012). Stdlib only.

MODE 4 — HYBRID routing order (Partner Routing and Cost Control Model, PRCC-001):

  1. Deterministic local tools  (free, always first)
  2. Local model                (if enabled and available)
  3. Economical cloud model     (if enabled; escalation)
  4. Strong cloud model         (if enabled; complex tasks only)

The router only ever *selects* a mode. Adapters enforce their own
availability and safety rules.
"""

COMPLEX_MARKERS = ("strategy", "legal", "architecture", "negotiation",
                   "long document", "multi-step reasoning")


class TaskRouter:
    def __init__(self, registry, local_adapter=None, cloud_economy=None,
                 cloud_strong=None):
        self.registry = registry
        self.local_adapter = local_adapter
        self.cloud_economy = cloud_economy
        self.cloud_strong = cloud_strong

    def classify_complexity(self, task_text):
        text = (task_text or "").lower()
        if any(m in text for m in COMPLEX_MARKERS):
            return "complex"
        if len(text) > 1200:
            return "complex"
        return "simple"

    def route(self, task):
        """task: {"tool": name} or {"text": free text}. Returns a route dict."""
        tool = task.get("tool")
        if tool and tool in self.registry.names():
            return {"mode": 1, "via": "deterministic", "tool": tool}
        complexity = self.classify_complexity(task.get("text", ""))
        if self.local_adapter is not None and self.local_adapter.available() \
                and complexity == "simple":
            return {"mode": 2, "via": "local_model"}
        if complexity == "simple" and self.cloud_economy is not None \
                and self.cloud_economy.available():
            return {"mode": 3, "via": "cloud_economy"}
        if self.cloud_strong is not None and self.cloud_strong.available():
            return {"mode": 3, "via": "cloud_strong"}
        return {"mode": 0, "via": "unavailable",
                "reason": "No capable mode is enabled. Deterministic tools cover "
                          "tool-based tasks; AI modes require Founder-enabled adapters."}
