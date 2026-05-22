# Phase 5 summary — Strategy consumer, portfolio, and risk-state parity

**Branch:** `phase-5-realism-portfolio-and-risk` (off `dev`)
**Audit refs:** P0-007, P0-010, P0-014, §11 Phase 5, Ticket 6.
**Status:** complete, merged to `dev`.

## What shipped

- **Position-id-keyed portfolio** — `Portfolio.open_positions` re-keyed from
  `{symbol → Position}` to `{position_id (UUID) → Position}`. `Position` gained
  `position_id`, `parent_order_id`, `link_id`, `entry_session`, `lot_index`.
  Helpers: `lots_for_symbol`, `symbol_open_notional`, `positions_for_symbol`,
  `close_position_by_id`. `close_position(symbol, …)` kept (deprecated; closes
  the oldest lot). Every symbol-keyed caller updated.
- **Multi-lot per symbol** — re-entry is no longer blocked just because a symbol
  has open lots. `same_symbol_entries_per_day` (per-session set) and
  `max_lots_per_symbol` enforced; rejections `same_symbol_entries_per_day` /
  `max_lots_per_symbol`.
- **Risk-gate parity** — `max_concurrent_positions` read from `sizing` (live
  location); ADV-tier cap applied to the AGGREGATE symbol notional
  (`symbol_open_notional + candidate`); `strategy_slice_loss_pct` kill switch;
  daily entry cap / gross exposure / daily-loss kill / consecutive stopouts.
- **`accepted_event_sequencing`** — `pre_submit` (parity/smoke): `accepted`
  emitted before broker submit, `broker_reject` follow-up on reject;
  `post_submit` (realism): `submitted_pending` then `accepted` only on broker
  confirm. A broker reject never creates a position in either mode.
- **Terminal decision schema** — `TERMINAL_DECISIONS` adds `submitted_pending`,
  `filled`, `partial_fill`, `broker_reject`, `expired`, `canceled`.
- **Session rollover** — `begin_session` recomputes gross exposure +
  `entered_symbols_today` from all open lots / `entry_session`.

## Files

Code: `sim/portfolio.py`, `sim/risk_gates.py`, `sim/strategy_consumer.py`,
`sim/backtester.py`, `sim/exits.py`, `sim/__init__.py`, `schemas/events.py`,
`schemas/decisions.py`, `schemas/__init__.py`. Doc:
`docs/current_code_vs_intended_realism.md` (§6 strategy-slice-loss divergence,
§7 ADV aggregate-cap port). Tests: 9 added (30 cases) —
`test_portfolio_{multi_lot_open,max_lots_per_symbol,same_symbol_entries_per_day,close_individual_lot}.py`,
`test_decision_sequencing_{pre,post}_submit.py`,
`tests/parity/test_{risk_gates_adv_tier_aggregate,risk_max_concurrent_from_sizing,strategy_slice_loss_enforced}.py`.
`test_sim_broker_reject_emits_canonical.py` updated (pre_submit now emits 2
decisions; load-bearing assertions preserved).

**Result:** 482 passed, 1 skipped, 12 deselected (slow/live), 0 failed.
env-check passes on all 5 shipping configs.

## Acceptance criteria

| Criterion | Status |
|---|---|
| Portfolio supports multi-lot; symbol-keyed callers updated | PASS |
| ADV cap parity matches live (aggregate-notional) | PASS |
| Decision sequencing matches mode | PASS |
| Broker reject never creates a position | PASS |
| env-check passes on all shipping configs | PASS (5/5) |

## Notes

- **Live-vs-realism divergence (`docs` §6):** live `_risk_gates` carries
  `strategy_slice_loss_pct` in schema but never consumes it (only `daily_loss_pct`
  fires). The lab enforces it as a distinct kill switch — additive (fires only
  when the key is present), so a `current_code_parity` config that omits it
  reproduces live single-gate behavior.
- `build_broker_reject_record` keeps `decision="rejected", reason="broker_reject"`
  (the established §15.1 contract); `broker_reject` is a `TERMINAL_DECISIONS`
  superset alias. `reason == "broker_reject"` stays the load-bearing field.
