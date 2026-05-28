"""Phase 3 — BOWAKA_MATRIX_RUNTIME_ASSERT debug parity check.

When the env var is set, the compatibility evaluator re-runs the legacy
aggregator on the same bars and compares dict-for-dict to the matrix
reconstruction. On the matched fixture supplier this passes silently; the
check is a forensic backstop, not a production path.
"""
from __future__ import annotations

import os

from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat


def test_debug_assert_passes_on_matched_supplier(matrix_parity, monkeypatch) -> None:
    monkeypatch.setenv("BOWAKA_MATRIX_RUNTIME_ASSERT", "1")
    fx = matrix_parity
    # The fixture's bars_supplier returns the SAME window the matrix builder
    # consumed, so the debug comparison must pass for every scan.
    for ts in fx.scan_times:
        evaluate_one_scan_compat(
            cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
            state={}, scan_context=fx.scan_context,
            universe_snapshot=fx.universe, volume_curve=None,
            collect_gate_dump=False,
            debug_bars_supplier=fx.bars_supplier,
        )


def test_debug_assert_disabled_by_default(matrix_parity) -> None:
    # No env var set — the debug supplier is ignored, no exception.
    os.environ.pop("BOWAKA_MATRIX_RUNTIME_ASSERT", None)
    fx = matrix_parity
    ts = fx.scan_times[0]
    evaluate_one_scan_compat(
        cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
        state={}, scan_context=fx.scan_context,
        universe_snapshot=fx.universe, volume_curve=None,
        collect_gate_dump=False,
        debug_bars_supplier=None,
    )
