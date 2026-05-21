# Phase 4 summary — Full intraday scanner replay

**Branch:** `phase-4-realism-intraday-replay` (off `dev`)
**Audit refs:** P0-003, P0-006, §11 Phase 4, Ticket 3.
**Status:** complete, merged to `dev`.

## What shipped

- **`sim/schedule.py`** — `scan_times_for_session(session_date, cfg)`:
  XNYS-calendar-aware intraday scan schedule. Returns `[]` for holidays/weekends;
  honors early closes (truncates `scanner_end` to the early close); DST-correct
  via `tz_convert`. Replaces the one-scan-per-session lambda hard-coding 14:00
  UTC, wired into `cli_runners.py`, `sim/backtester.py`, `backtest_runner.py`,
  `optuna/walkforward_runner.py`.
- **`IntradayWindowPolicy`** — `data/suppliers.py` honors
  `simulation.intraday_window_policy`: `scanner_start_to_scan` (09:45→scan),
  `regular_open_to_scan` (09:30→scan), `extended_hours_to_scan` (04:00→scan).
- **Full per-scan pipeline** — every scan timestamp runs the full pipeline for
  every eligible PIT-universe symbol; caps `max_candidates_per_scan` /
  `max_entries_per_scan`; cross-scan dedup via `signal_expiry_seconds`,
  `same_symbol_entries_per_day`, `symbol_cooldown_minutes` (session-reset state).
- **Stale-bar rejection** — last minute bar older than `max_bar_age_seconds` from
  scan_ts → `stale_bar`.
- **Gate dump** — one row per `(scan_ts, symbol)` in `gate_dump.parquet` (flat
  `scan_ts, score, rank, candidate_emitted, rejection_reason` + gate flags);
  large dumps additionally partitioned per session under
  `scanner/gate_dump_by_session/`.
- **Scan counts** — `run_manifest.json["scan_counts"]`: expected/actual scans,
  candidate/accepted counts, gate-rejection breakdown per session.

## Files

Code: `sim/schedule.py` (new); `sim/backtester.py`, `cli_runners.py`,
`backtest_runner.py`, `optuna/walkforward_runner.py`, `data/suppliers.py`,
`scanner/scan_loop.py`, `scanner/replay.py`. Config: `bowaka_v2_backtest_smoke.yml`
(coarse smoke interval). Doc: `docs/current_code_vs_intended_realism.md` (early-close note).
Tests: 9 added (`tests/unit/test_schedule_{normal_day,early_close,holiday,dst}.py`,
`test_intraday_window_policy.py`, `test_stale_bar_rejected.py`;
`tests/integration/test_{full_scan_replay,signal_appears_intraday}.py`;
`tests/parity/test_scan_count_per_session.py`).

**Result:** 452 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| Backtester replays every configured scan timestamp per session | PASS |
| `run_manifest.json` scan counts / cadence; non-empty `gate_dump.parquet` | PASS |
| Intraday window policy honored per simulation mode | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- **Early-close deviation from live:** the live scanner builds its loop bound
  purely from `scanner_end` and never consults the exchange calendar — on an
  early-close day it would tick past the real close. `scan_times_for_session`
  deliberately truncates to `min(scanner_end, early_close)` (unconditional —
  scanning a closed market is never correct). Documented in
  `docs/current_code_vs_intended_realism.md` §5.
- **Runtime:** full replay is ~346 scans/session (60s cadence) vs 1 before. The
  `smoke_fixture` config uses a coarse 900s interval (~24 scans) to keep the
  suite fast; `scan_times_for_session` still produces the real 60s cadence and
  tests verify the 346-scan count directly. Suite runs in ~130s.
