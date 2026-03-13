# PMM Lab — PMM Dynamic Hyper-Bayesian Optimization for Hummingbot

A complete pipeline for data ingestion, feature engineering, backtesting, walk-forward validation, stress testing, Bayesian hyperparameter optimization, and Hummingbot-compatible YAML export for the PMM Dynamic market-making strategy.

## Architecture

```
research_notebooks/market_lab/pmm_dynamic/
├── pmm_lab/
│   ├── config/          # Exchange rules, defaults, parameter dataclasses
│   ├── data/            # MongoDB ingestion, candle validation, hashing
│   ├── features/        # PMM Dynamic feature computation (MACD, NATR, spreads)
│   ├── sim/             # CPU backtest engine (executor model, fill model, fees)
│   ├── metrics/         # Equity curves, Sharpe, drawdown, diagnostics
│   ├── objective/       # Objective function, walk-forward CV, stress testing
│   ├── optuna/          # Bayesian optimization (TPE sampler, search space, callbacks)
│   ├── export/          # Hummingbot YAML exporter and schema validator
│   └── report/          # Markdown report generator with stop-ship checks
├── configs/
│   ├── exchange_rules.yaml     # Per-pair trading rules
│   ├── stress_scenarios.yaml   # Stress test scenario definitions
│   └── generated/              # Auto-generated configs from optimization
├── notebooks/
│   └── pmm_dynamic_hyperbo.ipynb  # Master notebook (15 sections)
├── tests/
│   ├── unit/            # Unit tests (no external dependencies)
│   ├── integration/     # Integration tests (MongoDB, Optuna)
│   └── regression/      # Determinism regression tests
├── artifacts/           # Saved reports, YAML exports
├── Makefile             # 11+ automation targets
├── pyproject.toml       # Package definition
└── README.md            # This file
```

## Prerequisites

- **Docker Compose stack** (`quantslab_desktop_compose.yaml`) with:
  - MongoDB (candle data storage)
  - PostgreSQL (optional, for Optuna study persistence)
  - JupyterLab
- **`.env` file** with `TRUENAS_LAN_IP` configured
- **Python 3.10+** (provided by the `quants-lab` conda environment)

## Project Location

All files live under `research_notebooks/market_lab/pmm_dynamic/` within the quants-lab repo. This is a self-contained sub-project — do not place files at the repo root.

## Quick Start

```bash
cd /quants-lab/research_notebooks/market_lab/pmm_dynamic
pip install -e ".[dev]"
make test
```

## Running in Docker

```bash
docker compose -f quantslab_desktop_compose.yaml exec -it ql-jupyter \
  bash -c "cd /quants-lab/research_notebooks/market_lab/pmm_dynamic && make test"
```

## Makefile Targets

| Target | Description |
|--------|-------------|
| `help` | Show all available targets |
| `test` | Run all unit + integration tests (no MongoDB needed) |
| `test-unit` | Run unit tests only |
| `test-live` | Run integration tests requiring MongoDB |
| `test-regression` | Run regression tests (determinism checks) |
| `data-audit` | Run data audit on default dataset (requires MongoDB) |
| `backtest-smoke` | Run a single baseline backtest on synthetic data |
| `walkforward-smoke` | Run walk-forward on synthetic data (3 folds) |
| `stress-smoke` | Run stress tests on synthetic data |
| `optimize-smoke` | Run 30-trial Optuna optimization on synthetic data |
| `export-validate` | Export best config as YAML and validate |
| `clean-artifacts` | Remove artifacts older than 30 days |

## Notebook Usage

Open `notebooks/pmm_dynamic_hyperbo.ipynb` in JupyterLab. The notebook has 15 sections covering the full pipeline:

1. Environment and Version Checks
2. Connect to MongoDB
3. Dataset Discovery
4. Candle Extraction and Validation
5. Forward-Fill Analysis
6. Timestamp Semantics
7. PMM Dynamic Feature Parity
8. Baseline CPU Backtest
9. Metrics and Objective Decomposition
10. Walk-Forward Validation
11. Stress Testing
12. Optuna Study Setup and Optimization
13. Best-Trial Review and Top-N Comparison
14. Hummingbot YAML Export and Validation
15. Markdown Report Generation

Cells that depend on MongoDB or Postgres are wrapped in `try/except` with clear skip messages, so the notebook can be reviewed even outside the Docker stack.

## Configuration Files

- **`configs/exchange_rules.yaml`**: Per-pair trading rules (price tick, amount step, min notional, fees). Used by the simulator and canonicalizer.
- **`configs/stress_scenarios.yaml`**: Stress test scenario definitions (fee multipliers, latency additions, liquidity reductions). Applied via `dataclasses.replace()` on SimConfig/PairRules.

## Future Work

- Forward-fill detection in candle data (v2)
- GPU backend for simulation (CuPy/Numba)
- XMR-quote trading pairs
- HBRunner integration for live strategy deployment
- Multi-objective optimization (Pareto front)
