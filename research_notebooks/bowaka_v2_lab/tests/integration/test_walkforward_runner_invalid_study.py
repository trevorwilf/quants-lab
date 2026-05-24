"""Audit 2026-05-23 §P0-001 — all-sentinel + structural-exception study aborts.

Pre-remediation an Optuna study whose every trial returned
``_FAILED_TRIAL_SCORE`` (or raised a structural exception that was swallowed by
the broad ``except Exception`` in the objective) still completed with
``status: "ok"`` and a non-empty ``best_params``. After remediation 3 Phase 0
the runner validates the completed-trial set and raises
:class:`OptunaStudyInvalidError`; a structural exception escaping the trial
also raises and writes a ``status: "failed"`` artifact.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest

from bowaka_v2_lab.devtools.wf_lake import (
    build_tiny_lake,
    write_walkforward_test_config,
)
from bowaka_v2_lab.optuna import walkforward_runner
from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.optuna.holdout_guard import HoldoutGuardError
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def _write_cfg(tmp_path: Path, lab_root: Path) -> Path:
    lake = tmp_path / "lake"
    build_tiny_lake(
        lake, ["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    return write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )


def _read_failed_artifact(tmp_path: Path) -> dict:
    """Locate and read the failed-status study artifact."""
    candidates = sorted((tmp_path).rglob("optuna/*.json"))
    assert candidates, "expected a failed-status study artifact under tmp_path"
    docs = []
    for p in candidates:
        try:
            docs.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    failed = [d for d in docs if d.get("status") == "failed"]
    assert failed, f"no failed-status artifact among {[c.name for c in candidates]}"
    return failed[0]


def test_all_sentinel_study_raises_invalid(tmp_path, lab_root, monkeypatch):
    """Every trial returns the sentinel score → OptunaStudyInvalidError."""
    cfg = _write_cfg(tmp_path, lab_root)

    # Force every fold to fail non-structurally — the broad except in the
    # objective will convert each to ``_FAILED_TRIAL_SCORE`` and the trial
    # completes with the sentinel value. The new validation must reject the
    # whole study.
    def _raise_non_structural(*args, **kwargs):
        raise RuntimeError("forced non-structural failure for test")

    monkeypatch.setattr(
        walkforward_runner, "_run_validation_folds", _raise_non_structural,
    )

    with pytest.raises(OptunaStudyInvalidError) as ei:
        run_walkforward_study(cfg, allow_smoke=True)
    assert "zero valid" in str(ei.value)

    # Forensic artifact was written before re-raising.
    failed = _read_failed_artifact(tmp_path)
    assert failed["status"] == "failed"
    assert failed["best_params"] == {}
    assert failed["best_value"] is None
    assert "error" in failed["best_trial_report"]


def test_structural_exception_aborts_study_not_sentinels(
    tmp_path, lab_root, monkeypatch,
):
    """A HoldoutGuardError must escape, not become _FAILED_TRIAL_SCORE."""
    cfg = _write_cfg(tmp_path, lab_root)

    def _raise_structural(*args, **kwargs):
        raise HoldoutGuardError("forced structural failure for test")

    monkeypatch.setattr(
        walkforward_runner, "_run_validation_folds", _raise_structural,
    )

    with pytest.raises(OptunaStudyInvalidError) as ei:
        run_walkforward_study(cfg, allow_smoke=True)
    assert "HoldoutGuardError" in str(ei.value) or "structural" in str(ei.value)

    # Forensic artifact was written before re-raising.
    failed = _read_failed_artifact(tmp_path)
    assert failed["status"] == "failed"
    assert failed["best_params"] == {}
    assert "error" in failed["best_trial_report"]


def test_failed_artifact_includes_study_metadata(tmp_path, lab_root, monkeypatch):
    """The forensic artifact must carry study metadata for post-mortem review."""
    cfg = _write_cfg(tmp_path, lab_root)

    def _raise_non_structural(*args, **kwargs):
        raise RuntimeError("forced")

    monkeypatch.setattr(
        walkforward_runner, "_run_validation_folds", _raise_non_structural,
    )
    with pytest.raises(OptunaStudyInvalidError):
        run_walkforward_study(cfg, allow_smoke=True)

    failed = _read_failed_artifact(tmp_path)
    # study_metadata is present and carries the dataset / config / code hashes
    # plus the fold definitions — the forensic minimum.
    md = failed["study_metadata"]
    assert "dataset_hash" in md
    assert "lab_config_hash" in md
    assert "code_hash" in md
    assert md["fold_definitions"], "fold_definitions must be retained for forensic review"
