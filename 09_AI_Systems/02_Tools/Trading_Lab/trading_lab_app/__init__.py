"""Portable local application layer for ALSAKKAF Trading Research Lab.

Importing this package has no runtime side effects. In particular, it does not
create a socket, open a browser, read the demonstration pack, or run the kernel.
"""

APPLICATION_NAME = "ALSAKKAF Trading Research Lab"
APPLICATION_VERSION = "2.0.0-r2.005"
CHECKPOINT_ID = "TRL-R2-005"
OPERATING_MODE = (
    "LOCAL_RESEARCH_WITH_OPTIONAL_FORWARD_PAPER_TIMELINE_"
    "MT5_READ_ONLY_AND_OFFICIAL_NEWS_METADATA"
)

__all__ = (
    "APPLICATION_NAME",
    "APPLICATION_VERSION",
    "CHECKPOINT_ID",
    "OPERATING_MODE",
)
