"""Enable USE_NUMBA_KERNEL=True in the 4 direction-custom notebooks.

This patcher:
1. Finds the cell that defines `OBJECTIVE_VERSION` (the config cell — typically
   cell 3) and inserts `USE_NUMBA_KERNEL = True` as a new config line.
2. Finds cell 8 (the sweep loop) and threads `use_numba_kernel=USE_NUMBA_KERNEL`
   into every directional `_replace(strategy_config, controller_compat=...)` call.

Re-runnable: checks for existing occurrences before inserting.

Use once after updating `_legacy/_build_cell8.py`:
    python scripts/enable_numba_in_notebooks.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

NB_DIR = Path(__file__).resolve().parent.parent / "notebooks" / "direction-custom"

NOTEBOOKS = [
    "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "mean_reversion_bb_rsi_retest_sweep.ipynb",
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
]


def _cell_source(cell: dict) -> str:
    src = cell.get("source", "")
    if isinstance(src, list):
        return "".join(src)
    return src or ""


def _set_cell_source(cell: dict, new_src: str) -> None:
    """Write source as a list of lines (nbformat convention)."""
    cell["source"] = new_src.splitlines(keepends=True)


def _patch_config_cell(cell_src: str) -> tuple[str, bool]:
    """Add USE_NUMBA_KERNEL = True if not already present.

    Inserted near OBJECTIVE_VERSION for visual grouping.
    """
    if "USE_NUMBA_KERNEL" in cell_src:
        return cell_src, False
    marker = "OBJECTIVE_VERSION = "
    idx = cell_src.find(marker)
    if idx == -1:
        # Append at end
        return cell_src.rstrip() + "\n\n# Stage 1 Numba kernel activation\nUSE_NUMBA_KERNEL = True\n", True
    # Find end of the OBJECTIVE_VERSION line
    end = cell_src.find("\n", idx)
    if end == -1:
        end = len(cell_src)
    insertion = (
        "\n"
        "# Enable the Numba-compiled controller-compat feature kernels.\n"
        "# Stage 1 benchmarks: ~247x MR, ~3549x EMA warm-call speedup.\n"
        "# Set to False to use the pandas replay path (no numerical change).\n"
        "USE_NUMBA_KERNEL = True"
    )
    return cell_src[: end] + insertion + cell_src[end:], True


# ── cell-8 regex replacements — keep surgical ──────────────────────────────

_REPLACEMENTS = [
    # MR + EMA Phase-2 dedup: sc = _replace(bundle.strategy_config, controller_compat=PHASE2_CONTROLLER_COMPAT)
    (
        "sc = _replace(bundle.strategy_config, controller_compat=PHASE2_CONTROLLER_COMPAT)",
        "sc = _replace(bundle.strategy_config, controller_compat=PHASE2_CONTROLLER_COMPAT, use_numba_kernel=USE_NUMBA_KERNEL)",
    ),
    # MR validation: val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT)
    (
        "val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT)",
        "val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT, use_numba_kernel=USE_NUMBA_KERNEL)",
    ),
    # MR holdout extras: tc_cfg = _replace(tc_bundle.strategy_config, controller_compat=VALIDATION_CONTROLLER_COMPAT)
    (
        "tc_cfg = _replace(tc_bundle.strategy_config, controller_compat=VALIDATION_CONTROLLER_COMPAT)",
        "tc_cfg = _replace(tc_bundle.strategy_config, controller_compat=VALIDATION_CONTROLLER_COMPAT, use_numba_kernel=USE_NUMBA_KERNEL)",
    ),
    # EMA val_config (two-line form)
    (
        "val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT,\n                          _regime_candles=regime_candles)",
        "val_config = _replace(best_config, controller_compat=VALIDATION_CONTROLLER_COMPAT,\n                          _regime_candles=regime_candles, use_numba_kernel=USE_NUMBA_KERNEL)",
    ),
    # EMA holdout-extras (multi-line form) — add use_numba_kernel=USE_NUMBA_KERNEL as extra kwarg
    (
        "tc_cfg = _replace(\n                    tc_bundle.strategy_config,\n                    controller_compat=VALIDATION_CONTROLLER_COMPAT,\n                    _regime_candles=regime_candles,\n                )",
        "tc_cfg = _replace(\n                    tc_bundle.strategy_config,\n                    controller_compat=VALIDATION_CONTROLLER_COMPAT,\n                    _regime_candles=regime_candles,\n                    use_numba_kernel=USE_NUMBA_KERNEL,\n                )",
    ),
    # MR compute_sensitivity — add use_numba_kernel kwarg (final kwarg before `)`)
    (
        "            canonicalize_fn=_mr_canon_adapter,\n            perturb_params=MR_PERTURBABLE_PARAMS,\n        )",
        "            canonicalize_fn=_mr_canon_adapter,\n            perturb_params=MR_PERTURBABLE_PARAMS,\n            use_numba_kernel=USE_NUMBA_KERNEL,\n        )",
    ),
    # EMA compute_sensitivity — add use_numba_kernel kwarg
    (
        "            canonicalize_fn=_ema_canon_adapter,\n            regime_candles=regime_candles,\n            perturb_params=EMA_PERTURBABLE_PARAMS,\n        )",
        "            canonicalize_fn=_ema_canon_adapter,\n            regime_candles=regime_candles,\n            perturb_params=EMA_PERTURBABLE_PARAMS,\n            use_numba_kernel=USE_NUMBA_KERNEL,\n        )",
    ),
]


def _patch_cell8(cell_src: str) -> tuple[str, int]:
    """Thread use_numba_kernel=USE_NUMBA_KERNEL into every directional _replace call."""
    n_changes = 0
    for old, new in _REPLACEMENTS:
        if old in cell_src and "use_numba_kernel=USE_NUMBA_KERNEL" not in cell_src[cell_src.find(old): cell_src.find(old) + len(new)]:
            # Only rewrite if the flag isn't already threaded at this exact site
            updated = cell_src.replace(old, new)
            if updated != cell_src:
                # Count occurrences replaced
                n_changes += cell_src.count(old) - updated.count(old)
                cell_src = updated
    return cell_src, n_changes


def _find_cell_indices(nb: dict) -> tuple[int | None, int | None]:
    """Locate the config cell (contains OBJECTIVE_VERSION) and the sweep-loop
    cell (contains _replace(bundle.strategy_config, ...))."""
    config_idx = None
    cell8_idx = None
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = _cell_source(cell)
        if config_idx is None and "OBJECTIVE_VERSION = " in src:
            config_idx = i
        if cell8_idx is None and "_replace(bundle.strategy_config" in src:
            cell8_idx = i
    return config_idx, cell8_idx


def patch_notebook(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)

    config_idx, cell8_idx = _find_cell_indices(nb)
    if config_idx is None:
        return {"path": path.name, "error": "no OBJECTIVE_VERSION cell found"}
    if cell8_idx is None:
        return {"path": path.name, "error": "no _replace(bundle.strategy_config cell found"}

    cfg_src = _cell_source(nb["cells"][config_idx])
    new_cfg_src, added_const = _patch_config_cell(cfg_src)
    if added_const:
        _set_cell_source(nb["cells"][config_idx], new_cfg_src)

    cell8_src = _cell_source(nb["cells"][cell8_idx])
    new_cell8_src, n_replace_changes = _patch_cell8(cell8_src)
    if n_replace_changes:
        _set_cell_source(nb["cells"][cell8_idx], new_cell8_src)

    # Clear execution metadata for cells we changed
    if added_const:
        nb["cells"][config_idx]["outputs"] = []
        nb["cells"][config_idx]["execution_count"] = None
    if n_replace_changes:
        nb["cells"][cell8_idx]["outputs"] = []
        nb["cells"][cell8_idx]["execution_count"] = None

    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    return {
        "path": path.name,
        "config_cell_idx": config_idx,
        "cell8_idx": cell8_idx,
        "constant_added": added_const,
        "replace_sites_updated": n_replace_changes,
    }


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for name in NOTEBOOKS:
        path = NB_DIR / name
        info = patch_notebook(path)
        print(info)


if __name__ == "__main__":
    main()
