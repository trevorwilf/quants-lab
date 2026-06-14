"""summary.json builder per [Report §18.3] + intermediate metrics for reports."""
from __future__ import annotations

import statistics
from typing import Any, Sequence


#: Per-pick profitability thresholds (decimal returns). The live strategy's
#: contract: each pick should make a MINIMUM of 0.5%, ideally above 4%. These
#: drive the per-pick quality metrics in :func:`build_summary` and the
#: ``pick_quality`` penalty in :mod:`bowaka_v2_lab.optuna.objective`.
PICK_QUALITY_MIN_PCT = 0.005    # 0.5% — minimum acceptable per-trade profit
PICK_QUALITY_STRETCH_PCT = 0.04  # 4%  — ideal per-trade profit


def _per_trade_returns(trades: list[dict]) -> list[float]:
    """Decimal return per closed trade = pnl / |qty * entry_price|.

    Trades with a non-positive entry notional (defensive) are skipped.
    """
    out: list[float] = []
    for t in trades:
        try:
            notional = abs(float(t.get("qty", 0)) * float(t.get("entry_price", 0.0)))
        except (TypeError, ValueError):
            continue
        if notional > 0:
            out.append(float(t.get("pnl", 0.0)) / notional)
    return out


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
        # Per-pick quality (operator goal: each pick >= 0.5%, ideally >= 4%).
        rets = _per_trade_returns(trades)
        if rets:
            frac_ge_min = sum(1 for r in rets if r >= PICK_QUALITY_MIN_PCT) / len(rets)
            frac_ge_stretch = sum(1 for r in rets if r >= PICK_QUALITY_STRETCH_PCT) / len(rets)
            avg_trade_return_pct = statistics.mean(rets)
            median_trade_return_pct = statistics.median(rets)
        else:
            # No usable per-trade notional — neutral (no quality penalty).
            frac_ge_min, frac_ge_stretch = 1.0, 0.0
            avg_trade_return_pct = median_trade_return_pct = 0.0
    else:
        win_rate = 0.0
        avg_win = avg_loss = total_pnl = 0.0
        max_drawdown = 0.0
        # Zero trades is handled by the low-trade-count penalty; keep the
        # per-pick quality neutral so a no-trade fold is not double-penalized.
        frac_ge_min, frac_ge_stretch = 1.0, 0.0
        avg_trade_return_pct = median_trade_return_pct = 0.0

    # §3.6 UNITS CONTRACT: ``net_return`` is a DECIMAL fraction (0.15 == +15%), NOT
    # a ×100 percentage — despite the ``net_return_pct`` key name below. The
    # objective's MetricUnits guard (optuna.objective) REQUIRES decimal returns and
    # rejects |v| > _RETURN_DECIMAL_MAX as percent, so a future "×100 fix" of this
    # field would either 100×-inflate every report/objective term or trip
    # MetricUnitsError downstream. Do NOT rescale; the "_pct" suffix is historical.
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
        "net_return_pct": net_return,  # §3.6: DECIMAL fraction, NOT ×100 (see units note above)
        "total_pnl": total_pnl,
        "max_drawdown_pct": max_drawdown,
        "n_trades": n_trades,
        "win_rate": win_rate,
        "avg_win": avg_win,
        "avg_loss": avg_loss,
        # Per-pick quality metrics (decimal returns). ``frac_trades_ge_min_profit``
        # drives the objective's ``pick_quality`` penalty; the others are for
        # report / finalist observability.
        "frac_trades_ge_min_profit": frac_ge_min,
        "frac_trades_ge_stretch_profit": frac_ge_stretch,
        "avg_trade_return_pct": avg_trade_return_pct,
        "median_trade_return_pct": median_trade_return_pct,
        "pick_quality_min_pct": PICK_QUALITY_MIN_PCT,
        "pick_quality_stretch_pct": PICK_QUALITY_STRETCH_PCT,
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
