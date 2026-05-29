"""End-to-end: ``run_parity`` against the operator's real lake.

Skip-guarded: pyarrow importable + production script present + real lake has
AAPL (a proxy for "the operator's lake is reachable from this host"). This
test does NOT assert audit thresholds pass — a 1-day, 5-symbol window has
too few trades for the metrics to be meaningful. It only proves the
end-to-end plumbing works.
"""
from __future__ import annotations

import datetime as _dt
import sys
from pathlib import Path

import pytest

_LAB = Path(__file__).resolve().parents[2]
_PROD_SCRIPT = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_backtest.py"
_PROD_CONFIG = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml"
_LAB_CONFIG = _LAB / "configs" / "bowaka_v2_actual_iex_current_code.yml"

pytestmark = pytest.mark.integration


@pytest.mark.timeout(600)
def test_run_parity_plumbing_returns_report(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    if not _PROD_SCRIPT.is_file():
        pytest.skip(f"production script not at {_PROD_SCRIPT} (run mirror)")
    if not _PROD_CONFIG.is_file():
        pytest.skip(f"production config not at {_PROD_CONFIG}")
    if not _LAB_CONFIG.is_file():
        pytest.skip(f"lab config not at {_LAB_CONFIG}")
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

    from bowaka_v2_lab.parity import ParityReport, run_parity

    # Tiny universe of 5 symbols and a 1-day window so the runner finishes fast.
    universe = syms[:5]
    start = _dt.date(2026, 5, 19)
    report = run_parity(
        start_date=start, end_date=start, symbols=universe,
        prod_config_path=_PROD_CONFIG, lab_config_path=_LAB_CONFIG,
        lake_root=lake_root, cost_stress="conservative",
        run_root=tmp_path / "run",
        python_exe=sys.executable, python_extra=(),
    )
    assert isinstance(report, ParityReport)
    assert report.window_start == start
    assert report.window_end == start
    assert report.universe_size == len(universe)
    assert report.prod_n_trades >= 0
    assert report.lab_n_trades >= 0
    # The report carries pass/fail booleans regardless of magnitude.
    assert isinstance(report.passes_audit_thresholds, bool)
