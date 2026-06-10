"""A fold that opens NO scan-matrix store must run on the LEGACY scanner, not
raise the vectorized parity-proof opt-in.

The holdout window under ``separate_holdout_matrix=true`` (holdout isolation)
deliberately opens no matrix store. The backtester's runtime opt-in fires on
``scan_matrix.enabled=True`` + ``runtime_mode!="disabled"`` regardless of whether
a store is present, so a vectorized config would raise
``MatrixRuntimeNotImplementedError`` ("requires a parity-proof marker with
verifier_version >= 2") on an honest legacy fold — which broke the finalist
holdout sweep (Holdout net% / 12-mo OOS% blank for every finalist).
``_matrix_runtime_disabled_if_no_store`` forces ``runtime_mode=disabled`` for a
storeless fold so the opt-in no-ops; it is a no-op when a store IS present, so
the validation-scope opt-in + parity check are unchanged.
"""
from __future__ import annotations

from bowaka_v2_lab.optuna.walkforward_runner import (
    _matrix_runtime_disabled_if_no_store as _disable,
)


def _cfg(mode: str = "vectorized", enabled: bool = True) -> dict:
    return {"optuna": {"acceleration": {"scan_matrix": {
        "enabled": enabled, "runtime_mode": mode}}}}


def _rt(cfg: dict) -> str:
    return cfg["optuna"]["acceleration"]["scan_matrix"]["runtime_mode"]


def test_no_store_vectorized_is_forced_to_disabled() -> None:
    base = _cfg("vectorized")
    out = _disable(base, None)
    assert _rt(out) == "disabled"          # the storeless fold runs legacy
    assert _rt(base) == "vectorized"       # original cfg is NOT mutated (deep-copied)


def test_no_store_compatibility_is_forced_to_disabled() -> None:
    assert _rt(_disable(_cfg("compatibility"), None)) == "disabled"


def test_store_present_is_unchanged() -> None:
    base = _cfg("vectorized")
    out = _disable(base, object())         # any non-None store
    assert out is base                     # no copy, opt-in + parity stay in force
    assert _rt(out) == "vectorized"


def test_already_disabled_is_unchanged() -> None:
    base = _cfg("disabled")
    assert _disable(base, None) is base


def test_matrix_not_enabled_is_unchanged() -> None:
    base = _cfg("vectorized", enabled=False)
    assert _disable(base, None) is base
