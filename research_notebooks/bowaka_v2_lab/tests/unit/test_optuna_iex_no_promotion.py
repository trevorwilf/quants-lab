"""Study annotated with feed=iex → promotion_eligible=False (raises on attempt)."""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.dispatcher import OptunaStudy


def test_iex_study_blocks_promotion() -> None:
    s = OptunaStudy(feed="iex", cost_stress="base",
                     dataset_hash="cafebabecafebabe",
                     config_hash="deadbeefdeadbeef",
                     storage_uri=None, n_trials=1)
    with pytest.raises(RuntimeError, match="IEX-only"):
        s.mark_promotion_eligible()
    assert s.promotion_eligible is False


def test_sip_study_allows_promotion() -> None:
    s = OptunaStudy(feed="sip", cost_stress="conservative",
                     dataset_hash="cafebabecafebabe",
                     config_hash="deadbeefdeadbeef",
                     storage_uri=None, n_trials=1)
    s.mark_promotion_eligible()
    assert s.promotion_eligible is True
