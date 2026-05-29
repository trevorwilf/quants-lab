"""Optuna refuses to run a current_code_parity study without an explicit opt-in.

Realism remediation 2 Phase 8 (audit §P0-011). The current_code_parity contract
reproduces the live code's *warts* (zero-spread quote fallback, fail-open halt
gate); optimizing against it produces a parameter set tuned to simulator
artifacts, not the strategy's edge. The runner refuses such studies unless the
operator explicitly passes ``--allow-current-code-parity-study --tier
research_only`` (CLI) / ``allow_current_code_parity_study=True, tier="research_only"``
(in-process). The refusal raises BEFORE any dataset / plan / lake probing so a
study against an unavailable lake also raises.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake, write_walkforward_test_config
from bowaka_v2_lab.optuna.walkforward_runner import (
    CurrentCodeParityStudyRefused,
    assert_simulation_contract_admissible,
    run_walkforward_study,
)


def _current_code_parity_cfg() -> dict:
    """Minimal config in current_code_parity mode for the gate-only tests."""
    return {
        "simulation": {"mode": "current_code_parity"},
        "market_data": {"feed": "iex"},
    }


def test_gate_refuses_current_code_parity_without_flag() -> None:
    """The gate raises CurrentCodeParityStudyRefused when neither flag is set."""
    with pytest.raises(CurrentCodeParityStudyRefused, match="current_code_parity"):
        assert_simulation_contract_admissible(
            _current_code_parity_cfg(),
            allow_current_code_parity_study=False,
            tier=None,
        )


def test_gate_refuses_current_code_parity_with_only_one_part_of_the_opt_in() -> None:
    """Both flags are required — only --allow-... without --tier is refused."""
    with pytest.raises(CurrentCodeParityStudyRefused):
        assert_simulation_contract_admissible(
            _current_code_parity_cfg(),
            allow_current_code_parity_study=True,
            tier=None,
        )
    with pytest.raises(CurrentCodeParityStudyRefused):
        assert_simulation_contract_admissible(
            _current_code_parity_cfg(),
            allow_current_code_parity_study=False,
            tier="research_only",
        )


def test_gate_refuses_current_code_parity_with_wrong_tier() -> None:
    """The tier MUST be research_only; backtesting_only or higher is refused."""
    for tier in ("backtesting_only", "paper_candidate", "live_candidate"):
        with pytest.raises(CurrentCodeParityStudyRefused):
            assert_simulation_contract_admissible(
                _current_code_parity_cfg(),
                allow_current_code_parity_study=True,
                tier=tier,
            )


def test_gate_admits_current_code_parity_with_explicit_opt_in() -> None:
    """With both flags set the gate is a no-op."""
    # No raise.
    assert_simulation_contract_admissible(
        _current_code_parity_cfg(),
        allow_current_code_parity_study=True,
        tier="research_only",
    )


def test_gate_admits_intended_realism_without_flag() -> None:
    """intended_realism is admissible at this gate (its data-prereq gate runs separately)."""
    cfg = {"simulation": {"mode": "intended_realism"}, "market_data": {"feed": "sip"}}
    assert_simulation_contract_admissible(
        cfg, allow_current_code_parity_study=False, tier=None,
    )


def test_gate_admits_smoke_fixture_without_flag() -> None:
    """smoke_fixture is admissible (the smoke gate is allow_smoke, separately)."""
    cfg = {"simulation": {"mode": "smoke_fixture"}, "market_data": {"feed": "iex"}}
    assert_simulation_contract_admissible(
        cfg, allow_current_code_parity_study=False, tier=None,
    )


def _write_parity_cfg(tmp_path: Path, lab_root: Path) -> Path:
    """Write a current_code_parity walk-forward config against a tiny lake.

    Speedup report §4 P0-A / Phase 0 task 3: the unified preflight DQ gate now
    fails closed on adjustment-gating failures even in parity mode (it used to
    surface them as a warn). The tiny synthetic lake here does not provide
    split / corporate-action metadata, so the test's parity config must drop
    ``require_adjusted_daily_bars`` / ``require_split_adjustment`` to keep the
    DQ probe clean — otherwise the study would fail closed before the
    parity-gate admission this test is exercising. This is a test-fixture
    change only; production parity studies against a real lake continue to
    require adjustment, and the new Phase 0 gate refuses them when the lake
    is raw (see ``test_walkforward_fails_before_context_build_on_raw_lake``).
    """
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1))
    raw_cfg = lab_root / "configs" / "bowaka_v2_actual_iex_current_code_optuna.yml"
    # Reuse the existing write_walkforward_test_config helper, then overwrite
    # simulation.mode = current_code_parity to exercise the refusal gate.
    cfg_path = write_walkforward_test_config(
        raw_cfg, tmp_path / "wf.yml",
        lake=lake, symbols=["AAA"],
        start=dt.date(2024, 1, 1), end=dt.date(2024, 5, 1), n_trials=1,
    )
    # The helper pins smoke_fixture; overwrite to current_code_parity for this test.
    cfg_doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    cfg_doc["simulation"] = {"mode": "current_code_parity"}
    # Drop adjustment requirements (see docstring): the tiny synthetic lake
    # carries no manifest declaring adjustment policy; the post-Phase-0
    # adjustment-gating DQ check would otherwise refuse the study.
    cfg_doc.setdefault("market_data", {})
    cfg_doc["market_data"]["require_adjusted_daily_bars"] = False
    cfg_doc["market_data"]["require_split_adjustment"] = False
    # Audit 2026-05-29 §5.4 / Phase 1: the full-fold preflight now runs for
    # current_code_parity too. The synthetic lake has no asset master (empty
    # PIT universe by design -> a fast, candidate-free plumbing backtest), so
    # set the PIT-universe floor to 0 to disable that gate for this fixture.
    # This test exercises the parity ADMISSION gate, not the universe-size gate
    # (covered by
    # test_current_code_parity_full_fold_preflight_blocks_empty_pit_universe).
    # ``scanner`` and other contract fields are parity-locked and must not be
    # altered here (doing so trips the config-parity gate).
    cfg_doc["preflight"] = {"min_pit_universe_per_fold": 0}
    cfg_path.write_text(yaml.safe_dump(cfg_doc), encoding="utf-8")
    return cfg_path


def test_run_walkforward_study_refuses_current_code_parity_without_flag(
    tmp_path: Path, lab_root: Path,
) -> None:
    """End-to-end: run_walkforward_study refuses current_code_parity without opt-in."""
    cfg_path = _write_parity_cfg(tmp_path, lab_root)
    with pytest.raises(CurrentCodeParityStudyRefused):
        run_walkforward_study(cfg_path, n_trials=1)


def test_run_walkforward_study_admits_current_code_parity_with_flag(
    tmp_path: Path, lab_root: Path,
) -> None:
    """End-to-end: run_walkforward_study admits current_code_parity with both flags."""
    cfg_path = _write_parity_cfg(tmp_path, lab_root)
    result = run_walkforward_study(
        cfg_path, n_trials=1,
        allow_current_code_parity_study=True, tier="research_only",
    )
    assert result["status"] == "ok"
    assert result["simulation_contract"] == "current_code_parity"
    # The mechanical tier cap stays research_only.
    assert result["suitability_tier"] == "research_only"
