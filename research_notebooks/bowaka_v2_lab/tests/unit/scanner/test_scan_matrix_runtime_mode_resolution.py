"""``runtime_mode`` resolves with default ``"disabled"`` + admissible aliases.

Speedup report v2 §4 P6 / §6.1 / Phase 6 task 3. The three-mode config
field is enforced — anything else raises ``ValueError`` at resolution
time so a typo doesn't silently degrade to the legacy default.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.scanner.scan_matrix_runtime import resolve_runtime_mode


def test_default_is_disabled() -> None:
    assert resolve_runtime_mode({}) == "disabled"
    assert resolve_runtime_mode({"optuna": {}}) == "disabled"
    assert resolve_runtime_mode(
        {"optuna": {"acceleration": {"scan_matrix": {}}}}
    ) == "disabled"


def test_explicit_disabled() -> None:
    cfg = {"optuna": {"acceleration": {"scan_matrix": {"runtime_mode": "disabled"}}}}
    assert resolve_runtime_mode(cfg) == "disabled"


def test_compatibility_resolves() -> None:
    cfg = {"optuna": {"acceleration": {"scan_matrix": {"runtime_mode": "compatibility"}}}}
    assert resolve_runtime_mode(cfg) == "compatibility"


def test_vectorized_resolves() -> None:
    cfg = {"optuna": {"acceleration": {"scan_matrix": {"runtime_mode": "vectorized"}}}}
    assert resolve_runtime_mode(cfg) == "vectorized"


def test_uppercase_normalised_to_lowercase() -> None:
    cfg = {"optuna": {"acceleration": {"scan_matrix": {"runtime_mode": "VECTORIZED"}}}}
    assert resolve_runtime_mode(cfg) == "vectorized"


def test_unknown_mode_raises() -> None:
    cfg = {"optuna": {"acceleration": {"scan_matrix": {"runtime_mode": "lazy"}}}}
    with pytest.raises(ValueError, match="runtime_mode must be one of"):
        resolve_runtime_mode(cfg)
