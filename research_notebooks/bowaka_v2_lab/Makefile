# bowaka_v2_lab test + dev workflow.
#
# All test targets set PYTHONPATH so the lab and the shared bowaka_common package
# resolve without an editable install. Per-segment timeouts come from
# pyproject.toml ([tool.pytest.ini_options] timeout = 60); long segments raise it
# explicitly. See docs/audits/2026-05-22_realism_audit.md §P1-007.

.PHONY: install test test-fast test-unit test-parity test-integration \
        test-reconcile test-live test-all smoke notebooks clean

# bowaka_common lives one directory up; both must be importable for the suite.
PYTHONPATH := src:../bowaka_common/src
PYTEST := PYTHONPATH=$(PYTHONPATH) python -m pytest
# Markers excluded from every non-live run.
NOT_LIVE := not live_alpaca and not live_paper and not live_mongo

install:
	pip install -e .[dev]
	pip install pytest-timeout

# Default `make test` — fast, non-slow, non-live (unit + parity + integration + reconcile).
test:
	$(PYTEST) tests -q --tb=short -m "$(NOT_LIVE) and not slow"

# test-fast — unit + parity only, the quickest meaningful gate.
test-fast:
	$(PYTEST) tests/unit tests/parity -q --tb=short \
	  -m "$(NOT_LIVE) and not slow"

# test-unit — unit tests only.
test-unit:
	$(PYTEST) tests/unit -q --tb=short -m "$(NOT_LIVE) and not slow"

# test-parity — actual-contract parity tests only.
test-parity:
	$(PYTEST) tests/parity -q --tb=short -m "$(NOT_LIVE) and not slow"

# test-integration — integration tests; 120s/test budget for real backtests.
test-integration:
	$(PYTEST) tests/integration --timeout=120 --timeout-method=thread \
	  -q --tb=short -m "$(NOT_LIVE) and not slow"

# test-reconcile — paper-vs-sim reconciliation tests.
test-reconcile:
	$(PYTEST) tests/reconcile --timeout=120 --timeout-method=thread \
	  -q --tb=short -m "$(NOT_LIVE) and not slow"

# test-live — live-credential / live-paper tests (opt-in; needs creds / paper logs).
test-live:
	$(PYTEST) tests --timeout=300 --timeout-method=thread \
	  -q --tb=short -m "live_alpaca or live_paper or live_mongo or slow"

# test-all — unit+parity, THEN integration+reconcile. Final exit = max of children
# so a later failure is never masked by an earlier pass.
test-all:
	@set +e; \
	  $(PYTEST) tests/unit tests/parity -q --tb=short -m "$(NOT_LIVE) and not slow"; \
	  rc1=$$?; \
	  $(PYTEST) tests/integration tests/reconcile --timeout=120 --timeout-method=thread \
	    -q --tb=short -m "$(NOT_LIVE) and not slow"; \
	  rc2=$$?; \
	  rc=$$rc1; if [ $$rc2 -gt $$rc ]; then rc=$$rc2; fi; \
	  echo "test-all: unit+parity exit=$$rc1, integration+reconcile exit=$$rc2, final exit=$$rc"; \
	  exit $$rc

smoke:
	python -m bowaka_v2_lab.cli smoke --config configs/bowaka_v2_backtest_smoke.yml

notebooks:
	@echo "Notebooks are built by notebooks/_build_*.py scripts; run individually after Phase 5/6/7."

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info src/*.egg-info
