"""Real walk-forward Optuna runner — end-to-end on a tiny synthetic lake.

Proves run_walkforward_study runs actual backtests per fold (no toy objective),
honors the holdout guard, and produces a study with completed trials.

The tiny-lake / config helpers live in
``bowaka_v2_lab.devtools.wf_lake`` so every Phase-9 test module can import them
through the package (sibling-test imports are fragile under pytest's default
``prepend`` import mode). ``build_tiny_lake`` / ``write_test_config`` are
re-exported here for backward compatibility.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.devtools.wf_lake import (
    write_walkforward_test_config as write_test_config,
)
from bowaka_v2_lab.optuna.walkforward_runner import apply_trial_params, run_walkforward_study


def test_apply_trial_params_sets_dotted_keys():
    cfg = {"signals": {"a": 1}, "exits": {}}
    out = apply_trial_params(cfg, {"signals.gap_pct_max": 0.2, "exits.stop_pct": 0.03})
    assert out["signals"]["gap_pct_max"] == 0.2
    assert out["exits"]["stop_pct"] == 0.03
    assert cfg["signals"] == {"a": 1}  # base config untouched (deep copy)


def test_apply_trial_params_nests_deep_dotted_keys():
    """Phase 9: dotted trial params nest to any depth (nested live params)."""
    cfg = {"exits": {}}
    out = apply_trial_params(cfg, {
        "exits.time_stop.exit_time": "15:45",
        "exits.signal_fade.score_thresholds.hard": 0.5,
    })
    assert out["exits"]["time_stop"]["exit_time"] == "15:45"
    assert out["exits"]["signal_fade"]["score_thresholds"]["hard"] == 0.5


def test_run_walkforward_study_real_backtests(tmp_path, lab_root):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    result = run_walkforward_study(cfg_path, allow_smoke=True)
    # Audit 2026-05-23 §P0-001 — the study should be ``ok`` AND the best
    # value must not be the sentinel score (pre-remediation the all-sentinel
    # study completed with ``status=ok`` and ``best_value=-1e9``).
    assert result["status"] == "ok", (
        f"study should be ok after P0 fixes, got {result.get('status')}: "
        f"{result.get('failure_reason')}"
    )
    assert result["n_trials_requested"] == 2
    assert result["n_trials_completed"] == 2          # both trials ran real backtests
    assert result["n_folds"] >= 1
    assert result["best_value"] is not None
    assert result["best_value"] > -1e9 + 1e-6, (
        f"best_value must not be sentinel; got {result['best_value']}"
    )
    assert set(result["best_params"]) >= {"signals.gap_pct_max", "exits.stop_pct"}
    assert Path(result["results_path"]).is_file()
    # Phase 9: the final holdout is reserved and never scored during the study.
    assert result["final_holdout_scored"] is False
    # Audit 2026-05-23 §P0-001 — every retained best trial must carry a full
    # fold-by-fold metrics payload; absence is what the new validation checks
    # for as ``missing_fold_metrics``.
    fold_by_fold = result["best_trial_report"]["fold_by_fold"]
    assert fold_by_fold["fold_metrics"], "fold_metrics must be non-empty"
    assert len(fold_by_fold["fold_metrics"]) == result["n_folds"]
    assert fold_by_fold["median_fold_score"] is not None


def test_run_walkforward_study_respects_final_holdout(tmp_path, lab_root):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=1,
    )
    result = run_walkforward_study(cfg_path, allow_smoke=True)
    # the final-holdout window is reserved at the tail and never tuned on
    holdout_start = dt.date.fromisoformat(result["final_holdout"][0])
    assert holdout_start == dt.date(2024, 4, 1)


def test_cli_optuna_command(tmp_path, lab_root):
    from bowaka_v2_lab import cli

    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf_cli.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    rc = cli.main(["optuna", "--config", str(cfg_path), "--n-trials", "2",
                   "--allow-smoke-optimization"])
    assert rc == 0


def test_run_walkforward_study_configurable_startup_trials(tmp_path, lab_root):
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_test_config(
        lab_root / "configs" / "quarantined" / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=3,
    )
    result = run_walkforward_study(cfg_path, n_trials=3, n_startup_trials=2, allow_smoke=True)
    assert result["n_startup_trials"] == 2


def test_n_startup_trials_reaches_the_tpe_sampler():
    """The configured count must actually reach the TPE sampler."""
    from bowaka_v2_lab.optuna.dispatcher import OptunaStudy

    study = OptunaStudy(
        feed="sip", cost_stress="conservative",
        dataset_hash="d" * 16, config_hash="c" * 16, n_startup_trials=4,
    )
    study.create()
    assert study.study.sampler._n_startup_trials == 4
