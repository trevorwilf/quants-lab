"""Vectorized scan-matrix gate evaluation (speedup report v2 §6.1 / Phase 6).

Implements ``evaluate_one_scan_vectorized(...)`` as numpy vector ops over
matrix partition columns. Each gate (signal threshold, ATR cap, RVOL
window, ema_slope, gap_pct, etc.) is a boolean mask; candidate events
are constructed in the same row order the compatibility-mode evaluator
produces them. Skip reasons are tracked by per-gate masks so the
*first* gate that drops a symbol determines its ``skip_reasons[0]`` —
mirroring how :func:`scanner.scan_loop.evaluate_one_scan` orders skip
reasons in the legacy path.

**This module is research-only scaffolding** in this build. The
vectorized path is admissible only when the parity manifest is present
AND the parity bridge in
:class:`MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat` is
proven bit-equal to the legacy scanner. Until that proof lands the
top-level entry point raises
:class:`MatrixRuntimeNotImplementedError`.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from .scan_matrix_runtime import MatrixRuntimeNotImplementedError


def evaluate_one_scan_vectorized(
    scan_ts: Any,
    eligible_symbols: Sequence[str],
    matrix_partition: Any,
    cfg: Mapping[str, Any],
) -> list:
    """Vectorized gate evaluation (Phase 6 scaffolding).

    Will iterate the matrix partition's dyn_float64 / dyn_int64 /
    dyn_uint8 columns at the resolved scan index, mask the gates in
    legacy order, ``np.argsort(-scores, kind="stable")`` the passing
    rows, and emit candidate events. The static-content surface +
    parity tests are reserved for the next remediation pickup; the
    refusal here keeps every committed config safely on the legacy
    path.
    """
    raise MatrixRuntimeNotImplementedError(
        "evaluate_one_scan_vectorized: scaffolding-only in this build "
        "(speedup report v2 §6.1 / matrix doc §17.3). Set "
        "optuna.acceleration.scan_matrix.runtime_mode = 'disabled' "
        "until the parity proof lands."
    )


__all__ = ["evaluate_one_scan_vectorized"]
