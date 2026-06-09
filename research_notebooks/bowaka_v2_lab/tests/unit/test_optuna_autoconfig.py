"""Notebook-10 feed auto-detection: SIP > IEX > synthetic."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest
import yaml

from bowaka_v2_lab.devtools.wf_lake import build_tiny_lake
from bowaka_v2_lab.optuna.autoconfig import (
    detect_best_feed,
    lake_has_quotes,
    resolve_walkforward_config,
)

_START = dt.date(2024, 1, 1)
_END = dt.date(2024, 3, 1)


def _write_sip_quote(lake: Path) -> None:
    """Write one quotes partition matching the lake quotes layout for feed=sip."""
    qpath = (
        lake / "quotes" / "vendor=alpaca" / "feed=sip" / "symbol=AAA"
        / "year=2024" / "month=1" / "part.parquet"
    )
    qpath.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {
            "symbol": ["AAA"],
            "timestamp": [pd.Timestamp("2024-01-02 14:00", tz="UTC")],
            "bid": [99.9], "ask": [100.1], "bid_size": [100], "ask_size": [100],
        }
    ).to_parquet(qpath, index=False)


def test_detect_iex_only(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="iex")
    feed, mode, _ = detect_best_feed(lake)
    assert feed == "iex"
    assert mode == "current_code_parity"


def test_detect_sip_bars_no_quotes(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="sip")
    feed, mode, _ = detect_best_feed(lake)
    assert feed == "sip"
    assert mode == "current_code_parity"  # SIP bars but no SIP quotes


def test_detect_sip_with_quotes_is_intended_realism(tmp_path: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="sip")
    _write_sip_quote(lake)
    assert lake_has_quotes(lake, "sip") is True
    feed, mode, _ = detect_best_feed(lake)
    assert feed == "sip"
    assert mode == "intended_realism"


def test_detect_sip_preferred_over_iex(tmp_path: Path) -> None:
    """SIP wins even when IEX bars are also present."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="iex")
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="sip")
    feed, _, _ = detect_best_feed(lake)
    assert feed == "sip"


def test_detect_empty_lake_is_smoke(tmp_path: Path) -> None:
    lake = tmp_path / "empty_lake"
    lake.mkdir()
    _, mode, _ = detect_best_feed(lake)
    assert mode == "smoke_fixture"


def test_resolve_writes_loadable_iex_config(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="iex")
    base = lab_root / "configs" / "bowaka_v2_intended_realism.yml"
    resolved = resolve_walkforward_config(base, lake_root=str(lake))
    assert resolved.feed == "iex"
    assert resolved.mode == "current_code_parity"
    assert resolved.allow_smoke is False
    assert Path(resolved.path).is_file()
    cfg = yaml.safe_load(Path(resolved.path).read_text(encoding="utf-8"))
    assert cfg["market_data"]["feed"] == "iex"
    assert cfg["simulation"]["mode"] == "current_code_parity"


def test_feed_override_synthetic_forces_smoke(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="sip")
    base = lab_root / "configs" / "bowaka_v2_intended_realism.yml"
    resolved = resolve_walkforward_config(base, feed_override="synthetic", lake_root=str(lake))
    assert resolved.mode == "smoke_fixture"
    assert resolved.allow_smoke is True


def test_feed_override_iex_forces_iex(tmp_path: Path, lab_root: Path) -> None:
    """An explicit iex override is honored even when SIP data is present."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="sip")
    base = lab_root / "configs" / "bowaka_v2_intended_realism.yml"
    resolved = resolve_walkforward_config(base, feed_override="iex", lake_root=str(lake))
    assert resolved.feed == "iex"
    assert resolved.mode == "current_code_parity"


def test_mode_override_pins_ccp_while_keeping_sip(tmp_path: Path, lab_root: Path) -> None:
    """SIP+quotes auto-picks intended_realism; ``mode_override`` keeps feed=sip
    but pins current_code_parity (the gap-2 fix for an IR-infeasible lake — e.g.
    no halt data), and the derived opt-in flags follow the EFFECTIVE mode."""
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="sip")
    _write_sip_quote(lake)
    base = lab_root / "configs" / "bowaka_v2_intended_realism.yml"
    # Without the override, auto resolves to intended_realism.
    auto = resolve_walkforward_config(base, lake_root=str(lake))
    assert auto.feed == "sip" and auto.mode == "intended_realism"
    assert auto.allow_current_code_parity_study is False
    # With the override: feed stays sip (matrix/suppliers resolve), mode pinned.
    pinned = resolve_walkforward_config(
        base, mode_override="current_code_parity", lake_root=str(lake))
    assert pinned.feed == "sip"
    assert pinned.mode == "current_code_parity"
    assert pinned.allow_current_code_parity_study is True
    assert pinned.tier == "research_only"
    cfg = yaml.safe_load(Path(pinned.path).read_text(encoding="utf-8"))
    assert cfg["market_data"]["feed"] == "sip"
    assert cfg["simulation"]["mode"] == "current_code_parity"


def test_invalid_mode_override_rejected(tmp_path: Path, lab_root: Path) -> None:
    lake = tmp_path / "lake"
    build_tiny_lake(lake, ["AAA"], start=_START, end=_END, feed="sip")
    base = lab_root / "configs" / "bowaka_v2_intended_realism.yml"
    with pytest.raises(ValueError):
        resolve_walkforward_config(base, mode_override="turbo", lake_root=str(lake))


def test_invalid_feed_override_rejected(lab_root: Path) -> None:
    base = lab_root / "configs" / "bowaka_v2_intended_realism.yml"
    with pytest.raises(ValueError):
        resolve_walkforward_config(base, feed_override="nasdaq")
