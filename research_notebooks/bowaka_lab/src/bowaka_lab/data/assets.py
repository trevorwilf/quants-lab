"""Re-export shim: assets.py now lives in bowaka_common.data.assets.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.data.assets import (  # noqa: F401
    OPERATING_EQUITY,
    LEVERAGED_ETP,
    INVERSE_ETP,
    ETN,
    ETF,
    SPAC,
    PREFERRED,
    UNKNOWN,
    classify_instrument,
    normalize_symbol_key,
    AssetRow,
    build_asset_snapshot,
    assets_to_dataframe,
    load_latest_asset_snapshot,
)

__all__ = ['OPERATING_EQUITY', 'LEVERAGED_ETP', 'INVERSE_ETP', 'ETN', 'ETF', 'SPAC', 'PREFERRED', 'UNKNOWN', 'classify_instrument', 'normalize_symbol_key', 'AssetRow', 'build_asset_snapshot', 'assets_to_dataframe', 'load_latest_asset_snapshot']
