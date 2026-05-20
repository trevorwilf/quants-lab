"""Re-export shim: corporate_actions.py now lives in bowaka_common.data.corporate_actions.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.data.corporate_actions import (  # noqa: F401
    detect_split_anomalies,
    compare_raw_vs_split,
    fetch_corporate_actions,
)

__all__ = ['detect_split_anomalies', 'compare_raw_vs_split', 'fetch_corporate_actions']
