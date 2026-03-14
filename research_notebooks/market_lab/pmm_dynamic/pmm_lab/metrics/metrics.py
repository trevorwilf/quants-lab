"""
Compute performance metrics from a SimResult.
"""

import numpy as np
from dataclasses import dataclass
from typing import List
from pmm_lab.sim.executor_model import SimResult, Trade
from pmm_lab.metrics.equity import compute_max_drawdown


@dataclass(frozen=True)
class Metrics:
    """Complete performance metrics for one backtest run."""
    # PnL
    pnl_pct: float              # (final_equity - initial_equity) / initial_equity * 100
    net_pnl_quote: float        # final_equity - initial_equity in quote terms

    # Risk
    max_drawdown_pct: float     # maximum peak-to-trough drawdown as percentage
    sharpe: float               # annualized Sharpe ratio

    # Trade statistics
    trade_count: int            # number of completed round-trip trades
    fill_count: int             # total number of fills (entries + exits)
    n_winning: int
    n_losing: int
    gross_win_quote: float      # sum of positive trade PnLs
    gross_loss_quote: float     # sum of negative trade PnLs (as positive number)
    profit_factor: float        # gross_win / gross_loss (inf if no losses, 0 if no wins)

    # Fees
    total_fees_quote: float
    maker_fees_quote: float
    taker_fees_quote: float
    fee_drag_pct: float         # total_fees / initial_equity * 100

    # Inventory
    inventory_exposure_mean: float   # mean |base_balance * mid_price| / equity
    inventory_exposure_max: float    # max of the above

    # Tail risk
    expected_shortfall_5pct: float  # average of worst 5% of per-bar returns

    # Volume zero stats
    volume_zero_bar_count: int
    volume_zero_bar_fraction: float

    # Per-trade edge (v2)
    median_trade_pnl_quote: float = 0.0     # median PnL across all trades
    inventory_exposure_p95: float = 0.0      # 95th percentile inventory exposure


def compute_metrics(
    result: SimResult,
    initial_equity: float,
    candles: np.ndarray,
    bar_interval_seconds: int,
) -> Metrics:
    """Compute comprehensive metrics from a simulation result.

    Parameters
    ----------
    result : SimResult
        Output from CandleSimRunner.run().
    initial_equity : float
        Starting quote balance (equals total_amount_quote from SimConfig).
    candles : np.ndarray
        The canonical candle array used in the simulation.
    bar_interval_seconds : int
        Duration of one candle in seconds (e.g., 300 for 5m).

    Returns
    -------
    Metrics
    """
    eq = result.equity_curve
    n = len(eq)

    # PnL
    final_equity = eq[-1] if n > 0 else initial_equity
    net_pnl = final_equity - initial_equity
    pnl_pct = (net_pnl / initial_equity * 100.0) if initial_equity != 0 else 0.0

    # Drawdown
    max_dd = compute_max_drawdown(eq)

    # Sharpe ratio and returns
    sharpe = 0.0
    valid_returns = np.array([], dtype="float64")
    if n > 1:
        # Per-bar returns
        prev_eq = eq[:-1]
        curr_eq = eq[1:]
        valid = prev_eq != 0
        if np.any(valid):
            returns = np.where(valid, (curr_eq - prev_eq) / np.where(valid, prev_eq, 1.0), 0.0)
            valid_returns = returns[valid]
            if len(valid_returns) > 1:
                r_mean = np.mean(valid_returns)
                r_std = np.std(valid_returns, ddof=0)
                if r_std > 0:
                    bars_per_year = 365.25 * 24 * 3600 / bar_interval_seconds
                    sharpe = float(r_mean / r_std * np.sqrt(bars_per_year))

    # Expected Shortfall (CVaR) at 5%
    es_5 = 0.0
    if len(valid_returns) > 1:
        sorted_returns = np.sort(valid_returns)
        cutoff_idx = max(1, int(len(sorted_returns) * 0.05))
        es_5 = float(np.mean(sorted_returns[:cutoff_idx]))

    # Trade statistics
    trades = result.trades
    trade_count = len(trades)
    fill_count = trade_count * 2  # entry + exit per trade

    n_winning = 0
    n_losing = 0
    gross_win = 0.0
    gross_loss = 0.0
    total_fees = 0.0
    maker_fees = 0.0
    taker_fees = 0.0

    for t in trades:
        pnl = t.pnl_quote if t.pnl_quote is not None else 0.0
        if pnl > 0:
            n_winning += 1
            gross_win += pnl
        elif pnl < 0:
            n_losing += 1
            gross_loss += abs(pnl)

        total_fees += t.fee_quote

        # Exact maker/taker split
        maker_fees += t.entry_fee_quote  # entries are always maker
        # LIMIT take-profit exits are maker; all other exits are taker
        if t.exit_type == "take_profit":
            maker_fees += t.exit_fee_quote
        else:
            taker_fees += t.exit_fee_quote

    # Profit factor
    if gross_loss == 0 and gross_win > 0:
        profit_factor = float('inf')
    elif gross_win == 0:
        profit_factor = 0.0
    else:
        profit_factor = gross_win / gross_loss

    # Fee drag
    fee_drag_pct = (total_fees / initial_equity * 100.0) if initial_equity != 0 else 0.0

    # Inventory exposure
    close_prices = candles["close"].astype("float64")
    pos = result.position_history
    inv_exposure = np.zeros(n, dtype="float64")
    for i in range(n):
        if eq[i] != 0:
            inv_exposure[i] = abs(pos[i] * close_prices[i]) / abs(eq[i])

    inv_mean = float(np.mean(inv_exposure)) if n > 0 else 0.0
    inv_max = float(np.max(inv_exposure)) if n > 0 else 0.0

    # Inventory p95
    inv_p95 = float(np.percentile(inv_exposure, 95)) if n > 0 and np.any(inv_exposure > 0) else 0.0

    # Median trade PnL
    trade_pnls = [t.pnl_quote for t in trades if t.pnl_quote is not None]
    median_trade_pnl = float(np.median(trade_pnls)) if trade_pnls else 0.0

    # Volume zero stats
    volumes = candles["volume"].astype("float64")
    vol_zero_count = int(np.sum(volumes == 0))
    vol_zero_frac = vol_zero_count / len(volumes) if len(volumes) > 0 else 0.0

    return Metrics(
        pnl_pct=pnl_pct,
        net_pnl_quote=net_pnl,
        max_drawdown_pct=max_dd,
        sharpe=sharpe,
        trade_count=trade_count,
        fill_count=fill_count,
        n_winning=n_winning,
        n_losing=n_losing,
        gross_win_quote=gross_win,
        gross_loss_quote=gross_loss,
        profit_factor=profit_factor,
        total_fees_quote=total_fees,
        maker_fees_quote=maker_fees,
        taker_fees_quote=taker_fees,
        fee_drag_pct=fee_drag_pct,
        expected_shortfall_5pct=es_5,
        inventory_exposure_mean=inv_mean,
        inventory_exposure_max=inv_max,
        volume_zero_bar_count=vol_zero_count,
        volume_zero_bar_fraction=vol_zero_frac,
        median_trade_pnl_quote=median_trade_pnl,
        inventory_exposure_p95=inv_p95,
    )
