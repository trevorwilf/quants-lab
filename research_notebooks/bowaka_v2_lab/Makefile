# bowaka_v2_lab test + dev workflow.
#
# All test targets set PYTHONPATH so the lab and the shared bowaka_common package
# resolve without an editable install. Per-segment timeouts come from
# pyproject.toml ([tool.pytest.ini_options] timeout = 60); long segments raise it
# explicitly. See docs/audits/2026-05-22_realism_audit.md §P1-007.

.PHONY: install test test-fast test-unit test-parity test-integration \
        test-reconcile test-live test-all smoke notebooks verify-bayesian-fix \
        verify-session-window-parity clean

# bowaka_common lives one directory up; both must be importable for the suite.
PYTHONPATH := src:../bowaka_common/src
# Interpreter override: the lab's runtime deps (optuna/pandas/pyarrow/...) must
# be importable. If your default `python` lacks them (e.g. a bare 3.14), pass an
# explicit one, e.g. `make verify-bayesian-fix PYTHON=C:/Python312/python.exe`.
PYTHON ?= python
PYTEST := PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest
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

# verify-bayesian-fix — emit the audit 2026-05-29 Phase 3 verification report
# (operator-pasteable PASS/FAIL grid). Sets PYTHONPATH like the test targets so
# the lab is importable without an editable install. Pass extra flags via ARGS,
# e.g. `make verify-bayesian-fix ARGS="--skip-short-run"`.
verify-bayesian-fix:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m bowaka_v2_lab.cli verify-bayesian-fix $(ARGS)

# verify-session-window-parity — runs every parity test guarding the
# session_minute_window_cache acceleration flag. Both legs must be green
# before re-enabling the flag in any config. See
# PHASE_NOTES/session_minute_window_supplier_parity_fix.md for the
# multi-phase fix that motivates this target.
verify-session-window-parity:
	@set +e; \
	  $(PYTEST) tests/scanner/test_session_minute_window_supplier_parity.py -v --tb=short; \
	  rc1=$$?; \
	  $(PYTEST) tests/integration/test_session_window_supplier_walkforward_parity.py -v --tb=short; \
	  rc2=$$?; \
	  rc=$$rc1; if [ $$rc2 -gt $$rc ]; then rc=$$rc2; fi; \
	  if [ $$rc -eq 0 ]; then \
	    echo "Phase 4 supplier parity: OK (supplier+walkforward parity tests passed)"; \
	  else \
	    echo "Phase 4 supplier parity: FAIL (supplier=$$rc1, walkforward=$$rc2)"; \
	  fi; \
	  exit $$rc

clean:
	rm -rf .pytest_cache .ruff_cache build dist *.egg-info src/*.egg-info
