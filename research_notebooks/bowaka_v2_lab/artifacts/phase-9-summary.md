# Phase 9 summary — Optuna and Bayesian optimization rebuild

**Branch:** `phase-9-realism-optuna-rebuild` (off `dev`)
**Audit refs:** P0-013, §11 Phase 9, Ticket 11.
**Status:** complete, merged to `dev`.

## What shipped

- **Versioned search space** (`optuna/search_space.py`) — `SEARCH_SPACE_VERSION`
  constant; bounds cover every live value in the frozen contract. Covers signal
  gates, sizing, risk, execution, and exit parameters; overridable via
  `cfg.optuna.search_space_overrides`. **P0-013 fix:** `rvol_so_far_min`'s lower
  bound was `1.0` — outside the live IEX value `0.7`, so the optimizer could
  never reproduce live; new bound `(0.3, 3.0)`. A parametrized test asserts
  every numeric bound brackets its live contract value.
- **Realistic objective** (`optuna/objective.py`) — primary = net return after
  realistic costs; penalties = daily mark-to-market max drawdown (from Phase 8
  `report.json` daily-equity curve, NOT the closed-trade curve), CVaR/worst-day,
  low-trade-count, missing-quote, missing-coverage, turnover, concentration,
  fill-rate; plus a fold-variance stability penalty.
- **Preflight** (`optuna/preflight.py`) — study-start prerequisite checks: refuse
  to optimize when DQ checks fail, quote coverage is below threshold, or
  `simulation.mode == smoke_fixture` without `--allow-smoke-optimization`.
- **Final holdout** (`optuna/holdout.py`) — the holdout fold is excluded from
  objective evaluation and scored once via `optuna --final-holdout`.
- **Study metadata** — `dataset_hash`, `lab_config_hash`, `code_hash` (git HEAD),
  `seed`, sampler/pruner config, fold definitions, `SEARCH_SPACE_VERSION`,
  `simulation.mode`, `feed` recorded in `study.user_attrs` + results JSON.
- **Best-result reporting** — fold-by-fold metrics, 5-neighbor parameter
  robustness, stability rank.

## Files

Code: `optuna/search_space.py`, `optuna/objective.py`,
`optuna/walkforward_runner.py`, `optuna/preflight.py` (new),
`optuna/holdout.py` (new), `cli.py`, `devtools/wf_lake.py` (new test helper).
Tests: 9 added + `tests/fixtures/search_space_v2.json`; 4 existing optuna tests
updated for the new search space / objective.

**Result:** 634 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| Optuna refuses to start without realism prerequisites | PASS |
| Search bounds cover every live contract value | PASS |
| Final holdout untouched until the explicit `--final-holdout` step | PASS |
| Best trial includes fold-by-fold metrics + robustness summary | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- Excluded from the search space (documented in `search_space.py`):
  `price_chase_gate` bounds + `halt_gate.block_on_recent_luld_pause` (no live
  order book / LULD feed); `scanner.symbol_cooldown_minutes` (sub-minute
  re-entry unresolvable at 1-minute bars); `risk.adv_tier_caps` (nested ordered
  list, not a scalar); `volume_curve.bucket_edges` (data-prep, not a strategy
  variable).
