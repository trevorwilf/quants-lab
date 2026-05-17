"""Phase optuna-3: Makefile has optuna-smoke + optuna-walkforward targets."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture(scope="module")
def makefile_text(bowaka_root: Path) -> str:
    mf = bowaka_root / "Makefile"
    assert mf.exists(), f"Makefile missing: {mf}"
    return mf.read_text(encoding="utf-8")


def test_makefile_has_optuna_smoke_target(makefile_text):
    assert "optuna-smoke:" in makefile_text


def test_makefile_has_optuna_walkforward_target(makefile_text):
    assert "optuna-walkforward:" in makefile_text


def test_makefile_optuna_walkforward_checks_OPTUNA_STORAGE(makefile_text):
    """The walkforward target must guard on OPTUNA_STORAGE being set."""
    # find the target block
    block = makefile_text.split("optuna-walkforward:", 1)[1]
    assert "OPTUNA_STORAGE" in block
    assert "exit 2" in block or "exit 1" in block


def test_makefile_optuna_walkforward_invokes_runner_script(makefile_text):
    block = makefile_text.split("optuna-walkforward:", 1)[1]
    assert "scripts/run_optuna_walkforward.py" in block
