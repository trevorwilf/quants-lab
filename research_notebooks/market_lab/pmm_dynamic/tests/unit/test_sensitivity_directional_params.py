"""Directional sensitivity must actually perturb signal hyperparameters."""
import pytest


def test_mr_perturbable_params_includes_signal_hyperparams():
    from pmm_lab.optuna.sensitivity import MR_PERTURBABLE_PARAMS
    for p in ("bb_length", "bb_std", "rsi_length", "rsi_entry_threshold",
              "trend_ema_length", "volume_filter_window"):
        assert p in MR_PERTURBABLE_PARAMS, f"MR perturb list must include {p}"


def test_ema_perturbable_params_includes_regime_hyperparams():
    from pmm_lab.optuna.sensitivity import EMA_PERTURBABLE_PARAMS
    for p in ("regime_ema_fast", "regime_ema_slow",
              "regime_adx_length", "regime_adx_threshold"):
        assert p in EMA_PERTURBABLE_PARAMS, f"EMA perturb list must include {p}"


def test_mr_notebook_calls_compute_sensitivity_with_directional_perturb():
    """_build_cell8.py MR block must pass MR_PERTURBABLE_PARAMS explicitly."""
    from pathlib import Path
    src = Path("notebooks/direction-custom/_build_cell8.py").read_text()
    assert "MR_PERTURBABLE_PARAMS" in src, (
        "_build_cell8.py must import/use MR_PERTURBABLE_PARAMS for MR sensitivity"
    )
    assert "EMA_PERTURBABLE_PARAMS" in src, (
        "_build_cell8.py must import/use EMA_PERTURBABLE_PARAMS for EMA sensitivity"
    )


def test_mr_perturbable_params_excludes_pmm_only_fields():
    """The existing 'silent-skip' logic for missing params must still work.
    MR doesn't have buy_spread_base / sell_spread_base / executor_refresh_time."""
    from pmm_lab.optuna.sensitivity import MR_PERTURBABLE_PARAMS
    assert "stop_loss" in MR_PERTURBABLE_PARAMS
    assert "buy_spread_base" not in MR_PERTURBABLE_PARAMS
    assert "sell_spread_base" not in MR_PERTURBABLE_PARAMS


def test_pmm_perturbable_params_unchanged():
    """Regression: the original PMM PERTURBABLE_PARAMS list is unmodified."""
    from pmm_lab.optuna.sensitivity import PERTURBABLE_PARAMS
    assert PERTURBABLE_PARAMS == [
        "buy_spread_base", "sell_spread_base",
        "stop_loss", "take_profit",
        "executor_refresh_time", "cooldown_time",
        "total_amount_quote",
    ]
