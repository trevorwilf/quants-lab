"""Kernel behavior on hand-built candles + RangeLadderConfig invariants.

All kernel assertions run the PURE-PYTHON path (use_numba=False): the numba
kernel is proven bit-identical in test_numba_range_ladder_parity.py, and the
pure path avoids JIT compilation in the fast unit lane.
"""

import numpy as np
import pytest

from pmm_lab.config.params import FeeConfig, PairRules
from pmm_lab.features._numba_range_ladder import run_ladder_sim
from pmm_lab.strategies.range_ladder import (
    RangeLadderConfig,
    RangeLadderStrategy,
    compute_anchor,
    run_range_ladder_window,
)
from tests.conftest import CANDLE_DTYPE


def _bars(rows):
    """rows: list of (o, h, l, c) → separate float arrays."""
    a = np.asarray(rows, dtype=np.float64)
    return a[:, 0], a[:, 1], a[:, 2], a[:, 3]


def _sim(rows, buys, sells, bw=None, sw=None, **kw):
    o, h, l, c = _bars(rows)
    kw.setdefault("fund", 1000.0)
    kw.setdefault("quote_frac", 0.5)
    kw.setdefault("fee", 0.002)
    kw.setdefault("bar_interval_seconds", 3600)
    return run_ladder_sim(
        o, h, l, c, np.asarray(buys, float), np.asarray(sells, float),
        None if bw is None else np.asarray(bw, float),
        None if sw is None else np.asarray(sw, float),
        use_numba=False, **kw,
    )


FLAT = (100.0, 100.0, 100.0, 100.0)


def test_down_up_pair_fills_one_buy_then_one_sell():
    rows = [
        FLAT,                          # arm: buys below, sells above
        (100.0, 100.0, 94.0, 96.0),    # down bar → buy @95 fills
        (96.0, 106.0, 96.0, 104.0),    # up bar → sell @105 fills
    ]
    r = _sim(rows, buys=[95.0, 90.0], sells=[105.0, 110.0], bw=[1, 1], sw=[1, 1])
    assert r["buy_fills"] == [1, 0]
    assert r["sell_fills"] == [1, 0]
    assert r["trades"] == 2


def test_buy_collateral_includes_fee():
    """quote == cost exactly is NOT enough — the exchange holds cost + fee."""
    # Single rung: static qty allocates the full quote budget → cost == quote,
    # so the fee makes the fill unaffordable. This mirrors live NonKYC holds.
    # Rung at 80 keeps 500/80*80 == 500 exact in float64.
    rows = [FLAT, (100.0, 100.0, 79.0, 96.0)]
    r = _sim(rows, buys=[80.0], sells=[110.0], bw=[1], sw=[1])
    assert r["buy_fills"] == [0], "fill must be skipped when quote < cost + fee"
    # With fee=0 the same fill succeeds — proving the fee was the blocker.
    r2 = _sim(rows, buys=[80.0], sells=[110.0], bw=[1], sw=[1], fee=0.0)
    assert r2["buy_fills"] == [1]


def test_fee_and_slip_arithmetic_exact():
    fund, qf, fee, slip = 1000.0, 0.5, 0.002, 0.001
    rows = [FLAT, (100.0, 100.0, 94.0, 96.0)]
    r = _sim(rows, buys=[95.0, 10.0], sells=[110.0], bw=[1, 1], sw=[1],
             fee=fee, slip=slip)
    # Replicate the kernel's arithmetic exactly
    buy_qty0 = (fund * qf * 1.0 / 2.0) / 95.0
    cost = 95.0 * buy_qty0
    f = cost * (fee + slip)
    assert r["buy_fills"] == [1, 0]
    assert abs(r["fees"] - f) < 1e-12
    assert abs(r["final_quote"] - (fund * qf - cost - f)) < 1e-12
    assert abs(r["final_base"] - (fund * qf / 100.0 + buy_qty0)) < 1e-12


def test_sell_proceeds_credit_minus_fee_exact():
    fund, qf, fee = 1000.0, 0.5, 0.002
    rows = [FLAT, (100.0, 106.0, 100.0, 104.0)]
    r = _sim(rows, buys=[10.0], sells=[105.0, 120.0], bw=[1], sw=[1, 1], fee=fee)
    sell_qty0 = (fund * qf / 100.0) * 0.5
    proceeds = 105.0 * sell_qty0
    f = proceeds * fee
    assert r["sell_fills"] == [1, 0]
    assert abs(r["final_quote"] - (fund * qf + proceeds - f)) < 1e-12
    assert abs(r["final_base"] - (fund * qf / 100.0 - sell_qty0)) < 1e-12


def test_cash_starved_buy_is_skipped():
    """When the first fill drains the quote budget, deeper rungs are skipped."""
    rows = [FLAT, (100.0, 100.0, 89.0, 96.0)]  # sweeps through both rungs
    r = _sim(rows, buys=[95.0, 90.0], sells=[110.0], bw=[9, 1], sw=[1])
    # rung0 costs 450 (+0.9 fee) of the 500 quote; rung1 needs 50 + 0.1 → skipped
    assert r["buy_fills"] == [1, 0]


def test_cooldown_blocks_within_window_and_allows_after():
    dip = (100.0, 100.0, 94.0, 96.0)
    rearm = (96.0, 100.0, 96.0, 97.0)
    rows = [
        FLAT,    # t0
        dip,     # t1: fill (last=-inf)
        rearm,   # t2: close 97 > 95 → re-arm
        dip,     # t3: 3-1=2, NOT > cooldown_bars=2 → blocked
        dip,     # t4: 4-1=3 > 2 → fills
    ]
    # bw=[1,3]: rung0 only claims a quarter of the quote budget, so BOTH
    # fills stay affordable (collateral includes the fee).
    r = _sim(rows, buys=[95.0, 10.0], sells=[200.0], bw=[1, 3], sw=[1],
             cooldown_bars=2)
    assert r["buy_fills"] == [2, 0]
    assert list(r["cum_buy_fills"]) == [0, 1, 1, 1, 2]


def test_rearm_requires_close_cross_back():
    dip_close_below = (100.0, 100.0, 93.0, 94.5)   # fill; close stays below rung
    dip_again = (94.5, 94.5, 93.0, 94.0)           # still disarmed → no fill
    close_above = (94.0, 96.5, 94.0, 96.0)         # close 96 > 95 → re-arm
    dip_final = (96.0, 96.0, 94.0, 94.5)           # fills again
    rows = [FLAT, dip_close_below, dip_again, close_above, dip_final]
    r = _sim(rows, buys=[95.0, 10.0], sells=[200.0], bw=[1, 3], sw=[1],
             cooldown_bars=0)
    assert r["buy_fills"] == [2, 0]
    assert list(r["cum_buy_fills"]) == [0, 1, 1, 1, 2]


def test_intrabar_path_up_bar_visits_low_first():
    """Up bar (c>=o) walks o→l→h→c: a buy then a sell can fill in ONE bar."""
    rows = [FLAT, (100.0, 106.0, 94.0, 104.0)]
    r = _sim(rows, buys=[95.0, 10.0], sells=[105.0, 200.0], bw=[1, 1], sw=[1, 1])
    assert r["buy_fills"] == [1, 0]
    assert r["sell_fills"] == [1, 0]


def test_max_fills_per_bar_caps_total_fills():
    rows = [FLAT, (100.0, 106.0, 94.0, 104.0)]
    r = _sim(rows, buys=[95.0, 10.0], sells=[105.0, 200.0], bw=[1, 1], sw=[1, 1],
             max_fills_per_bar=1)
    assert sum(r["buy_fills"]) + sum(r["sell_fills"]) == 1
    assert r["buy_fills"] == [1, 0], "down leg comes first on an up bar"


def test_body_only_ignores_wicks():
    rows = [FLAT, (100.0, 100.0, 94.0, 99.0)]   # wick to 94, body 100→99
    r = _sim(rows, buys=[95.0, 10.0], sells=[200.0], bw=[1, 1], sw=[1])
    assert r["buy_fills"] == [1, 0]
    r2 = _sim(rows, buys=[95.0, 10.0], sells=[200.0], bw=[1, 1], sw=[1],
              body_only=True)
    assert r2["buy_fills"] == [0, 0]


def test_no_fill_flat_run_matches_hold():
    rows = [FLAT] * 10
    r = _sim(rows, buys=[95.0, 90.0], sells=[105.0, 110.0])
    assert r["trades"] == 0
    assert r["pnl_pct"] == pytest.approx(r["hold_pct"])
    assert r["endinv_pct"] == pytest.approx(50.0)
    assert r["fees"] == 0.0


# ----------------------------------------------------------------------
# Config invariants + Strategy protocol shell
# ----------------------------------------------------------------------

def test_config_rejects_small_rung_counts():
    with pytest.raises(ValueError, match="n_buy/n_sell >= 3"):
        RangeLadderConfig(n_buy=2)
    with pytest.raises(ValueError, match="n_buy/n_sell >= 3"):
        RangeLadderConfig(n_sell=1)


def test_config_literal_requires_all_four_fields():
    with pytest.raises(ValueError, match="literal ladder requires"):
        RangeLadderConfig(literal_buy_prices=(95.0,), literal_buy_weights=(1.0,))


def test_config_literal_resolves_sorted_nearest_first():
    cfg = RangeLadderConfig(
        literal_buy_prices=(90.0, 95.0),      # unsorted on purpose
        literal_buy_weights=(1.0, 2.0),
        literal_sell_prices=(110.0, 105.0),
        literal_sell_weights=(1.0, 2.0),
    )
    assert cfg.uses_literal_ladder
    rungs = cfg.resolve_rungs(100.0, 0.01)
    assert list(rungs.buys) == [95.0, 90.0]
    assert list(rungs.sells) == [105.0, 110.0]


def test_config_quote_frac_bounds():
    with pytest.raises(ValueError, match="quote_frac"):
        RangeLadderConfig(quote_frac=0.0)


def test_config_fingerprint_hashable_and_distinct():
    a = RangeLadderConfig()
    b = RangeLadderConfig(k_buy=1.0)
    assert hash(a.to_fingerprint()) != hash(b.to_fingerprint())


def _make_candles(n=50, seed=3):
    rng = np.random.default_rng(seed)
    ts = np.arange(n, dtype="int64") * 3600 + 1_700_000_000
    close = 100.0 + np.cumsum(rng.normal(0, 1.0, n))
    close = np.maximum(close, 1.0)
    o = np.roll(close, 1)
    o[0] = close[0]
    rows = [
        (int(ts[i]), o[i], max(o[i], close[i]) + 0.5,
         min(o[i], close[i]) - 0.5, close[i], 1.0, False)
        for i in range(n)
    ]
    return np.array(rows, dtype=CANDLE_DTYPE)


def test_compute_signals_passthrough():
    candles = _make_candles()
    strat = RangeLadderStrategy(RangeLadderConfig())
    sig = strat.compute_signals(candles)
    assert sig.warmup_end == 0
    assert np.array_equal(sig.data["close_price"], candles["close"])
    assert np.array_equal(sig.data["timestamp"], candles["timestamp"].astype(float))


def test_build_orders_is_noop():
    strat = RangeLadderStrategy(RangeLadderConfig())
    orders, placed, rejected = strat.build_orders(0, None, None, None, None)
    assert orders == [] and placed == 0 and rejected == 0


def test_compute_anchor_median3():
    closes = np.array([1.0, 2.0, 10.0, 20.0, 30.0])
    assert compute_anchor(closes) == 20.0
    with pytest.raises(ValueError):
        compute_anchor(np.array([]))


def test_run_range_ladder_window_alignment():
    candles = _make_candles(n=60)
    cfg = RangeLadderConfig(fund_quote=500.0)
    rules = PairRules(
        price_tick=0.01, amount_step=0.001, min_notional_quote=1.0,
        fees=FeeConfig(0.002, 0.002),
    )
    result = run_range_ladder_window(cfg, rules, candles, sim_start_idx=20)
    assert len(result.equity_curve) == 60
    assert len(result.position_history) == 60
    assert np.all(result.equity_curve[:20] == 500.0)
    assert np.all(result.position_history[:20] == 0.0)
    assert result.trades == []
    assert result.n_orders_filled == result.n_orders_placed
    with pytest.raises(ValueError, match="sim_start_idx"):
        run_range_ladder_window(cfg, rules, candles, sim_start_idx=60)
