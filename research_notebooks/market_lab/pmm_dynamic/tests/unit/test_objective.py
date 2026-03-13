"""Tests for pmm_lab.objective.objective — objective function."""

import pytest
from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import (
    objective_v1, ObjectiveWeights, ObjectiveDecomposition, REJECT_SCORE,
)


def _make_metrics(**overrides) -> Metrics:
    """Create a Metrics instance with sensible defaults, overridable by kwargs."""
    defaults = dict(
        pnl_pct=5.0,
        net_pnl_quote=5.0,
        max_drawdown_pct=10.0,
        sharpe=1.5,
        trade_count=20,
        fill_count=40,
        n_winning=12,
        n_losing=8,
        gross_win_quote=30.0,
        gross_loss_quote=15.0,
        profit_factor=2.0,
        total_fees_quote=1.0,
        maker_fees_quote=0.5,
        taker_fees_quote=0.5,
        fee_drag_pct=1.0,
        inventory_exposure_mean=0.05,
        inventory_exposure_max=0.1,
        expected_shortfall_5pct=0.0,
        volume_zero_bar_count=0,
        volume_zero_bar_fraction=0.0,
    )
    defaults.update(overrides)
    return Metrics(**defaults)


class TestObjectiveV1:
    def test_good_strategy_positive_score(self):
        """Metrics with pnl_pct=5, sharpe=1.5, max_dd=10, fee_drag=1, 20 trades → score > 0."""
        m = _make_metrics()
        result = objective_v1(m)
        assert not result.is_rejected
        assert result.raw_score > 0

    def test_bad_strategy_negative_score(self):
        """Metrics with pnl_pct=-10, sharpe=-1.0, max_dd=30, fee_drag=3, 15 trades → score < 0."""
        m = _make_metrics(
            pnl_pct=-10.0, sharpe=-1.0, max_drawdown_pct=30.0,
            fee_drag_pct=3.0, trade_count=15, n_winning=3, n_losing=12,
        )
        result = objective_v1(m)
        assert result.raw_score < 0

    def test_no_trades_hard_reject(self):
        """Metrics with trade_count=0 → is_rejected=True and raw_score=REJECT_SCORE."""
        m = _make_metrics(trade_count=0, n_winning=0, n_losing=0, fill_count=0)
        result = objective_v1(m)
        assert result.is_rejected
        assert result.raw_score == REJECT_SCORE

    def test_few_trades_soft_penalty(self):
        """trade_count=4 → score lower than trade_count=20, but NOT rejected."""
        m_few = _make_metrics(trade_count=4)
        m_many = _make_metrics(trade_count=20)
        r_few = objective_v1(m_few)
        r_many = objective_v1(m_many)
        assert not r_few.is_rejected
        assert r_few.raw_score < r_many.raw_score

    def test_decomposition_sums_correctly(self):
        """raw_score = pnl + sharpe - dd - fee - inv - tc_penalty - es."""
        m = _make_metrics()
        r = objective_v1(m)
        expected = (
            r.pnl_component + r.sharpe_component
            - r.drawdown_component - r.fee_drag_component
            - r.inventory_component - r.trade_count_penalty
            - r.es_component
        )
        assert abs(r.raw_score - expected) < 1e-9

    def test_sharpe_clipping(self):
        """Metrics with sharpe=10 → sharpe_component uses clipped value (5.0)."""
        m = _make_metrics(sharpe=10.0)
        w = ObjectiveWeights()
        r = objective_v1(m, w)
        expected_sharpe_comp = w.w_sharpe * w.sharpe_clip_max
        assert abs(r.sharpe_component - expected_sharpe_comp) < 1e-9

    def test_custom_weights(self):
        """Custom ObjectiveWeights with w_pnl=2.0 → pnl_component is doubled."""
        m = _make_metrics()
        w_default = ObjectiveWeights()
        w_custom = ObjectiveWeights(w_pnl=2.0)
        r_default = objective_v1(m, w_default)
        r_custom = objective_v1(m, w_custom)
        assert abs(r_custom.pnl_component - 2.0 * r_default.pnl_component) < 1e-9
