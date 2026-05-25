"""``artifact_mode="objective_minimal"`` produces an identical ``FoldResult``.

Speedup report §5.1 / §11.2 Phase 1 — the per-trial fast path. For a fixed
parameter set, run the same backtest in both ``"full"`` and
``"objective_minimal"`` modes; the resulting :class:`FoldResult` (built via
the legacy ``fold_result_from_report`` path for full, the new
``fold_result_from_backtest_result`` for minimal) must be field-by-field
equal within tolerance. The minimal-mode ``run_dir`` must contain none of
the artifact files.
"""
from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path

import pandas as pd
import pytest

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.optuna.objective import (
    compute_objective,
    fold_result_from_backtest_result,
    fold_result_from_report,
)
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


def _run(tmp_path: Path, *, artifact_mode: str):
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
    run_dir = tmp_path / artifact_mode / "run"
    return run_backtest(
        cfg=_cfg(), sessions=[sd],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=lambda sym, ts: bars,
        daily_bars_supplier=lambda sym, d: daily[daily["session_date"] == d],
        initial_bankroll=10_000.0,
        paths=_paths(tmp_path / artifact_mode),
        run_dir=run_dir,
        artifact_mode=artifact_mode,
    )


def test_objective_minimal_produces_same_fold_result(tmp_path):
    full = _run(tmp_path, artifact_mode="full")
    minimal = _run(tmp_path, artifact_mode="objective_minimal")

    assert full.artifact_mode == "full"
    assert minimal.artifact_mode == "objective_minimal"

    # FoldResult built two ways must agree field-by-field.
    full_report = json.loads((full.run_dir / "report.json").read_text(encoding="utf-8"))
    fr_full = fold_result_from_report("f0", full_report, full.summary)
    fr_min = fold_result_from_backtest_result("f0", minimal)

    for attr in (
        "net_return", "max_drawdown", "worst_day_loss", "turnover",
        "concentration", "n_trades", "ambiguous_bar_count",
        "missing_quote_count", "quote_coverage", "fill_rate",
    ):
        assert getattr(fr_full, attr) == pytest.approx(getattr(fr_min, attr)), (
            f"{attr} differs: full={getattr(fr_full, attr)!r} "
            f"min={getattr(fr_min, attr)!r}"
        )


def test_compute_objective_agrees_across_modes(tmp_path):
    full = _run(tmp_path, artifact_mode="full")
    minimal = _run(tmp_path, artifact_mode="objective_minimal")

    full_report = json.loads((full.run_dir / "report.json").read_text(encoding="utf-8"))
    fr_full = fold_result_from_report("f0", full_report, full.summary)
    fr_min = fold_result_from_backtest_result("f0", minimal)

    obj_full = compute_objective([fr_full]).objective
    obj_min = compute_objective([fr_min]).objective
    assert obj_full == pytest.approx(obj_min, abs=1e-9)


def test_minimal_mode_writes_no_artifact_files(tmp_path):
    minimal = _run(tmp_path, artifact_mode="objective_minimal")
    rd = minimal.run_dir
    # No required-artifact file may exist.
    leaked = [rel for rel in _REQUIRED_ARTIFACTS if (rd / rel).exists()]
    assert not leaked, f"objective_minimal leaked disk artifacts: {leaked}"
    # And no stray parquet/json under run_dir at all.
    stray = [p.relative_to(rd) for p in rd.rglob("*")
             if p.is_file() and p.suffix in {".parquet", ".jsonl", ".json", ".md"}]
    assert not stray, f"objective_minimal wrote non-required files: {stray}"


def test_minimal_mode_summary_matches_full_mode_summary(tmp_path):
    """The in-memory summary dicts agree across modes for keys we actually
    consume (the per-host fields like run_id will differ; deterministic
    business fields must match)."""
    full = _run(tmp_path, artifact_mode="full")
    minimal = _run(tmp_path, artifact_mode="objective_minimal")
    for key in (
        "n_trades", "win_rate", "total_pnl", "net_return_pct",
        "final_bankroll", "accepted_count", "rejected_count",
        "fills_count", "partial_fill_count", "fill_rate",
        "historical_quote_coverage_pct", "missing_quote_count",
        "fees_paid_total", "ambiguous_bar_count", "exit_slippage_bps",
    ):
        assert full.summary.get(key) == minimal.summary.get(key), (
            f"summary differs on {key}: full={full.summary.get(key)!r} "
            f"min={minimal.summary.get(key)!r}"
        )
