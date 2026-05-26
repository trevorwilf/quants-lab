"""Walk-forward objective is unchanged when the batch daily cache is enabled.

Speedup report v2 §4 P1 / Phase 1 task 5. The strongest parity test: a
2-trial walk-forward study with the batch path off vs on must produce
identical ``best_value`` / ``best_params`` / ``fold_scores`` because the
per-session daily cache is the only thing the flag affects, and that cache
is bit-equal between the two paths.
"""
from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study


_LAB_ROOT = Path(__file__).resolve().parents[2]


def _write_cfg_with_batch(out_path: Path, *, lake: Path, symbols, batch: bool) -> Path:
    raw_cfg = _LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code_optuna.yml"
    cfg_path = write_walkforward_test_config(
        raw_cfg, out_path,
        lake=lake, symbols=symbols,
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=2,
    )
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    doc.setdefault("optuna", {}).setdefault("acceleration", {})[
        "batch_daily_cache"
    ] = {"enabled": bool(batch)}
    cfg_path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return cfg_path


@pytest.mark.slow
def test_walkforward_objective_parity_legacy_vs_batch(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    symbols = ["AAA"]
    build_tiny_lake(lake, symbols, start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))

    cfg_legacy = _write_cfg_with_batch(
        tmp_path / "wf_legacy.yml", lake=lake, symbols=symbols, batch=False,
    )
    cfg_batch = _write_cfg_with_batch(
        tmp_path / "wf_batch.yml", lake=lake, symbols=symbols, batch=True,
    )

    res_legacy = run_walkforward_study(
        cfg_legacy, n_trials=2, allow_smoke=True, incumbent_trial=False,
    )
    res_batch = run_walkforward_study(
        cfg_batch, n_trials=2, allow_smoke=True, incumbent_trial=False,
    )

    assert res_legacy["status"] == "ok"
    assert res_batch["status"] == "ok"
    # best_value within 1e-9.
    assert abs(float(res_legacy["best_value"]) - float(res_batch["best_value"])) <= 1e-9
    # best_params exact (matching tolerance set on numerics).
    for k, v in res_legacy["best_params"].items():
        assert k in res_batch["best_params"]
        vb = res_batch["best_params"][k]
        if isinstance(v, float):
            assert abs(float(v) - float(vb)) <= 1e-9, f"{k}: legacy={v!r} batch={vb!r}"
        else:
            assert v == vb, f"{k}: legacy={v!r} batch={vb!r}"


def test_phase_profile_json_is_written_on_success(tmp_path: Path) -> None:
    """The phase-profile JSON lands next to the main study artifact."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    cfg = _write_cfg_with_batch(
        tmp_path / "wf.yml", lake=lake, symbols=["AAA"], batch=False,
    )
    result = run_walkforward_study(cfg, n_trials=2, allow_smoke=True)
    assert result["status"] == "ok"
    profile_path = Path(result["phase_profile_path"])
    assert profile_path.is_file(), f"phase profile not written: {profile_path}"
    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    assert "phase_seconds" in payload
    assert "optuna_optimize" in payload["phase_seconds"]
    assert "fold_context_precompute" in payload["phase_seconds"]
    assert "counters" in payload
    assert "memory" in payload
    assert payload["config_hash"]
    # dataset_hash + code_hash are set on success path.
    assert payload["dataset_hash"]
