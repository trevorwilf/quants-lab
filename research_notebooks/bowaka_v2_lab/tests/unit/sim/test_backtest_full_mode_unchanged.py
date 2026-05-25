"""``artifact_mode="full"`` (the default) still writes every artifact.

Speedup report §5.1 / §11.2 Phase 1. Phase 1 introduces the ``artifact_mode``
parameter to ``run_backtest`` but defaults it to ``"full"``. This test
snapshots the run_dir produced by the default-mode backtest of a synthetic
fixture and asserts every entry in the existing ``_REQUIRED_ARTIFACTS`` list
is present — i.e. no full-mode regression.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import _REQUIRED_ARTIFACTS, run_backtest


def _cfg() -> dict:
    return {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                       "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                  "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                  "max_stopouts_per_day": 4,
                  "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10,
                   "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04",
                      "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
    }


def _paths(tmp_path: Path) -> BowakaV2Paths:
    return BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )


def _tiny_fixture_run(tmp_path: Path):
    from tests.fixtures.build_daily_fixture import make_daily_bars
    from tests.fixtures.build_minute_fixture import make_minute_bars

    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5,
                             minute_volume=10_000)
    daily = make_daily_bars("AAA", _dt.date(2024, 9, 1), n_sessions=5)
    universe = {
        sd: {"universe_hash": "sha256:t",
             "symbols": [{"symbol": "AAA", "exchange": "NASDAQ", "venue_code": "XNAS",
                          "instrument_class": "operating_equity",
                          "eligible_for_bowaka_equity_bucket": True}]}
    }
    daily_cache = {sd: pd.DataFrame([{"symbol": "AAA", "prior_close": 100.0,
                                       "avg_dollar_volume_20d": 5_000_000,
                                       "prior_atr_pct": 0.02,
                                       "ema_slope_prior": 0.01}])}
    return run_backtest(
        cfg=_cfg(), sessions=[sd],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars,
        daily_bars_supplier=lambda sym, d: daily[daily["session_date"] == d],
        initial_bankroll=10_000.0, paths=_paths(tmp_path),
    )


def test_default_mode_writes_required_artifact_set(tmp_path):
    """Every artifact in ``_REQUIRED_ARTIFACTS`` is written in default mode."""
    result = _tiny_fixture_run(tmp_path)
    assert result.artifact_mode == "full"
    missing = [rel for rel in _REQUIRED_ARTIFACTS if not (result.run_dir / rel).is_file()]
    assert not missing, f"full mode dropped required artifact(s): {missing}"


def test_default_mode_populates_enriched_in_memory_fields(tmp_path):
    """``BacktestResult`` exposes the new Phase 1 fields in both modes."""
    result = _tiny_fixture_run(tmp_path)
    assert result.artifact_mode == "full"
    # The new fields are always populated (lists/dicts), regardless of mode.
    assert isinstance(result.daily_equity, list)
    assert isinstance(result.execution_quality_rows, list)
    assert isinstance(result.quote_coverage_rows, list)
    assert isinstance(result.orders, list)
    assert isinstance(result.fills, list)
    assert isinstance(result.positions, list)
    assert isinstance(result.exit_analysis, dict)
