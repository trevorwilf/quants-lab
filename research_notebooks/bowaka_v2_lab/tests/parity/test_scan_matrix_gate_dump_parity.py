"""Phase 3 — gate_dump parity under collect_gate_dump=True.

A full-session run in both paths with ``collect_gate_dump=True``: the
gate_dump list of dicts must be deep-equal (same row order, same keys,
same values).
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat


def test_gate_dump_deep_equal_over_session(matrix_parity) -> None:
    fx = matrix_parity
    state_leg: dict = {}
    state_cmp: dict = {}
    for ts in fx.scan_times:
        r_leg = evaluate_one_scan(
            cfg=fx.cfg, universe_snapshot=fx.universe, daily_cache=fx.daily_cache,
            volume_curve=None, state=state_leg, scan_ts=ts,
            bars_supplier=fx.bars_supplier, scan_context=fx.scan_context,
            collect_gate_dump=True,
        )
        r_cmp = evaluate_one_scan_compat(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state=state_cmp, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None,
            collect_gate_dump=True,
        )
        assert r_leg.gate_dump == r_cmp.gate_dump, f"gate_dump mismatch at {ts}"
