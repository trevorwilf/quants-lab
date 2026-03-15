# CLAUDE.md — quants-lab

## Project Overview

Quantitative research framework for Hummingbot trading strategies. The primary active subproject is `research_notebooks/market_lab/pmm_dynamic` — a backtesting, Bayesian optimization, and deployment pipeline for PMM Dynamic market-making strategies.

## Repository Layout

```
quants-lab/
├── .env                          # TRUENAS_LAN_IP, MONGO_URI, MONGO_ROOT_PASSWORD, etc.
├── quantslab_desktop_compose.yaml # Docker Compose: Jupyter + Optuna Postgres + MongoDB
├── environment.yml               # Conda environment (root)
├── pyproject.toml                # Root package config (quants-lab 2.0.0)
├── app/
│   └── controllers/market_making/
│       └── pmm_dynamic.py        # LIVE Hummingbot controller (source of truth for parity)
├── research_notebooks/
│   └── market_lab/
│       └── pmm_dynamic/          # ← PRIMARY SUBPROJECT (pmm_lab package)
│           ├── pyproject.toml    # Subproject config (pmm-lab 0.1.0)
│           ├── README.md
│           ├── pmm_lab/          # Python package
│           ├── tests/            # unit/ integration/ regression/
│           ├── notebooks/
│           ├── fixtures/         # Frozen parity fixtures
│           └── scripts/
├── config/                       # Task pipeline configs
└── scripts/                      # Maintenance scripts
```

## Key Architecture: pmm_lab

The `pmm_lab` package in `research_notebooks/market_lab/pmm_dynamic/` contains:

| Module | Purpose |
|---|---|
| `pmm_lab/data/` | MongoDB candle loader, validation, forward-fill detection, hashing |
| `pmm_lab/features/` | PMM Dynamic features (MACD+NATR), regime classification, alignment |
| `pmm_lab/sim/` | Generic candle-bar simulator engine, fill model, inventory, fees |
| `pmm_lab/strategies/` | PMM Dynamic + Bollinger strategies, strategy factory |
| `pmm_lab/optuna/` | Optuna study, search space, canonicalizer, sensitivity, clustering |
| `pmm_lab/objective/` | Objective v1/v2, walk-forward CV, stress testing, holdout validation |
| `pmm_lab/export/` | YAML export for Hummingbot, mirror + native validation |
| `pmm_lab/deploy/` | Pipeline runner, deployment packages, live tracker, drift monitoring |
| `pmm_lab/parity/` | Frozen fixture system, feature parity checking |
| `pmm_lab/report/` | Markdown report generation, stop-ship checks |
| `pmm_lab/utils/` | Reproducibility (seed_everything), trial replay |
| `pmm_lab/config/` | Exchange rules, defaults, parameter definitions |
| `pmm_lab/metrics/` | Performance metrics, equity curves, diagnostics |

## Critical Design Decisions

### Feature Engine — Controller Parity
The live controller (`app/controllers/market_making/pmm_dynamic.py`) recomputes MACD on a **sliding window** of `max_records` bars. The local feature engine has a `controller_compat` mode (default `True`) that replicates this sliding-window behavior. **Do not change this default** — it is required for backtest-to-live equivalence.

### VPN Routing
All containers in the Trading Pod route through Gluetun VPN. The quants-lab desktop stack connects to the Trading Pod's MongoDB over LAN. Never bypass VPN on the trading side.

### Objective Versions
- **v1**: Linear PnL + Sharpe (legacy)
- **v2**: Log-return + edge penalty, no Sharpe (recommended)
`objective_version` must be threaded consistently through optimization, walk-forward, stress, and holdout.

### Simulation Intrabar Ordering
The engine processes barriers in order: stop-loss → trailing stop (peak update + trigger) → take-profit → time-limit. Trailing stop can activate and trigger on the same bar. This is documented in `pmm_lab/sim/engine.py`.

## Infrastructure

### MongoDB (candle data)
- Lives on TrueNAS Trading Pod at `TRUENAS_LAN_IP:27017`
- Database: `quants_lab`, collection: `candles` (~4.6M docs)
- Auth: `admin` user (credentials in compose, NOT from `MONGO_ROOT_PASSWORD`)
- Connection: set `MONGO_URI` in `.env` at repo root

### Optuna Postgres (study storage)
- Local container via `quantslab_desktop_compose.yaml`
- `postgresql+psycopg2://optuna:optuna@optuna-postgres:5432/optuna`

### Hummingbot Postgres (live trade data)
- On Trading Pod at `TRUENAS_LAN_IP:5432`
- Database: `hummingbot_api`, user: `hbot`
- Used by `LivePerformanceTracker` for drift detection

## .env File

Located at the repo root. Required variables:

```dotenv
TRUENAS_LAN_IP=192.168.1.54
MONGO_URI=mongodb://admin:<password>@192.168.1.54:27017/quants_lab?authSource=admin&retryWrites=true&w=majority
MONGO_ROOT_PASSWORD=<not used for auth — legacy>
POSTGRES_PASSWORD=<hummingbot db password>
JUPYTER_TOKEN=<jupyter access token>
```

The test suite auto-discovers `.env` by walking up from the test directory.

## Running Tests

```powershell
# From the pmm_dynamic subproject directory:
cd research_notebooks/market_lab/pmm_dynamic

# All tests (MongoDB auto-detected from .env, PostgreSQL auto-skips if unreachable)
python -m pytest tests/ -v --tb=long

# Quick unit tests only
python -m pytest tests/unit/ -v -x --tb=short

# Specific test file
python -m pytest tests/unit/test_engine.py -v --tb=long
```

Expected results: ~500+ passed, 3 skipped (Hummingbot PostgreSQL), 0 failed.

## Full Pipeline Usage

```python
from pmm_lab.deploy.runner import run_full_pipeline

result = run_full_pipeline(
    connector="nonkyc",
    trading_pair="XMR-USDT",
    interval="5m",
    n_trials=200,
    output_dir="artifacts",
    objective_version=2,
    certified=True,  # n_jobs=1 for determinism
)

if result.stop_ship_passed:
    print(f"Deploy: {result.yaml_path}")
```

## Common Tasks

### Adding a new strategy
1. Create `pmm_lab/strategies/my_strategy.py` implementing `compute_signals()` + `build_orders()`
2. Register in `pmm_lab/strategies/factory.py`
3. Test with `GenericSimRunner`

### Regenerating frozen fixtures
```bash
cd research_notebooks/market_lab/pmm_dynamic
python scripts/generate_fixtures.py
# Then commit the fixtures/ directory
```

### Monitoring live deployments
```python
from pmm_lab.deploy.monitor import monitor_all_deployments
results = monitor_all_deployments("artifacts/")
```

## File Naming Conventions

- Claude Code prompts: `pmmLab_{description}_claude_code_prompt.md`
- Other Claude outputs: `*_claude_code.md`
- Test files: `tests/{unit,integration,regression}/test_*.py`
- Strategy files: `pmm_lab/strategies/{name}.py`

## Do NOT

- Change `controller_compat` default to `False` without regenerating all fixtures
- Use `network_mode: host` on any Trading Pod container
- Hardcode MongoDB credentials (use `.env`)
- Skip stop-ship checks for deployment
- Run certified/deployment pipelines with `n_jobs > 1`
- Modify golden values in tests without a changelog comment explaining why
