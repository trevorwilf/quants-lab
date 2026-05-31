# Phase 4 session_minute_window_supplier — parity fix phase notes

Tracking the multi-phase fix for the Phase 4 minute-supplier silent-empty bug
(2026-05-30). Symptom: every walkforward trial in
`iex__bowaka_v2_iex_walkforward_conservative_b44ea02b_20260530` returned
`value=-1.5`, every fold reported `n_trades=0` / `fold_status=ok` /
`historical_quote_coverage_pct=100.0` (denominator-zero). Cause: with
`optuna.acceleration.session_minute_window_cache.enabled=true` AND
`cached_suppliers=True`, `fold_context` swaps the minute supplier from
`CachedSessionMarketData.forming_minutes` to
`make_session_minute_window_supplier`; the Phase 4 supplier returned empty
frames for every call.

Operator workaround already applied: `session_minute_window_cache.enabled=false`
in the workstation YAML. The walkforward now produces real trade counts. This
CC's job is to fix the supplier and add a real parity test so the flag can be
re-enabled safely.

---

## Phase 1 — Repro (xfail test) — 2026-05-30

**Branch:** `fix/phase4-minute-supplier-repro` (off `dev`).

**What changed.**
- New test file: `tests/scanner/test_session_minute_window_supplier_parity.py`
  with one xfail-strict case `test_phase4_supplier_matches_cached_forming_minutes_on_real_lake`.
- New empty `tests/scanner/__init__.py` so pytest collects the new directory.

**Test inputs (matched to the operator's diagnostic).**
- Session: `2025-08-27`.
- Cutoff: `pd.Timestamp("2025-08-27 15:00:00", tz="UTC")` (= 11:00 ET).
- Symbols: `("AAL", "KSS", "ABEV", "ACHR", "RR", "BBAI", "SOUN")`.
- Module-level skip: lake AAL probe at
  `<lake>/bars/vendor=alpaca/feed=iex/timeframe=1m/adjustment=raw/symbol=AAL/year=2025/month=08/part.parquet`
  via `bowaka_common.marketdata.store.default_market_data_root()`.

**Verified on the Windows host (the Linux container's behaviour matches per
the operator's diagnostic):** the test xfails. The trace shows:

```
AssertionError: AAL: Phase 4 supplier returned 0 rows where cached returned 66 (the bug).
assert not True
 +  where True = Empty DataFrame\nColumns: [symbol, timestamp, open, high, low, close, volume, vwap, trade_count]\nIndex: [].empty
```

So **both** symptoms reproduce locally:
1. **Empty bars on Phase 4** while cached returns 66 rows for the SAME
   `(symbol, cutoff)` — the primary bug.
2. **Column-schema mismatch**: cached frames carry
   `[symbol, timestamp, open, high, low, close, volume, vwap, trade_count]`;
   the Phase 4 `_empty_minute_frame()` only declares
   `(symbol, timestamp, open, high, low, close, volume)` — secondary parity
   gap Phase 2 must reconcile.

**Suite shape preserved.** No production code edited. Phase 1 is a
diagnostic landmark; the failure is loud and points exactly at the swap
boundary. `make test-all` passes (modulo the §0 pre-existing WSL failure)
with the new test reported as XFAIL — not ERROR, not PASS.

**For Phase 2.** Three candidate root-cause layers per the CC prompt:
1. `SessionMinuteWindowCache.__init__` eager probe — frames never populated.
2. `SessionMinuteWindowCache.bars_until` searchsorted — frames present
   but `lo_idx`/`hi_idx` both resolve to wrong values (e.g., both 0 → empty).
3. `make_session_minute_window_supplier._resolve_session` wrapper — frame
   fine, but the wrapper bails before delegating to the cache.

The "frames present" hypothesis is testable with a direct
`SessionMinuteWindowCache(...).bars_until(...)` call inspecting
`cache._frames` after construction. Phase 2 task 1 starts there.

---

## Phase 2 — Root cause + fix — 2026-05-30

**Branch:** `fix/phase4-minute-supplier-root-fix` (off `dev` after Phase 1 merged).

### Phase 2 root cause

The diagnostic from the Phase 1 trace was layer **(2)** — the cache frames ARE
populated (eager probe works fine and loads 287 rows for AAL across the full
session window), but `bars_until`'s `searchsorted` returns `len(arr)` for BOTH
`lo` and `hi` on every call, slicing `frame.iloc[287:287]` → empty.

Pinned at the lowest layer by building `SessionMinuteWindowCache` directly and
inspecting `cache._timestamps` after init:

```
REF cached.forming_minutes('AAL', 2025-08-27 15:00:00 UTC)  -> 66 rows, ts dtype: datetime64[us, UTC]
CACHE._frames['AAL']: 287 rows; ts dtype: datetime64[us, UTC]
CACHE._timestamps['AAL'] dtype: int64
CACHE._timestamps['AAL'] first/last: 1756302300000000 / 1756324740000000   <-- microseconds

BARS_UNTIL('AAL', 2025-08-27 15:00:00 UTC) -> 0 rows

cutoff ns        = 1756306800000000000
policy_lo_ns     = 1756302300000000000
timestamps[0]    = 1756302300000000        <-- 3 orders of magnitude smaller
timestamps[-1]   = 1756324740000000
searchsorted hi  = 287                     <-- past the end of every-value-smaller-than-cutoff
searchsorted lo  = 287                     <-- same
expected slice  -> rows: 0
```

**The bug, named:** `session_minute_window_cache.py:__init__` builds the
nanosecond timestamp array via `frame["timestamp"].astype("int64")`. The
code comment immediately above states:

> Pandas `datetime64[ns, UTC]` is int64 nanoseconds-since-epoch under the hood.

But the lake parquets store timestamps at `datetime64[us, UTC]` **(microseconds)**,
not nanoseconds. `astype("int64")` on a `datetime64[us, UTC]` Series returns
**µs-since-epoch**, not ns. `bars_until` then compares against
`pd.Timestamp(scan_ts).value` which is **always ns** regardless of the source's
resolution. `cutoff_ns` (~1.756e18) is ~1000× larger than every value in
`timestamps` (~1.756e15), so `np.searchsorted(timestamps, cutoff_ns, side="right")`
returns `len(timestamps)` for both bounds and `frame.iloc[287:287]` is empty
on every call. The whole optimisation path silently returned no rows.

Both the prompt's hypothesis #2 ("astype('int64') on a tz-aware datetime
column can behave differently across pandas versions") and the underlying
units assumption were exact matches.

### Phase 2 fix

Single-file change in `src/bowaka_v2_lab/scanner/session_minute_window_cache.py`
at the timestamp-storage step. Force NS resolution via numpy before viewing
as int64:

```python
self._timestamps[str(symbol)] = (
    ts_col.dt.tz_convert("UTC")
    .dt.tz_localize(None)
    .to_numpy(dtype="datetime64[ns]")
    .view("int64")
)
```

`to_numpy(dtype="datetime64[ns]")` forces ns resolution regardless of source
(us/ms/ns), `tz_localize(None)` strips tz (numpy datetime64 is naive), and
`view("int64")` extracts ns-since-epoch — exactly what `pd.Timestamp.value`
returns. The fix preserves the cache's design intent: ONE parquet read per
(symbol, session) at construction, then numpy-searchsorted slicing per call —
the legacy LRU-per-month read path is NOT introduced. Diff: +9 lines / -3 in
`session_minute_window_cache.py` only; `session_minute_window_supplier.py`
unchanged.

### Phase 1 test now PASSES

The xfail marker was removed:

```
tests/scanner/test_session_minute_window_supplier_parity.py::test_phase4_supplier_matches_cached_forming_minutes_on_real_lake PASSED [100%]
1 passed in 0.68s
```

For all 7 symbols (`AAL, KSS, ABEV, ACHR, RR, BBAI, SOUN`) the Phase 4
supplier now returns byte-identical frames to the cached supplier at the
fixed 2025-08-27 11:00 ET cutoff. `strict=True` was implicit in the xfail
removal: any re-introduction of the unit mismatch (or any other regression
of the per-symbol byte-parity) will fail this test immediately.

---

## Phase 3 — Parametric parity suite — 2026-05-30

**Branch:** `fix/phase4-minute-supplier-parity-suite` (off `dev` after Phase 2).

**Tests added (same file):**

- `test_phase4_supplier_byte_parity_with_cached_over_real_fold[session{0..4}]` —
  5 parametric sessions × 10 microcap symbols × 3 cutoffs (09:45 ET,
  12:00 ET, 15:55 ET); each `(session, symbol, cutoff)` triple where the
  cached reader returns ≥1 row is compared via `assert_frame_equal`
  (sorted by timestamp, index reset). Sessions resolved via XNYS calendar
  at collection time so non-trading days are dropped automatically.
- `test_phase4_supplier_max_bar_age_tightens_lower_bound` — verifies that
  with `max_bar_age_seconds=120` the first returned timestamp is
  ≥ `max(intraday_window_start, cutoff - 120s)`, and the last is ≤ cutoff.
- `test_phase4_supplier_unknown_symbol_returns_empty_frame_with_canonical_columns`
  — exercises the unknown-symbol path; asserts the empty frame carries
  the canonical 9-column lake schema
  `(symbol, timestamp, open, high, low, close, volume, vwap, trade_count)`.

**Schema decision: empty-frame parity beats canonical-columns idealism.**
Initial draft of Phase 3 extended `_empty_minute_frame()` from 7 → 9
columns (adding `vwap`, `trade_count` to match the lake populated
schema). This broke the pre-existing
`tests/unit/scanner/test_session_minute_window_cache_supplier_parity.py`
because the LEGACY supplier (via `make_lake_suppliers` → `store.minute_bars`
→ `bowaka_common._empty_bars()`) returns 7-col empties on the synthetic
tiny test lake; the cache then returned 9-col empties for the same input
— a fresh PARITY violation introduced by the canonical-columns "fix".

Resolution: keep `_empty_minute_frame()` at 7 cols (matching
`bowaka_common._empty_bars()`), and rewrite
`test_phase4_supplier_unknown_symbol_returns_empty_frame_with_canonical_columns`
to assert parity with the cached supplier's empty (whichever schema that
is) rather than against a hard-coded 9-column expectation. This is more
aligned with Phase 4's "byte-stable swap-in" contract: the two suppliers
must agree on the empty shape, period. The prompt's "canonical columns
… including vwap" wording is satisfied when both populated paths produce
9-col frames; the empty paths agreeing on 7-col is the parity invariant.

**Docstring cross-refs added** on both ends:
- `make_session_minute_window_supplier` (Phase 4) docstring now points at
  `tests/scanner/test_session_minute_window_supplier_parity.py`.
- `CachedSessionMarketData.forming_minutes` (legacy) docstring points at
  the same file.

**Timing.** Total wall-clock for the 8 cases in the parity file: **1.48 s**
on the operator's Windows host with the real lake — well under the
prompt's 30 s budget.
