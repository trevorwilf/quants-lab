"""Gate funnel — counts of candidates by stage / failing gate / symbol / date."""
from __future__ import annotations

from collections import Counter
from typing import Iterable

import pandas as pd


def gate_funnel_by_date_symbol(candidate_events: list[dict]) -> pd.DataFrame:
    """Per (session_date, symbol): how many candidates emitted, breakdown by gate pass/fail."""
    rows = []
    for ev in candidate_events:
        gates = ev.get("gate_results") or {}
        rows.append({
            "session_date": ev.get("session_date"),
            "symbol": ev.get("symbol"),
            "all_pass": all(gates.values()) if gates else False,
            "failing_gates": sum(1 for v in gates.values() if not v),
        })
    return pd.DataFrame(rows)


def top_failure_reasons(gate_dump_rows: list[dict], *, top_n: int = 10) -> list[tuple[str, int]]:
    """Most common single-gate failures across the dump."""
    cnt: Counter = Counter()
    for row in gate_dump_rows:
        for g in (row.get("failing_gates") or []):
            cnt[g] += 1
    return cnt.most_common(top_n)
