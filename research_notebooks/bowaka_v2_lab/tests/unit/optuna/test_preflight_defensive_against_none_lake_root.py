"""Hotfix 2026-05-29 — _coerce_lake_root never yields Path('None') / Path('')."""
from __future__ import annotations

from pathlib import Path

from bowaka_common.marketdata.store import resolve_market_data_root
from bowaka_v2_lab.optuna.preflight import _coerce_lake_root


def test_none_resolves_to_standard_chain() -> None:
    got = _coerce_lake_root(None)
    assert isinstance(got, Path)
    assert got == resolve_market_data_root(None, create=False)
    assert got != Path("None")


def test_blank_strings_fall_through_to_resolver() -> None:
    expected = resolve_market_data_root(None, create=False)
    for blank in ("", "   "):
        got = _coerce_lake_root(blank)
        assert got == expected
        assert got != Path(blank)


def test_explicit_path_is_preserved(tmp_path: Path) -> None:
    assert _coerce_lake_root(tmp_path) == tmp_path
