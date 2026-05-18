"""Phase weekly-report-plumbing: ReportInputs threads notebook 07/08/10 artifacts
into the right sections, and ``has_walk_forward`` is derived from ``optuna_best``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from bowaka_lab.reports.markdown import ReportInputs, build_markdown, research_status_flags
from bowaka_lab.reports.tables import (
    candidate_rank_distribution,
    optuna_top_trials,
    signal_fade_bucket_distribution,
)
from bowaka_lab.reports.weekly_report import generate_weekly_report


def _signal_fade_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trade_id": "t1", "symbol": "AAA", "trade_date": "2026-05-12",
             "eval_label": "rth", "score": 3, "bucket": "soft"},
            {"trade_id": "t1", "symbol": "AAA", "trade_date": "2026-05-12",
             "eval_label": "after_close", "score": 2, "bucket": "none"},
            {"trade_id": "t2", "symbol": "BBB", "trade_date": "2026-05-12",
             "eval_label": "rth", "score": 9, "bucket": "critical"},
        ]
    )


def _liquidity_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"bucket": "<$200k", "trades": 0, "win_rate": 0.0, "median_pnl_pct": None, "stop_gap_rate": 0.0},
            {"bucket": "$200k-$1M", "trades": 857, "win_rate": 0.34, "median_pnl_pct": -0.08, "stop_gap_rate": 0.3},
        ]
    )


def test_has_walk_forward_set_when_optuna_best_present():
    inp = ReportInputs(
        run_id="rid",
        config_hash="h",
        optuna_best={"study_name": "s", "n_trials": 100, "best_value": 0.12, "best_params": {}},
    )
    assert inp.has_walk_forward is True
    flags = research_status_flags(inp)
    assert "walk_forward_not_run" not in flags


def test_has_walk_forward_stays_false_when_optuna_best_empty():
    inp = ReportInputs(
        run_id="rid", config_hash="h",
        optuna_best={"study_name": "s", "n_trials": 0, "best_value": None, "best_params": {}},
    )
    assert inp.has_walk_forward is False


def test_explicit_has_walk_forward_overrides_optuna_inference():
    inp = ReportInputs(run_id="rid", config_hash="h", has_walk_forward=True, optuna_best=None)
    assert inp.has_walk_forward is True


def test_signal_fade_bucket_distribution_groups_by_bucket_and_eval_label():
    out = signal_fade_bucket_distribution(_signal_fade_fixture())
    assert {"bucket", "eval_label", "trades", "mean_score"}.issubset(out.columns)
    # Three buckets present: soft, none, critical -> 3 rows (1 eval each)
    assert len(out) == 3


def test_section_12_uses_signal_fade_artifact_when_provided(tmp_path):
    inp = ReportInputs(
        run_id="rid", config_hash="h",
        signal_fade=_signal_fade_fixture(),
    )
    md = build_markdown(inp)
    # Bucket labels from the dedicated artifact must appear in the rendered
    # section -- this is what the variant-derived fallback would never show.
    assert "critical" in md
    assert "soft" in md


def test_section_13_uses_liquidity_artifact_when_provided(tmp_path):
    inp = ReportInputs(
        run_id="rid", config_hash="h",
        liquidity=_liquidity_fixture(),
    )
    md = build_markdown(inp)
    assert "$200k-$1M" in md
    # Old derived view would show "1k-5k" etc. from trades.notional -- ensure
    # we are reading from the dedicated artifact, not the fallback.
    assert "stop_gap_rate" in md


def test_section_13_falls_back_to_derived_view_when_liquidity_missing():
    inp = ReportInputs(
        run_id="rid", config_hash="h",
        trades=pd.DataFrame(
            [{"symbol": "AAA", "pnl_pct": 0.1, "pnl": 100.0, "notional": 2500.0}]
        ),
    )
    md = build_markdown(inp)
    assert "1k-5k" in md


def test_candidate_rank_distribution_buckets_and_trims_empty():
    df = pd.DataFrame(
        {
            "rank": [5, 25, 45, 75, 150, 350, 700, 1500],
            "signal_strength": [20.0, 15.0, 12.0, 10.0, 8.0, 6.0, 4.0, 3.0],
        }
    )
    out = candidate_rank_distribution(df)
    assert {"rank_bucket", "candidates", "median_signal_strength"}.issubset(out.columns)
    # All non-empty buckets should appear; the >1000 bucket is present for rank=1500.
    assert "1000+" in out["rank_bucket"].tolist()
    assert int(out["candidates"].sum()) == 8


def test_candidate_rank_distribution_empty_input_returns_typed_empty_frame():
    out = candidate_rank_distribution(pd.DataFrame())
    assert out.empty
    assert "rank_bucket" in out.columns


def test_section_6_renders_when_candidate_rank_distribution_provided():
    df = pd.DataFrame({"rank": [10, 75, 200], "signal_strength": [12.0, 8.0, 5.0]})
    inp = ReportInputs(
        run_id="rid", config_hash="h",
        candidate_rank_distribution=candidate_rank_distribution(df),
    )
    md = build_markdown(inp)
    # Section 6 should now show a rank-bucket table, not the _not provided_ stub.
    assert "_not provided_" not in md.split("## 6.")[1].split("## 7.")[0]
    assert "rank_bucket" in md


def _optuna_best_fixture() -> dict:
    return {
        "study_name": "bowaka_prod_test_v1",
        "n_trials": 250,
        "best_value": 0.123456,
        "best_params": {"rvol_min": 1.4, "atr_pct_min": 0.05},
    }


def _optuna_trials_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"trial_number": 0, "objective_value": 0.05, "state": "COMPLETE",
             "param_rvol_min": 1.0, "param_atr_pct_min": 0.04},
            {"trial_number": 1, "objective_value": None, "state": "FAIL",
             "param_rvol_min": 1.5, "param_atr_pct_min": 0.05},
            {"trial_number": 2, "objective_value": 0.123, "state": "COMPLETE",
             "param_rvol_min": 1.4, "param_atr_pct_min": 0.05},
            {"trial_number": 3, "objective_value": 0.08, "state": "COMPLETE",
             "param_rvol_min": 1.2, "param_atr_pct_min": 0.06},
        ]
    )


def test_section_14_renders_optuna_best_when_provided():
    inp = ReportInputs(
        run_id="rid", config_hash="h",
        optuna_best=_optuna_best_fixture(),
    )
    md = build_markdown(inp)
    sec14 = md.split("## 14. Walk-forward optimization")[1].split("## 15.")[0]
    assert "bowaka_prod_test_v1" in sec14
    assert "250" in sec14
    assert "0.123456" in sec14
    assert "rvol_min" in sec14
    assert "1.4" in sec14


def test_section_14_renders_top_trials_when_optuna_trials_provided():
    inp = ReportInputs(
        run_id="rid", config_hash="h",
        optuna_best=_optuna_best_fixture(),
        optuna_trials=_optuna_trials_fixture(),
    )
    md = build_markdown(inp)
    sec14 = md.split("## 14. Walk-forward optimization")[1].split("## 15.")[0]
    assert "Top trials by objective value" in sec14
    assert "trial_number" in sec14
    assert "param_rvol_min" in sec14


def test_section_14_no_data_when_optuna_missing():
    md = build_markdown(ReportInputs(run_id="rid", config_hash="h"))
    sec14 = md.split("## 14. Walk-forward optimization")[1].split("## 15.")[0]
    assert "no walk-forward optimization run" in sec14


def test_optuna_top_trials_filters_to_completed_and_sorts_desc():
    out = optuna_top_trials(_optuna_trials_fixture(), n=5)
    # FAIL row dropped, completed rows sorted by objective_value desc.
    assert list(out["trial_number"]) == [2, 3, 0]
    # Param columns preserved.
    assert "param_rvol_min" in out.columns


def test_section_15_is_paper_reconciliation_after_walkforward_insert():
    """After renumbering, Section 15 is paper-vs-backtest reconciliation."""
    md = build_markdown(ReportInputs(run_id="rid", config_hash="h"))
    assert "## 15. Paper-vs-backtest reconciliation" in md
    assert "## 17. Stop-ship" in md
    assert "## 18. Exact next actions" in md


def test_generate_weekly_report_records_optuna_in_summary_when_present(tmp_path):
    res = generate_weekly_report(
        output_dir=tmp_path,
        inputs=ReportInputs(
            run_id="rid", config_hash="h",
            optuna_best={"study_name": "s", "n_trials": 100, "best_value": 0.12, "best_params": {"x": 1}},
        ),
    )
    md = res.markdown_path.read_text(encoding="utf-8")
    assert "walk_forward_not_run" not in md
