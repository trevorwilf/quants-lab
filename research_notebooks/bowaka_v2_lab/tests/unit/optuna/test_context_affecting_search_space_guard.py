"""`assert_search_space_does_not_affect_context` refuses context-affecting tunables.

Speedup report §5.2 / §11.2 Phase 2. A precomputed :class:`FoldRuntimeContext`
is only safe when no trial-tuned parameter influences the PIT universe / daily
baselines / scan cadence / minute-window policy. The guard fails closed for
any override that names one of :data:`CONTEXT_AFFECTING_PREFIXES`.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.optuna.fold_context import (
    CONTEXT_AFFECTING_PREFIXES,
    assert_search_space_does_not_affect_context,
)


def test_default_search_space_passes():
    assert_search_space_does_not_affect_context(None)
    assert_search_space_does_not_affect_context({})


@pytest.mark.parametrize(
    "key",
    [
        "universe.min_price",
        "universe.min_adv_dollars",
        "historical_features.volume_curve.bucket_count",
        "market_data.feed",
        "market_data.adjustment",
        "data.lake_root",
        "session.scanner_start",
        "session.scanner_end",
        "session.scan_interval_seconds",
        "simulation.intraday_window_policy",
    ],
)
def test_each_context_prefix_is_refused(key: str):
    with pytest.raises(OptunaStudyInvalidError) as info:
        assert_search_space_does_not_affect_context(
            {key: ("uniform", 1.0, 5.0)}
        )
    msg = str(info.value)
    assert key in msg
    assert "context-affecting" in msg


def test_non_context_key_is_accepted():
    """A signals.* / sizing.* / risk.* override (the legitimate tuning
    surface) does NOT raise."""
    assert_search_space_does_not_affect_context(
        {"signals.gap_pct_max": ("uniform", 0.05, 0.20)}
    )


def test_prefix_constants_match_audit_list():
    assert CONTEXT_AFFECTING_PREFIXES == (
        "universe.",
        "historical_features.",
        "market_data.",
        "data.",
        "session.scanner_start",
        "session.scanner_end",
        "session.scan_interval_seconds",
        "simulation.intraday_window_policy",
    )
