# Phase 6 — Lazy event scheduling scaffolding (default off, RUNTIME-REFUSED)

Speedup report §6.3.

## What landed (scaffolding only)

- **`CadenceConfig.cadence_strategy: str = "preload"`** — new field; parsed
  from `cfg.session.cadence_strategy` or `cfg.simulation.cadence_strategy`.
  Valid values: `"preload"` (default) and `"lazy"`.
- **`preload_session_events_lazy(...)`** (new):
  Returns ONLY SCAN events and EOD_MARK for the session. No
  PROTECTION_CHECK / QUOTE / TIME_STOP_CHECK events are emitted at
  session start; the lazy dispatcher would materialise them from
  handlers on demand.
- **`next_tick_at_or_after(ts, interval_seconds, *, anchor=...)`** —
  helper computing the next cadence-aligned tick. The handler hooks
  would use this to schedule the next PROTECTION_CHECK / QUOTE /
  TIME_STOP_CHECK from the dispatcher.
- **Backtester runtime guard.** `run_backtest` reads
  `cadence.cadence_strategy` and **raises `RuntimeError` when set to
  `"lazy"`** — the on-demand handler hooks that schedule
  PROTECTION_CHECK / QUOTE / TIME_STOP_CHECK events from inside
  ``_handle_protection_check`` / ``_handle_quote_fill_poll`` /
  ``_handle_time_stop_check`` are NOT wired in this build. The flag
  documents intent; honouring it requires the Phase 6 parity matrix
  proving identical FoldResults to preload mode (13 cases:
  no-positions, one-parent-order-fills-at-poll-boundary,
  parent-order-times-out, oco-attach-fail-once-recovers,
  halt-during-unprotected-state, same-minute-stop-and-target,
  max-hold-exit-at-session-open, time-stop-at-configured-exit-time,
  daily-stopout-caps, multiple-lots-same-symbol,
  same-timestamp-event-ordering, signal-fade-exit, full-session-
  random-seed-walkthrough).

## Why ship as scaffolding

The Phase 6 prompt explicitly calls this out as the highest-proof-burden
phase with the wording "Default off. Highest proof burden — only the
parity matrix below justifies merging it." Wiring the on-demand handler
hooks across `sim/event_loop.py` and the dispatch loop in
`sim/backtester.py` (lines ~1080+) and then proving 13 full-backtest
parity matches against the preload variant is a multi-day deep refactor.

The scaffolding committed here:
* declares the public API the future implementation will use,
* keeps the legacy behaviour intact in EVERY existing run,
* refuses the opt-in at runtime so a careless flag flip cannot ship a
  half-implemented lazy scheduler,
* leaves the failing-closed parity test file location documented
  (`tests/parity/test_lazy_event_scheduling_parity.py`) for the next
  worker to fill in.

## New tests

- `tests/unit/sim/test_cadence_strategy.py` (9): flag parse paths, lazy
  preload emits only SCAN+EOD, full preload emits every event type, the
  next-tick helper aligns to the cadence grid, and the backtester
  refuses the lazy opt-in at runtime.

## Result

`make test`: **1238 passed, 2 skipped, 12 deselected** (10:06). The 2
skipped are the Phase 5 PostgreSQL-gated tests.

## Branch

`feature/phase-6-lazy-events` merged to `dev` with `--no-ff`. Phase 7
takes off from `dev` next.
