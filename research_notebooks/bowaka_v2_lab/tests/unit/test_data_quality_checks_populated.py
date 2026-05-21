"""Realism Phase 2 — ``data_quality_report.json["checks"]`` is non-empty after a run.

Builds a small synthetic lake (a self-contained sample of the supplied lake's
shape, including an ``_ingestion/audits`` parquet) and runs the backtester
against it; the emitted DQ report must carry substantive checks.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake, make_lake_suppliers
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.sim.replay_fixtures import synthetic_universe


def _write(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _build_lake_with_audit(root: Path, symbol: str, session: dt.date) -> None:
    """A minimal lake: daily + minute bars, manifest, and a research-audit parquet."""
    ddates = [session - dt.timedelta(days=i) for i in range(80, -1, -1)]
    _write(
        layout.daily_bars_path(root, symbol),
        pd.DataFrame(
            {
                "symbol": [symbol] * len(ddates),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates],
                "open": [100.0] * len(ddates),
                "high": [101.0] * len(ddates),
                "low": [99.0] * len(ddates),
                "close": [100.0] * len(ddates),
                "volume": [1_000_000] * len(ddates),
                "session_date": ddates,
            }
        ),
    )
    mts = [pd.Timestamp(f"{session} 13:30", tz="UTC") + pd.Timedelta(minutes=i) for i in range(60)]
    _write(
        layout.minute_bars_path(root, symbol, session.year, session.month),
        pd.DataFrame(
            {
                "symbol": [symbol] * 60,
                "timestamp": mts,
                "open": [100.0] * 60,
                "high": [101.0] * 60,
                "low": [99.0] * 60,
                "close": [100.5] * 60,
                "volume": [5000.0] * 60,
            }
        ),
    )
    # Lake manifest.
    mpath = layout.ingestion_manifest_path(root)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(
        json.dumps(
            {"feed": "iex", "adjustment": "raw", "dataset_hashes": {"lake": "sha256:cafe"}}
        ),
        encoding="utf-8",
    )
    # Research-audit parquet — same column shape as the supplied lake.
    audit_dir = layout.ingestion_dir(root) / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [
            {
                "symbol": symbol,
                "feed": "iex",
                "timeframe": "1d",
                "start": "2024-06-01",
                "end": session.isoformat(),
                "expected_sessions": 81,
                "observed_sessions": 81,
                "missing_sessions": 0,
                "duplicate_sessions": 0,
                "ohlc_violations": 0,
                "zero_volume_sessions": 0,
                "large_gap_flags": 0,
                "passed_research_audit": True,
                "warnings": [],
                "audit_run_id": "audit_2024-09-01T000000Z_iex",
            }
        ]
    ).to_parquet(audit_dir / "audit_2024-09-01T000000Z_iex.parquet", index=False)


def _cfg(lake_root: Path) -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": {"mode": "smoke_fixture"},
        "market_data": {
            "feed": "iex",
            "max_bar_age_seconds": 600,
            "minute_bar_source": "alpaca",
            "daily_bar_source": "alpaca",
            "shared_root": str(lake_root),
        },
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0},
        "signals": {"allow_unknown_instrument_class_for_research": False},
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                 "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                 "max_stopouts_per_day": 4, "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10, "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-04", "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                  "data_root": "research_notebooks/bowaka_v2_lab/data",
                  "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }


def test_data_quality_report_checks_non_empty_on_lake_run(tmp_path):
    lake = tmp_path / "lake"
    symbol = "AAA"
    session = dt.date(2024, 9, 4)
    _build_lake_with_audit(lake, symbol, session)

    cfg = _cfg(lake)
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, [symbol], session, feed="iex")}
    universe = {session: synthetic_universe([symbol])}

    result = run_backtest(
        cfg=cfg,
        sessions=[session],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        initial_bankroll=10_000.0,
        paths=paths,
        run_dir=tmp_path / "run",
    )

    dq = json.loads((result.run_dir / "data_quality_report.json").read_text())
    assert dq["checks"], "data_quality_report.json checks must be non-empty"
    assert dq["regime"] == "lake"
    names = {c["name"] for c in dq["checks"]}
    # Audit-derived + per-run coverage + adjustment + quote checks all present.
    assert "audit_passed_research_audit" in names
    assert "coverage_missing" in names
    assert "adjustment_mismatch" in names
    assert "quotes_partitions_available" in names
    # Every check carries the required shape.
    for c in dq["checks"]:
        assert set(c.keys()) >= {"name", "status", "count", "threshold", "source_file", "evidence"}
        assert c["status"] in ("pass", "fail", "warn")


def test_data_quality_report_checks_non_empty_on_synthetic_run(tmp_path):
    """Synthetic runs still emit a labelled, non-empty check set (never []) ."""
    from bowaka_v2_lab.sim.replay_fixtures import synthetic_daily_cache

    cfg = _cfg(tmp_path / "unused_lake")
    cfg["market_data"]["minute_bar_source"] = "fixture"
    cfg["market_data"]["daily_bar_source"] = "fixture"
    cfg["market_data"].pop("shared_root", None)
    session = dt.date(2024, 9, 4)
    symbol = "AAA"

    def minute_supplier(sym, ts):
        open_et = pd.Timestamp(session, tz="America/New_York") + pd.Timedelta(hours=9, minutes=30)
        return pd.DataFrame(
            [{"symbol": sym, "timestamp": (open_et + pd.Timedelta(minutes=i)).tz_convert("UTC"),
              "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 5000.0}
             for i in range(30)]
        )

    def daily_supplier(sym, sd):
        return pd.DataFrame(
            [{"symbol": sym, "session_date": sd, "open": 100.0, "high": 110.0,
              "low": 98.0, "close": 108.0, "volume": 100_000}]
        )

    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    result = run_backtest(
        cfg=cfg,
        sessions=[session],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session={session: synthetic_universe([symbol])},
        daily_cache_by_session={session: synthetic_daily_cache([symbol])},
        minute_bars_supplier=minute_supplier,
        daily_bars_supplier=daily_supplier,
        initial_bankroll=10_000.0,
        paths=paths,
        run_dir=tmp_path / "run_synth",
    )
    dq = json.loads((result.run_dir / "data_quality_report.json").read_text())
    assert dq["checks"], "synthetic run DQ report must still be non-empty"
    assert dq["regime"] == "synthetic"
    assert any(c["name"] == "synthetic_data" for c in dq["checks"])
