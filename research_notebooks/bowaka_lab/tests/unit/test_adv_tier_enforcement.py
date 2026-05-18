"""Phase fidelity-5: ADV tier enforcement (walks top-to-bottom, reject_if_below)."""

from __future__ import annotations

import pandas as pd

from bowaka_lab.config.models import (
    AdvTierCap,
    BowakaBacktestConfig,
    RealismConfig,
)
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester


_FIVE_TIERS = [
    AdvTierCap(max_adv_dollars=250_000, reject_if_below=True),
    AdvTierCap(max_adv_dollars=500_000, max_position_as_adv_frac=0.003),
    AdvTierCap(max_adv_dollars=1_000_000, max_position_as_adv_frac=0.005),
    AdvTierCap(max_adv_dollars=5_000_000, max_position_as_adv_frac=0.010),
    AdvTierCap(max_adv_dollars=None, max_position_as_adv_frac=0.015),
]


def _cfg(realism: RealismConfig | None = None):
    return BowakaBacktestConfig.model_validate(
        {
            "data": {"vendor": "alpaca", "feed": "iex",
                     "start_date": "2026-05-11", "end_date": "2026-05-12"},
        }
    ).model_copy(update={"realism": realism or RealismConfig(adv_tier_caps=_FIVE_TIERS)})


def _runner():
    cfg = _cfg()
    return BowakaPortfolioBacktester(
        cfg,
        candidate_source=lambda sd: pd.DataFrame(),
        minute_bars_for=lambda td, syms: pd.DataFrame(),
    )


def test_adv_tier_reject_below_thin_threshold():
    runner = _runner()
    qty, diag = runner._maybe_apply_realism_cap(
        qty=1000, candidate={"avg_dollar_volume": 150_000, "close": 5.0},
        realism=runner.cfg.realism,
    )
    assert qty == 0
    assert diag["adv_cap_reason"] == "adv_below_tier_threshold"
    assert diag["adv_tier_index"] == 0


def test_adv_tier_matches_3M_bucket():
    runner = _runner()
    qty, diag = runner._maybe_apply_realism_cap(
        qty=10_000, candidate={"avg_dollar_volume": 3_000_000, "close": 5.0},
        realism=runner.cfg.realism,
    )
    # Tier index 3 ($1M-$5M): max_position_as_adv_frac=0.010 → max_dollars=30k → max_qty=6000
    assert diag["adv_tier_index"] == 3
    assert qty == 6000


def test_adv_tier_catch_all_for_large_caps():
    runner = _runner()
    qty, diag = runner._maybe_apply_realism_cap(
        qty=1_000_000, candidate={"avg_dollar_volume": 10_000_000, "close": 5.0},
        realism=runner.cfg.realism,
    )
    # Last tier (null catch-all): 0.015 → 150k dollars → 30000 qty
    assert diag["adv_tier_index"] == 4
    assert qty == 30_000


def test_adv_tier_falls_back_to_flat_cap_when_tiers_empty():
    cfg = _cfg(realism=RealismConfig(adv_tier_caps=[], max_position_as_adv_frac=0.02))
    runner = BowakaPortfolioBacktester(
        cfg, candidate_source=lambda sd: pd.DataFrame(),
        minute_bars_for=lambda td, syms: pd.DataFrame(),
    )
    qty, diag = runner._maybe_apply_realism_cap(
        qty=100_000, candidate={"avg_dollar_volume": 5_000_000, "close": 5.0},
        realism=runner.cfg.realism,
    )
    # flat cap: 5M * 0.02 = 100k dollars; close 5.0 → max_qty = 20000.
    # min(qty=100000, max_qty=20000) = 20000.
    assert qty == 20_000
    assert diag["adv_tier_index"] is None
    assert diag["adv_cap_dollars"] == 100_000.0


def test_adv_diag_missing_adv():
    runner = _runner()
    qty, diag = runner._maybe_apply_realism_cap(
        qty=100, candidate={"avg_dollar_volume": 0.0, "close": 5.0},
        realism=runner.cfg.realism,
    )
    assert qty == 100
    assert diag["adv_cap_reason"] == "missing_adv"


def test_min_order_notional_blocks_tiny_qty():
    """Phase fidelity-5: min_order_notional applies in _qty_for."""
    cfg = BowakaBacktestConfig.model_validate(
        {
            "data": {"vendor": "alpaca", "feed": "iex",
                     "start_date": "2026-05-11", "end_date": "2026-05-12"},
            "portfolio": {
                "sizing_mode": "legacy_fixed_notional",
                "per_trade_notional": 100,  # tiny
                "min_order_notional": 500,
            },
        }
    )
    runner = BowakaPortfolioBacktester(
        cfg, candidate_source=lambda sd: pd.DataFrame(),
        minute_bars_for=lambda td, syms: pd.DataFrame(),
    )
    runner._cached_per_trade_dollars = 100.0
    qty = runner._qty_for(
        entry_price=10.0, portfolio=cfg.portfolio,
        exits=cfg.exits, candidate={"close": 10.0},
    )
    assert qty == 0  # 100 / 10 = 10 shares → notional = 100 < 500 → reject
