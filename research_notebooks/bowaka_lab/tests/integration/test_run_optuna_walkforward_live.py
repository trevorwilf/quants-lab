"""Phase optuna-3: live Postgres end-to-end run of the headless runner."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import optuna
import pandas as pd
import pytest

pytestmark = pytest.mark.live_postgres


def _is_postgres(url):
    return bool(url) and "postgresql" in url.lower()


@pytest.fixture
def live_storage_url():
    url = os.environ.get("OPTUNA_STORAGE")
    if not _is_postgres(url):
        pytest.skip(
            "Live Postgres test requires OPTUNA_STORAGE to point at a PostgreSQL URI"
        )
    return url


@pytest.fixture
def runner_path(bowaka_root: Path) -> Path:
    p = bowaka_root / "scripts" / "run_optuna_walkforward.py"
    assert p.exists(), f"runner missing: {p}"
    return p


@pytest.fixture
def candidates_fixture(tmp_path: Path) -> Path:
    """Tiny candidates parquet so the runner has something to score."""
    run_id = "live_pg_test"
    artifacts_root = tmp_path / "artifacts"
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True)
    df = pd.DataFrame(
        {
            "symbol": [f"SYM{i}" for i in range(20)],
            "rvol": [1.0 + 0.01 * i for i in range(20)],
            "atr_pct": [0.02 + 0.005 * i for i in range(20)],
            "range_expansion": [0.1 + 0.02 * i for i in range(20)],
            "signal_strength": [0.5 + 0.01 * i for i in range(20)],
        }
    )
    df.to_parquet(run_dir / "candidates.parquet")
    return artifacts_root


@pytest.mark.timeout(180)
def test_run_optuna_walkforward_script_completes_against_live_postgres(
    runner_path, live_storage_url, candidates_fixture, tmp_path
):
    study_name = f"bowaka_live_runner_{uuid.uuid4().hex[:10]}"
    env = {**os.environ, "OPTUNA_STORAGE": live_storage_url}
    try:
        result = subprocess.run(
            [
                sys.executable,
                str(runner_path),
                "--run-id",
                "live_pg_test",
                "--n-trials",
                "3",
                "--n-jobs",
                "1",
                "--artifacts-root",
                str(candidates_fixture),
                "--study-name",
                study_name,
            ],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
        assert result.returncode == 0, (
            f"runner failed with code {result.returncode}.\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )

        trials_pq = candidates_fixture / "live_pg_test" / "optuna_trials.parquet"
        best_json = candidates_fixture / "live_pg_test" / "optuna_best.json"
        assert trials_pq.exists(), f"missing: {trials_pq}"
        assert best_json.exists(), f"missing: {best_json}"

        trials_df = pd.read_parquet(trials_pq)
        assert len(trials_df) == 3
        payload = json.loads(best_json.read_text(encoding="utf-8"))
        assert payload["study_name"] == study_name
        assert payload["n_trials"] == 3
    finally:
        try:
            optuna.delete_study(study_name=study_name, storage=live_storage_url)
        except Exception:
            pass
