# paper_logs/2024-09-03 — FROZEN synthetic paper-log fixture (Phase 9)

This directory is a frozen, **fully synthetic** paper-trading session log for
the single session ``2024-09-03``. It exists only to exercise the realism
remediation 2 **Phase 9** paper-vs-sim reconciliation framework
(``bowaka_v2_lab.reconcile`` — importer, comparators, calibrators, report).

**This is NOT real paper-trading data.** Phase 9 is scaffolding only — no real
paper logs are supplied. Every value here is hand-authored to be self-
consistent (parent submit → ack → fill → OCO attempt → attach → child fill /
close → EOD summary) and to drive each of the seven Phase-9 comparators.

## Shape (per the prompt's Phase-9 spec)

| Event | Count | Notes |
|---|---|---|
| ``paper_candidate``       | 5  | AAA / BBB / CCC / DDD / EEE |
| ``paper_decision``        | 5  | 3 acceptances (AAA, CCC, DDD), 2 rejections (BBB spread_too_wide, EEE daily_entry_cap) |
| ``paper_parent_submit``   | 3  | one per accepted candidate |
| ``paper_parent_ack``      | 3  | broker acks (150 ms after submit) |
| ``paper_parent_fill``     | 3  | 1 partial (CCC: 120/200), 2 full (AAA: 100, DDD: 150) |
| ``paper_oco_attempt``     | 4  | AAA needs a retry (attempt 1 failure, attempt 2 success); CCC + DDD succeed first try |
| ``paper_oco_attached``    | 3  | one per accepted candidate, after final OCO success |
| ``paper_child_fill``      | 1  | CCC stop-out (1 stop) |
| ``paper_position_close``  | 3  | AAA take-profit (+$61), CCC stop (-$19.20), DDD time_stop (+$12) |
| ``paper_daily_summary``   | 1  | EOD: 3 entries, 3 exits, +$53.80 realized |

## File / kind mapping

Every event ``kind`` maps to one JSONL file in this directory; the importer
:func:`bowaka_v2_lab.reconcile.importer.import_paper_event_logs` reads the set
in one pass and validates each row against its Pydantic model from
:mod:`bowaka_v2_lab.reconcile.paper_log_schema`.

| Kind | File |
|---|---|
| paper_candidate       | ``paper_candidates.jsonl`` |
| paper_decision        | ``paper_decisions.jsonl`` |
| paper_parent_submit   | ``paper_parent_submits.jsonl`` |
| paper_parent_ack      | ``paper_parent_acks.jsonl`` |
| paper_parent_fill     | ``paper_parent_fills.jsonl`` |
| paper_oco_attempt     | ``paper_oco_attempts.jsonl`` |
| paper_oco_attached    | ``paper_oco_attached.jsonl`` |
| paper_child_fill      | ``paper_child_fills.jsonl`` |
| paper_position_close  | ``paper_position_closes.jsonl`` |
| paper_daily_summary   | ``paper_daily_summary.jsonl`` |

Records link by ``candidate_event_id`` and ``parent_order_id``. The candidate
ids use the live ``bowaka_v2:<session>:<symbol>:<ts>`` format.

Do not edit these files casually — the Phase-9 reconciliation tests assert
against their exact contents (especially fill prices for the
intentional-mismatch test in ``tests/integration/``).
