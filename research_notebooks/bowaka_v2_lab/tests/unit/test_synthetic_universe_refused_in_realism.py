"""Phase 3 — the synthetic universe is refused in non-smoke modes.

``--allow-synthetic-universe`` may be passed only when
``simulation.mode == smoke_fixture``. In any real mode
(``current_code_parity`` / ``intended_realism``) the flag is refused, and the
backtester itself refuses a synthetic universe snapshot.
"""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.cli_runners import _resolve_universe_for_backtest, _load
from bowaka_v2_lab.config.models import BowakaV2Config
from bowaka_v2_lab.sim.backtester import _is_synthetic_universe_snapshot, _normalise_universe_by_session
from bowaka_v2_lab.sim.replay_fixtures import synthetic_universe


def test_synthetic_universe_snapshot_is_detected() -> None:
    """The synthetic fixture is recognised; a PIT snapshot is not."""
    syn = synthetic_universe(["AAA", "BBB"])
    assert _is_synthetic_universe_snapshot(syn) is True
    # A PIT-style snapshot carries synthetic: False.
    assert _is_synthetic_universe_snapshot(
        {"universe_hash": "sha256:abc", "symbols": [], "synthetic": False}
    ) is False


def test_backtester_refuses_synthetic_universe_in_realism() -> None:
    syn_by_session = {_dt.date(2024, 9, 4): synthetic_universe(["AAA"])}
    with pytest.raises(RuntimeError, match="synthetic universe"):
        _normalise_universe_by_session(syn_by_session, sim_mode="intended_realism")
    with pytest.raises(RuntimeError, match="synthetic universe"):
        _normalise_universe_by_session(syn_by_session, sim_mode="current_code_parity")


def test_backtester_allows_synthetic_universe_in_smoke() -> None:
    syn_by_session = {_dt.date(2024, 9, 4): synthetic_universe(["AAA"])}
    snapshots, pit = _normalise_universe_by_session(syn_by_session, sim_mode="smoke_fixture")
    assert pit == {}  # no PIT records for a synthetic universe
    assert _dt.date(2024, 9, 4) in snapshots


def test_allow_synthetic_universe_flag_refused_in_realism(lab_root) -> None:
    """The CLI resolver refuses --allow-synthetic-universe for a non-smoke config."""
    cfg, validated, _paths = _load(
        str(lab_root / "configs" / "bowaka_v2_intended_realism.yml")
    )
    assert validated.simulation.mode == "intended_realism"
    with pytest.raises(RuntimeError, match="allow-synthetic-universe"):
        _resolve_universe_for_backtest(
            cfg, validated, [_dt.date(2024, 9, 4)], cfg.get("market_data", {}),
            ["AAA"], allow_synthetic_universe=True, command="run-backtest",
        )


def test_allow_synthetic_universe_flag_accepted_in_smoke(lab_root) -> None:
    """In smoke mode the flag is accepted and yields the synthetic universe."""
    cfg, validated, _paths = _load(
        str(lab_root / "configs" / "bowaka_v2_backtest_smoke.yml")
    )
    assert validated.simulation.mode == "smoke_fixture"
    universe, kind = _resolve_universe_for_backtest(
        cfg, validated, [_dt.date(2024, 9, 4)], cfg.get("market_data", {}),
        ["AAA", "BBB"], allow_synthetic_universe=True, command="smoke",
    )
    assert kind == "synthetic"
    assert _dt.date(2024, 9, 4) in universe
