"""Re-export shim: schemas.py now lives in bowaka_common.data.schemas.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.data.schemas import (  # noqa: F401
    asset_snapshot_doc,
    asset_row_doc,
    ingestion_run_doc,
    candidate_v2_doc,
    candidate_v3_doc,
    build_candidate_v2,
    build_candidate_v3,
)

__all__ = ['asset_snapshot_doc', 'asset_row_doc', 'ingestion_run_doc', 'candidate_v2_doc', 'candidate_v3_doc', 'build_candidate_v2', 'build_candidate_v3']
