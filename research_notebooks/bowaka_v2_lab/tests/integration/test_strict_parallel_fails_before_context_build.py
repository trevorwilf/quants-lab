"""Strict parallel + SQLite raises before ``build_fold_contexts`` is called.

Speedup report v2 §1.3 / §4 P2 / §5.4 / Phase 2 task 6. The preflight
helper raises ``OptunaStudyInvalidError`` immediately for any SQLite (or
None) storage URI with ``n_jobs > 1``; the runner writes the
failed-status artifact and re-raises. ``build_fold_contexts`` MUST NOT
be called.
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


_LAB_ROOT = Path(__file__).resolve().parents[2]


def test_strict_parallel_with_sqlite_fails_before_context_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    raw_cfg = _LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code_optuna.yml"
    cfg_path = write_walkforward_test_config(
        raw_cfg, tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=1,
    )

    # Force strict_parallel + n_jobs=2 against the default SQLite (or in-memory) storage.
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc["optuna"]["n_jobs"] = 2
    doc["optuna"]["storage"] = "sqlite:///./tmp.db"
    doc["optuna"].setdefault("parallel", {})
    doc["optuna"]["parallel"]["strict_parallel"] = True
    doc["optuna"]["parallel"]["memory_reserve_gib"] = 62
    doc["optuna"]["parallel"]["max_workers"] = 8
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")

    # ``build_fold_contexts`` must not be called; raise if it ever is.
    def _must_not_be_called(*_args, **_kwargs):
        raise AssertionError(
            "build_fold_contexts must not be called when strict_parallel + SQLite "
            "preflight refuses"
        )

    monkeypatch.setattr(runner, "build_fold_contexts", _must_not_be_called)

    with pytest.raises(OptunaStudyInvalidError) as exc_info:
        runner.run_walkforward_study(
            cfg_path, allow_smoke=True,
        )
    assert "parallel preflight" in str(exc_info.value) or "PostgreSQL" in str(exc_info.value)

    # Failed-status artifact exists.
    artifact_root = tmp_path / "bowaka_v2_lab" / "artifacts" / "optuna"
    artifacts = list(artifact_root.glob("*.json"))
    failed = [
        p for p in artifacts
        if "phase_profile" not in p.name
        and json.loads(p.read_text(encoding="utf-8")).get("status") == "failed"
    ]
    assert failed, f"no failed-status artifact in {artifact_root}"
    payload = json.loads(failed[0].read_text(encoding="utf-8"))
    assert "parallel preflight" in payload["failure_reason"]
