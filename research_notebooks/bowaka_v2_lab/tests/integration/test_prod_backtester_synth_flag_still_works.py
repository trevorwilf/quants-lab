"""The ``--synth`` flag must remain functional for smoke runs. Logs a WARNING
when used (per the post-fix script docstring).
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


@pytest.mark.timeout(60)
def test_synth_flag_runs_and_warns(tmp_path: Path) -> None:
    if not _SCRIPT.is_file():
        pytest.skip(f"production script not at {_SCRIPT} (run mirror)")
    symbols_file = tmp_path / "uni.txt"
    symbols_file.write_text("AAA\nBBB\n", encoding="utf-8")
    out_dir = tmp_path / "out"
    proc = subprocess.run(
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
    assert proc.returncode == 0
    combined = proc.stdout + proc.stderr
    assert "synth" in combined.lower()
    assert ("synthetic" in combined.lower()
            or "fictitious" in combined.lower()
            or "WARNING" in combined)
