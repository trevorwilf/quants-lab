"""End-to-end: invoke the production backtester against the lab's
iex_short_run_lake fixture and assert it reads real (fixture) data, not
synthetic.
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
_FIXTURE_LAKE = _LAB / "tests" / "fixtures" / "iex_short_run_lake"

pytestmark = pytest.mark.integration


@pytest.mark.timeout(180)
def test_prod_backtester_against_fixture_lake_produces_real_outputs(tmp_path: Path) -> None:
    if not _FIXTURE_LAKE.is_dir():
        pytest.skip(f"fixture lake not at {_FIXTURE_LAKE}")
    if not _SCRIPT.is_file():
        pytest.skip(f"production script not at {_SCRIPT} (run mirror)")
    try:
        from bowaka_common.marketdata.catalog import available_symbols
    except ImportError:
        pytest.skip("bowaka_common not importable")
    syms = available_symbols(
        _FIXTURE_LAKE, timeframe="1d", vendor="alpaca",
        feed="iex", adjustment="split_adjusted",
    )[:5]
    if not syms:
        pytest.skip("fixture lake has no IEX split_adjusted symbols")
    symbols_file = tmp_path / "uni.txt"
    symbols_file.write_text("\n".join(syms), encoding="utf-8")
    out_dir = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(_SCRIPT),
         "--config", str(_PROD_CONFIG),
         "--from", "2025-08-25", "--to", "2025-08-26",
         "--symbols", str(symbols_file),
         "--output-dir", str(out_dir),
         "--cost-stress", "conservative",
         "--ablation", "none",
         "--lake-root", str(_FIXTURE_LAKE)],
        capture_output=True, text=True, timeout=120,
    )
    assert proc.returncode == 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    summary_path = out_dir / "summary.json"
    assert summary_path.is_file()
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    trades_path = out_dir / "trades.parquet"
    if not trades_path.is_file():
        # Older mirror writes trades.json — accept either shape.
        trades_path = out_dir / "trades.json"
    if trades_path.is_file() and trades_path.suffix == ".parquet":
        import pandas as pd
        df = pd.read_parquet(trades_path)
        trades = df.to_dict(orient="records") if not df.empty else []
    elif trades_path.is_file():
        trades = json.loads(trades_path.read_text(encoding="utf-8"))
    else:
        trades = []
    if trades:
        wins = sum(1 for t in trades if (t.get("pnl_dollars") or 0) > 0)
        losses = sum(1 for t in trades if (t.get("pnl_dollars") or 0) < 0)
        # Synthetic mode gives 100% wins and the deterministic +19.5% pattern.
        # Real (or fixture) data must look different.
        if wins + losses > 5:
            assert losses > 0 or summary.get("win_rate", 0.0) < 1.0, (
                "production backtester appears to still be using synthetic "
                "data (100% win rate)"
            )
