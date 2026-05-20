.PHONY: install test test-unit test-integration smoke notebooks clean

install:
	pip install -e .[dev]

test:
	python -m pytest tests -q --tb=short -m "not live_alpaca and not slow"

test-unit:
	python -m pytest tests/unit -q --tb=short

test-integration:
	python -m pytest tests/integration -q --tb=short

smoke:
	python -m bowaka_v2_lab.cli smoke --config configs/bowaka_v2_backtest_smoke.yml

notebooks:
	@echo "Notebooks are built by notebooks/_build_*.py scripts; run individually after Phase 5/6/7."

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info src/*.egg-info
