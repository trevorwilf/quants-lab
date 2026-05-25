"""Matrix-backed scanner runtime evaluator (Phase 9 scaffolding).

Matrix doc §8, §13, §17.2, §17.3 / speedup report §6.4. Adds
``evaluate_one_scan_from_matrix(...)`` (compatibility row-wise) and
``evaluate_one_scan_from_matrix_vectorized(...)`` (vectorized) plus the
backtester integration hooks. **Default off**; the runtime refuses the
opt-in until the parity matrix in
``tests/parity/test_scan_matrix_one_scan_parity.py`` and friends proves
bit-identical results to the legacy ``evaluate_one_scan`` for the full
walk-forward backtest.

The structural contract this module honours even in the scaffolding:

1. ``ScanMatrixStore.assert_can_read(date, purpose=...)`` blocks
   holdout reads under ``purpose="objective"``
   (:class:`HoldoutMatrixReadError`) — the final-holdout scorer must
   opt in with ``purpose="final_holdout"``.
2. The matrix-sensitive search-space guard
   (:func:`assert_search_space_compatible_with_matrix`) fires before
   any matrix access whenever the matrix is enabled.

Phase 9 wiring of ``evaluate_one_scan_from_matrix`` into the dispatch
loop in ``sim/backtester.py`` is intentionally NOT done in this
scaffolding — it requires the parity proof against the legacy scanner
(per-symbol dict reconstruction, gate ordering, score tie-stability,
event_id determinism). The backtester's matrix opt-in raises
``NotImplementedError`` until that proof lands.
"""
from __future__ import annotations

from typing import Any, Optional

from .scan_matrix import (
    HoldoutMatrixReadError,
    ScanMatrixSession,
    ScanMatrixStore,
)


class MatrixRuntimeNotImplementedError(RuntimeError):
    """Raised when the runtime opt-in is set but the parity proof is missing."""


def evaluate_one_scan_from_matrix(
    *,
    cfg: Any,
    matrix_session: ScanMatrixSession,
    state: dict,
    scan_idx: int,
    consumer: Any,
    quote_supplier: Optional[Any] = None,
    forward_minute_supplier: Optional[Any] = None,
    status_supplier: Optional[Any] = None,
    collect_gate_dump: bool = False,
) -> tuple[Any, list]:
    """**Phase 9 scaffolding: NOT yet wired.**

    The compatibility-mode evaluator (Step 9A) MUST:

    1. Read dynamic+static rows from
       ``matrix_session.dynamic_float64[col][scan_idx, :]`` etc.
    2. Reconstruct per-symbol ``session_bar`` + ``forming_feats`` dicts
       identical in keys to the legacy path output.
    3. Call existing ``apply_v2_gates`` / ``compute_signal_strength``
       on those dicts — do not re-implement gate logic.
    4. Build candidate events via
       ``scanner.event_builder.build_candidate_event(...)``. Event IDs
       / hashes / schema MUST match the legacy path exactly.
    5. Apply scanner-state updates
       (``signal_emits_per_symbol_today``, ``symbol_last_emit_ts``)
       identically to ``evaluate_one_scan``.

    Until the parity matrix
    (``tests/parity/test_scan_matrix_one_scan_parity.py`` and
    ``test_scan_matrix_full_session_parity.py`` and
    ``test_scan_matrix_full_fold_backtest_parity.py``) is wired and
    proves identical emitted-candidate sequences + scanner state +
    fills + trades + daily equity + FoldResults, the runtime opt-in
    is refused.
    """
    raise MatrixRuntimeNotImplementedError(
        "evaluate_one_scan_from_matrix is reserved for the Phase 9 "
        "matrix-backed scanner runtime; the per-symbol dict "
        "reconstruction + gate ordering + score tie-stability + "
        "event_id determinism parity proof against evaluate_one_scan "
        "(legacy) is not yet shipped. Set "
        "optuna.acceleration.scan_matrix.enabled=false until the "
        "parity matrix proves bit-identical results "
        "(speedup report §6.4 / matrix doc §17.2)."
    )


def evaluate_one_scan_from_matrix_vectorized(
    *,
    cfg: Any,
    matrix_session: ScanMatrixSession,
    state: dict,
    scan_idx: int,
    consumer: Any,
    quote_supplier: Optional[Any] = None,
    forward_minute_supplier: Optional[Any] = None,
    status_supplier: Optional[Any] = None,
    collect_gate_dump: bool = False,
) -> tuple[Any, list]:
    """Vectorized (Step 9B) — also Phase 9 scaffolding.

    Will use ``np.argsort(-scores, kind="stable")`` (matrix doc §17.3) on
    the full ``dyn_f64`` / ``flags`` slices for ``scan_idx``, then call
    ``build_candidate_event`` row-wise for passing rows. Missing-value
    semantics from matrix doc §6 must be implemented explicitly (no
    NaN-compares — every gate masks on the corresponding uint8 flag).
    """
    raise MatrixRuntimeNotImplementedError(
        "evaluate_one_scan_from_matrix_vectorized is reserved for "
        "Phase 9 Step 9B and is not yet shipped."
    )


def assert_backtester_matrix_opt_in_is_supported(
    *,
    enabled: bool,
) -> None:
    """Refuse the matrix-backed scanner opt-in until the parity proof lands.

    Called from ``sim/backtester.run_backtest`` when the cfg's
    ``optuna.acceleration.scan_matrix.enabled`` flag would route the
    SCAN events through the matrix evaluator.
    """
    if not enabled:
        return
    raise MatrixRuntimeNotImplementedError(
        "scan-matrix runtime opt-in (optuna.acceleration.scan_matrix.enabled=True) "
        "is reserved for Phase 9; the matrix-backed evaluator's parity proof "
        "against the legacy evaluate_one_scan path is not yet wired in this "
        "build. The Phase 8 builder + manifest + holdout guard are fully "
        "shipped — the matrix can be precomputed and inspected via "
        "`bowaka-v2-lab scan-matrix build|verify` — but the scanner runtime "
        "still uses the legacy per-symbol path until the Phase 9 parity "
        "matrix tests prove bit-identical FoldResults "
        "(speedup report §6.4 / matrix doc §17.2)."
    )


__all__ = [
    "MatrixRuntimeNotImplementedError",
    "assert_backtester_matrix_opt_in_is_supported",
    "evaluate_one_scan_from_matrix",
    "evaluate_one_scan_from_matrix_vectorized",
]
