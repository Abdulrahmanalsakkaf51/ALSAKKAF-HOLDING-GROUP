"""Role 5 — Independent Risk Partner (TRL-R2-006 Section 2, corrected
independence requirement).

This module is deliberately separate from ``signal_role3_strategy.py`` and
MUST NOT import or call anything from it, and MUST NOT accept Role 3's
suggested quantity as an input to its own sizing calculation. It
independently recomputes position size from governed account state, the
active risk-policy hash, and the candidate's entry/stop prices (the stop
*distance*) alone. If its own recomputed quantity disagrees with Role 3's
candidate quantity by more than the documented rounding tolerance
(``risk_policy.quantity_step_tolerance_percent``), that disagreement is
itself a rejection (``SIZE_MISMATCH_BETWEEN_PARTNERS``) — never silently
reconciled by trusting one number over the other.

The only code this module shares with Role 3 is ``paper_data.quantity_floor``,
a bare floor-to-step arithmetic utility with no sizing formula or strategy
decision logic in it (it does not know what "risk percent" or "stop
distance" mean); sharing it does not create a dependency on Role 3's
implementation. This sharing is intentional and documented here per the
R2-006 contract's allowance for "a shared low-level safe numeric utility."
"""

from decimal import Decimal

from .paper_data import quantity_floor
from .timeline_data import canonical_decimal, decimal_value


ROLE_NAME = "independent_risk"
PASS = "PASS"
RISK_REJECTED = "RISK_REJECTED"
SIZE_MISMATCH_BETWEEN_PARTNERS = "SIZE_MISMATCH_BETWEEN_PARTNERS"

REASON_RISK_HALT_ACTIVE = "RISK_HALT_ACTIVE"
REASON_PER_INSTRUMENT_EXPOSURE_LIMIT = "PER_INSTRUMENT_EXPOSURE_LIMIT"
REASON_CORRELATED_EXPOSURE_LIMIT = "CORRELATED_EXPOSURE_LIMIT"
REASON_QUANTITY_BELOW_MINIMUM = "QUANTITY_BELOW_MINIMUM"
REASON_INVALID_STOP_DISTANCE = "INVALID_STOP_DISTANCE"
REASON_RISK_INCREASE_AFTER_LOSS_FORBIDDEN = "RISK_INCREASE_AFTER_LOSS_FORBIDDEN"


def _independent_quantity(entry, stop, metadata, equity, risk_percent):
    """Recompute quantity from first principles: equity x risk% / stop
    distance value, floored to the instrument's quantity step. This is a
    separately implemented evaluation of the same governed formula
    documented in TRL_R2_006_SIGNAL_INTELLIGENCE_CONTRACT.md Section 6.4,
    not a call into Role 3's code."""
    tick_size = decimal_value(metadata["tick_size"])
    tick_value = decimal_value(metadata["tick_value"])
    if tick_size <= 0 or tick_value <= 0:
        return None, REASON_INVALID_STOP_DISTANCE
    distance = abs(entry - stop)
    if distance <= 0:
        return None, REASON_INVALID_STOP_DISTANCE
    value_per_price = tick_value / tick_size
    risk_amount = equity * risk_percent / Decimal("100")
    raw_quantity = risk_amount / (distance * value_per_price)
    quantity = quantity_floor(raw_quantity, metadata["quantity_step"])
    minimum = decimal_value(metadata["minimum_quantity"])
    maximum = decimal_value(metadata["maximum_quantity"])
    if quantity < minimum:
        return None, REASON_QUANTITY_BELOW_MINIMUM
    quantity = min(quantity, maximum)
    return quantity, None


def evaluate(request, candidate_side, candidate_entry, candidate_stop, candidate_quantity):
    """candidate_entry/candidate_stop/candidate_quantity are the raw price
    strings Role 3 proposed; only entry and stop (the stop *distance*) are
    used as calculation inputs. candidate_quantity is used only for the
    final comparison, never fed into this role's own arithmetic."""
    if candidate_side not in ("BUY", "SELL"):
        return {"status": PASS, "reasons": [], "independent_quantity": None}

    account = request["account_state"]
    if account["risk_halt"]:
        return {
            "status": RISK_REJECTED,
            "reasons": [REASON_RISK_HALT_ACTIVE],
            "independent_quantity": None,
        }

    instrument = request["instrument"]
    policy = request["risk_policy"]
    same_instrument = sum(
        1 for position in account["open_positions"] if position["instrument"] == instrument
    )
    if same_instrument:
        return {
            "status": RISK_REJECTED,
            "reasons": [REASON_PER_INSTRUMENT_EXPOSURE_LIMIT],
            "independent_quantity": None,
        }
    correlation_groups = {}
    for position in account["open_positions"]:
        correlation_groups[position["correlation_group"]] = (
            correlation_groups.get(position["correlation_group"], 0) + 1
        )
    max_correlated = policy["maximum_correlated_positions"]
    if any(count >= max_correlated for count in correlation_groups.values()):
        return {
            "status": RISK_REJECTED,
            "reasons": [REASON_CORRELATED_EXPOSURE_LIMIT],
            "independent_quantity": None,
        }
    if account["last_closed_trade_realized_pnl_negative"]:
        prior_risk = account["last_closed_trade_risk_percent"]
        if prior_risk is not None and decimal_value(policy["risk_percent"]) > decimal_value(prior_risk):
            return {
                "status": RISK_REJECTED,
                "reasons": [REASON_RISK_INCREASE_AFTER_LOSS_FORBIDDEN],
                "independent_quantity": None,
            }

    metadata = request["market_observation"]["instrument_metadata"]
    entry = decimal_value(candidate_entry)
    stop = decimal_value(candidate_stop)
    equity = decimal_value(account["equity"])
    risk_percent = decimal_value(policy["risk_percent"])
    independent_quantity, reason = _independent_quantity(entry, stop, metadata, equity, risk_percent)
    if independent_quantity is None:
        return {"status": RISK_REJECTED, "reasons": [reason], "independent_quantity": None}

    tolerance_pct = decimal_value(policy["quantity_step_tolerance_percent"])
    role3_quantity = decimal_value(candidate_quantity)
    if role3_quantity <= 0:
        allowed_delta = decimal_value(metadata["quantity_step"])
    else:
        allowed_delta = role3_quantity * tolerance_pct / Decimal("100")
        allowed_delta = max(allowed_delta, decimal_value(metadata["quantity_step"]))
    if abs(independent_quantity - role3_quantity) > allowed_delta:
        return {
            "status": SIZE_MISMATCH_BETWEEN_PARTNERS,
            "reasons": [SIZE_MISMATCH_BETWEEN_PARTNERS],
            "independent_quantity": canonical_decimal(independent_quantity),
        }
    return {
        "status": PASS,
        "reasons": [],
        "independent_quantity": canonical_decimal(independent_quantity),
    }


__all__ = ("PASS", "RISK_REJECTED", "ROLE_NAME", "SIZE_MISMATCH_BETWEEN_PARTNERS", "evaluate")
