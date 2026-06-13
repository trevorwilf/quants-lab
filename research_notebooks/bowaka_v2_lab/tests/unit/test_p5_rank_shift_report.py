"""P5 — rank-shift report pure-core tests (legacy vs honest fill contract).

The heavy re-scoring is operator-run (needs the completed study + real tape); this
pins the deterministic diff/rank logic that turns two scored finalist sets into the
old-vs-new rank table — the headline P5 artifact.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from p5_rank_shift_report import (  # noqa: E402
    _coerce_finalists,
    compute_rank_shift,
    render_markdown,
)

_LEGACY = [
    {"trial": "3155", "score": 0.50, "metrics": {"pnl_pct": 16.0}},
    {"trial": "2001", "score": 0.40, "metrics": {"pnl_pct": 12.0}},
    {"trial": "0007", "score": 0.30, "metrics": {"pnl_pct": 9.0}},
]
_HONEST = [
    {"trial": "2001", "score": 0.20, "metrics": {"pnl_pct": 5.0}},    # now best
    {"trial": "3155", "score": -0.10, "metrics": {"pnl_pct": -2.0}},  # flipped + demoted
    # 0007 is absent under the honest contract (e.g. no honest fills).
]


def test_rank_shift_winner_changes_and_flips_detected() -> None:
    rep = compute_rank_shift(_LEGACY, _HONEST)
    s = rep["summary"]
    assert s["legacy_winner"] == "3155"
    assert s["honest_winner"] == "2001"
    assert s["winner_changed"] is True
    assert s["flipped_positive_to_nonpositive"] == ["3155"]
    assert s["dropped_under_honest"] == ["0007"]
    assert s["n_legacy"] == 3 and s["n_honest"] == 2


def test_rank_shift_rows_carry_rank_and_metric_deltas() -> None:
    rep = compute_rank_shift(_LEGACY, _HONEST)
    rows = {r["trial"]: r for r in rep["rows"]}
    # #3155 was rank 1 (legacy) -> rank 2 (honest): rank_delta = 1 - 2 = -1 (worse).
    assert rows["3155"]["legacy_rank"] == 1
    assert rows["3155"]["honest_rank"] == 2
    assert rows["3155"]["rank_delta"] == -1
    assert rows["3155"]["score_delta"] == pytest.approx(-0.6)
    assert rows["3155"]["metric_deltas"]["pnl_pct"] == pytest.approx(-18.0)
    # #2001 climbed from 2 to 1.
    assert rows["2001"]["rank_delta"] == 1
    # #0007 dropped under the honest contract.
    assert rows["0007"]["dropped_under_honest"] is True
    assert rows["0007"]["honest_rank"] is None
    assert rows["0007"]["score_delta"] is None


def test_render_markdown_has_table_and_winner_change() -> None:
    md = render_markdown(compute_rank_shift(_LEGACY, _HONEST))
    assert "CHANGED" in md
    assert "| trial |" in md
    assert "3155" in md and "2001" in md


def test_coerce_accepts_list_and_wrapper_and_validates() -> None:
    assert len(_coerce_finalists(_LEGACY)) == 3
    assert len(_coerce_finalists({"finalists": _LEGACY})) == 3
    with pytest.raises(ValueError):
        _coerce_finalists([{"trial": "x"}])  # missing score
    with pytest.raises(ValueError):
        _coerce_finalists("not a list")


def test_identical_inputs_yield_no_movement() -> None:
    rep = compute_rank_shift(_LEGACY, _LEGACY)
    assert rep["summary"]["winner_changed"] is False
    assert rep["summary"]["max_abs_rank_move"] == 0
    assert all(r["rank_delta"] == 0 for r in rep["rows"])
