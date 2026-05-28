"""Phase 3 — one-scan compatibility-runtime parity vs legacy evaluate_one_scan.

Speedup report v2 §10.5. For a grid of scan timestamps drawn from the
fixture session, the matrix compatibility evaluator must produce a
:class:`ScanResult` field-by-field equal to the legacy
``evaluate_one_scan``: same emitted symbols / order / scores / event IDs /
candidate ranks, same rejection counts, same scanner state after the call,
and a byte-equal gate_dump under ``collect_gate_dump=True``.
"""
from __future__ import annotations

import pandas as pd

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat


def _emit_tuples(result):
    return [
        (e["symbol"], e["candidate_rank"], round(float(e["features"]["signal_strength"]), 12), e["event_id"])
        for e in result.emitted
    ]


def test_one_scan_emitted_events_match(matrix_parity) -> None:
    fx = matrix_parity
    # Sample first / middle / last scan timestamps.
    scans = fx.scan_times
    idxs = sorted({0, len(scans) // 2, len(scans) - 1})
    for i in idxs:
        ts = scans[i]
        state_leg: dict = {}
        state_cmp: dict = {}
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
        assert _emit_tuples(r_leg) == _emit_tuples(r_cmp), f"emit mismatch at {ts}"
        assert dict(r_leg.rejection_counts) == dict(r_cmp.rejection_counts), ts
        assert state_leg == state_cmp, f"state mismatch at {ts}"


def test_one_scan_gate_dump_byte_equal(matrix_parity) -> None:
    fx = matrix_parity
    ts = fx.scan_times[len(fx.scan_times) // 2]
    r_leg = evaluate_one_scan(
        cfg=fx.cfg, universe_snapshot=fx.universe, daily_cache=fx.daily_cache,
        volume_curve=None, state={}, scan_ts=ts,
        bars_supplier=fx.bars_supplier, scan_context=fx.scan_context,
        collect_gate_dump=True,
    )
    r_cmp = evaluate_one_scan_compat(
        cfg=fx.cfg, matrix_session=fx.matrix_session, scan_ts=ts,
        state={}, scan_context=fx.scan_context,
        universe_snapshot=fx.universe, volume_curve=None,
        collect_gate_dump=True,
    )
    assert r_leg.gate_dump == r_cmp.gate_dump
