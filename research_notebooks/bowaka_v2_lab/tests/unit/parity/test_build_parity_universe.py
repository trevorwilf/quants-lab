"""``build_parity_universe`` mirrors bowaka_v2's screen → monitor flow.

The function must:
  - resolve the XNYS sessions in the window,
  - call ``build_pit_universe_for_sessions`` with the lab config + lake store,
  - reduce each session to ``eligible_symbols`` (the bowaka-equity-bucket
    survivors — the universe the live strategy would actually monitor),
  - return the sorted union across sessions,
  - honor ``max_universe_size`` for fast smoke runs.
"""
from __future__ import annotations

import datetime as _dt
from pathlib import Path
from unittest import mock

import pytest
import yaml

from bowaka_v2_lab.parity.runner import build_parity_universe


def _write_minimal_lab_config(tmp_path: Path) -> Path:
    cfg = {
        "strategy_id": "screen_monitor_parity",
        "simulation": {"mode": "smoke_fixture"},
        "universe": {"symbols": []},
        "backtest": {"start_date": "2026-05-19", "end_date": "2026-05-19"},
        "market_data": {"minute_bar_source": "fixture", "shared_root": str(tmp_path / "lake")},
    }
    p = tmp_path / "lab.yml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")
    return p


def _records(eligible: list[str], rejected: list[str]) -> dict:
    """A minimal records-like dict that ``eligible_symbols`` can read."""
    out = {}
    for s in eligible:
        out[s] = mock.MagicMock(eligible_for_bowaka_equity_bucket=True)
    for s in rejected:
        out[s] = mock.MagicMock(eligible_for_bowaka_equity_bucket=False)
    return out


def test_returns_sorted_union_of_eligibles_across_sessions(tmp_path: Path) -> None:
    cfg_path = _write_minimal_lab_config(tmp_path)
    with (
        mock.patch("bowaka_v2_lab.cli_runners._lake_store", return_value=mock.MagicMock()),
        mock.patch(
            "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
            return_value={
                _dt.date(2026, 5, 19): _records(
                    eligible=["CCC", "AAA"], rejected=["ZZZ"],
                ),
                _dt.date(2026, 5, 20): _records(
                    eligible=["BBB", "AAA"], rejected=[],
                ),
            },
        ),
    ):
        out = build_parity_universe(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 20),
            lab_config_path=cfg_path,
        )
    # Sorted, deduped, only eligibles.
    assert out == ["AAA", "BBB", "CCC"]


def test_max_universe_size_caps_output(tmp_path: Path) -> None:
    cfg_path = _write_minimal_lab_config(tmp_path)
    with (
        mock.patch("bowaka_v2_lab.cli_runners._lake_store", return_value=mock.MagicMock()),
        mock.patch(
            "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
            return_value={
                _dt.date(2026, 5, 19): _records(
                    eligible=["AAA", "BBB", "CCC", "DDD", "EEE", "FFF"],
                    rejected=[],
                ),
            },
        ),
    ):
        out = build_parity_universe(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 19),
            lab_config_path=cfg_path,
            max_universe_size=3,
        )
    assert out == ["AAA", "BBB", "CCC"]


def test_empty_screen_returns_empty_list(tmp_path: Path) -> None:
    cfg_path = _write_minimal_lab_config(tmp_path)
    with (
        mock.patch("bowaka_v2_lab.cli_runners._lake_store", return_value=mock.MagicMock()),
        mock.patch(
            "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
            return_value={_dt.date(2026, 5, 19): _records([], rejected=["X", "Y"])},
        ),
    ):
        out = build_parity_universe(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 19),
            lab_config_path=cfg_path,
        )
    assert out == []


def test_lake_root_override_pins_market_data_shared_root(tmp_path: Path) -> None:
    """When lake_root is passed, it must override cfg.market_data.shared_root.

    This is the path used by ``_lake_store`` to construct a MarketDataStore.
    Without the override, the function would read from whatever shared_root
    happens to be in the lab config — which may be unset or wrong.
    """
    cfg_path = _write_minimal_lab_config(tmp_path)
    custom_root = tmp_path / "custom_lake"
    captured_md = {}

    def _fake_lake_store(md: dict):
        captured_md.update(md)
        return mock.MagicMock()

    with (
        mock.patch("bowaka_v2_lab.cli_runners._lake_store", side_effect=_fake_lake_store),
        mock.patch(
            "bowaka_v2_lab.universe.builder.build_pit_universe_for_sessions",
            return_value={_dt.date(2026, 5, 19): _records(["AAA"], [])},
        ),
    ):
        build_parity_universe(
            start_date=_dt.date(2026, 5, 19),
            end_date=_dt.date(2026, 5, 19),
            lab_config_path=cfg_path,
            lake_root=custom_root,
        )
    assert captured_md.get("shared_root") == str(custom_root)
