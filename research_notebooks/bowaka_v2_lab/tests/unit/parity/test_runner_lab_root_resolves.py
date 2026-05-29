"""Regression: ``_LAB_ROOT`` in ``parity.runner`` must point at the lab root.

Pre-hotfix, ``Path(__file__).resolve().parents[2]`` was one level too shallow
because the file lives at ``<lab_root>/src/bowaka_v2_lab/parity/runner.py``
(4 parents deep), not ``<lab_root>/bowaka_v2_lab/parity/runner.py`` (3 deep).
``parents[2]`` resolved to ``<lab_root>/src/`` and the default
``prod_script`` path became ``<lab_root>/src/reference/source_strategy/...``,
which doesn't exist:

    FileNotFoundError: ... can't open file '.../src/reference/source_strategy/scripts/bowaka_v2_backtest.py'

The right number is ``parents[3]`` — confirmed by the fact that the lab
root holds ``reference/source_strategy/scripts/bowaka_v2_backtest.py`` (the
mirror) and a sibling ``src/bowaka_v2_lab/`` directory.
"""
from __future__ import annotations

from pathlib import Path

from bowaka_v2_lab.parity import runner as _runner_mod


def test_lab_root_points_at_lab_tree_not_src() -> None:
    lab_root = _runner_mod._LAB_ROOT
    # The lab root's name is "bowaka_v2_lab" and its src/ sibling holds this
    # very module.
    assert lab_root.is_dir()
    assert lab_root.name == "bowaka_v2_lab"
    src_dir = lab_root / "src" / "bowaka_v2_lab"
    assert src_dir.is_dir(), (
        f"_LAB_ROOT is wrong: expected lab root with src/bowaka_v2_lab/, "
        f"but {src_dir} doesn't exist. _LAB_ROOT = {lab_root}"
    )
    # And it must hold the mirror.
    mirror_script = lab_root / "reference" / "source_strategy" / "scripts" / "bowaka_v2_backtest.py"
    assert mirror_script.is_file(), (
        f"_LAB_ROOT is wrong: expected mirror at {mirror_script}, missing. "
        f"_LAB_ROOT = {lab_root}"
    )


def test_lab_root_is_not_src() -> None:
    # Explicit guard against the off-by-one: _LAB_ROOT must not END at /src/.
    assert _runner_mod._LAB_ROOT.name != "src"


def test_runner_module_lives_under_lab_root_src() -> None:
    runner_file = Path(_runner_mod.__file__).resolve()
    assert runner_file.is_relative_to(_runner_mod._LAB_ROOT / "src" / "bowaka_v2_lab")
