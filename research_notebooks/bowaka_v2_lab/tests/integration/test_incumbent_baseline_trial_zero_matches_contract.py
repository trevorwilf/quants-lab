"""When --incumbent-trial is set, trial 0 is pinned to the actual-contract params.

Realism remediation 2 Phase 8. The optimizer's best is meaningful only when it
beats the live config; the incumbent baseline guarantees there is one such
trial in every study (trial 0). The reference parameter set is the actual
contract; ``_incumbent_baseline_params`` projects every search-space key to its
contract value.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from bowaka_v2_lab import reference
from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.search_space import SEARCH_SPACE_SPEC
from bowaka_v2_lab.optuna.walkforward_runner import (
    _incumbent_baseline_params,
    run_walkforward_study,
)


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated -- run mirror_bowaka_v2_source.ps1")


def test_incumbent_baseline_params_reads_contract_values() -> None:
    """Every contract-projected key maps to its value from the frozen contract."""
    params = _incumbent_baseline_params()
    contract = reference.load_actual_contract()
    # At minimum the strategy contract carries enough signal/sizing/risk/exits
    # values that several search-space keys are populated. The exact count
    # depends on the contract content; assert "non-empty + every value matches".
    assert params, "incumbent baseline must be non-empty against a real contract"
    for name, value in params.items():
        # Dotted-path lookup against the contract reproduces the same value.
        parts = name.split(".")
        node = contract
        for p in parts:
            node = node[p]
        assert node == value, (
            f"incumbent[{name}]={value!r} does not match contract value {node!r}"
        )


def test_incumbent_keys_are_subset_of_search_space() -> None:
    """Every incumbent key is also in the Optuna search space (so trial 0 records it)."""
    params = _incumbent_baseline_params()
    extra = set(params) - set(SEARCH_SPACE_SPEC)
    assert not extra, f"incumbent keys not in search space: {sorted(extra)}"


def test_run_walkforward_study_pins_trial_zero_to_incumbent(
    tmp_path: Path, lab_root: Path,
) -> None:
    """End-to-end: with incumbent_trial=True, trial 0 carries the contract params."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    raw_cfg = lab_root / "configs" / "bowaka_v2_actual_iex_current_code_optuna.yml"
    cfg_path = write_walkforward_test_config(
        raw_cfg, tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1),
        n_trials=2,
    )
    result = run_walkforward_study(
        cfg_path, n_trials=2, allow_smoke=True, incumbent_trial=True,
    )
    assert result["status"] == "ok"
    # The study artifact carries the incumbent comparison.
    promo = result["promotion_evidence"]
    assert promo["incumbent_comparison"] is not None, (
        "promotion_evidence missing incumbent_comparison — trial 0 was not "
        "pinned as the incumbent baseline"
    )
    inc = promo["incumbent_comparison"]
    assert inc["incumbent_trial_number"] == 0
    # The recorded params on trial 0 match (clamped to bounds) the contract.
    incumbent_params = _incumbent_baseline_params()
    for name, value in incumbent_params.items():
        if name in inc["incumbent_params"]:
            recorded = inc["incumbent_params"][name]
            # For numerics the recorded value should be the contract value (or
            # the clamped equivalent for an out-of-bounds incumbent).
            if isinstance(value, (int, float)) and isinstance(recorded, (int, float)):
                assert abs(float(recorded) - float(value)) < max(abs(float(value)) * 1e-3, 1e-6) \
                    or name in inc.get("incumbent_clamped", {}), (
                    f"trial-0 {name}={recorded!r} != contract {value!r}"
                )
            else:
                assert recorded == value or name in inc.get("incumbent_clamped", {}), (
                    f"trial-0 {name}={recorded!r} != contract {value!r}"
                )
