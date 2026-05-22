"""The quarantined Optuna config is refused by the standard config loader.

Realism remediation 2 Phase 0 (audit §P0-001). The prior
``bowaka_v2_walkforward_optuna.yml`` claimed ``current_code_parity`` while
materially changing the strategy; it now lives under ``configs/quarantined/``
and ``load_config`` must refuse any path under a ``quarantined/`` directory.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.config.loader import load_config

# tests/unit/<this file> -> tests -> bowaka_v2_lab
_LAB_ROOT = Path(__file__).resolve().parents[2]
_QUARANTINED = (
    _LAB_ROOT / "configs" / "quarantined"
    / "bowaka_v2_walkforward_optuna__DO_NOT_USE.yml"
)


def test_quarantined_optuna_config_file_exists() -> None:
    """The optuna config was moved into configs/quarantined/, not deleted."""
    assert _QUARANTINED.is_file(), f"quarantined config missing: {_QUARANTINED}"
    # The banner is the first line and is a YAML comment.
    first_line = _QUARANTINED.read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("# QUARANTINED 2026-05-22")


def test_quarantined_optuna_config_not_loadable_by_default() -> None:
    """Loading the quarantined path through the standard loader raises."""
    with pytest.raises(ValueError, match="quarantined"):
        load_config(_QUARANTINED)


def test_quarantine_refusal_is_path_based() -> None:
    """ANY path under a quarantined/ directory is refused, not just by name."""
    other = _LAB_ROOT / "configs" / "quarantined" / "anything.yml"
    with pytest.raises(ValueError, match="quarantined"):
        load_config(other)


def test_non_quarantined_config_still_loads() -> None:
    """A regular shipping config is unaffected by the quarantine gate."""
    cfg = load_config(_LAB_ROOT / "configs" / "bowaka_v2_intended_realism.yml")
    assert cfg["strategy_id"] == "bowaka_v2"
