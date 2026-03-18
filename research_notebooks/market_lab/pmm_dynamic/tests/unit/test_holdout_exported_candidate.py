"""Holdout gating must be based on the exported candidate (rank 0),
not the best holdout candidate.

Validates Fix 3: HoldoutReport now has exported_holdout_* fields,
and stop-ship / PipelineResult use those instead of best-of-k.
"""
import numpy as np
import pytest
import inspect
from dataclasses import replace
from tests.conftest import _make_sample_candles_500
from pmm_lab.objective.holdout import evaluate_holdout, HoldoutReport
from pmm_lab.sim.executor_model import SimConfig
from pmm_lab.config.params import PairRules, FeeConfig

_RULES = PairRules(
    price_tick=0.01, amount_step=0.000001, min_notional_quote=5.0,
    fees=FeeConfig(0.001, 0.002),
)


def _make_config(**overrides):
    defaults = dict(
        buy_spreads=[1.0, 2.0], sell_spreads=[1.0, 2.0],
        buy_amounts_pct=[0.5, 0.5], sell_amounts_pct=[0.5, 0.5],
        total_amount_quote=100.0,
    )
    defaults.update(overrides)
    return SimConfig(**defaults)


class TestExportedCandidateFields:
    """HoldoutReport must expose exported-candidate gating fields."""

    def test_fields_exist(self):
        candles = _make_sample_candles_500()
        config = _make_config()
        report = evaluate_holdout(candles[-100:], [(config, 1.0)], _RULES, 300)
        assert hasattr(report, 'exported_holdout_passed')
        assert hasattr(report, 'exported_holdout_score')
        assert hasattr(report, 'exported_holdout_collapse')

    def test_single_candidate_exported_equals_best(self):
        """With one candidate, exported and best-of-k must agree."""
        candles = _make_sample_candles_500()
        config = _make_config()
        report = evaluate_holdout(candles[-100:], [(config, 1.0)], _RULES, 300)
        assert report.exported_holdout_passed == report.passed
        assert report.exported_holdout_score == report.best_holdout_score

    def test_exported_score_matches_candidate_zero(self):
        """exported_holdout_score must equal candidate 0's objective score."""
        candles = _make_sample_candles_500()
        config = _make_config()
        report = evaluate_holdout(candles[-100:], [(config, 1.0)], _RULES, 300)
        assert report.exported_holdout_score == report.candidates[0].objective.raw_score


class TestExportedCanFailWhileBestPasses:
    """Stop-ship must fail if candidate 0 fails, even if another candidate passes."""

    def test_two_candidates_exported_gating_independent(self):
        candles = _make_sample_candles_500()
        # Candidate 0: very tight stop loss likely causes bad performance
        bad_config = _make_config(stop_loss=0.001, take_profit=0.50)
        # Candidate 1: normal config
        ok_config = _make_config(stop_loss=0.03, take_profit=0.015)

        candidates = [
            (bad_config, 10.0),   # rank 0 = exported
            (ok_config, 8.0),     # rank 1 = diagnostic only
        ]
        report = evaluate_holdout(candles[-100:], candidates, _RULES, 300)

        exported_score = report.candidates[0].objective.raw_score
        if exported_score <= 0:
            assert not report.exported_holdout_passed, (
                "Exported candidate has non-positive score but was marked passed"
            )
            assert not report.passed


class TestStopShipUsesExportedFields:
    """run_stop_ship_checks must reference exported_holdout_* fields."""

    def test_stop_ship_source_uses_exported(self):
        from pmm_lab.report import report_md
        source = inspect.getsource(report_md.run_stop_ship_checks)
        assert "exported_holdout_passed" in source, \
            "stop_ship must use exported_holdout_passed, not holdout_report.passed"
        assert "exported_holdout_collapse" in source, \
            "stop_ship must use exported_holdout_collapse"


class TestPipelineResultUsesExportedFields:
    """PipelineResult must reference exported_holdout_* fields."""

    def test_runner_source_uses_exported_score(self):
        from pmm_lab.deploy import runner
        source = inspect.getsource(runner.run_full_pipeline)
        assert "exported_holdout_score" in source, \
            "PipelineResult must use exported_holdout_score"
        assert "exported_holdout_passed" in source, \
            "PipelineResult must use exported_holdout_passed"
