"""Phase 2 (audit 2026-05-29 §6.8 / Appendix E.6) — version-bump refuses reuse.

A study created under search-space version 2 must NOT be reused under version 3
(its trials were sampled from a different bound set). The version-compatibility
gate (``assert_search_space_version_compatible``) refuses it. This tests the
gate directly (the gate is what ``run_walkforward_study`` calls after Optuna's
``load_if_exists`` reuses a study by name).
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.errors import OptunaStudyInvalidError
from bowaka_v2_lab.optuna.search_space import SEARCH_SPACE_VERSION
from bowaka_v2_lab.optuna.walkforward_runner import (
    assert_search_space_version_compatible,
)


def test_v2_study_refused_under_v3() -> None:
    with pytest.raises(OptunaStudyInvalidError, match="SEARCH_SPACE_HASH_MISMATCH"):
        assert_search_space_version_compatible(
            {"search_space_version": 2}, study_name="reused", current_version=3,
        )


def test_fresh_study_passes() -> None:
    # no stored version -> fresh study, no raise
    assert_search_space_version_compatible({}, current_version=3)


def test_matching_version_passes() -> None:
    assert_search_space_version_compatible(
        {"search_space_version": SEARCH_SPACE_VERSION},
        current_version=SEARCH_SPACE_VERSION,
    )
