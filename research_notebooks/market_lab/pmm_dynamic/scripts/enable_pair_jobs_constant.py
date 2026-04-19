"""Add PAIR_JOBS=1 constant to each direction-custom notebook's config cell.

PAIR_JOBS=1 preserves the current serial behavior bit-identically; setting
to 4 (after wiring the pair-loop into `sweep_pairs`) activates outer thread
parallelism. See pmm_lab/sweep/pair_worker.py for the primitive.

Re-runnable: inserts the constant only if not already present.
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
    cell["source"] = new_src.splitlines(keepends=True)


def _patch_config_cell(cell_src: str) -> tuple[str, bool]:
    if "PAIR_JOBS" in cell_src:
        return cell_src, False
    marker = "USE_NUMBA_KERNEL = True"
    idx = cell_src.find(marker)
    if idx == -1:
        marker = "OBJECTIVE_VERSION = "
        idx = cell_src.find(marker)
    if idx == -1:
        # Append at end
        return cell_src.rstrip() + "\n\n# Pair-level parallelism (opt-in; set to 4 after wiring sweep_pairs)\nPAIR_JOBS = 1\n", True
    end = cell_src.find("\n", idx)
    if end == -1:
        end = len(cell_src)
    insertion = (
        "\n\n"
        "# Pair-level parallelism: run N pairs concurrently via a ThreadPoolExecutor.\n"
        "# 1 = serial (current behavior). Set to 4 on a 32-CPU host (with N_JOBS=8)\n"
        "# to saturate CPUs — see pmm_lab/sweep/pair_worker.py for the primitive.\n"
        "# The outer pool MUST be threads, not processes (nested ProcessPoolExecutor\n"
        "# raises 'daemonic processes are not allowed to have children').\n"
        "PAIR_JOBS = 1"
    )
    return cell_src[: end] + insertion + cell_src[end:], True


def _find_config_cell(nb: dict) -> int | None:
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        if "OBJECTIVE_VERSION = " in _cell_source(cell):
            return i
    return None


def patch_notebook(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        nb = json.load(f)
    idx = _find_config_cell(nb)
    if idx is None:
        return {"path": path.name, "error": "no config cell found"}
    src = _cell_source(nb["cells"][idx])
    new_src, changed = _patch_config_cell(src)
    if changed:
        _set_cell_source(nb["cells"][idx], new_src)
        nb["cells"][idx]["outputs"] = []
        nb["cells"][idx]["execution_count"] = None
        with open(path, "w", encoding="utf-8") as f:
            json.dump(nb, f, indent=1)
    return {"path": path.name, "config_cell_idx": idx, "constant_added": changed}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for name in NOTEBOOKS:
        info = patch_notebook(NB_DIR / name)
        print(info)


if __name__ == "__main__":
    main()
