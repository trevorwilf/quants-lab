# CLAUDE.md — PMM Dynamic Backtester & Optimizer

## What This Project Is

This is a Bayesian optimization pipeline for the Hummingbot `pmm_dynamic` market-making controller. It backtests a PMM (Pure Market Making) strategy with dynamic MACD-based reference price shifting and NATR-based volatility-scaled spreads, then uses Optuna to find optimal parameters. The target exchange is **NonKYC.io** (maker 0.1%, taker 0.2%).

The pipeline has two backends: a pure-Python CPU backtester and a Numba CUDA GPU kernel that must produce identical results. Both feed into a shared Optuna objective function. Results export as Hummingbot V2 controller YAML configs.

## File Structure

```
pmm_dynamic/
├── pmm_dynamic_core.py                  # Shared library (ALL shared logic lives here)
├── pmm_dynamic_optimizer.py             # CPU backtester + Optuna objective factory
├── pmm_dynamic_optimizer_gpu.py         # GPU (Numba CUDA) backtester + objective factory
├── pmm_dynamic_optimizer_parity_test.py # CPU/GPU parity test suite
├── pmm_dynamic_optimize - CPU.ipynb     # Main notebook (CPU mode, also supports GPU auto-detect)
├── pmm_dynamic_optimize - GPU.ipynb     # GPU-first notebook (includes pre-opt parity gate)
└── CLAUDE.md                            # This file
```

## Module Dependency Graph

```
pmm_dynamic_core.py          ← Source of truth for ALL shared components
    ↑                ↑
    │                │
pmm_dynamic_optimizer.py     pmm_dynamic_optimizer_gpu.py
(CPU backtester)             (GPU backtester, imports CPU for fallback)
    ↑                ↑           ↑
    │                │           │
    └── Notebooks ───┘           │
                                 │
pmm_dynamic_optimizer_parity_test.py ──┘
```

**Import rule**: Shared logic (config dataclass, indicators, scoring, YAML export, validation) belongs in `pmm_dynamic_core.py`. The CPU and GPU modules import from core. The GPU module also imports the CPU backtester for fallback when no GPU is available. Never duplicate shared logic across modules.

## Key Architectural Concepts

### The Backtester State Machine

Each candle iteration follows this strict order:

1. **STEP 1** — Process exits on open positions (triple barrier: SL → TP → trailing → time limit)
2. **STEP 2** — Check fills on pending orders from previous candles
3. **STEP 3** — If signals valid AND refresh elapsed: cancel all pending, place new orders
4. **STEP 4** — Mark-to-market equity (always, even during warmup)

Orders placed at candle `i` are fillable starting at candle `i+1`. This is the latency model.

### Indicator Pipeline

```
close → EMA(fast) - EMA(slow) = MACD line
MACD line → EMA(signal) = signal line
MACD line - signal line = histogram
MACD line → rolling z-score (window = max(fast,slow,signal,natr_len) + 100) → negated
histogram → sign (+1/-1)
price_signal = 0.5 * macd_zscore + 0.5 * macdh_sign
reference_price = close * (1 + price_signal * natr/2)
spread_multiplier = natr
```

### Spot Portfolio Model

The backtester tracks `quote_balance` and `base_balance` separately (spot, not derivatives). Buy orders reserve quote on placement; sell orders reserve base. Equity = free_quote + reserved_quote + (free_base + reserved_base) × mid_price.

### Timestamp Semantics

- `timestamp_mode="open"` (default, correct for NonKYC.io): signals shift by 1 candle (no look-ahead)
- `timestamp_mode="close"`: signals use same candle (only if data timestamps are candle close times)
- `timestamp_mode="unknown"`: same as "open" with a warning

### GPU Kernel Constraints

The Numba CUDA kernel uses fixed-size local arrays:
- `_MAX_POSITIONS = 64` — max simultaneous open positions
- `_MAX_PENDING = 20` — max pending orders
- `_MAX_LEVELS = 10` — max spread levels per side

The kernel computes indicators inline (no pandas) using online EMA accumulators and a ring buffer for rolling z-score. All arithmetic is float64 for parity with CPU.

## Configuration

Both notebooks have a single configuration cell (Cell 3) that defines all parameters. No other cell should be edited for normal use. Key settings:

```python
CONNECTOR          = "nonkyc"       # Exchange connector name
TRADING_PAIR       = "BTC-USDT"     # Trading pair (hyphen format for MongoDB)
INTERVAL           = "5m"           # Candle interval
TIMESTAMP_MODE     = "open"         # Signal shift mode
VOLUME_UNITS       = "base"         # Volume column units

# Fees (NonKYC.io)
MAKER_FEE = 0.001                   # 0.1%
TAKER_FEE = 0.002                   # 0.2%

# Realism
SLIPPAGE_MAX_PCT   = 0.001          # Deterministic avg slippage per fill
FILL_RATE_PCT      = 0.05           # Order must be ≤5% of candle volume
DEPLOY_FRACTION    = 0.4            # 40% of capital per refresh cycle
MAX_OPEN_POSITIONS = 4              # Hard cap on simultaneous positions
COOLDOWN_SECONDS   = 15             # Post-close cooldown before re-quoting

N_TRIALS = 500                      # Optuna trials to run
BACKTEST_DAYS = 100                 # Historical window
```

## Data Flow

1. **MongoDB** → `load_candles()` → pandas DataFrame (timestamp, OHLCV)
2. `validate_candles()` checks monotonicity, gaps, OHLC sanity
3. `compute_macd()` + `compute_natr()` → indicator columns
4. `PMMDynamicBacktester.run()` or GPU kernel → `BacktestResult`
5. `_compute_objective()` / `compute_enhanced_objective()` → Optuna score
6. `walk_forward_evaluate()` + `stress_test_config()` → deployment gates
7. `trial_to_controller_yaml()` → Hummingbot V2 YAML config

MongoDB connection uses env vars `TRUENAS_LAN_IP`, `MONGO_ROOT_PASSWORD` or falls back to defaults in the config cell. Database is `quants_lab`, collection is `candles`.

## Running the Notebooks

### Prerequisites

```
pip install optuna pandas numpy pymongo plotly python-dotenv pyyaml
# For GPU: pip install cupy-cuda12x numba
```

### CPU Notebook

Run all cells top-to-bottom. Cell 3 (config) is the only cell to edit. The notebook auto-detects GPU availability but defaults to CPU (`FORCE_CPU = True`). Set `FORCE_CPU = False` to use GPU if available.

### GPU Notebook

Same workflow but includes a pre-optimization parity gate (Cell 8) that verifies CPU/GPU agreement on synthetic candles before committing to a full optimization run. Has two optimization cells (12 and 13) — cell 12 includes V3 timestamp/volume flags, cell 13 is legacy. Run only one.

### Parity Test

```bash
python pmm_dynamic_optimizer_parity_test.py
```

Requires GPU. Tests 5 baseline param sets, 6 auto-spread-floor configs, and 5 edge cases. Exit code 0 = all pass.

## Coding Conventions

- **Single source of truth**: All shared logic in `pmm_dynamic_core.py`. CPU and GPU modules only contain their backend-specific code.
- **Parity**: CPU and GPU must produce identical results for identical inputs. Any change to simulation logic must be made in both. Use deterministic math (avg slippage, not random).
- **Config dataclass**: `PMMDynamicConfig` holds all tunable parameters. Add new knobs here, not as loose function args.
- **Optuna integration**: `_suggest_params()` is the single parameter suggestion function imported by both backends. `_compute_objective()` is the single scoring function.
- **Naming**: `_` prefix for internal helpers. Module-level functions use snake_case. Dataclasses use PascalCase.
- **GPU kernel rules**: No Python objects, no dynamic allocation, no pandas. Float64 only. Local arrays for state. Online accumulators for statistics.
- **Testing**: Parity tests in `pmm_dynamic_optimizer_parity_test.py`. Synthetic candle generators (`generate_synthetic_candles`, `generate_low_vol_candles`, `generate_high_vol_candles`) use fixed seeds for reproducibility.

## Deployment Context

This optimizer is part of a larger Hummingbot Trading Pod stack running on TrueNAS Scale. The exported YAML goes to `/mnt/sharedrive/apps/hummingbot/hummingbot/controllers/` and is loaded by the Hummingbot V2 framework. All traffic routes through a Gluetun/NordVPN WireGuard VPN container. See the project-level system prompt for full stack architecture.

### Hummingbot Live Behavior (Must Match Simulator)

- Controller computes z-score over a **finite trailing window** (`max_records = max(periods) + 100`)
- One executor per level (not multiple positions per level over time)
- Cooldown applies only after STOP_LOSS closures (not after TP/trailing/time)
- Take-profit uses LIMIT order (maker fee, no slippage); SL/time use MARKET (taker fee)
- No spread floors or non-crossing clamps

### YAML Output Contract (Required Fields)

```yaml
id: <uuid>
controller_name: pmm_dynamic
controller_type: market_making
connector_name: nonkyc
trading_pair: BTC/USDT
candles_connector: nonkyc
candles_trading_pair: BTC/USDT
interval: 5m
macd_fast: <int>
macd_slow: <int>
macd_signal: <int>
natr_length: <int>
total_amount_quote: <float>
leverage: <int>
buy_spreads: [<float>, ...]
sell_spreads: [<float>, ...]
buy_amounts_pct: [<float>, ...]
sell_amounts_pct: [<float>, ...]
stop_loss: <float>
take_profit: <float>
time_limit: <int seconds>
take_profit_order_type: LIMIT
trailing_stop:
  activation_price: <float>
  trailing_delta: <float>
executor_refresh_time: <int seconds>
cooldown_time: <int seconds>
```

## Stop-Ship Conditions

Do NOT trust or deploy optimized parameters if:
- Default config (refresh=300s, candle=5m) produces 0 trades (BUG-0 not fixed)
- CPU/GPU parity test fails
- Equity curve shows >5% single-candle drops on low-vol data (BUG-2 not fixed)
- Walk-forward validation fails (median test Sharpe < 0.5 or < 3/5 windows profitable)
- Stress tests flip performance negative under 1.5× fees or 2× slippage
- Parameter sensitivity check finds cliff parameters (>50% score drop from 10% perturbation)
