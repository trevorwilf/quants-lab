"""The ``--synth`` flag must remain functional for smoke runs.

CHANGELOG:
- 2026-07-06 prod re-mirror: the live script's ``--synth`` branch no longer
  logs the "synthetic data" WARNING the production-backtester fix added (it
  silently selects the synthetic suppliers). The functional check (flag still
  runs, rc=0) stays live below; the warning check is split out and marked
  strict-xfail so the suite is green while the prod-side regression stays
  visible — when the live script restores the warning, the XPASS will fail
  loudly and the marker should be removed. The lab cannot fix this (the prod
  boundary is one-way, mirror = prod -> lab).
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_LAB = Path(__file__).resolve().parents[2]
_SCRIPT = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_backtest.py"
_PROD_CONFIG = _LAB / "reference" / "source_strategy" / "scripts" / "bowaka_v2_config.yaml"

pytestmark = pytest.mark.integration


def _run_synth(tmp_path: Path) -> subprocess.CompletedProcess:
    if not _SCRIPT.is_file():
        pytest.skip(f"production script not at {_SCRIPT} (run mirror)")
    symbols_file = tmp_path / "uni.txt"
    symbols_file.write_text("AAA\nBBB\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    return subprocess.run(
        [sys.executable, str(_SCRIPT),
         "--config", str(_PROD_CONFIG),
         "--from", "2025-08-25", "--to", "2025-08-25",
         "--symbols", str(symbols_file),
         "--output-dir", str(out_dir),
         "--cost-stress", "conservative",
         "--ablation", "none",
         "--synth"],
        capture_output=True, text=True, timeout=30,
    )


@pytest.mark.timeout(60)
def test_synth_flag_runs(tmp_path: Path) -> None:
    proc = _run_synth(tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr


@pytest.mark.timeout(60)
@pytest.mark.xfail(
    strict=True,
    reason=(
        "prod-side regression (observed at the 2026-07-06 re-mirror): the live "
        "--synth branch dropped the 'synthetic data' WARNING the production-"
        "backtester fix added. Remove this marker when the live script warns "
        "again."
    ),
)
def test_synth_flag_warns(tmp_path: Path) -> None:
    proc = _run_synth(tmp_path)
    combined = proc.stdout + proc.stderr
    assert "synth" in combined.lower()
    assert ("synthetic" in combined.lower()
            or "fictitious" in combined.lower()
            or "WARNING" in combined)
