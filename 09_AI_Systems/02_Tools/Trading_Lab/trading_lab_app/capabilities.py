"""Closed capability manifest for the TRL-R2-001 application boundary."""

from . import APPLICATION_VERSION, CHECKPOINT_ID, OPERATING_MODE


IMPLEMENTED = (
    "Local application foundation",
    "Local synthetic demonstration",
    "Interactive synthetic charts",
    "Deterministic report display and download",
    "Release 1 kernel integration",
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
    }
