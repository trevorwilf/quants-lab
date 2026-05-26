"""Backtester raises ``StartupDataQualityError`` (not a generic ``RuntimeError``).

Speedup report §4 P0-A / §5.1 / Phase 0 task 2. The pre-remediation backtester
raised a bare ``RuntimeError(startup_dq_failure)`` at the abort point; the
Optuna runner's broad ``except Exception`` matched it and degraded the fold to
a sentinel score, masking the structural rejection. The replacement type is a
``DataQualityError`` subclass so the runner's existing structural handler
``except DataQualityError: raise`` propagates it.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import pytest

import bowaka_v2_lab.sim.backtester as backtester
from bowaka_common.marketdata import MarketDataStore, layout
from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.data_quality import (
    DataQualityError,
    StartupDataQualityError,
)
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake, make_lake_suppliers
from bowaka_v2_lab.universe.builder import build_pit_universe_for_sessions
from tests.fixtures.universe_fixture import write_lake_asset_master

_LAB_ROOT = Path(__file__).resolve().parents[3]


def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _build_minimal_lake(root: Path, symbol: str, session: dt.date) -> None:
    """A minimal IEX lake — enough to run the backtester past schema checks."""
    ddates = [session - dt.timedelta(days=i) for i in range(80, -1, -1)]
    _write(
        layout.daily_bars_path(root, symbol, feed="iex"),
        pd.DataFrame(
            {
                "symbol": [symbol] * len(ddates),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates],
                "open": [10.0] * len(ddates), "high": [10.1] * len(ddates),
                "low": [9.9] * len(ddates), "close": [10.0] * len(ddates),
                "volume": [1_000_000] * len(ddates), "session_date": ddates,
            }
        ),
    )
    mts = [pd.Timestamp(f"{session} 13:30", tz="UTC") + pd.Timedelta(minutes=i) for i in range(60)]
    _write(
        layout.minute_bars_path(root, symbol, session.year, session.month, feed="iex"),
        pd.DataFrame(
            {
                "symbol": [symbol] * 60, "timestamp": mts,
                "open": [10.0] * 60, "high": [10.1] * 60, "low": [9.9] * 60,
                "close": [10.05] * 60, "volume": [5000.0] * 60,
            }
        ),
    )
    mpath = layout.ingestion_manifest_path(root)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(
        json.dumps({"feed": "iex", "adjustment": "raw", "dataset_hashes": {"lake": "sha256:raw"}}),
        encoding="utf-8",
    )
    audit_dir = layout.ingestion_dir(root) / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{
            "symbol": symbol, "feed": "iex", "timeframe": "1d",
            "start": "2024-06-01", "end": session.isoformat(),
            "expected_sessions": 81, "observed_sessions": 81,
            "missing_sessions": 0, "duplicate_sessions": 0, "ohlc_violations": 0,
            "zero_volume_sessions": 0, "large_gap_flags": 0,
            "passed_research_audit": True, "warnings": [],
            "audit_run_id": "audit_2024-09-01T000000Z_iex",
        }]
    ).to_parquet(audit_dir / "audit_2024-09-01T000000Z_iex.parquet", index=False)
    write_lake_asset_master(root, [symbol])


def test_run_backtest_raises_startup_dq_error_when_evaluate_returns_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Forcing ``evaluate_startup_dq`` to return a non-None reason raises
    :class:`StartupDataQualityError` from the backtester.
    """
    symbol, session = "AAA", dt.date(2024, 9, 4)
    lake = tmp_path / "lake"
    _build_minimal_lake(lake, symbol, session)
    cfg = load_config(_LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code.yml")
    cfg.pop("_source_path", None)
    cfg["market_data"]["shared_root"] = str(lake)
    cfg["universe"] = {**cfg.get("universe", {}), "min_adv_dollars": 0,
                       "min_price": 1.0, "max_price": 1_000.0}
    cfg["backtest"] = {"start_date": session.isoformat(), "end_date": session.isoformat(),
                       "cost_stress": "base"}
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, [symbol], session, feed="iex")}
    universe = build_pit_universe_for_sessions([session], cfg, MarketDataStore(lake))

    # Force the gate to fire even if the lake/config combo would otherwise pass.
    monkeypatch.setattr(
        backtester, "evaluate_startup_dq",
        lambda report, *, simulation_mode: "forced failure",
    )

    with pytest.raises(StartupDataQualityError, match="forced failure"):
        backtester.run_backtest(
            cfg=cfg, sessions=[session],
            scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=minute_supplier, daily_bars_supplier=daily_supplier,
            initial_bankroll=10_000.0, paths=paths, run_dir=tmp_path / "run",
        )


def test_startup_dq_error_can_be_caught_as_data_quality_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The structural handler catches by ``DataQualityError`` — the subclass propagates.

    Mirror of the previous test but asserts the inheritance chain at the catch
    site (the production code in ``walkforward_runner._run_validation_folds``
    catches ``structural_exceptions()`` which binds ``DataQualityError``).
    """
    symbol, session = "AAA", dt.date(2024, 9, 4)
    lake = tmp_path / "lake"
    _build_minimal_lake(lake, symbol, session)
    cfg = load_config(_LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code.yml")
    cfg.pop("_source_path", None)
    cfg["market_data"]["shared_root"] = str(lake)
    cfg["universe"] = {**cfg.get("universe", {}), "min_adv_dollars": 0,
                       "min_price": 1.0, "max_price": 1_000.0}
    cfg["backtest"] = {"start_date": session.isoformat(), "end_date": session.isoformat(),
                       "cost_stress": "base"}
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, [symbol], session, feed="iex")}
    universe = build_pit_universe_for_sessions([session], cfg, MarketDataStore(lake))

    monkeypatch.setattr(
        backtester, "evaluate_startup_dq",
        lambda report, *, simulation_mode: "forced again",
    )

    caught: Exception | None = None
    try:
        backtester.run_backtest(
            cfg=cfg, sessions=[session],
            scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=minute_supplier, daily_bars_supplier=daily_supplier,
            initial_bankroll=10_000.0, paths=paths, run_dir=tmp_path / "run",
        )
    except DataQualityError as exc:
        caught = exc
    assert isinstance(caught, StartupDataQualityError)
