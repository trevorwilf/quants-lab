"""The `optuna` CLI must expose --skip-best-trial-report and forward it.

Speedup investigation 2026-06-16. The post-search single-best neighbour sweep
(build_best_trial_report) rebuilds fold contexts from scratch in process-parallel
mode, so it runs slow and is redundant whenever a Top-N robustness/holdout sweep
follows (the notebook two-stage always skips it). This flag is the CLI/relaunch
escape hatch; these tests lock in that it parses and threads through to
run_walkforward_study. Pure CLI wiring — no study is actually run.
"""
from __future__ import annotations

from unittest.mock import patch

from bowaka_v2_lab import cli


def test_parser_accepts_skip_best_trial_report():
    a = cli.build_parser().parse_args(["optuna", "--config", "x", "--skip-best-trial-report"])
    assert a.skip_best_trial_report is True
    b = cli.build_parser().parse_args(["optuna", "--config", "x"])
    assert b.skip_best_trial_report is False  # preserved default (standalone runs still get the sweep)


def test_cmd_optuna_forwards_skip_best_trial_report():
    captured: dict = {}

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return {"status": "ok"}

    with patch(
        "bowaka_v2_lab.optuna.walkforward_runner.run_walkforward_study",
        side_effect=fake_run,
    ):
        rc = cli.main(["optuna", "--config", "x", "--skip-best-trial-report"])
    assert rc == 0
    assert captured.get("skip_best_trial_report") is True


def test_cmd_optuna_default_does_not_skip():
    captured: dict = {}

    def fake_run(*args, **kwargs):
        captured.update(kwargs)
        return {"status": "ok"}

    with patch(
        "bowaka_v2_lab.optuna.walkforward_runner.run_walkforward_study",
        side_effect=fake_run,
    ):
        rc = cli.main(["optuna", "--config", "x"])
    assert rc == 0
    assert captured.get("skip_best_trial_report") is False
