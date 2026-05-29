"""Phase 3 (audit 2026-05-29 §7 / §8.1) — resolved config persisted under artifacts.

The resolved config must land under ``artifacts/resolved_configs/`` (not
volatile /tmp), and the run manifest records its SHA-256.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


def _read_ok_artifact(tmp_path: Path) -> dict:
    for p in sorted(tmp_path.rglob("optuna/*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if d.get("status") == "ok":
            return d
    raise AssertionError("no status=ok study artifact found")


def test_resolved_config_persisted_with_matching_sha(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg_path = write_walkforward_test_config(
        lab_root / "configs" / "quarantined"
        / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml",
        tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    art = run_walkforward_study(cfg_path, allow_smoke=True)
    md = art["study_metadata"]

    resolved_path = Path(md["resolved_config_path"])
    assert resolved_path.is_file(), f"resolved config not persisted at {resolved_path}"
    assert "resolved_configs" in resolved_path.parts
    assert resolved_path.name.endswith("__resolved.yml")

    sha = hashlib.sha256(resolved_path.read_bytes()).hexdigest()
    assert md["resolved_config_sha256"] == sha
