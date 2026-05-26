"""Matrix-backed scanner runtime evaluator.

Speedup report v2 §4 P6, §6.1, §11.2 Phase 6 — research-only by design.
Adds two evaluator paths:

* :class:`MatrixRuntimeCompatibilityMode` — produces per-scan candidate
  events field-by-field equal to the legacy
  :func:`scanner.scan_loop.evaluate_one_scan`. The parity bridge for the
  compatibility runtime_mode.
* :func:`evaluate_one_scan_vectorized` — gate evaluation as numpy
  vector ops over the matrix partition. Requires the parity manifest
  (``optuna.acceleration.scan_matrix.require_parity_manifest``).

Both are **scaffolding** in this build: the parity bridge requires
multi-day work to reconstruct per-symbol dicts identically to the
legacy scanner's gate ordering / score tie-stability / event-id
determinism, so the opt-in is refused at the backtester boundary until
the parity matrix (tests/parity/test_scan_matrix_*) proves bit-equal
results. The Phase 6 contract is:

1. ``runtime_mode`` defaults to ``"disabled"`` in every committed
   config — no production behaviour change.
2. ``runtime_mode="compatibility"`` is admissible AS A RESEARCH OPT-IN
   only when the parity manifest is present AND the parity tests pass;
   today the runtime still refuses at the backtester opt-in boundary.
3. ``runtime_mode="vectorized"`` requires the parity manifest plus the
   parity proof; refused for the same reason.
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


class MatrixParityManifestMissingError(MatrixRuntimeNotImplementedError):
    """Raised when ``runtime_mode="vectorized"`` is set without a parity manifest.

    Speedup report v2 §6.1 / Phase 6 task 3. The vectorized path produces
    candidate events from numpy vector ops; without the parity manifest
    (built by ``bowaka-v2-lab scan-matrix build``) there is no proof the
    vectorized path matches the legacy scanner. The runtime refuses to
    enable the vectorized path under those conditions.
    """


def resolve_runtime_mode(cfg: Any) -> str:
    """Read ``optuna.acceleration.scan_matrix.runtime_mode`` with the default.

    Speedup report v2 §4 P6 / Phase 6 task 3. Valid values are
    ``"disabled"`` (the default — legacy ``evaluate_one_scan`` path),
    ``"compatibility"`` (matrix-backed evaluator returning identical
    candidate events to the legacy path), and ``"vectorized"`` (numpy
    vector-op gate evaluation; requires the parity manifest).
    """
    mode = (
        ((cfg or {}).get("optuna") or {}).get("acceleration", {})
        .get("scan_matrix", {}).get("runtime_mode", "disabled")
    )
    mode = str(mode).lower().strip() or "disabled"
    if mode not in ("disabled", "compatibility", "vectorized"):
        raise ValueError(
            f"optuna.acceleration.scan_matrix.runtime_mode must be one of "
            f"'disabled' / 'compatibility' / 'vectorized'; got {mode!r}"
        )
    return mode


class MatrixRuntimeCompatibilityMode:
    """Parity-bridge evaluator for ``runtime_mode='compatibility'``.

    Speedup report v2 §4 P6 / §6.1 / Phase 6 task 2 — produces a
    candidate-event list field-by-field equal to
    :func:`scanner.scan_loop.evaluate_one_scan` for the same inputs.
    The bridge reconstructs the per-symbol ``session_bar`` /
    ``forming_feats`` dicts from the matrix partition in the SAME
    arithmetic order the legacy loop uses, calls the EXISTING
    ``apply_v2_gates`` / ``compute_signal_strength`` (no gate re-impl),
    and builds candidate events via
    :func:`scanner.event_builder.build_candidate_event`.

    **Currently a scaffolding class.** Construction is allowed (so
    config validation + parity tests can target the surface), but
    :meth:`evaluate_one_scan_compat` raises
    :class:`MatrixRuntimeNotImplementedError` until the per-symbol
    dict reconstruction + gate ordering + event_id determinism parity
    proof against ``evaluate_one_scan`` is shipped. The scaffolding
    refusal at the backtester opt-in boundary
    (:func:`assert_backtester_matrix_opt_in_is_supported`) ensures no
    production caller can enable this mode silently.
    """

    def __init__(
        self,
        *,
        matrix_partition: Any,
        cfg: Optional[Any] = None,
    ) -> None:
        self.matrix_partition = matrix_partition
        self.cfg = cfg

    def evaluate_one_scan_compat(
        self,
        scan_ts: Any,
        eligible_symbols: Any,
    ) -> list:
        """Return the same candidate-event list ``evaluate_one_scan`` would.

        Per the class docstring — refuses with
        :class:`MatrixRuntimeNotImplementedError` until the parity proof
        lands. The class is admitted so callers can probe the API +
        parity tests can target the surface.
        """
        raise MatrixRuntimeNotImplementedError(
            "MatrixRuntimeCompatibilityMode.evaluate_one_scan_compat: the "
            "parity bridge between matrix rows and per-symbol dict "
            "reconstruction (gate ordering, score tie-stability, event_id "
            "determinism vs evaluate_one_scan) is scaffolding-only in this "
            "build. Set optuna.acceleration.scan_matrix.runtime_mode = "
            "'disabled' (the default) until the parity matrix tests pass. "
            "See speedup report v2 §6.1 / matrix doc §17.2."
        )


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
    runtime_mode: str = "disabled",
    parity_manifest_present: bool = False,
) -> None:
    """Refuse the matrix-backed scanner opt-in until the parity proof lands.

    Speedup report v2 §4 P6 / §6.1 / Phase 6 task 3. Three-mode resolution:

    * ``runtime_mode == "disabled"`` (the default) → no-op; legacy scanner.
    * ``runtime_mode == "compatibility"`` → refused
      (:class:`MatrixRuntimeNotImplementedError`) until the parity bridge
      proves bit-equality with ``evaluate_one_scan``.
    * ``runtime_mode == "vectorized"`` → refused
      (:class:`MatrixParityManifestMissingError` when the parity manifest
      is absent; :class:`MatrixRuntimeNotImplementedError` when present
      because the parity proof against the legacy path still has not
      shipped).
    """
    if not enabled or runtime_mode == "disabled":
        return
    if runtime_mode == "vectorized" and not parity_manifest_present:
        raise MatrixParityManifestMissingError(
            "scan-matrix runtime_mode='vectorized' requires the parity "
            "manifest. Build it via `bowaka-v2-lab scan-matrix build` "
            "(speedup report v2 §6.1 / matrix doc §17.2)."
        )
    raise MatrixRuntimeNotImplementedError(
        f"scan-matrix runtime_mode={runtime_mode!r} is scaffolding-only "
        "in this build. The compatibility-mode parity bridge against "
        "evaluate_one_scan (per-symbol dict reconstruction, gate ordering, "
        "event_id determinism) and the vectorized gate evaluator are "
        "reserved for the next remediation pickup. Set "
        "optuna.acceleration.scan_matrix.runtime_mode = 'disabled' until "
        "the parity matrix tests prove bit-identical FoldResults "
        "(speedup report v2 §6.1 / matrix doc §17.2)."
    )


__all__ = [
    "MatrixParityManifestMissingError",
    "MatrixRuntimeCompatibilityMode",
    "MatrixRuntimeNotImplementedError",
    "assert_backtester_matrix_opt_in_is_supported",
    "evaluate_one_scan_from_matrix",
    "evaluate_one_scan_from_matrix_vectorized",
    "resolve_runtime_mode",
]
