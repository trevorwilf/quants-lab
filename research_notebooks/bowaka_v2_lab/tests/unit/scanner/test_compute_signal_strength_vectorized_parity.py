"""Phase 4 — compute_signal_strength_vectorized matches the scalar function.

Speedup report v2 §10.6 task 7. Over a randomized grid of 200 synthetic
feature dicts (including None / 0.0 / negative values), the vectorized
score computed over stacked columns must equal the scalar
``compute_signal_strength`` called row-wise, within 1e-12.
"""
from __future__ import annotations

import numpy as np

from bowaka_v2_lab.features import compute_signal_strength
from bowaka_v2_lab.scanner.scan_matrix_vectorized import (
    compute_signal_strength_vectorized,
)


def _rand_or_none(rng, *, none_p=0.15):
    if rng.random() < none_p:
        return None
    return float(rng.normal(0.5, 1.5))


def test_vectorized_score_matches_scalar_grid() -> None:
    rng = np.random.default_rng(7)
    n = 200
    rows = []
    for _ in range(n):
        rows.append({
            "rvol_so_far": _rand_or_none(rng),
            "range_expansion_so_far": _rand_or_none(rng),
            "close_location_so_far": _rand_or_none(rng),
            "ema_distance": _rand_or_none(rng),
            "gap_pct": _rand_or_none(rng),
        })
    es_vals = [(_rand_or_none(rng)) for _ in range(n)]
    score_cfg = {"bounded": True}

    scalar_scores = [
        compute_signal_strength(rows[i], score_cfg, ema_slope_prior=es_vals[i])
        for i in range(n)
    ]

    def col(key):
        return np.array(
            [rows[i].get(key) if rows[i].get(key) is not None else np.nan for i in range(n)],
            dtype=np.float64,
        )

    es_col = np.array(
        [es_vals[i] if es_vals[i] is not None else np.nan for i in range(n)],
        dtype=np.float64,
    )
    vec_scores = compute_signal_strength_vectorized(
        rvol_so_far=col("rvol_so_far"),
        range_expansion_so_far=col("range_expansion_so_far"),
        close_location_so_far=col("close_location_so_far"),
        ema_distance=col("ema_distance"),
        ema_slope_prior=es_col,
        gap_pct=col("gap_pct"),
        score_cfg=score_cfg,
    )
    for i in range(n):
        assert abs(scalar_scores[i] - float(vec_scores[i])) <= 1e-12, (
            i, rows[i], es_vals[i], scalar_scores[i], vec_scores[i]
        )


def test_vectorized_score_matches_scalar_unbounded() -> None:
    rng = np.random.default_rng(11)
    n = 50
    rows = [{
        "rvol_so_far": float(rng.normal()),
        "range_expansion_so_far": float(rng.normal()),
        "close_location_so_far": float(rng.normal()),
        "ema_distance": float(rng.normal()),
        "gap_pct": float(rng.normal()),
    } for _ in range(n)]
    es_vals = [float(rng.normal()) for _ in range(n)]
    score_cfg = {"bounded": False}
    scalar = [
        compute_signal_strength(rows[i], score_cfg, ema_slope_prior=es_vals[i])
        for i in range(n)
    ]
    vec = compute_signal_strength_vectorized(
        rvol_so_far=np.array([r["rvol_so_far"] for r in rows]),
        range_expansion_so_far=np.array([r["range_expansion_so_far"] for r in rows]),
        close_location_so_far=np.array([r["close_location_so_far"] for r in rows]),
        ema_distance=np.array([r["ema_distance"] for r in rows]),
        ema_slope_prior=np.array(es_vals),
        gap_pct=np.array([r["gap_pct"] for r in rows]),
        score_cfg=score_cfg,
    )
    for i in range(n):
        assert abs(scalar[i] - float(vec[i])) <= 1e-12
