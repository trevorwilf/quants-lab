"""range_ladder conservative stress re-score.

Same fill kernel as the base sim, different dials (there is deliberately no
second kernel):

- ``max_fills_per_bar = 1``          (one fill per bar, both sides combined)
- ``cooldown_bars = max(base, 1)``   (at least one full bar between refills)
- ``slip = max(0.001, spread / 2)``  (spread plumbed via
  ``RangeLadderConfig.stress_spread_pct``; default 0 → slip floor 0.001)
- ``body_only`` option               (open→close only, no wick fills)

Mirrors ladder_lab's conservative walk-forward re-score. The stress result
is informational per fold (recorded in trial user_attrs); the fold score
itself comes from the base sim per the Phase A spec.
"""

from __future__ import annotations

from typing import Optional

import numpy as np

from pmm_lab.strategies.range_ladder import RangeLadderConfig
from pmm_lab.strategies.range_ladder_gen import RungSet

STRESS_SLIP_FLOOR = 0.001


def stress_dials(config: RangeLadderConfig, body_only: bool = False) -> dict:
    """Conservative dial set derived from a base config."""
    return dict(
        max_fills_per_bar=1,
        cooldown_bars=max(int(config.cooldown_bars), 1),
        slip=max(STRESS_SLIP_FLOOR, float(config.stress_spread_pct) / 2.0),
        body_only=bool(body_only),
    )


def run_range_ladder_stress(
    candles: np.ndarray,
    config: RangeLadderConfig,
    rungs: RungSet,
    bar_interval_seconds: int,
    body_only: bool = False,
    use_numba: Optional[bool] = None,
) -> dict:
    """Run the conservative re-score on a candle window with fixed rungs.

    Parameters
    ----------
    candles : np.ndarray
        Structured candle array (the fold's TEST slice).
    rungs : RungSet
        The concrete ladder already built at the fold's train anchor — the
        stress run must price the SAME ladder, not rebuild it.
    """
    from pmm_lab.features._numba_range_ladder import run_ladder_sim

    dials = stress_dials(config, body_only=body_only)
    return run_ladder_sim(
        candles["open"], candles["high"], candles["low"], candles["close"],
        rungs.buys, rungs.sells, rungs.buy_weights, rungs.sell_weights,
        fund=config.fund_quote,
        quote_frac=config.quote_frac,
        fee=config.fee,
        slip=dials["slip"],
        cooldown_bars=dials["cooldown_bars"],
        max_fills_per_bar=dials["max_fills_per_bar"],
        body_only=dials["body_only"],
        bar_interval_seconds=bar_interval_seconds,
        use_numba=use_numba,
    )
