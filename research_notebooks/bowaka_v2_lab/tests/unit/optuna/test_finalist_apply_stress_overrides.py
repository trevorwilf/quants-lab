"""``apply_stress_overrides`` applies absolute + multiplier dotted-path patches.

Speedup report v2 §1.4 / §8.3 / Phase 5 task 3. Two override forms:

* Absolute: ``"execution.max_spread_bps": 50`` → sets the value verbatim.
* Multiplier: ``"execution.max_spread_bps_multiplier": 1.5`` → resolves
  the current value and multiplies it.

Unknown ``*_multiplier`` targets raise ``KeyError`` so the operator sees
a clear error rather than a silently-ignored stress.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.evaluate_finalists import apply_stress_overrides


def test_absolute_override_replaces_value() -> None:
    cfg = {"execution": {"max_spread_bps": 100}}
    out = apply_stress_overrides(cfg, {"execution.max_spread_bps": 50})
    assert out["execution"]["max_spread_bps"] == 50
    # Original is untouched (deep copy).
    assert cfg["execution"]["max_spread_bps"] == 100


def test_multiplier_form_multiplies_resolved_value() -> None:
    cfg = {"execution": {"max_spread_bps": 100}}
    out = apply_stress_overrides(
        cfg, {"execution.max_spread_bps_multiplier": 1.5},
    )
    assert out["execution"]["max_spread_bps"] == 150


def test_multiplier_form_preserves_int_type() -> None:
    cfg = {"execution": {"max_quote_age_seconds": 60}}
    out = apply_stress_overrides(
        cfg, {"execution.max_quote_age_seconds_multiplier": 0.5},
    )
    assert out["execution"]["max_quote_age_seconds"] == 30
    assert isinstance(out["execution"]["max_quote_age_seconds"], int)


def test_multiplier_missing_target_raises() -> None:
    cfg = {"execution": {"max_spread_bps": 100}}
    with pytest.raises(KeyError, match="fill_participation"):
        apply_stress_overrides(
            cfg, {"execution.fill_participation_multiplier": 0.75},
        )


def test_absolute_path_creates_nested_key() -> None:
    """``apply_stress_overrides`` allows setting a previously-absent key."""
    cfg = {"backtest": {}}
    out = apply_stress_overrides(cfg, {"backtest.cost_stress": "aggressive"})
    assert out["backtest"]["cost_stress"] == "aggressive"
