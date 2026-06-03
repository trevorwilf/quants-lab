"""Phase 1 (walk-forward numba) — numba is OFF by default on every base config.

Optional-dependency contract: no committed ``configs/bowaka_v2_*.yml`` may set
``optuna.acceleration.numba.enabled: true``. Enabling numba is reserved for a
dedicated overlay (Phase 3). Mirrors the scan-matrix disabled-default sweep.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_CONFIGS = Path(__file__).resolve().parents[2] / "configs"
_BASE_CONFIGS = sorted(_CONFIGS.glob("bowaka_v2_*.yml"))


def _numba_enabled(raw: dict) -> bool:
    nb = (((raw or {}).get("optuna") or {}).get("acceleration") or {}).get("numba") or {}
    return bool(nb.get("enabled", False))


def test_some_base_configs_exist() -> None:
    assert _BASE_CONFIGS, "no committed bowaka_v2_*.yml configs found"


@pytest.mark.parametrize("cfg_path", _BASE_CONFIGS, ids=lambda p: p.name)
def test_numba_disabled_by_default_on_base_config(cfg_path: Path) -> None:
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    assert not _numba_enabled(raw), (
        f"{cfg_path.name} enables optuna.acceleration.numba — base configs must "
        f"keep it OFF (enable only via a dedicated overlay)."
    )


def test_numba_flag_parses_false_when_absent() -> None:
    # An entirely missing acceleration/numba block must read as disabled.
    assert _numba_enabled({}) is False
    assert _numba_enabled({"optuna": {}}) is False
    assert _numba_enabled({"optuna": {"acceleration": {}}}) is False
