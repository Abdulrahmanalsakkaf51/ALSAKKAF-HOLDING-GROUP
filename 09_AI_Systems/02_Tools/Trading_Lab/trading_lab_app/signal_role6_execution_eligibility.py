"""Role 6 — Execution Eligibility Partner (TRL-R2-006 Section 2).

Final deterministic gate: instrument allowlist/broker mapping, spread,
market-hours/session, account risk-halt state. This is the last role in
the pipeline and its output is only a *proposal* eligibility status — it
never calls ``order_check``, ``order_send``, or any broker/MT5 function,
and it cannot authorize execution by itself.
"""

from .timeline_data import decimal_value


ROLE_NAME = "execution_eligibility"
PASS = "PASS"
EXECUTION_INELIGIBLE = "EXECUTION_INELIGIBLE"

REASON_INSTRUMENT_NOT_ALLOWLISTED = "INSTRUMENT_NOT_ALLOWLISTED"
REASON_SPREAD_EXCEEDS_MAXIMUM = "SPREAD_EXCEEDS_MAXIMUM"
REASON_MARKET_SESSION_CLOSED = "MARKET_SESSION_CLOSED"
REASON_ACCOUNT_RISK_HALT = "ACCOUNT_RISK_HALT"


def evaluate(request, candidate_side):
    reasons = []
    if not request["instrument_allowlisted"]:
        reasons.append(REASON_INSTRUMENT_NOT_ALLOWLISTED)
    if request["account_state"]["risk_halt"]:
        reasons.append(REASON_ACCOUNT_RISK_HALT)
    if candidate_side in ("BUY", "SELL"):
        spread = decimal_value(request["market_observation"]["spread"])
        max_spread = decimal_value(request["risk_policy"]["maximum_spread"])
        if spread > max_spread:
            reasons.append(REASON_SPREAD_EXCEEDS_MAXIMUM)
        if request["session_window"]["status"] != "OPEN":
            reasons.append(REASON_MARKET_SESSION_CLOSED)
    status = EXECUTION_INELIGIBLE if reasons else PASS
    return {"status": status, "reasons": reasons}


__all__ = ("EXECUTION_INELIGIBLE", "PASS", "ROLE_NAME", "evaluate")
