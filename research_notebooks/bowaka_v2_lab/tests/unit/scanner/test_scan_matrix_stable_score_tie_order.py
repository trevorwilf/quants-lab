"""``np.argsort(-scores, kind="stable")`` mirrors the legacy passing sort.

Matrix doc §17.3. The matrix-backed scanner must use a STABLE sort to
preserve the same ranking the legacy ``passing.sort(key=lambda x: -x[0])``
produced for identical scores.
"""
from __future__ import annotations

import numpy as np


def test_stable_argsort_matches_python_sorted_descending():
    scores = np.array([0.5, 0.7, 0.5, 0.3, 0.7, 0.5], dtype=np.float64)
    symbols = ["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"]

    # Legacy: list of (score, symbol) sorted by -score.
    legacy = sorted(zip(scores, symbols), key=lambda x: -x[0])
    legacy_order = [sym for _, sym in legacy]

    # Matrix: argsort(-scores, kind="stable").
    order = np.argsort(-scores, kind="stable")
    matrix_order = [symbols[i] for i in order]

    assert legacy_order == matrix_order


def test_argsort_stable_preserves_index_order_for_ties():
    """For perfectly tied scores the original index order is preserved."""
    scores = np.array([1.0, 1.0, 1.0], dtype=np.float64)
    order = np.argsort(-scores, kind="stable")
    assert list(order) == [0, 1, 2]
