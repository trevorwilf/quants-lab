"""All post-search stages must use the validation controller_compat setting.

Validates Fix 4: canonicalize_params() defaults controller_compat=True,
and the pipeline must explicitly override it for all downstream stages.
"""
import inspect
import pytest
from dataclasses import replace
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.optuna.canonicalizer import canonicalize_params
from pmm_lab.config.params import PairRules, FeeConfig

_RULES = PairRules(
    price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0,
    fees=FeeConfig(0.001, 0.002),
)

_RAW_PARAMS = {
    "buy_spread_base": 1.0, "buy_spread_ratio": 2.0, "buy_n_levels": 2,
    "sell_spread_base": 1.0, "sell_spread_ratio": 2.0, "sell_n_levels": 2,
    "buy_side_weight": 0.5, "total_amount_quote": 100.0, "amount_skew": 1.0,
    "executor_refresh_time": 3120, "cooldown_time": 3120,
    "stop_loss": 0.03, "take_profit": 0.015, "time_limit": 43200,
    "trailing_stop_activation": 0.0, "trailing_stop_delta": 0.0,
    "macd_fast": 21, "macd_slow": 42, "macd_signal": 9, "natr_length": 14,
}


class TestCanonicalizeDefaultsControllerCompat:
    """canonicalize_params does NOT set controller_compat — uses SimConfig default."""

    def test_defaults_to_true(self):
        config, reject = canonicalize_params(_RAW_PARAMS, _RULES, 100.0)
        assert config is not None
        assert config.controller_compat is True

    def test_replace_overrides(self):
        config, _ = canonicalize_params(_RAW_PARAMS, _RULES, 100.0)
        val_config = replace(config, controller_compat=False)
        assert val_config.controller_compat is False
        assert config.controller_compat is True  # original unchanged


class TestSensitivityAcceptsControllerCompat:
    """compute_sensitivity() must accept a controller_compat parameter."""

    def test_parameter_exists(self):
        from pmm_lab.optuna.sensitivity import compute_sensitivity
        sig = inspect.signature(compute_sensitivity)
        assert "controller_compat" in sig.parameters, \
            "compute_sensitivity must accept controller_compat parameter"


class TestRunnerUsesValConfig:
    """run_full_pipeline must use val_config (not best_config) for all post-search stages."""

    def test_walkforward_uses_val_config(self):
        """Walk-forward call must reference val_config."""
        from pmm_lab.deploy import runner
        source = inspect.getsource(runner.run_full_pipeline)
        val_idx = source.find("val_config = _replace(")
        assert val_idx > 0, "val_config creation not found in runner"
        post_val = source[val_idx:]
        wf_start = post_val.find("run_walk_forward(")
        assert wf_start >= 0
        wf_call = post_val[wf_start:wf_start + 300]
        assert "val_config" in wf_call, \
            "run_walk_forward should use val_config, not best_config"

    def test_sensitivity_gets_controller_compat(self):
        """The sensitivity call in the pipeline must pass controller_compat."""
        from pmm_lab.deploy import runner
        source = inspect.getsource(runner.run_full_pipeline)
        sens_idx = source.find("compute_sensitivity(")
        assert sens_idx > 0
        sens_call = source[sens_idx:sens_idx + 300]
        assert "controller_compat" in sens_call, \
            "compute_sensitivity call must pass controller_compat"

    def test_export_uses_val_config(self):
        """export_yaml call must use val_config."""
        from pmm_lab.deploy import runner
        source = inspect.getsource(runner.run_full_pipeline)
        val_idx = source.find("val_config = _replace(")
        post_val = source[val_idx:]
        export_idx = post_val.find("export_yaml(")
        assert export_idx >= 0
        export_call = post_val[export_idx:export_idx + 200]
        assert "val_config" in export_call, \
            "export_yaml should use val_config, not best_config"
