# Live incumbent ladder configs

Live `range_inventory_ladder` controller YAMLs used as walk-forward
benchmarks by `notebooks/range_ladder/range_ladder_optuna_walkforward.ipynb`
(`INCUMBENT_TRIAL=True`).

Naming convention: `<connector>__<TRADING-PAIR>.yml`
(e.g. `nonkyc__DASH-USDT.yml`). A missing file is not an error — the
notebook logs "no incumbent" and proceeds (Kraken has no live ladders yet).

The DASH and SUN files were seeded from the rung/weight values in the Phase A
prompt; their fund fields are placeholders. To benchmark XMR-USDT / ZANO-USDT
(or refresh DASH/SUN), copy the actual live controller YAMLs from the
Trading Pod here under the same names.

What the notebook does with an incumbent:
1. Evaluates the LITERAL ladder through the same fold machinery and prints
   it as a benchmark row (raw prices are not in the generative search space,
   so it cannot be an Optuna trial).
2. Enqueues a least-squares generative approximation
   (`pmm_lab.strategies.range_ladder_gen.fit_generative_to_ladder`) as an
   early trial so the optimizer starts near the incumbent.
