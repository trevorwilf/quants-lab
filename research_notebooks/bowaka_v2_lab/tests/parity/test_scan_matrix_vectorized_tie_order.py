"""Phase 4 — three-way tie-order parity on equal scores.

A two-symbol tiny lake produces identical scores (flat fixture). Legacy,
compatibility, and vectorized must all preserve eligible-symbol order on
the tie (AAA before BBB), by virtue of the stable sort.
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat
from bowaka_v2_lab.scanner.scan_matrix_vectorized import (
    evaluate_one_scan_vectorized,
)
from tests.fixtures.scan_matrix_parity import build_matrix_parity_fixture


def test_three_way_tie_order(tmp_path, lab_root) -> None:
    fx = build_matrix_parity_fixture(tmp_path, lab_root, symbols=["AAA", "BBB"])
    ts = fx.scan_times[len(fx.scan_times) // 2]
    r_leg = evaluate_one_scan(
        cfg=fx.cfg, universe_snapshot=fx.universe, daily_cache=fx.daily_cache,
        volume_curve=None, state={}, scan_ts=ts,
        bars_supplier=fx.bars_supplier, scan_context=fx.scan_context,
        collect_gate_dump=False,
    )
    r_cmp = evaluate_one_scan_compat(
        cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
        state={}, scan_context=fx.scan_context,
        universe_snapshot=fx.universe, volume_curve=None, collect_gate_dump=False,
    )
    r_vec = evaluate_one_scan_vectorized(
        cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
        state={}, scan_context=fx.scan_context,
        universe_snapshot=fx.universe, volume_curve=None, collect_gate_dump=False,
    )
    leg = [e["symbol"] for e in r_leg.emitted]
    cmp = [e["symbol"] for e in r_cmp.emitted]
    vec = [e["symbol"] for e in r_vec.emitted]
    assert leg == cmp == vec
    if len(vec) == 2:
        assert vec == sorted(vec), "vectorized tie-order not stable"
