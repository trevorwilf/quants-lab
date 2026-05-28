"""Phase 4 — vectorized gate helpers match the scalar _ge/_le/_between.

Speedup report v2 §15.2. The vectorized gate masks must reproduce the
asymmetric missing-value semantics of the legacy scalar helpers exactly:

  * _ge(val, t): t None -> pass; val None -> fail when t set.
  * _le(val, t): t None -> pass; val None -> PASS when t set (asymmetric).
  * _between(val, lo, hi): no bounds -> pass; val None -> fail with bounds.

NaN in the vectorized array represents the legacy None.
"""
from __future__ import annotations

import numpy as np
import pytest

from bowaka_v2_lab.features.forming_bar import _ge, _le, _between
from bowaka_v2_lab.scanner.scan_matrix_vectorized import (
    _ge_vec, _le_vec, _between_vec,
)


_VALUES = [None, 0.0, -1.0, 1.5, 100.0]
_THRESHOLDS = [None, 0.0, 1.0, 50.0]


def _to_arr(v):
    return np.array([v if v is not None else np.nan], dtype=np.float64)


@pytest.mark.parametrize("val", _VALUES)
@pytest.mark.parametrize("threshold", _THRESHOLDS)
def test_ge_vec_matches_scalar(val, threshold) -> None:
    scalar = _ge(val, threshold)
    vec = bool(_ge_vec(_to_arr(val), threshold)[0])
    assert scalar == vec, (val, threshold, scalar, vec)


@pytest.mark.parametrize("val", _VALUES)
@pytest.mark.parametrize("threshold", _THRESHOLDS)
def test_le_vec_matches_scalar(val, threshold) -> None:
    scalar = _le(val, threshold)
    vec = bool(_le_vec(_to_arr(val), threshold)[0])
    assert scalar == vec, (val, threshold, scalar, vec)


@pytest.mark.parametrize("val", _VALUES)
@pytest.mark.parametrize("lo", [None, 0.0, 1.0])
@pytest.mark.parametrize("hi", [None, 2.0, 50.0])
def test_between_vec_matches_scalar(val, lo, hi) -> None:
    scalar = _between(val, lo, hi)
    vec = bool(_between_vec(_to_arr(val), lo, hi)[0])
    assert scalar == vec, (val, lo, hi, scalar, vec)


def test_ge_vec_array_form() -> None:
    """Vectorized form over a mixed array agrees element-wise with scalar."""
    vals = [None, 0.0, 5.0, -2.0, 1.0]
    arr = np.array([v if v is not None else np.nan for v in vals], dtype=np.float64)
    got = _ge_vec(arr, 1.0)
    want = [_ge(v, 1.0) for v in vals]
    assert list(map(bool, got)) == want
