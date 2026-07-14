"""Thin shim exposing Partner Runtime deterministic tools to the benchmark
without importing the whole runtime package layout. Stdlib only."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "Partner_Runtime"))

from tool_registry import (  # noqa: E402,F401
    tool_classify_request as classify_request,
    tool_make_checklist as make_checklist,
    tool_csv_stats as csv_stats,
    tool_summarize_extractive as summarize,
)
