"""Every non-quarantined shipping config declares simulation.mode (realism Phase 0)."""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

# tests/unit/<this file> -> tests -> bowaka_v2_lab
_LAB_ROOT = Path(__file__).resolve().parents[2]
_CONFIGS = sorted((_LAB_ROOT / "configs").glob("bowaka_v2_*.yml"))
_VALID_MODES = {"current_code_parity", "intended_realism", "smoke_fixture"}


def test_shipping_configs_discovered() -> None:
    assert _CONFIGS, f"no bowaka_v2_*.yml configs under {_LAB_ROOT / 'configs'}"
    # The glob is non-recursive, so the quarantined configs/quarantined/ tree is
    # excluded (realism remediation 2 Phase 0); the parametrized test below
    # still checks every discovered shipping config declares simulation.mode.


@pytest.mark.parametrize("cfg_path", _CONFIGS, ids=[p.name for p in _CONFIGS])
def test_config_has_simulation_mode(cfg_path: Path) -> None:
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    assert "simulation" in raw, f"{cfg_path.name} has no `simulation:` block"
    mode = raw["simulation"].get("mode")
    assert mode in _VALID_MODES, f"{cfg_path.name}: simulation.mode={mode!r} is invalid"
