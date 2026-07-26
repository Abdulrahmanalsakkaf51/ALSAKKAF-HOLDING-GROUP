"""Module entry point for the local application.

The small path bootstrap supports invoking this file by absolute path from an
unrelated working directory. Normal package imports remain side-effect free.
"""

import sys
from pathlib import Path


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trading_lab_app.app import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
