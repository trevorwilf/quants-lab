"""Tests for the directional sweep notebook factory."""

import ast
import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from create_sweep_nb_directional import build_notebook


def _collect_code_source(nb_path: Path) -> str:
    with open(nb_path) as f:
        nb = json.load(f)
    parts = []
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            src = "".join(cell["source"])
            parts.append(src)
    return "\n\n".join(parts)


def test_mr_notebook_builds(tmp_path):
    out = build_notebook(
        strategy="mr", connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=5,
        study_name="test_mr", out_dir=tmp_path,
    )
    assert out.exists()
    with open(out) as f:
        nb = json.load(f)
    assert nb["nbformat"] == 4
    assert len(nb["cells"]) > 0


def test_ema_notebook_builds(tmp_path):
    out = build_notebook(
        strategy="ema", connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=5,
        study_name="test_ema", out_dir=tmp_path,
    )
    assert out.exists()


def test_generated_code_parses_as_python_mr(tmp_path):
    out = build_notebook(
        strategy="mr", connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=5,
        study_name="test_parse_mr", out_dir=tmp_path,
    )
    src = _collect_code_source(out)
    # ast.parse over concatenated code cells — the generated code should be
    # syntactically valid Python.
    ast.parse(src)


def test_generated_code_parses_as_python_ema(tmp_path):
    out = build_notebook(
        strategy="ema", connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=5,
        study_name="test_parse_ema", out_dir=tmp_path,
    )
    src = _collect_code_source(out)
    ast.parse(src)


def test_mr_notebook_does_not_reference_regime_candles(tmp_path):
    out = build_notebook(
        strategy="mr", connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=5,
        study_name="test_mr_no_regime", out_dir=tmp_path,
    )
    src = _collect_code_source(out)
    # MR is single-timeframe — regime_candles kwarg should NOT be passed.
    assert "regime_candles=regime_candles" not in src


def test_ema_notebook_references_regime_candles(tmp_path):
    out = build_notebook(
        strategy="ema", connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=5,
        study_name="test_ema_regime", out_dir=tmp_path,
    )
    src = _collect_code_source(out)
    assert "regime_candles=regime_candles" in src
