"""State-machine tests for directional validation statuses.

The validation layer must produce explicit statuses (`validated_pass`,
`validated_fail`, `validation_error`, `optimized_only`), must place YAML
artifacts under `rejected/` when mandatory gates fail, and must never label
a gate-failed candidate as `validated_pass` or `complete`.
"""
import json
from pathlib import Path

import pytest


MANDATORY_GATES = {
    "dataset_audit", "runtime_sanity", "objective_not_degenerate",
    "stress_not_collapsed", "yaml_validates",
    "walkforward_robust", "walkforward_positive_majority",
    "holdout_passed", "holdout_no_collapse",
    "sensitivity_stable", "recent_28d_passed", "top_k_clustered",
}


def _derive_status(gates_result, had_error):
    """Mirror the notebook's logic. This exact derivation must be present in
    `_build_cell8.py`'s MR and EMA validation blocks."""
    if had_error:
        return "validation_error"
    failed = [g for g, v in gates_result.items() if g in MANDATORY_GATES and v is False]
    if failed:
        return "validated_fail"
    return "validated_pass"


def test_all_mandatory_pass_is_validated_pass():
    gates = {g: True for g in MANDATORY_GATES}
    assert _derive_status(gates, had_error=False) == "validated_pass"


def test_any_mandatory_fail_is_validated_fail():
    for bad in MANDATORY_GATES:
        gates = {g: True for g in MANDATORY_GATES}
        gates[bad] = False
        assert _derive_status(gates, had_error=False) == "validated_fail", (
            f"gate {bad} failing must yield validated_fail"
        )


def test_exception_is_validation_error():
    gates = {g: True for g in MANDATORY_GATES}
    assert _derive_status(gates, had_error=True) == "validation_error"


def test_build_cell8_defines_mandatory_gates():
    """_build_cell8.py must contain the MANDATORY_GATES set definition with the
    full canonical gate list."""
    src = Path("notebooks/direction-custom/_build_cell8.py").read_text(encoding="utf-8")
    assert "MANDATORY_GATES = {" in src
    for g in ("dataset_audit", "walkforward_robust", "holdout_passed",
              "recent_28d_passed", "top_k_clustered", "sensitivity_stable"):
        assert g in src, f"_build_cell8.py MANDATORY_GATES must include {g!r}"


def test_build_cell8_emits_validation_status_in_result_entry():
    """The generator body must write validation_status (not just 'complete') on
    every result_entry after gates run."""
    src = Path("notebooks/direction-custom/_build_cell8.py").read_text(encoding="utf-8")
    assert '"validation_status"' in src, (
        "_build_cell8.py must emit 'validation_status' on result_entry"
    )
    assert '"validated_pass"' in src and '"validated_fail"' in src, (
        "_build_cell8.py must reference validated_pass and validated_fail strings"
    )


def test_build_cell8_yaml_goes_to_pending_first():
    """YAML must be written to .pending/ before gates decide final placement."""
    src = Path("notebooks/direction-custom/_build_cell8.py").read_text(encoding="utf-8")
    assert ".pending" in src, "YAML export must go through .pending/ first (fail-closed)"


def test_build_cell8_moves_to_rejected_on_failure():
    """On validated_fail, YAML must be moved to rejected/ with a REJECTED.json marker."""
    src = Path("notebooks/direction-custom/_build_cell8.py").read_text(encoding="utf-8")
    assert "/ \"rejected\"" in src or '"rejected"' in src, (
        "Fail branch must place YAML under rejected/ subdirectory"
    )
    assert "_REJECTED.json" in src, "Fail branch must write a REJECTED.json marker"


def test_yaml_placement_rejected_subdirectory_on_failure(tmp_path):
    """Simulate the notebook's placement policy — YAML to rejected/ with marker."""
    artifacts = tmp_path / "artifacts" / "direction-custom" / "mr_bb_rsi" / "testconn"
    (artifacts / "rejected").mkdir(parents=True)
    (artifacts / ".pending").mkdir(parents=True)

    pending = artifacts / ".pending" / "test.yml"
    pending.write_text("controller_name: mean_reversion_bb_rsi_v1\n")

    import shutil
    final = artifacts / "rejected" / "test.yml"
    shutil.move(str(pending), str(final))
    marker = artifacts / "rejected" / "test_REJECTED.json"
    marker.write_text(json.dumps({
        "validation_status": "validated_fail",
        "mandatory_gates_failed": ["walkforward_robust"],
    }))

    assert final.exists()
    assert marker.exists()
    info = json.loads(marker.read_text())
    assert info["validation_status"] == "validated_fail"
    assert "walkforward_robust" in info["mandatory_gates_failed"]
    assert not (artifacts / "test.yml").exists(), (
        "failed candidate YAML must NOT be placed at the deployable path"
    )


def test_optimized_only_is_a_recognized_status():
    src = Path("notebooks/direction-custom/_build_cell8.py").read_text(encoding="utf-8")
    assert '"optimized_only"' in src, (
        "_build_cell8.py must initialize validation_status to 'optimized_only'"
    )
