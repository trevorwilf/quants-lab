"""Deterministic run-id generation."""
from __future__ import annotations

import datetime as _dt

import pytest

from bowaka_v2_lab.utils.ids import generate_run_id


def test_run_id_is_deterministic() -> None:
    cfg_h = "abcdef1234567890"
    ds_h = "0123456789abcdef"
    rid = generate_run_id(
        kind="backtest", cfg_hash=cfg_h, dataset_hash=ds_h, on_date=_dt.date(2026, 5, 20)
    )
    assert rid == "20260520_bowaka_v2_backtest_abcdef12_01234567"


def test_run_id_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="unknown run kind"):
        generate_run_id(kind="bogus", cfg_hash="abcdef12", dataset_hash="01234567")


def test_run_id_rejects_short_hashes() -> None:
    with pytest.raises(ValueError, match="at least 8"):
        generate_run_id(kind="backtest", cfg_hash="abc", dataset_hash="01234567")
    with pytest.raises(ValueError, match="at least 8"):
        generate_run_id(kind="backtest", cfg_hash="abcdef12", dataset_hash="01")


def test_run_id_uses_today_by_default() -> None:
    rid = generate_run_id(kind="smoke", cfg_hash="abcdef12345", dataset_hash="0123456789ab")
    assert rid.startswith(_dt.date.today().strftime("%Y%m%d"))
