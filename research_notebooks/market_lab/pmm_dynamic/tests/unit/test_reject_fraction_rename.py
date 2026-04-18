"""MR cap-binding rename: total_reject_fraction (honest name) + deprecation alias."""
from pathlib import Path


def test_reject_fraction_is_emitted():
    """Verify the MR objective wrapper sets 'total_reject_fraction' on the trial."""
    src = Path("pmm_lab/optuna/objective_wrapper_mr_bb_rsi.py").read_text(encoding="utf-8")
    assert 'trial.set_user_attr("total_reject_fraction"' in src, (
        "MR objective wrapper must emit 'total_reject_fraction' user attr"
    )
    # Deprecation-window compatibility with the old key
    assert "max_trades_per_day_binding_fraction" in src, (
        "Old key must remain for one release so existing studies aren't broken"
    )


def test_result_entry_stores_reject_fraction():
    """_build_cell8.py MR block must populate total_reject_fraction in result_entry."""
    src = Path("notebooks/direction-custom/_legacy/_build_cell8.py").read_text(encoding="utf-8")
    assert '"total_reject_fraction"' in src, (
        "MR result_entry must include total_reject_fraction field"
    )
    # The rename is still readable from old user_attrs for back-compat
    assert "max_trades_per_day_binding_fraction" in src, (
        "Notebook must read old user_attrs as fallback"
    )
