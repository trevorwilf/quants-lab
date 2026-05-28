"""Phase 3 — rejection-counts parity under collect_gate_dump=False.

With ``collect_gate_dump=False`` (the objective-minimal path), the bounded
``rejection_counts`` totals across a full session must match exactly
between the legacy and compatibility paths.
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat


def test_rejection_counts_match_over_session(matrix_parity) -> None:
    fx = matrix_parity
    state_leg: dict = {}
    state_cmp: dict = {}
    counts_leg: dict = {}
    counts_cmp: dict = {}
    for ts in fx.scan_times:
        r_leg = evaluate_one_scan(
            cfg=fx.cfg, universe_snapshot=fx.universe, daily_cache=fx.daily_cache,
            volume_curve=None, state=state_leg, scan_ts=ts,
            bars_supplier=fx.bars_supplier, scan_context=fx.scan_context,
            collect_gate_dump=False,
        )
        r_cmp = evaluate_one_scan_compat(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state=state_cmp, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None,
            collect_gate_dump=False,
        )
        assert r_leg.gate_dump == []
        assert r_cmp.gate_dump == []
        for k, v in r_leg.rejection_counts.items():
            counts_leg[k] = counts_leg.get(k, 0) + int(v)
        for k, v in r_cmp.rejection_counts.items():
            counts_cmp[k] = counts_cmp.get(k, 0) + int(v)
    assert counts_leg == counts_cmp
