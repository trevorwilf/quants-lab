"""Regression lock for the per-trial scan-floor optimization.

`evaluate_one_scan_vectorized` skips the per-cell session_bar/forming-feats
reconstruction for GATE-FAILING symbols when ``collect_gate_dump=False`` (the
objective/per-trial path): those dicts were discarded there, so this is dead-work
elimination, NOT a semantic change. The three-way parity tests guard the
end-to-end result; this pins the skip behaviour directly with a self-contained
1-scan / 1-symbol matrix session (no lake/matrix build), where the symbol clears
the pre-checks and then fails an impossible gate.
"""
from __future__ import annotations

import types

import numpy as np
import pandas as pd

from bowaka_v2_lab.scanner.scan_loop import ScanSkipReason
from bowaka_v2_lab.scanner.scan_matrix import (
    DYNAMIC_FLOAT64_COLUMNS,
    DYNAMIC_INT64_COLUMNS,
    DYNAMIC_UINT8_COLUMNS,
    ScanMatrixSession,
)

_GATE_FAILED = ScanSkipReason.GATE_FAILED.value


def _one_cell_session() -> tuple[ScanMatrixSession, pd.Timestamp]:
    """A matrix session with one scan, one symbol that has a bar + valid ts."""
    scan_ts = pd.Timestamp("2024-05-01 14:00", tz="UTC")
    f64 = {c: np.full((1, 1), np.nan, dtype=np.float64) for c in DYNAMIC_FLOAT64_COLUMNS}
    f64["last_price"][0, 0] = 10.0
    f64["rvol_so_far"][0, 0] = 2.0  # finite -> fails an impossible rvol_so_far_min
    f64["bar_age_seconds"][0, 0] = 0.0
    u8 = {c: np.zeros((1, 1), dtype=np.uint8) for c in DYNAMIC_UINT8_COLUMNS}
    u8["has_bar"][0, 0] = 1
    u8["has_valid_timestamp"][0, 0] = 1
    i64 = {c: np.full((1, 1), -1, dtype=np.int64) for c in DYNAMIC_INT64_COLUMNS}
    i64["last_bar_ts_ns"][0, 0] = (scan_ts - pd.Timedelta(seconds=30)).value
    ms = ScanMatrixSession(
        session_date=scan_ts.date(),
        root=None,
        scan_timestamps_ns=np.array([scan_ts.value], dtype=np.int64),
        symbol_ids=np.array([0], dtype=np.int32),
        dynamic_float64=f64, dynamic_int64=i64, dynamic_uint8=u8,
        static_float64={}, static_int8={},
        universe_meta=pd.DataFrame({"symbol": ["AAA"], "symbol_id": [0]}),
    )
    return ms, scan_ts


def _ctx():
    return types.SimpleNamespace(
        universe_meta_by_sym={"AAA": {"symbol": "AAA", "instrument_class": "operating_equity"}},
        cache_by_sym={"AAA": {
            "avg_dollar_volume_20d": 1.0e6, "prior_atr_pct": 0.02,
            "ema_slope_prior": 0.0, "prior_close": 10.0,
        }},
        config_hash_v="sha256:test",
        volume_curve_fraction_by_scan_bucket={},
    )


def _cfg() -> dict:
    # Impossible rvol minimum -> the single symbol clears the pre-checks then
    # fails the rvol gate. Other gates default-pass (unset thresholds).
    return {
        "signals": {"rvol_so_far_min": 1.0e12},
        "score": {}, "scanner": {}, "market_data": {}, "historical_features": {},
    }


def test_objective_mode_skips_reconstruct_for_gate_failures(monkeypatch) -> None:
    import bowaka_v2_lab.scanner.scan_matrix_runtime as rt
    from bowaka_v2_lab.scanner.scan_matrix_vectorized import evaluate_one_scan_vectorized

    def _boom(*_a, **_k):
        raise AssertionError(
            "per-cell reconstruct called for a gate-failing symbol in objective "
            "mode (collect_gate_dump=False) — the skip optimization regressed"
        )

    monkeypatch.setattr(rt, "_reconstruct_session_bar", _boom)
    monkeypatch.setattr(rt, "_reconstruct_forming_feats", _boom)

    ms, scan_ts = _one_cell_session()
    res = evaluate_one_scan_vectorized(
        cfg=_cfg(), matrix_session=ms, scan_ts=scan_ts, state={},
        scan_context=_ctx(), universe_snapshot={"universe_hash": "sha256:t"},
        collect_gate_dump=False,
    )
    assert res.emitted == [], "nothing may pass an impossible gate"
    assert res.rejection_counts.get(_GATE_FAILED) == 1, (
        f"the symbol must reach + fail the gate; counts={dict(res.rejection_counts)}"
    )
    # If reconstruct had been called, _boom would have raised before we got here.


def test_gate_dump_mode_still_reconstructs(monkeypatch) -> None:
    import bowaka_v2_lab.scanner.scan_matrix_runtime as rt
    from bowaka_v2_lab.scanner.scan_matrix_vectorized import evaluate_one_scan_vectorized

    calls = {"n": 0}
    real = rt._reconstruct_session_bar

    def _counting(*a, **k):
        calls["n"] += 1
        return real(*a, **k)

    monkeypatch.setattr(rt, "_reconstruct_session_bar", _counting)

    ms, scan_ts = _one_cell_session()
    res = evaluate_one_scan_vectorized(
        cfg=_cfg(), matrix_session=ms, scan_ts=scan_ts, state={},
        scan_context=_ctx(), universe_snapshot={"universe_hash": "sha256:t"},
        collect_gate_dump=True,
    )
    assert calls["n"] == 1, "gate_dump mode must reconstruct for the dump row"
    assert any(r.get("skipped") == _GATE_FAILED for r in res.gate_dump)
