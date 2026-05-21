"""import-actual-config is deterministic and produces a valid config.

Realism Phase 1, Task A/D. Running ``import-actual-config`` twice must yield
byte-identical files (deterministic YAML), and the output must validate as a
``BowakaV2Config``.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from bowaka_v2_lab import reference
from bowaka_v2_lab.config.models import BowakaV2Config


def test_import_actual_config_is_byte_identical_on_rerun(tmp_path: Path) -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    out_a = tmp_path / "regen_a.yml"
    out_b = tmp_path / "regen_b.yml"
    for out in (out_a, out_b):
        result = subprocess.run(
            [sys.executable, "-m", "bowaka_v2_lab.cli", "import-actual-config",
             "--out", str(out)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0, f"stderr: {result.stderr}"
        assert out.is_file()
    assert out_a.read_bytes() == out_b.read_bytes(), (
        "import-actual-config output is not byte-identical on re-run"
    )


def test_import_actual_config_output_validates(tmp_path: Path) -> None:
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    out = tmp_path / "regen.yml"
    result = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "import-actual-config", "--out", str(out)],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    raw = yaml.safe_load(out.read_text(encoding="utf-8"))
    validated = BowakaV2Config.model_validate(raw)
    assert validated.strategy_id == "bowaka_v2"
    assert validated.simulation.mode == "intended_realism"


def test_import_actual_config_iex_feed(tmp_path: Path) -> None:
    """--feed iex sets market_data.feed accordingly and still validates."""
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    out = tmp_path / "regen_iex.yml"
    result = subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "import-actual-config",
         "--out", str(out), "--feed", "iex"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    validated = BowakaV2Config.model_validate(yaml.safe_load(out.read_text(encoding="utf-8")))
    assert validated.market_data.feed == "iex"


def test_shipped_realism_config_matches_regenerated(tmp_path: Path) -> None:
    """The shipped configs/bowaka_v2_intended_realism.yml equals a fresh regen."""
    if not reference.contract_available():
        pytest.xfail("frozen contract not generated")
    lab_root = Path(__file__).resolve().parents[2]
    shipped = lab_root / "configs" / "bowaka_v2_intended_realism.yml"
    assert shipped.is_file(), "configs/bowaka_v2_intended_realism.yml not committed"
    out = tmp_path / "regen.yml"
    subprocess.run(
        [sys.executable, "-m", "bowaka_v2_lab.cli", "import-actual-config", "--out", str(out)],
        capture_output=True, text=True, check=True,
    )
    assert shipped.read_bytes() == out.read_bytes(), (
        "shipped intended-realism config drifted from import-actual-config -- regenerate it"
    )
