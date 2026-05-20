"""Re-export shim: stress.py now lives in bowaka_common.research.stress.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.research.stress import (  # noqa: F401
    high_vol_sessions,
    low_liquidity_sessions,
    gap_event_sessions,
    slice_trades_to_sessions,
)

__all__ = ['high_vol_sessions', 'low_liquidity_sessions', 'gap_event_sessions', 'slice_trades_to_sessions']
