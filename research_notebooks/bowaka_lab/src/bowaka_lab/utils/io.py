"""Re-export shim: io.py now lives in bowaka_common.utils.io.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.utils.io import (  # noqa: F401
    PathResolution,
    PathResolver,
    to_parquet_safe,
)

__all__ = ['PathResolution', 'PathResolver', 'to_parquet_safe']
