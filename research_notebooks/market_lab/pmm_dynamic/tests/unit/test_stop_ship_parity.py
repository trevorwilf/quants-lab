"""Stop-ship checks must include parity gate."""
from pmm_lab.report.report_md import run_stop_ship_checks
from pmm_lab.parity.feature_parity import ParityResult
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


def test_parity_passed_shows_in_stop_ship():
    parity = ParityResult(passed=True, mode="frozen", mismatches=[], max_abs_diff=0.0, max_rel_diff=0.0)
    checks = run_stop_ship_checks(**_make_minimal_args(parity_result=parity))
    assert "frozen_parity" in checks
    assert checks["frozen_parity"] is True


def test_parity_failed_shows_in_stop_ship():
    parity = ParityResult(passed=False, mode="frozen",
                          mismatches=[{"bar": 60, "field": "ref_price", "expected": 1.0, "actual": 2.0, "diff": 1.0}],
                          max_abs_diff=1.0, max_rel_diff=1.0)
    checks = run_stop_ship_checks(**_make_minimal_args(parity_result=parity))
    assert "frozen_parity" in checks
    assert checks["frozen_parity"] is False


def test_no_parity_result_fails_stop_ship():
    checks = run_stop_ship_checks(**_make_minimal_args(parity_result=None))
    assert checks["frozen_parity"] is False


class TestLongParityInPipeline:
    """Pipeline must check both short and long parity fixtures."""

    def test_long_fixture_referenced(self):
        import inspect
        from pmm_lab.deploy import runner
        source = inspect.getsource(runner.run_full_pipeline)
        assert "long_500bar_compat" in source, \
            "Pipeline must check the long-history parity fixture"
