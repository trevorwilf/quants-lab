"""Re-export shim: ambiguity.py now lives in bowaka_common.sim.ambiguity.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.sim.ambiguity import (  # noqa: F401
    AmbiguityResolution,
    resolve,
)

__all__ = ['AmbiguityResolution', 'resolve']
