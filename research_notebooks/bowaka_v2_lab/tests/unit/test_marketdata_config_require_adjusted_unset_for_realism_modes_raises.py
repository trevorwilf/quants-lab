"""``require_adjusted_daily_bars`` must be explicit for real-mode configs.

Realism remediation 2 Phase 1 (audit §P0-005). The live contract requires
adjusted daily bars; a config in ``intended_realism`` / ``current_code_parity``
that omits ``market_data.require_adjusted_daily_bars`` would silently allow raw
daily baselines. The ``BowakaV2Config`` validator raises in that case;
``smoke_fixture`` keeps the historical ``False`` default; an explicit value is
always honored.
"""
from __future__ import annotations

import pytest
from pydantic import ValidationError

from bowaka_v2_lab.config.models import BowakaV2Config

# A full live signal-gate set — real modes also require every signal threshold.
_FULL_SIGNALS: dict[str, float] = {
    "rvol_so_far_min": 0.7,
    "projected_full_day_rvol_min": 0.5,
    "prior_atr_pct_min": 0.06,
    "range_expansion_so_far_min": 0.5,
    "close_location_so_far_min": 0.6,
    "ema_distance_min": -0.05,
    "ema_slope_min": -0.05,
    "price_min": 1.0,
    "price_max": 20.0,
    "avg_dollar_volume_min": 250000,
    "rvol_so_far_max": 8.0,
    "projected_full_day_rvol_max": 8.0,
    "range_expansion_so_far_max": 2.5,
    "gap_pct_max": 0.25,
    "current_return_pct_max": 0.5,
}

_PATHS = {
    "lab_root": "research_notebooks/bowaka_v2_lab",
    "data_root": "research_notebooks/bowaka_v2_lab/data",
    "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts",
}


def _cfg(*, mode: str, market_data: dict) -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": {"mode": mode},
        "market_data": market_data,
        "signals": dict(_FULL_SIGNALS),
        "paths": dict(_PATHS),
    }


@pytest.mark.parametrize("mode", ["intended_realism", "current_code_parity"])
def test_unset_require_adjusted_raises_for_realism_modes(mode: str) -> None:
    """A real-mode config that omits the flag fails Pydantic validation."""
    with pytest.raises(ValidationError, match="require_adjusted_daily_bars"):
        BowakaV2Config.model_validate(_cfg(mode=mode, market_data={"feed": "sip"}))


@pytest.mark.parametrize("mode", ["intended_realism", "current_code_parity"])
@pytest.mark.parametrize("value", [True, False])
def test_explicit_require_adjusted_is_honored_for_realism_modes(
    mode: str, value: bool
) -> None:
    """An explicit value validates and is preserved verbatim."""
    cfg = BowakaV2Config.model_validate(
        _cfg(mode=mode, market_data={"feed": "sip", "require_adjusted_daily_bars": value})
    )
    assert cfg.market_data.require_adjusted_daily_bars is value


def test_smoke_fixture_unset_resolves_to_false() -> None:
    """smoke_fixture keeps the historical False default when the flag is unset."""
    cfg = BowakaV2Config.model_validate(
        {
            "strategy_id": "bowaka_v2",
            "strategy_version": "0.1.0",
            "simulation": {"mode": "smoke_fixture"},
            "market_data": {"feed": "iex"},
            "paths": dict(_PATHS),
        }
    )
    assert cfg.market_data.require_adjusted_daily_bars is False


def test_require_split_adjustment_and_max_quote_age_defaults() -> None:
    """The new sibling fields have the contract-aligned defaults."""
    cfg = BowakaV2Config.model_validate(
        _cfg(mode="intended_realism", market_data={"feed": "sip",
                                                   "require_adjusted_daily_bars": True})
    )
    assert cfg.market_data.require_split_adjustment is False  # default; opt-in
    assert cfg.market_data.max_quote_age_seconds == 15
