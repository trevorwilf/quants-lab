"""Phase 3 — tie-order parity on equal scores.

The tiny-lake builder writes IDENTICAL flat OHLCV for every symbol, so a
two-symbol lake produces two candidates with identical signal scores. Both
the legacy scanner and the compatibility runtime use a STABLE descending
sort (``passing.sort(key=lambda x: -x[0])``), so the emitted order must
follow the eligible-symbol iteration order (AAA before BBB) identically.
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat
from tests.fixtures.scan_matrix_parity import build_matrix_parity_fixture


def test_tie_order_preserved_between_paths(tmp_path, lab_root) -> None:
    fx = build_matrix_parity_fixture(
        tmp_path, lab_root, symbols=["AAA", "BBB"],
    )
    # Use a scan with both symbols present (mid session).
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
        universe_snapshot=fx.universe, volume_curve=None,
        collect_gate_dump=False,
    )
    leg_syms = [e["symbol"] for e in r_leg.emitted]
    cmp_syms = [e["symbol"] for e in r_cmp.emitted]
    # If both symbols passed gates (flat fixture should pass or fail
    # identically), the emitted order is identical between paths.
    assert leg_syms == cmp_syms
    # When two candidates emit, they must be in the eligible-symbol order.
    if len(cmp_syms) == 2:
        assert cmp_syms == sorted(cmp_syms), (
            "tie-order not stable: expected eligible-symbol order on equal scores"
        )
