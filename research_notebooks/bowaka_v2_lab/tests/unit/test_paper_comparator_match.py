"""Exact-match case."""
from __future__ import annotations

from bowaka_v2_lab.reconcile.comparator import compare_candidates


def test_exact_match() -> None:
    paper = [{"event_id": "p1", "symbol": "AAA", "scan_timestamp": "2024-09-04T14:00:00Z"}]
    sim = [{"event_id": "s1", "symbol": "AAA", "scan_timestamp": "2024-09-04T14:00:00Z"}]
    r = compare_candidates(paper, sim, window_seconds=10)
    assert r.n_match == 1
    assert r.n_miss == 0
    assert r.n_extra == 0
    assert r.matches[0].match_kind == "match"
    assert r.matches[0].scan_ts_delta_seconds == 0.0
