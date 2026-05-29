"""Phase 1 (audit 2026-05-29 §8.5) — stress-matrix base point == unstressed.

The stress point ``(slippage_bps_offset=0, spread_multiplier=1.0,
cost_stress="base")`` MUST reproduce the unstressed backtest's fold metrics
exactly. If this drifts, the stress framework has corrupted the base path.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.stress_matrix import StressPoint
from bowaka_v2_lab.optuna.walkforward_runner import build_validation_scorer


def test_base_point_reproduces_unstressed_folds(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    # Pin the unstressed cost_stress to the matrix's base level.
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc.setdefault("backtest", {})["cost_stress"] = "base"
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")

    scorer = build_validation_scorer(cfg_path)
    params: dict = {}

    _obj_u, unstressed = scorer(params, {})
    _obj_b, base = scorer(params, StressPoint(0, 1.0, "base").as_overrides())

    assert len(unstressed) == len(base) >= 1
    for u, b in zip(unstressed, base):
        assert abs(float(u.net_return) - float(b.net_return)) < 1e-12
        assert int(u.n_trades) == int(b.n_trades)
        assert abs(float(u.fill_rate) - float(b.fill_rate)) < 1e-12
