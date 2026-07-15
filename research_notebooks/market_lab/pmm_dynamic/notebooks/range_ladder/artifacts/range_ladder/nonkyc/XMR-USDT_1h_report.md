# range_ladder report — nonkyc XMR-USDT 1h (generative)

- Generated: 2026-07-07T16:30:35.460904+00:00
- Study: `nonkyc_XMR-USDT_1h_range_ladder_v2_strict_median_ann`
- Dataset: 27858 bars (native), hash `af7118f9c5a724cb...`
- Fold plan: train 980.8d / test 60.0d x 3 folds
- Fees: maker 0.002 (nonkyc), dead-zone floor 0.0080
- Fund: 1000.0 quote, quote_frac 0.5
- Gate policy: `{'mode': 'strict', 'endinv_gate_pct': 75.0, 'endinv_penalty': 20.0, 'cons_floor_ann_pct': 0.0, 'max_dd_pct': 60.0, 'min_trades_per_month': 6.0, 'min_side_fills_per_fold': 3, 'min_rung_touches_train': 8, 'touch_lookback_days': 270.0}`
- Objective mode: `median_ann`
- Deploy anchor: 326.11 (last close 328.28, divergence 0.66%)

## Trials

| total | complete | pruned | failed |
|---|---|---|---|
| 1000 | 1 | 999 | 0 |

## Top 10

| trial | objective | pnl_med % | endinv_med % | cons_med | trades_mo_med | min_rung_touches | gate viol |
|---|---|---|---|---|---|---|---|
| 278 | -44.71 | -3.86 | 65.4 | -34.0 | 31.4 | 27 | 1 |

## Incumbent benchmark (same policy + objective)

Objective: **59.96**, gate violations 1 (reported, never pruned)

| fold | score | ann % | cons ann % | endinv % | maxdd % | fills | trades/mo |
|---|---|---|---|---|---|---|---|
| 0 | 65.4 | 65.4 | 56.2 | 2.4 | 37.4 | 96b/125s | 112.0 |
| 1 | 54.5 | 54.5 | 50.0 | 4.9 | 4.7 | 67b/65s | 66.9 |
| 2 | 76.6 | 76.6 | 73.4 | 98.6 | 11.8 | 64b/68s | 66.9 |

## Best trial (#278, objective -44.71)

| fold | score | ann % | cons ann % | endinv % | maxdd % | fills | trades/mo |
|---|---|---|---|---|---|---|---|
| 0 | -66.0 | -66.0 | -69.1 | 65.4 | 24.0 | 12b/15s | 13.7 |
| 1 | 98.4 | 98.4 | 100.9 | 1.5 | 8.2 | 24b/41s | 32.9 |
| 2 | -23.5 | -23.5 | -34.0 | 97.9 | 22.8 | 33b/29s | 31.4 |

### Params

```json
{
  "n_buy": 3,
  "n_sell": 3,
  "buy_near_pct": 0.01166295069343381,
  "buy_far_pct": 0.06499374835258814,
  "sell_near_pct": 0.007392205115059191,
  "sell_far_pct": 0.04411306098972532,
  "buy_gamma": 0.6836825406305141,
  "sell_gamma": 1.7067384998833548,
  "k_buy": 3.4899032509940504,
  "k_sell": 3.052959135992812
}
```

### Per-rung train touches (per fold)

- fold 0: buys [107, 94, 102], sells [45, 46, 27]
- fold 1: buys [229, 280, 381], sells [125, 90, 81]
- fold 2: buys [150, 197, 123], sells [197, 179, 153]

### Per-rung fills (per fold)

- fold 0: buys [6, 4, 2], sells [5, 6, 4]
- fold 1: buys [21, 3, 0], sells [20, 15, 6]
- fold 2: buys [14, 11, 8], sells [13, 13, 3]

## Export

Export: `artifacts/range_ladder/nonkyc/XMR-USDT_1h_screening_best.yml` (validated: True)

### Exported ladder (rebuilt at the deploy anchor)

```json
{
  "deploy_anchor": 326.11,
  "buys": [
    322.3,
    311.47,
    304.91
  ],
  "sells": [
    328.53,
    332.19,
    340.5
  ],
  "buy_weights": [
    1.0,
    0.17465343753569518,
    0.1
  ],
  "sell_weights": [
    1.0,
    0.21729930979617945,
    0.1
  ]
}
```

## Phase A caveats

- No proceeds recycling; static per-rung quantities (Phase B).
- `executor_refresh_time` not modeled (Phase B event-level sim).
- Conservative (stress) scores gate only in accumulate_ok mode; otherwise informational.