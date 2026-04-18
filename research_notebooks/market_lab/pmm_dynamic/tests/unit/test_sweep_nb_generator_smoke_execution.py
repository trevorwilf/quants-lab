"""Smoke-execute the data-load section of generated directional notebooks with a
mocked MongoCandleLoader. ML-DIR-010 & ML-DIR-011 combined regression."""
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))


def _dummy_candles(n: int) -> np.ndarray:
    a = np.zeros(n, dtype=[
        ("timestamp", "i8"), ("open", "f8"), ("high", "f8"),
        ("low", "f8"), ("close", "f8"), ("volume", "f8"),
    ])
    a["timestamp"] = np.arange(n) * 60
    a["close"] = 100.0 + np.arange(n) * 0.01
    a["open"] = a["close"]
    a["high"] = a["close"] + 0.1
    a["low"] = a["close"] - 0.1
    a["volume"] = 1000.0
    return a


@pytest.mark.parametrize("strategy", ["mr", "ema"])
def test_generated_load_section_executes(strategy, tmp_path, monkeypatch):
    from create_sweep_nb_directional import build_notebook
    out = build_notebook(
        strategy=strategy, connector="nonkyc", trading_pair="XMR-USDT",
        interval="5m", regime_interval="4h", n_trials=3,
        study_name=f"test_exec_{strategy}", out_dir=tmp_path,
    )
    with open(out, encoding="utf-8") as f:
        nb = json.load(f)

    exec_ns = {}

    class _MockMongoCandleLoader:
        def __init__(self, *a, **kw):
            pass
        def load_range(self, *a, **kw):
            return _dummy_candles(500)

    fake_mongo_mod = types.ModuleType("pmm_lab.data.mongo")
    fake_mongo_mod.MongoCandleLoader = _MockMongoCandleLoader
    monkeypatch.setitem(sys.modules, "pmm_lab.data.mongo", fake_mongo_mod)

    # Execute each code cell up to and including the one that does loader.load_range(...)
    # Stop BEFORE audit/optimizer cells (they need real feature computation we haven't mocked).
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        # Stop-before markers: an audit/optimizer cell has an actual CALL, not just the import.
        if ("validate_candles(" in src
            or "optuna.create_study" in src
            or "create_objective(" in src
            or "load_exchange_rules()" in src):
            break
        try:
            exec(src, exec_ns)
        except Exception as e:
            pytest.fail(f"{strategy}: generated cell failed: {type(e).__name__}: {e}\n---\n{src}")
        if "load_range" in src and "MongoCandleLoader()" in src:
            break

    assert "candles" in exec_ns, f"{strategy}: candles not loaded in generated notebook"
    if strategy == "ema":
        assert "regime_candles" in exec_ns, "EMA notebook must load regime_candles"
