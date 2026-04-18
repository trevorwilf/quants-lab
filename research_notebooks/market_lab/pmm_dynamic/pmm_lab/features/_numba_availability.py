"""Shared Numba availability check.

All compiled-kernel modules import from here. Numba is an optional dependency;
if it's not installed, kernels fall back to pure-Python implementations that
preserve the same numerical semantics (but without the speedup).
"""

from __future__ import annotations

try:
    import numba as _numba  # type: ignore
    _NUMBA_AVAILABLE = True
    NUMBA_VERSION = _numba.__version__
except ImportError:
    _NUMBA_AVAILABLE = False
    NUMBA_VERSION = None
    _numba = None
