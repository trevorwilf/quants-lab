"""Every committed config defaults ``runtime_mode`` to ``"disabled"`` — except
the dedicated enablement overlay.

Speedup report v2 §6.1 / §11.2 Phase 6 / acceptance. The Phase 6
deliverables are research-only — no *base* production config flips the matrix
runtime on. This integration test sweeps the configs/ directory and asserts
the default.

Walk-forward scan-matrix speedup Phase 2 amends this: the matrix is now
enabled in exactly ONE committed config — the ``*matrix*.yml`` enablement
overlay — which is EXCLUDED from the sweep below and asserted-on by the
sibling positive test. Enablement therefore lives only in the overlay; it is
never reachable by flipping a base config.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

_LAB_ROOT = Path(__file__).resolve().parents[2]
# Exclude the dedicated enablement overlay(s): enablement lives ONLY there.
_CONFIGS = sorted(
    p for p in (_LAB_ROOT / "configs").glob("bowaka_v2_*.yml")
    if "matrix" not in p.name
)
#: The enablement overlay(s) the positive test asserts on.
_MATRIX_CONFIGS = sorted((_LAB_ROOT / "configs").glob("bowaka_v2_*matrix*.yml"))


@pytest.mark.parametrize("cfg_path", _CONFIGS, ids=[p.name for p in _CONFIGS])
def test_runtime_mode_is_disabled_or_absent(cfg_path: Path) -> None:
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    sm = (((doc or {}).get("optuna") or {}).get("acceleration") or {}).get(
        "scan_matrix", {},
    )
    # Absent → loader defaults to disabled. Present → must be "disabled".
    mode = sm.get("runtime_mode", "disabled")
    assert mode == "disabled", (
        f"{cfg_path.name} sets runtime_mode={mode!r}; every committed config "
        "EXCEPT the dedicated *matrix*.yml enablement overlay must default to "
        "'disabled'"
    )


def test_matrix_overlay_exists_and_is_excluded() -> None:
    """The enablement overlay ships and is not in the disabled sweep."""
    assert _MATRIX_CONFIGS, (
        "expected a *matrix*.yml enablement overlay under configs/ "
        "(walk-forward scan-matrix speedup Phase 2)"
    )
    swept = {p.name for p in _CONFIGS}
    for m in _MATRIX_CONFIGS:
        assert m.name not in swept, (
            f"{m.name} must be excluded from the default-disabled sweep"
        )


@pytest.mark.parametrize(
    "cfg_path", _MATRIX_CONFIGS, ids=[p.name for p in _MATRIX_CONFIGS],
)
def test_matrix_overlay_enables_vectorized_runtime(cfg_path: Path) -> None:
    """The enablement overlay turns the vectorized runtime ON with a proof
    requirement and a scoped store_root — the positive counterpart to the
    default-disabled sweep."""
    doc = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    sm = (((doc or {}).get("optuna") or {}).get("acceleration") or {}).get(
        "scan_matrix", {},
    )
    assert sm.get("enabled") is True, f"{cfg_path.name}: enabled must be True"
    assert sm.get("runtime_mode") == "vectorized", (
        f"{cfg_path.name}: runtime_mode must be 'vectorized'"
    )
    assert sm.get("require_parity_manifest") is True, (
        f"{cfg_path.name}: require_parity_manifest must be True (vectorized "
        "opt-in needs the verifier_version>=2 proof)"
    )
    # store_root (preferred over the back-compat ``root``) must name the
    # validation scope so the resolver lands on the built layout.
    store_root = sm.get("store_root") or sm.get("root")
    assert store_root, f"{cfg_path.name}: a store_root/root must be configured"
    assert str(store_root).rstrip("/").endswith("/validation"), (
        f"{cfg_path.name}: store_root must end with '/validation' (got "
        f"{store_root!r})"
    )
    # Holdout stays isolated even with the matrix on.
    assert sm.get("separate_holdout_matrix") is True, (
        f"{cfg_path.name}: separate_holdout_matrix must stay True"
    )
