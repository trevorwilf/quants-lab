"""IEX promotion gate refuses any tier > research_only (audit §P1-010).

Realism remediation 2 Phase 10. The IEX cap is mechanical: every code path
that *writes* a suitability tier onto an IEX artifact must refuse to set
``suitability_tier`` above ``research_only`` — raising
:class:`IEXPromotionBlocked`. SIP / other-feed artifacts are unaffected.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.promotion.suitability import (
    FEED_CAVEAT_PARTIAL_TAPE,
    IEXPromotionBlocked,
    assert_not_above_research_only_for_iex,
    build_suitability_artifact,
    feed_caveat_for,
)


def test_feed_caveat_for_iex_returns_partial_tape_label() -> None:
    assert feed_caveat_for("iex") == FEED_CAVEAT_PARTIAL_TAPE
    assert feed_caveat_for("IEX") == FEED_CAVEAT_PARTIAL_TAPE


def test_feed_caveat_for_sip_returns_none() -> None:
    assert feed_caveat_for("sip") is None


def test_feed_caveat_for_empty_returns_none() -> None:
    assert feed_caveat_for(None) is None
    assert feed_caveat_for("") is None


@pytest.mark.parametrize("tier", ["backtesting_only", "paper_candidate", "live_candidate"])
def test_assert_iex_above_research_only_raises_iex_promotion_blocked(tier: str) -> None:
    """Setting any tier > research_only on a feed:iex artifact raises."""
    with pytest.raises(IEXPromotionBlocked, match="research_only"):
        assert_not_above_research_only_for_iex(
            feed="iex", proposed_tier=tier, context="phase10_test",
        )


def test_assert_iex_research_only_does_not_raise() -> None:
    """research_only is the explicit IEX cap — no raise."""
    assert_not_above_research_only_for_iex(
        feed="iex", proposed_tier="research_only", context="phase10_ok",
    )


def test_assert_sip_above_research_only_does_not_raise() -> None:
    """SIP feeds are not affected by the IEX gate."""
    assert_not_above_research_only_for_iex(
        feed="sip", proposed_tier="backtesting_only", context="phase10_sip",
    )
    assert_not_above_research_only_for_iex(
        feed="sip", proposed_tier="paper_candidate", context="phase10_sip",
    )


def test_assert_unknown_tier_does_not_raise() -> None:
    """An unknown tier name does not trip the IEX gate."""
    assert_not_above_research_only_for_iex(
        feed="iex", proposed_tier="bogus_tier_name", context="phase10_unknown",
    )


def test_build_suitability_artifact_iex_caps_at_research_only_with_caveat() -> None:
    """The standard IEX-artifact envelope carries research_only + feed_caveat."""
    art = build_suitability_artifact(feed="iex", simulation_contract="intended_realism")
    assert art["feed"] == "iex"
    assert art["suitability_tier"] == "research_only", (
        "IEX artifacts must be capped at research_only"
    )
    assert art["feed_caveat"] == "partial_tape_features"
    assert art["simulation_contract"] == "intended_realism"


def test_build_suitability_artifact_iex_raises_when_caller_forces_higher_tier() -> None:
    """Forcing a higher tier on an IEX artifact raises IEXPromotionBlocked."""
    with pytest.raises(IEXPromotionBlocked):
        build_suitability_artifact(
            feed="iex", simulation_contract="intended_realism", tier="paper_candidate",
        )


def test_build_suitability_artifact_sip_does_not_carry_feed_caveat() -> None:
    """SIP artifacts have no feed_caveat (and respect the contract cap)."""
    art = build_suitability_artifact(
        feed="sip", simulation_contract="intended_realism",
    )
    assert art["feed"] == "sip"
    # ``intended_realism`` contract default is backtesting_only.
    assert art["suitability_tier"] == "backtesting_only"
    assert "feed_caveat" not in art


def test_optuna_iex_dispatcher_blocks_promotion() -> None:
    """The Optuna dispatcher's mark_promotion_eligible call raises IEXPromotionBlocked."""
    from bowaka_v2_lab.optuna.dispatcher import OptunaStudy

    s = OptunaStudy(
        feed="iex", cost_stress="base",
        dataset_hash="cafebabecafebabe",
        config_hash="deadbeefdeadbeef",
        storage_uri=None, n_trials=1,
    )
    # The exception is IEXPromotionBlocked, which is a RuntimeError so the
    # existing parity test that uses ``pytest.raises(RuntimeError)`` still works.
    with pytest.raises(IEXPromotionBlocked):
        s.mark_promotion_eligible()


def test_iex_promotion_blocked_is_runtime_error() -> None:
    """IEXPromotionBlocked subclasses RuntimeError (backward-compatible)."""
    assert issubclass(IEXPromotionBlocked, RuntimeError)
