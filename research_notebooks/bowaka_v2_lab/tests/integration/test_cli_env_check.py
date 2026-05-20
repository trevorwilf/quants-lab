"""CLI env-check on the bundled smoke config exits 0."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_env_check_smoke_exits_zero(lab_root: Path) -> None:
    cfg = lab_root / "configs" / "bowaka_v2_backtest_smoke.yml"
    result = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "env-check", "--config", str(cfg)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["strategy_id"] == "bowaka_v2"
    assert payload["feed"] == "iex"


def test_env_check_sip_config_exits_zero(lab_root: Path) -> None:
    cfg = lab_root / "configs" / "bowaka_v2_research_sip.yml"
    result = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "env-check", "--config", str(cfg)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}\nstdout: {result.stdout}"
    payload = json.loads(result.stdout)
    assert payload["feed"] == "sip"
