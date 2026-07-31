"""Governed local strategy registry for the signal-intelligence pipeline.

TRL-R2-006 (Phase 4). Distinct from ``trading_lab_app.strategy_registry``,
which is the Release-1 kernel vault registry used by the backtest demo. This
registry describes which strategies the six-role signal pipeline (Role 3,
Technical Strategy Partner) may execute. Every entry below is a literal
dict reviewed like any other source change; nothing here is hot-loaded from
an untrusted path or the filesystem at runtime.
"""

import copy


REGISTRY_SCHEMA_VERSION = "TRL_SIGNAL_STRATEGY_REGISTRY.v1"

IMPLEMENTATION_STATUSES = ("IMPLEMENTED", "PLANNED_NOT_IMPLEMENTED")
APPROVAL_STATUSES = ("EXPERIMENTAL_RESEARCH_ONLY", "APPROVAL_PENDING")

# The stable reason code returned when a caller requests execution of a
# strategy whose exact numeric parameters have not received Founder
# approval (FIB-001). Matches the R2-006 contract's fallback code since no
# more specific contract-defined code exists for this condition.
STRATEGY_PARAMETERS_NOT_APPROVED = "STRATEGY_PARAMETERS_NOT_APPROVED"
STRATEGY_NOT_REGISTERED = "STRATEGY_NOT_REGISTERED"
STRATEGY_DISABLED = "STRATEGY_DISABLED"

_REGISTRY = (
    {
        "strategy_id": "SMA-001",
        "strategy_version": "1.0.0",
        "module_path": "trading_lab_app.signal_role3_strategy",
        "enabled": True,
        "description": (
            "Simple moving-average crossover, ported unchanged in behavior "
            "from the TRL-R1 kernel (trading_lab_core.strategy.sma, "
            "sma_cross_signals): transition-only bullish/bearish crosses, "
            "close-at-time-t signal, independently computed fast/slow "
            "windows, no look-ahead."
        ),
        "parameter_schema": {
            "fast": {"type": "INTEGER", "minimum": 1},
            "slow": {"type": "INTEGER", "minimum": 2, "relation": "GREATER_THAN_FAST"},
        },
        "approval_status": "EXPERIMENTAL_RESEARCH_ONLY",
        "implementation_status": "IMPLEMENTED",
    },
    {
        "strategy_id": "FIB-001",
        "strategy_version": "0.0.0",
        "module_path": None,
        "enabled": False,
        "description": (
            "Fibonacci retracement/extension strategy. Its exact numeric "
            "parameters (which retracement/extension ratios, which "
            "swing-detection rule, which invalidation distance) are not "
            "fixed by TRL_R2_006_SIGNAL_INTELLIGENCE_CONTRACT.md and "
            "require an explicit, dated Founder decision recorded in "
            "TRL_DECISION_LOG.md before implementation begins; see "
            "TRL_BLOCKERS.md. No executable numeric strategy behavior "
            "exists for this checkpoint."
        ),
        "parameter_schema": {},
        "approval_status": "APPROVAL_PENDING",
        "implementation_status": "PLANNED_NOT_IMPLEMENTED",
    },
)


def list_strategies():
    """Return an isolated copy of every registered strategy record."""
    return [copy.deepcopy(record) for record in _REGISTRY]


def get_strategy(strategy_id, strategy_version=None):
    """Return the registry record for strategy_id, or None if unknown."""
    for record in _REGISTRY:
        if record["strategy_id"] != strategy_id:
            continue
        if strategy_version is not None and record["strategy_version"] != strategy_version:
            continue
        return copy.deepcopy(record)
    return None


def executable_status(strategy_id, strategy_version=None):
    """Return (allowed, reason_code) for whether Role 3 may execute this
    strategy right now. reason_code is None when allowed is True."""
    record = get_strategy(strategy_id, strategy_version)
    if record is None:
        return False, STRATEGY_NOT_REGISTERED
    # Checked before the generic enabled/implemented gate below so a
    # strategy blocked specifically on missing Founder-approved numeric
    # parameters (FIB-001) always surfaces the precise, contract-required
    # reason rather than the more generic STRATEGY_DISABLED.
    if record["approval_status"] == "APPROVAL_PENDING":
        return False, STRATEGY_PARAMETERS_NOT_APPROVED
    if not record["enabled"] or record["implementation_status"] != "IMPLEMENTED":
        return False, STRATEGY_DISABLED
    return True, None


__all__ = (
    "APPROVAL_STATUSES",
    "IMPLEMENTATION_STATUSES",
    "REGISTRY_SCHEMA_VERSION",
    "STRATEGY_DISABLED",
    "STRATEGY_NOT_REGISTERED",
    "STRATEGY_PARAMETERS_NOT_APPROVED",
    "executable_status",
    "get_strategy",
    "list_strategies",
)
