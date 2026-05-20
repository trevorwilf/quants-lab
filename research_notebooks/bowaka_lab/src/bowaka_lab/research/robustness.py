"""Re-export shim: robustness.py now lives in bowaka_common.research.robustness.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.research.robustness import (  # noqa: F401
    topk_convergence,
    parameter_sensitivity,
)

__all__ = ['topk_convergence', 'parameter_sensitivity']
