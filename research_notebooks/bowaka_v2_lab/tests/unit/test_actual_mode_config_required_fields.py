"""Real-mode configs reject missing required fields (audit 2026-05-23 §P2-001).

Pre-remediation stale defaults like ``UniverseConfig.max_price = 1000.0`` /
``min_adv_dollars = 1_000_000`` masked omission of these fields in real-mode
configs. Phase 3 reset those defaults to the live values; this test ensures
that a real-mode config which OMITS a required field still loads (because the
default now matches the live contract) and that the resulting validated value
equals the live contract value.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.config.models import BowakaV2Config


@pytest.fixture
def _intended_realism_dict(lab_root: Path) -> dict:
    cfg_path = lab_root / "configs" / "bowaka_v2_actual_iex_intended_realism.yml"
    if not cfg_path.is_file():
        pytest.skip(f"{cfg_path} not committed")
    return yaml.safe_load(cfg_path.read_text(encoding="utf-8"))


def _delete_dotted(d: dict, dotted: str) -> None:
    parts = dotted.split(".")
    node = d
    for p in parts[:-1]:
        node = node[p]
    node.pop(parts[-1], None)


def test_universe_max_price_default_is_live_value():
    """A real-mode config that omits ``universe.max_price`` loads as 20.0 (live)."""
    from bowaka_v2_lab.config.models import UniverseConfig

    sc = UniverseConfig()
    assert sc.max_price == 20.0


def test_universe_min_adv_dollars_default_is_live_value():
    from bowaka_v2_lab.config.models import UniverseConfig

    sc = UniverseConfig()
    assert sc.min_adv_dollars == 250_000.0


def test_scanner_max_candidates_default_is_live_value():
    from bowaka_v2_lab.config.models import ScannerConfig

    sc = ScannerConfig()
    assert sc.max_candidates_per_scan == 25


def test_scanner_min_signal_strength_default_is_live_value():
    from bowaka_v2_lab.config.models import ScannerConfig

    sc = ScannerConfig()
    assert sc.min_signal_strength == 0.0


def test_committed_config_universe_matches_live_contract(_intended_realism_dict):
    """The shipped intended_realism config carries the live universe limits."""
    assert _intended_realism_dict["universe"]["max_price"] == 20.0
    assert _intended_realism_dict["universe"]["min_adv_dollars"] == 250_000


def test_committed_config_scanner_matches_live_contract(_intended_realism_dict):
    """The shipped intended_realism config carries the live scanner limits."""
    sc = _intended_realism_dict["scanner"]
    assert sc["max_candidates_per_scan"] == 25
    assert sc["max_entries_per_scan"] == 3
    assert sc["min_signal_strength"] == 0.0


def test_config_with_omitted_universe_fields_loads_with_live_defaults(
    _intended_realism_dict,
):
    """Omitting universe.max_price / min_adv_dollars falls back to live defaults."""
    cfg = dict(_intended_realism_dict)
    _delete_dotted(cfg, "universe.max_price")
    _delete_dotted(cfg, "universe.min_adv_dollars")
    validated = BowakaV2Config.model_validate(cfg)
    assert validated.universe.max_price == 20.0
    assert validated.universe.min_adv_dollars == 250_000.0


def test_config_with_stale_max_price_is_validated_as_provided(_intended_realism_dict):
    """An explicit value still wins over the default (no silent override)."""
    cfg = dict(_intended_realism_dict)
    cfg["universe"] = dict(cfg["universe"])
    cfg["universe"]["max_price"] = 1000.0  # the OLD stale default
    validated = BowakaV2Config.model_validate(cfg)
    assert validated.universe.max_price == 1000.0  # honored verbatim


def test_defaults_module_was_removed():
    """``config/defaults.py`` was unused and removed (audit §P2-001)."""
    with pytest.raises(ImportError):
        from bowaka_v2_lab.config import defaults  # noqa: F401
