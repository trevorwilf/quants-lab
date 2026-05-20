"""Re-export shim: sensitivity.py now lives in bowaka_common.research.sensitivity.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.research.sensitivity import (  # noqa: F401
    SensitivityResult,
    one_at_a_time,
    grouped,
)

__all__ = ['SensitivityResult', 'one_at_a_time', 'grouped']
