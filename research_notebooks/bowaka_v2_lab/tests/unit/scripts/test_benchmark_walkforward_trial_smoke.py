"""Smoke test for the per-trial benchmark harness (wf scan-matrix speedup P3).

The benchmark itself runs a real study (needs a built matrix + lake — an
operator step), so CI only asserts the module is import-clean and its CLI
parses, without executing a study.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "scripts" / "benchmark_walkforward_trial.py"
)


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "benchmark_walkforward_trial", _SCRIPT,
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_script_exists():
    assert _SCRIPT.is_file()


def test_import_clean():
    mod = _load_module()
    assert hasattr(mod, "main")
    assert callable(mod.main)
    # the heavy study import must be deferred (module import must not need the
    # lab runtime), so these helpers are present at import time.
    assert hasattr(mod, "_parse_args")
    assert mod.TARGET_SECONDS_PER_TRIAL == 180.0


def test_help_exits_zero():
    mod = _load_module()
    with pytest.raises(SystemExit) as exc:
        mod._parse_args(["--help"])
    assert exc.value.code == 0


def test_args_parse_defaults():
    mod = _load_module()
    args = mod._parse_args([])
    assert args.n_trials == 8
    assert args.legacy is False
    assert args.target_trials == 5000
    assert "matrix" in args.config
