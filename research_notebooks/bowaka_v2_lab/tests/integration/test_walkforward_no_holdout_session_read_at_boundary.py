"""No fold reads a holdout-window session at the boundary (speedup §3 / audit §P0-002).

When ``val_end == final_holdout_start`` and the boundary date is a trading
day, the old closed-closed enumerator silently included the holdout's first
session in the validation window. Phase 0 makes the enumeration half-open;
this integration test wraps :meth:`MarketDataStore.minute_bars` and asserts
no recorded read window includes any session date ``>= final_holdout_start``.
"""
from __future__ import annotations

import datetime as dt

import pandas as pd

from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def test_no_minute_read_touches_a_holdout_session(tmp_path, lab_root, monkeypatch):
    lake = tmp_path / "lake"
    # 2024-01-01 .. 2024-05-01 with 1/1/1 month walk-forward → final_holdout
    # starts around 2024-04-01 (Mon) which is a trading day.
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml", lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=1,
    )

    # Hook MarketDataStore.minute_bars to record every (symbol, start, end)
    # read window the runner pulls from the lake.
    from bowaka_common.marketdata import store as _store_mod

    recorded: list[tuple[str, pd.Timestamp, pd.Timestamp]] = []
    original = _store_mod.MarketDataStore.minute_bars

    def wrapped(self, symbol, start, end, *args, **kwargs):
        recorded.append((symbol, pd.Timestamp(start), pd.Timestamp(end)))
        return original(self, symbol, start, end, *args, **kwargs)

    monkeypatch.setattr(_store_mod.MarketDataStore, "minute_bars", wrapped)

    result = run_walkforward_study(cfg, allow_smoke=True)

    final_holdout_start = dt.date.fromisoformat(result["final_holdout"][0])
    holdout_start_ts = pd.Timestamp(final_holdout_start, tz="UTC")

    # No recorded read window may overlap any holdout session date. The
    # exact equivalent of "covers a holdout session" is: window.start <
    # next_holdout_session AND window.end >= holdout_session.
    # Simpler half-open check: every read window must satisfy
    # window.start < holdout_start (a SCAN cutoff exactly at holdout_start
    # would imply the runner overran the validation boundary).
    leaking = [
        (sym, s, e) for (sym, s, e) in recorded
        if s.tz_convert("UTC") >= holdout_start_ts or e.tz_convert("UTC") >= holdout_start_ts
    ]
    # The legitimate holdout scorer ALSO uses MarketDataStore.minute_bars, but
    # this study run never calls it (run_walkforward_study does not score the
    # holdout — that's the explicit --final-holdout path).
    assert result["final_holdout_scored"] is False, (
        "study scored the holdout; the boundary-leak test is no longer valid"
    )
    assert not leaking, (
        f"{len(leaking)} minute-bar reads overlapped the holdout window "
        f"starting {final_holdout_start} (showing first 3): {leaking[:3]}"
    )
