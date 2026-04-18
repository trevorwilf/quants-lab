"""Runtime test: generated directional notebook's load cell actually invokes load_range,
not the nonexistent .load() method. This catches ML-DIR-010 regressions."""
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from create_sweep_nb_directional import build_notebook


def _extract_load_cell_source(nb_path: Path) -> str:
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    # Find the cell that instantiates MongoCandleLoader()
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if "MongoCandleLoader()" in src:
            return src
    raise AssertionError("No loader cell found in notebook")


@pytest.mark.parametrize("strategy", ["mr", "ema"])
def test_generator_emits_load_range_not_load(strategy, tmp_path):
    out = build_notebook(
        strategy=strategy, connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=5,
        study_name=f"test_{strategy}_load_range", out_dir=tmp_path,
    )
    src = _extract_load_cell_source(out)
    # Must call load_range(DataQuery(...))
    assert "load_range(" in src, f"{strategy}: must emit .load_range(...)"
    assert "DataQuery(" in src, f"{strategy}: must emit DataQuery(...)"
    # Must NOT call the nonexistent .load() method
    assert "loader.load(" not in src, (
        f"{strategy}: generator still emits the nonexistent .load() method"
    )


@pytest.mark.parametrize("strategy", ["mr", "ema"])
def test_generated_load_cell_executes_with_mocked_loader(strategy, tmp_path, monkeypatch):
    """Execute the generated load cell with a mocked MongoCandleLoader to confirm it
    actually runs without AttributeError."""
    import numpy as np
    out = build_notebook(
        strategy=strategy, connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=5,
        study_name=f"test_{strategy}_exec", out_dir=tmp_path,
    )
    src = _extract_load_cell_source(out)

    # Build a dummy candle array
    dummy_candles = np.zeros(100, dtype=[
        ("timestamp", "i8"), ("open", "f8"), ("high", "f8"),
        ("low", "f8"), ("close", "f8"), ("volume", "f8"),
    ])
    dummy_candles["timestamp"] = np.arange(100) * 60_000
    dummy_candles["close"] = np.arange(100) + 100.0

    # Mock loader
    mock_loader_instance = MagicMock()
    mock_loader_instance.load_range.return_value = dummy_candles
    MockLoader = MagicMock(return_value=mock_loader_instance)

    from pmm_lab.config.params import DataQuery as RealDataQuery

    exec_ns = {
        "MongoCandleLoader": MockLoader,
        "DataQuery": RealDataQuery,
        "CONNECTOR": "nonkyc",
        "TRADING_PAIR": "XMR-USDT",
        "SIGNAL_INTERVAL": "5m",
        "REGIME_INTERVAL": "4h",
        "print": print,
    }
    # Execute the cell source — must not raise
    exec(src, exec_ns)

    # The mock should have been called with load_range, not load
    mock_loader_instance.load_range.assert_called()
    assert mock_loader_instance.load.call_count == 0, (
        f"{strategy}: mock was called with the nonexistent .load() method"
    )
