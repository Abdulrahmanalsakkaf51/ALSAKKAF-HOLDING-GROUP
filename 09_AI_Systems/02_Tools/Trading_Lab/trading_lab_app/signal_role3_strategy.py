"""Role 3 — Technical Strategy Partner (TRL-R2-006 Section 2).

Runs the selected registered strategy against governed evidence. A pure
function: no timeline, storage, or network access.

SMA-001 reuses ``trading_lab_core.strategy.sma`` and ``sma_cross_signals``
unchanged (the same functions the Release-1 kernel uses), so the crossing
detection itself is byte-for-byte the ported R1 behavior — see
``test_signal_intelligence.py::SMA001ParityTests``. That crossing detection
only ever produced a *direction* (enter/exit/none); R1 never produced an
entry-zone, stop-loss, or TP1-TP4 (it sized positions as a percentage of
equity with no explicit price stop).

**No Founder-approved execution geometry exists for SMA-001 in this
checkpoint.** A repository-wide search (`TRL_DECISION_LOG.md`,
`TRL_BLOCKERS.md`, every R2-006 document) found no dated, citable approval
covering a lookback window, entry-zone rule, stop rule, TP1-TP4 formula,
target allocations, or rounding/tolerance behavior for SMA-001 — the same
absence of approval that already blocks FIB-001. An earlier draft of this
module invented such a geometry (a 20-bar swing stop, 1x/2x/3x/4x targets,
equal 25% allocations) and is corrected here: that geometry has been
removed from every executable code path. A detected BUY/SELL crossing is
now recorded as a non-executable research ``candidate_direction`` only;
Role 3 itself fails closed with reason ``STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED``
whenever a crossing is detected, so the pipeline cannot authorize an
executable BUY/SELL proposal for SMA-001 until a dated Decision Log entry
records an approved geometry (see ``TRL_BLOCKERS.md``). HOLD (no crossing)
and WAIT (insufficient bar history) are unaffected — neither ever needed
execution geometry.

Role 5 (``signal_role5_independent_risk.py``) independently recomputes
position size from a separate implementation whenever geometry is
eventually authorized; that module does not import anything from this one.
"""

from . import signal_strategy_registry
from trading_lab_core.strategy import sma_cross_signals


ROLE_NAME = "technical_strategy"
PASS = "PASS"
NO_STRATEGY_SIGNAL = "NO_STRATEGY_SIGNAL"

REASON_STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED = "STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED"


def _empty_candidate(status, reasons, strategy_version="0.0.0", side=None, candidate_direction=None):
    return {
        "status": status,
        "reasons": reasons,
        "side": side if side is not None else ("HOLD" if status == PASS else None),
        "candidate_direction": candidate_direction,
        "strategy_version": strategy_version,
        "entry_zone_lower": None,
        "entry_zone_upper": None,
        "stop_loss": None,
        "targets": None,
        "target_allocations_percent": None,
        "candidate_quantity": None,
    }


def _sma_parameters(strategy_parameters):
    fast = strategy_parameters.get("fast")
    slow = strategy_parameters.get("slow")
    if (
        isinstance(fast, bool) or isinstance(slow, bool)
        or not isinstance(fast, int) or not isinstance(slow, int)
        or not 1 <= fast < slow
    ):
        return None, None
    return fast, slow


def _evaluate_sma001(request, strategy_version):
    fast, slow = _sma_parameters(request["strategy_parameters"])
    if fast is None:
        return _empty_candidate(NO_STRATEGY_SIGNAL, ["STRATEGY_PARAMETERS_INVALID"], strategy_version)
    bars = request["bar_series"]
    if len(bars) < slow:
        # Evidence exists but is not yet sufficient for this strategy's
        # window: a WAIT outcome (Section 3), not a hard BLOCKED failure —
        # distinct from an unregistered/disabled/unapproved strategy, which
        # is a genuine NO_STRATEGY_SIGNAL failure below.
        return _empty_candidate(
            PASS, ["INSUFFICIENT_BAR_HISTORY_FOR_STRATEGY"], strategy_version,
            side="WAIT", candidate_direction="WAIT",
        )
    ohlcv = [{"date": bar["date"], "close": float(bar["close"])} for bar in bars]
    signals = sma_cross_signals(ohlcv, fast, slow)
    action = signals[-1][1]
    if action == "none":
        return _empty_candidate(PASS, [], strategy_version, side="HOLD", candidate_direction="HOLD")
    # A genuine crossing was detected — this is the exact, unmodified R1
    # crossing-detection result. It is recorded for research traceability
    # only; no execution geometry may be attached to it (see module
    # docstring), so this is a Role 3 failure, not a pass.
    direction = "BUY" if action == "enter" else "SELL"
    return _empty_candidate(
        NO_STRATEGY_SIGNAL,
        [REASON_STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED],
        strategy_version,
        side=None,
        candidate_direction=direction,
    )


def evaluate(request):
    strategy_id = request["strategy_id"]
    allowed, reason = signal_strategy_registry.executable_status(strategy_id)
    if not allowed:
        return _empty_candidate(NO_STRATEGY_SIGNAL, [reason])
    record = signal_strategy_registry.get_strategy(strategy_id)
    if strategy_id == "SMA-001":
        return _evaluate_sma001(request, record["strategy_version"])
    return _empty_candidate(NO_STRATEGY_SIGNAL, ["STRATEGY_NOT_IMPLEMENTED"], record["strategy_version"])


__all__ = (
    "NO_STRATEGY_SIGNAL",
    "PASS",
    "REASON_STRATEGY_EXECUTION_GEOMETRY_NOT_APPROVED",
    "ROLE_NAME",
    "evaluate",
)
