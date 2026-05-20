"""smoke_backtester output files carry performance_use='prohibited'."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from bowaka_v2_lab.config.paths import BowakaV2Paths
from bowaka_v2_lab.devtools.smoke_backtester import run_smoke_backtest


def test_smoke_output_is_tagged_prohibited(tmp_path: Path) -> None:
    fake_lab = tmp_path / "research_notebooks" / "bowaka_v2_lab"
    paths = BowakaV2Paths(
        lab_root=fake_lab,
        data_root=fake_lab / "data",
        artifact_root=fake_lab / "artifacts",
        config_path=Path("ignored.yml"),
    )
    summary = run_smoke_backtest(paths=paths, n_synthetic_trades=3, initial_bankroll=10_000)
    assert summary["performance_use"] == "prohibited"
    assert summary["artifact_class"] == "dev_smoke_or_regression"
    # Verify the parquet trades carry the tag as well.
    run_id = summary["run_id"]
    trades_path = fake_lab / "artifacts" / "smoke" / run_id / "trades.parquet"
    assert trades_path.is_file()
    df = pd.read_parquet(trades_path)
    assert (df["performance_use"] == "prohibited").all()
