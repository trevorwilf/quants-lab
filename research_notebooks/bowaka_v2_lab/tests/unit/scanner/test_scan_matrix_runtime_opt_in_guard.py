"""Scan-matrix runtime opt-in is refused until parity is proven.

Matrix doc §17.2 / Phase 9 scaffolding. The Phase 8 builder ships fully
(matrix can be precomputed via the CLI), but the matrix-backed scanner
runtime is still scaffolding — flipping
``optuna.acceleration.scan_matrix.enabled=True`` raises a clear error
at backtest start instead of silently using a half-implemented evaluator.
"""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from bowaka_v2_lab.scanner.scan_matrix_runtime import (
    MatrixRuntimeNotImplementedError,
    assert_backtester_matrix_opt_in_is_supported,
    evaluate_one_scan_from_matrix,
    evaluate_one_scan_from_matrix_vectorized,
)


def test_assert_disabled_passes():
    """``enabled=False`` is a no-op."""
    assert_backtester_matrix_opt_in_is_supported(enabled=False)


def test_assert_enabled_with_non_disabled_runtime_mode_raises():
    """Speedup report v2 §6.1 / Phase 6: ``runtime_mode != 'disabled'`` raises.

    Phase 6 refactored the guard to a three-mode resolution. ``enabled=True``
    alone with the default ``runtime_mode='disabled'`` no longer raises (the
    matrix can be built for inspection without firing the runtime path).
    Non-disabled modes — compatibility / vectorized — are still
    scaffolding-only and refused with an actionable message.
    """
    with pytest.raises(MatrixRuntimeNotImplementedError) as info:
        assert_backtester_matrix_opt_in_is_supported(
            enabled=True, runtime_mode="compatibility", parity_manifest_present=True,
        )
    msg = str(info.value)
    assert "runtime_mode" in msg or "scan-matrix" in msg or "scan_matrix" in msg
    assert "disabled" in msg.lower() or "parity" in msg.lower()


def test_assert_enabled_with_default_runtime_mode_is_a_no_op():
    """``enabled=True`` with the default ``runtime_mode='disabled'`` is admissible
    — Phase 6 lets the matrix be built for inspection without firing the
    runtime path."""
    assert_backtester_matrix_opt_in_is_supported(enabled=True, runtime_mode="disabled")


def test_row_wise_evaluator_raises_scaffolding_error():
    with pytest.raises(MatrixRuntimeNotImplementedError):
        evaluate_one_scan_from_matrix(
            cfg={}, matrix_session=MagicMock(), state={}, scan_idx=0,
            consumer=MagicMock(),
        )


def test_vectorized_evaluator_raises_scaffolding_error():
    with pytest.raises(MatrixRuntimeNotImplementedError):
        evaluate_one_scan_from_matrix_vectorized(
            cfg={}, matrix_session=MagicMock(), state={}, scan_idx=0,
            consumer=MagicMock(),
        )


def test_backtester_refuses_matrix_enabled_at_run_start(tmp_path):
    """``run_backtest`` raises when the scan_matrix.enabled flag is true."""
    import datetime as _dt
    from pathlib import Path

    import pandas as pd

    from bowaka_v2_lab.config.paths import BowakaV2Paths
    from bowaka_v2_lab.sim.backtester import run_backtest
    from tests.fixtures.build_daily_fixture import make_daily_bars
    from tests.fixtures.build_minute_fixture import make_minute_bars

    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5,
                             minute_volume=10_000)
    daily = make_daily_bars("AAA", _dt.date(2024, 9, 1), n_sessions=5)
    universe = {
        sd: {"universe_hash": "sha256:t",
             "symbols": [{"symbol": "AAA", "exchange": "NASDAQ",
                          "venue_code": "XNAS",
                          "instrument_class": "operating_equity",
                          "eligible_for_bowaka_equity_bucket": True}]}
    }
    daily_cache = {sd: pd.DataFrame([{"symbol": "AAA", "prior_close": 100.0,
                                       "avg_dollar_volume_20d": 5_000_000,
                                       "prior_atr_pct": 0.02,
                                       "ema_slope_prior": 0.01}])}
    cfg = {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {}, "execution": {"max_spread_bps": 200,
                                       "max_quote_age_seconds": 60,
                                       "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                  "max_gross_exposure_pct": 0.5, "daily_loss_pct": 0.5,
                  "max_stopouts_per_day": 4,
                  "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10,
                   "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04",
                      "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "optuna": {"acceleration": {"scan_matrix": {
            "enabled": True,
            # Speedup report v2 §6.1 / Phase 6 — force runtime_mode=
            # "compatibility" so the backtester opt-in guard fires.
            "runtime_mode": "compatibility",
            "require_parity_manifest": True,
        }}},
    }
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    with pytest.raises(MatrixRuntimeNotImplementedError):
        run_backtest(
            cfg=cfg, sessions=[sd],
            scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=lambda sym, ts: bars,
            daily_bars_supplier=lambda sym, d: daily[daily["session_date"] == d],
            initial_bankroll=10_000.0, paths=paths,
        )


def test_backtester_default_scan_matrix_flag_does_not_trigger_guard(tmp_path):
    """With the flag at default (False / absent) run_backtest does NOT raise."""
    import datetime as _dt
    from pathlib import Path

    import pandas as pd

    from bowaka_v2_lab.config.paths import BowakaV2Paths
    from bowaka_v2_lab.sim.backtester import run_backtest
    from tests.fixtures.build_daily_fixture import make_daily_bars
    from tests.fixtures.build_minute_fixture import make_minute_bars

    sd = _dt.date(2024, 9, 4)
    bars = make_minute_bars("AAA", sd, minutes=30, drift_per_minute=0.5,
                             minute_volume=10_000)
    daily = make_daily_bars("AAA", _dt.date(2024, 9, 1), n_sessions=5)
    universe = {
        sd: {"universe_hash": "sha256:t",
             "symbols": [{"symbol": "AAA", "exchange": "NASDAQ",
                          "venue_code": "XNAS",
                          "instrument_class": "operating_equity",
                          "eligible_for_bowaka_equity_bucket": True}]}
    }
    daily_cache = {sd: pd.DataFrame([{"symbol": "AAA", "prior_close": 100.0,
                                       "avg_dollar_volume_20d": 5_000_000,
                                       "prior_atr_pct": 0.02,
                                       "ema_slope_prior": 0.01}])}
    cfg = {
        "strategy_id": "bowaka_v2", "strategy_version": "0.1.0",
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": {}, "execution": {"max_spread_bps": 200,
                                       "max_quote_age_seconds": 60,
                                       "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                  "max_gross_exposure_pct": 0.5, "daily_loss_pct": 0.5,
                  "max_stopouts_per_day": 4,
                  "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10,
                   "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04",
                      "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
    }
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=Path("ignored.yml"),
    )
    # Must NOT raise the Phase 9 guard; backtest completes.
    result = run_backtest(
        cfg=cfg, sessions=[sd],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars,
        daily_bars_supplier=lambda sym, d: daily[daily["session_date"] == d],
        initial_bankroll=10_000.0, paths=paths,
    )
    assert result.artifact_mode == "full"
