"""Re-export shim: alpaca_client.py now lives in bowaka_common.data.alpaca_client.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.data.alpaca_client import (  # noqa: F401
    FeedUnavailableError,
    AlpacaClientConfig,
    AlpacaClient,
)

__all__ = ['FeedUnavailableError', 'AlpacaClientConfig', 'AlpacaClient']
