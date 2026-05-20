"""Re-export shim: portfolio_metrics.py now lives in bowaka_common.metrics.portfolio_metrics.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.metrics.portfolio_metrics import (  # noqa: F401
    daily_pnl,
    equity_curve,
    drawdown_stats,
    exposure_summary,
)

__all__ = ['daily_pnl', 'equity_curve', 'drawdown_stats', 'exposure_summary']
