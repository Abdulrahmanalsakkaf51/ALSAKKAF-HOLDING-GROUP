"""Closed capability manifest including the TRL-R2-002 registry boundary."""

from . import APPLICATION_VERSION, CHECKPOINT_ID, OPERATING_MODE


IMPLEMENTED = (
    "Local application foundation",
    "Local synthetic demonstration",
    "Interactive synthetic charts",
    "Deterministic report display and download",
    "Release 1 kernel integration",
    "Local governed strategy registry",
    "Local immutable strategy-definition vault",
    "Deterministic registry identities",
    "Separate non-executable research backlog",
    "Registry dashboard and read-only API",
)

NOT_IMPLEMENTED = (
    "External/live market data",
    "Forward paper portfolio service",
    "Accounts and authentication",
    "Subscriptions and payments",
    "Customer distribution",
    "Broker credentials",
    "Broker connectivity",
    "Assisted execution",
    "Automated execution",
    "External orders",
    "Customer funds or custody",
    "Personalized investment advice",
    "MT5 integration",
    "News feeds",
    "Strategy optimization",
    "Strategy ranking",
    "Regime selection",
    "Order proposals",
    "Cloud backend",
    "Telemetry and analytics",
    "Customer distribution approval",
)


def capability_manifest():
    """Return a new machine-readable, fail-closed capability manifest."""
    return {
        "application_version": APPLICATION_VERSION,
        "checkpoint": CHECKPOINT_ID,
        "operating_mode": OPERATING_MODE,
        "paper_research_only": True,
        "data_boundary": "COMMITTED_SYNTHETIC_DEMONSTRATION_ONLY",
        "network_boundary": "INBOUND_HTTP_ON_127.0.0.1_ONLY; NO_OUTBOUND_NETWORK",
        "implemented": list(IMPLEMENTED),
        "not_implemented": list(NOT_IMPLEMENTED),
        "execution_capability": False,
        "external_order_capability": False,
        "broker_capability": False,
        "credential_storage_capability": False,
        "telemetry": False,
        "atlas_runtime_dependency": False,
        "strategy_registry_checkpoint": "TRL-R2-002",
        "strategy_registry_capability": True,
        "strategy_vault_capability": True,
        "strategy_ranking_capability": False,
        "strategy_optimization_capability": False,
        "regime_selection_capability": False,
        "live_market_data_capability": False,
        "mt5_capability": False,
        "news_feed_capability": False,
        "order_proposal_capability": False,
        "cloud_backend_capability": False,
        "accounts_capability": False,
        "subscriptions_capability": False,
        "payments_capability": False,
        "customer_distribution_approved": False,
    }
