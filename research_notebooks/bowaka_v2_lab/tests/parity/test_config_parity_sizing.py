"""Equal-slice sizing math parity with the live strategy.

Realism Phase 1, Task D. The live strategy sizes each position as an equal
slice of a fixed bankroll: ``target_notional = bankroll_fraction * bankroll /
max_concurrent_positions`` and ``qty = int(target_notional // price)``.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from bowaka_v2_lab.sim.strategy_consumer import compute_target_notional, size_quantity

_LAB_ROOT = Path(__file__).resolve().parents[2]
_REALISM_CONFIG = _LAB_ROOT / "configs" / "bowaka_v2_intended_realism.yml"


def test_equal_slice_target_notional_is_4000() -> None:
    """0.8 * 90_000 / 18 == 4_000.0 (the live equal-slice slot)."""
    sizing = {
        "sizing_mode": "equal_slice",
        "bankroll_fixed_dollars": 90_000,
        "max_concurrent_positions": 18,
        "equal_slice_bankroll_fraction": 0.80,
        "min_order_notional": 500,
    }
    assert compute_target_notional(sizing) == 4_000.0


def test_size_quantity_floor_division() -> None:
    """qty = int(4000 // 12.34) == 324 (whole-share floor division)."""
    assert size_quantity(4_000.0, 12.34) == 324


def test_realism_config_sizing_yields_4000() -> None:
    """The shipped intended-realism config's sizing block sizes to $4,000."""
    assert _REALISM_CONFIG.is_file(), (
        f"{_REALISM_CONFIG} missing -- run `bowaka-v2-lab import-actual-config`"
    )
    cfg = yaml.safe_load(_REALISM_CONFIG.read_text(encoding="utf-8"))
    sizing = cfg["sizing"]
    assert sizing["sizing_mode"] == "equal_slice"
    assert compute_target_notional(sizing) == 4_000.0
