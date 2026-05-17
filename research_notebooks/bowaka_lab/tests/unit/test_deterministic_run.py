"""Phase 4: determinism — same inputs → byte-identical trades.parquet."""

from __future__ import annotations

import hashlib
from datetime import date

import pandas as pd

from bowaka_lab.config.models import BowakaBacktestConfig
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester


def _cfg():
    return BowakaBacktestConfig.model_validate(
        {
            "data": {"vendor": "alpaca", "feed": "iex", "start_date": "2026-05-11", "end_date": "2026-05-15"},
            "portfolio": {"per_trade_notional": 5000.0, "max_concurrent_positions": 5},
            "exits": {"stop_pct": 0.08, "target_pct": 0.15, "max_hold_days": 3},
        }
    )


def _make_candidates(symbol: str, signal_date: date) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "symbol": symbol,
                "signal_date": signal_date,
                "rank": 1,
                "close": 5.0,
                "passed_prefilter": True,
                "avg_dollar_volume": 1e8,
            }
        ]
    )


def _ramp_minute_bars(symbol: str, trade_date: date, final_pct: float) -> pd.DataFrame:
    minutes = pd.date_range(
        start=pd.Timestamp(trade_date).tz_localize("America/New_York") + pd.Timedelta(hours=9, minutes=30),
        periods=390,
        freq="1min",
        tz="America/New_York",
    ).tz_convert("UTC")
    rows = []
    base = 5.0
    for i, ts in enumerate(minutes):
        p = base * (1.0 + final_pct * (i / 389.0))
        rows.append({"symbol": symbol, "timestamp": ts, "open": p, "high": p * 1.001, "low": p * 0.999, "close": p, "volume": 100})
    df = pd.DataFrame(rows)
    df["session_date"] = df["timestamp"].dt.tz_convert("America/New_York").dt.date
    return df


def _run(cfg, candidates_by_session, minute_bars_by_date):
    runner = BowakaPortfolioBacktester(
        cfg,
        candidate_source=lambda sd: candidates_by_session.get(sd, pd.DataFrame()),
        minute_bars_for=lambda td, syms: minute_bars_by_date.get(td, pd.DataFrame()),
    )
    return runner.run()


def test_same_inputs_produce_same_trades():
    cfg = _cfg()
    candidates = {date(2026, 5, 8): _make_candidates("AAA", date(2026, 5, 8))}
    minute_bars = {date(2026, 5, 11): _ramp_minute_bars("AAA", date(2026, 5, 11), 0.20)}
    res_a = _run(cfg, candidates, minute_bars)
    res_b = _run(cfg, candidates, minute_bars)
    df_a = res_a.trades_df().sort_values("trade_id").reset_index(drop=True)
    df_b = res_b.trades_df().sort_values("trade_id").reset_index(drop=True)
    pd.testing.assert_frame_equal(df_a, df_b)


def test_byte_identical_serialization(tmp_path):
    cfg = _cfg()
    candidates = {date(2026, 5, 8): _make_candidates("AAA", date(2026, 5, 8))}
    minute_bars = {date(2026, 5, 11): _ramp_minute_bars("AAA", date(2026, 5, 11), 0.20)}
    res_a = _run(cfg, candidates, minute_bars)
    res_b = _run(cfg, candidates, minute_bars)
    pa = tmp_path / "a.parquet"
    pb = tmp_path / "b.parquet"
    res_a.trades_df().to_parquet(pa, index=False)
    res_b.trades_df().to_parquet(pb, index=False)
    ha = hashlib.sha256(pa.read_bytes()).hexdigest()
    hb = hashlib.sha256(pb.read_bytes()).hexdigest()
    assert ha == hb
