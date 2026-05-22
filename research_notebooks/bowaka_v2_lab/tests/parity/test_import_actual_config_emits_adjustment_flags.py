"""import-actual-config emits the contract's adjustment / freshness flags.

Realism remediation 2 Phase 1 (audit §P0-005). A config generated from the
frozen contract must carry ``market_data.require_adjusted_daily_bars: true``,
``market_data.require_split_adjustment: true`` and ``max_bar_age_seconds: 90`` —
the live contract's ``data:`` block requires adjusted + split-adjusted daily
bars, and the generated config must not silently drop that.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab import reference


@pytest.fixture(autouse=True)
def _require_contract() -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated -- run mirror_bowaka_v2_source.ps1")


def _generate(tmp_path: Path, *, feed: str, mode: str) -> dict:
    out = tmp_path / f"gen_{feed}_{mode}.yml"
    result = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "import-actual-config",
         "--out", str(out), "--feed", feed, "--mode", mode],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    return yaml.safe_load(out.read_text(encoding="utf-8"))


@pytest.mark.parametrize("feed", ["iex", "sip"])
@pytest.mark.parametrize("mode", ["intended_realism", "current_code_parity"])
def test_generated_config_carries_adjustment_flags(
    tmp_path: Path, feed: str, mode: str
) -> None:
    cfg = _generate(tmp_path, feed=feed, mode=mode)
    md = cfg["market_data"]
    assert md["require_adjusted_daily_bars"] is True, (
        f"{feed}/{mode} config dropped require_adjusted_daily_bars"
    )
    assert md["require_split_adjustment"] is True, (
        f"{feed}/{mode} config dropped require_split_adjustment"
    )
    assert md["max_bar_age_seconds"] == 90, (
        f"{feed}/{mode} config max_bar_age_seconds is not the contract's 90"
    )
    assert md["max_quote_age_seconds"] == 15, (
        f"{feed}/{mode} config max_quote_age_seconds is not the contract's 15"
    )


def test_shipped_actual_configs_carry_adjustment_flags() -> None:
    """The three committed bowaka_v2_actual_* configs carry the flags."""
    lab_root = Path(__file__).resolve().parents[2]
    for name in (
        "bowaka_v2_actual_iex_current_code.yml",
        "bowaka_v2_actual_iex_intended_realism.yml",
        "bowaka_v2_actual_sip_intended_realism.yml",
    ):
        path = lab_root / "configs" / name
        assert path.is_file(), f"{name} not committed"
        md = yaml.safe_load(path.read_text(encoding="utf-8"))["market_data"]
        assert md["require_adjusted_daily_bars"] is True, name
        assert md["require_split_adjustment"] is True, name
        assert md["max_bar_age_seconds"] == 90, name
