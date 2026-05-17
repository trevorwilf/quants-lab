.PHONY: install test test-unit test-integration test-live lint smoke clean optuna-smoke optuna-walkforward

install:
	pip install -e .[dev]

test:
	python -m pytest tests -q --tb=short -m "not live_alpaca and not live_mongo and not slow"

test-unit:
	python -m pytest tests/unit -q --tb=short

test-integration:
	python -m pytest tests/integration -q --tb=short

test-live:
	python -m pytest tests/live -q --tb=short -m "live_alpaca or live_mongo"

lint:
	ruff check src tests
	black --check src tests
	isort --check-only src tests

smoke:
	bowaka-lab smoke --offline-fixtures

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info

# Quick smoke study using the notebook's smoke mode (in-memory sqlite, 20 trials)
optuna-smoke:
	@echo "==> Running notebook 10 in smoke mode"
	jupyter nbconvert --to notebook --execute \
	  --ExecutePreprocessor.timeout=300 \
	  notebooks/10_optuna_walkforward.ipynb \
	  --output /tmp/10_optuna_smoke_out.ipynb

# Production walk-forward against PostgreSQL.
# Requires OPTUNA_STORAGE to be set to a PostgreSQL URI.
optuna-walkforward:
	@if [ -z "$$OPTUNA_STORAGE" ]; then \
	    echo "ERROR: OPTUNA_STORAGE not set. Production runs require PostgreSQL."; \
	    echo "Example: export OPTUNA_STORAGE='postgresql+psycopg2://optuna:optuna@localhost:5433/optuna'"; \
	    exit 2; \
	fi
	@echo "==> Running production walk-forward (Postgres-backed)"
	python scripts/run_optuna_walkforward.py \
	  --run-id $${RUN_ID:-bt_iex_default} \
	  --n-trials $${N_TRIALS:-500} \
	  --n-jobs $${N_JOBS:-4} \
	  --study-name $${STUDY_NAME:-bowaka_prod_$${RUN_ID:-bt_iex_default}_v1}
