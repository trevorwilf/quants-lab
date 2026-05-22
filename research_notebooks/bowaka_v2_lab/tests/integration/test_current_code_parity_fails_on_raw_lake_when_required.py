"""current_code_parity also fails closed on a raw lake when adjustment required.

Realism remediation 2 Phase 1 (audit §P0-005). Before this remediation
``current_code_parity`` was NEVER gated by data quality. That is wrong for an
*actual-contract* run: the live contract requires adjusted daily bars, so a
``current_code_parity`` run whose config carries
``require_adjusted_daily_bars: true`` against a ``adjustment: raw`` lake must
also fail closed with ``adjustment_mismatch``. (Other DQ failures — coverage,
quotes — are still tolerated in parity mode.)
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import pytest

from bowaka_common.marketdata import MarketDataStore, layout
from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake, make_lake_suppliers
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.universe.builder import build_pit_universe_for_sessions
from tests.fixtures.universe_fixture import write_lake_asset_master

_LAB_ROOT = Path(__file__).resolve().parents[2]


def _write(path: Path, df: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _build_raw_lake(root: Path, symbol: str, session: dt.date) -> None:
    """An IEX lake whose ``_ingestion/manifest.json`` declares ``adjustment: raw``."""
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


def _load_shipped_for_fixture(lake_root: Path, session: dt.date) -> dict:
    """Load the shipped IEX current-code config, retargeted at the fixture lake."""
    cfg = load_config(_LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code.yml")
    cfg.pop("_source_path", None)
    cfg["market_data"]["shared_root"] = str(lake_root)
    cfg["universe"] = {**cfg.get("universe", {}), "min_adv_dollars": 0,
                       "min_price": 1.0, "max_price": 1_000.0}
    cfg["backtest"] = {"start_date": session.isoformat(), "end_date": session.isoformat(),
                       "cost_stress": "base"}
    return cfg


def test_current_code_parity_config_fails_closed_on_raw_lake(tmp_path: Path) -> None:
    symbol, session = "AAA", dt.date(2024, 9, 4)
    lake = tmp_path / "lake"
    _build_raw_lake(lake, symbol, session)
    cfg = _load_shipped_for_fixture(lake, session)
    assert cfg["simulation"]["mode"] == "current_code_parity"
    assert cfg["market_data"]["require_adjusted_daily_bars"] is True

    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, [symbol], session, feed="iex")}
    universe = build_pit_universe_for_sessions([session], cfg, MarketDataStore(lake))
    run_dir = tmp_path / "run_fail"

    with pytest.raises(RuntimeError, match="adjustment_mismatch"):
        run_backtest(
            cfg=cfg, sessions=[session],
            scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
            universe_snapshot_by_session=universe,
            daily_cache_by_session=daily_cache,
            minute_bars_supplier=minute_supplier, daily_bars_supplier=daily_supplier,
            initial_bankroll=10_000.0, paths=paths, run_dir=run_dir,
        )

    dq = json.loads((run_dir / "data_quality_report.json").read_text())
    adj = next(c for c in dq["checks"] if c["name"] == "adjustment_mismatch")
    assert adj["status"] == "fail"
    # adjustment_mismatch is an adjustment-gating failure (fires for parity too).
    assert "adjustment_mismatch" in dq.get("adjustment_gating_failures", [])
    rm = json.loads((run_dir / "run_manifest.json").read_text())
    assert "adjustment_mismatch" in rm["startup_dq_failure"]
    assert "current_code_parity run aborted" in rm["startup_dq_failure"]
