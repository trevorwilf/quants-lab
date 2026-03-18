"""Clustering must be a stop-ship gate."""
from pmm_lab.report.report_md import run_stop_ship_checks
from pmm_lab.optuna.clustering import ClusteringReport
from pmm_lab.metrics.metrics import Metrics
from pmm_lab.objective.objective import ObjectiveDecomposition


def _make_minimal_args(**overrides):
    """Build minimal kwargs for run_stop_ship_checks."""
    defaults = dict(
        best_metrics=Metrics(
            pnl_pct=1.0, net_pnl_quote=1.0, max_drawdown_pct=0.5, sharpe=1.0,
            trade_count=10, fill_count=20, n_winning=6, n_losing=4,
            gross_win_quote=1.0, gross_loss_quote=0.5, profit_factor=2.0,
            total_fees_quote=0.01, maker_fees_quote=0.005, taker_fees_quote=0.005,
            fee_drag_pct=0.1, inventory_exposure_mean=0.01,
            inventory_exposure_max=0.05,
            expected_shortfall_5pct=-0.001,
            volume_zero_bar_count=0, volume_zero_bar_fraction=0.0,
            median_trade_pnl_quote=0.01,
            inventory_exposure_p95=0.05,
            open_trade_count=0,
        ),
        best_objective=ObjectiveDecomposition(
            raw_score=1.0, pnl_component=1.0, sharpe_component=0.0,
            drawdown_component=0.0, fee_drag_component=0.0,
            inventory_component=0.0, trade_count_penalty=0.0,
            es_component=0.0, is_rejected=False,
        ),
    )
    defaults.update(overrides)
    return defaults


def test_clustered_passes_stop_ship():
    """Clustered top-k should pass the clustering gate."""
    cluster = ClusteringReport(
        k=5, param_cv={}, mean_cv=0.2, max_cv=0.3,
        clustered_params=["a", "b"], scattered_params=[],
        is_clustered=True, param_ranges={},
    )
    checks = run_stop_ship_checks(**_make_minimal_args(cluster_report=cluster))
    assert checks["top_k_clustered"] is True


def test_scattered_fails_stop_ship():
    """Scattered top-k should fail the clustering gate."""
    cluster = ClusteringReport(
        k=5, param_cv={}, mean_cv=0.8, max_cv=1.2,
        clustered_params=[], scattered_params=["a", "b"],
        is_clustered=False, param_ranges={},
    )
    checks = run_stop_ship_checks(**_make_minimal_args(cluster_report=cluster))
    assert checks["top_k_clustered"] is False


def test_no_cluster_report_fails():
    checks = run_stop_ship_checks(**_make_minimal_args(cluster_report=None))
    assert checks["top_k_clustered"] is False
