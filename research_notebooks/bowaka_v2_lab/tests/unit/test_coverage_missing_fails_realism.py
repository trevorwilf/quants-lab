"""Realism Phase 2 — a missing minute partition fails an intended_realism run.

A lake is built with two requested symbols but minute bars for only one of them.
The per-run coverage probe finds the gap; with the missing fraction at or above
1% the ``intended_realism`` run fails closed. A ``smoke_fixture`` run against the
same lake completes (it is never gated by DQ).
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pandas as pd
import pytest

from bowaka_common.marketdata import MarketDataStore, layout
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.data.suppliers import build_daily_cache_from_lake, make_lake_suppliers
from bowaka_v2_lab.sim.backtester import run_backtest
from bowaka_v2_lab.universe.builder import build_pit_universe_for_sessions
from tests.fixtures.universe_fixture import write_lake_asset_master


def _write(path, df):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def _daily(symbol, session):
    ddates = [session - dt.timedelta(days=i) for i in range(80, -1, -1)]
    return pd.DataFrame(
        {
            "symbol": [symbol] * len(ddates),
            "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates],
            "open": [100.0] * len(ddates), "high": [101.0] * len(ddates),
            "low": [99.0] * len(ddates), "close": [100.0] * len(ddates),
            "volume": [1_000_000] * len(ddates), "session_date": ddates,
        }
    )


def _minute(symbol, session):
    mts = [pd.Timestamp(f"{session} 13:30", tz="UTC") + pd.Timedelta(minutes=i) for i in range(60)]
    return pd.DataFrame(
        {
            "symbol": [symbol] * 60, "timestamp": mts,
            "open": [100.0] * 60, "high": [101.0] * 60, "low": [99.0] * 60,
            "close": [100.5] * 60, "volume": [5000.0] * 60,
        }
    )


def _build_lake_missing_one_minute_partition(root: Path, session: dt.date) -> tuple[str, str]:
    """Two symbols with daily bars; minute bars present only for the first.

    Returns ``(covered_symbol, missing_symbol)``.
    """
    covered, missing = "AAA", "BBB"
    for sym in (covered, missing):
        _write(layout.daily_bars_path(root, sym), _daily(sym, session))
    # Minute bars for AAA only — BBB's minute partition is absent.
    _write(layout.minute_bars_path(root, covered, session.year, session.month),
           _minute(covered, session))

    mpath = layout.ingestion_manifest_path(root)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mpath.write_text(
        json.dumps({"feed": "iex", "adjustment": "raw", "dataset_hashes": {"lake": "sha256:gap"}}),
        encoding="utf-8",
    )
    audit_dir = layout.ingestion_dir(root) / "audits"
    audit_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        [{
            "symbol": sym, "feed": "iex", "timeframe": "1d",
            "start": "2024-06-01", "end": session.isoformat(),
            "expected_sessions": 81, "observed_sessions": 81,
            "missing_sessions": 0, "duplicate_sessions": 0, "ohlc_violations": 0,
            "zero_volume_sessions": 0, "large_gap_flags": 0,
            "passed_research_audit": True, "warnings": [],
            "audit_run_id": "audit_2024-09-01T000000Z_iex",
        } for sym in (covered, missing)]
    ).to_parquet(audit_dir / "audit_2024-09-01T000000Z_iex.parquet", index=False)
    # Phase 3: a minimal asset master so the run can build a PIT universe.
    # Both symbols have daily bars, so both are PIT-eligible — the coverage
    # probe then finds BBB's missing minute partition.
    write_lake_asset_master(root, [covered, missing])
    return covered, missing


def _cfg(lake_root: Path, *, mode: str) -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": {"mode": mode},
        # Wide price band — the fixture lake prices bars at $100, outside the
        # contract band ($1-20). The coverage-gate test is not exercising the
        # price filter; the band is widened so both fixture symbols stay in the
        # PIT universe and the coverage probe has symbols to test.
        "universe": {"price_min": 1.0, "price_max": 1_000.0,
                     "avg_dollar_volume_min": 0},
        "market_data": {
            "feed": "iex", "max_bar_age_seconds": 600,
            "minute_bar_source": "alpaca", "daily_bar_source": "alpaca",
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


def _run(tmp_path, cfg, lake, symbols, session, run_dir_name):
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, symbols, session, feed="iex")}
    # Phase 3: a point-in-time universe built from the lake asset master.
    universe = build_pit_universe_for_sessions([session], cfg, MarketDataStore(lake))
    return run_backtest(
        cfg=cfg, sessions=[session],
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe,
        daily_cache_by_session=daily_cache,
        minute_bars_supplier=minute_supplier, daily_bars_supplier=daily_supplier,
        initial_bankroll=10_000.0, paths=paths,
        run_dir=tmp_path / run_dir_name,
    )


def test_realism_run_fails_when_a_minute_partition_is_missing(tmp_path):
    lake = tmp_path / "lake"
    session = dt.date(2024, 9, 4)
    covered, missing = _build_lake_missing_one_minute_partition(lake, session)
    cfg = _cfg(lake, mode="intended_realism")

    with pytest.raises(RuntimeError, match="coverage_missing"):
        _run(tmp_path, cfg, lake, [covered, missing], session, "run_fail")

    run_dir = tmp_path / "run_fail"
    dq = json.loads((run_dir / "data_quality_report.json").read_text())
    cov = next(c for c in dq["checks"] if c["name"] == "coverage_missing")
    assert cov["status"] == "fail"
    assert cov["count"] >= 1
    # The missing symbol@date pair is named in the evidence.
    missing_pairs = cov["evidence"]["missing_minute"]
    assert any(missing in p for p in missing_pairs)
    rm = json.loads((run_dir / "run_manifest.json").read_text())
    assert rm["startup_dq_failure"]
    assert "coverage_missing" in rm["startup_dq_failure"]


def test_realism_run_fails_on_empty_universe(tmp_path):
    """A lake-backed realism run that resolves to zero symbols fails closed.

    Mirrors a SIP-feed config against an IEX-only lake: the universe resolves
    empty, so there are zero (symbol, session) pairs to test. ``coverage_missing``
    must ``fail`` rather than warn — a realism run with no data is degenerate.
    """
    from bowaka_v2_lab.data.data_quality import build_coverage_check

    check = build_coverage_check(
        requested_symbols=[],  # empty universe
        sessions=[dt.date(2024, 9, 4)],
        daily_bars_supplier=lambda s, d: None,
        minute_bars_supplier=lambda s, t: None,
        scan_times_per_session=lambda d: [pd.Timestamp(f"{d}T14:00:00", tz="UTC")],
    )
    assert check["name"] == "coverage_missing"
    assert check["status"] == "fail"
    assert "ZERO" in check["evidence"]["detail"]


def test_smoke_run_not_failed_by_missing_minute_partition(tmp_path):
    """The same gap in smoke_fixture mode runs to completion (DQ not gated)."""
    lake = tmp_path / "lake"
    session = dt.date(2024, 9, 4)
    covered, missing = _build_lake_missing_one_minute_partition(lake, session)
    cfg = _cfg(lake, mode="smoke_fixture")

    result = _run(tmp_path, cfg, lake, [covered, missing], session, "run_smoke")
    assert (result.run_dir / "summary.json").is_file()
    dq = json.loads((result.run_dir / "data_quality_report.json").read_text())
    cov = next(c for c in dq["checks"] if c["name"] == "coverage_missing")
    assert cov["status"] == "fail"  # still recorded
    rm = json.loads((result.run_dir / "run_manifest.json").read_text())
    assert rm.get("startup_dq_failure") is None  # but not gated
