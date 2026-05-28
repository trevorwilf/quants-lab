"""Phase 4 — np.argsort(kind="stable") matches Python sorted on ties.

Speedup report v2 §10.6 task 8 / matrix doc §17.3. The vectorized runtime
ranks candidates with ``np.argsort(-scores, kind="stable")``; this must
produce the same ordering as the legacy ``sorted(passing, key=lambda x:
-x[0])`` on the same scalar inputs, including ties (where eligible-symbol
order must be preserved).
"""
from __future__ import annotations

import numpy as np


def _python_order(scores: list[float]) -> list[int]:
    """The legacy ordering: stable sort of (score, original_index) desc."""
    indexed = list(enumerate(scores))
    indexed.sort(key=lambda x: -x[1])  # Python sort is stable
    return [i for i, _ in indexed]


def test_argsort_stable_matches_python_sorted_with_ties() -> None:
    cases = [
        [3.0, 1.0, 2.0],
        [1.0, 1.0, 1.0],            # all tied -> identity order
        [2.0, 2.0, 1.0, 3.0, 3.0],  # multiple tie groups
        [0.5, 0.5, 0.5, 0.4],
        [-1.0, -1.0, 0.0],
    ]
    for scores in cases:
        arr = np.array(scores, dtype=np.float64)
        vec_order = np.argsort(-arr, kind="stable").tolist()
        py_order = _python_order(scores)
        assert vec_order == py_order, (scores, vec_order, py_order)


def test_argsort_stable_random_grid() -> None:
    rng = np.random.default_rng(3)
    for _ in range(50):
        # Quantise to create deliberate ties.
        scores = np.round(rng.normal(size=20), 1).tolist()
        arr = np.array(scores, dtype=np.float64)
        assert np.argsort(-arr, kind="stable").tolist() == _python_order(scores)
