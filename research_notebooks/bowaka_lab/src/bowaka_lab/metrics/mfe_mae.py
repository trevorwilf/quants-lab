"""Re-export shim: mfe_mae.py now lives in bowaka_common.metrics.mfe_mae.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.metrics.mfe_mae import (  # noqa: F401
    MFEMAEResult,
    compute_mfe_mae,
)

__all__ = ['MFEMAEResult', 'compute_mfe_mae']
