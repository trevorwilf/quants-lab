"""Tests for objective_v2 log-return formulation."""

import math
import pytest
from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import (
    objective_v1, ObjectiveWeights,
    objective_v2, ObjectiveWeightsV2,
    ObjectiveDecomposition, REJECT_SCORE,
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
        expected_shortfall_5pct=-0.001,
        volume_zero_bar_count=0,
        volume_zero_bar_fraction=0.0,
        median_trade_pnl_quote=0.5,
        inventory_exposure_p95=0.08,
    )
    defaults.update(overrides)
    return Metrics(**defaults)


# ── Core function tests ───────────────────────────────────────────


class TestV2GoodStrategyPositiveScore:
    def test_v2_good_strategy_positive_score(self):
        m = _make_metrics(pnl_pct=20.0, max_drawdown_pct=5.0, trade_count=60)
        r = objective_v2(m)
        assert not r.is_rejected
        assert r.raw_score > 0


class TestV2BadStrategyNegativeScore:
    def test_v2_bad_strategy_negative_score(self):
        m = _make_metrics(
            pnl_pct=-10.0, max_drawdown_pct=30.0, trade_count=15,
            n_winning=3, n_losing=12, median_trade_pnl_quote=-0.5,
        )
        r = objective_v2(m)
        assert r.raw_score < 0


class TestV2NoTradesRejected:
    def test_v2_no_trades_rejected(self):
        m = _make_metrics(trade_count=0, n_winning=0, n_losing=0, fill_count=0)
        r = objective_v2(m)
        assert r.is_rejected
        assert r.raw_score == REJECT_SCORE


class TestV2FewTradesPenalty:
    def test_v2_few_trades_penalty(self):
        m_few = _make_metrics(trade_count=4)
        m_many = _make_metrics(trade_count=20)
        r_few = objective_v2(m_few)
        r_many = objective_v2(m_many)
        assert not r_few.is_rejected
        assert r_few.raw_score < r_many.raw_score


class TestV2DecompositionConsistent:
    def test_v2_decomposition_consistent(self):
        m = _make_metrics()
        r = objective_v2(m)
        expected = (
            r.pnl_component
            - r.drawdown_component - r.es_component
            - r.fee_drag_component - r.inventory_component
            - r.trade_count_penalty
        )
        # Edge penalty is folded into raw_score but not exposed as a separate field
        # We can verify raw_score <= expected (since edge_comp >= 0)
        assert r.raw_score <= expected + 1e-9


# ── Log-return behavior ──────────────────────────────────────────


class TestV2LogReturnDampsLargePnl:
    def test_v2_log_return_damps_large_pnl(self):
        """pnl_pct=200% produces log(3) ~ 1.1, not 200. Compare v1 vs v2 ratios."""
        m_10 = _make_metrics(pnl_pct=10.0, trade_count=50)
        m_200 = _make_metrics(pnl_pct=200.0, trade_count=50)

        r_v1_10 = objective_v1(m_10)
        r_v1_200 = objective_v1(m_200)
        r_v2_10 = objective_v2(m_10)
        r_v2_200 = objective_v2(m_200)

        v1_ratio = r_v1_200.pnl_component / r_v1_10.pnl_component
        v2_ratio = r_v2_200.pnl_component / r_v2_10.pnl_component

        assert v1_ratio > 15  # linear: 200/10 = 20
        assert v2_ratio < 12  # log-damped


class TestV2LogReturnNegativeHandled:
    def test_v2_log_return_negative_handled(self):
        """pnl_pct=-50% produces log(0.5) ~ -0.69, no crash."""
        m = _make_metrics(pnl_pct=-50.0, trade_count=10, median_trade_pnl_quote=-1.0)
        r = objective_v2(m)
        assert not r.is_rejected
        assert r.pnl_component < 0  # log(0.5) is negative


class TestV2LogReturnTotalLossHandled:
    def test_v2_log_return_total_loss_handled(self):
        """pnl_pct=-100% → guarded, no math error."""
        m = _make_metrics(pnl_pct=-100.0, trade_count=10, median_trade_pnl_quote=-5.0)
        r = objective_v2(m)
        assert not r.is_rejected
        # Should use the -10.0 guard value
        assert r.pnl_component < -5.0


# ── Per-trade edge ────────────────────────────────────────────────


class TestV2NegativeEdgePenalty:
    def test_v2_negative_edge_penalty(self):
        """median_trade_pnl_quote < 0 → edge penalty applied, lower score."""
        m_positive = _make_metrics(median_trade_pnl_quote=0.5)
        m_negative = _make_metrics(median_trade_pnl_quote=-0.5)
        r_positive = objective_v2(m_positive)
        r_negative = objective_v2(m_negative)
        assert r_negative.raw_score < r_positive.raw_score


class TestV2PositiveEdgeNoPenalty:
    def test_v2_positive_edge_no_penalty(self):
        """median_trade_pnl_quote > 0 → no edge penalty."""
        m = _make_metrics(median_trade_pnl_quote=1.0)
        r = objective_v2(m)
        # Edge penalty is 0 when median is positive
        # Check by comparing with zero-edge case
        m_zero = _make_metrics(median_trade_pnl_quote=0.0)
        r_zero = objective_v2(m_zero)
        assert abs(r.raw_score - r_zero.raw_score) < 1e-9


class TestV2ZeroTradesNoEdgePenalty:
    def test_v2_zero_trades_no_edge_penalty(self):
        """trade_count=0 → rejected before edge check."""
        m = _make_metrics(trade_count=0, n_winning=0, n_losing=0, fill_count=0)
        r = objective_v2(m)
        assert r.is_rejected


# ── Sharpe removed ────────────────────────────────────────────────


class TestV2SharpeNotInScore:
    def test_v2_sharpe_not_in_score(self):
        """sharpe_component is always 0.0 in v2."""
        m = _make_metrics(sharpe=5.0)
        r = objective_v2(m)
        assert r.sharpe_component == 0.0


# ── v1 backward compatibility ────────────────────────────────────


class TestV1StillWorksUnchanged:
    def test_v1_still_works_unchanged(self):
        """objective_v1 produces same result as before (not affected by v2 addition)."""
        m = _make_metrics()
        r = objective_v1(m)
        assert not r.is_rejected
        assert r.raw_score > 0
        # Verify decomposition still works
        expected = (
            r.pnl_component + r.sharpe_component
            - r.drawdown_component - r.fee_drag_component
            - r.inventory_component - r.trade_count_penalty
            - r.es_component
        )
        assert abs(r.raw_score - expected) < 1e-9
