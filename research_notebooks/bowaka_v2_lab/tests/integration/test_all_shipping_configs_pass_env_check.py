"""Every shipping ``bowaka_v2_*.yml`` config passes ``cli env-check`` (Phase 11)."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_LAB_ROOT = Path(__file__).resolve().parents[2]
# Shipping configs at the end of remediation 2 (audit closure reference).
# Phase 0 quarantined the prior walk-forward Optuna config; Phase 1 + Phase 8
# generated these contract-parity replacements.
_SHIPPING_CONFIGS = (
    "bowaka_v2_actual_iex_current_code.yml",
    "bowaka_v2_actual_iex_intended_realism.yml",
    "bowaka_v2_actual_sip_intended_realism.yml",
    "bowaka_v2_actual_iex_current_code_optuna.yml",
    "bowaka_v2_actual_iex_intended_realism_optuna.yml",
    "bowaka_v2_actual_sip_intended_realism_optuna.yml",
    "bowaka_v2_backtest_smoke.yml",
)


@pytest.mark.parametrize("config", _SHIPPING_CONFIGS)
def test_shipping_config_env_checks(config: str) -> None:
    cfg = _LAB_ROOT / "configs" / config
    assert cfg.is_file(), f"shipping config missing: {cfg}"
    out = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "env-check", "--config", str(cfg)],
        capture_output=True, text=True, timeout=30,
    )
    assert out.returncode == 0, (
        f"env-check failed for {config}: stderr={out.stderr!r}, stdout={out.stdout!r}"
    )
    payload = json.loads(out.stdout)
    assert payload.get("status") == "ok"
    assert payload.get("strategy_id") == "bowaka_v2"
