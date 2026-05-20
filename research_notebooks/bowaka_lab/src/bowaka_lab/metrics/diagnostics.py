"""Re-export shim: diagnostics.py now lives in bowaka_common.metrics.diagnostics.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.metrics.diagnostics import (  # noqa: F401
    exit_reason_distribution,
    first_touch_summary,
)

__all__ = ['exit_reason_distribution', 'first_touch_summary']
