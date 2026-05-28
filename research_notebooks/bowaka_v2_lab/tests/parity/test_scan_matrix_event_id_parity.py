"""Phase 3 — emitted event_id parity.

Emitted candidate ``event_id`` values must be identical across the legacy
and compatibility paths. Event IDs come from ``build_candidate_event`` /
``make_event_id`` — since compatibility mode calls the same builder, this is
a backstop against accidentally reordering the event-builder inputs.
"""
from __future__ import annotations

from bowaka_v2_lab.scanner.scan_loop import evaluate_one_scan
from bowaka_v2_lab.scanner.scan_matrix_runtime import evaluate_one_scan_compat


def test_event_ids_match_over_session(matrix_parity) -> None:
    fx = matrix_parity
    state_leg: dict = {}
    state_cmp: dict = {}
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
        assert [e["event_id"] for e in r_leg.emitted] == [
            e["event_id"] for e in r_cmp.emitted
        ], f"event_id mismatch at {ts}"
