"""Realism Phase 2 — an intended_realism run fails on an adjustment mismatch.

When ``market_data.require_adjusted_daily_bars`` is true but the lake declares
``adjustment: raw`` (corporate actions not applied to daily bars), the run must
fail closed with ``adjustment_mismatch`` recorded as a required DQ failure.
``smoke_fixture`` runs against the same lake are *not* failed.
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


def _build_raw_lake(root: Path, symbol: str, session: dt.date) -> None:
    """A lake whose manifest declares ``adjustment: raw`` (full bar coverage)."""
    ddates = [session - dt.timedelta(days=i) for i in range(80, -1, -1)]
    _write(
        layout.daily_bars_path(root, symbol),
        pd.DataFrame(
            {
                "symbol": [symbol] * len(ddates),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates],
                "open": [100.0] * len(ddates), "high": [101.0] * len(ddates),
                "low": [99.0] * len(ddates), "close": [100.0] * len(ddates),
                "volume": [1_000_000] * len(ddates), "session_date": ddates,
            }
        ),
    )
    mts = [pd.Timestamp(f"{session} 13:30", tz="UTC") + pd.Timedelta(minutes=i) for i in range(60)]
    _write(
        layout.minute_bars_path(root, symbol, session.year, session.month),
        pd.DataFrame(
            {
                "symbol": [symbol] * 60, "timestamp": mts,
                "open": [100.0] * 60, "high": [101.0] * 60, "low": [99.0] * 60,
                "close": [100.5] * 60, "volume": [5000.0] * 60,
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
    # Phase 3: a minimal asset master so the run can build a PIT universe.
    write_lake_asset_master(root, [symbol])


def _cfg(lake_root: Path, *, mode: str, require_adjusted: bool) -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": {"mode": mode},
        # Wide price band — the fixture lake prices bars at $100, outside the
        # contract band ($1-20). The DQ-gate tests are not exercising the price
        # filter; the band is widened so the fixture symbol stays in the PIT
        # universe and the coverage/adjustment probes have a symbol to test.
        "universe": {"price_min": 1.0, "price_max": 1_000.0,
                     "avg_dollar_volume_min": 0},
        "market_data": {
            "feed": "iex", "max_bar_age_seconds": 600,
            "minute_bar_source": "alpaca", "daily_bar_source": "alpaca",
            "shared_root": str(lake_root),
            "require_adjusted_daily_bars": require_adjusted,
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


def _run(tmp_path, cfg, lake, symbol, session, run_dir_name):
    paths = BowakaV2Paths(
        lab_root=tmp_path / "bowaka_v2_lab",
        data_root=tmp_path / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "bowaka_v2_lab" / "artifacts",
        config_path=Path(""),
    )
    minute_supplier, daily_supplier = make_lake_suppliers(lake, feed="iex")
    daily_cache = {session: build_daily_cache_from_lake(lake, [symbol], session, feed="iex")}
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


def test_realism_run_fails_on_adjustment_mismatch(tmp_path):
    lake = tmp_path / "lake"
    symbol, session = "AAA", dt.date(2024, 9, 4)
    _build_raw_lake(lake, symbol, session)
    cfg = _cfg(lake, mode="intended_realism", require_adjusted=True)

    with pytest.raises(RuntimeError, match="adjustment_mismatch"):
        _run(tmp_path, cfg, lake, symbol, session, "run_fail")

    # The DQ report and a run manifest with the precise reason were written.
    run_dir = tmp_path / "run_fail"
    dq = json.loads((run_dir / "data_quality_report.json").read_text())
    adj = next(c for c in dq["checks"] if c["name"] == "adjustment_mismatch")
    assert adj["status"] == "fail"
    assert "adjustment_mismatch" in dq["required_failures"]
    rm = json.loads((run_dir / "run_manifest.json").read_text())
    assert rm["startup_dq_failure"]
    assert "adjustment_mismatch" in rm["startup_dq_failure"]


def test_smoke_run_not_failed_by_adjustment_mismatch(tmp_path):
    """The same lake + require_adjusted in smoke_fixture mode runs to completion."""
    lake = tmp_path / "lake"
    symbol, session = "AAA", dt.date(2024, 9, 4)
    _build_raw_lake(lake, symbol, session)
    cfg = _cfg(lake, mode="smoke_fixture", require_adjusted=True)

    result = _run(tmp_path, cfg, lake, symbol, session, "run_smoke")
    assert (result.run_dir / "summary.json").is_file()
    dq = json.loads((result.run_dir / "data_quality_report.json").read_text())
    # The mismatch is still recorded as a failed check...
    adj = next(c for c in dq["checks"] if c["name"] == "adjustment_mismatch")
    assert adj["status"] == "fail"
    # ...but smoke_fixture mode is not gated by it.
    rm = json.loads((result.run_dir / "run_manifest.json").read_text())
    assert rm.get("startup_dq_failure") is None


def test_realism_run_clears_dq_gate_when_adjustment_not_required(tmp_path):
    """A raw lake clears the DQ gate for realism mode when adjustment is not required.

    The minimal test config does not match the frozen live contract, so the run
    still aborts — but at the *config-parity* gate, which runs after the DQ gate.
    Proving the abort is parity (not ``adjustment_mismatch``) proves the DQ gate
    passed the run through. The DQ report records ``adjustment_mismatch: pass``.
    """
    lake = tmp_path / "lake"
    symbol, session = "AAA", dt.date(2024, 9, 4)
    _build_raw_lake(lake, symbol, session)
    cfg = _cfg(lake, mode="intended_realism", require_adjusted=False)

    try:
        result = _run(tmp_path, cfg, lake, symbol, session, "run_ok")
        run_dir = result.run_dir
    except RuntimeError as exc:
        # The run cleared the DQ gate; any abort here is the config-parity gate,
        # never a data-quality failure.
        assert "data-quality" not in str(exc)
        assert "adjustment_mismatch" not in str(exc)
        assert "coverage_missing" not in str(exc)
        run_dir = tmp_path / "run_ok"

    dq = json.loads((run_dir / "data_quality_report.json").read_text())
    adj = next(c for c in dq["checks"] if c["name"] == "adjustment_mismatch")
    assert adj["status"] == "pass"
    assert "adjustment_mismatch" not in dq["required_failures"]
