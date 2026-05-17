"""Phase 6: bucket boundaries 0-2 / 3-5 / 6-8 / 9+."""

from __future__ import annotations

import pytest

from bowaka_lab.sim.signal_fade import _bucket_for


@pytest.mark.parametrize("score,expected", [(0, "none"), (1, "none"), (2, "none"), (3, "soft"), (5, "soft"), (6, "hard"), (8, "hard"), (9, "critical"), (15, "critical")])
def test_bucket_boundaries(score, expected):
    assert _bucket_for(score) == expected
