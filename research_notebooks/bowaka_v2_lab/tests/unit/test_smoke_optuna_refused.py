"""run-backtest / walk-forward Optuna refuse smoke_fixture configs (realism Phase 0).

The `smoke` subcommand is the intended entry point for fixture configs and is
always exempt; `run-backtest` and `optuna` refuse smoke_fixture unless the
override is passed.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.cli_runners import run_backtest_command
from bowaka_v2_lab.optuna.walkforward_runner import run_walkforward_study

_REFUSAL = "refused: simulation.mode is 'smoke_fixture'"


def _minimal_smoke_config(tmp_path: Path, lab_root: Path) -> Path:
    """A loadable simulation.mode=smoke_fixture config with paths under tmp."""
    raw = yaml.safe_load(
        (lab_root / "configs" / "bowaka_v2_backtest_smoke.yml").read_text(encoding="utf-8")
    )
    # lab_root must contain 'bowaka_v2_lab' (assert_strategy_isolation).
    lab = tmp_path / "bowaka_v2_lab"
    raw["paths"] = {
        "lab_root": str(lab),
        "data_root": str(lab / "data"),
        "artifact_root": str(lab / "artifacts"),
    }
    out = tmp_path / "smoke_cfg.yml"
    out.write_text(yaml.safe_dump(raw), encoding="utf-8")
    return out


def test_walkforward_refuses_smoke_fixture(tmp_path: Path, lab_root: Path) -> None:
    cfg = _minimal_smoke_config(tmp_path, lab_root)
    with pytest.raises(RuntimeError) as exc:
        run_walkforward_study(cfg)
    assert "smoke_fixture" in str(exc.value)
    assert "refused" in str(exc.value).lower()


def test_walkforward_smoke_override_passes_the_refusal_gate(
    tmp_path: Path, lab_root: Path
) -> None:
    """allow_smoke=True clears the refusal; any later failure is NOT the refusal."""
    cfg = _minimal_smoke_config(tmp_path, lab_root)
    try:
        run_walkforward_study(cfg, allow_smoke=True)
    except Exception as exc:  # noqa: BLE001 — a non-refusal failure is acceptable here
        assert _REFUSAL not in str(exc), "allow_smoke=True must clear the smoke refusal"


def test_run_backtest_refuses_smoke_fixture(tmp_path: Path, lab_root: Path) -> None:
    cfg = _minimal_smoke_config(tmp_path, lab_root)
    with pytest.raises(RuntimeError) as exc:
        run_backtest_command(cfg, smoke=False)
    assert "smoke_fixture" in str(exc.value)


def test_run_backtest_smoke_override_accepted(tmp_path: Path, lab_root: Path) -> None:
    cfg = _minimal_smoke_config(tmp_path, lab_root)
    result = run_backtest_command(
        cfg, smoke=False, allow_smoke=True, run_dir=str(tmp_path / "ovr")
    )
    assert result["status"] == "ok"


def test_smoke_subcommand_is_exempt(tmp_path: Path, lab_root: Path) -> None:
    """The `smoke` subcommand path (smoke=True) is never refused."""
    cfg = _minimal_smoke_config(tmp_path, lab_root)
    result = run_backtest_command(cfg, smoke=True, run_dir=str(tmp_path / "smoke_rd"))
    assert result["status"] == "ok"
