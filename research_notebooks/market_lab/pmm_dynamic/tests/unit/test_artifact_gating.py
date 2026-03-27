"""Tests that artifact naming follows validation semantics."""
import json, pytest
from pathlib import Path

def test_no_ambiguous_best_yaml():
    nb_dir = Path(__file__).resolve().parents[2] / "notebooks" / "pmm_dynamic"
    for nb_path in nb_dir.glob("pmm_dynamic_*_sweep*.ipynb"):
        with open(nb_path, encoding="utf-8") as f:
            nb = json.load(f)
        src = "".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")
        bad_lines = [l.strip() for l in src.split("\n")
                     if "_best.yaml" in l and "screening_best" not in l and "validated_best" not in l
                     and not l.strip().startswith("#")]
        assert not bad_lines, f"{nb_path.name} has ambiguous '_best.yaml':\n" + "\n".join(bad_lines)
