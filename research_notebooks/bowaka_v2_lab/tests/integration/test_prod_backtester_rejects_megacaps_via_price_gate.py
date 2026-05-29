"""Regression: with the price gate set to [1.0, 20.0], a universe of
AAPL/TSLA/NVDA/AMD/SPY (all > $50) must produce ZERO trades.

This is the bug signature the operator observed pre-fix: 20 trades over 5 days
on this exact universe (because the synthetic suppliers ignored the symbol
names and served $10 prices). Post-fix, the price gate correctly rejects every
entry.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_LAB = Path(__file__).resolve().parents[2]
_SCRIPT = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_backtest.py"
_PROD_CONFIG = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml"

pytestmark = pytest.mark.integration


@pytest.mark.timeout(180)
def test_megacaps_produce_zero_trades_when_price_gate_active(tmp_path: Path) -> None:
    if not _SCRIPT.is_file():
        pytest.skip(f"production script not at {_SCRIPT} (run mirror)")
    try:
        from bowaka_common.marketdata.catalog import available_symbols
        from bowaka_common.marketdata.store import resolve_market_data_root
    except ImportError:
        pytest.skip("bowaka_common not importable")
    lake_root = resolve_market_data_root(None, create=False)
    syms = available_symbols(
        lake_root, timeframe="1d", vendor="alpaca",
        feed="iex", adjustment="split_adjusted",
    )
    if "AAPL" not in syms:
        pytest.skip("real lake not present (AAPL not in available symbols)")

    symbols_file = tmp_path / "megacaps.txt"
    symbols_file.write_text("AAPL\nTSLA\nNVDA\nAMD\nSPY\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT),
         "--config", str(_PROD_CONFIG),
         "--from", "2026-05-19", "--to", "2026-05-23",
         "--symbols", str(symbols_file),
         "--output-dir", str(out_dir),
         "--cost-stress", "conservative",
         "--ablation", "none"],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    summary = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary.get("trade_count", -1) == 0, (
        f"price gate failed: produced {summary.get('trade_count')} trades on "
        "AAPL/TSLA/NVDA/AMD/SPY (all > $50). Either the price gate isn't being "
        "applied or the synthetic-data bug has regressed."
    )
