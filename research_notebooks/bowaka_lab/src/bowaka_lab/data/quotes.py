"""Re-export shim: quotes.py now lives in bowaka_common.data.quotes.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.data.quotes import (  # noqa: F401
    fetch_quotes,
)

__all__ = ['fetch_quotes']
