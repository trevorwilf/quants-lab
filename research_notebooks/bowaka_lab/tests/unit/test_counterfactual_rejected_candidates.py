"""Phase 5: rejected candidates with would_enter=True when their entry rule fires."""

from __future__ import annotations

from datetime import date

import pandas as pd

from bowaka_lab.config.models import CounterfactualConfig
from bowaka_lab.sim.counterfactuals import run_grid_for_candidates
from bowaka_lab.sim.fill_model import BowakaFillModel


def _flat_minute_bars(symbol: str, trade_date: date) -> pd.DataFrame:
    minutes = pd.date_range(
        start=pd.Timestamp(trade_date).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30),
        periods=20,
        freq="1min",
        tz="America/New_York",
    ).tz_convert("UTC")
    rows = []
    p = 5.0
    for ts in minutes:
        rows.append({"symbol": symbol, "timestamp": ts, "open": p, "high": p * 1.01, "low": p * 0.99, "close": p, "volume": 100})
        p *= 1.005
    return pd.DataFrame(rows)


def test_rejected_candidates_included_in_grid():
    candidates = pd.DataFrame(
        [
            {"symbol": "AAA", "rank": 1, "passed_prefilter": True},
            {"symbol": "BBB", "rank": 2, "passed_prefilter": False},  # rejected
        ]
    )
    minute_bars = {
        "AAA": _flat_minute_bars("AAA", date(2026, 5, 11)),
        "BBB": _flat_minute_bars("BBB", date(2026, 5, 11)),
    }
    cfg = CounterfactualConfig(
        include_rejected_candidates=True,
        entry_rules=["fixed_time_0935"],
        stop_pct=[0.08],
        target_pct=[0.15],
        max_hold_days=[3],
        signal_fade_thresholds=[None],
        stop_manager_models=["none"],
    )
    df = run_grid_for_candidates(
        candidates=candidates,
        minute_bars_by_symbol=minute_bars,
        cfg=cfg,
        fill_model=BowakaFillModel(slippage_bps=0),
        signal_date=date(2026, 5, 8),
        trade_date=date(2026, 5, 11),
    )
    symbols = set(df["symbol"].tolist())
    assert "AAA" in symbols
    assert "BBB" in symbols
    bbb_rows = df[df["symbol"] == "BBB"]
    assert bool(bbb_rows.iloc[0]["would_enter"]) is True


def test_rejected_candidates_excluded_when_configured():
    candidates = pd.DataFrame(
        [
            {"symbol": "AAA", "rank": 1, "passed_prefilter": True},
            {"symbol": "BBB", "rank": 2, "passed_prefilter": False},
        ]
    )
    minute_bars = {
        "AAA": _flat_minute_bars("AAA", date(2026, 5, 11)),
        "BBB": _flat_minute_bars("BBB", date(2026, 5, 11)),
    }
    cfg = CounterfactualConfig(
        include_rejected_candidates=False,
        entry_rules=["fixed_time_0935"],
        stop_pct=[0.08],
        target_pct=[0.15],
        max_hold_days=[3],
        signal_fade_thresholds=[None],
        stop_manager_models=["none"],
    )
    df = run_grid_for_candidates(
        candidates=candidates,
        minute_bars_by_symbol=minute_bars,
        cfg=cfg,
        fill_model=BowakaFillModel(slippage_bps=0),
        signal_date=date(2026, 5, 8),
        trade_date=date(2026, 5, 11),
    )
    assert "BBB" not in df["symbol"].tolist()
