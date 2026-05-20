"""base/conservative/severe produce strictly increasing slippage on identical inputs."""
from __future__ import annotations

import pytest

from bowaka_v2_lab.sim.cost_model import COST_STRESS_LEVELS, slippage_bps


def test_strictly_increasing_slippage() -> None:
    b = slippage_bps(stress_level="base", adv_participation_frac=0.001)
    c = slippage_bps(stress_level="conservative", adv_participation_frac=0.001)
    s = slippage_bps(stress_level="severe", adv_participation_frac=0.001)
    assert b < c < s


def test_levels_advertised_correctly() -> None:
    assert set(COST_STRESS_LEVELS) == {"base", "conservative", "severe"}


def test_unknown_level_rejected() -> None:
    with pytest.raises(ValueError):
        slippage_bps(stress_level="totally_fake", adv_participation_frac=0.001)


def test_impact_grows_with_participation() -> None:
    low = slippage_bps(stress_level="base", adv_participation_frac=0.001)
    high = slippage_bps(stress_level="base", adv_participation_frac=0.10)
    assert high > low
