"""Canonical config-driven backtest runner — synthetic + lake paths."""
from __future__ import annotations

import datetime as dt

import yaml

from bowaka_v2_lab.backtest_runner import (
    apply_overrides,
    config_sessions,
    run_config_backtest,
    uses_lake,
)

from .test_walkforward_runner import build_tiny_lake


def test_apply_overrides_merges_section_wise():
    cfg = {"backtest": {"start_date": "2024-01-01", "entry_delay_minutes": 0},
           "exits": {"stop_loss_pct": 0.02}}
    out = apply_overrides(cfg, {"backtest": {"entry_delay_minutes": 5}})
    assert out["backtest"]["entry_delay_minutes"] == 5
    assert out["backtest"]["start_date"] == "2024-01-01"   # sibling key preserved
    assert cfg["backtest"]["entry_delay_minutes"] == 0     # base config untouched


def test_uses_lake():
    assert uses_lake({"market_data": {"minute_bar_source": "alpaca"}})
    assert not uses_lake({"market_data": {"minute_bar_source": "fixture"}})


def test_config_sessions():
    sessions = config_sessions({"backtest": {"start_date": "2024-10-01", "end_date": "2024-10-03"}})
    assert sessions == [dt.date(2024, 10, 1), dt.date(2024, 10, 2), dt.date(2024, 10, 3)]


def test_run_config_backtest_synthetic(tmp_path, lab_root):
    smoke = lab_root / "configs" / "bowaka_v2_backtest_smoke.yml"
    result = run_config_backtest(
        smoke,
        param_overrides={"backtest": {"start_date": "2024-10-01", "end_date": "2024-10-03"}},
        run_dir=tmp_path / "run",
    )
    assert (tmp_path / "run" / "summary.json").is_file()
    assert "net_return_pct" in result.summary


def test_run_config_backtest_reads_the_lake(tmp_path, lab_root):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 8, 1), end=dt.date(2024, 9, 10))
    raw = yaml.safe_load((lab_root / "configs" / "bowaka_v2_backtest_smoke.yml").read_text(encoding="utf-8"))
    raw["market_data"]["minute_bar_source"] = "alpaca"
    raw["market_data"]["daily_bar_source"] = "alpaca"
    raw["market_data"]["feed"] = "iex"
    raw["market_data"]["shared_root"] = str(lake)
    raw["universe"]["symbols"] = ["AAA"]
    raw["backtest"]["start_date"] = "2024-09-04"
    raw["backtest"]["end_date"] = "2024-09-06"
    cfg_path = tmp_path / "lake.yml"
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    result = run_config_backtest(cfg_path, run_dir=tmp_path / "run")
    assert (tmp_path / "run" / "summary.json").is_file()
    assert "net_return_pct" in result.summary


def test_run_config_backtest_accepts_a_dict(tmp_path, lab_root):
    """run_counterfactual_grid passes a dict, not a path."""
    smoke = lab_root / "configs" / "bowaka_v2_backtest_smoke.yml"
    from bowaka_v2_lab.config import load_config

    cfg = load_config(smoke)
    cfg["backtest"]["start_date"] = "2024-10-01"
    cfg["backtest"]["end_date"] = "2024-10-02"
    result = run_config_backtest(cfg, run_dir=tmp_path / "run")
    assert (tmp_path / "run" / "summary.json").is_file()
