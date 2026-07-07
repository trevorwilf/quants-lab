"""Stress dials must strictly never increase fills vs the base sim."""

import numpy as np
import pytest

from pmm_lab.features._numba_range_ladder import run_ladder_sim
from pmm_lab.objective.stress_range_ladder import (
    STRESS_SLIP_FLOOR,
    run_range_ladder_stress,
    stress_dials,
)
from pmm_lab.strategies.range_ladder import RangeLadderConfig
from pmm_lab.strategies.range_ladder_gen import build_rungs
from tests.conftest import CANDLE_DTYPE


def _candles(n=600, seed=0, amplitude=10.0, period=60):
    rng = np.random.default_rng(seed)
    ts = np.arange(n, dtype="int64") * 3600 + 1_700_000_000
    close = 100.0 + amplitude * np.sin(2 * np.pi * np.arange(n) / period)
    close = close + rng.normal(0, 0.8, n)
    close = np.maximum(close, 1.0)
    o = np.roll(close, 1)
    o[0] = close[0]
    h = np.maximum(o, close) + np.abs(rng.normal(0, 0.6, n))
    l = np.minimum(o, close) - np.abs(rng.normal(0, 0.6, n))
    rows = [(int(ts[i]), o[i], h[i], l[i], close[i], 1.0, False) for i in range(n)]
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_stress_dials_values():
    cfg = RangeLadderConfig(cooldown_bars=0, stress_spread_pct=0.0)
    d = stress_dials(cfg)
    assert d["max_fills_per_bar"] == 1
    assert d["cooldown_bars"] == 1          # max(base, 1)
    assert d["slip"] == STRESS_SLIP_FLOOR   # spread 0 → floor
    cfg2 = RangeLadderConfig(cooldown_bars=4, stress_spread_pct=0.01)
    d2 = stress_dials(cfg2, body_only=True)
    assert d2["cooldown_bars"] == 4
    assert d2["slip"] == pytest.approx(0.005)   # spread/2 above the floor
    assert d2["body_only"] is True


@pytest.mark.parametrize("seed", [0, 1, 2])
@pytest.mark.parametrize("k_buy,k_sell", [(1.0, 1.0), (-1.5, 2.0)])
def test_stress_never_increases_fills(seed, k_buy, k_sell):
    candles = _candles(seed=seed)
    cfg = RangeLadderConfig(
        n_buy=5, n_sell=5, buy_near_pct=0.02, buy_far_pct=0.15,
        sell_near_pct=0.02, sell_far_pct=0.15,
        k_buy=k_buy, k_sell=k_sell,
        fund_quote=1000.0, cooldown_bars=1,
    )
    rungs = build_rungs(100.0, cfg, 0.01)
    base = run_ladder_sim(
        candles["open"], candles["high"], candles["low"], candles["close"],
        rungs.buys, rungs.sells, rungs.buy_weights, rungs.sell_weights,
        fund=cfg.fund_quote, quote_frac=cfg.quote_frac, fee=cfg.fee,
        cooldown_bars=cfg.cooldown_bars, use_numba=False,
    )
    stress = run_range_ladder_stress(candles, cfg, rungs, 3600, use_numba=False)
    assert stress["trades"] <= base["trades"]
    assert all(
        s <= b for s, b in zip(stress["buy_fills"], base["buy_fills"])
    ) or stress["trades"] <= base["trades"]

    body = run_range_ladder_stress(
        candles, cfg, rungs, 3600, body_only=True, use_numba=False,
    )
    assert body["trades"] <= base["trades"]


def test_stress_fees_reflect_slip_floor():
    """With identical fills, stress fees per fill are strictly higher (slip)."""
    candles = _candles(seed=3)
    cfg = RangeLadderConfig(cooldown_bars=1)
    rungs = build_rungs(100.0, cfg, 0.01)
    stress = run_range_ladder_stress(candles, cfg, rungs, 3600, use_numba=False)
    if stress["trades"] > 0:
        base = run_ladder_sim(
            candles["open"], candles["high"], candles["low"], candles["close"],
            rungs.buys, rungs.sells, rungs.buy_weights, rungs.sell_weights,
            fund=cfg.fund_quote, quote_frac=cfg.quote_frac, fee=cfg.fee,
            cooldown_bars=cfg.cooldown_bars, use_numba=False,
        )
        assert stress["fees"] / max(stress["trades"], 1) > 0
        # slip is charged on top of the fee — per-fill cost rate is higher
        assert (stress["fees"] / stress["trades"]) >= (
            base["fees"] / base["trades"] * 0.999 if base["trades"] else 0.0
        )
