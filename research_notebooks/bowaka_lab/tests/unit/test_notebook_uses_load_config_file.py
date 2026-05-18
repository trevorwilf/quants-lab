"""Phase fidelity-1: notebook builders must use ``load_config_file`` instead of
inline ``BowakaBacktestConfig.model_validate({...})`` literals.

This is an AST-grep style test that scans each builder's source and refuses
the build if the inline-config pattern reappears. Only an explicit
``_overrides_for_testing`` helper is allowed.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

NOTEBOOKS_DIR = Path(__file__).resolve().parents[2] / "notebooks"
BUILDERS = [
    "_build_03_prefilter_replay.py",
    "_build_04_single_config_backtest.py",
    "_build_05_entry_timing_counterfactuals.py",
    "_build_06_exit_surface_and_stop_manager.py",
    "_build_run_backtest_notebook.py",
]

_INLINE_PATTERN = re.compile(r"BowakaBacktestConfig\s*\.\s*model_validate\s*\(")
_LOADER_PATTERN = re.compile(r"load_config_file\s*\(")
_OVERRIDE_HELPER = re.compile(r"_overrides_for_testing")


@pytest.mark.parametrize("builder", BUILDERS)
def test_builder_uses_load_config_file(builder: str):
    path = NOTEBOOKS_DIR / builder
    assert path.exists(), f"builder missing: {path}"
    src = path.read_text(encoding="utf-8")
    assert _LOADER_PATTERN.search(src), (
        f"{builder} must call load_config_file(...) for the canonical config load"
    )


@pytest.mark.parametrize("builder", BUILDERS)
def test_builder_does_not_inline_model_validate(builder: str):
    path = NOTEBOOKS_DIR / builder
    src = path.read_text(encoding="utf-8")
    # Allow the pattern only inside _overrides_for_testing helpers.
    for match in _INLINE_PATTERN.finditer(src):
        prefix = src[: match.start()]
        if _OVERRIDE_HELPER.search(prefix.splitlines()[-50:].__str__()):
            continue
        # The match must not appear in real notebook code.
        pytest.fail(
            f"{builder} contains an inline BowakaBacktestConfig.model_validate(...) call "
            f"at character {match.start()}. Replace with load_config_file(CONFIG_PATH)."
        )


@pytest.mark.parametrize("builder", BUILDERS)
def test_builder_declares_config_path_parameter(builder: str):
    """``CONFIG_PATH = "configs/..."`` must appear in the PARAMETERS cell."""
    path = NOTEBOOKS_DIR / builder
    src = path.read_text(encoding="utf-8")
    assert re.search(r'CONFIG_PATH\s*=\s*[\'"][^\'"]+\.yml[\'"]', src), (
        f"{builder} must expose CONFIG_PATH as a parameter constant"
    )
