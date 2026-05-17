"""Phase optuna-3: headless runner CLI behavior (no live Postgres needed)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def runner_path(bowaka_root: Path) -> Path:
    p = bowaka_root / "scripts" / "run_optuna_walkforward.py"
    assert p.exists(), f"runner missing: {p}"
    return p


def _run(runner_path: Path, args: list[str], env: dict[str, str]):
    full_env = {**os.environ, **env}
    return subprocess.run(
        [sys.executable, str(runner_path), *args],
        capture_output=True,
        text=True,
        env=full_env,
        timeout=60,
    )


def test_run_optuna_walkforward_script_help_exits_0(runner_path):
    result = _run(runner_path, ["--help"], env={})
    assert result.returncode == 0
    assert "run-id" in result.stdout.lower()


def test_run_optuna_walkforward_script_exits_2_without_postgres(runner_path, tmp_path):
    env = {
        "OPTUNA_STORAGE": "",  # explicitly empty
        "BOWAKA_OPTUNA_STORAGE": "",  # also clear the back-compat var
    }
    result = _run(
        runner_path,
        [
            "--run-id",
            "no_pg_test",
            "--n-trials",
            "2",
            "--artifacts-root",
            str(tmp_path),
        ],
        env=env,
    )
    assert result.returncode == 2, (
        f"expected exit 2, got {result.returncode}.\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    combined = result.stdout + result.stderr
    assert "PostgreSQL" in combined or "OPTUNA_STORAGE" in combined


def test_run_optuna_walkforward_script_exits_2_on_sqlite_storage(runner_path, tmp_path):
    env = {
        "OPTUNA_STORAGE": f"sqlite:///{tmp_path}/x.db",
        "BOWAKA_OPTUNA_STORAGE": "",
    }
    result = _run(
        runner_path,
        [
            "--run-id",
            "sqlite_test",
            "--n-trials",
            "2",
            "--artifacts-root",
            str(tmp_path),
        ],
        env=env,
    )
    assert result.returncode == 2
    combined = result.stdout + result.stderr
    assert "PostgreSQL" in combined
