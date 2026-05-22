"""Every shipping bowaka_v2_*.yml config passes env-check.

Parametrized over ``configs/bowaka_v2_*.yml`` (a *non-recursive* glob, so the
quarantined ``configs/quarantined/`` tree is excluded — realism remediation 2
Phase 0). Each shipping config must ``BowakaV2Config.model_validate`` and exit 0
from the ``env-check`` CLI.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.config.models import BowakaV2Config

_LAB_ROOT = Path(__file__).resolve().parents[2]
_CONFIGS = sorted((_LAB_ROOT / "configs").glob("bowaka_v2_*.yml"))


def test_shipping_configs_discovered() -> None:
    names = {p.name for p in _CONFIGS}
    assert _CONFIGS, f"no bowaka_v2_*.yml configs under {_LAB_ROOT / 'configs'}"
    # The realism-intended config ships; the walk-forward optuna config is
    # quarantined (realism remediation 2 Phase 0) and must NOT be discovered.
    assert "bowaka_v2_intended_realism.yml" in names
    assert "bowaka_v2_walkforward_optuna.yml" not in names


@pytest.mark.parametrize("cfg_path", _CONFIGS, ids=[p.name for p in _CONFIGS])
def test_config_env_check_exits_zero(cfg_path: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "env-check", "--config", str(cfg_path)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"{cfg_path.name} env-check failed\nstderr: {result.stderr}\nstdout: {result.stdout}"
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["strategy_id"] == "bowaka_v2"


@pytest.mark.parametrize("cfg_path", _CONFIGS, ids=[p.name for p in _CONFIGS])
def test_config_pydantic_validates(cfg_path: Path) -> None:
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    validated = BowakaV2Config.model_validate(raw)
    assert validated.strategy_id == "bowaka_v2"
