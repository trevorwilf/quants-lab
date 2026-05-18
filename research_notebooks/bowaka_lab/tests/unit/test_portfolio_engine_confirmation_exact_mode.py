"""Phase fidelity-3: exact-mode confirmation paths.

- exact + no quotes → entry SKIPPED with fail_reason='no_quote_exact_mode'.
- exact + confirmation disabled → engine init RAISES.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import datetime as _dt

import pandas as pd
import pytest

from bowaka_lab.config import load_config_file
from bowaka_lab.sim.portfolio_engine import BowakaPortfolioBacktester


EXACT_YAML = (
    Path(__file__).resolve().parents[2]
    / "configs"
    / "bowaka_exact_current_strategy.yml"
)


@pytest.fixture(autouse=True)
def _stub_env(monkeypatch):
    monkeypatch.setenv("MONGO_URI", "mongodb://stub:stub@localhost:27017/db?authSource=admin")


def _exact_cfg():
    cfg = load_config_file(EXACT_YAML)
    # model_copy bypasses validators — pass real date objects (the DataConfig
    # field is typed as ``date``).
    return cfg.model_copy(
        update={"data": cfg.data.model_copy(update={
            "start_date": _dt.date(2026, 5, 11),
            "end_date":   _dt.date(2026, 5, 12),
        })}
    )


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


def _candidates(signal_date):
    return pd.DataFrame([
        {"symbol": "AAA", "signal_date": signal_date, "rank": 1, "close": 5.0,
         "passed_prefilter": True, "avg_dollar_volume": 1e8},
    ])


def test_exact_mode_skips_when_no_quote():
    cfg = _exact_cfg()
    assert cfg.is_exact_mode
    signal_date = date(2026, 5, 11)
    trade_date = date(2026, 5, 12)
    runner = BowakaPortfolioBacktester(
        cfg,
        candidate_source=lambda sd: _candidates(signal_date) if sd == signal_date else pd.DataFrame(),
        minute_bars_for=lambda td, syms: _bars("AAA", trade_date) if td == trade_date else pd.DataFrame(),
        quote_loader=lambda td, syms: pd.DataFrame(),  # NO quotes
    )
    res = runner.run()
    assert len(res.trades) == 0, "exact mode must NOT enter without quotes"
    assert len(res.entry_skips) == 1
    assert res.entry_skips[0].fail_reason == "no_quote_exact_mode"


def test_exact_mode_raises_when_confirmation_disabled():
    cfg = _exact_cfg()
    cfg = cfg.model_copy(update={
        "entry": cfg.entry.model_copy(update={
            "intraday_confirmation": cfg.entry.intraday_confirmation.model_copy(
                update={"enabled": False}
            ),
        }),
    })
    with pytest.raises(RuntimeError, match="intraday_confirmation.enabled=true"):
        BowakaPortfolioBacktester(
            cfg,
            candidate_source=lambda sd: pd.DataFrame(),
            minute_bars_for=lambda td, syms: pd.DataFrame(),
        )


def test_exact_mode_invariants_block_loose_thresholds():
    """Phase fidelity-3 extension to assert_exact_mode_invariants."""
    from bowaka_lab.config import assert_exact_mode_invariants

    cfg = _exact_cfg()
    bad = cfg.model_copy(update={
        "entry": cfg.entry.model_copy(update={
            "intraday_confirmation": cfg.entry.intraday_confirmation.model_copy(
                update={"max_spread_pct": 0.02},
            ),
        }),
    })
    with pytest.raises(ValueError, match="max_spread_pct"):
        assert_exact_mode_invariants(bad)
