"""Phase 7: event_key + dedup behavior."""

from __future__ import annotations

import pandas as pd

from bowaka_lab.reconcile.event_normalizer import event_key, normalize_paper_events


def test_event_key_stable_across_runs():
    e = {
        "event_type": "order_filled",
        "trade_id": "BOWAKA-AAA-1001",
        "order_id": "T-1",
        "ts": "2026-05-11T17:30:00+00:00",
        "status": "FILLED",
        "filled_qty": 1000,
        "fill_price": 5.76,
    }
    assert event_key(e) == event_key(e)


def test_dedup_removes_duplicate_rows():
    df = pd.DataFrame(
        [
            {"event_type": "order_filled", "trade_id": "T1", "order_id": "O1", "ts": "x", "status": "FILLED", "filled_qty": 1, "fill_price": 1.0},
            {"event_type": "order_filled", "trade_id": "T1", "order_id": "O1", "ts": "x", "status": "FILLED", "filled_qty": 1, "fill_price": 1.0},
        ]
    )
    out = normalize_paper_events(df)
    assert out.shape[0] == 1


def test_normalize_distinct_events_kept():
    df = pd.DataFrame(
        [
            {"event_type": "order_filled", "trade_id": "T1", "order_id": "O1", "ts": "x", "status": "FILLED", "filled_qty": 1, "fill_price": 1.0},
            {"event_type": "order_canceled", "trade_id": "T1", "order_id": "O1", "ts": "y", "status": "CANCELED", "filled_qty": 0, "fill_price": None},
        ]
    )
    out = normalize_paper_events(df)
    assert out.shape[0] == 2
