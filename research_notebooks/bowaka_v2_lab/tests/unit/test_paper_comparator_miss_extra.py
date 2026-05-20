"""sim has 3 candidates, paper has 2 → 1 extra; 1 paper has no sim match → 1 miss."""
from __future__ import annotations

from bowaka_v2_lab.reconcile.comparator import compare_candidates


def test_miss_and_extra() -> None:
    paper = [
        {"event_id": "p1", "symbol": "AAA", "scan_timestamp": "2024-09-04T14:00:00Z"},
        {"event_id": "p2", "symbol": "BBB", "scan_timestamp": "2024-09-04T14:01:00Z"},  # no sim match
    ]
    sim = [
        {"event_id": "s1", "symbol": "AAA", "scan_timestamp": "2024-09-04T14:00:05Z"},
        {"event_id": "s2", "symbol": "CCC", "scan_timestamp": "2024-09-04T14:02:00Z"},  # no paper match
        {"event_id": "s3", "symbol": "DDD", "scan_timestamp": "2024-09-04T14:03:00Z"},  # no paper match
    ]
    r = compare_candidates(paper, sim, window_seconds=60)
    assert r.n_match == 1
    assert r.n_miss == 1
    assert r.n_extra == 2
