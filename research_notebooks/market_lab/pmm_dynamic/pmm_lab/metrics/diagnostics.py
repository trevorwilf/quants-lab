"""
Metric sanity checks and diagnostic flags.
"""

from pmm_lab.metrics.metrics import Metrics
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class DiagnosticFlags:
    """Flags indicating potential issues with a backtest result."""
    no_trades: bool               # trade_count == 0
    very_few_trades: bool         # trade_count < 5
    extreme_drawdown: bool        # max_drawdown_pct > 50
    negative_sharpe: bool         # sharpe < 0
    high_fee_drag: bool           # fee_drag_pct > 5
    high_inventory_exposure: bool # inventory_exposure_max > 0.8
    all_winners: bool             # n_losing == 0 and trade_count > 0 (suspicious)
    all_losers: bool              # n_winning == 0 and trade_count > 0
    warnings: List[str]           # human-readable warning messages


def diagnose(metrics: Metrics) -> DiagnosticFlags:
    """Run diagnostic checks on computed metrics and return flags + warnings."""
    warnings = []

    no_trades = metrics.trade_count == 0
    very_few_trades = 0 < metrics.trade_count < 5
    extreme_drawdown = metrics.max_drawdown_pct > 50
    negative_sharpe = metrics.sharpe < 0
    high_fee_drag = metrics.fee_drag_pct > 5
    high_inventory_exposure = metrics.inventory_exposure_max > 0.8
    all_winners = metrics.n_losing == 0 and metrics.trade_count > 0
    all_losers = metrics.n_winning == 0 and metrics.trade_count > 0

    if no_trades:
        warnings.append("No trades executed — strategy may be too conservative or data too short")
    if very_few_trades:
        warnings.append(f"Only {metrics.trade_count} trades — results may not be statistically significant")
    if extreme_drawdown:
        warnings.append(f"Extreme drawdown of {metrics.max_drawdown_pct:.1f}% — risk of ruin")
    if negative_sharpe:
        warnings.append(f"Negative Sharpe ratio ({metrics.sharpe:.2f}) — strategy loses money on risk-adjusted basis")
    if high_fee_drag:
        warnings.append(f"High fee drag of {metrics.fee_drag_pct:.1f}% — consider reducing trade frequency")
    if high_inventory_exposure:
        warnings.append(f"High inventory exposure (max {metrics.inventory_exposure_max:.1%}) — unbalanced position risk")
    if all_winners:
        warnings.append("All trades are winners — suspiciously good, check for look-ahead bias")
    if all_losers:
        warnings.append("All trades are losers — strategy is consistently wrong")

    return DiagnosticFlags(
        no_trades=no_trades,
        very_few_trades=very_few_trades,
        extreme_drawdown=extreme_drawdown,
        negative_sharpe=negative_sharpe,
        high_fee_drag=high_fee_drag,
        high_inventory_exposure=high_inventory_exposure,
        all_winners=all_winners,
        all_losers=all_losers,
        warnings=warnings,
    )
