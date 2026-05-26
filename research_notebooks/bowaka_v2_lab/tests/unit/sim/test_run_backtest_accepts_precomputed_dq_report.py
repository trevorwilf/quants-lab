"""``run_backtest`` accepts a precomputed startup_dq_report and merges halves.

Speedup report v2 §4 P4 / §5.6 / Phase 3 task 3. When the caller passes
``startup_dq_report=<invariant subset>`` with a matching ``_cache_key``,
the backtester reuses the cached checks and only recomputes the
trial-dependent half.
"""
from __future__ import annotations

import datetime as dt
import hashlib as _hashlib
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
          "audit_run_id": "audit_phase3_test"}]
    ).to_parquet(audit_dir / "audit_phase3_test.parquet", index=False)
    write_lake_asset_master(root, [symbol])


def _make_cfg(lake: Path, symbol: str, session: dt.date) -> dict:
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


def test_passing_a_matching_cached_report_skips_invariant_rebuild(
    tmp_path: Path,
) -> None:
    """When the cache key matches, ``build_data_quality_report`` is invoked
    only ONCE (for the trial-dependent half) — not twice."""
    symbol, session = "AAA", dt.date(2024, 9, 4)
    lake = tmp_path / "lake"
    _build_minimal_lake(lake, symbol, session)
    cfg = _make_cfg(lake, symbol, session)
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, [symbol], session, feed="iex")}
    universe = build_pit_universe_for_sessions([session], cfg, MarketDataStore(lake))

    # Build a synthetic invariant-half report with a matching cache key.
    symbols_hash = _hashlib.sha256(b"AAA").hexdigest()[:16]
    cached = {
        "schema_version": 2, "regime": "lake", "feed": "iex",
        "checks": [
            {"name": "audit_missing_sessions", "status": "pass", "count": 0},
        ],
        "passed": 1, "failed": 0, "warned": 0,
        "required_failures": [], "adjustment_gating_failures": [],
        "_cache_key": {
            "lake_root": str(lake),
            "feed": "iex",
            "symbols_hash": symbols_hash,
            "sessions": [session.isoformat()],
            "simulation_mode": cfg["simulation"]["mode"],
            "market_data_keys": {
                "require_adjusted_daily_bars": False,
                "require_split_adjustment": False,
                "max_bar_age_seconds": cfg["market_data"].get("max_bar_age_seconds"),
                "max_quote_age_seconds": cfg["market_data"].get("max_quote_age_seconds"),
            },
            "dq_check_invariance_version": DQ_CHECK_INVARIANCE_VERSION,
        },
    }

    # Count `build_data_quality_report` invocations.
    original = backtester.build_data_quality_report
    call_args: list[dict] = []

    def _counting(*args: Any, **kwargs: Any):
        call_args.append(dict(kwargs))
        return original(*args, **kwargs)

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

    # Exactly one call — for the trial-dependent half. The invariant half
    # came from the cache.
    assert len(call_args) == 1, (
        f"expected exactly one trial-dependent build; got {len(call_args)}"
    )
    assert call_args[0].get("classify_filter") == "trial_dependent"
