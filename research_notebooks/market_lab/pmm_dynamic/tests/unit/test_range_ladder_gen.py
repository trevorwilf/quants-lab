"""Unit tests for range_ladder rung construction + hard constraints."""

import numpy as np
import pytest

from pmm_lab.strategies.range_ladder_gen import (
    RungSet,
    build_rungs,
    fit_generative_to_ladder,
    ladder_round_trip_error,
    quantize_price,
    shape_weights,
    validate_rungs,
)

TINY_TICK = 1e-9


def _params(**overrides):
    base = dict(
        n_buy=5, n_sell=5,
        buy_near_pct=0.02, buy_far_pct=0.20,
        sell_near_pct=0.02, sell_far_pct=0.20,
        buy_gamma=1.0, sell_gamma=1.0,
        k_buy=1.0, k_sell=1.0,
        min_weight_frac=0.10,
    )
    base.update(overrides)
    return base


def _validate_kwargs(params, **overrides):
    kwargs = dict(
        anchor=100.0, fee=0.002, price_tick=TINY_TICK,
        min_order_quote=1.0, fund=1000.0, quote_frac=0.5,
        buy_near_pct=params["buy_near_pct"], buy_far_pct=params["buy_far_pct"],
        sell_near_pct=params["sell_near_pct"], sell_far_pct=params["sell_far_pct"],
    )
    kwargs.update(overrides)
    return kwargs


# ----------------------------------------------------------------------
# Rung construction
# ----------------------------------------------------------------------

def test_buys_descending_sells_ascending():
    for gamma in (0.5, 1.0, 2.0):
        r = build_rungs(100.0, _params(buy_gamma=gamma, sell_gamma=gamma), TINY_TICK)
        assert np.all(np.diff(r.buys) < 0), "buys must be nearest-first (descending)"
        assert np.all(np.diff(r.sells) > 0), "sells must be nearest-first (ascending)"
        assert np.max(r.buys) < 100.0 < np.min(r.sells)


def test_gamma_one_is_arithmetic_spacing():
    r = build_rungs(100.0, _params(buy_gamma=1.0, sell_gamma=1.0), 1e-12)
    buy_gaps = np.diff(r.buys)
    sell_gaps = np.diff(r.sells)
    assert np.allclose(buy_gaps, buy_gaps[0], rtol=1e-9)
    assert np.allclose(sell_gaps, sell_gaps[0], rtol=1e-9)


def test_gamma_curvature_direction():
    """gamma < 1 front-loads spacing away from the anchor, gamma > 1 clusters near."""
    near = build_rungs(100.0, _params(buy_gamma=2.0), 1e-12)
    far = build_rungs(100.0, _params(buy_gamma=0.5), 1e-12)
    # First gap (nearest rungs) is smaller when gamma > 1
    assert abs(np.diff(near.buys)[0]) < abs(np.diff(far.buys)[0])


def test_tick_quantization_direction():
    """Buys round DOWN, sells round UP — quantization only widens the dead zone."""
    tick = 0.5
    p = _params()
    r = build_rungs(100.0, p, tick)
    raw = build_rungs(100.0, p, 1e-12)
    for q in np.concatenate([r.buys, r.sells]):
        assert abs(q / tick - round(q / tick)) < 1e-9, f"{q} not on tick grid"
    assert np.all(r.buys <= raw.buys + 1e-12)
    assert np.all(r.sells >= raw.sells - 1e-12)


def test_quantize_price_exact():
    assert quantize_price(100.057, 0.01, "buy") == 100.05
    assert quantize_price(100.051, 0.01, "sell") == 100.06
    assert quantize_price(0.0167139, 0.0000001, "buy") == pytest.approx(0.0167139)


def test_weight_floor_and_normalisation():
    w = shape_weights(10, 4.0, 0.10)
    assert w.max() == 1.0
    assert w.min() == pytest.approx(0.10)
    # k>0 front-loads (non-increasing), k<0 loads deep rungs
    assert np.all(np.diff(w) <= 1e-12)
    w_neg = shape_weights(5, -2.0, 0.10)
    assert np.all(np.diff(w_neg) >= -1e-12)
    assert w_neg[-1] == 1.0


def test_min_counts_enforced():
    with pytest.raises(ValueError):
        shape_weights(1, 1.0)
    with pytest.raises(ValueError, match="rung counts"):
        build_rungs(100.0, _params(n_buy=1), TINY_TICK)
    with pytest.raises(ValueError, match="anchor"):
        build_rungs(0.0, _params(), TINY_TICK)


# ----------------------------------------------------------------------
# Constraints — one passing and one failing case each
# ----------------------------------------------------------------------

def test_constraint_all_pass():
    p = _params()
    r = build_rungs(100.0, p, TINY_TICK)
    ok, reason = validate_rungs(r, **_validate_kwargs(p))
    assert ok, reason


def test_constraint1_far_not_greater_than_near_fails():
    p = _params(buy_far_pct=0.02, buy_near_pct=0.02)
    r = build_rungs(100.0, _params(), TINY_TICK)   # arrays irrelevant here
    ok, reason = validate_rungs(r, **_validate_kwargs(p))
    assert not ok and "buy_far_pct" in reason

    p2 = _params(sell_far_pct=0.01, sell_near_pct=0.02)
    ok2, reason2 = validate_rungs(r, **_validate_kwargs(p2))
    assert not ok2 and "sell_far_pct" in reason2


def test_constraint1_tick_separation_fails_on_coarse_tick():
    """A coarse tick collapses adjacent rungs onto the same grid point."""
    p = _params(buy_near_pct=0.010, buy_far_pct=0.014)  # rungs ~0.1 apart at anchor 100
    r = build_rungs(100.0, p, 1.0)  # tick of 1.0 collapses them
    ok, reason = validate_rungs(r, **_validate_kwargs(p, price_tick=1.0))
    assert not ok and "price tick" in reason


def test_constraint2_dead_zone_fee_floor():
    # fee 0.002 → floor 0.008. 0.004 + 0.004 = 0.008 passes (>=).
    p_pass = _params(buy_near_pct=0.004, sell_near_pct=0.004)
    r = build_rungs(100.0, p_pass, TINY_TICK)
    ok, reason = validate_rungs(r, **_validate_kwargs(p_pass))
    assert ok, reason
    # 0.003 + 0.003 = 0.006 < 0.008 fails.
    p_fail = _params(buy_near_pct=0.003, sell_near_pct=0.003)
    r2 = build_rungs(100.0, p_fail, TINY_TICK)
    ok2, reason2 = validate_rungs(r2, **_validate_kwargs(p_fail))
    assert not ok2 and "dead zone" in reason2


def test_constraint2_scales_with_fee():
    """The same params pass at fee 0.002 but fail at fee 0.0025 (kraken floor 0.010)."""
    p = _params(buy_near_pct=0.0045, sell_near_pct=0.0045)  # dead zone 0.009
    r = build_rungs(100.0, p, TINY_TICK)
    ok, _ = validate_rungs(r, **_validate_kwargs(p, fee=0.002))
    assert ok
    ok2, reason2 = validate_rungs(r, **_validate_kwargs(p, fee=0.0025))
    assert not ok2 and "dead zone" in reason2


def test_constraint3_adjacent_gap_fee_floor():
    # 5 rungs from 1% to 1.3%: avg gap ~0.075% < 0.4% → fail
    p = _params(buy_near_pct=0.010, buy_far_pct=0.013)
    r = build_rungs(100.0, p, TINY_TICK)
    ok, reason = validate_rungs(r, **_validate_kwargs(p))
    assert not ok and "adjacent buy gap" in reason


def test_constraint4_budget_feasibility():
    p = _params(n_buy=10, k_buy=4.0)
    r = build_rungs(100.0, p, TINY_TICK)
    ok, reason = validate_rungs(r, **_validate_kwargs(p, fund=1000.0))
    assert ok, reason
    ok2, reason2 = validate_rungs(r, **_validate_kwargs(p, fund=20.0))
    assert not ok2 and "min_order_quote" in reason2


def test_constraint5_cross_side_overlap():
    p = _params()
    overlapping = RungSet(
        buys=np.array([101.0, 99.0]),
        sells=np.array([100.0, 103.0]),
        buy_weights=np.array([1.0, 1.0]),
        sell_weights=np.array([1.0, 1.0]),
    )
    ok, reason = validate_rungs(overlapping, **_validate_kwargs(p))
    assert not ok and "overlap" in reason


def test_literal_ladder_dead_zone_from_arrays():
    """Without generative params, the dead zone is checked on the arrays."""
    tight = RungSet(
        buys=np.array([99.9, 98.0]),
        sells=np.array([100.1, 102.0]),
        buy_weights=np.array([1.0, 1.0]),
        sell_weights=np.array([1.0, 1.0]),
    )
    ok, reason = validate_rungs(
        tight, anchor=100.0, fee=0.002, price_tick=TINY_TICK,
        min_order_quote=1.0, fund=1000.0, quote_frac=0.5,
    )
    assert not ok and "dead zone" in reason


# ----------------------------------------------------------------------
# Incumbent approximation (§3.7)
# ----------------------------------------------------------------------

DASH = dict(
    buys=[32.851, 32.112, 31.3395, 30.6005, 29.8615],
    bw=[7.6, 11.4, 17.1, 25.6, 38.4],
    sells=[36.1764, 38.7965, 41.3829, 43.9693, 46.5893],
    sw=[39.9, 25.8, 16.6, 10.7, 6.9],
    tick=0.01,
)
SUN = dict(
    buys=[0.0167139, 0.0163557, 0.0160146, 0.0156735, 0.0153324],
    bw=[44.3, 26.1, 15.3, 9.0, 5.3],
    sells=[0.0184876, 0.0199032, 0.0213358, 0.0227514, 0.024184],
    sw=[15.3, 17.4, 19.7, 22.3, 25.3],
    tick=0.0000001,
)


@pytest.mark.parametrize("inc", [DASH, SUN], ids=["DASH", "SUN"])
def test_incumbent_round_trip_under_5pct(inc):
    err = ladder_round_trip_error(
        inc["buys"], inc["bw"], inc["sells"], inc["sw"], inc["tick"],
    )
    assert err < 0.05, f"round-trip error {err:.4f} >= 5%"


def test_fit_returns_search_space_compatible_params():
    fit = fit_generative_to_ladder(DASH["buys"], DASH["bw"], DASH["sells"], DASH["sw"])
    assert fit["n_buy"] == 5 and fit["n_sell"] == 5
    assert 0.005 <= fit["buy_near_pct"] <= 0.10
    assert 0.03 <= fit["buy_far_pct"] <= 0.45
    assert 0.005 <= fit["sell_near_pct"] <= 0.10
    assert 0.03 <= fit["sell_far_pct"] <= 0.45
    assert 0.5 <= fit["buy_gamma"] <= 2.0
    assert 0.5 <= fit["sell_gamma"] <= 2.0
    assert -2.0 <= fit["k_buy"] <= 4.0
    assert -2.0 <= fit["k_sell"] <= 4.0
    # DASH buys are deep-loaded (weights grow with depth) → negative k
    assert fit["k_buy"] < 0
    # DASH sells are front-loaded → positive k
    assert fit["k_sell"] > 0


def test_fit_rejects_mismatched_lengths():
    with pytest.raises(ValueError, match="matching lengths"):
        fit_generative_to_ladder([100.0, 99.0], [1.0], [101.0, 102.0], [1.0, 1.0])
