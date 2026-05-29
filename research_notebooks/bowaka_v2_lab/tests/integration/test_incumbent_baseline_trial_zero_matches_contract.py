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
    """Every incumbent key matches the MAPPED lab config (audit 2026-05-29 §6.7).

    Post-Phase-2 the incumbent reads the mapped lab config (flat execution keys,
    derived signal-fade gap + reward/risk ratio), NOT a raw-contract dotted
    lookup. Directly-mapped keys equal the mapped config; the v3 gap/ratio keys
    equal the value derived from the mapped config's absolute thresholds.
    """
    import pytest

    from bowaka_v2_lab.reference.import_config import build_config_from_contract

    params = _incumbent_baseline_params()
    cfg = build_config_from_contract(
        reference.load_actual_contract(),
        feed="iex", mode="current_code_parity", feed_thresholds="actual",
    )
    assert params, "incumbent baseline must be non-empty against a real contract"

    sf = "exits.signal_fade.score_thresholds."
    derived_keys = {sf + "hard_gap", sf + "critical_gap", "exits.reward_risk_ratio"}

    def _dig(d: dict, dotted: str):
        node = d
        for p in dotted.split("."):
            node = node[p]
        return node

    # Directly-mapped keys equal the mapped lab config value.
    for name, value in params.items():
        if name in derived_keys:
            continue
        assert _dig(cfg, name) == value, (
            f"incumbent[{name}]={value!r} does not match mapped config "
            f"{_dig(cfg, name)!r}"
        )

    # v3 gap/ratio keys are derived from the mapped config's absolute fields.
    st = _dig(cfg, "exits.signal_fade.score_thresholds")
    assert params[sf + "hard_gap"] == pytest.approx(st["hard"] - st["soft"])
    assert params[sf + "critical_gap"] == pytest.approx(st["critical"] - st["hard"])
    assert params["exits.reward_risk_ratio"] == pytest.approx(
        _dig(cfg, "exits.target_pct") / _dig(cfg, "exits.stop_pct")
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
