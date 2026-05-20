"""Paper fill 0.05$ worse than sim → residual sign + magnitude correct."""
from __future__ import annotations

from bowaka_v2_lab.reconcile.slippage_residuals import compute_slippage_residuals


def test_residual_sign_and_magnitude() -> None:
    paper = [{"parent_order_id": "po1", "symbol": "AAA", "avg_fill_price": 100.20}]
    sim = [{"parent_order_id": "po1", "symbol": "AAA", "avg_fill_price": 100.15}]
    df = compute_slippage_residuals(paper, sim)
    assert len(df) == 1
    assert abs(df["residual"].iloc[0] - 0.05) < 1e-9


def test_no_match_when_keys_diverge() -> None:
    paper = [{"parent_order_id": "po1", "symbol": "AAA", "avg_fill_price": 100.20}]
    sim = [{"parent_order_id": "po2", "symbol": "BBB", "avg_fill_price": 100.15}]
    df = compute_slippage_residuals(paper, sim)
    assert len(df) == 0
