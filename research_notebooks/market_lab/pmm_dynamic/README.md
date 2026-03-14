# pmm_lab — PMM Dynamic Hyper-Bayesian Optimization

A production-grade backtesting, optimization, and deployment framework for
Hummingbot market-making strategies.

## Quick Start

```python
from pmm_lab.deploy.runner import run_full_pipeline

result = run_full_pipeline(
    connector="nonkyc",
    trading_pair="XMR-USDT",
    interval="5m",
    n_trials=200,
    output_dir="artifacts",
)

if result.stop_ship_passed:
    print(f"Deploy: {result.yaml_path}")
else:
    print(f"Stop-ship FAILED: {result.stop_ship_checks}")
```

## Architecture

### Data Pipeline
- **`pmm_lab.data.mongo`** — MongoDB candle loader (4.6M+ candles)
- **`pmm_lab.data.candles`** — validation, gap detection, forward-fill detection
- **`pmm_lab.data.hashing`** — deterministic dataset hashing for audit trail

### Simulation Engine
- **`pmm_lab.sim.engine`** — Generic candle-bar simulator (fills, barriers, inventory, equity)
- **`pmm_lab.sim.strategy`** — Strategy protocol (any strategy that produces signals + orders)
- **`pmm_lab.sim.fill_model`** — Touch-through, entry spread, maker fill probability
- **`pmm_lab.sim.inventory`** — Position tracking with rebalance support
- **`pmm_lab.sim.runner`** — PMM Dynamic runner (thin wrapper over engine)
- **`pmm_lab.sim.generic_runner`** — Run any strategy through the engine

### Strategies
- **`pmm_lab.strategies.pmm_dynamic`** — MACD + NATR market making
- **`pmm_lab.strategies.bollinger`** — Bollinger Bands market making
- **`pmm_lab.strategies.factory`** — `create_strategy("name", config)` factory

### Features
- **`pmm_lab.features.pmm_dynamic_features`** — MACD, NATR, spread/price multipliers
- **`pmm_lab.features.regime`** — Market regime classification (vol + trend)
- **`pmm_lab.features.alignment`** — Timestamp alignment (open vs close mode)

### Optimization
- **`pmm_lab.optuna.study`** — Optuna study creation (TPE sampler)
- **`pmm_lab.optuna.search_space`** — Log-scaled search space (v2)
- **`pmm_lab.optuna.canonicalizer`** — Raw params → valid SimConfig
- **`pmm_lab.optuna.objective_wrapper`** — Walk-forward + fold-local stress
- **`pmm_lab.optuna.sensitivity`** — ±10% perturbation analysis
- **`pmm_lab.optuna.clustering`** — Top-k parameter convergence check

### Objective Functions
- **`pmm_lab.objective.objective`** — v1 (linear PnL + Sharpe) and v2 (log-return + edge penalty)
- **`pmm_lab.objective.robustness`** — Median - λ×MAD aggregation (v1 and v2)
- **`pmm_lab.objective.walkforward`** — Time-series cross-validation with embargo
- **`pmm_lab.objective.stress`** — 15+ stress scenarios + fold-local stress
- **`pmm_lab.objective.holdout`** — 80/20 split, collapse detection

### Export & Validation
- **`pmm_lab.export.hb_yaml`** — Export SimConfig → Hummingbot YAML
- **`pmm_lab.export.validate_export`** — Mirror + native validation (19 checks)
- **`pmm_lab.parity`** — Frozen fixture regression + native parity (when HB installed)

### Deployment
- **`pmm_lab.deploy.runner`** — Full pipeline: data → optimize → validate → package → report
- **`pmm_lab.deploy.package`** — Deployment package (config + expected metrics + audit trail)
- **`pmm_lab.deploy.live_tracker`** — Read live trades from Hummingbot PostgreSQL
- **`pmm_lab.deploy.comparison`** — Live vs backtest drift detection
- **`pmm_lab.deploy.monitor`** — Monitor all deployments, generate summary

### Utilities
- **`pmm_lab.utils.reproducibility`** — `seed_everything()`, environment snapshots
- **`pmm_lab.utils.replay`** — Trial recording, save/load JSONL, replay verification

### Reports
- **`pmm_lab.report.report_md`** — Markdown report + stop-ship checks

## Testing

```bash
# Run all tests (MongoDB auto-discovered from .env)
python -m pytest tests/ -v --tb=long

# Quick smoke test
python -m pytest tests/unit/ -v -x --tb=short
```

## Configuration

### .env file

```dotenv
TRUENAS_LAN_IP=192.168.1.54
MONGO_ROOT_PASSWORD=<mongo_password>
POSTGRES_PASSWORD=<hummingbot_db_password>
```

### Exchange rules

Exchange-specific tick sizes, min notionals, and fees are in:
```
pmm_lab/config/exchange_rules.yaml
```

### Stress scenarios

Stress test configurations in:
```
pmm_lab/configs/stress_scenarios.yaml
```

## Monitoring

```python
from pmm_lab.deploy.monitor import monitor_all_deployments, generate_monitoring_summary

results = monitor_all_deployments("artifacts/")
summary = generate_monitoring_summary(results)
print(summary)
```

## Adding a New Strategy

1. Create `pmm_lab/strategies/my_strategy.py`
2. Implement the Strategy protocol:
   ```python
   class MyStrategy:
       def compute_signals(self, candles): ...
       def build_orders(self, bar_idx, signals, engine_config, pair_rules, inventory): ...
   ```
3. Register in factory: `pmm_lab/strategies/factory.py`
4. Run through GenericSimRunner or the full pipeline
