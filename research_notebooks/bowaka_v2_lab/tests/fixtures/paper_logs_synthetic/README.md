# paper_logs_synthetic — FROZEN synthetic paper-log fixture

This directory is a **frozen, fully synthetic** paper-trading session log for
the single session `2024-09-04`. It exists only to exercise the Phase-10
paper-vs-lab reconciliation framework (`bowaka_v2_lab.reconcile.replay` /
`comparators` / `report` and the `reconcile` CLI command) end-to-end.

**This is NOT real paper-trading data.** Phase 10 is scaffolding only — no real
paper logs are supplied. Every value here is hand-authored to be self-consistent
and to drive the reconciliation comparators, not to represent a real session.

## Files (one JSONL record per line)

| File | Records |
|---|---|
| `candidate_events.jsonl` | candidate-signal events |
| `entry_decisions.jsonl`  | entry decisions (accepted / rejected + reason) |
| `orders.jsonl`           | parent orders |
| `fills.jsonl`            | order fills |
| `exits.jsonl`            | per-lot exits (reason + realized PnL) |
| `brackets.jsonl`         | OCO bracket definitions |
| `quotes.jsonl`           | quote snapshots at scan time |
| `state.json`             | fixture metadata |

Records link by `candidate_event_id` (the candidate the downstream record
descends from) and `parent_order_id`. The candidate ids use the live
`bowaka_v2:<session>:<symbol>:<ts>` format.

Do not edit these files casually — the reconcile tests assert against their
exact contents.
