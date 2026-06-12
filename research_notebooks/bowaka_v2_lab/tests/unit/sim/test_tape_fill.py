"""PB.4 — trade-tape fill oracle: deterministic VWAP / fill-fraction on a
synthetic-trades fixture (hand-computed), plus clean no-fill fallback."""
from __future__ import annotations

import pandas as pd
import pytest

from bowaka_v2_lab.sim.tape_fill import replay_tape_fill

_BASE = "2026-05-01 14:00:00"


def _trades(rows, base=_BASE):
    """rows: list of (offset_seconds, price, size)."""
    t0 = pd.Timestamp(base, tz="UTC")
    return pd.DataFrame({
        "timestamp": [t0 + pd.Timedelta(seconds=s) for s, _, _ in rows],
        "price": [p for _, p, _ in rows],
        "size": [float(sz) for _, _, sz in rows],
    })


def test_full_fill_size_weighted_vwap():
    tr = _trades([(0, 10.00, 100), (10, 10.02, 200), (20, 10.05, 300)])
    r = replay_tape_fill(tr, qty=600, start_ts=_BASE, window_seconds=60)
    assert r.filled and r.filled_qty == 600 and r.n_prints == 3
    exp = (100 * 10.00 + 200 * 10.02 + 300 * 10.05) / 600
    assert r.avg_fill_price == pytest.approx(exp)
    assert r.fill_fraction == 1.0


def test_partial_fill_consumes_in_time_order():
    tr = _trades([(0, 10.00, 100), (10, 10.02, 200), (20, 10.05, 300)])
    r = replay_tape_fill(tr, qty=500, start_ts=_BASE, window_seconds=60)
    assert r.filled and r.filled_qty == 500
    exp = (100 * 10.00 + 200 * 10.02 + 200 * 10.05) / 500  # only 200 of the last print
    assert r.avg_fill_price == pytest.approx(exp)


def test_partial_when_window_volume_insufficient():
    tr = _trades([(0, 10.00, 100), (10, 10.02, 200)])  # 300 total
    r = replay_tape_fill(tr, qty=1000, start_ts=_BASE, window_seconds=60)
    assert not r.filled
    assert r.filled_qty == 300
    assert r.fill_fraction == pytest.approx(0.3)
    assert r.window_qty == 300


def test_window_excludes_late_prints():
    tr = _trades([(0, 10.00, 100), (120, 9.50, 1000)])  # 2nd print 120s out
    r = replay_tape_fill(tr, qty=500, start_ts=_BASE, window_seconds=60)
    assert r.filled_qty == 100
    assert r.avg_fill_price == pytest.approx(10.00)


def test_no_fill_when_trades_absent_or_empty():
    assert not replay_tape_fill(None, qty=100, start_ts=_BASE, window_seconds=60).filled
    empty = replay_tape_fill(pd.DataFrame(), qty=100, start_ts=_BASE, window_seconds=60)
    assert empty.filled_qty == 0 and not empty.filled


def test_sell_stop_trigger_keeps_prints_at_or_below():
    tr = _trades([(0, 10.00, 100), (10, 9.95, 200), (20, 9.90, 300)])
    r = replay_tape_fill(tr, qty=400, start_ts=_BASE, window_seconds=60, max_price=9.95)
    assert r.filled_qty == 400  # 200@9.95 + 200 of 300@9.90 (10.00 excluded)
    exp = (200 * 9.95 + 200 * 9.90) / 400
    assert r.avg_fill_price == pytest.approx(exp)


def test_sell_target_trigger_keeps_prints_at_or_above():
    tr = _trades([(0, 10.00, 100), (10, 10.10, 200), (20, 9.90, 300)])
    r = replay_tape_fill(tr, qty=250, start_ts=_BASE, window_seconds=60, min_price=10.10)
    assert r.filled_qty == 200 and not r.filled  # only the 10.10 print qualifies
    assert r.avg_fill_price == pytest.approx(10.10)


def test_participation_caps_capture_per_print():
    tr = _trades([(0, 10.00, 1000)])
    r = replay_tape_fill(tr, qty=1000, start_ts=_BASE, window_seconds=60, participation=0.5)
    assert r.filled_qty == 500 and not r.filled
    assert r.window_qty == 500


def test_make_trades_supplier_reads_lake_and_empty_when_absent(tmp_path):
    from bowaka_common.marketdata import layout
    from bowaka_v2_lab.data.suppliers import make_trades_supplier

    # Empty when the lake has no trades/ partitions (the case until PA.4 lands).
    sup = make_trades_supplier(tmp_path, feed="sip")
    assert sup("AAA", "2026-05-01 13:00", "2026-05-01 15:00").empty

    # Write a tiny trades partition + read it back through the supplier.
    ts = pd.to_datetime(["2026-05-01 14:00:00", "2026-05-01 14:00:30"], utc=True)
    df = pd.DataFrame({"symbol": ["AAA"] * 2, "timestamp": ts, "price": [10.0, 10.01],
                       "size": [100.0, 200.0], "exchange": ["V"] * 2,
                       "conditions": ["@"] * 2, "tape": ["C"] * 2, "trade_id": [1, 2]})
    p = layout.trades_path(tmp_path, "AAA", 2026, 5, feed="sip")
    p.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(p, index=False)
    out = make_trades_supplier(tmp_path, feed="sip")("AAA", "2026-05-01 13:00", "2026-05-01 15:00")
    assert len(out) == 2

    # The tape oracle consumes exactly what the supplier returns.
    r = replay_tape_fill(out, qty=250, start_ts="2026-05-01 14:00:00", window_seconds=120)
    assert r.filled and r.filled_qty == 250
