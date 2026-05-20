"""Re-export shim: artifacts.py now lives in bowaka_common.utils.artifacts.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.utils.artifacts import (  # noqa: F401
    ArtifactPaths,
    save_json,
    load_json,
    save_parquet,
    load_parquet,
    artifact_exists,
)

__all__ = ['ArtifactPaths', 'save_json', 'load_json', 'save_parquet', 'load_parquet', 'artifact_exists']
