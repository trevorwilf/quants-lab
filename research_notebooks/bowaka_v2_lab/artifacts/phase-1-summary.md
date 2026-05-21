# Phase 1 summary — Config schema parity with actual Bowaka v2

**Branch:** `phase-1-realism-config-parity` (off `dev`)
**Audit refs:** P0-001, P0-002, §11 Phase 1, Tickets 1 & 2.
**Status:** complete, merged to `dev`.

## What shipped

- **`SignalsConfig`** — expanded with all 16 live signal-gate thresholds
  (`Optional[float]`, None = gate disabled). `BowakaV2Config` gained a
  cross-mode validator: `current_code_parity` / `intended_realism` (not
  `allow_research_relaxed`) require every live gate to be set.
- **`SizingConfig`** — replaced with the live schema; `sizing_mode`
  (`equal_slice` default) + `bankroll_fixed_dollars`, `max_concurrent_positions`,
  `equal_slice_bankroll_fraction`, `target_risk_dollars`, `min_order_notional`,
  `max_per_trade_dollars`; `dollars_per_position` / `max_position_dollars` kept
  for back-compat. Equal-slice math wired through `StrategyConsumer`
  (`compute_target_notional`, `size_quantity`).
- **`AdvTierCap`** — replaced with the live schema (`max_adv_dollars`,
  `reject_if_below`, `max_position_as_adv_frac`). `adv_tier_cap()` ported
  byte-identically into `sim/risk_gates.py`; `evaluate_risk_gates` uses it.
- **`ExitsConfig`** — `stop_pct` / `target_pct` canonical with
  `stop_loss_pct` / `take_profit_pct` aliases; `time_stop` / `signal_fade`
  substructures.
- **`SessionConfig`** — live key names (`timezone`, `start`, `end`,
  `scanner_start`, `scanner_end`, `loop_interval_seconds`); legacy
  `scan_window_local_*` accepted as aliases.
- **`OptunaConfig.n_startup_trials`** — `Optional[int]` with a
  `0 <= n_startup_trials <= n_trials` validator.
- **Restored** `configs/bowaka_v2_walkforward_optuna.yml` from quarantine.
- **`configs/bowaka_v2_intended_realism.yml`** — generated from the frozen
  contract; `feed: sip`, `simulation.mode: intended_realism`, full live values.
- **`config_diff_vs_actual_bowaka_v2.yaml`** — emitted on every backtest run;
  `intended_realism` runs abort at startup on any unannotated `mismatch`.
- **`import-actual-config`** CLI — regenerates `bowaka_v2_intended_realism.yml`
  from the contract, byte-identically.

## Files

Code: `config/models.py`, `config/config_diff.py` (new),
`reference/import_config.py` (new), `reference/__init__.py`, `cli.py`,
`sim/risk_gates.py`, `sim/strategy_consumer.py`, `sim/backtester.py`.
Configs: 3 shipping configs updated; `bowaka_v2_walkforward_optuna.yml`
restored; `bowaka_v2_intended_realism.yml` new.
Tests: 8 added (`tests/parity/test_config_parity_{signals,sizing,adv_tiers}.py`,
`tests/unit/test_optuna_n_startup_trials.py`,
`tests/unit/test_realism_mode_requires_full_signals.py`,
`tests/integration/test_{all_shipping_configs_validate,config_diff_artifact,import_actual_config_roundtrip}.py`).
Phase 0 quarantine tests reconciled: `test_quarantined_excluded.py` removed;
`test_simulation_mode_required.py`, `test_walkforward_runner.py`,
`test_notebook_10_runs.py` updated for the restored config.

**Result:** 377 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| env-check passes on all shipping configs incl. restored walkforward | PASS (5/5) |
| `tests/parity/` signal / sizing / ADV parity tests pass | PASS |
| Realism-mode runs fail on unannotated parity-diff mismatch | PASS |
| `import-actual-config` round-trips byte-identical | PASS |

## Known follow-up

`bowaka_v2_research_sip.yml` is `intended_realism` mode with SIP-tuned values
that intentionally diverge from the (IEX-frozen) contract; a realism-mode
*backtest* of it would abort on `config_diff`. No test backtests it (env-check
still passes). If it is backtested in realism mode in a later phase, add a
`bowaka_v2_research_sip.parity.yml` sidecar annotating the intentional overrides.
