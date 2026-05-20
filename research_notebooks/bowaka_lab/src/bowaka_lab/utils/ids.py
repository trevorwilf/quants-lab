"""Re-export shim: ids.py now lives in bowaka_common.utils.ids.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.utils.ids import (  # noqa: F401
    run_id,
    prefilter_run_id,
    trade_id,
    counterfactual_id,
    ingestion_run_id,
    asset_snapshot_id,
)

__all__ = ['run_id', 'prefilter_run_id', 'trade_id', 'counterfactual_id', 'ingestion_run_id', 'asset_snapshot_id']
