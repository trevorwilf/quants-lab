"""Re-export shim: parquet_io.py now lives in bowaka_common.storage.parquet_io.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.storage.parquet_io import (  # noqa: F401
    load_daily_bars_from_root,
    MinuteBarLoader,
    candidates_dict_to_source,
)

__all__ = ['load_daily_bars_from_root', 'MinuteBarLoader', 'candidates_dict_to_source']
