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
├── all_tests.ps1                 # Grouped test runner (PowerShell)
├── app/
│   └── controllers/market_making/
│       └── pmm_dynamic.py        # LIVE Hummingbot controller (source of truth for parity)
├── research_notebooks/
│   └── market_lab/
│       └── pmm_dynamic/          # ← PRIMARY SUBPROJECT (pmm_lab package)
│           ├── pyproject.toml    # Subproject config (pmm-lab 0.1.0)
│           ├── README.md
│           ├── requirements-regression.txt  # Pinned deps for frozen regression tests
│           ├── create_sweep_nb.py  # Copier (NOT generator) — notebook is source of truth
│           ├── pmm_lab/          # Python package
│           ├── tests/            # unit/ integration/ regression/
│           ├── notebooks/        # Multi-pair sweep, screener notebooks
│           ├── fixtures/         # Frozen parity fixtures (short_100bar, long_500bar)
│           ├── configs/          # stress_scenarios.yaml, exchange_rules.yaml
│           └── scripts/
├── config/                       # Task pipeline configs
└── scripts/                      # Maintenance scripts
```

## Key Architecture: pmm_lab

The `pmm_lab` package in `research_notebooks/market_lab/pmm_dynamic/` contains:

| Module | Purpose |
|---|---|
| `pmm_lab/data/` | MongoDB candle loader (with synthetic enrichment from `candle_features`), validation (source-declared vs unexpected forward-fill audit), gap detection, hashing |
| `pmm_lab/features/` | PMM Dynamic features (MACD+NATR), regime classification, alignment |
| `pmm_lab/sim/` | Generic candle-bar simulator engine, fill model, inventory, fees |
| `pmm_lab/strategies/` | PMM Dynamic + Bollinger strategies, strategy factory |
| `pmm_lab/optuna/` | Optuna study, search space, canonicalizer (with 50% spread cap), sensitivity, clustering, dispatcher (process-based parallel optimization), preflight checks |
| `pmm_lab/objective/` | Objective v1/v2, walk-forward CV, stress testing (fold-local + holdout-local), holdout validation (exported-candidate gating), signal cache (`SharedSignalCache`), stress selection (early pruning), recent-window evaluation |
| `pmm_lab/export/` | YAML export for Hummingbot, mirror + native validation (requires `id` field) |
| `pmm_lab/deploy/` | Pipeline runner, deployment packages, live tracker, drift monitoring |
| `pmm_lab/parity/` | Frozen fixture system, feature parity checking (short + long fixtures) |
| `pmm_lab/report/` | Markdown report generation (with validation coverage table), stop-ship checks |
| `pmm_lab/utils/` | Reproducibility (seed_everything), trial replay |
| `pmm_lab/config/` | Exchange rules, defaults, parameter definitions |
| `pmm_lab/metrics/` | Performance metrics, equity curves, diagnostics |

## Critical Design Decisions

### Feature Engine — Controller Parity
The live controller (`app/controllers/market_making/pmm_dynamic.py`) recomputes MACD on a **sliding window** of `max_records` bars. The local feature engine has a `controller_compat` mode (default `True`) that replicates this sliding-window behavior. **Do not change this default** — it is required for backtest-to-live equivalence.

The pipeline now supports **split compat modes**: `search_controller_compat=False` (fast vectorized for broad search) and `validation_controller_compat=True` (slow sliding-window for final validation). The multi-pair sweep notebook uses `SEARCH_CONTROLLER_COMPAT = False` by default for performance.

### VPN Routing
All containers in the Trading Pod route through Gluetun VPN. The quants-lab desktop stack connects to the Trading Pod's MongoDB over LAN. Never bypass VPN on the trading side.

### Objective Versions
- **v1**: Linear PnL + Sharpe (legacy)
- **v2**: Log-return + edge penalty, no Sharpe (recommended)
`objective_version` must be threaded consistently through optimization, walk-forward, stress, and holdout.

### Simulation Intrabar Ordering
The engine processes barriers in order: stop-loss → trailing stop (peak update + trigger) → take-profit → time-limit. Trailing stop can activate and trigger on the same bar. Capacity is decremented by the **actually executed** quantity (after spot-constraint clamping), not the requested fill quantity.

### Timing Fields
`executor_refresh_time` and `cooldown_time` are **integers** (seconds) end-to-end: search space (`suggest_int`), SimConfig (`int`), exported YAML (`int`), mirror validator (int check). Do not use floats for these fields.

### Holdout — Exported Candidate Gating
The holdout evaluation gates stop-ship on the **exported config** (candidate index 0), not the best-of-k. `HoldoutReport` has `exported_holdout_passed`, `exported_holdout_score`, `exported_holdout_collapse` fields that drive stop-ship decisions.

### Stop-Ship Checks
The current stop-ship gate includes: `dataset_audit`, `runtime_sanity`, `objective_not_degenerate`, `stress_not_collapsed`, `yaml_validates`, `walkforward_robust`, `walkforward_positive_majority`, `holdout_passed`, `holdout_no_collapse`, `sensitivity_stable`, `recent_28d_passed`, `frozen_parity`, `top_k_clustered`. Optional: `long_parity_passed`. ALL must pass for deployment.

### Spread Cap
The canonicalizer caps spread levels at `MAX_SPREAD_PCT = 50.0`. Levels beyond 50% from reference price are truncated. If all levels exceed the cap, the config is rejected.

### SharedSignalCache
`pmm_lab/objective/signal_cache.py` provides `SharedSignalCache` — a cross-step signal cache keyed by `(signal_cache_key, dataset_key)`. This is used across walk-forward, holdout, stress, sensitivity, and recent-window steps to avoid redundant signal computation.

## Infrastructure

### MongoDB (candle data)
- Lives on TrueNAS Trading Pod at `TRUENAS_LAN_IP:27017`
- Database: `quants_lab`, collections: `candles` (~4.6M docs), `candle_features` (synthetic flags)
- Auth: `admin` user (credentials in compose, NOT from `MONGO_ROOT_PASSWORD`)
- Connection: set `MONGO_URI` in `.env` at repo root
- Loader projects only OHLCV fields and enriches `is_forward_fill` from `candle_features`

### Optuna Postgres (study storage)
- Local container via `quantslab_desktop_compose.yaml`
- `postgresql+psycopg2://optuna:optuna@optuna-postgres:5432/optuna`
- **Multi-worker optimization requires PostgreSQL** — SQLite is forced to `n_jobs=1`

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

# Grouped test runner (from repo root)
.\all_tests.ps1 -Grouped    # Per-category pass/fail table
.\all_tests.ps1 -Quick       # Unit tests only
```

Expected results: ~850+ passed, 3 skipped (Hummingbot PostgreSQL), 0 failed.

Frozen regression tests depend on exact dependency versions — see `requirements-regression.txt`. The test suite warns if the environment doesn't match pinned versions.

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
    search_controller_compat=False,      # fast vectorized for search
    validation_controller_compat=True,   # sliding-window for validation
)

if result.stop_ship_passed:
    print(f"Deploy: {result.yaml_path}")
```

## Multi-Pair Sweep Notebook

The **authoritative** sweep notebook is `notebooks/pmm_dynamic_multi_pair_sweep.ipynb`. The file `create_sweep_nb.py` is a **copier** (not a generator) — the notebook is the single source of truth. Key features:

- `SEARCH_CONTROLLER_COMPAT = False` for fast search (root cause fix)
- Preflight check enforces `N_JOBS=1` on SQLite
- Zero-completed-trial guard (explicit `ranked` list, no bare `study.best_trial`)
- Stale-pair filtering (`MAX_STALE_DAYS = 7`)
- Phase-1 score gate before stress (`MIN_PHASE1_BEST_FOR_STRESS = 0.0`)
- `total_amount_quote` search range surfaced in reports

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
- Pass `dataset_hash` to `run_stop_ship_checks()` (it has no such parameter)
- Use `study.best_trial` / `study.best_value` directly — build explicit `ranked` list from completed trials
- Run multi-worker Optuna on SQLite storage (use PostgreSQL or force `n_jobs=1`)
- Use `create_sweep_nb.py` to regenerate the notebook — edit the notebook directly
