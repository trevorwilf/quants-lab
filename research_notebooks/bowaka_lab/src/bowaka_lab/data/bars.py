"""Re-export shim: bars.py now lives in bowaka_common.data.bars.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.data.bars import (  # noqa: F401
    fetch_daily_bars,
    fetch_minute_bars,
)

__all__ = ['fetch_daily_bars', 'fetch_minute_bars']
