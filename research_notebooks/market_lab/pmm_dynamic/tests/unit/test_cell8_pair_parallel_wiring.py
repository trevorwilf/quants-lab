"""Structural test — cell 8 actually wires pair-level parallelism.

The previous prompt shipped the `pair_worker.py` primitive but left the
notebook's sweep loop untouched. This test proves cell 8 now contains:

  1. A `def _run_one_pair(pair_idx, pair_info):` definition (replacing the
     old top-level `for pair_idx, pair_info in enumerate(candidates):`).
  2. A `if PAIR_JOBS <= 1:` / `else:` dispatcher.
  3. A `ThreadPoolExecutor` import/use in the parallel branch.
  4. Trial-bar creation guarded by `if PAIR_JOBS > 1:`.
  5. No bare top-level `continue` statements inside the function body
     (would be a SyntaxError anyway — this is a belt-and-suspenders check).
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2]
_NOTEBOOKS = [
    _ROOT / "notebooks" / "direction-custom" / name
    for name in (
        "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "mean_reversion_bb_rsi_retest_sweep.ipynb",
        "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
        "ema_regime_hold_retest_sweep.ipynb",
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
    raise AssertionError(f"No sweep cell found in {nb_path.name}")


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_sweep_cell_defines_run_one_pair(nb_path):
    src = _sweep_cell_source(nb_path)
    assert "def _run_one_pair(pair_idx, pair_info):" in src, (
        f"{nb_path.name}: cell 8 must define _run_one_pair(pair_idx, pair_info)"
    )


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_sweep_cell_has_pair_jobs_dispatcher(nb_path):
    src = _sweep_cell_source(nb_path)
    assert "if PAIR_JOBS <= 1:" in src, (
        f"{nb_path.name}: cell 8 must guard serial path with 'if PAIR_JOBS <= 1:'"
    )
    assert "ThreadPoolExecutor" in src, (
        f"{nb_path.name}: parallel branch must use ThreadPoolExecutor"
    )
    # Parallel branch submits via pool.submit
    assert "_pool.submit(_run_one_pair" in src, (
        f"{nb_path.name}: parallel dispatcher must submit _run_one_pair"
    )


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_sweep_cell_trial_bar_guarded_by_pair_jobs(nb_path):
    src = _sweep_cell_source(nb_path)
    # Per-trial tqdm should be suppressed when running multiple pairs
    assert "if PAIR_JOBS > 1:" in src, (
        f"{nb_path.name}: cell 8 must guard _trial_bar creation with 'if PAIR_JOBS > 1:'"
    )


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_sweep_cell_has_no_bare_continue_in_run_one_pair(nb_path):
    """Inside _run_one_pair, all early-exit paths must use `return`, not
    `continue` (which would be a SyntaxError outside a loop). We verified
    Python AST parse already catches SyntaxErrors; this doubles as a
    regression guard on the wiring."""
    src = _sweep_cell_source(nb_path)
    # cell 8 must parse as Python
    ast.parse(src)

    # In the parsed tree, find the `_run_one_pair` function definition
    # and assert no `continue` inside (other than inside an inner loop).
    tree = ast.parse(src)
    # Collect module-level functions named _run_one_pair
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "_run_one_pair":
            found = True
            # Walk the body; any Continue must be inside a For/While.
            for sub in ast.walk(node):
                if isinstance(sub, ast.Continue):
                    # Walk parents via ast-no-parents: do a containment check.
                    # Since ast doesn't track parents, we recheck: the continue
                    # must be nested inside a For/While. Use a parent map.
                    pass
            # Build parent map for this function
            parents = {}
            for p in ast.walk(node):
                for child in ast.iter_child_nodes(p):
                    parents[child] = p
            for sub in ast.walk(node):
                if isinstance(sub, ast.Continue):
                    # Trace up until we see a For/While (inner loop - OK)
                    # or the function itself (bare continue - BAD).
                    p = parents.get(sub)
                    while p is not None:
                        if isinstance(p, (ast.For, ast.AsyncFor, ast.While)):
                            break
                        if isinstance(p, ast.FunctionDef):
                            assert False, (
                                f"{nb_path.name}: bare `continue` inside "
                                f"_run_one_pair (not in an inner loop) — "
                                f"would raise SyntaxError"
                            )
                        p = parents.get(p)
            break
    assert found, f"{nb_path.name}: could not locate _run_one_pair FunctionDef"


@pytest.mark.parametrize("nb_path", _NOTEBOOKS)
def test_sweep_cell_dispatcher_drives_pair_bar(nb_path):
    """`_pair_bar.update(1)` must happen in the dispatcher (once per pair),
    not inside the pair body."""
    src = _sweep_cell_source(nb_path)
    # The dispatcher's update sites: one in the serial branch's for loop,
    # one in the parallel branch's as_completed loop. At least 2 total.
    assert src.count("_pair_bar.update(1)") >= 2, (
        f"{nb_path.name}: dispatcher must update _pair_bar in both branches"
    )
    # And the final close
    assert "_pair_bar.close()" in src
