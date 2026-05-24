"""Structural-exception taxonomy for the Optuna runner (realism remediation 3).

Audit 2026-05-23 §P0-001: a structural rejection (HoldoutGuardError,
PreflightError, DataQualityError, MissingLakePartitionError, ConfigParityError)
must NEVER be swallowed by the broad ``except Exception`` blocks in the
per-trial objective or the per-fold handler. Any structural exception escapes
the trial and aborts the study with :class:`OptunaStudyInvalidError`; only
non-structural strategy / evaluation errors degrade to ``_FAILED_TRIAL_SCORE``.

``STRUCTURAL_EXCEPTIONS`` is populated lazily inside :func:`structural_exceptions`
to avoid an import cycle between this module, ``holdout_guard``, ``preflight``
and ``data.data_quality``. Call ``structural_exceptions()`` from the runner; do
not import ``STRUCTURAL_EXCEPTIONS`` at module load (it will be the empty
tuple until first call).
"""
from __future__ import annotations

from typing import Tuple, Type


class OptunaStudyInvalidError(RuntimeError):
    """Raised when an Optuna study completed but produced zero valid trials.

    Audit 2026-05-23 §P0-001. The pre-remediation behaviour was a study writer
    emitting ``status: "ok"`` and a non-empty ``best_params`` for an all-sentinel
    study (every trial returned ``_FAILED_TRIAL_SCORE``). Post-remediation the
    runner validates the completed trial set and raises this exception when
    zero valid non-sentinel trials exist; the writer records ``status: "failed"``
    and ``best_params: {}`` before re-raising.
    """


class ConfigParityError(RuntimeError):
    """Raised when the lab config (or any of its declared source files) diverges
    from the frozen actual contract without a parity-sidecar waiver.

    Audit 2026-05-23 §P1-002. Used by the source-manifest parity test
    (``assert_source_manifest_unchanged``) and by the scanner-key normalisation
    gate (Phase 2 task 2.4) when both ``risk.same_symbol_entries_per_day`` and
    ``scanner.same_symbol_entries_per_day`` are present in a loaded config.
    """


class MissingLakePartitionError(RuntimeError):
    """Raised when a required lake partition is absent under intended_realism.

    Audit 2026-05-23 §P0-004 / §P0-005. The lake verification CLI raises this
    when a required parquet partition (bars / quotes / statuses /
    corporate_actions / assets) is missing and ``--intended-realism`` is set.
    """


#: Late-bound tuple of structural exception classes. Use
#: :func:`structural_exceptions` to read; this name exists for back-compat with
#: ``from .errors import STRUCTURAL_EXCEPTIONS`` callers that do not need the
#: late binding (they accept the empty tuple at import time and pay the lookup
#: cost on every exception). Prefer ``structural_exceptions()`` in hot code.
STRUCTURAL_EXCEPTIONS: Tuple[Type[BaseException], ...] = ()


def structural_exceptions() -> Tuple[Type[BaseException], ...]:
    """Return the tuple of structural exception classes (lazy binding).

    Late-imports the structural classes from their owning modules on first
    call, populates :data:`STRUCTURAL_EXCEPTIONS`, and caches the result on
    the module. Subsequent calls return the cached tuple.
    """
    global STRUCTURAL_EXCEPTIONS
    if STRUCTURAL_EXCEPTIONS:
        return STRUCTURAL_EXCEPTIONS
    from .holdout_guard import HoldoutGuardError
    from .preflight import PreflightError
    from ..data.data_quality import DataQualityError

    STRUCTURAL_EXCEPTIONS = (
        HoldoutGuardError,
        PreflightError,
        DataQualityError,
        MissingLakePartitionError,
        ConfigParityError,
        OptunaStudyInvalidError,
    )
    return STRUCTURAL_EXCEPTIONS


__all__ = [
    "OptunaStudyInvalidError",
    "ConfigParityError",
    "MissingLakePartitionError",
    "STRUCTURAL_EXCEPTIONS",
    "structural_exceptions",
]
