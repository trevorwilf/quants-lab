"""Re-export shim: dataset_hash.py now lives in bowaka_common.storage.dataset_hash.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.storage.dataset_hash import (  # noqa: F401
    PREFIX,
    hash_dataframe,
    hash_parquet_files,
    hash_documents,
)

__all__ = ['PREFIX', 'hash_dataframe', 'hash_parquet_files', 'hash_documents']
