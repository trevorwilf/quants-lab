"""Regenerate cell 8 in the 4 direction-custom notebooks from _legacy/_build_cell8.py."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
BUILD = HERE / "notebooks" / "direction-custom" / "_legacy" / "_build_cell8.py"
NB_DIR = HERE / "notebooks" / "direction-custom"

NOTEBOOKS_MR = [
    "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "mean_reversion_bb_rsi_retest_sweep.ipynb",
]
NOTEBOOKS_EMA = [
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
]


def _import_build():
    spec = importlib.util.spec_from_file_location("_legacy_build_cell8", BUILD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_cell8(nb_path: Path, new_source: str) -> int:
    with open(nb_path, encoding="utf-8") as f:
        nb = json.load(f)
    # Locate cell 8 by content: the one containing "_pair_bar = tqdm"
    target = None
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = cell["source"]
        if isinstance(src, list):
            src = "".join(src)
        if "_pair_bar = tqdm" in src:
            target = i
            break
    if target is None:
        # Fallback to index 8 (the build script's assumption)
        target = 8
    nb["cells"][target]["source"] = new_source.splitlines(keepends=True)
    nb["cells"][target]["outputs"] = []
    nb["cells"][target]["execution_count"] = None
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    return len(new_source.splitlines())


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    mod = _import_build()
    mr_src = mod.build_mr_cell8()
    ema_src = mod.build_ema_cell8()

    for name in NOTEBOOKS_MR:
        lines = _write_cell8(NB_DIR / name, mr_src)
        print(f"{name}: cell 8 = {lines} lines")
    for name in NOTEBOOKS_EMA:
        lines = _write_cell8(NB_DIR / name, ema_src)
        print(f"{name}: cell 8 = {lines} lines")


if __name__ == "__main__":
    main()
