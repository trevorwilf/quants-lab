# Live incumbent ladder configs

Live `range_inventory_ladder` controller YAMLs used as walk-forward
benchmarks by `notebooks/range_ladder/range_ladder_optuna_walkforward.ipynb`
(`INCUMBENT_TRIAL=True`).

Naming convention: `<connector>__<TRADING-PAIR>.yml`
(e.g. `nonkyc__DASH-USDT.yml`, `kraken__XMR-USD.yml`). A missing file is not
an error — the notebook logs "no incumbent" and proceeds.

Drop live controller YAMLs here VERBATIM: the loader
(`pmm_lab.export.hb_yaml_range_ladder.load_range_ladder_incumbent`) accepts
the live format's comma-separated ladder fields
(`buy_prices: 328,324,321,...`) as well as YAML lists, and only reads the
four ladder fields — all other live fields (fund ledger, refresh,
diagnostics) are carried through untouched in `raw`.

Current inventory (copied from the live controller configs, 2026-07):

| file | note |
|---|---|
| `nonkyc__XMR-USDT.yml` | live 7-buy/9-sell ladder, sell-only seed |
| `nonkyc__DASH-USDT.yml` | optimized plateau band + shape weights |
| `nonkyc__SUN-USDT.yml` | small experiment, front-loaded buys |
| `nonkyc__ZANO-USDT.yml` | probe only (thin book) |
| `kraken__XMR-USD.yml` | validated Kraken band ACTIVATED here (the file as copied had a stale NonKYC ladder pasted in as the active block — see ALTERNATE C inside) |

What the notebook does with an incumbent:
1. Evaluates the LITERAL ladder through the same fold machinery and prints
   it as a benchmark row (raw prices are not in the generative search space,
   so it cannot be an Optuna trial).
2. Enqueues a least-squares generative approximation
   (`pmm_lab.strategies.range_ladder_gen.fit_generative_to_ladder`) as an
   early trial so the optimizer starts near the incumbent.
