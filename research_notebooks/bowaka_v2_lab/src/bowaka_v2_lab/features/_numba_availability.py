"""Shared Numba availability check (walk-forward numba speedup, Phase 1).

All compiled-kernel modules in ``bowaka_v2_lab`` import from here. Numba is an
optional dependency (``pip install -e .[numba]``); if it is not installed, the
kernel modules fall back to pure-Python implementations that preserve the same
numerical semantics (but without the compiled speedup). Ported verbatim from the
market_lab reference (``pmm_lab/features/_numba_availability.py``).
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
