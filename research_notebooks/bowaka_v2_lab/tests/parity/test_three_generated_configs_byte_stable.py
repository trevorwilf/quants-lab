"""The three generated bowaka_v2_actual_* configs are byte-stable.

Realism remediation 2 Phase 1. ``import-actual-config`` is deterministic — each
of the three committed configs must regenerate byte-identically (the header is
filename-agnostic; the body is sorted-key, LF-newline YAML).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from bowaka_v2_lab import reference

_LAB_ROOT = Path(__file__).resolve().parents[2]

#: (committed filename, generator flags) for each of the three Phase-1 backtest
#: configs and the three Phase-8 Optuna configs. ``--purpose backtest`` is the
#: default (omitted) for Phase 1; Phase 8 adds ``--purpose optuna``.
_GENERATED_CONFIGS: tuple[tuple[str, list[str]], ...] = (
    (
        "bowaka_v2_actual_iex_current_code.yml",
        ["--feed", "iex", "--mode", "current_code_parity", "--feed-thresholds", "actual"],
    ),
    (
        "bowaka_v2_actual_iex_intended_realism.yml",
        ["--feed", "iex", "--mode", "intended_realism", "--feed-thresholds", "actual"],
    ),
    (
        "bowaka_v2_actual_sip_intended_realism.yml",
        ["--feed", "sip", "--mode", "intended_realism", "--feed-thresholds", "actual"],
    ),
    # Realism remediation 2 Phase 8 — the three Optuna configs replacing the
    # quarantined ``bowaka_v2_walkforward_optuna.yml``.
    (
        "bowaka_v2_actual_iex_current_code_optuna.yml",
        ["--feed", "iex", "--mode", "current_code_parity",
         "--feed-thresholds", "actual", "--purpose", "optuna"],
    ),
    (
        "bowaka_v2_actual_iex_intended_realism_optuna.yml",
        ["--feed", "iex", "--mode", "intended_realism",
         "--feed-thresholds", "actual", "--purpose", "optuna"],
    ),
    (
        "bowaka_v2_actual_sip_intended_realism_optuna.yml",
        ["--feed", "sip", "--mode", "intended_realism",
         "--feed-thresholds", "actual", "--purpose", "optuna"],
    ),
)


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated -- run mirror_bowaka_v2_source.ps1")


@pytest.mark.parametrize(
    "name,flags", _GENERATED_CONFIGS, ids=[c[0] for c in _GENERATED_CONFIGS]
)
def test_generated_config_regenerates_byte_identical(
    name: str, flags: list[str], tmp_path: Path
) -> None:
    committed = _LAB_ROOT / "configs" / name
    assert committed.is_file(), f"{name} not committed"
    out = tmp_path / name
    result = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "import-actual-config",
         "--out", str(out), *flags],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert committed.read_bytes() == out.read_bytes(), (
        f"{name} drifted from import-actual-config — regenerate it"
    )


@pytest.mark.parametrize(
    "name,flags", _GENERATED_CONFIGS, ids=[c[0] for c in _GENERATED_CONFIGS]
)
def test_generated_config_uses_lf_newlines(
    name: str, flags: list[str], tmp_path: Path
) -> None:
    """The committed configs use LF newlines (``.gitattributes`` pins *.yml)."""
    committed = (_LAB_ROOT / "configs" / name).read_bytes()
    assert b"\r\n" not in committed, f"{name} has CRLF newlines"


def test_rerun_is_byte_identical(tmp_path: Path) -> None:
    """Two back-to-back regenerations of the same config agree."""
    name, flags = _GENERATED_CONFIGS[0]
    out_a = tmp_path / "a.yml"
    out_b = tmp_path / "b.yml"
    for out in (out_a, out_b):
        subprocess.run(
            [sys.executable, "-m", "bowaka_v2_lab.cli", "import-actual-config",
             "--out", str(out), *flags],
            capture_output=True, text=True, check=True,
        )
    assert out_a.read_bytes() == out_b.read_bytes()
