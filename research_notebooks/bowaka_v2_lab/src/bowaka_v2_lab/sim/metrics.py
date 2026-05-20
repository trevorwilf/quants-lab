"""summary.json builder per [Report §18.3] + intermediate metrics for reports."""
from __future__ import annotations

import statistics
from typing import Any, Sequence


def build_summary(
    *,
    trades: list[dict],
    candidate_events_count: int,
    entry_decisions_count: int,
    accepted_count: int,
    rejected_count: int,
    broker_reject_count: int,
    initial_bankroll: float,
    final_bankroll: float,
    ambiguous_bar_count: int,
    cost_stress: str,
    feed: str,
    run_id: str,
    strategy_version: str = "0.1.0",
) -> dict[str, Any]:
    n_trades = len(trades)
    if n_trades:
        wins = sum(1 for t in trades if t["pnl"] > 0)
        win_rate = wins / n_trades
        pnls = [t["pnl"] for t in trades]
        avg_win = statistics.mean([p for p in pnls if p > 0]) if any(p > 0 for p in pnls) else 0.0
        avg_loss = statistics.mean([p for p in pnls if p <= 0]) if any(p <= 0 for p in pnls) else 0.0
        total_pnl = sum(pnls)
        max_drawdown = _max_drawdown([initial_bankroll + sum(pnls[:i + 1]) for i in range(n_trades)], initial_bankroll)
    else:
        win_rate = 0.0
        avg_win = avg_loss = total_pnl = 0.0
        max_drawdown = 0.0

    net_return = (final_bankroll - initial_bankroll) / initial_bankroll if initial_bankroll > 0 else 0.0
    return {
        "schema_version": 1,
        "run_id": run_id,
        "strategy_id": "bowaka_v2",
        "strategy_version": strategy_version,
        "feed": feed,
        "cost_stress": cost_stress,
        "initial_bankroll": initial_bankroll,
        "final_bankroll": final_bankroll,
        "net_return_pct": net_return,
        "total_pnl": total_pnl,
        "max_drawdown_pct": max_drawdown,
        "n_trades": n_trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        "candidate_events_count": candidate_events_count,
        "entry_decisions_count": entry_decisions_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "broker_reject_count": broker_reject_count,
        "ambiguous_bar_count": ambiguous_bar_count,
    }


def _max_drawdown(equity_curve: Sequence[float], initial: float) -> float:
    if not equity_curve:
        return 0.0
    peak = initial
    max_dd = 0.0
    for v in equity_curve:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (peak - v) / peak
            max_dd = max(max_dd, dd)
    return max_dd
