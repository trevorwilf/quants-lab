# Full Parity — Section 3 Investigation

**Date**: 2026-04-17

## The four validation helpers

### 1. `pmm_lab/objective/holdout.py::evaluate_holdout`

`SimConfig` / `CandleSimRunner` references:

| Line | Reference | Kind |
|---|---|---|
| 20  | `from pmm_lab.sim.executor_model import SimConfig, SimResult` | import |
| 21  | `from pmm_lab.sim.runner import CandleSimRunner` | import |
| 71  | `config: SimConfig` (HoldoutCandidateResult.config) | dataclass type hint |
| 100 | `candidate_configs: List[Tuple[SimConfig, float]]` | signature type hint |
| 159 | `runner = CandleSimRunner(config, pair_rules)` | **runtime instantiation** |
| 167 | `signals = runner.compute_signals(full_candles)` | signals via runner |
| 172 | `result = runner.run_with_signals(...)` | **simulation** |
| 195 | `result = runner.run(holdout_candles)` | **simulation (cold-start)** |
| 205–218 | `run_stress_tests(...)` | delegated — see stress.py |

**Change plan**:
- Type hints → `Any`.
- Accept optional `engine_config` and `regime_candles` kwargs.
- Route signal computation through `shared_signal_cache.get_or_compute`.
- Replace `CandleSimRunner(...).run_with_signals(...)` / `.run(...)` with `run_simulation(config, pair_rules, candles, signals, engine_config=..., sim_start_idx=..., regime_candles=...)`.
- Pass `regime_candles` through to `run_stress_tests`.

### 2. `pmm_lab/objective/recent_window.py::evaluate_recent_window`

| Line | Reference | Kind |
|---|---|---|
| 16  | `from pmm_lab.sim.executor_model import SimConfig, SimResult` | import |
| 17  | `from pmm_lab.sim.runner import CandleSimRunner` | import |
| 45  | `config: SimConfig` | signature type hint |
| 139 | `runner = CandleSimRunner(config, pair_rules)` | **runtime instantiation** |
| 144 | `shared_signal_cache.get_or_compute(...)` | already cache-routed |
| 146 | `signals = runner.compute_signals(full_candles)` | signals via runner |
| 147 | `result = runner.run_with_signals(...)` | **simulation** |
| 173 | `run_stress_tests(...)` | delegated |

**Change plan**: same as holdout.

### 3. `pmm_lab/optuna/sensitivity.py::compute_sensitivity`

| Line | Reference | Kind |
|---|---|---|
| 19  | `from pmm_lab.optuna.canonicalizer import canonicalize_params` | import |
| 20  | `from pmm_lab.sim.runner import CandleSimRunner` | import |
| 171 | `CandleSimRunner(cfg, pair_rules).compute_signals(candles)` | signals via runner |
| 178 | `canonicalize_params(params, pair_rules, reference_price)` | PMM-only canonicalizer |
| 192 | `runner = CandleSimRunner(baseline_config, pair_rules)` | **runtime instantiation** |
| 193 | `runner.run_with_signals(candles, baseline_signals)` | **simulation** |
| 214 | `canonicalize_params(variant_params, ...)` | PMM-only canonicalizer |
| 226 | `CandleSimRunner(config, pair_rules).run_with_signals(...)` | **runtime** |

**Change plan**: this one has additional coupling through the PMM-specific `canonicalize_params`. Generalize via a `canonicalizer` callable kwarg (default `pmm_lab.optuna.canonicalizer.canonicalize_params` for backward compat). For MR the caller passes `canonicalize_mr_bb_rsi_params`; for EMA `canonicalize_ema_regime_hold_params`. The canonicalizer kwarg returns either `SimConfig` (PMM) or `CandidateBundle` (MR/EMA), so the sensitivity loop must detect the bundle type and extract `strategy_config` + `engine_config`.

### 4. `pmm_lab/objective/stress_selection.py::select_best_stressed_candidate`

| Line | Reference | Kind |
|---|---|---|
| 14  | `from pmm_lab.sim.executor_model import SimConfig` | import |
| 15  | `from pmm_lab.sim.runner import CandleSimRunner` | import |
| 151 | `CandleSimRunner(config, pair_rules).compute_signals(candles)` | signals via runner |
| 156 | `runner = CandleSimRunner(config, pair_rules)` | **runtime instantiation** |
| 157 | `runner.run_with_signals(candles, signals)` | **simulation** |
| 170 | `apply_scenario(config, pair_rules, scenario)` | — |
| 171 | `sc_runner = CandleSimRunner(stressed_config, stressed_rules)` | **stressed simulation** |

**Change plan**: `apply_scenario` is PMM-specific. But this helper is ALSO PMM-specific in practice. Per the user's sweep-notebook architecture, MR/EMA sweeps use their own stress modules (`stress_mean_reversion_bb_rsi.py`, `stress_ema_regime_hold.py`) and don't call `select_best_stressed_candidate` directly. However, the PMM sweep notebook (5.A substitution table) shows MR/EMA notebooks using `select_best_stressed_candidate` for cross-scenario aggregation of Phase-2 results. To support both, we add a `stress_runner_fn` kwarg: a callable that takes `(candidate, candles, pair_rules, scenarios, ...)` and returns a `StressReport`. Default: the existing PMM-based path.

## Runner-dispatch helper

`pmm_lab/sim/runner_dispatch.py` — new file. One function:

```python
def run_simulation(config, pair_rules, candles, precomputed_signals,
                   engine_config=None, sim_start_idx=None,
                   bar_index_offset=0, regime_candles=None) -> SimResult:
    """Dispatch simulation by config type."""
```

- `SimConfig`: use `CandleSimRunner(config, pair_rules).run_with_signals(...)`; `engine_config` is ignored (SimConfig has all fields).
- `MeanReversionBBRSIStrategyConfig`: require `engine_config`; `SimEngine(engine_config, pair_rules).run_with_signals(candles, MeanReversionBBRSIStrategy(config), signals, sim_start_idx, bar_index_offset)`.
- `EMARegimeHoldStrategyConfig`: require `engine_config`; regime_candles must already be on the config (canonicalizer attaches it); instantiate strategy and engine, run.

Also a convenience:

```python
def run_simulation_cold(config, pair_rules, candles,
                         engine_config=None, regime_candles=None) -> SimResult:
    """Cold-start (no precomputed signals)."""
```

## Summary

- Add `pmm_lab/sim/runner_dispatch.py` with `run_simulation` and `run_simulation_cold`.
- Generalize all four helpers: type hints → `Any`; accept `engine_config=None`, `regime_candles=None`; route through `runner_dispatch` and `shared_signal_cache`.
- `compute_sensitivity` additionally gets a `canonicalizer` callable kwarg.
- `select_best_stressed_candidate` gets a `stress_runner_fn` kwarg (default = PMM path).
- All existing tests must continue to pass.
