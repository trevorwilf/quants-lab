"""IEX Optuna studies record the partial_tape flag + iex__ name prefix.

Realism remediation 2 Phase 10 (audit §P1-010). An IEX study must announce
its partial-tape nature at every observable surface: the study name carries
the ``iex__`` prefix, ``study.user_attrs["partial_tape"]`` is ``True``, and
the IEX feed caveat travels through ``study.user_attrs["feed_caveat"]``.
SIP / non-IEX studies must NOT carry the prefix and must record
``partial_tape: false``.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.dispatcher import (
    IEX_STUDY_PREFIX,
    OptunaStudy,
    build_study_name,
)


def test_iex_study_name_carries_iex_prefix() -> None:
    """``build_study_name(feed='iex', ...)`` returns a name with ``iex__`` prefix."""
    name = build_study_name(
        feed="iex", cost_stress="base", dataset_hash="abcdef1234567890",
    )
    assert name.startswith(IEX_STUDY_PREFIX), (
        f"IEX study name must start with {IEX_STUDY_PREFIX!r}; got {name!r}"
    )
    # The legacy body is still embedded — feed remains queryable in the name.
    assert "bowaka_v2_iex_walkforward_base_abcdef12_" in name


def test_sip_study_name_has_no_iex_prefix() -> None:
    """SIP study names are NOT prefixed."""
    name = build_study_name(
        feed="sip", cost_stress="conservative", dataset_hash="cafebabecafebabe",
    )
    assert not name.startswith(IEX_STUDY_PREFIX)
    assert name.startswith("bowaka_v2_sip_walkforward_conservative_")


def test_iex_study_user_attrs_carry_partial_tape_flag() -> None:
    """An IEX study's ``user_attrs`` carries ``partial_tape: True`` and ``feed_caveat``."""
    s = OptunaStudy(
        feed="iex", cost_stress="base",
        dataset_hash="cafebabecafebabe",
        config_hash="deadbeefdeadbeef",
        storage_uri=None, n_trials=1,
    )
    s.create()
    attrs = s.study.user_attrs
    assert attrs.get("feed") == "iex"
    assert attrs.get("partial_tape") is True, (
        "IEX studies must carry partial_tape=True in user_attrs"
    )
    assert attrs.get("feed_caveat") == "partial_tape_features", (
        "IEX studies must carry feed_caveat='partial_tape_features' in user_attrs"
    )
    # Study name also reflects the prefix.
    assert s.study.study_name.startswith(IEX_STUDY_PREFIX)


def test_sip_study_user_attrs_record_partial_tape_false() -> None:
    """A SIP study records ``partial_tape: False`` and no feed_caveat."""
    s = OptunaStudy(
        feed="sip", cost_stress="conservative",
        dataset_hash="cafebabecafebabe",
        config_hash="deadbeefdeadbeef",
        storage_uri=None, n_trials=1,
    )
    s.create()
    attrs = s.study.user_attrs
    assert attrs.get("feed") == "sip"
    assert attrs.get("partial_tape") is False, (
        "SIP studies must carry partial_tape=False (the flag is always set)"
    )
    # No feed_caveat for SIP.
    assert "feed_caveat" not in attrs, (
        "SIP studies must not carry feed_caveat (no partial-tape caveat for SIP)"
    )
    # Study name has no IEX prefix.
    assert not s.study.study_name.startswith(IEX_STUDY_PREFIX)


def test_iex_promotion_attempt_raises_iex_promotion_blocked() -> None:
    """``mark_promotion_eligible`` on an IEX study raises IEXPromotionBlocked."""
    from bowaka_v2_lab.promotion.suitability import IEXPromotionBlocked

    s = OptunaStudy(
        feed="iex", cost_stress="base",
        dataset_hash="cafebabecafebabe",
        config_hash="deadbeefdeadbeef",
        storage_uri=None, n_trials=1,
    )
    with pytest.raises(IEXPromotionBlocked):
        s.mark_promotion_eligible()
    # Still also a RuntimeError so the existing test surface holds.
    assert issubclass(IEXPromotionBlocked, RuntimeError)
