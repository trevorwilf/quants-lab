"""Production-vs-lab parity for the Bowaka v2 strategy.

With the Phase-0 fix landed, the production backtester
``reference/source_strategy/scripts/bowaka_v2_backtest.py`` reads the same
lake the lab does and runs the same scanner gates + cost model + exit logic.
This module measures empirical agreement between the production-side and
lab-side backtest outputs over a chosen window.

The metrics mirror the audit's Phase 6 paper-reconciliation thresholds
(§14.5) — same shape, same buckets, same thresholds — but the second side
is the production backtester, not paper logs. Sim-vs-sim parity is a
strictly stronger statement than paper-reconciliation parity because both
sides are deterministic, so any divergence is provably a code-level drift,
not a market-realism effect.
"""
from .metrics import DEFAULT_THRESHOLDS, compute_parity_metrics, evaluate_thresholds
from .normalizers import normalize_lab_output, normalize_production_output
from .report import render_markdown_report
from .runner import (
    ProductionRunResult,
    run_lab_backtester,
    run_parity,
    run_production_backtester,
)
from .schemas import NormalizedCandidate, NormalizedTrade, ParityReport

__all__ = (
    "NormalizedTrade",
    "NormalizedCandidate",
    "ParityReport",
    "normalize_production_output",
    "normalize_lab_output",
    "ProductionRunResult",
    "run_production_backtester",
    "run_lab_backtester",
    "run_parity",
    "compute_parity_metrics",
    "evaluate_thresholds",
    "DEFAULT_THRESHOLDS",
    "render_markdown_report",
)
