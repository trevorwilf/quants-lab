"""Parallel vs serial TPE: same regions of parameter space explored.

Speedup report §6.1 / §11.3 Phase 5. Parallel TPE is NOT bit-identical to
serial — workers see different in-flight trial sets when sampling — so the
acceptance is regional, not point-exact. With a tiny lake we just assert
the parallel run completes and produces a real (non-sentinel) best_value.
Gated by ``BOWAKA_TEST_POSTGRES=1`` for the same reason as the smoke test.
"""
from __future__ import annotations

import datetime as dt
import os

import pytest
import yaml


def _pg_url() -> str | None:
    url = os.environ.get("OPTUNA_STORAGE") or os.environ.get("BOWAKA_TEST_PG_URL")
    if url and "postgresql" in url.lower():
        return url
    return None


@pytest.mark.skipif(
    os.environ.get("BOWAKA_TEST_POSTGRES") != "1" or _pg_url() is None,
    reason="BOWAKA_TEST_POSTGRES != 1 or no PostgreSQL URL configured",
)
def test_parallel_run_produces_real_best_value(tmp_path, lab_root):
    from bowaka_v2_lab.devtools.wf_lake import (
        build_tiny_lake, write_walkforward_test_config,
    )
    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study

    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"],
                    start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml", lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=10,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw["optuna"]["n_jobs"] = 2
    raw["optuna"]["storage"] = _pg_url()
    raw["optuna"]["objective_artifact_mode"] = "objective_minimal"
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    result = run_walkforward_study(cfg_path, allow_smoke=True)
    assert result["status"] == "ok"
    # Not a sentinel: the dispatcher must have produced a real objective.
    assert result["best_value"] is not None
    assert result["best_value"] > -1.0e9 + 1.0
