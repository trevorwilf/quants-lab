"""Re-export shim: splits.py now lives in bowaka_common.research.splits.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.research.splits import (  # noqa: F401
    WalkForwardSplit,
    WalkForwardPlan,
    WalkForwardSplitter,
)

__all__ = ['WalkForwardSplit', 'WalkForwardPlan', 'WalkForwardSplitter']
