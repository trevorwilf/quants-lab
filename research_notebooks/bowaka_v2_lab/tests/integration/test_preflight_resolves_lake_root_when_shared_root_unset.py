"""Regression: a workstation-shape config with no ``market_data.shared_root``
must NOT make the preflight raise ``daily_adjustment_partition`` even though the
lake has every required partition on disk.

Hotfix 2026-05-29 — root cause was ``Path(str(None)) == Path('None')``.
"""
from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.integration
def test_preflight_resolves_lake_root_from_default_chain_when_md_shared_root_unset(
    tmp_path, monkeypatch
):
    from bowaka_common.marketdata.layout import bars_timeframe_root

    split_dir = bars_timeframe_root(
        tmp_path, "1d", vendor="alpaca", feed="iex",
        adjustment="split_adjusted",
    )
    (split_dir / "symbol=AAAA").mkdir(parents=True)

    monkeypatch.setenv("MARKET_DATA_ROOT", str(tmp_path))

    cfg = {
        "market_data": {
            "feed": "iex",
            "require_split_adjustment": True,
            # intentionally NO 'shared_root' key
        },
        "simulation": {"mode": "current_code_parity"},
        "preflight": {"min_pit_universe_per_fold": 1},
    }

    from bowaka_v2_lab.data.lineage import resolve_lake_root
    resolved = resolve_lake_root(cfg)
    assert Path(str(resolved)).resolve() == tmp_path.resolve()

    from bowaka_v2_lab.optuna.autoconfig import probe_lake_capability
    cap = probe_lake_capability(resolved, "iex",
                                required_adjustment="split_adjusted")
    assert cap.has_required_daily_adjustment, (
        "lake has the partition but the probe says it does not — the "
        "'Path(None)' bug has regressed"
    )
