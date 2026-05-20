"""Re-export shim: trade_metrics.py now lives in bowaka_common.metrics.trade_metrics.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.metrics.trade_metrics import (  # noqa: F401
    per_trade_metrics,
    summary_stats,
)

__all__ = ['per_trade_metrics', 'summary_stats']
