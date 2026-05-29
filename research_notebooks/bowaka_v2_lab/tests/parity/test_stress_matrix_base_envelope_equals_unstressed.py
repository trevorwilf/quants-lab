"""Phase 2 (audit 2026-05-29 §8.5) — the base/disabled stress point reproduces
the unstressed backtest (mirror of the Phase 1 parity test, now with the
timing-adjacent flags all explicitly off).
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.stress_matrix import RECOMMENDED_STRESS_POINTS
from bowaka_v2_lab.optuna.walkforward_runner import build_validation_scorer


def test_base_envelope_point_reproduces_unstressed(tmp_path: Path, lab_root: Path) -> None:
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
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc.setdefault("backtest", {})["cost_stress"] = "base"
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")

    scorer = build_validation_scorer(cfg_path)
    params: dict = {}

    base_point = RECOMMENDED_STRESS_POINTS[0]
    assert base_point.is_base

    _u, unstressed = scorer(params, {})
    _b, base = scorer(params, base_point.as_overrides())

    assert len(unstressed) == len(base) >= 1
    for u, b in zip(unstressed, base):
        assert abs(float(u.net_return) - float(b.net_return)) < 1e-12
        assert int(u.n_trades) == int(b.n_trades)
