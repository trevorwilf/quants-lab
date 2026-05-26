"""``StartupDataQualityError`` is a structural ``DataQualityError`` subclass.

Speedup report §4 P0-A / §5.1 / Phase 0 task 1. The pre-remediation backtester
raised a generic ``RuntimeError`` on startup DQ failure; the Optuna runner's
broad ``except Exception`` then degraded the fold to a sentinel score and the
study finished with a confidently-wrong best. ``StartupDataQualityError``
inherits from :class:`DataQualityError` so the runner's existing structural
exception handler (``except DataQualityError: raise``) propagates it.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.data.data_quality import (
    DataQualityError,
    StartupDataQualityError,
)
from bowaka_v2_lab.optuna.errors import structural_exceptions


def test_startup_dq_error_is_a_data_quality_error() -> None:
    exc = StartupDataQualityError("forced failure")
    assert isinstance(exc, DataQualityError)
    assert isinstance(exc, RuntimeError)
    assert "forced failure" in str(exc)


def test_structural_exceptions_match_startup_dq_error() -> None:
    """Every structural class that's a parent of StartupDataQualityError matches."""
    classes = structural_exceptions()
    matches = [c for c in classes if issubclass(StartupDataQualityError, c)]
    assert matches, (
        "expected at least one structural exception class to be a parent of "
        "StartupDataQualityError (DataQualityError); got: "
        f"{[c.__name__ for c in classes]}"
    )


def test_catching_data_quality_error_catches_startup_subclass() -> None:
    caught: Exception | None = None
    try:
        raise StartupDataQualityError("test")
    except DataQualityError as exc:
        caught = exc
    assert isinstance(caught, StartupDataQualityError)


def test_isinstance_chain_short_circuits_for_legacy_runtime_match() -> None:
    """``pytest.raises(RuntimeError, match=...)`` still catches it (back-compat)."""
    with pytest.raises(RuntimeError, match="legacy match"):
        raise StartupDataQualityError("legacy match path")
