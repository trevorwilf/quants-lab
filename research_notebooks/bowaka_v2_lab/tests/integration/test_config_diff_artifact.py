"""config_diff_vs_actual_bowaka_v2.yaml is emitted; realism mode fails on a mismatch.

Realism Phase 1, Task C/D. Every backtest writes the parity-diff artifact. An
``intended_realism`` run must abort at startup when the config has an
unannotated ``mismatch`` against the frozen live contract.
"""
from __future__ import annotations

import datetime as _dt

import pandas as pd
import pytest
import yaml

from bowaka_v2_lab import reference
from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.sim.backtester import run_backtest
from tests.fixtures.build_daily_fixture import make_daily_bars
from tests.fixtures.build_minute_fixture import make_minute_bars

# Full live signal-gate set, copied from the contract so an intended_realism
# config validates the SignalsConfig cross-field check.
_FULL_SIGNALS = {
    "rvol_so_far_min": 0.7, "projected_full_day_rvol_min": 0.5,
    "prior_atr_pct_min": 0.06, "range_expansion_so_far_min": 0.5,
    "close_location_so_far_min": 0.6, "ema_distance_min": -0.05,
    "ema_slope_min": -0.05, "price_min": 1.0, "price_max": 20.0,
    "avg_dollar_volume_min": 250000, "rvol_so_far_max": 8.0,
    "projected_full_day_rvol_max": 8.0, "range_expansion_so_far_max": 2.5,
    "gap_pct_max": 0.25, "current_return_pct_max": 0.5,
}


def _base_cfg(simulation: dict) -> dict:
    return {
        "strategy_id": "bowaka_v2",
        "strategy_version": "0.1.0",
        "simulation": simulation,
        "market_data": {"feed": "iex", "max_bar_age_seconds": 600},
        "scanner": {"max_candidates_per_scan": 5, "max_entries_per_scan": 3,
                    "min_signal_strength": 0.0, "signal_expiry_seconds": 600},
        "signals": dict(_FULL_SIGNALS),
        "execution": {"max_spread_bps": 200, "max_quote_age_seconds": 60,
                      "order_type": "marketable_limit"},
        "sizing": {"dollars_per_position": 1000, "max_position_dollars": 5000},
        "risk": {"max_concurrent_positions": 5, "max_total_entries_per_day": 12,
                 "max_gross_exposure_pct": 0.50, "daily_loss_pct": 0.50,
                 "max_stopouts_per_day": 4,
                 "stop_trading_after_consecutive_stopouts": 3},
        "exits": {"stop_loss_pct": 0.05, "take_profit_pct": 0.10, "max_hold_days": 3},
        "backtest": {"start_date": "2024-09-04", "end_date": "2024-09-05",
                     "cost_stress": "base"},
        "run": {"kind": "backtest", "seed": 1337},
        "paths": {"lab_root": "research_notebooks/bowaka_v2_lab",
                  "data_root": "research_notebooks/bowaka_v2_lab/data",
                  "artifact_root": "research_notebooks/bowaka_v2_lab/artifacts"},
    }


def _wire_run(tmp_path, cfg):
    paths = BowakaV2Paths(
        lab_root=tmp_path / "research_notebooks" / "bowaka_v2_lab",
        data_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "data",
        artifact_root=tmp_path / "research_notebooks" / "bowaka_v2_lab" / "artifacts",
        config_path=tmp_path / "ignored.yml",
    )
    sessions = [_dt.date(2024, 9, 4), _dt.date(2024, 9, 5)]
    symbols = ["AAA"]
    minute_by = {(s, sd): make_minute_bars(s, sd, minutes=30, drift_per_minute=0.5,
                                           minute_volume=10_000)
                 for s in symbols for sd in sessions}
    daily_by = {s: make_daily_bars(s, _dt.date(2024, 9, 1), n_sessions=10) for s in symbols}
    universe_by = {sd: {"universe_hash": "sha256:t",
                        "symbols": [{"symbol": s, "exchange": "NASDAQ", "venue_code": "XNAS",
                                     "instrument_class": "operating_equity",
                                     "eligible_for_bowaka_equity_bucket": True}
                                    for s in symbols]}
                   for sd in sessions}
    daily_cache_by = {sd: pd.DataFrame([{"symbol": s, "prior_close": 100.0,
                                         "avg_dollar_volume_20d": 5_000_000,
                                         "prior_atr_pct": 0.02, "ema_slope_prior": 0.01}
                                        for s in symbols])
                      for sd in sessions}

    def minute_supplier(sym, ts):
        sd = pd.Timestamp(ts).tz_convert("America/New_York").date()
        return minute_by.get((sym, sd))

    def daily_supplier(sym, sd):
        df = daily_by.get(sym)
        return None if df is None else df[df["session_date"] == sd]

    return run_backtest(
        cfg=cfg, sessions=sessions,
        scan_times_per_session=lambda sd: [pd.Timestamp(f"{sd}T14:00:00", tz="UTC")],
        universe_snapshot_by_session=universe_by,
        daily_cache_by_session=daily_cache_by,
        minute_bars_supplier=minute_supplier, daily_bars_supplier=daily_supplier,
        initial_bankroll=10_000.0, paths=paths,
    )


def test_backtest_emits_config_diff_artifact(tmp_path) -> None:
    """A smoke-mode run writes config_diff_vs_actual_bowaka_v2.yaml."""
    result = _wire_run(tmp_path, _base_cfg({"mode": "smoke_fixture"}))
    diff_path = result.run_dir / "config_diff_vs_actual_bowaka_v2.yaml"
    assert diff_path.is_file(), "config_diff_vs_actual_bowaka_v2.yaml not written"
    doc = yaml.safe_load(diff_path.read_text(encoding="utf-8"))
    assert "rows" in doc and "summary" in doc


def test_realism_run_with_full_parity_succeeds(tmp_path) -> None:
    """An intended_realism run whose comparable sections all match must NOT fail.

    Built from the frozen contract so signals/sizing/risk/exits/session match.
    """
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    contract = reference.load_actual_contract()
    cfg = _base_cfg({"mode": "intended_realism"})
    # Copy the comparable sections verbatim from the contract -> all `match`.
    for section in ("signals", "sizing", "risk", "exits", "session"):
        cfg[section] = dict(contract[section])
    cfg["signals"]["allow_unknown_instrument_class_for_research"] = False
    cfg["universe"] = {"asset_classes": ["operating_equity"],
                       "min_price": 1.0, "max_price": 20.0,
                       "min_adv_dollars": 250000, "exclude_pattern_class": True}
    # For the divergent sections only the common keys are diffed -- align them
    # with the contract so no spurious mismatch fires.
    c_scanner = contract["scanner"]
    cfg["scanner"]["max_candidates_per_scan"] = c_scanner["max_candidates_per_scan"]
    cfg["scanner"]["max_entries_per_scan"] = c_scanner["max_entries_per_scan"]
    # run_backtest must not raise on parity grounds.
    result = _wire_run(tmp_path, cfg)
    diff_path = result.run_dir / "config_diff_vs_actual_bowaka_v2.yaml"
    doc = yaml.safe_load(diff_path.read_text(encoding="utf-8"))
    assert doc["summary"]["mismatch"] == 0, (
        f"realism config built from the contract has mismatches: "
        f"{[r for r in doc['rows'] if r['parity_status'] == 'mismatch']}"
    )


def test_realism_run_with_unannotated_mismatch_fails_at_startup(tmp_path) -> None:
    """intended_realism + an injected unannotated mismatch -> RuntimeError."""
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    contract = reference.load_actual_contract()
    cfg = _base_cfg({"mode": "intended_realism"})
    for section in ("signals", "sizing", "risk", "exits", "session"):
        cfg[section] = dict(contract[section])
    cfg["signals"]["allow_unknown_instrument_class_for_research"] = False
    cfg["universe"] = {"asset_classes": ["operating_equity"],
                       "min_price": 1.0, "max_price": 20.0,
                       "min_adv_dollars": 250000, "exclude_pattern_class": True}
    cfg["scanner"]["max_candidates_per_scan"] = contract["scanner"]["max_candidates_per_scan"]
    cfg["scanner"]["max_entries_per_scan"] = contract["scanner"]["max_entries_per_scan"]
    # Inject a single deliberate divergence: exits.stop_pct != the contract.
    cfg["exits"]["stop_pct"] = 0.99
    with pytest.raises(RuntimeError, match="stop_pct"):
        _wire_run(tmp_path, cfg)
