"""Re-export shim: quote_loader.py now lives in bowaka_common.data.quote_loader.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.data.quote_loader import (  # noqa: F401
    QuoteLoader,
)

__all__ = ['QuoteLoader']
