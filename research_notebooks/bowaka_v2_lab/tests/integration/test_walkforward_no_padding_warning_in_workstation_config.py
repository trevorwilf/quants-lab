"""Phase 2 (audit 2026-05-29 §6.7) — the workstation config incumbent never pads.

The operator runs Notebook 10 against
``bowaka_v2_actual_iex_current_code_optuna.workstation.yml``. Building the
incumbent baseline for that run must NOT emit the "incumbent baseline padded"
warning (the pre-fix run did, for execution.max_quote_age_seconds /
execution.max_spread_bps).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from bowaka_v2_lab.config.loader import load_config
from bowaka_v2_lab.optuna.walkforward_runner import _incumbent_baseline_params
from bowaka_v2_lab.reference import contract_available

_LAB_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not contract_available():
        pytest.xfail("frozen contract not generated — run mirror_bowaka_v2_source.ps1")


def test_workstation_config_incumbent_has_no_padding(caplog) -> None:
    # The exact config the operator runs Notebook 10 against must load.
    cfg = load_config(
        _LAB_ROOT / "configs" / "bowaka_v2_actual_iex_current_code_optuna.workstation.yml"
    )
    assert cfg["simulation"]["mode"] == "current_code_parity"

    with caplog.at_level("WARNING"):
        params = _incumbent_baseline_params()

    assert params, "incumbent baseline should be non-empty against the contract"
    assert "incumbent baseline padded" not in caplog.text
