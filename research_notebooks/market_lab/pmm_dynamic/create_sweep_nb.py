"""Copy the authoritative sweep notebook to a new location.

The notebook at notebooks/pmm_dynamic_multi_pair_sweep.ipynb is the single
source of truth. This script copies it (optionally with a new name) for
deployment or experimentation. It does NOT generate notebook content.
"""

import shutil
import sys
from pathlib import Path

NOTEBOOK_DIR = Path(__file__).parent / "notebooks"
SOURCE = NOTEBOOK_DIR / "pmm_dynamic_multi_pair_sweep.ipynb"


def copy_notebook(dest: str | None = None) -> Path:
    """Copy the authoritative notebook to dest.

    If dest is None, copies to notebooks/pmm_dynamic_multi_pair_sweep_copy.ipynb.
    """
    if not SOURCE.exists():
        raise FileNotFoundError(f"Source notebook not found: {SOURCE}")

    if dest is None:
        dest_path = NOTEBOOK_DIR / "pmm_dynamic_multi_pair_sweep_copy.ipynb"
    else:
        dest_path = Path(dest)

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE, dest_path)
    print(f"Copied: {SOURCE} -> {dest_path}")
    return dest_path


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else None
    copy_notebook(dest)
