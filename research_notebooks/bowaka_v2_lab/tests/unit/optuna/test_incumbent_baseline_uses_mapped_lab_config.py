"""Phase 2 (audit 2026-05-29 §6.7 / Appendix E.3) — incumbent reads mapped config.

The incumbent (Trial 0) must be the ACTUAL strategy, read from the mapped lab
config (flat keys, derived gap/ratio), with NOTHING padded from search-space
midpoints. The pre-fix run padded execution.max_quote_age_seconds (60) and
execution.max_spread_bps (102); the actual contract values are 15 / 100.
"""
from __future__ import annotations

import pytest

from bowaka_v2_lab.optuna.walkforward_runner import _incumbent_baseline_params
from bowaka_v2_lab.reference import contract_available, load_actual_contract
from bowaka_v2_lab.reference.import_config import build_config_from_contract


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not contract_available():
        pytest.xfail("frozen contract not generated — run mirror_bowaka_v2_source.ps1")


def test_incumbent_maps_every_key_without_padding(caplog) -> None:
    cfg = build_config_from_contract(
        load_actual_contract(),
        feed="iex", mode="current_code_parity", feed_thresholds="actual",
    )
    with caplog.at_level("WARNING"):
        p = _incumbent_baseline_params(lab_config=cfg)

    assert p["execution.max_quote_age_seconds"] == 15
    assert p["execution.max_spread_bps"] == 100
    assert p["exits.stop_pct"] == pytest.approx(0.025)
    assert p["exits.signal_fade.score_thresholds.soft"] == pytest.approx(0.34)
    assert p["exits.signal_fade.score_thresholds.hard_gap"] == pytest.approx(0.16)
    assert p["exits.signal_fade.score_thresholds.critical_gap"] == pytest.approx(0.17)
    assert p["exits.reward_risk_ratio"] == pytest.approx(6.0)
    assert p["sizing.equal_slice_bankroll_fraction"] == pytest.approx(0.80)
    # No padding — not via the old WARNING, not via any side channel.
    assert "incumbent baseline padded" not in caplog.text


def test_incumbent_has_no_pre_v3_threshold_keys() -> None:
    cfg = build_config_from_contract(
        load_actual_contract(),
        feed="iex", mode="current_code_parity", feed_thresholds="actual",
    )
    p = _incumbent_baseline_params(lab_config=cfg)
    # The v3 search space samples gap/ratio, not the absolute hard/critical/
    # target_pct — those must NOT appear as incumbent search params.
    assert "exits.signal_fade.score_thresholds.hard" not in p
    assert "exits.signal_fade.score_thresholds.critical" not in p
    assert "exits.target_pct" not in p
