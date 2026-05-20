"""Re-export shim: rate_limit.py now lives in bowaka_common.data.rate_limit.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.data.rate_limit import (  # noqa: F401
    TokenBucket,
)

__all__ = ['TokenBucket']
