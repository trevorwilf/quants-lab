"""Re-export shim: parquet_store.py now lives in bowaka_common.storage.parquet_store.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.storage.parquet_store import (  # noqa: F401
    PathParts,
    ParquetStore,
)

__all__ = ['PathParts', 'ParquetStore']
