"""Backtester opt-in refuses every non-disabled mode (scaffolding).

Speedup report v2 §6.1 / Phase 6. The compatibility-mode parity bridge
and the vectorized gate evaluator are scaffolding-only in this build;
the backtester opt-in refuses both. Only ``runtime_mode='disabled'``
(the default in every committed config) is admissible.
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
    """The compatibility / vectorized runtime modes are scaffolding-only
    until the parity proof against the legacy scanner lands."""
    with pytest.raises(MatrixRuntimeNotImplementedError):
        assert_backtester_matrix_opt_in_is_supported(
            enabled=True, runtime_mode="vectorized",
            parity_manifest_present=True,
        )


def test_compatibility_mode_refused_at_backtester_boundary() -> None:
    with pytest.raises(MatrixRuntimeNotImplementedError):
        assert_backtester_matrix_opt_in_is_supported(
            enabled=True, runtime_mode="compatibility",
            parity_manifest_present=True,
        )


def test_compatibility_class_construction_admitted_but_evaluator_refused() -> None:
    """Constructing the class is OK (parity tests target the surface)."""
    compat = MatrixRuntimeCompatibilityMode(matrix_partition=None, cfg={})
    with pytest.raises(MatrixRuntimeNotImplementedError):
        compat.evaluate_one_scan_compat(None, [])


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
