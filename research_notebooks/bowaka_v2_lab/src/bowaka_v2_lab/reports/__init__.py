"""Reporting library — read run-dir artifacts and produce diagnostics."""
from .gate_funnel import gate_funnel_by_date_symbol, top_failure_reasons
from .trade_metrics import win_rate_summary, hold_duration_distribution, exit_mix
from .liquidity_execution import adv_bucket_distribution, spread_bucket_distribution, time_of_day_buckets
from .mfe_mae import mfe_mae_per_trade
from .cost_stress import cost_stress_compare
from .delay_sensitivity import delay_sensitivity_grid
from .data_quality_section import render_data_quality_section
from .render_run_report import render_run_report, SUITABILITY_TIERS

__all__ = [
    "gate_funnel_by_date_symbol", "top_failure_reasons",
    "win_rate_summary", "hold_duration_distribution", "exit_mix",
    "adv_bucket_distribution", "spread_bucket_distribution", "time_of_day_buckets",
    "mfe_mae_per_trade",
    "cost_stress_compare",
    "delay_sensitivity_grid",
    "render_data_quality_section",
    "render_run_report", "SUITABILITY_TIERS",
]
