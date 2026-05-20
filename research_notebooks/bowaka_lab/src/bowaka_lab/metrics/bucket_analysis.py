"""Re-export shim: bucket_analysis.py now lives in bowaka_common.metrics.bucket_analysis.


This shim preserves the v1 public import surface during the Phase 2 refactor.

Public objects are *identical* (id() match) to their bowaka_common counterparts.
"""

from bowaka_common.metrics.bucket_analysis import (  # noqa: F401
    flatten_variant_column,
    summarize_by_entry_rule,
    summarize_by_exit_geometry,
    summarize_by_signal_fade_threshold,
)

__all__ = ['flatten_variant_column', 'summarize_by_entry_rule', 'summarize_by_exit_geometry', 'summarize_by_signal_fade_threshold']
