"""AOS Partner Runtime - workflow runner (PRJ-012). Stdlib only.

Executes one named workflow from a Partner definition, step by step:

  * Steps whose tool is in the Partner's allowed tools run through the registry.
  * Steps with an "approval_action" only execute if the approval gate holds an
    approved record for (partner, action); otherwise an approval request is
    filed and the step is reported as "blocked_awaiting_approval".
  * Every step is logged. Outputs of earlier steps can feed later inputs via
    "$prev" placeholders.
"""

from tool_registry import ToolError


class WorkflowError(Exception):
    pass


class WorkflowRunner:
    def __init__(self, registry, gate, logger, memory=None):
        self.registry = registry
        self.gate = gate
        self.logger = logger
        self.memory = memory

    def _resolve_input(self, raw_input, prev_output):
        if not isinstance(raw_input, dict):
            return {}
        resolved = {}
        for key, value in raw_input.items():
            if value == "$prev":
                resolved[key] = prev_output
            elif isinstance(value, str) and value.startswith("$prev."):
                field = value.split(".", 1)[1]
                resolved[key] = (prev_output or {}).get(field)
            else:
                resolved[key] = value
        return resolved

    def run(self, partner, workflow_name, extra_input=None):
        workflows = partner.get("workflows", {})
        if workflow_name not in workflows:
            raise WorkflowError("Partner %s has no workflow '%s'"
                                % (partner.id, workflow_name))
        allowed_tools = set(partner.get("tools", []))
        results = []
        prev_output = extra_input or {}
        self.logger.log("workflow_start", partner=partner.id, workflow=workflow_name)

        for i, step in enumerate(workflows[workflow_name], start=1):
            entry = {"step": i, "name": step.get("step", "step %d" % i),
                     "tool": step.get("tool"), "status": None, "output": None}

            approval_action = step.get("approval_action")
            if approval_action and not self.gate.is_approved(partner.id, approval_action):
                request = self.gate.request(partner.id, approval_action,
                                            detail=entry["name"])
                entry["status"] = "blocked_awaiting_approval"
                entry["output"] = {"approval_request": request["id"]}
                self.logger.log("step_blocked", partner=partner.id,
                                workflow=workflow_name, step=entry["name"],
                                approval_request=request["id"])
                results.append(entry)
                continue

            tool_name = step.get("tool")
            if tool_name is None:
                entry["status"] = "note"
                entry["output"] = {"note": step.get("step", "")}
                results.append(entry)
                continue
            if tool_name not in allowed_tools:
                entry["status"] = "denied_tool_not_allowed"
                self.logger.log("step_denied", partner=partner.id,
                                workflow=workflow_name, tool=tool_name)
                results.append(entry)
                continue

            payload = self._resolve_input(step.get("input", {}), prev_output)
            try:
                output = self.registry.run(tool_name, payload)
                entry["status"] = "ok"
                entry["output"] = output
                prev_output = output
            except ToolError as exc:
                entry["status"] = "tool_error"
                entry["output"] = {"error": str(exc)}
            self.logger.log("step_done", partner=partner.id,
                            workflow=workflow_name, step=entry["name"],
                            status=entry["status"])
            results.append(entry)

        if self.memory is not None and partner.get("memory_rules", {}).get("remember_outcomes"):
            ok = sum(1 for r in results if r["status"] == "ok")
            self.memory.remember(partner.id, "last_workflow",
                                 "%s: %d/%d steps ok" % (workflow_name, ok, len(results)))
        self.logger.log("workflow_end", partner=partner.id, workflow=workflow_name,
                        steps=len(results))
        return results
