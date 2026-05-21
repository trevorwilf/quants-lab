"""bowaka_v2_lab CLI subcommands — run end-to-end on the smoke config.

The smoke config uses ``*_source: fixture`` → the synthetic data path, so these
tests need no lake and no network. The lake path is covered by the loaders /
suppliers / backtester-on-lake tests.
"""
from __future__ import annotations

from bowaka_v2_lab import cli


def _smoke_config(lab_root) -> str:
    return str(lab_root / "configs" / "bowaka_v2_backtest_smoke.yml")


def test_cli_smoke(tmp_path, lab_root):
    run_dir = tmp_path / "smoke_run"
    rc = cli.main(["smoke", "--config", _smoke_config(lab_root), "--run-dir", str(run_dir)])
    assert rc == 0
    assert (run_dir / "summary.json").is_file()


def test_cli_run_backtest(tmp_path, lab_root):
    run_dir = tmp_path / "bt_run"
    # The smoke config is simulation.mode=smoke_fixture; run-backtest refuses
    # that mode unless --allow-smoke-optimization is passed (realism Phase 0).
    rc = cli.main(["run-backtest", "--config", _smoke_config(lab_root),
                   "--run-dir", str(run_dir), "--allow-smoke-optimization"])
    assert rc == 0
    assert (run_dir / "summary.json").is_file()


def test_cli_build_universe(tmp_path, lab_root):
    out_path = tmp_path / "universe.json"
    rc = cli.main(["build-universe", "--config", _smoke_config(lab_root), "--out", str(out_path)])
    assert rc == 0
    assert out_path.is_file()


def test_cli_build_volume_curve(tmp_path, lab_root):
    out_path = tmp_path / "curve.parquet"
    rc = cli.main(["build-volume-curve", "--config", _smoke_config(lab_root), "--out", str(out_path)])
    assert rc == 0
    assert out_path.is_file()


def test_cli_replay_scanner(tmp_path, lab_root):
    run_dir = tmp_path / "replay_run"
    rc = cli.main(["replay-scanner", "--config", _smoke_config(lab_root), "--run-dir", str(run_dir)])
    assert rc == 0
    assert run_dir.is_dir()


def test_cli_subcommands_are_not_placeholders():
    # regression: the commands must no longer print the Phase-1 placeholder.
    import inspect

    from bowaka_v2_lab import cli_runners

    src = inspect.getsource(cli) + inspect.getsource(cli_runners)
    assert "not_implemented_in_phase_1" not in src


def test_cli_run_backtest_reads_the_lake(tmp_path, lab_root):
    """run-backtest against a config with *_source: alpaca reads the shared lake."""
    import datetime as dt

    import pandas as pd
    import yaml

    from bowaka_common.marketdata import layout

    # tiny synthetic lake: daily warmup + one session of minute bars for AAA
    lake = tmp_path / "lake"
    session = dt.date(2024, 9, 4)
    ddates = [session - dt.timedelta(days=i) for i in range(80, 0, -1)]
    dpath = layout.daily_bars_path(lake, "AAA")
    dpath.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["AAA"] * len(ddates),
            "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in ddates],
            "open": [100.0] * len(ddates), "high": [101.0] * len(ddates),
            "low": [99.0] * len(ddates), "close": [100.0] * len(ddates),
            "volume": [1_000_000] * len(ddates), "session_date": ddates,
        }
    ).to_parquet(dpath, index=False)
    mpath = layout.minute_bars_path(lake, "AAA", 2024, 9)
    mpath.parent.mkdir(parents=True, exist_ok=True)
    mts = [pd.Timestamp(f"{session} 13:30", tz="UTC") + pd.Timedelta(minutes=i) for i in range(60)]
    pd.DataFrame(
        {
            "symbol": ["AAA"] * 60, "timestamp": mts,
            "open": [100.0] * 60, "high": [101.0] * 60, "low": [99.0] * 60,
            "close": [100.5] * 60, "volume": [5000.0] * 60,
        }
    ).to_parquet(mpath, index=False)

    # smoke config switched to the lake
    raw = yaml.safe_load((lab_root / "configs" / "bowaka_v2_backtest_smoke.yml").read_text(encoding="utf-8"))
    raw["market_data"]["minute_bar_source"] = "alpaca"
    raw["market_data"]["daily_bar_source"] = "alpaca"
    raw["market_data"]["shared_root"] = str(lake)
    raw["universe"]["symbols"] = ["AAA"]
    raw["backtest"]["start_date"] = session.isoformat()
    raw["backtest"]["end_date"] = session.isoformat()
    cfg_path = tmp_path / "lake_cfg.yml"
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    run_dir = tmp_path / "lake_run"
    # config derives from the smoke config -> simulation.mode=smoke_fixture.
    rc = cli.main(["run-backtest", "--config", str(cfg_path), "--run-dir", str(run_dir),
                   "--allow-smoke-optimization"])
    assert rc == 0
    assert (run_dir / "summary.json").is_file()
