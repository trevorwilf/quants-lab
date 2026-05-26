"""Strict-parallel preflight failure writes the failed-study artifact.

Speedup report v2 §1.3 / §4 P2 / §5.4 / Phase 2 task 6. When
``run_walkforward_study`` invokes ``preflight_parallel_dispatch`` with
``strict_parallel=true`` and the memory budget refuses, the failed-status
JSON lands on disk BEFORE ``OptunaStudyInvalidError`` propagates. Other
existing tests in this directory pin the SQLite refusal path; this one
pins the memory-refusal path and the artifact-write contract.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest
import yaml

import bowaka_v2_lab.optuna.walkforward_runner as runner
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.utils.memory_guard import MemoryBudget, MemoryReserveViolation


_LAB_ROOT = Path(__file__).resolve().parents[3]


def _make_strict_parallel_cfg(tmp_path: Path) -> Path:
    """Build a tiny-lake config that opts INTO strict_parallel with n_jobs=2.

    Storage stays at the SQLite default; the preflight helper will refuse
    immediately on the SQLite + n_jobs > 1 check (no PostgreSQL needed for
    this test).
    """
    lake = tmp_path / "lake"
    build_tiny_lake(
        lake, ["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
    )
    raw_cfg = _LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code_optuna.yml"
    cfg_path = write_walkforward_test_config(
        raw_cfg, tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=1,
    )
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc["optuna"]["n_jobs"] = 2
    # SQLite-default storage triggers the preflight SQLite refusal under
    # strict_parallel — same artifact-write codepath as the memory refusal.
    doc["optuna"]["storage"] = "sqlite:///./tmp.db"
    doc["optuna"].setdefault("parallel", {})
    doc["optuna"]["parallel"]["strict_parallel"] = True
    doc["optuna"]["parallel"]["memory_reserve_gib"] = 62
    doc["optuna"]["parallel"]["max_workers"] = 8
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return cfg_path


def test_strict_parallel_refusal_writes_failed_artifact(tmp_path: Path) -> None:
    """Strict-parallel + SQLite refusal lands a failed-status artifact."""
    cfg_path = _make_strict_parallel_cfg(tmp_path)

    with pytest.raises(OptunaStudyInvalidError) as exc_info:
        runner.run_walkforward_study(
            cfg_path,
            allow_smoke=True,
            allow_current_code_parity_study=True,
            tier="research_only",
        )

    msg = str(exc_info.value)
    assert "parallel preflight" in msg, msg

    # The failed-study artifact landed under the per-config artifact root.
    artifact_root = tmp_path / "bowaka_v2_lab" / "artifacts" / "optuna"
    assert artifact_root.is_dir()
    artifacts = sorted(artifact_root.glob("*.json"))
    failed = [
        p for p in artifacts if (
            "phase_profile" not in p.name
            and json.loads(p.read_text(encoding="utf-8")).get("status") == "failed"
        )
    ]
    assert failed, f"no failed-status study artifact in {artifact_root}"
    payload = json.loads(failed[0].read_text(encoding="utf-8"))
    assert payload["status"] == "failed"
    assert "parallel preflight" in payload["failure_reason"]
