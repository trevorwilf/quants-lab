"""Real walk-forward Optuna runner — end-to-end on a tiny synthetic lake.

Proves run_walkforward_study runs actual backtests per fold (no toy objective),
honors the holdout guard, and produces a study with completed trials.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import yaml

from bowaka_common.marketdata import layout
from bowaka_v2_lab.optuna.walkforward_runner import apply_trial_params, run_walkforward_study


def build_tiny_lake(lake: Path, symbols, *, start: dt.date, end: dt.date, feed: str = "iex") -> None:
    """Daily bars over [start, end] plus per-month minute bars, for each symbol."""
    for sym in symbols:
        days = [d.date() for d in pd.bdate_range(start, end)]
        dpath = layout.daily_bars_path(lake, sym, feed=feed)
        dpath.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(
            {
                "symbol": [sym] * len(days),
                "timestamp": [pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=20) for d in days],
                "open": [100.0] * len(days), "high": [101.0] * len(days),
                "low": [99.0] * len(days), "close": [100.0] * len(days),
                "volume": [1_000_000] * len(days), "session_date": days,
            }
        ).to_parquet(dpath, index=False)
        by_month: dict[tuple[int, int], list] = {}
        for d in days:
            for i in range(30):
                ts = pd.Timestamp(d, tz="UTC") + pd.Timedelta(hours=13, minutes=30 + i)
                by_month.setdefault((d.year, d.month), []).append(
                    {"symbol": sym, "timestamp": ts, "open": 100.0, "high": 101.0,
                     "low": 99.0, "close": 100.5, "volume": 5000.0}
                )
        for (year, month), rows in by_month.items():
            mpath = layout.minute_bars_path(lake, sym, year, month, feed=feed)
            mpath.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame(rows).to_parquet(mpath, index=False)


def write_test_config(
    base_config_path: Path, out_path: Path, *,
    lake: Path, symbols, start: dt.date, end: dt.date, n_trials: int = 2,
) -> Path:
    """Derive a small, in-memory-storage walk-forward config from the real one."""
    raw = yaml.safe_load(Path(base_config_path).read_text(encoding="utf-8"))
    raw["backtest"]["start_date"] = start.isoformat()
    raw["backtest"]["end_date"] = end.isoformat()
    raw["market_data"]["shared_root"] = str(lake)
    raw["market_data"]["feed"] = "iex"  # pin to match build_tiny_lake's feed
    raw.setdefault("universe", {})["symbols"] = list(symbols)
    raw["optuna"]["n_trials"] = n_trials
    raw["optuna"]["n_jobs"] = 1
    raw["optuna"]["walkforward"] = {"train_months": 1, "val_months": 1, "final_holdout_months": 1}
    raw["optuna"].pop("storage", None)  # -> in-memory Optuna study
    # redirect lab paths into the tmp area so no test artifacts land in the repo
    tmp_lab = Path(out_path).parent / "bowaka_v2_lab"
    raw["paths"] = {
        "lab_root": str(tmp_lab),
        "data_root": str(tmp_lab / "data"),
        "artifact_root": str(tmp_lab / "artifacts"),
    }
    Path(out_path).write_text(yaml.safe_dump(raw), encoding="utf-8")
    return Path(out_path)


def test_apply_trial_params_sets_dotted_keys():
    cfg = {"signals": {"a": 1}, "exits": {}}
    out = apply_trial_params(cfg, {"signals.gap_pct_max": 0.2, "exits.stop_loss_pct": 0.03})
    assert out["signals"]["gap_pct_max"] == 0.2
    assert out["exits"]["stop_loss_pct"] == 0.03
    assert cfg["signals"] == {"a": 1}  # base config untouched (deep copy)


def test_run_walkforward_study_real_backtests(tmp_path, lab_root):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "bowaka_v2_walkforward_optuna.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    result = run_walkforward_study(cfg_path)
    assert result["status"] == "ok"
    assert result["n_trials_requested"] == 2
    assert result["n_trials_completed"] == 2          # both trials ran real backtests
    assert result["n_folds"] >= 1
    assert result["best_value"] is not None
    assert set(result["best_params"]) >= {"signals.gap_pct_max", "exits.stop_loss_pct"}
    assert Path(result["results_path"]).is_file()


def test_run_walkforward_study_respects_final_holdout(tmp_path, lab_root):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "bowaka_v2_walkforward_optuna.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=1,
    )
    result = run_walkforward_study(cfg_path)
    # the final-holdout window is reserved at the tail and never tuned on
    holdout_start = dt.date.fromisoformat(result["final_holdout"][0])
    assert holdout_start == dt.date(2024, 4, 1)


def test_cli_optuna_command(tmp_path, lab_root):
    from bowaka_v2_lab import cli

    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "bowaka_v2_walkforward_optuna.yml",
        tmp_path / "wf_cli.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    rc = cli.main(["optuna", "--config", str(cfg_path), "--n-trials", "2"])
    assert rc == 0
