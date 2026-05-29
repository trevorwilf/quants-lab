"""Audit 2026-05-29 §10.1 / §A.9 — Notebook 10 short-run IEX papermill test.

The existing ``test_notebook_10_runs.py`` uses ``FEED='synthetic'`` and does
NOT prove the IEX current-code-parity path works. This test runs Notebook 10
against a real (tiny) IEX-shaped lake fixture (split-adjusted daily + minute
bars, no quotes) and asserts the post-Phase-2 invariants.

Skip policy: a full headless Notebook 10 papermill run is heavy and
environment-dependent, and the prompt's top-matter states "Notebook 10 is not
run inside CC" — the equivalent IEX short-run validation is provided by the
``verify-bayesian-fix`` CLI (Section 7, ``test_verify_bayesian_fix_cli.py``)
which runs the same ``run_walkforward_study`` incumbent + current-code-parity
path in-process. This papermill test is therefore opt-in: set
``BOWAKA_RUN_NOTEBOOK_PAPERMILL=1`` to execute it (e.g. on the operator's
workstation), otherwise it skips.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.fixtures.iex_short_run_lake import build_iex_short_run_lake

pytestmark = [pytest.mark.integration]

_RUN = os.environ.get("BOWAKA_RUN_NOTEBOOK_PAPERMILL") == "1"


@pytest.fixture
def iex_short_run_lake_fixture(tmp_path: Path) -> Path:
    return build_iex_short_run_lake(tmp_path / "iex_short_run_lake")


@pytest.mark.skipif(
    not _RUN,
    reason="headless Notebook 10 papermill run is opt-in "
           "(set BOWAKA_RUN_NOTEBOOK_PAPERMILL=1); the equivalent IEX short-run "
           "is covered by verify-bayesian-fix Section 7",
)
@pytest.mark.timeout(600)
def test_notebook_10_iex_short_run_completes_without_padding_or_dynamic_errors(
    tmp_path: Path, iex_short_run_lake_fixture: Path
) -> None:
    if shutil.which("papermill") is None:
        pytest.skip("papermill CLI not on PATH")
    lab = Path(__file__).resolve().parents[1]
    nb = lab / "notebooks" / "10_optuna_walkforward.ipynb"
    if not nb.is_file():
        pytest.skip("notebook 10 not found")
    executed = tmp_path / "10_executed.ipynb"
    cmd = [
        "papermill", str(nb), str(executed),
        "-p", "CONFIG_PATH",
        str(lab / "configs" / "bowaka_v2_actual_iex_current_code_optuna.workstation.yml"),
        "-p", "FEED", "iex",
        "-p", "N_TRIALS", "3",
        "-p", "N_STARTUP_TRIALS", "1",
        "-p", "N_JOBS", "1",
        "-p", "INCUMBENT_TRIAL", "true",
        "-p", "SHARED_LAKE_ROOT", str(iex_short_run_lake_fixture),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=540)
    out = (executed.read_text(encoding="utf-8", errors="ignore")
           if executed.is_file() else "") + result.stdout + result.stderr
    assert result.returncode == 0, out[-3000:]
    # P1-001 regression guard
    assert "CategoricalDistribution does not support dynamic value space" not in out
    # P0-003 regression guard (no padding)
    assert "incumbent baseline padded" not in out
    # P0-005 regression guard (current-code-parity full-fold preflight ran)
    assert "full-fold preflight" in out or "full per-fold preflight" in out
    # Promotion evidence: research_only, NOT a paper/live recommendation.
    study_jsons = list((lab / "artifacts" / "optuna").glob("iex__*.json"))
    assert study_jsons, f"no study artifact under artifacts/optuna; out={out[-2000:]}"
    latest = max(study_jsons, key=lambda p: p.stat().st_mtime)
    art = json.loads(latest.read_text(encoding="utf-8"))
    evidence = art["promotion_evidence"]
    assert evidence["reviewable_for_research"] is True
    assert evidence["parameter_recommendation_allowed"] is False
    assert "IEX_PARTIAL_TAPE" in evidence["caps_applied"]
