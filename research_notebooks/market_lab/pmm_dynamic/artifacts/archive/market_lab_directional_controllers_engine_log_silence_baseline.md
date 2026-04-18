# Engine Log Silence — Baseline

**Date**: 2026-04-17

## Test Suite Baseline

Command:
```
pytest tests/ -q --ignore=tests/integration/test_mongo_live.py --ignore=tests/integration/test_optuna_smoke.py
```

Result: **1251 passed, 58 skipped, 0 failed, 25 warnings** in 49.13s.

Matches the phase-2-delta FINAL count exactly (1251 / 58 / 0). Ready to proceed.

## Warning-code presence check

Command:
```
grep -n "_warned_no_orders\|no orders placed" pmm_lab/sim/engine.py
```

Output (all 5 expected matches present):
```
51:        self._warned_no_orders = False
303:        self._warned_no_orders = False
651:                if placed == 0 and not self._warned_no_orders:
652:                    self._warned_no_orders = True
654:                        "Bar %d: no orders placed (this warning will not repeat)", bar
```

Ready to delete.
