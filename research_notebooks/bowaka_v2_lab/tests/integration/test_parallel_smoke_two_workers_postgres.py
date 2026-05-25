"""End-to-end smoke: 4 trials × 2 workers against a real PostgreSQL.

Speedup report §6.1 / §11.3 Phase 5. Gated by ``BOWAKA_TEST_POSTGRES=1`` —
the test is opt-in because it needs a live PostgreSQL reachable at the
URL from ``OPTUNA_STORAGE`` (or an explicit
``BOWAKA_TEST_PG_URL`` fallback).
"""
from __future__ import annotations

import datetime as dt
import os

import pytest

from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)


def _pg_url() -> str | None:
    url = os.environ.get("OPTUNA_STORAGE") or os.environ.get("BOWAKA_TEST_PG_URL")
    if url and "postgresql" in url.lower():
        return url
    return None


@pytest.mark.skipif(
    os.environ.get("BOWAKA_TEST_POSTGRES") != "1" or _pg_url() is None,
    reason="BOWAKA_TEST_POSTGRES != 1 or no PostgreSQL URL configured",
)
def test_parallel_smoke_two_workers(tmp_path, lab_root):
    """4 trials × 2 workers must complete and produce 4 trials in storage."""
    import yaml

    from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study

    lake = tmp_path / "lake"
    build_tiny_lake(
        lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml", lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=4,
    )
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    raw["optuna"]["n_jobs"] = 2
    raw["optuna"]["storage"] = _pg_url()
    raw["optuna"]["objective_artifact_mode"] = "objective_minimal"
    raw["optuna"]["parallel"] = {"strict_parallel": True}
    cfg_path.write_text(yaml.safe_dump(raw), encoding="utf-8")

    result = run_walkforward_study(cfg_path, allow_smoke=True)
    assert result["status"] == "ok"
    assert result["n_trials_completed"] >= 4
