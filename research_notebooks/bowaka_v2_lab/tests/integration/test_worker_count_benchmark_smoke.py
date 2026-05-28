"""Phase 2.5 §6.3 — smoke for the worker-count benchmark script.

Marked ``@pytest.mark.slow`` so ``make test-all`` skips it by default; the
operator runs it explicitly before the live benchmark to confirm the
script imports + the CLI surface accepts the expected flags.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


_BENCHMARK = (
    Path(__file__).resolve().parents[2]
    / "scripts" / "benchmark_worker_count_matrix.py"
)


def _load_benchmark():
    spec = importlib.util.spec_from_file_location(
        "benchmark_worker_count_matrix", _BENCHMARK,
    )
    assert spec and spec.loader, _BENCHMARK
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("benchmark_worker_count_matrix", mod)
    spec.loader.exec_module(mod)
    return mod


def test_benchmark_module_imports() -> None:
    """Sanity: the benchmark module imports without side effects."""
    mod = _load_benchmark()
    assert hasattr(mod, "main")
    assert hasattr(mod, "_run_one_worker_count")


@pytest.mark.slow
def test_benchmark_cli_help_runs() -> None:
    """The CLI surface accepts the expected flags."""
    mod = _load_benchmark()
    with pytest.raises(SystemExit) as ei:
        mod.main(["--help"])
    assert ei.value.code == 0
