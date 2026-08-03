"""Risk policy, lot sizing, and hard caps for ALSAKKAF SCALPING
(TRL-R2-012 contract Sections 11-13).

Every calculation uses ``Decimal``. Every function fails closed
(raises ``ScalpingRiskError``) rather than silently proceeding when an
input needed to prove a safe result is missing or non-finite. Lot size is
always a pure function of current equity, the configured risk percentage,
and the plan's own stop-loss geometry -- never of prior cycle outcome, so
martingale / lot-escalation-after-loss is structurally impossible.
"""

from decimal import Decimal, ROUND_DOWN

from .alsakkaf_scalping_data import ScalpingDataValidationError


class ScalpingRiskError(ScalpingDataValidationError):
    """Raised when a safe risk/lot result cannot be proven."""


# Safe defaults (contract Section 11).
DEFAULT_RISK_PER_CYCLE_PCT = Decimal("0.25")
DEFAULT_MAX_TOTAL_ACTIVE_RISK_PCT = Decimal("0.50")
DEFAULT_MAX_DAILY_LOSS_PCT = Decimal("1.00")
DEFAULT_MAX_SESSION_DRAWDOWN_PCT = Decimal("2.00")
DEFAULT_MAX_CONSECUTIVE_LOSSES = 3
DEFAULT_COOLDOWN_MINUTES = 15
DEFAULT_MAX_OPEN_POSITIONS = 3
DEFAULT_MAX_PENDING_ORDERS = 6
DEFAULT_MARKET_OPEN_COOLDOWN_MINUTES = 10
DEFAULT_SCALPING_MAX_HOLDING_MINUTES = 30
DEFAULT_INTRADAY_MAX_HOLDING_MINUTES = 8 * 60
DEFAULT_SCALPING_PENDING_EXPIRY_MINUTES = 5
DEFAULT_INTRADAY_PENDING_EXPIRY_MINUTES = 30

# Hard V0 caps (contract Section 11) -- the dashboard can reduce risk but
# never exceed these.
HARD_MAX_RISK_PER_CYCLE_PCT = Decimal("0.50")
HARD_MAX_TOTAL_ACTIVE_RISK_PCT = Decimal("1.00")
HARD_MAX_DAILY_LOSS_PCT = Decimal("2.00")
HARD_MAX_SESSION_DRAWDOWN_PCT = Decimal("3.00")
HARD_MAX_CONSECUTIVE_LOSSES = 3
HARD_MIN_COOLDOWN_MINUTES = 15
HARD_MAX_OPEN_POSITIONS = 5
HARD_MAX_PENDING_ORDERS = 8
HARD_MIN_MARKET_OPEN_COOLDOWN_MINUTES = 10
HARD_MAX_SCALPING_HOLDING_MINUTES = 30
HARD_MAX_INTRADAY_HOLDING_MINUTES = 8 * 60
HARD_MAX_SCALPING_PENDING_EXPIRY_MINUTES = 15
HARD_MAX_INTRADAY_PENDING_EXPIRY_MINUTES = 60

MAX_LADDER_ORDERS = 6
MAX_LADDER_ORDERS_PER_SIDE = 3


def default_risk_settings():
    return {
        "risk_per_cycle_pct": DEFAULT_RISK_PER_CYCLE_PCT,
        "max_total_active_risk_pct": DEFAULT_MAX_TOTAL_ACTIVE_RISK_PCT,
        "max_daily_loss_pct": DEFAULT_MAX_DAILY_LOSS_PCT,
        "max_session_drawdown_pct": DEFAULT_MAX_SESSION_DRAWDOWN_PCT,
        "max_consecutive_losses": DEFAULT_MAX_CONSECUTIVE_LOSSES,
        "cooldown_minutes": DEFAULT_COOLDOWN_MINUTES,
        "max_open_positions": DEFAULT_MAX_OPEN_POSITIONS,
        "max_pending_orders": DEFAULT_MAX_PENDING_ORDERS,
        "market_open_cooldown_minutes": DEFAULT_MARKET_OPEN_COOLDOWN_MINUTES,
        "scalping_max_holding_minutes": DEFAULT_SCALPING_MAX_HOLDING_MINUTES,
        "intraday_max_holding_minutes": DEFAULT_INTRADAY_MAX_HOLDING_MINUTES,
        "scalping_pending_expiry_minutes": DEFAULT_SCALPING_PENDING_EXPIRY_MINUTES,
        "intraday_pending_expiry_minutes": DEFAULT_INTRADAY_PENDING_EXPIRY_MINUTES,
    }


def validate_risk_settings(settings):
    """Fail closed (never clamp) when a setting exceeds its hard cap."""
    checks = (
        ("risk_per_cycle_pct", HARD_MAX_RISK_PER_CYCLE_PCT, True),
        ("max_total_active_risk_pct", HARD_MAX_TOTAL_ACTIVE_RISK_PCT, True),
        ("max_daily_loss_pct", HARD_MAX_DAILY_LOSS_PCT, True),
        ("max_session_drawdown_pct", HARD_MAX_SESSION_DRAWDOWN_PCT, True),
        ("max_consecutive_losses", HARD_MAX_CONSECUTIVE_LOSSES, False),
        ("max_open_positions", HARD_MAX_OPEN_POSITIONS, False),
        ("max_pending_orders", HARD_MAX_PENDING_ORDERS, False),
        ("scalping_max_holding_minutes", HARD_MAX_SCALPING_HOLDING_MINUTES, False),
        ("intraday_max_holding_minutes", HARD_MAX_INTRADAY_HOLDING_MINUTES, False),
        ("scalping_pending_expiry_minutes", HARD_MAX_SCALPING_PENDING_EXPIRY_MINUTES, False),
        ("intraday_pending_expiry_minutes", HARD_MAX_INTRADAY_PENDING_EXPIRY_MINUTES, False),
    )
    for key, cap, is_decimal in checks:
        if key not in settings:
            raise ScalpingRiskError("risk setting {} is missing".format(key))
        value = Decimal(str(settings[key])) if is_decimal else settings[key]
        cap_value = cap if is_decimal else cap
        if is_decimal:
            if value < 0 or value > cap_value:
                raise ScalpingRiskError("SCALPING_RISK_SETTING_EXCEEDS_HARD_CAP:{}".format(key))
        else:
            if not isinstance(value, int) or isinstance(value, bool) or value < 1 or value > cap_value:
                raise ScalpingRiskError("SCALPING_RISK_SETTING_EXCEEDS_HARD_CAP:{}".format(key))
    for minimum_key, minimum_value in (
        ("cooldown_minutes", HARD_MIN_COOLDOWN_MINUTES),
        ("market_open_cooldown_minutes", HARD_MIN_MARKET_OPEN_COOLDOWN_MINUTES),
    ):
        value = settings.get(minimum_key)
        if not isinstance(value, int) or isinstance(value, bool) or value < minimum_value:
            raise ScalpingRiskError("SCALPING_RISK_SETTING_BELOW_HARD_MINIMUM:{}".format(minimum_key))
    return dict(settings)


def floor_to_step(value, step):
    value, step = Decimal(str(value)), Decimal(str(step))
    if step <= 0:
        raise ScalpingRiskError("SCALPING_LOT_CALCULATION_UNPROVABLE")
    steps = (value / step).to_integral_value(rounding=ROUND_DOWN)
    return steps * step


def calculate_lots(equity, risk_per_cycle_pct, entry_price, stop_price, symbol_info):
    """Contract Section 11.1 -- fails closed rather than ever silently
    exceeding the calculated risk budget."""
    try:
        equity = Decimal(str(equity))
        risk_per_cycle_pct = Decimal(str(risk_per_cycle_pct))
        entry_price = Decimal(str(entry_price))
        stop_price = Decimal(str(stop_price))
        tick_value = Decimal(str(symbol_info["tick_value"]))
        tick_size = Decimal(str(symbol_info["tick_size"]))
        volume_min = Decimal(str(symbol_info["volume_minimum"]))
        volume_max = Decimal(str(symbol_info["volume_maximum"]))
        volume_step = Decimal(str(symbol_info["volume_step"]))
    except (KeyError, TypeError, ValueError, ArithmeticError) as error:
        raise ScalpingRiskError("SCALPING_LOT_CALCULATION_UNPROVABLE") from error

    stop_distance = abs(entry_price - stop_price)
    if stop_distance <= 0 or tick_size <= 0 or tick_value <= 0 or volume_step <= 0:
        raise ScalpingRiskError("SCALPING_LOT_CALCULATION_UNPROVABLE")

    risk_amount = equity * (risk_per_cycle_pct / Decimal("100"))
    value_per_point = tick_value / tick_size
    raw_lots = risk_amount / (stop_distance * value_per_point)
    lots = floor_to_step(raw_lots, volume_step)

    if lots < volume_min:
        raise ScalpingRiskError("SCALPING_LOT_BELOW_BROKER_MINIMUM")
    if lots > volume_max:
        lots = volume_max
        resulting_risk = lots * stop_distance * value_per_point
        if resulting_risk > risk_amount:
            raise ScalpingRiskError("SCALPING_LOT_CANNOT_BE_BOUNDED_TO_RISK")

    return {"lots": lots, "risk_amount": risk_amount}


def divide_ladder_risk(risk_amount, order_count):
    """Contract Section 12.1 -- equal per-order share; residual from
    step-rounding is a caller-tracked remainder, never redistributed."""
    risk_amount = Decimal(str(risk_amount))
    if order_count < 1 or order_count > MAX_LADDER_ORDERS:
        raise ScalpingRiskError("SCALPING_LADDER_ORDER_COUNT_OUT_OF_BOUNDS")
    return risk_amount / Decimal(order_count)


def ladder_distance_floor(entry_timeframe_atr, current_spread, broker_minimum_stop_distance, one_broker_point):
    values = [
        Decimal("0.25") * Decimal(str(entry_timeframe_atr)),
        Decimal("2") * Decimal(str(current_spread)),
        Decimal(str(broker_minimum_stop_distance)),
        Decimal(str(one_broker_point)),
    ]
    return max(values)


def cap_same_direction_orders(risk_amount, ordered_orders_by_distance):
    """Contract Section 12.2 -- keep same-direction orders in ascending
    distance from the fill price while cumulative risk stays within the
    cycle budget; cancel (never resize) any order that would breach it."""
    risk_amount = Decimal(str(risk_amount))
    kept, cancelled = [], []
    cumulative = Decimal("0")
    for order in ordered_orders_by_distance:
        order_risk = Decimal(str(order["risk_amount"]))
        if cumulative + order_risk <= risk_amount:
            cumulative += order_risk
            kept.append(order)
        else:
            cancelled.append(order)
    return {"kept": kept, "cancelled": cancelled}


def daily_loss_breached(realized_and_unrealized_loss, start_of_day_equity, max_daily_loss_pct):
    loss = Decimal(str(realized_and_unrealized_loss))
    equity = Decimal(str(start_of_day_equity))
    cap = Decimal(str(max_daily_loss_pct))
    if equity <= 0:
        raise ScalpingRiskError("SCALPING_RISK_CALCULATION_UNPROVABLE")
    return (loss / equity) * Decimal("100") >= cap


def session_drawdown_breached(peak_equity, current_equity, max_drawdown_pct):
    peak_equity = Decimal(str(peak_equity))
    current_equity = Decimal(str(current_equity))
    cap = Decimal(str(max_drawdown_pct))
    if peak_equity <= 0:
        raise ScalpingRiskError("SCALPING_RISK_CALCULATION_UNPROVABLE")
    drawdown_pct = ((peak_equity - current_equity) / peak_equity) * Decimal("100")
    return drawdown_pct >= cap


__all__ = (
    "HARD_MAX_CONSECUTIVE_LOSSES",
    "HARD_MAX_DAILY_LOSS_PCT",
    "HARD_MAX_OPEN_POSITIONS",
    "HARD_MAX_PENDING_ORDERS",
    "HARD_MAX_RISK_PER_CYCLE_PCT",
    "HARD_MAX_SESSION_DRAWDOWN_PCT",
    "HARD_MAX_TOTAL_ACTIVE_RISK_PCT",
    "MAX_LADDER_ORDERS",
    "MAX_LADDER_ORDERS_PER_SIDE",
    "ScalpingRiskError",
    "calculate_lots",
    "cap_same_direction_orders",
    "daily_loss_breached",
    "default_risk_settings",
    "divide_ladder_risk",
    "floor_to_step",
    "ladder_distance_floor",
    "session_drawdown_breached",
    "validate_risk_settings",
)
