"""Phase 4 — three-way one-scan parity (legacy == compatibility == vectorized).

Speedup report v2 §10.6 task 1. For a grid of scan timestamps, all three
evaluators must produce identical emitted-event lists, scanner state,
rejection counts, and gate_dump (under collect_gate_dump=True).
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat
from bowaka_v2_lab.scanner.scan_matrix_vectorized import (
    evaluate_one_scan_vectorized,
)


def _emits(result):
    return [(e["symbol"], e["candidate_rank"], e["event_id"]) for e in result.emitted]


def test_three_way_one_scan_parity(matrix_parity) -> None:
    fx = matrix_parity
    scans = fx.scan_times
    idxs = sorted({0, len(scans) // 2, len(scans) - 1})
    for i in idxs:
        ts = scans[i]
        s_leg: dict = {}
        s_cmp: dict = {}
        s_vec: dict = {}
        r_leg = evaluate_one_scan(
            cfg=fx.cfg, universe_snapshot=fx.universe, daily_cache=fx.daily_cache,
            volume_curve=None, state=s_leg, scan_ts=ts,
            bars_supplier=fx.bars_supplier, scan_context=fx.scan_context,
            collect_gate_dump=True,
        )
        r_cmp = evaluate_one_scan_compat(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state=s_cmp, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None, collect_gate_dump=True,
        )
        r_vec = evaluate_one_scan_vectorized(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state=s_vec, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None, collect_gate_dump=True,
        )
        assert _emits(r_leg) == _emits(r_cmp) == _emits(r_vec), f"emit mismatch at {ts}"
        assert (
            dict(r_leg.rejection_counts)
            == dict(r_cmp.rejection_counts)
            == dict(r_vec.rejection_counts)
        )
        assert r_leg.gate_dump == r_cmp.gate_dump == r_vec.gate_dump, ts
        assert s_leg == s_cmp == s_vec, f"state mismatch at {ts}"
