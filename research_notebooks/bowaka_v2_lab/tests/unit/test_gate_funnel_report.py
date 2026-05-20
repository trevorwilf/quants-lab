"""Synthetic candidate events → funnel counts match."""
from __future__ import annotations

from bowaka_v2_lab.reports.gate_funnel import gate_funnel_by_date_symbol, top_failure_reasons


def test_gate_funnel_basic() -> None:
    events = [
        {"session_date": "2024-09-04", "symbol": "AAA", "gate_results": {"rvol_gate": True, "ema_distance_gate": True}},
        {"session_date": "2024-09-04", "symbol": "BBB", "gate_results": {"rvol_gate": False, "ema_distance_gate": True}},
        {"session_date": "2024-09-04", "symbol": "CCC", "gate_results": {"rvol_gate": True, "ema_distance_gate": False}},
    ]
    df = gate_funnel_by_date_symbol(events)
    assert len(df) == 3
    assert df["all_pass"].tolist() == [True, False, False]
    assert df["failing_gates"].tolist() == [0, 1, 1]


def test_top_failure_reasons() -> None:
    dump = [
        {"failing_gates": ["rvol_gate"]},
        {"failing_gates": ["rvol_gate", "max_gap_gate"]},
        {"failing_gates": ["max_gap_gate"]},
    ]
    out = top_failure_reasons(dump, top_n=2)
    out_sorted = sorted(out, key=lambda x: (-x[1], x[0]))
    assert out_sorted[0] == ("max_gap_gate", 2)
    assert out_sorted[1] == ("rvol_gate", 2)
