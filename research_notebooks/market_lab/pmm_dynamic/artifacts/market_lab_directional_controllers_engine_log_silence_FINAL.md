# Engine Log Silence — FINAL

**Date**: 2026-04-17

## Test Counts

| Stage | Passed | Skipped | Failed |
|---|---|---|---|
| Baseline (after phase-2-delta) | 1251 | 58 | 0 |
| After engine log silence | **1252** | 58 | 0 |

Net: **+1 passing test** (the new silence contract). No regressions.

## Files Modified

Only `pmm_lab/sim/engine.py`. Three deletions; no additions.

### Pre-deletion content (5 matched lines)
```
 51:        self._warned_no_orders = False
303:        self._warned_no_orders = False
651:                if placed == 0 and not self._warned_no_orders:
652:                    self._warned_no_orders = True
654:                        "Bar %d: no orders placed (this warning will not repeat)", bar
```

### Deletions

1. **Line 51** (`__init__`):
   ```python
           self._warned_no_orders = False
   ```

2. **Line 303** (top of `run()`):
   ```python
           self._warned_no_orders = False
   ```

3. **Lines 651–655** (the full warning block):
   ```python
                   if placed == 0 and not self._warned_no_orders:
                       self._warned_no_orders = True
                       logger.warning(
                           "Bar %d: no orders placed (this warning will not repeat)", bar
                       )
   ```

No `pass`, no replacement comment, no DEBUG-level shim. The surrounding
control flow is intact.

### Verification grep (post-deletion)
```
$ grep -n "_warned_no_orders\|no orders placed" pmm_lab/sim/engine.py
(no matches)
```

## Tests Added

- `tests/unit/test_engine_no_orders_log_silenced.py` — 1 test
  (`test_engine_does_not_emit_no_orders_warning`). Uses `caplog` at DEBUG
  level on the `pmm_lab.sim.engine` logger so a demotion-to-DEBUG would
  still fail; the contract is **absence of the record**, not just
  "silent at WARNING."

Test result: **1 passed**.

## Acceptance Criteria

- [x] Baseline passing count met/exceeded: 1251 → 1252 (net +1).
- [x] New test passes.
- [x] All previously-passing engine tests still pass; no indirect impact.
- [x] `grep -n "_warned_no_orders\|no orders placed" pmm_lab/sim/engine.py`
  returns zero matches.
- [x] No strategy, canonicalizer, search space, stress, exporter,
  objective_wrapper, notebook, YAML, or `hummingbot/` file modified.
- [x] No root-logger / package-level log config changed.
- [x] No suppression filter or context manager added.

## Escalations

None.

## Status: COMPLETE
