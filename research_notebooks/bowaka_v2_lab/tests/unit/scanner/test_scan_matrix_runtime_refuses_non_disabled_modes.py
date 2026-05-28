"""Backtester opt-in: compatibility accepted (Phase 3), vectorized refused.

Speedup report v2 §6.1. Phase 3 SHIPS the compatibility-mode parity bridge,
so the backtester opt-in now ACCEPTS ``runtime_mode='compatibility'`` (the
``tests/parity/test_scan_matrix_*`` matrix is the proof). The vectorized
gate evaluator is still scaffolding-only and refused until Phase 4. Only
``runtime_mode='disabled'`` (the default) and ``'compatibility'`` are
admissible at this revision.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.scanner.scan_matrix_runtime import (
    MatrixParityManifestMissingError,
    MatrixRuntimeCompatibilityMode,
    MatrixRuntimeNotImplementedError,
    assert_backtester_matrix_opt_in_is_supported,
    evaluate_one_scan_from_matrix,
    evaluate_one_scan_from_matrix_vectorized,
)
from bowaka_v2_lab.scanner.scan_matrix_vectorized import (
    evaluate_one_scan_vectorized,
)


def test_disabled_is_a_no_op() -> None:
    assert_backtester_matrix_opt_in_is_supported(
        enabled=False, runtime_mode="disabled",
    )
    # Enabling the matrix while leaving runtime_mode=disabled is also OK —
    # the matrix can be built and inspected without the runtime path firing.
    assert_backtester_matrix_opt_in_is_supported(
        enabled=True, runtime_mode="disabled",
    )


def test_vectorized_without_parity_manifest_raises_manifest_error() -> None:
    with pytest.raises(MatrixParityManifestMissingError):
        assert_backtester_matrix_opt_in_is_supported(
            enabled=True, runtime_mode="vectorized",
            parity_manifest_present=False,
        )


def test_vectorized_with_manifest_still_refused_pending_parity_proof() -> None:
    """The vectorized runtime mode is scaffolding-only until Phase 4."""
    with pytest.raises(MatrixRuntimeNotImplementedError):
        assert_backtester_matrix_opt_in_is_supported(
            enabled=True, runtime_mode="vectorized",
            parity_manifest_present=True,
        )


def test_compatibility_mode_accepted_at_backtester_boundary() -> None:
    """Phase 3 — the compatibility runtime is admissible (no raise)."""
    assert_backtester_matrix_opt_in_is_supported(
        enabled=True, runtime_mode="compatibility",
        parity_manifest_present=True,
    )
    # Also accepted without a parity manifest present — the parity tests are
    # the proof and the fold-context builder verifies the manifest hashes.
    assert_backtester_matrix_opt_in_is_supported(
        enabled=True, runtime_mode="compatibility",
        parity_manifest_present=False,
    )


def test_compatibility_class_without_partition_refuses() -> None:
    """Constructing with no partition is OK; evaluating without one refuses."""
    compat = MatrixRuntimeCompatibilityMode(matrix_partition=None, cfg={})
    with pytest.raises(MatrixRuntimeNotImplementedError):
        compat.evaluate_one_scan_compat(
            None, [], state={}, scan_context=None, universe_snapshot={},
        )


def test_legacy_evaluator_stubs_still_refuse() -> None:
    """The Phase 9 ``evaluate_one_scan_from_matrix`` stubs continue to refuse."""
    with pytest.raises(MatrixRuntimeNotImplementedError):
        evaluate_one_scan_from_matrix(
            cfg=None, matrix_session=None, state={}, scan_idx=0, consumer=None,
        )
    with pytest.raises(MatrixRuntimeNotImplementedError):
        evaluate_one_scan_from_matrix_vectorized(
            cfg=None, matrix_session=None, state={}, scan_idx=0, consumer=None,
        )
    with pytest.raises(MatrixRuntimeNotImplementedError):
        evaluate_one_scan_vectorized(None, [], None, {})
