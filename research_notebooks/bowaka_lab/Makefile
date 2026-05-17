.PHONY: install test test-unit test-integration test-live lint smoke clean

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
