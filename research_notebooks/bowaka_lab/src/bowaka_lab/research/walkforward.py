"""Re-export shim: walkforward.py now lives in bowaka_common.research.walkforward.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.research.walkforward import (  # noqa: F401
    FoldResult,
    WalkForwardSummary,
    run_walkforward,
)

__all__ = ['FoldResult', 'WalkForwardSummary', 'run_walkforward']
