"""PB.4 — engine ROUTING tests for ``fill_model="tape_replay"``.

These are pure-logic tests of the dispatch wiring (NOT a fidelity claim): they
feed a hand-built trades frame through a stub ``trades_supplier`` and assert that

* the sell-side bracket fill (:func:`exits._bracket_fill`) routes to the tape
  oracle, honouring the stop/target trigger, and falls through to the legacy
  bracket price when no print qualifies;
* the buy-side entry fill (:func:`fills._tape_replay_fill`) replays the tape,
  honouring a marketable-limit ceiling and returning ``None`` (fall back) on an
  empty tape;
* ``fill_model="legacy"`` NEVER touches the tape (the stub raises if called) —
  the byte-identical guarantee.

Fidelity vs the REAL tape is validated separately (PB.5 / PC.3) on the lake.
"""
from __future__ import annotations

import pandas as pd
import pytest

from bowaka_v2_lab.sim.exits import _XFill, _bracket_fill
from bowaka_v2_lab.sim.fills import _tape_replay_fill
from bowaka_v2_lab.sim.quote_model import QuoteSnapshot

_BASE = pd.Timestamp("2025-09-02 14:00:00", tz="UTC")


def _trades(rows):
    """rows: list of ``(offset_seconds, price, size)`` → a trades DataFrame."""
    return pd.DataFrame(
        [
            {"timestamp": _BASE + pd.Timedelta(seconds=o), "price": float(p), "size": int(s)}
            for (o, p, s) in rows
        ]
    )


def _supplier(df):
    def trades_supplier(symbol, t0, t1):  # noqa: ANN001 - test stub
        return df

    return trades_supplier


def _boom_supplier():
    def trades_supplier(symbol, t0, t1):  # noqa: ANN001 - must never be called
        raise AssertionError("trades_supplier called under fill_model='legacy'")

    return trades_supplier


def _xf(*, fill_model, trades_supplier, qty=50, participation=1.0):
    return _XFill(
        symbol="AAA", quote_supplier=None, cross_spread=False, half_spread_bps=0.0,
        qty=qty, participation_cap=None, impact_coef_bps=10.0, impact_model="sqrt",
        cost_stress="base", require_fresh_quote=False, max_quote_age_seconds=15,
        fill_model=fill_model, trades_supplier=trades_supplier,
        tape_window_seconds=300.0, tape_participation=participation,
    )


def _quote(*, bid=99.0, ask=100.0):
    return QuoteSnapshot(
        bid=bid, ask=ask, mid=(bid + ask) / 2.0, spread_pct=(ask - bid) / ask,
        quote_timestamp=str(_BASE), quote_age_seconds=0.0, source="historical",
        bid_size=100.0, ask_size=100.0,
    )


# --------------------------------------------------------------------------- #
# Sell-side bracket routing (exits._bracket_fill)
# --------------------------------------------------------------------------- #
def test_exit_stop_fills_at_tape_vwap_of_prints_at_or_below_stop():
    # stop=100; prints at 99 (eligible) and 101 (above stop → excluded).
    df = _trades([(1, 99.0, 50), (2, 101.0, 50)])
    bar = {"timestamp": _BASE, "volume": 10_000}
    px, slip = _bracket_fill(100.0, bar, _xf(fill_model="tape_replay", trades_supplier=_supplier(df)), kind="stop")
    assert px == pytest.approx(99.0)          # VWAP of the single qualifying print
    assert slip == pytest.approx(-100.0)      # gave up 100 bps vs the 100 bracket


def test_exit_target_fills_at_tape_vwap_of_prints_at_or_above_target():
    # target=100; prints at 99 (below → excluded) and 101 (eligible).
    df = _trades([(1, 99.0, 50), (2, 101.0, 50)])
    bar = {"timestamp": _BASE, "volume": 10_000}
    px, slip = _bracket_fill(100.0, bar, _xf(fill_model="tape_replay", trades_supplier=_supplier(df)), kind="target")
    assert px == pytest.approx(101.0)
    assert slip == pytest.approx(100.0)


def test_exit_stop_vwap_blends_multiple_eligible_prints():
    # two prints ≤ stop, sizes 30 & 20 → VWAP = (98*30 + 100*20)/50 = 98.8
    df = _trades([(1, 98.0, 30), (2, 100.0, 20)])
    bar = {"timestamp": _BASE, "volume": 10_000}
    px, _ = _bracket_fill(100.0, bar, _xf(fill_model="tape_replay", trades_supplier=_supplier(df)), kind="stop")
    assert px == pytest.approx(98.8)


def test_exit_no_qualifying_print_falls_through_to_legacy_bracket():
    # stop=100 but every print is above the stop → tape excludes all → legacy.
    df = _trades([(1, 101.0, 50), (2, 102.0, 50)])
    bar = {"timestamp": _BASE, "volume": 10_000}
    px, slip = _bracket_fill(100.0, bar, _xf(fill_model="tape_replay", trades_supplier=_supplier(df)), kind="stop")
    assert px == pytest.approx(100.0)   # exact bracket — legacy fall-through
    assert slip is None


def test_exit_legacy_fill_model_never_calls_the_tape():
    bar = {"timestamp": _BASE, "volume": 10_000}
    # The stub raises if touched; legacy must not enter the tape branch.
    px, slip = _bracket_fill(100.0, bar, _xf(fill_model="legacy", trades_supplier=_boom_supplier()), kind="stop")
    assert px == pytest.approx(100.0)
    assert slip is None


# --------------------------------------------------------------------------- #
# Buy-side entry routing (fills._tape_replay_fill)
# --------------------------------------------------------------------------- #
def test_buy_market_fills_at_tape_vwap_of_all_prints():
    # market buy, no ceiling → VWAP of (100*30 + 102*30)/60 = 101.0
    df = _trades([(1, 100.0, 30), (2, 102.0, 30)])
    fill = _tape_replay_fill(
        side="buy", requested_qty=60, quote=_quote(), forward_trades=df, scan_ts=_BASE,
        tape_window_seconds=300.0, tape_participation=1.0, limit_price=None,
        min_order_notional=0.0, commission_per_share=0.0, regulatory_fee_bps=0.0,
        order_style="market",
    )
    assert fill is not None
    assert fill.filled is True
    assert fill.filled_qty == 60
    assert fill.avg_fill_price == pytest.approx(101.0)
    assert fill.is_partial is False


def test_buy_marketable_limit_excludes_prints_above_the_ceiling():
    # limit ceiling 100.5 → only the 100.0 print is eligible (50 sh), 101.0 excluded.
    df = _trades([(1, 100.0, 50), (2, 101.0, 50)])
    fill = _tape_replay_fill(
        side="buy", requested_qty=50, quote=_quote(), forward_trades=df, scan_ts=_BASE,
        tape_window_seconds=300.0, tape_participation=1.0, limit_price=100.5,
        min_order_notional=0.0, commission_per_share=0.0, regulatory_fee_bps=0.0,
        order_style="marketable_limit",
    )
    assert fill is not None
    assert fill.filled_qty == 50
    assert fill.avg_fill_price == pytest.approx(100.0)


def test_buy_partial_when_window_volume_below_requested():
    # only 60 sh on the tape vs 100 requested → partial fill of 60.
    df = _trades([(1, 100.0, 60)])
    fill = _tape_replay_fill(
        side="buy", requested_qty=100, quote=_quote(), forward_trades=df, scan_ts=_BASE,
        tape_window_seconds=300.0, tape_participation=1.0, limit_price=None,
        min_order_notional=0.0, commission_per_share=0.0, regulatory_fee_bps=0.0,
        order_style="market",
    )
    assert fill is not None
    assert fill.filled_qty == 60
    assert fill.is_partial is True
    assert fill.reason == "partial_fill"


def test_buy_empty_tape_returns_none_so_caller_falls_back():
    fill = _tape_replay_fill(
        side="buy", requested_qty=50, quote=_quote(), forward_trades=_trades([]), scan_ts=_BASE,
        tape_window_seconds=300.0, tape_participation=1.0, limit_price=None,
        min_order_notional=0.0, commission_per_share=0.0, regulatory_fee_bps=0.0,
        order_style="market",
    )
    assert fill is None


def test_buy_partial_below_min_notional_is_rejected():
    # 1 sh at $100 = $100 notional, below a $500 min → no-fill.
    df = _trades([(1, 100.0, 1)])
    fill = _tape_replay_fill(
        side="buy", requested_qty=50, quote=_quote(), forward_trades=df, scan_ts=_BASE,
        tape_window_seconds=300.0, tape_participation=1.0, limit_price=None,
        min_order_notional=500.0, commission_per_share=0.0, regulatory_fee_bps=0.0,
        order_style="market",
    )
    assert fill is not None
    assert fill.filled is False
    assert fill.reason == "partial_below_min"
