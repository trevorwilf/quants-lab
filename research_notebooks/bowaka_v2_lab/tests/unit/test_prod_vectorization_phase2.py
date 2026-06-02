"""Phase 2 — the vectorized prod helpers match the scalar reference exactly.

Covers the binding corrections from the speedup prompt's Appendix B:
  * forming-bar prefix arrays == ``aggregate_forming_session_bar`` (NaN-aware
    max/min/sum, per-column gating, single-bar, missing columns);
  * exit-walk first-touch == the iterrows semantics: 0.0/None coalesce to close
    (NOT NaN), stop checked before target (stop wins same-bar ties), no-touch ->
    time_stop, first-touch ordering across bars.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

_SCRIPTS = (
    Path(__file__).resolve().parents[2]
    / "reference" / "source_strategy" / "scripts"
)
if not (_SCRIPTS / "bowaka_v2_backtest.py").is_file():
    pytest.skip(
        "source-strategy mirror absent (reference/ is gitignored)",
        allow_module_level=True,
    )
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

import bowaka_v2_backtest as bt  # noqa: E402
import bowaka_v2_features as features  # noqa: E402

if not hasattr(bt, "_precompute_symbol_arrays"):  # mirror not Phase-2-vectorized
    pytest.skip(
        "source-strategy mirror is not Phase-2-vectorized",
        allow_module_level=True,
    )


def _minute(ts: str, o, h, l, c, v) -> dict:
    return {"timestamp": pd.Timestamp(ts, tz="UTC"),
            "open": o, "high": h, "low": l, "close": c, "volume": v}


# --- forming bar: prefix == aggregate_forming_session_bar -------------------
@pytest.mark.parametrize("rows", [
    [_minute("2026-05-19T14:30", 10, 11, 9, 10.5, 100),
     _minute("2026-05-19T14:31", 10.5, 12, 10, 11, 200),
     _minute("2026-05-19T14:32", 11, 11.5, 10.5, 11.2, 150)],
    # NaN high / low / volume on some bars (NaN-skipping must match pandas).
    [_minute("2026-05-19T14:30", 10, np.nan, 9, 10.5, 100),
     _minute("2026-05-19T14:31", 10.5, 12, np.nan, 11, np.nan),
     _minute("2026-05-19T14:32", 11, 11.5, 10.5, 11.2, 150)],
    # Single bar.
    [_minute("2026-05-19T14:30", 10, 11, 9, 10.5, 100)],
])
def test_forming_bar_prefix_matches_scalar(rows) -> None:
    df = pd.DataFrame(rows)
    pre = bt._precompute_symbol_arrays(df)
    for hi in range(1, len(df) + 1):
        got = bt._forming_bar_from_prefix(pre, hi)
        exp = features.aggregate_forming_session_bar(pre["df"].iloc[:hi])
        assert set(got) == set(exp)
        for k in exp:
            g, e = got[k], exp[k]
            if isinstance(e, float) and e != e:  # NaN
                assert isinstance(g, float) and g != g, (hi, k, g, e)
            else:
                assert g == e, (hi, k, g, e)


def test_forming_bar_missing_columns_gated() -> None:
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-05-19T14:30", tz="UTC")],
        "close": [10.0],
    })
    pre = bt._precompute_symbol_arrays(df)
    got = bt._forming_bar_from_prefix(pre, 1)
    exp = features.aggregate_forming_session_bar(df)
    assert got == exp  # open/high/low/volume all gate to None on both paths


# --- exit walk edge fixtures ------------------------------------------------
def _exit(rows, *, stop: float, target: float, entry_price: float = 10.0,
          qty: int = 100):
    bars = pd.DataFrame(rows)
    trade = bt.BacktestTrade(
        session_date="2026-05-19", symbol="X",
        entry_ts="2026-05-19T14:29:00+00:00", entry_price=entry_price, qty=qty,
        notional=qty * entry_price, stop_price=stop, target_price=target,
        max_hold_session_minutes=390, adv_at_entry=1e7, spread_bps_at_entry=5.0,
    )
    bt._manage_position(trade, bars, stop_price=stop, target_price=target,
                        cost_stress="base", adv=1e7)
    return trade


def test_exit_stop_first_touch() -> None:
    t = _exit([_minute("2026-05-19T14:30", 10, 10.5, 9.0, 10, 100)],
              stop=9.5, target=11.0)
    assert t.exit_reason == "stop_hit"


def test_exit_target_touch() -> None:
    t = _exit([_minute("2026-05-19T14:30", 10, 11.5, 9.8, 11, 100)],
              stop=9.0, target=11.0)
    assert t.exit_reason == "target_hit"


def test_exit_same_bar_stop_and_target_stop_wins() -> None:
    # Bar touches BOTH stop (low 8<=9) and target (high 12>=11); stop wins.
    t = _exit([_minute("2026-05-19T14:30", 10, 12, 8, 10, 100)],
              stop=9.0, target=11.0)
    assert t.exit_reason == "stop_hit"


def test_exit_no_touch_time_stop() -> None:
    t = _exit([_minute("2026-05-19T14:30", 10, 10.4, 9.6, 10.2, 100)],
              stop=9.0, target=11.0)
    assert t.exit_reason == "time_stop"


def test_exit_nan_high_low_does_not_trigger() -> None:
    # NaN is truthy under the ``or`` rule -> kept; NaN comparisons are False.
    t = _exit([_minute("2026-05-19T14:30", 10, np.nan, np.nan, 10.0, 100)],
              stop=9.0, target=11.0)
    assert t.exit_reason == "time_stop"


def test_exit_zero_low_coalesces_to_close() -> None:
    # low=0.0 is falsy -> coalesces to close (10.2); 10.2 > stop 9.0 -> no stop.
    # (Without coalescing, 0.0 <= 9.0 would falsely stop.)
    t = _exit([_minute("2026-05-19T14:30", 10, 10.4, 0.0, 10.2, 100)],
              stop=9.0, target=11.0)
    assert t.exit_reason == "time_stop"


def test_exit_first_touch_ordering() -> None:
    rows = [
        _minute("2026-05-19T14:30", 10, 10.4, 9.6, 10.2, 100),   # no touch
        _minute("2026-05-19T14:31", 10.2, 11.5, 9.8, 11, 100),   # target first
        _minute("2026-05-19T14:32", 11, 12, 8, 10, 100),          # stop, but later
    ]
    t = _exit(rows, stop=9.0, target=11.0)
    assert t.exit_reason == "target_hit"
    assert "14:31" in t.exit_ts
