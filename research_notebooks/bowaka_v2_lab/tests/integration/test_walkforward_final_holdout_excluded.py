"""The final-holdout window is never scored during the study (Phase 9, Task 3/6).

Realism remediation Phase 9. Two guarantees:

1. During tuning, NO walk-forward fold overlaps the final-holdout window — the
   :class:`HoldoutGuard` raises if one would, and the study result reports
   ``final_holdout_scored == False``.
2. The holdout is scored exactly once, separately, via
   :func:`score_final_holdout` (the ``optuna --final-holdout`` CLI path).

Extends the pure-split disjointness test in
``tests/unit/test_walkforward_final_holdout_excluded.py`` with an end-to-end run.
"""
from __future__ import annotations

import datetime as dt

import pytest

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.devtools.wf_lake import (
    write_walkforward_test_config as write_test_config,
)
from bowaka_v2_lab.optuna.holdout import score_final_holdout
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuard, HoldoutGuardError
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def test_no_tuning_split_overlaps_the_final_holdout(tmp_path, lab_root):
    """Every walk-forward validation window ends before the holdout starts."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=1,
    )
    result = run_walkforward_study(cfg_path, allow_smoke=True)
    holdout_start = dt.date.fromisoformat(result["final_holdout"][0])

    # The study NEVER scores the holdout.
    assert result["final_holdout_scored"] is False

    # Every recorded fold's validation window precedes the holdout.
    for fold in result["study_metadata"]["fold_definitions"]:
        assert dt.date.fromisoformat(fold["val_end"]) <= holdout_start


def test_holdout_guard_blocks_a_tuning_read_of_the_holdout() -> None:
    """The guard raises if tuning code attempts to read the holdout window."""
    guard = HoldoutGuard(dt.date(2024, 4, 1), dt.date(2024, 5, 1))
    # A read fully inside the holdout window during tuning is forbidden.
    with pytest.raises(HoldoutGuardError):
        guard.assert_can_read(dt.date(2024, 4, 10), dt.date(2024, 4, 20))
    # A pre-holdout read is fine.
    guard.assert_can_read(dt.date(2024, 1, 1), dt.date(2024, 2, 1))


def test_final_holdout_scored_only_via_score_final_holdout(tmp_path, lab_root):
    """The holdout is scored once, by the explicit --final-holdout path."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf_holdout.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    study = run_walkforward_study(cfg_path, allow_smoke=True)
    assert study["final_holdout_scored"] is False  # untouched by the study

    # Now score the holdout ONCE against the study's best params.
    holdout = score_final_holdout(
        cfg_path, study["best_params"], allow_smoke=True,
        out_path=tmp_path / "holdout_result.json",
    )
    assert holdout["status"] == "ok"
    assert holdout["kind"] == "final_holdout"
    # the holdout window matches the study's reserved window.
    assert holdout["final_holdout"] == study["final_holdout"]
    assert "holdout_score" in holdout
    assert "holdout_metrics" in holdout
    assert (tmp_path / "holdout_result.json").is_file()


def test_final_holdout_cli_path(tmp_path, lab_root):
    """`optuna --final-holdout` scores a params file against the holdout."""
    import json

    from bowaka_v2_lab import cli

    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf_cli.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    study = run_walkforward_study(cfg_path, allow_smoke=True)

    # Persist a params file and score it through the CLI.
    params_path = tmp_path / "params.json"
    params_path.write_text(json.dumps(study["best_params"]), encoding="utf-8")
    out_path = tmp_path / "cli_holdout.json"
    rc = cli.main([
        "optuna", "--config", str(cfg_path), "--final-holdout",
        "--params-json", str(params_path), "--out", str(out_path),
        "--allow-smoke-optimization",
    ])
    assert rc == 0
    assert out_path.is_file()
    doc = json.loads(out_path.read_text(encoding="utf-8"))
    assert doc["kind"] == "final_holdout"
