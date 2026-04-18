"""Cell-10 compact results table tests (Section 6)."""

import json
from pathlib import Path

import pytest

NB_DIR = Path(__file__).resolve().parents[2] / "notebooks" / "direction-custom"

NOTEBOOKS = [
    "mean_reversion_bb_rsi_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "mean_reversion_bb_rsi_retest_sweep.ipynb",
    "ema_regime_hold_multi_exchange_sweep_mexc_nonkyc.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
]


def _cell10_source(nb_name: str) -> str:
    with open(NB_DIR / nb_name, encoding="utf-8") as f:
        nb = json.load(f)
    src = nb["cells"][10]["source"]
    if isinstance(src, list):
        src = "".join(src)
    return src


@pytest.mark.parametrize("nb_name", NOTEBOOKS)
def test_cell10_has_compact_results_table(nb_name):
    src = _cell10_source(nb_name)
    assert "COMPACT RESULTS TABLE" in src
    # Required columns (Time renamed to DataDays per P1.5 / ML-DIR-003 cleanup)
    for col in ["Rank", "Connector", "Pair", "Robust", "Holdout", "Recent28d", "Gates", "DataDays", "YAML"]:
        assert col in src, f"{nb_name}: missing column {col!r} in cell 10"


@pytest.mark.parametrize("nb_name", NOTEBOOKS)
def test_cell10_sorts_by_robust_score(nb_name):
    src = _cell10_source(nb_name)
    assert 'key=lambda r: r.get("robust_score"' in src, (
        f"{nb_name}: cell 10 must sort by robust_score"
    )
    assert "reverse=True" in src, f"{nb_name}: cell 10 must sort descending"


@pytest.mark.parametrize("nb_name", [
    "mean_reversion_bb_rsi_retest_sweep.ipynb",
    "ema_regime_hold_retest_sweep.ipynb",
])
def test_retest_notebook_still_has_cross_pair_ranking(nb_name):
    """Retest notebooks must KEEP their existing cross-pair ranking cell (cell 13/14)."""
    with open(NB_DIR / nb_name, encoding="utf-8") as f:
        nb = json.load(f)
    # Retest layout: 16 cells, heading "Cross-Pair Ranking" is at cell 13
    c13_src = nb["cells"][13]["source"]
    if isinstance(c13_src, list):
        c13_src = "".join(c13_src)
    assert "Cross-Pair Ranking" in c13_src, (
        f"{nb_name}: retest notebook lost its ## 6 Cross-Pair Ranking heading"
    )
