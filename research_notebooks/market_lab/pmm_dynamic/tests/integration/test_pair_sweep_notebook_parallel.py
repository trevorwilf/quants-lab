"""Notebook-driven sweep: parallel vs serial via the ACTUAL cell-8 dispatch.

Tests that the wired-up `_run_one_pair` + dispatcher in cell 8 (not just the
pair_worker primitive) runs pairs concurrently when `PAIR_JOBS > 1`.

Uses an in-process MOCK pipeline: we replicate cell 8's dispatcher pattern
around a stand-in `_run_one_pair` that sleeps. This isolates the dispatch
logic from the heavy pipeline (Optuna/Mongo/etc) while still proving the
dispatcher behaves correctly.

A companion test actually parses the committed cell-8 source and exec()s
the dispatcher block with a mocked `_run_one_pair` to catch wiring bugs
in the cell itself (e.g., f-string brace-escaping regressions).
"""

from __future__ import annotations

import json
import re
import textwrap
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

_ROOT = Path(__file__).resolve().parents[2]
_NOTEBOOKS = [
    _ROOT / "notebooks" / "direction-custom" / name
    for name in (
        "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    )
]


def _sweep_cell_source(nb_path: Path) -> str:
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    for cell in nb["cells"]:
        if cell["cell_type"] != "code":
            continue
        src = cell["source"]
        if isinstance(src, list):
            src = "".join(src)
        if "_pair_bar = tqdm" in src:
            return src
    raise AssertionError(f"No sweep cell in {nb_path.name}")


def _dispatcher_block(src: str) -> str:
    """Extract just the `if PAIR_JOBS <= 1: ... _pair_bar.close()` dispatcher
    from cell 8 source, so tests can exec it in isolation."""
    lines = src.splitlines(keepends=True)
    start = None
    end = None
    for i, l in enumerate(lines):
        if start is None and l.startswith("if PAIR_JOBS <= 1:"):
            start = i
        if start is not None and "_pair_bar.close()" in l:
            end = i + 1
            break
    if start is None or end is None:
        raise AssertionError("Couldn't locate dispatcher in cell source")
    return "".join(lines[start:end])


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_dispatcher_serial_path_runs_pairs(nb_path):
    """PAIR_JOBS=1 branch: runs every candidate pair through _run_one_pair, once."""
    dispatcher_src = _dispatcher_block(_sweep_cell_source(nb_path))

    called: list[tuple[int, dict]] = []

    def mock_run_one_pair(pair_idx, pair_info):
        called.append((pair_idx, pair_info))

    class _Bar:
        def __init__(self):
            self.updates = 0
        def update(self, n=1):
            self.updates += n
        def close(self):
            pass

    candidates = [{"connector": "mexc", "trading_pair": f"P{i}-USDT", "interval": "5m"}
                  for i in range(3)]
    bar = _Bar()
    ns = {
        "PAIR_JOBS": 1,
        "N_JOBS": 8,
        "candidates": candidates,
        "_run_one_pair": mock_run_one_pair,
        "_pair_bar": bar,
    }
    exec(dispatcher_src, ns)

    assert len(called) == 3
    assert [c[0] for c in called] == [0, 1, 2]
    assert bar.updates == 3


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_dispatcher_parallel_path_uses_threadpool(nb_path):
    """PAIR_JOBS=4 branch: runs every pair in a ThreadPoolExecutor. Measures
    wall time to confirm concurrent execution (each pair sleeps 0.3s; serial
    would be 1.2s, parallel should be ~0.3s)."""
    dispatcher_src = _dispatcher_block(_sweep_cell_source(nb_path))

    called = []
    called_lock = None  # threads share the list; Python's append is thread-safe

    def mock_run_one_pair(pair_idx, pair_info):
        time.sleep(0.3)
        called.append(pair_idx)

    class _Bar:
        def __init__(self):
            self.updates = 0
        def update(self, n=1):
            self.updates += n
        def close(self):
            pass

    candidates = [{"connector": "mexc", "trading_pair": f"P{i}-USDT", "interval": "5m"}
                  for i in range(4)]
    bar = _Bar()
    ns = {
        "PAIR_JOBS": 4,
        "N_JOBS": 8,
        "candidates": candidates,
        "_run_one_pair": mock_run_one_pair,
        "_pair_bar": bar,
    }
    t0 = time.perf_counter()
    exec(dispatcher_src, ns)
    wall = time.perf_counter() - t0

    assert len(called) == 4
    assert set(called) == {0, 1, 2, 3}
    assert bar.updates == 4
    # 4 threads × 0.3s each: parallel should be well under serial's ~1.2s.
    # Allow generous threshold to avoid CI flakiness.
    assert wall < 0.9, (
        f"Parallel wall time {wall:.2f}s not significantly < serial 1.2s — "
        f"dispatcher is not actually running pairs concurrently"
    )


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_dispatcher_isolates_errors(nb_path):
    """A pair that raises in _run_one_pair must not kill the pool."""
    dispatcher_src = _dispatcher_block(_sweep_cell_source(nb_path))

    call_log = []

    def mock_run_one_pair(pair_idx, pair_info):
        call_log.append(pair_idx)
        if pair_idx == 1:
            raise RuntimeError("simulated pair failure")

    class _Bar:
        def __init__(self):
            self.updates = 0
        def update(self, n=1):
            self.updates += n
        def close(self):
            pass

    for pj in (1, 4):
        call_log.clear()
        candidates = [{"connector": "mexc", "trading_pair": f"P{i}-USDT", "interval": "5m"}
                      for i in range(3)]
        bar = _Bar()
        ns = {
            "PAIR_JOBS": pj,
            "N_JOBS": 8,
            "candidates": candidates,
            "_run_one_pair": mock_run_one_pair,
            "_pair_bar": bar,
        }
        # Dispatcher catches exceptions per-pair and prints. Must not raise.
        exec(dispatcher_src, ns)
        assert len(call_log) == 3, f"PAIR_JOBS={pj}: expected all 3 pairs attempted"
        assert bar.updates == 3, f"PAIR_JOBS={pj}: bar must tick for every pair"


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_dispatcher_f_strings_interpolate_correctly(nb_path):
    """Regression guard against the double-brace escape bug that made the
    dispatcher print literal `{PAIR_JOBS}` / `{_e}` instead of values."""
    dispatcher_src = _dispatcher_block(_sweep_cell_source(nb_path))
    # Double-brace escapes would appear as literal `{{` in the cell source.
    # With proper single braces, these substrings must NOT appear.
    assert "{{PAIR_JOBS}}" not in dispatcher_src
    assert "{{_e}}" not in dispatcher_src
    assert "{{pair_idx+1}}" not in dispatcher_src
    assert "{{_pidx+1}}" not in dispatcher_src
