"""Phase fidelity-6: lab ``compute_source_fade_score`` matches source.

Source ``compute_fade_score`` lives in
``reference/source_strategy/scripts/bowaka_strategy.py``. Importing that
module triggers ``alpaca`` deps, so we copy the function verbatim into
``tests/fixtures/source_compute_fade.py`` and exercise both.
"""

from __future__ import annotations

import pytest

from bowaka_lab.sim.source_signal_fade import (
    compute_source_fade_score,
    source_fade_score_to_band,
)
from tests.fixtures.source_compute_fade import (
    compute_fade_score as src_compute_fade_score,
    fade_score_to_band as src_fade_score_to_band,
)


SIGNAL_GATES = {
    "rvol_min": 1.5,
    "atr_pct_min": 0.06,
    "range_expansion_min": 1.25,
    "close_location_min": 0.60,
    "ema_distance_min": 0.0,
    "ema_slope_min": 0.0,
}


CASES = [
    # All gates pass → score 0
    ("all_pass",
     {"rvol": 2.0, "atr_pct": 0.10, "range_expansion": 1.5, "close_location": 0.8,
      "ema_distance": 0.05, "ema_slope": 0.02}),
    # 3/6 fail → score 0.5
    ("three_fail",
     {"rvol": 1.0, "atr_pct": 0.05, "range_expansion": 1.0, "close_location": 0.8,
      "ema_distance": 0.05, "ema_slope": 0.02}),
    # All 6 fail → score 1.0
    ("all_fail",
     {"rvol": 1.0, "atr_pct": 0.05, "range_expansion": 1.0, "close_location": 0.5,
      "ema_distance": -0.05, "ema_slope": -0.02}),
    # Missing feature counts as fail
    ("missing_feature_fails",
     {"rvol": 2.0, "atr_pct": None, "range_expansion": 1.5, "close_location": 0.8,
      "ema_distance": 0.05, "ema_slope": 0.02}),
]


@pytest.mark.parametrize("label,features", [pytest.param(*c, id=c[0]) for c in CASES])
def test_source_fade_score_matches_source(label, features):
    lab_score, lab_components = compute_source_fade_score(features, SIGNAL_GATES)
    src_score, src_components = src_compute_fade_score(features, SIGNAL_GATES)
    assert lab_score == pytest.approx(src_score)
    assert lab_components == src_components


def test_source_fade_band_boundaries():
    """Source semantics: lower edge is inclusive for the band assignment."""
    assert source_fade_score_to_band(0.33) == "hold"
    assert source_fade_score_to_band(0.34) == "soft"
    assert source_fade_score_to_band(0.50) == "hard"
    assert source_fade_score_to_band(0.67) == "critical"
    assert source_fade_score_to_band(1.0) == "critical"


def test_source_fade_band_custom_thresholds():
    assert source_fade_score_to_band(0.5, soft=0.2, hard=0.6, critical=0.9) == "soft"
    assert source_fade_score_to_band(0.7, soft=0.2, hard=0.6, critical=0.9) == "hard"


@pytest.mark.parametrize("score", [0.0, 0.25, 0.5, 0.75, 1.0])
def test_band_matches_source(score):
    assert source_fade_score_to_band(score) == src_fade_score_to_band(score)
