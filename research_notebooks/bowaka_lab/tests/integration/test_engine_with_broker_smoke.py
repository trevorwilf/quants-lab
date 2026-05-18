"""Phase fidelity-4: engine smoke test with broker enabled.

Runs ``BowakaPortfolioBacktester`` end-to-end with a deterministic broker
(all probabilities 0). Asserts trades happen, ``order_events.parquet`` is
populated, and each entered trade has both a ``parent_submitted`` and
``oco_attached`` event in the broker stream.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from bowaka_lab.config.models import BowakaBacktestConfig
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester


def _cfg():
    return BowakaBacktestConfig.model_validate(
        {
            "data": {"vendor": "alpaca", "feed": "iex",
                     "start_date": "2026-05-11", "end_date": "2026-05-12"},
            "portfolio": {"per_trade_notional": 1000.0,
                          "max_concurrent_positions": 5,
                          "max_total_entries_per_day": 5},
            "broker_sim": {
                "enabled": True,
                "parent_fill_latency_seconds": 0.0,
                "oco_attach_latency_seconds": 0.0,
                "broker_rejection_probability": 0.0,
                "partial_fill_probability": 0.0,
                "oco_attach_failure_probability": 0.0,
            },
        }
    )


def _candidates(signal_date):
    return pd.DataFrame([
        {"symbol": "AAA", "signal_date": signal_date, "rank": 1, "close": 5.0,
         "passed_prefilter": True, "avg_dollar_volume": 1e8},
    ])


def _bars(symbol, trade_date):
    minutes = pd.date_range(
        start=pd.Timestamp(trade_date).tz_localize("America/New_York")
        + pd.Timedelta(hours=9, minutes=30),
        periods=60, freq="1min", tz="America/New_York",
    ).tz_convert("UTC")
    return pd.DataFrame([
        {"symbol": symbol, "timestamp": ts, "open": 5.0, "high": 5.05, "low": 4.95,
         "close": 5.0, "volume": 100}
        for ts in minutes
    ])


def test_engine_smoke_with_broker_enabled():
    cfg = _cfg()
    signal_date = date(2026, 5, 11)
    trade_date = date(2026, 5, 12)
    runner = BowakaPortfolioBacktester(
        cfg,
        candidate_source=lambda sd: _candidates(signal_date) if sd == signal_date else pd.DataFrame(),
        minute_bars_for=lambda td, syms: _bars("AAA", trade_date) if td == trade_date else pd.DataFrame(),
    )
    res = runner.run()
    # Position opens on May 12 with constant prices → no exit → open at close.
    assert len(res.open_positions) == 1
    # Broker stream should have a parent_submitted + oco_attached pair.
    types = [e.event_type for e in res.broker_events]
    assert "parent_submitted" in types
    assert "oco_attach_pending" in types
    assert "oco_attached" in types
    df = res.order_events_df()
    assert df.shape[0] >= 3
    assert "event_id" in df.columns
    assert "protection_state" in df.columns
