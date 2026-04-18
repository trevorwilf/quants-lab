"""
Parameter sensitivity analysis.

Perturbs key parameters by +/-delta_pct and re-evaluates the objective.
A config is fragile if small perturbations cause the score to flip sign
or collapse by more than a threshold fraction.

Usage (post-optimization, on top candidates):
    report = compute_sensitivity(params, candles, pair_rules, ...)
    penalty = report.sensitivity_penalty
"""

import logging
import numpy as np
from dataclasses import dataclass
from typing import Callable, Dict, List, Any, Optional

from pmm_lab.config.params import PairRules
from pmm_lab.optuna.canonicalizer import canonicalize_params
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.sim.runner import CandleSimRunner
from pmm_lab.sim.runner_dispatch import run_simulation
from pmm_lab.metrics.metrics import compute_metrics
from pmm_lab.objective.objective import objective_v1, objective_v2, REJECT_SCORE, ObjectiveWeights

logger = logging.getLogger(__name__)

# Parameters that are perturbed for sensitivity analysis
PERTURBABLE_PARAMS = [
    "buy_spread_base",
    "sell_spread_base",
    "stop_loss",
    "take_profit",
    "executor_refresh_time",
    "cooldown_time",
    "total_amount_quote",
]


# Directional-specific perturbation lists (ML-DIR-006). These include the
# strategy's actual signal-generation hyperparameters, not only execution params,
# so the sensitivity penalty reflects directional-strategy fragility.
MR_PERTURBABLE_PARAMS = [
    # Signal params
    "bb_length",
    "bb_std",
    "bbp_entry_threshold",
    "rsi_length",
    "rsi_entry_threshold",
    "trend_ema_length",
    "max_atr_pct_for_entry",
    "volume_filter_window",
    "min_volume_quantile",
    # Execution params
    "stop_loss",
    "take_profit",
    "cooldown_time",
    "total_amount_quote",
]


EMA_PERTURBABLE_PARAMS = [
    # Regime params
    "regime_ema_fast",
    "regime_ema_slow",
    "regime_adx_length",
    "regime_adx_threshold",
    "volume_filter_window",
    "min_volume_quantile",
    # Execution params
    "stop_loss",
    "take_profit",
    "cooldown_time",
    "total_amount_quote",
]
# TODO(P2.2 follow-up): perturbations of regime_ema_fast can trivially produce
# regime_ema_fast >= regime_ema_slow, which the canonicalizer rejects and inflates
# the sensitivity penalty with noise. Add a monotonic-aware perturbation policy
# that only perturbs regime_ema_fast downward when fast >= slow.


@dataclass
class SensitivityReport:
    """Result of sensitivity analysis on one parameter set."""
    baseline_score: float
    perturbed_scores: Dict[str, List[float]]  # param_name -> list of scores for each perturbation
    sign_flips: int                            # how many perturbations flipped score sign
    collapse_count: int                        # how many perturbations caused >50% collapse
    sensitivity_penalty: float                 # 0.0 = stable, higher = fragile
    n_perturbations: int
    n_rejected: int                            # perturbations that failed canonicalization


def _perturb_params(
    params: Dict[str, Any],
    param_name: str,
    delta_pct: float = 0.10,
) -> List[Dict[str, Any]]:
    """Generate perturbed copies of params for one parameter.

    Creates two variants: +delta_pct and -delta_pct of the named param.
    Integer params are perturbed by at least +/-1.

    Returns list of perturbed_params dicts.
    """
    variants = []
    val = params[param_name]

    if isinstance(val, int):
        delta = max(1, int(round(val * delta_pct)))
        for sign in [1, -1]:
            new_params = dict(params)
            new_val = val + sign * delta
            # Clamp to positive
            new_val = max(1, new_val)
            new_params[param_name] = new_val
            variants.append(new_params)
    elif isinstance(val, float):
        delta = val * delta_pct
        for sign in [1, -1]:
            new_params = dict(params)
            new_val = val + sign * delta
            # Clamp to small positive for proportional params
            new_val = max(1e-6, new_val)
            new_params[param_name] = new_val
            variants.append(new_params)

    return variants


def _signal_cache_key(config) -> tuple:
    """Cache key covering all feature-affecting config fields.

    Delegates to the shared signal_cache module.
    """
    from pmm_lab.objective.signal_cache import signal_cache_key
    return signal_cache_key(config)


def compute_sensitivity(
    params: Dict[str, Any],
    candles: np.ndarray,
    pair_rules: PairRules,
    bar_interval_seconds: int,
    reference_price: float,
    delta_pct: float = 0.10,
    objective_version: int = 1,
    objective_weights=None,
    perturb_params: Optional[List[str]] = None,
    collapse_threshold: float = 0.50,
    controller_compat: Optional[bool] = None,
    shared_signal_cache=None,
    dataset_key: str = "dev",
    canonicalize_fn: Optional[Callable] = None,
    regime_candles: Optional[np.ndarray] = None,
) -> SensitivityReport:
    """Compute sensitivity of objective to parameter perturbations.

    For each param in perturb_params:
    1. Create +delta_pct and -delta_pct variants
    2. Canonicalize each variant
    3. Run simulation and compute objective
    4. Compare to baseline score

    Parameters
    ----------
    params : Dict
        Raw params dict (as stored in TrialRecord or trial.params).
    candles : np.ndarray
        Full candle dataset.
    pair_rules : PairRules
        Exchange rules.
    bar_interval_seconds : int
        Candle interval in seconds.
    reference_price : float
        For canonicalization.
    delta_pct : float
        Perturbation magnitude (0.10 = +/-10%).
    objective_version : int
        1 or 2.
    objective_weights : optional
        Weights for the objective function.
    perturb_params : List[str], optional
        Which params to perturb. If None, uses PERTURBABLE_PARAMS.
    collapse_threshold : float
        A perturbation "collapses" if score drops by more than this fraction
        of the baseline score magnitude.

    Returns
    -------
    SensitivityReport
    """
    if perturb_params is None:
        perturb_params = PERTURBABLE_PARAMS

    _canonicalize = canonicalize_fn if canonicalize_fn is not None else canonicalize_params

    # Select objective function
    if objective_version == 2:
        from pmm_lab.objective.objective import ObjectiveWeightsV2
        _weights = objective_weights or ObjectiveWeightsV2()
        obj_fn = lambda m: objective_v2(m, _weights)
    else:
        _weights = objective_weights or ObjectiveWeights()
        obj_fn = lambda m: objective_v1(m, _weights)

    # Signal cache — reuse signals when indicator params are unchanged
    _signal_cache = {}

    def _unpack(result):
        """Normalize canonicalize return to (strategy_config, engine_config_or_None, reject_reason)."""
        if isinstance(result, tuple) and len(result) == 2:
            cfg_or_bundle, reason = result
            if cfg_or_bundle is None:
                return None, None, reason
            if isinstance(cfg_or_bundle, SimConfig):
                return cfg_or_bundle, None, None
            # Assume CandidateBundle-like with .strategy_config + .engine_config
            sc = getattr(cfg_or_bundle, "strategy_config", None)
            ec = getattr(cfg_or_bundle, "engine_config", None)
            if sc is not None and ec is not None:
                return sc, ec, None
            # Else a raw strategy config
            return cfg_or_bundle, None, None
        raise TypeError(f"Unexpected canonicalize return: {result!r}")

    def _get_or_compute_signals(cfg):
        key = _signal_cache_key(cfg)
        if key in _signal_cache:
            return _signal_cache[key]

        if shared_signal_cache is not None:
            # Config-aware probe honors EMA's regime-hashed dataset key (Stage 2 fix).
            cached = shared_signal_cache.get_for_config(
                cfg, dataset_key, regime_candles=regime_candles,
            )
            if cached is not None:
                _signal_cache[key] = cached
                return cached
            computed = shared_signal_cache.get_or_compute(
                cfg, dataset_key, candles, pair_rules,
                regime_candles=regime_candles,
            )
        else:
            from pmm_lab.objective.signal_cache import SharedSignalCache
            _tmp = SharedSignalCache()
            computed = _tmp.get_or_compute(
                cfg, dataset_key, candles, pair_rules,
                regime_candles=regime_candles,
            )

        _signal_cache[key] = computed
        # NOTE: do NOT call shared_signal_cache.put(key, dataset_key, computed)
        # here. get_or_compute already stored the entry under the *effective*
        # dataset key (e.g. "dev#regime=<hash>"). Writing again under the bare
        # dataset_key would create an alias that breaks regime isolation for EMA.
        return computed

    # Compute baseline
    baseline_config, baseline_engine, reject = _unpack(
        _canonicalize(params, pair_rules, reference_price)
    )
    if baseline_config is None:
        return SensitivityReport(
            baseline_score=REJECT_SCORE,
            perturbed_scores={},
            sign_flips=0, collapse_count=0,
            sensitivity_penalty=1.0,
            n_perturbations=0, n_rejected=0,
        )
    if controller_compat is not None:
        from dataclasses import replace
        baseline_config = replace(baseline_config, controller_compat=controller_compat)

    baseline_signals = _get_or_compute_signals(baseline_config)
    result = run_simulation(
        baseline_config, pair_rules, candles, baseline_signals,
        engine_config=baseline_engine, regime_candles=regime_candles,
    )
    initial_equity = (
        baseline_config.total_amount_quote if isinstance(baseline_config, SimConfig)
        else baseline_engine.total_amount_quote if baseline_engine is not None
        else 100.0
    )
    metrics = compute_metrics(result, initial_equity, candles, bar_interval_seconds)
    baseline_obj = obj_fn(metrics)
    baseline_score = baseline_obj.raw_score

    # Perturb each parameter
    all_perturbed_scores: Dict[str, List[float]] = {}
    sign_flips = 0
    collapse_count = 0
    n_perturbations = 0
    n_rejected = 0

    for param_name in perturb_params:
        if param_name not in params:
            continue

        variants = _perturb_params(params, param_name, delta_pct)
        scores_for_param = []

        for variant_params in variants:
            n_perturbations += 1
            var_strategy, var_engine, reject_reason = _unpack(
                _canonicalize(variant_params, pair_rules, reference_price)
            )
            config = var_strategy

            if config is None:
                n_rejected += 1
                scores_for_param.append(REJECT_SCORE)
                continue

            if controller_compat is not None:
                from dataclasses import replace
                config = replace(config, controller_compat=controller_compat)

            variant_signals = _get_or_compute_signals(config)
            r = run_simulation(
                config, pair_rules, candles, variant_signals,
                engine_config=var_engine, regime_candles=regime_candles,
            )
            v_equity = (
                config.total_amount_quote if isinstance(config, SimConfig)
                else var_engine.total_amount_quote if var_engine is not None
                else 100.0
            )
            m = compute_metrics(r, v_equity, candles, bar_interval_seconds)
            obj = obj_fn(m)
            score = obj.raw_score

            scores_for_param.append(score)

            # Check sign flip
            if baseline_score > 0 and score < 0:
                sign_flips += 1
            elif baseline_score < 0 and score > 0:
                sign_flips += 1

            # Check collapse
            if abs(baseline_score) > 1e-6:
                drop_frac = (baseline_score - score) / abs(baseline_score)
                if drop_frac > collapse_threshold:
                    collapse_count += 1

        all_perturbed_scores[param_name] = scores_for_param

    # Compute penalty
    # Penalty = fraction of perturbations that flipped or collapsed
    n_valid = n_perturbations - n_rejected
    if n_valid > 0:
        sensitivity_penalty = (sign_flips + collapse_count) / n_valid
    else:
        sensitivity_penalty = 1.0  # all rejected = maximally fragile

    return SensitivityReport(
        baseline_score=baseline_score,
        perturbed_scores=all_perturbed_scores,
        sign_flips=sign_flips,
        collapse_count=collapse_count,
        sensitivity_penalty=sensitivity_penalty,
        n_perturbations=n_perturbations,
        n_rejected=n_rejected,
    )
