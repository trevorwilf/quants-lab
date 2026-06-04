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

## First run (study `5f7a4857_20260603`, pre-SIP — objectives negative by design)

12 finalists, 7 neighbours, 8 fork-workers; contexts built in ~40 min, sweep
~10 min. All finalists cluster ~-0.87 dev, dropping to ~-1.05 under ±10%
perturbation. Most stable: trial 4816 (dev→nb drop 0.142, fold var 0.019);
best dev: 4979 (-0.869). Bottom 5 (4669/1661/3851/4893/3847) are fragile
(neighbours collapse to -1.5…-1.9, robust=no). Report:
`artifacts/optuna/topn_robustness.{md,json}`.
