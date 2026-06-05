# Top-N robustness + holdout sweep (post-hoc finalist evaluation)

`scripts/topn_robustness_sweep.py` — operator tool that loads a FINISHED
walk-forward Optuna study and evaluates the top-N finalists (default 12) so you
can pick a deployable config from a side-by-side comparison instead of trusting
the single best trial. Mirrors the market_lab `validate_finalist` pattern.

Per finalist it runs:
* a **neighbour / robustness sweep** — re-scores ``--neighbours`` (default 7)
  parameter sets perturbed ±10% (`_neighbour_param_sets`) on the validation
  folds (`_run_validation_folds`, objective_minimal), surfacing whether the dev
  score sits on a robust plateau or a fragile spike; and
* a **final-holdout evaluation** — scores the finalist once on the reserved
  holdout window (`build_holdout_context` + `_run_fold_backtest_objective`).

Ranks finalists by a combined score (mean of dev-median, neighbour-mean,
holdout), names the winner (highest combined passing both the robustness AND
no-holdout-collapse gates; else highest combined, flagged), and writes a
markdown comparison table + per-finalist detail (+ JSON sidecar). All metrics
are shown so the operator can override the auto-pick.

**Parallelism (Linux/WSL2):** the validation + holdout fold contexts are built
ONCE in the parent; the worker processes are **forked** so they inherit the
contexts copy-on-write — no per-worker rebuild, no pickling the non-picklable
suppliers. `--jobs` workers each score one finalist's sweep + holdout.

**Modes:** `--dry-run` (rank + render from stored trial attrs, no backtests —
plumbing check); `--from-json <path>` (regenerate the markdown from a prior
run's JSON with the current verdict logic — no backtests).

## GOTCHA — the holdout needs a holdout-scope matrix

The study builds/verifies only the **validation**-scope scan-matrix. The holdout
backtest runs against the **holdout** window, whose matrix store does not exist /
is unverified → the backtester's parity-proof gate refuses it
(`runtime_mode='vectorized' requires a parity-proof marker`). With
`final_holdout_months: 5` the window is too large for the legacy scanner, so the
tool records the holdout error per finalist and falls back to a combined score of
**dev-median + neighbour-mean** (the Holdout / HO-collapse columns show `—`, with
an explanatory note in the report). To get the out-of-sample column, build +
verify the holdout-scope matrix first, then re-run (or `--from-json` won't add it
— a real re-run is needed).

The neighbour-robustness pass is independent of the holdout and works as-is — it
already separates the stable plateau (small dev→neighbour drop, low fold
variance) from the fragile spikes.

## PnL + quant metrics (the report now leads with PnL)

`_agg_fold_metrics` pulls each finalist's per-fold metrics straight from the
trial's `user_attrs["fold_metrics"]` (no re-run): **net_return_pct** (mean of
folds), **mtm_max_drawdown_pct** (worst fold), worst_day_loss, win_rate,
avg/median_trade_return_pct, n_trades (sum), fill_rate, frac_trades_ge_min_profit,
plus per-fold detail. KEY READING NOTE surfaced in the report: the v2 **objective
is log-return minus edge/turnover/fill penalties → it is negative even when PnL is
positive**. On study `5f7a4857` the top-12 are all PROFITABLE (~+15–17% net
return, 58–67% win rate, ~2–3% max DD, 73–95 trades) despite ~−0.87 objectives.
The comparison table leads with Net ret% / Max DD% / Win% / Trades / Avg trade%,
then Objective / FoldVar / NbObj-min / Robust? / Holdout net% / Combined; per
finalist a full PnL + objective + robustness + holdout + params block.

## Two single-best YAMLs + notebook integration

`_export_yaml` writes `wr.apply_trial_params(base_cfg, params)` (gap/ratio →
actual-strategy fields, optuna block stripped) for BOTH the **robustness winner**
(combined-score #1 passing the gates) and the **study #1 by objective** (★ in the
table) — `<out>_winner.yml` / `<out>_study_best.yml`. `--from-json` regenerates
the markdown (+ YAMLs) from a prior run's JSON with the current verdict logic.

**Runner flag:** `run_walkforward_study(..., skip_best_trial_report=True)` skips
ONLY the slow internal single-best neighbour sweep (it re-runs folds in FULL
artifact mode → DQ not cached → was the ~hours hang) while keeping the cheap
ranking / best_params / clustering / promotion_evidence. The notebook passes it.

**Notebook (`notebooks/10_optuna_walkforward.ipynb`):** cell 4 (the study) passes
`skip_best_trial_report=True`; two new cells after the timing cell — a markdown
header + a code cell that runs `scripts/topn_robustness_sweep.py` **as a
subprocess** (fork-parallel is unsafe inside a Jupyter kernel — see the
parity-speedup note) against `resolved.path` (the resolved config the study ran),
streams progress, renders the markdown inline (`IPython.display.Markdown`), and
lists the exported YAMLs. Knobs `TOP_N` / `NEIGHBOURS` / `JOBS` / `STUDY_NAME`
(None → auto-detect the latest study).

## First run (study `5f7a4857_20260603`, pre-SIP — objectives negative by design)

12 finalists, 7 neighbours, 8 fork-workers; contexts built in ~40 min, sweep
~10 min. All finalists cluster ~-0.87 dev, dropping to ~-1.05 under ±10%
perturbation. Most stable: trial 4816 (dev→nb drop 0.142, fold var 0.019);
best dev: 4979 (-0.869). Bottom 5 (4669/1661/3851/4893/3847) are fragile
(neighbours collapse to -1.5…-1.9, robust=no). Report:
`artifacts/optuna/topn_robustness.{md,json}`.
