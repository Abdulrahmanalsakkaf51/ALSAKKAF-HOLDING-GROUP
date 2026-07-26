"""Portable local application layer for ALSAKKAF Trading Research Lab.

Importing this package has no runtime side effects. In particular, it does not
create a socket, open a browser, read the demonstration pack, or run the kernel.
"""

APPLICATION_NAME = "ALSAKKAF Trading Research Lab"
APPLICATION_VERSION = "2.0.0-r2.001"
CHECKPOINT_ID = "TRL-R2-001"
OPERATING_MODE = "PAPER_RESEARCH_DEMONSTRATION"

__all__ = (
    "APPLICATION_NAME",
    "APPLICATION_VERSION",
    "CHECKPOINT_ID",
    "OPERATING_MODE",
)
