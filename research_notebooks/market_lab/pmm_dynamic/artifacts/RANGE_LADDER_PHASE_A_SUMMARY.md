# RANGE_LADDER Phase A — implementation summary

Date: 2026-07-06. Registers `range_ladder` (the live `range_inventory_ladder`
controller) as a first-class pmm_lab strategy with a generative Optuna
walk-forward pipeline, per `market_lab_RANGE_LADDER_PHASE_A_claude_code_prompt.md`
plus the Kraken addendum.

## Files created

| Area | Files |
|---|---|
| Strategy | `pmm_lab/strategies/range_ladder.py` (RangeLadderConfig + literal escape hatch + dispatch window-runner), `pmm_lab/strategies/range_ladder_gen.py` (build_rungs / validate_rungs / incumbent least-squares fit — pure, no I/O) |
| Fill kernel | `pmm_lab/features/_numba_range_ladder.py` — exact port of the validated ladder_lab `_sim_kernel` (v3 cooldown-in-bars semantics) + pure-Python reference + `run_ladder_sim` wrapper + `quarter_split`; extended with a per-bar base track for SimResult position history |
| Optuna | `pmm_lab/optuna/search_space_range_ladder.py` (10 generative params, log-scaled offsets), `canonicalizer_range_ladder.py` (fee-parametric §0 constraints), `objective_wrapper_range_ladder.py` (§3 walk-forward: train-only median-3 anchor, endinv/two-sided gates, majority-violation prune, winsorized median−0.5·MAD) |
| Stress | `pmm_lab/objective/stress_range_ladder.py` (max_fills=1, cooldown≥1, slip=max(0.001, spread/2), body_only option — same kernel, different dials) |
| Export | `pmm_lab/export/hb_yaml_range_ladder.py` (deploy-anchor export, weights sum exactly 100.0, frozen Phase A timing) + `range_inventory_ladder` mirror validator in `validate_export.py` |
| Data | `pmm_lab/data/coverage.py` (`audit_pair`, UTC-aligned 5m→1h `resample_candles`, `preflight_pair` abort <150d / >5% gaps) |
| Notebook | `notebooks/range_ladder/range_ladder_optuna_walkforward.ipynb` (papermill `parameters` cell; connector-parametric nonkyc/kraken; incumbent benchmark + enqueue; export + md report) |
| Scripts | `scripts/generate_range_ladder_fixtures.py`, `scripts/print_kraken_metadata.py` |
| Fixtures | `fixtures/numba_parity/rl_{small,medium,large}_{cfg0..cfg3}.{npz,json}` — 12 frozen kernel-parity fixtures (asymmetric 3×9, k<0/k>0 tilts, cash-starved qf=0.05, stress dials) |
| Incumbents | `configs/incumbents/nonkyc__DASH-USDT.yml`, `nonkyc__SUN-USDT.yml` (seeded from prompt rungs; fund fields are placeholders), `configs/incumbents/README.md` |

## Files modified

- `configs/exchange_rules.yaml` — **nonkyc maker fee 0.0010 → 0.0020** (verified
  from live trades; buy collateral = notional+fee), new nonkyc pair blocks
  DASH/SUN/ZANO-USDT (`# TODO verify against /market/info`), new **kraken**
  connector block (tiered fee schedule, base tier 0.0025/0.0040) with
  XMR-USDT + XMR-USD pair rules from `quants_lab.symbol_metadata`.
- Dispatch registrations: `strategies/factory.py`, `strategies/__init__.py`,
  `optuna/objective_wrapper.py`, `sim/runner_dispatch.py`,
  `objective/walkforward_dispatch.py`, `objective/signal_cache.py`
  (signal-less passthrough branch, key = `("range_ladder",)`).
- `optuna/study.py` + `optuna/notebook_dispatch.py` — optional `pruner`
  passthrough (default MedianPruner unchanged; the ladder notebook passes
  HyperbandPruner).
- Tests updated: `test_exchange_rules.py` (fee fix + kraken block tests),
  `test_walkforward_dispatch.py`, `test_signal_cache_multi_strategy.py`,
  `test_objective_wrapper_dispatch_regression.py`.

## Kraken addendum

- Metadata source: **MongoDB `quants_lab.symbol_metadata`** (source AssetPairs,
  updated 2026-07): tick 0.01, quantity_step 1e-8, costmin 0.5, ordermin
  0.015 XMR, maker 0.0025 / taker 0.0040 — cross-checked live against
  `https://api.kraken.com/0/public/AssetPairs` (fees_maker/fees schedules
  match; the yaml carries the full 30d-volume tier table). No placeholders
  were needed. `scripts/print_kraken_metadata.py` re-prints the values.
- Constraints are fee-parametric from exchange rules (never hardcoded):
  dead-zone floor nonkyc 0.008 vs kraken 0.010 (unit-tested); min-notional
  feasibility uses `max(min_notional_quote, min_order_size_base × ref_price)`
  → ~6 USD on kraken XMR (ordermin binds) vs 1 USDT on nonkyc.
- Incumbent machinery degrades gracefully (no kraken YAML → "no incumbent"
  log, study proceeds) and a USD-quoted export (`XMR-USD`) is unit-tested.

## Test results

- New/extended range_ladder + addendum tests: **197 passed** (constraint
  pass/fail pairs, kernel semantics on hand-built candles, 12-fixture
  bit-exact numba↔reference parity, train-only anchor leakage, gate/prune
  logic, winsorized math, export/validator round-trips incl. kraken XMR-USD,
  connector-parametric objective smoke, coverage/resample/preflight).
- Full suite (`python -m pytest tests/`): **1676 passed, 59 skipped,
  1 failed in 10:27** (Python 3.12, live Mongo reachable). The single
  failure is `tests/integration/test_mongo_live.py::test_live_audit_passes_strict`
  — PRE-EXISTING/environmental: it strict-audits the FIRST 500 bars of live
  nonkyc BTC-USDT 5m (May 2023), which are 72.6% heuristic forward-fills in
  the lake. Nothing in this change touches the loader, validator, or that
  test; it fails identically without the Phase A diff.

## Notebook smoke runs (real lake data)

`nonkyc XMR-USDT 1h` (native, 27,852 bars, 0.00% gaps): preflight, fold plan
(train 980.5d / test 60d × 3), incumbent-absent path, study, and the
zero-completed-trial guard all exercised end-to-end. With 100 trials,
**every trial was pruned** — an honest market answer, not a bug:

- 12% canonicalizer rejections (adjacent-gap fee floor, far<near) — expected
  under random sampling.
- The rest failed the **endinv > 75% gate in 2 of 3 folds**: the last-180d
  XMR test windows fell −22.7% and −16.9%, and with static per-rung
  quantities + no proceeds recycling the ladder accumulates into declines
  (fold endinv 97–99%). Only 2 of 211 observed folds failed two-sidedness.

Note: the predecessor ladder_lab pipeline carried XMR on an `accumulate_ok`
whitelist that waived exactly this gate. Phase A gates unconditionally per
spec — if XMR accumulation is acceptable, that is a deliberate operator
decision for Phase B/C, not a default.

## Known issues / data gaps

1. **DASH-USDT and SUN-USDT have ZERO candles in the lake** (any connector,
   any name variant, checked 2026-07-06). The §5 preflight aborts for them
   by design. Backfill via the ingester (MEXC proxy, e.g.
   `notebooks/mongo_tools/candle_backfill_v6.ipynb`) before running their
   studies. ZANO-USDT (nonkyc 5m+1h, ~3y) and XMR-USDT (nonkyc + kraken)
   are ready.
2. **kraken XMR-USD** is thin in the lake (~135k docs across intervals,
   short 1h span) — the preflight gate correctly rejects it until
   backfilled; the gate was not weakened (addendum §5).
3. nonkyc `symbol_metadata` docs carry priceDecimals-derived ticks (1e-8)
   and null fees, so DASH/SUN/ZANO ticks in `exchange_rules.yaml` are from
   live prices with `# TODO verify against /market/info` (DASH 0.01,
   SUN 0.0000001, ZANO 0.001; amount steps are conservative estimates).
   The seeded DASH incumbent's live prices have 4-dp granularity (e.g.
   31.3395), suggesting DASH's true tick is finer than 0.01 — verify before
   trusting tick-quantized exports for DASH.
4. Incumbent fund fields in `configs/incumbents/*.yml` are placeholders —
   copy the actual live controller YAMLs from the Trading Pod over the seeds
   (same filenames) to benchmark with real fund values (rungs/weights are
   exact from the prompt).
5. Phase A accepted bias (by spec): no proceeds recycling, static rung
   quantities, `executor_refresh_time` not modeled — Phase B (event-level
   sim) owns these.

## Notebook invocation (the four nonkyc pairs + kraken)

From `notebooks/range_ladder/` (or via papermill from anywhere — the
bootstrap cell discovers the subproject root and `.env`):

```bash
# nonkyc pairs (DASH/SUN abort in preflight until backfilled)
papermill range_ladder_optuna_walkforward.ipynb out_xmr.ipynb  -p CONNECTOR nonkyc -p TRADING_PAIR XMR-USDT  -p N_TRIALS 400
papermill range_ladder_optuna_walkforward.ipynb out_dash.ipynb -p CONNECTOR nonkyc -p TRADING_PAIR DASH-USDT -p N_TRIALS 400
papermill range_ladder_optuna_walkforward.ipynb out_sun.ipynb  -p CONNECTOR nonkyc -p TRADING_PAIR SUN-USDT  -p N_TRIALS 400
papermill range_ladder_optuna_walkforward.ipynb out_zano.ipynb -p CONNECTOR nonkyc -p TRADING_PAIR ZANO-USDT -p N_TRIALS 400

# kraken (addendum): XMR-USDT ready; XMR-USD gated until backfilled
papermill range_ladder_optuna_walkforward.ipynb out_kxmr.ipynb -p CONNECTOR kraken -p TRADING_PAIR XMR-USDT -p N_TRIALS 400
```

Key parameters: `FUND_USD` (default 1000, drives feasibility + export fund
placeholders), `INCUMBENT_TRIAL` (benchmark + warm-start when a YAML exists
under `configs/incumbents/`), `STRESS_SPREAD_PCT` (measured spread → stress
slip), `N_JOBS>1` requires PostgreSQL `OPTUNA_STORAGE`.

Artifacts land at `artifacts/range_ladder/<connector>/<PAIR>_<interval>_screening_best.yml`
(+ `_report.md`), validated by the `range_inventory_ladder` mirror validator
before the notebook finishes.

## Out of scope (per prompt §7)

No event-refresh / proceeds-recycling sim, no timing-parameter tuning, no
new exchange fetchers, no live-controller changes, no top-N finalist sweep
(trial user_attrs carry per-fold detail + last-fold rungs so Phase C can
rank finalists without re-running).
