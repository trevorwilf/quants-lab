"""Phase 3 — parallel parity is identical to the serial chunked run.

Runs the SAME window twice (parallel_workers=1 serial vs 3 parallel) and diffs
the persisted golden bundles: report fields + every prod/lab trade row + the
candidate stream must match (sessions are independent in chunked mode, so the
only difference is execution shape).
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


@pytest.mark.timeout(900)
def test_parallel_matches_serial(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    if not (_PROD_SCRIPT.is_file() and _PROD_CONFIG.is_file() and _LAB_CONFIG.is_file()):
        pytest.skip("source-strategy mirror / configs absent")
    try:
        from bowaka_common.marketdata.catalog import available_symbols
        from bowaka_common.marketdata.store import resolve_market_data_root
    except ImportError:
        pytest.skip("bowaka_common not importable")
    lake_root = resolve_market_data_root(None, create=False)
    syms = available_symbols(
        lake_root, timeframe="1d", vendor="alpaca", feed="iex",
        adjustment="split_adjusted",
    )
    if "AGNC" not in syms:
        pytest.skip("real lake absent")

    from bowaka_v2_lab.parity import run_parity
    from bowaka_v2_lab.parity.golden import diff_parity_bundles

    universe = ["AGNC", "ALHC", "ALT", "BLMN", "CCC", "PACB", "PSEC", "SONO", "VNDA"]
    start, end = _dt.date(2026, 5, 19), _dt.date(2026, 5, 21)  # 3 XNYS sessions
    common = dict(
        start_date=start, end_date=end, symbols=universe,
        prod_config_path=_PROD_CONFIG, lab_config_path=_LAB_CONFIG,
        lake_root=lake_root, cost_stress="base", python_exe=sys.executable,
        chunk_per_session=True, print_progress=False,
    )
    serial_b = tmp_path / "serial_bundle"
    parallel_b = tmp_path / "parallel_bundle"

    run_parity(**common, run_root=tmp_path / "serial",
               parallel_workers=1, bundle_out=serial_b)
    run_parity(**common, run_root=tmp_path / "parallel",
               parallel_workers=3, bundle_out=parallel_b)

    d = diff_parity_bundles(serial_b, parallel_b)
    assert d["match"], (
        f"parallel diverged from serial: report={d['report_diffs']} "
        f"trades={d['trade_diffs']} cands={d['candidate_diffs']}"
    )
