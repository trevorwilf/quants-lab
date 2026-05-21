"""The quarantined walk-forward Optuna config is excluded from the shipping glob.

Realism Phase 0: `bowaka_v2_walkforward_optuna.yml` is renamed with a
`.quarantined` suffix so env-check and config-validation tests (which glob
`configs/bowaka_v2_*.yml`) cannot pick up a known-broken schema. Phase 1
restores it.
"""
from __future__ import annotations

from pathlib import Path


def test_quarantined_file_exists(lab_root: Path) -> None:
    q = lab_root / "configs" / "bowaka_v2_walkforward_optuna.yml.quarantined"
    assert q.is_file(), "expected the quarantined optuna config with .quarantined suffix"


def test_original_optuna_config_absent(lab_root: Path) -> None:
    original = lab_root / "configs" / "bowaka_v2_walkforward_optuna.yml"
    assert not original.exists(), "the un-quarantined .yml optuna config must not exist"


def test_quarantined_excluded_from_shipping_glob(lab_root: Path) -> None:
    shipping = sorted((lab_root / "configs").glob("bowaka_v2_*.yml"))
    assert shipping, "expected at least one bowaka_v2_*.yml shipping config"
    names = {p.name for p in shipping}
    assert "bowaka_v2_walkforward_optuna.yml" not in names
    assert "bowaka_v2_walkforward_optuna.yml.quarantined" not in names


def test_quarantined_file_still_parses_as_yaml(lab_root: Path) -> None:
    """The quarantined file is intact YAML (Phase 1 restores it verbatim)."""
    import yaml

    q = lab_root / "configs" / "bowaka_v2_walkforward_optuna.yml.quarantined"
    raw = yaml.safe_load(q.read_text(encoding="utf-8"))
    assert isinstance(raw, dict)
    assert raw["strategy_id"] == "bowaka_v2"
    assert raw["optuna"]["n_startup_trials"] == 500
