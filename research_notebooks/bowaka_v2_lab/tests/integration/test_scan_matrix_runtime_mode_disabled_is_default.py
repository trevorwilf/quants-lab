"""Every committed config defaults ``runtime_mode`` to ``"disabled"``.

Speedup report v2 §6.1 / §11.2 Phase 6 / acceptance. The Phase 6
deliverables are research-only — no production config flips the matrix
runtime on. This integration test sweeps the configs/ directory and
asserts the default.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_LAB_ROOT = Path(__file__).resolve().parents[2]
_CONFIGS = sorted((_LAB_ROOT / "configs").glob("bowaka_v2_*.yml"))


@pytest.mark.parametrize("cfg_path", _CONFIGS, ids=[p.name for p in _CONFIGS])
def test_runtime_mode_is_disabled_or_absent(cfg_path: Path) -> None:
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    sm = (((doc or {}).get("optuna") or {}).get("acceleration") or {}).get(
        "scan_matrix", {},
    )
    # Absent → loader defaults to disabled. Present → must be "disabled".
    mode = sm.get("runtime_mode", "disabled")
    assert mode == "disabled", (
        f"{cfg_path.name} sets runtime_mode={mode!r}; speedup v2 Phase 6 is "
        "research-only and EVERY committed config must default to "
        "'disabled'"
    )
