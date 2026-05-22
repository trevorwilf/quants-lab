# Phase 7 summary — Intraday exit lifecycle

**Branch:** `phase-7-realism-intraday-exits` (off `dev`)
**Audit refs:** P0-009, §11 Phase 7, Ticket 9.
**Status:** complete, merged to `dev`.

## What shipped

- **Minute-path per-lot exit lifecycle** (`sim/exits.py` `walk_lot_exit()` +
  `sim/exit_driver.py`) — each open lot is walked over minute bars from the bar
  after fill to the earliest of stop / target / time-stop / max-hold /
  signal-fade. Same-minute stop+target ambiguity resolves via
  `simulation.same_minute_resolution` (`conservative` default → stop wins;
  `optimistic` → target; `random_with_seed` → seeded).
- **Gap-through** — minute open below stop → `gap_stop` at open; open above
  target → `gap_target` at open.
- **Time stop** — at `exits.time_stop.exit_time` (15:45 ET) exit at next bid
  (quote-aware in realism; minute-close in smoke).
- **Max hold** — counts XNYS trading days; holidays inside the window do not
  count; EOD exit at last regular-session close.
- **Signal fade** — re-scores the forming bar at `eval_time`; `telemetry_only`
  records a `FadeTelemetry` would-have-exited event without closing;
  `active` / `telemetry_then_active_after_validation` close the lot. Live
  thresholds `{soft:0.34, hard:0.50, critical:0.67}`, `exit_on:[hard,critical]`.
- **Per-lot exit driving** — `Portfolio` + backtester close by `position_id`;
  daily-bar-only exits retained ONLY for `smoke_fixture` (keeps the smoke suite
  fast); realism/parity use the minute path.
- **Halt/LULD stress** — `cost_stress: severe` models a 60s halt on a bracket
  trip, force-exiting at the next bid after resume (`halt_resume_exit`).
- **Exit-analysis report** (`reports/exit_analysis.py`) — exit-reason
  distribution, exit-slippage-bps distribution, per-trade MFE/MAE, written to
  `exit_analysis.json`, `summary.json`, and `report.md`.

## Files

Code: `sim/exits.py`, `sim/exit_driver.py` (new), `sim/backtester.py`,
`sim/portfolio.py`, `sim/strategy_consumer.py`, `sim/__init__.py`,
`config/models.py` (`same_minute_resolution`), `reports/exit_analysis.py` (new),
`reports/render_run_report.py`. Tests: 11 added
(`test_exit_{stop_first,target_first,same_minute_stop_wins,gap_below_stop,gap_above_target,time_stop,max_hold_trading_days,max_hold_skips_holiday,signal_fade_telemetry,signal_fade_active}.py`,
`test_exit_lifecycle_metrics_in_report.py`).

**Result:** 541 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| Minute-path triggers for all scenarios (stop/target/same-minute/gap) | PASS |
| Time stop, max hold (trading-day), signal fade per live semantics | PASS |
| Daily-bar-only exit allowed only in `smoke_fixture` mode | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- Signal-fade threshold semantics: the contract thresholds are ascending and the
  rule is `score < threshold → exit`; a score below multiple `exit_on`
  thresholds is reported as the tightest (smallest) one it is still below
  (deterministic).
