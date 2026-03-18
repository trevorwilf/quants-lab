.PHONY: test test-unit test-slow test-full test-live test-regression data-audit backtest-smoke \
        walkforward-smoke stress-smoke optimize-smoke export-validate \
        test-phase1 test-phase2 test-phase3 test-all-phases test-parity test-stop-ship \
        test-trade-accounting clean-artifacts help

PROJ_DIR := $(shell pwd)

help:
	@echo "PMM Lab — Available targets:"
	@echo "  test              Run all unit + integration tests (no MongoDB needed)"
	@echo "  test-unit         Run unit tests only"
	@echo "  test-live         Run integration tests requiring MongoDB"
	@echo "  test-regression   Run regression tests"
	@echo "  test-phase1       Run Phase 1 correctness fix tests"
	@echo "  test-phase2       Run Phase 2 parity & contract tests"
	@echo "  test-phase3       Run Phase 3 hardening & stress tests"
	@echo "  test-all-phases   Run all Phase 1-3 tests sequentially"
	@echo "  test-parity       Run parity tests only"
	@echo "  test-stop-ship    Run stop-ship gate tests"
	@echo "  test-trade-accounting  Run trade accounting tests"
	@echo "  data-audit        Run data audit on default dataset (requires MongoDB)"
	@echo "  backtest-smoke    Run a single baseline backtest on synthetic data"
	@echo "  walkforward-smoke Run walk-forward on synthetic data (3 folds)"
	@echo "  stress-smoke      Run stress tests on synthetic data"
	@echo "  optimize-smoke    Run 30-trial Optuna optimization on synthetic data"
	@echo "  export-validate   Export best config as YAML and validate"
	@echo "  clean-artifacts   Remove old artifacts"

test:
	python -m pytest tests/ -q --tb=short -m "not live_mongo and not slow"

test-unit:
	python -m pytest tests/unit/ -q --tb=short -m "not slow"

test-slow:
	python -m pytest tests/ -q --tb=short -m "slow and not live_mongo"

test-full:
	python -m pytest tests/ -q --tb=short -m "not live_mongo"

test-live:
	python -m pytest tests/integration/ -q --tb=short -m live_mongo

test-regression:
	python -m pytest tests/regression/ -q --tb=short

data-audit:
	python -m pmm_lab.data.quality

backtest-smoke:
	python -c "\
from tests.conftest import _make_sample_candles_5m; \
from pmm_lab.sim.runner import CandleSimRunner; \
from pmm_lab.sim.executor_model import SimConfig; \
from pmm_lab.config.params import PairRules, FeeConfig; \
candles = _make_sample_candles_5m(); \
config = SimConfig(buy_spreads=[1.0,2.0], sell_spreads=[1.0,2.0], \
  buy_amounts_pct=[0.5,0.5], sell_amounts_pct=[0.5,0.5]); \
rules = PairRules(price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0, \
  fees=FeeConfig(0.001, 0.002)); \
result = CandleSimRunner(config, rules).run(candles); \
print(f'Trades: {len(result.trades)}, PnL: {result.equity_curve[-1] - 100:.2f} quote'); \
"

walkforward-smoke:
	python -c "\
from tests.conftest import _make_sample_candles_500; \
from pmm_lab.sim.executor_model import SimConfig; \
from pmm_lab.config.params import PairRules, FeeConfig; \
from pmm_lab.objective.walkforward import run_walk_forward; \
from pmm_lab.data.hashing import hash_candles; \
candles = _make_sample_candles_500(); \
config = SimConfig(buy_spreads=[1.0,2.0], sell_spreads=[1.0,2.0], \
  buy_amounts_pct=[0.5,0.5], sell_amounts_pct=[0.5,0.5]); \
rules = PairRules(price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0, \
  fees=FeeConfig(0.001, 0.002)); \
result = run_walk_forward(candles, config, rules, 300, hash_candles(candles), \
  train_days=0.5, test_days=0.25, step_days=0.25); \
print(f'Folds: {len(result.folds)}, Aggregate: {result.aggregate_score:.4f}'); \
"

stress-smoke:
	python -c "\
from tests.conftest import _make_sample_candles_5m; \
from pmm_lab.sim.executor_model import SimConfig; \
from pmm_lab.config.params import PairRules, FeeConfig; \
from pmm_lab.objective.stress import run_stress_tests; \
candles = _make_sample_candles_5m(); \
config = SimConfig(buy_spreads=[1.0,2.0], sell_spreads=[1.0,2.0], \
  buy_amounts_pct=[0.5,0.5], sell_amounts_pct=[0.5,0.5]); \
rules = PairRules(price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0, \
  fees=FeeConfig(0.001, 0.002)); \
report = run_stress_tests(candles, config, rules, 300); \
print(f'Scenarios: {len(report.scenario_results)}, Worst: {report.worst_scenario}'); \
"

optimize-smoke:
	python -c "\
from tests.conftest import _make_sample_candles_500; \
from pmm_lab.config.params import PairRules, FeeConfig; \
from pmm_lab.data.hashing import hash_candles; \
from pmm_lab.optuna.study import create_study, run_optimization; \
from pmm_lab.optuna.objective_wrapper import create_objective; \
import numpy as np; \
candles = _make_sample_candles_500(); \
rules = PairRules(price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0, \
  fees=FeeConfig(0.001, 0.002)); \
dh = hash_candles(candles); \
ref_price = float(np.median(candles['close'])); \
obj = create_objective(candles, rules, 300, dh, ref_price, \
  train_days=0.5, test_days=0.25, step_days=0.25, run_stress=False); \
study = create_study('smoke_test', storage_url='sqlite:///smoke_test.db'); \
run_optimization(study, obj, n_trials=30); \
print(f'Trials: {len(study.trials)}, Best: {study.best_value:.4f}'); \
import os; os.remove('smoke_test.db'); \
"

export-validate:
	python -c "\
from pmm_lab.sim.executor_model import SimConfig; \
from pmm_lab.export.hb_yaml import export_yaml, ExportParams; \
from pmm_lab.export.validate_export import validate_yaml_file; \
config = SimConfig(buy_spreads=[1.0,2.0,4.0], sell_spreads=[1.0,2.0], \
  buy_amounts_pct=[0.33,0.33,0.34], sell_amounts_pct=[0.5,0.5]); \
path = export_yaml(config, 'artifacts/test_export.yml'); \
result = validate_yaml_file(path); \
print(f'Valid: {result.valid}, Mode: {result.mode}, Errors: {result.errors}'); \
import os; os.remove(path); \
"

# --- Phase 1-3 specific test targets ---

test-phase1:
	@echo "Running Phase 1 tests (correctness fixes)..."
	python -m pytest \
		tests/unit/test_trade_accounting.py \
		tests/unit/test_final_liquidation.py \
		tests/unit/test_objective.py \
		tests/unit/test_objective_v2.py \
		tests/unit/test_search_space.py \
		tests/unit/test_canonicalizer.py \
		tests/unit/test_holdout.py \
		tests/unit/test_recent_window.py \
		tests/unit/test_pipeline_runner.py \
		-v --tb=short

test-phase2:
	@echo "Running Phase 2 tests (parity & contract)..."
	python -m pytest \
		tests/unit/test_parity_harness.py \
		tests/unit/test_features_parity.py \
		tests/unit/test_native_parity.py \
		tests/unit/test_stop_ship_parity.py \
		tests/unit/test_stop_ship_clustering.py \
		tests/unit/test_live_tracker_fees.py \
		tests/unit/test_export_contract.py \
		tests/unit/test_yaml_export.py \
		tests/unit/test_validate_export_v2.py \
		-v --tb=short

test-phase3:
	@echo "Running Phase 3 tests (hardening & stress)..."
	python -m pytest \
		tests/unit/test_price_rounding.py \
		tests/unit/test_partial_close.py \
		tests/unit/test_stress.py \
		tests/unit/test_fold_local_stress.py \
		tests/unit/test_parallel.py \
		tests/unit/test_exchange_rules.py \
		tests/unit/test_canonicalizer.py \
		-v --tb=short

test-all-phases:
	@echo "Running all Phase 1-3 tests..."
	$(MAKE) test-phase1
	$(MAKE) test-phase2
	$(MAKE) test-phase3

test-parity:
	@echo "Running parity tests only..."
	python -m pytest \
		tests/unit/test_parity_harness.py \
		tests/unit/test_features_parity.py \
		tests/unit/test_native_parity.py \
		tests/unit/test_feature_controller_compat.py \
		-v --tb=short

test-stop-ship:
	@echo "Running stop-ship gate tests..."
	python -m pytest \
		tests/unit/test_stop_ship_parity.py \
		tests/unit/test_stop_ship_clustering.py \
		tests/unit/test_report.py \
		-v --tb=short

test-trade-accounting:
	@echo "Running trade accounting tests..."
	python -m pytest \
		tests/unit/test_trade_accounting.py \
		tests/unit/test_final_liquidation.py \
		tests/unit/test_partial_close.py \
		tests/unit/test_metrics.py \
		tests/unit/test_engine.py \
		-v --tb=short

clean-artifacts:
	find artifacts/ -name "*.yml" -mtime +30 -delete 2>/dev/null || true
	find artifacts/ -name "*.json" -mtime +30 -delete 2>/dev/null || true
	find artifacts/ -name "*.md" -mtime +30 -delete 2>/dev/null || true
	@echo "Cleaned artifacts older than 30 days."
