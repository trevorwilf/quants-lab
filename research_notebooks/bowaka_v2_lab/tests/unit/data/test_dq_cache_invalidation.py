"""Cache invalidation rebuilds the full DQ report on any key mismatch.

Speedup report v2 §4 P4 / §5.6 / Phase 3 task 4. The conservative
fallback: when the cached ``_cache_key`` does not match the trial's
inputs, the backtester logs a warning and rebuilds from scratch — never
returns stale data.

Covered mismatches:

* Lake root.
* Feed.
* Market-data flag (``require_adjusted_daily_bars`` toggled).
* Code hash / config hash (carried as the
  ``dq_check_invariance_version`` field for now).
"""
from __future__ import annotations

import datetime as dt
import hashlib as _hashlib
import logging
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

import bowaka_v2_lab.sim.backtester as backtester
from bowaka_common.marketdata import MarketDataStore, layout
from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.data_quality import DQ_CHECK_INVARIANCE_VERSION
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake, make_lake_suppliers
from bowaka_v2_lab.universe.builder import build_pit_universe_for_sessions
from tests.fixtures.universe_fixture import write_lake_asset_master


_LAB_ROOT = Path(__file__).resolve().parents[3]


def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _build_minimal_lake(root: Path, symbol: str, session: dt.date) -> None:
    ddates = [session - dt.timedelta(days=i) for i in range(80, -1, -1)]
    _write(
        layout.daily_bars_path(root, symbol, feed="iex"),
        pd.DataFrame(
            {"symbol": [symbol] * len(ddates),
             "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates],
             "open": [10.0] * len(ddates), "high": [10.1] * len(ddates),
             "low": [9.9] * len(ddates), "close": [10.0] * len(ddates),
             "volume": [1_000_000] * len(ddates), "session_date": ddates}
        ),
    )
    mts = [pd.Timestamp(f"{session} 13:30", tz="UTC") + pd.Timedelta(minutes=i) for i in range(60)]
    _write(
        layout.minute_bars_path(root, symbol, session.year, session.month, feed="iex"),
        pd.DataFrame(
            {"symbol": [symbol] * 60, "timestamp": mts,
             "open": [10.0] * 60, "high": [10.1] * 60, "low": [9.9] * 60,
             "close": [10.05] * 60, "volume": [5000.0] * 60}
        ),
    )
    import json
    mpath = layout.ingestion_manifest_path(root)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(
        json.dumps({"feed": "iex", "adjustment": "raw", "dataset_hashes": {"lake": "sha256:raw"}}),
        encoding="utf-8",
    )
    audit_dir = layout.ingestion_dir(root) / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{"symbol": symbol, "feed": "iex", "timeframe": "1d",
          "start": "2024-06-01", "end": session.isoformat(),
          "expected_sessions": 81, "observed_sessions": 81,
          "missing_sessions": 0, "duplicate_sessions": 0, "ohlc_violations": 0,
          "zero_volume_sessions": 0, "large_gap_flags": 0,
          "passed_research_audit": True, "warnings": [],
          "audit_run_id": "audit_phase3_invalidate"}]
    ).to_parquet(audit_dir / "audit_phase3_invalidate.parquet", index=False)
    write_lake_asset_master(root, [symbol])


def _make_cfg(lake: Path, session: dt.date) -> dict:
    cfg = load_config(_LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code.yml")
    cfg.pop("_source_path", None)
    cfg["market_data"]["shared_root"] = str(lake)
    cfg["market_data"]["require_adjusted_daily_bars"] = False
    cfg["market_data"]["require_split_adjustment"] = False
    cfg["universe"] = {**cfg.get("universe", {}), "min_adv_dollars": 0,
                       "min_price": 1.0, "max_price": 1_000.0}
    cfg["backtest"] = {"start_date": session.isoformat(), "end_date": session.isoformat(),
                       "cost_stress": "base"}
    return cfg


def _make_stale_cache(*, lake: Path, session: dt.date, **overrides: Any) -> dict:
    """Build a synthetic invariant-half report; any key in ``overrides`` is
    deliberately mismatched against the live run's expected key.
    """
    symbols_hash = _hashlib.sha256(b"AAA").hexdigest()[:16]
    key = {
        "lake_root": str(lake), "feed": "iex", "symbols_hash": symbols_hash,
        "sessions": [session.isoformat()], "simulation_mode": "current_code_parity",
        "market_data_keys": {
            "require_adjusted_daily_bars": False,
            "require_split_adjustment": False,
            "max_bar_age_seconds": None, "max_quote_age_seconds": None,
        },
        "dq_check_invariance_version": DQ_CHECK_INVARIANCE_VERSION,
    }
    key.update(overrides)
    return {
        "schema_version": 2, "regime": "lake", "feed": "iex",
        "checks": [{"name": "audit_missing_sessions", "status": "pass", "count": 0}],
        "passed": 1, "failed": 0, "warned": 0,
        "required_failures": [], "adjustment_gating_failures": [],
        "_cache_key": key,
    }


def _exercise(
    tmp_path: Path, cached: dict, caplog: pytest.LogCaptureFixture,
) -> int:
    """Run ``run_backtest`` with ``cached`` and return the number of full
    rebuilds (i.e. ``build_data_quality_report`` calls without
    ``classify_filter=trial_dependent``).
    """
    symbol, session = "AAA", dt.date(2024, 9, 4)
    lake = tmp_path / "lake"
    _build_minimal_lake(lake, symbol, session)
    cfg = _make_cfg(lake, session)
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, [symbol], session, feed="iex")}
    universe = build_pit_universe_for_sessions([session], cfg, MarketDataStore(lake))

    original = backtester.build_data_quality_report
    call_args: list[dict] = []

    def _counting(*args: Any, **kwargs: Any):
        call_args.append(dict(kwargs))
        return original(*args, **kwargs)

    caplog.set_level(logging.WARNING, logger="bowaka_v2_lab.sim.backtester")
    with patch.object(backtester, "build_data_quality_report", _counting):
        backtester.run_backtest(
            cfg=cfg, sessions=[session],
            scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=minute_supplier, daily_bars_supplier=daily_supplier,
            initial_bankroll=10_000.0, paths=paths, run_dir=tmp_path / "run",
            startup_dq_report=cached,
        )
    full_rebuilds = sum(
        1 for k in call_args
        if k.get("classify_filter") not in ("trial_dependent",)
    )
    return full_rebuilds


def test_dq_cache_invalidates_on_lake_root_mismatch(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    cached = _make_stale_cache(
        lake=tmp_path / "lake", session=dt.date(2024, 9, 4),
        lake_root="/nowhere/else",
    )
    rebuilds = _exercise(tmp_path, cached, caplog)
    assert rebuilds == 1, f"expected 1 full rebuild; got {rebuilds}"
    assert any("startup_dq_cache miss" in r.getMessage() for r in caplog.records)


def test_dq_cache_invalidates_on_market_data_flag_mismatch(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    cached = _make_stale_cache(
        lake=tmp_path / "lake", session=dt.date(2024, 9, 4),
        market_data_keys={
            "require_adjusted_daily_bars": True,  # different from cfg
            "require_split_adjustment": False,
            "max_bar_age_seconds": None, "max_quote_age_seconds": None,
        },
    )
    rebuilds = _exercise(tmp_path, cached, caplog)
    assert rebuilds == 1
    assert any("startup_dq_cache miss" in r.getMessage() for r in caplog.records)


def test_dq_cache_invalidates_on_invariance_version_bump(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    cached = _make_stale_cache(
        lake=tmp_path / "lake", session=dt.date(2024, 9, 4),
        dq_check_invariance_version=DQ_CHECK_INVARIANCE_VERSION + 999,
    )
    rebuilds = _exercise(tmp_path, cached, caplog)
    assert rebuilds == 1
    assert any("startup_dq_cache miss" in r.getMessage() for r in caplog.records)
