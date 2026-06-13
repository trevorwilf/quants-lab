"""P4 — fill-model correctness (L2, L11, L12, §2.2/§2.3) regression pins.

The legacy fill model manufactured liquidity and charged zero-cost exits — the
path the production finalist was scored under. P4 removes that:

* **L2** — a marketable-limit (T1) fill is capped at the DISPLAYED top-of-book
  size (no penny-walk re-consuming the touch); zero displayed size → no fill.
* **L11** — non-smoke realism contracts price the exit: a marketable STOP gives
  up the half-spread by default (``cross_spread`` on); a TARGET clamps to the
  resting limit; and the closure charges explicit sell-side fees.
* **§2.2** — a missing ADV/liquidity proxy no longer fills unbounded (it is
  bounded by the displayed touch), and synthetic quotes carry no fabricated size.
* **L12** — the T3 ``max(touch, cap)`` is intended design (touch is the floor,
  the participation cap bounds consumption beyond it) — pinned, not changed.
* **§2.3** — a real fill records the ~5s decision→fill latency (was 0.0).
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest

from bowaka_v2_lab.sim.exits import (
    _default_exit_cross_spread,
    _walk_lot_exit_pandas,
)
from bowaka_v2_lab.sim.fills import (
    DEFAULT_FILL_LATENCY_SECONDS,
    simulate_market_fill,
    simulate_marketable_limit_fill,
)
from bowaka_v2_lab.sim.portfolio import Portfolio, Position
from bowaka_v2_lab.sim.quote_model import (
    QuoteSnapshot,
    SOURCE_HISTORICAL,
    synthesize_calibrated_quote,
    synthesize_quote,
)

_TS = pd.Timestamp("2024-09-04T14:00:00Z")
_ET = "America/New_York"


def _hist_quote(*, ask: float = 10.0, ask_size: float = 200.0) -> QuoteSnapshot:
    bid = ask - 0.02
    mid = (bid + ask) / 2.0
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=mid, spread_pct=(ask - bid) / mid,
        quote_timestamp=_TS.isoformat(), quote_age_seconds=0.5,
        source=SOURCE_HISTORICAL, bid_size=ask_size, ask_size=ask_size,
    )


# --------------------------------------------------------------------------
# L2 — T1 fill ≤ displayed touch; zero displayed size → no fill
# --------------------------------------------------------------------------
def test_l2_t1_fill_capped_at_displayed_touch() -> None:
    """A 1000-share order against a 200-share displayed touch fills only 200."""
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=1000, quote=_hist_quote(ask=10.0, ask_size=200),
        marketable_limit_slippage_pct=0.01,  # 10.10 limit — would have walked 10c
        minute_bars=None, scan_ts=_TS, cost_stress="base", min_order_notional=100.0,
    )
    assert fill.filled is True
    assert fill.filled_qty == 200          # capped at displayed depth, NOT walked up
    assert fill.is_partial is True
    assert fill.avg_fill_price == 10.0     # at the touch, no penny-walk premium
    # The total fill never exceeds the displayed touch size (§6.1 #6).
    assert fill.filled_qty <= 200


def test_l2_zero_displayed_size_does_not_fill() -> None:
    """A historical quote with zero displayed size → no fill (was a full fill at
    the limit price)."""
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=500, quote=_hist_quote(ask=10.0, ask_size=0.0),
        marketable_limit_slippage_pct=0.005, minute_bars=None, scan_ts=_TS,
        cost_stress="base", min_order_notional=100.0,
    )
    assert fill.filled is False
    assert fill.filled_qty == 0


# --------------------------------------------------------------------------
# L11 — default exit prices the stop (mode-driven cross_spread); target clamps
# --------------------------------------------------------------------------
def _lot(*, stop_price: float, target_price: float, qty: int = 10) -> Position:
    base = pd.Timestamp("2024-09-04 09:30", tz=_ET).tz_convert("UTC")
    return Position(
        symbol="AAA", entry_date=_dt.date(2024, 9, 4), entry_price=100.0, qty=qty,
        stop_pct=0.08, target_pct=0.15, max_hold_days=3,
        entry_session=_dt.date(2024, 9, 4), entry_timestamp=base.isoformat(),
        stop_price=stop_price, target_price=target_price,
    )


def _bars(rows: list[dict]) -> pd.DataFrame:
    base = pd.Timestamp("2024-09-04 09:31", tz=_ET).tz_convert("UTC")
    return pd.DataFrame([
        {"symbol": "AAA", "timestamp": base + pd.Timedelta(minutes=i),
         "open": r["o"], "high": r["h"], "low": r["l"], "close": r["c"], "volume": 1000.0}
        for i, r in enumerate(rows)
    ])


def _stop_bars() -> pd.DataFrame:
    return _bars([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 100.5, "l": 91.0, "c": 95},   # low 91 <= stop 92
    ])


def test_l11_default_cross_spread_helper() -> None:
    """Non-smoke contracts default the exit cross_spread ON; smoke / unset stay
    OFF (cost-free bracket)."""
    assert _default_exit_cross_spread("current_code_parity") is True
    assert _default_exit_cross_spread("intended_realism") is True
    assert _default_exit_cross_spread("fast_realism") is True
    assert _default_exit_cross_spread("smoke_fixture") is False
    assert _default_exit_cross_spread(None) is False


def test_l11_smoke_stop_fills_cost_free_at_bracket() -> None:
    """smoke_fixture keeps the byte-identical cost-free bracket fill."""
    quote = lambda sym, ts: {"bid": 91.5}  # noqa: E731 — bid below the stop
    ev = _walk_lot_exit_pandas(
        _lot(stop_price=92.0, target_price=115.0), _stop_bars(),
        exit_cfg={"time_stop": {"enabled": False}},  # no explicit cross_spread
        quote_supplier=quote, cost_stress="conservative",
        simulation_mode="smoke_fixture",
    )
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0           # exact bracket, no give-up
    assert ev.exit_slippage_bps == 0.0


def test_l11_ccp_stop_gives_up_half_spread_by_default() -> None:
    """current_code_parity defaults cross_spread ON — the marketable stop gives up
    the half-spread (was the cost-free bracket fill)."""
    quote = lambda sym, ts: {"bid": 91.9}  # noqa: E731
    ev = _walk_lot_exit_pandas(
        _lot(stop_price=92.0, target_price=115.0), _stop_bars(),
        exit_cfg={"time_stop": {"enabled": False}},  # mode default kicks in
        quote_supplier=quote, cost_stress="conservative",
        simulation_mode="current_code_parity",
    )
    assert ev.exit_reason == "stop"
    assert ev.exit_price < 92.0            # gave up the spread vs the bracket
    assert ev.exit_slippage_bps < 0.0


def test_l11_explicit_cross_spread_false_overrides_mode_default() -> None:
    """An explicit ``cross_spread: false`` is honored even under CCP."""
    quote = lambda sym, ts: {"bid": 91.0}  # noqa: E731
    ev = _walk_lot_exit_pandas(
        _lot(stop_price=92.0, target_price=115.0), _stop_bars(),
        exit_cfg={"time_stop": {"enabled": False}, "cross_spread": False},
        quote_supplier=quote, cost_stress="conservative",
        simulation_mode="current_code_parity",
    )
    assert ev.exit_reason == "stop"
    assert ev.exit_price == 92.0           # explicit off -> bracket fill


def test_l11_ccp_target_clamps_to_bracket() -> None:
    """A TARGET clamps to the resting limit under CCP (no give-up, no improvement)
    even though stops pay the spread."""
    bars = _bars([
        {"o": 100, "h": 100.5, "l": 99.8, "c": 100},
        {"o": 100, "h": 116.0, "l": 99.0, "c": 110},  # high 116 >= target 115
    ])
    quote = lambda sym, ts: {"bid": 114.0}  # noqa: E731 — bid below the target
    ev = _walk_lot_exit_pandas(
        _lot(stop_price=80.0, target_price=115.0), bars,
        exit_cfg={"time_stop": {"enabled": False}},
        quote_supplier=quote, cost_stress="conservative",
        simulation_mode="current_code_parity",
    )
    assert ev.exit_reason == "target"
    assert ev.exit_price == pytest.approx(115.0)  # clamped to the limit
    assert ev.exit_slippage_bps == 0.0


# --------------------------------------------------------------------------
# L11 — explicit sell-side fees on the closure
# --------------------------------------------------------------------------
def test_l11_exit_closure_charges_sell_side_fees() -> None:
    """The closure records explicit sell-side commission + regulatory fees
    (mirroring the entry schedule). Default 0.0 stays fee-free."""
    pf = Portfolio(
        initial_bankroll=100_000.0,
        exit_commission_per_share=0.005,
        exit_regulatory_fee_bps=2.0,
    )
    pos = _lot(stop_price=92.0, target_price=115.0, qty=100)
    pf.open_positions[pos.position_id] = pos
    trade = pf.close_position_by_id(
        pos.position_id, exit_price=110.0, exit_reason="target",
        exit_date=_dt.date(2024, 9, 5),
    )
    assert trade["exit_commission"] == pytest.approx(0.005 * 100)           # 0.50
    assert trade["exit_regulatory_fees"] == pytest.approx(110.0 * 100 * 2.0 / 1e4)  # 2.20
    # pnl stays GROSS (symmetric with the entry side).
    assert trade["pnl"] == pytest.approx((110.0 - 100.0) * 100)


def test_l11_exit_fees_default_to_zero() -> None:
    pf = Portfolio(initial_bankroll=100_000.0)
    pos = _lot(stop_price=92.0, target_price=115.0, qty=100)
    pf.open_positions[pos.position_id] = pos
    trade = pf.close_position_by_id(
        pos.position_id, exit_price=110.0, exit_reason="target",
        exit_date=_dt.date(2024, 9, 5),
    )
    assert trade["exit_commission"] == 0.0
    assert trade["exit_regulatory_fees"] == 0.0


# --------------------------------------------------------------------------
# §2.2 — missing-ADV bound + synthetic sizes carry no fabricated depth
# --------------------------------------------------------------------------
def test_s22_missing_proxy_market_fill_bounded_by_displayed_touch() -> None:
    """A market fill with NO liquidity proxy is bounded by the displayed touch,
    not the whole order (was an unbounded full fill)."""
    fill = simulate_market_fill(
        side="buy", requested_qty=1000, quote=_hist_quote(ask=10.0, ask_size=150),
        liquidity_proxy_shares=None, cost_stress="base", min_order_notional=100.0,
    )
    assert fill.filled is True
    assert fill.filled_qty == 150          # capped at the displayed touch
    assert fill.is_partial is True


def test_s22_missing_proxy_and_no_displayed_size_no_fill() -> None:
    fill = simulate_market_fill(
        side="buy", requested_qty=1000, quote=_hist_quote(ask=10.0, ask_size=0.0),
        liquidity_proxy_shares=None, cost_stress="base", min_order_notional=100.0,
    )
    assert fill.filled is False


def test_s22_synthetic_quotes_carry_no_fabricated_depth() -> None:
    """Synthetic quotes (smoke / fallback) report zero displayed size — they are
    not accessible depth (was a fabricated 10_000)."""
    qc = synthesize_calibrated_quote(signal_price=10.0, at=_TS)
    assert qc.bid_size == 0.0 and qc.ask_size == 0.0
    ql = synthesize_quote(last_price=10.0, at=_TS)
    assert ql.bid_size == 0.0 and ql.ask_size == 0.0


# --------------------------------------------------------------------------
# L12 — T3 max(touch, cap): touch is the floor, cap bounds beyond it (pinned)
# --------------------------------------------------------------------------
def _t3_minute_bars(volume: float) -> pd.DataFrame:
    return pd.DataFrame({
        "timestamp": [_TS], "open": [10.0], "high": [10.1], "low": [9.9],
        "close": [10.0], "volume": [volume],
    })


def test_l12_displayed_touch_is_the_floor() -> None:
    """touch 100 > participation cap 80 → fills the displayed 100 (touch floor)."""
    fill = simulate_market_fill(
        side="buy", requested_qty=577, quote=_hist_quote(ask=10.0, ask_size=100),
        minute_bars=_t3_minute_bars(800.0), scan_ts=_TS, has_nbbo_depth=True,
        participation_cap=0.10, market_impact_coef_bps=10.0, adv_dollar=5_000_000.0,
    )
    assert fill.filled_qty == pytest.approx(100.0)


def test_l12_cap_bounds_consumption_beyond_touch() -> None:
    """cap 80 > touch 50 → fills 80 (the cap bounds consumption beyond the touch,
    no fabricated depth past the larger real signal)."""
    fill = simulate_market_fill(
        side="buy", requested_qty=577, quote=_hist_quote(ask=10.0, ask_size=50),
        minute_bars=_t3_minute_bars(800.0), scan_ts=_TS, has_nbbo_depth=True,
        participation_cap=0.10, market_impact_coef_bps=10.0, adv_dollar=5_000_000.0,
    )
    assert fill.filled_qty == pytest.approx(80.0)


# --------------------------------------------------------------------------
# §2.3 — decision→fill latency recorded on a real fill (was hardcoded 0.0)
# --------------------------------------------------------------------------
def test_s23_marketable_limit_records_fill_latency() -> None:
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=100, quote=_hist_quote(ask=10.0, ask_size=500),
        marketable_limit_slippage_pct=0.005, minute_bars=None, scan_ts=_TS,
        cost_stress="base",
    )
    assert fill.filled is True
    assert fill.fill_time_seconds == pytest.approx(DEFAULT_FILL_LATENCY_SECONDS)
    assert DEFAULT_FILL_LATENCY_SECONDS > 0.0


def test_s23_market_fill_records_fill_latency() -> None:
    fill = simulate_market_fill(
        side="buy", requested_qty=100, quote=_hist_quote(ask=10.0, ask_size=500),
        liquidity_proxy_shares=10_000, cost_stress="base",
    )
    assert fill.filled is True
    assert fill.fill_time_seconds == pytest.approx(DEFAULT_FILL_LATENCY_SECONDS)


def test_s23_fill_latency_is_sub_minute_so_scan_minute_is_fill_minute() -> None:
    """§2.3 entry-timestamp: the decision->fill latency is sub-minute, so the fill
    lands within the scan minute and ``Position.entry_timestamp = scan_ts`` (set in
    strategy_consumer) remains the REAL fill minute. The per-lot exit walk starts
    AFTER that minute (no same-bar exit / no look-ahead), and the fill model
    anchors every fill at scan_ts so a fill never drifts into a later minute and
    skips its early adverse path."""
    assert 0.0 < DEFAULT_FILL_LATENCY_SECONDS < 60.0


def test_s23_no_fill_has_zero_latency() -> None:
    """A no-fill carries no latency (latency is a property of a real fill)."""
    fill = simulate_marketable_limit_fill(
        side="buy", requested_qty=500, quote=_hist_quote(ask=10.0, ask_size=0.0),
        marketable_limit_slippage_pct=0.005, minute_bars=None, scan_ts=_TS,
        cost_stress="base", min_order_notional=100.0,
    )
    assert fill.filled is False
    assert fill.fill_time_seconds == 0.0


# --------------------------------------------------------------------------
# §5.5 (P5) — round-lot vs odd-lot displayed NBBO depth
# --------------------------------------------------------------------------
def test_s55_round_lot_depth_filters_sub_100() -> None:
    """Sub-100 displayed sizes (odd-lot / BOLO) are not protected accessible depth."""
    from bowaka_v2_lab.sim.fills import _round_lot_depth

    assert _round_lot_depth(0) == 0.0
    assert _round_lot_depth(None) == 0.0
    assert _round_lot_depth(50) == 0.0       # odd-lot
    assert _round_lot_depth(99) == 0.0
    assert _round_lot_depth(100) == 100.0    # one round lot counts
    assert _round_lot_depth(250) == 250.0


def test_s55_odd_lot_touch_is_not_protected_depth() -> None:
    """A 50-share displayed touch (odd-lot) is not accessible protected depth, so a
    T1 marketable order does not fill; a 100-share round lot does."""
    odd = simulate_marketable_limit_fill(
        side="buy", requested_qty=300, quote=_hist_quote(ask=10.0, ask_size=50),
        marketable_limit_slippage_pct=0.005, minute_bars=None, scan_ts=_TS,
        cost_stress="base", min_order_notional=100.0,
    )
    assert odd.filled is False
    rnd = simulate_marketable_limit_fill(
        side="buy", requested_qty=300, quote=_hist_quote(ask=10.0, ask_size=100),
        marketable_limit_slippage_pct=0.005, minute_bars=None, scan_ts=_TS,
        cost_stress="base", min_order_notional=100.0,
    )
    assert rnd.filled is True
    assert rnd.filled_qty == 100             # the round-lot displayed depth
