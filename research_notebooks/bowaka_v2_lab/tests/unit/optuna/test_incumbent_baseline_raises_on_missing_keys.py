"""Phase 2 (audit 2026-05-29 §6.7) — incumbent fails closed on a missing key.

A search-space key absent from the mapped lab config must raise
``INCUMBENT_MAPPING_INCOMPLETE`` (NOT silently pad), so a broken mapping can
never produce a Trial 0 that is not the actual strategy.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.errors import (
    REASON_INCUMBENT_MAPPING_INCOMPLETE,
    OptunaStudyInvalidError,
)
from bowaka_v2_lab.optuna.walkforward_runner import _incumbent_baseline_params
from bowaka_v2_lab.reference import contract_available, load_actual_contract
from bowaka_v2_lab.reference.import_config import build_config_from_contract


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not contract_available():
        pytest.xfail("frozen contract not generated — run mirror_bowaka_v2_source.ps1")


def test_missing_search_key_raises() -> None:
    cfg = build_config_from_contract(
        load_actual_contract(),
        feed="iex", mode="current_code_parity", feed_thresholds="actual",
    )
    # Drop a directly-mapped search key.
    del cfg["execution"]["max_quote_age_seconds"]
    with pytest.raises(OptunaStudyInvalidError) as ei:
        _incumbent_baseline_params(lab_config=cfg)
    msg = str(ei.value)
    assert REASON_INCUMBENT_MAPPING_INCOMPLETE in msg
    assert "execution.max_quote_age_seconds" in msg
