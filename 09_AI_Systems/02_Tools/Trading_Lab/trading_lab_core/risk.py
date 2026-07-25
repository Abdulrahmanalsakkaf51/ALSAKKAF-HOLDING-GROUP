# -*- coding: utf-8 -*-
"""System-owned risk limits, stricter policies, and authorization gates."""

from .canonical import _finite_float, _is_number
from .constants import (
    BLOCKED_INCREASE_TO_LOSER,
    BLOCKED_POSITION_LIMIT,
    DRAWDOWN_HALT_PCT,
    MAX_OPEN_POSITIONS,
    MAX_POSITION_PCT,
    NO_TRADE_ALREADY_POSITIONED,
)
from .validation import _field_list

class RiskPolicyViolation(Exception):
    """Raised by the legacy decision-log helper for invalid human decisions."""

def _system_risk_limits():
    return {
        "max_position_pct": MAX_POSITION_PCT,
        "drawdown_halt_pct": DRAWDOWN_HALT_PCT,
        "max_open_positions": MAX_OPEN_POSITIONS,
        "leverage_allowed": False,
        "shorting_allowed": False,
        "increase_to_loser_allowed": False,
    }


def _effective_policy(risk_policy, strategy):
    policy = _system_risk_limits()
    if risk_policy is not None:
        if type(risk_policy) is not dict:
            return None, [
                "risk_policy must be an exact built-in dictionary when supplied"
            ]
        if not all(type(key) is str for key in risk_policy):
            return None, ["risk-policy field names must be exact built-in strings"]
        unsupported = set(risk_policy) - {"max_position_pct", "drawdown_halt_pct"}
        if unsupported:
            return None, ["unsupported risk-policy fields: %s" %
                          _field_list(unsupported)]
        if "max_position_pct" in risk_policy:
            value = risk_policy["max_position_pct"]
            safe_value = _finite_float(value)
            if (safe_value is None or safe_value <= 0
                    or safe_value > MAX_POSITION_PCT):
                return None, ["risk_policy cannot raise or invalidate max_position_pct"]
            policy["max_position_pct"] = safe_value
        if "drawdown_halt_pct" in risk_policy:
            value = risk_policy["drawdown_halt_pct"]
            safe_value = _finite_float(value)
            if (safe_value is None or safe_value >= 0
                    or safe_value < DRAWDOWN_HALT_PCT):
                return None, ["risk_policy cannot weaken or invalidate drawdown_halt_pct"]
            policy["drawdown_halt_pct"] = safe_value
    if strategy and "drawdown_halt_pct" in strategy:
        policy["drawdown_halt_pct"] = max(
            policy["drawdown_halt_pct"], float(strategy["drawdown_halt_pct"])
        )
    return policy, []

def check_entry_allowed(open_positions, last_loss_size_pct, symbol,
                        asset_class, size_pct, policy=None):
    """Pure risk gate retained for focused tests; run policy stays system-owned."""
    del asset_class
    effective_max = MAX_POSITION_PCT
    if policy and _is_number(policy.get("max_position_pct")):
        effective_max = min(effective_max, policy["max_position_pct"])
    if size_pct > effective_max:
        return False, BLOCKED_POSITION_LIMIT
    if open_positions:
        return False, NO_TRADE_ALREADY_POSITIONED
    prior_loss = last_loss_size_pct.get(symbol)
    if prior_loss is not None and size_pct > prior_loss:
        return False, BLOCKED_INCREASE_TO_LOSER
    return True, None


def drawdown_halt_triggered(drawdown_pct, halt_threshold_pct, already_halted):
    """Authorize the one-way transition into a mark-to-market risk halt."""
    return not already_halted and drawdown_pct <= halt_threshold_pct

def decision_log_entry(decision_id, input_packs, manager_proposal, bull_ref,
                       bear_ref, unknowns, human_decision, human_name,
                       risk_checks):
    """Construct a passive human decision record; never decide automatically."""
    if human_decision not in ("ACCEPT", "REJECT", "PENDING"):
        raise RiskPolicyViolation(
            "human_decision must be ACCEPT, REJECT, or PENDING - never auto-set"
        )
    return {
        "decision_id": decision_id,
        "input_packs": input_packs,
        "manager_proposal": manager_proposal,
        "bull_case_ref": bull_ref,
        "bear_case_ref": bear_ref,
        "unknowns": unknowns,
        "human_decision": human_decision,
        "human_name": human_name,
        "risk_policy_checks": risk_checks,
    }
