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
