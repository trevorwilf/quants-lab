"""End-to-end: ``run_parity`` against the REAL SIP lake (P2 enforced lane).

The §6 "lab vs live on real bars" gate. On an ordinary host this SKIPS; in the
ql-jupyter container with ``BOWAKA_REAL_DATA_LANE=1`` +
``MARKET_DATA_ROOT=/opt/market_data_cache`` it RUNS and a missing lake FAILS (see
:mod:`tests._real_data_lane`). Proves the lab<->prod parity plumbing runs
end-to-end on real bars; it does NOT assert audit thresholds (the 4-session
golden window has too few trades for the metrics to be meaningful).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tests._real_data_lane import require_real_lake

_LAB = Path(__file__).resolve().parents[2]
_PROD_SCRIPT = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_backtest.py"
_PROD_CONFIG = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml"
_LAB_CONFIG = _LAB / "configs" / "bowaka_v2_actual_sip_current_code.yml"

pytestmark = pytest.mark.integration


@pytest.mark.timeout(600)
def test_run_parity_plumbing_returns_report_on_real_lake(tmp_path: Path) -> None:
    pytest.importorskip("pyarrow")
    lake_root = require_real_lake("IREN", feed="sip")
    assert _PROD_SCRIPT.is_file(), f"production mirror script missing at {_PROD_SCRIPT}"
    assert _PROD_CONFIG.is_file(), f"production config missing at {_PROD_CONFIG}"
    assert _LAB_CONFIG.is_file(), f"lab SIP config missing at {_LAB_CONFIG}"

    from bowaka_v2_lab.parity import ParityReport, run_parity
    from bowaka_v2_lab.parity.golden_sample import (
        GOLDEN_COST_STRESS, GOLDEN_END, GOLDEN_START, GOLDEN_SYMBOLS,
    )

    universe = list(GOLDEN_SYMBOLS[:8])
    report = run_parity(
        start_date=GOLDEN_START, end_date=GOLDEN_END, symbols=universe,
        prod_config_path=_PROD_CONFIG, lab_config_path=_LAB_CONFIG,
        lake_root=lake_root, cost_stress=GOLDEN_COST_STRESS,
        run_root=tmp_path / "run",
        python_exe=sys.executable, python_extra=(),
    )
    assert isinstance(report, ParityReport)
    assert report.window_start == GOLDEN_START
    assert report.window_end == GOLDEN_END
    assert report.universe_size == len(universe)
    # Real bars flowed through both engines (plumbing intact); magnitudes are not
    # asserted (too few trades on a 4-session window).
    assert report.prod_n_trades >= 0
    assert report.lab_n_trades >= 0
    assert isinstance(report.passes_audit_thresholds, bool)
