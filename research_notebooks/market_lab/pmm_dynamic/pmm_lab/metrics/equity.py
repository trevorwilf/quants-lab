"""
Equity curve analysis: drawdown computation.
"""

import numpy as np


def compute_max_drawdown(equity_curve: np.ndarray) -> float:
    """Compute maximum peak-to-trough drawdown as a percentage.

    Parameters
    ----------
    equity_curve : np.ndarray
        float64 array of equity values over time.

    Returns
    -------
    float
        Max drawdown as a percentage (e.g., 15.3 means 15.3% drawdown).
        Returns 0.0 if equity_curve is empty or all equal.
    """
    if len(equity_curve) == 0:
        return 0.0

    running_max = np.maximum.accumulate(equity_curve)
    # Guard against division by zero
    safe_max = np.where(running_max == 0, 1.0, running_max)
    drawdowns = (running_max - equity_curve) / safe_max * 100.0
    return float(np.max(drawdowns))


def compute_drawdown_series(equity_curve: np.ndarray) -> np.ndarray:
    """Compute the drawdown at each bar as a percentage from the running peak.

    Returns an array of the same length as equity_curve.
    """
    if len(equity_curve) == 0:
        return np.array([], dtype="float64")

    running_max = np.maximum.accumulate(equity_curve)
    safe_max = np.where(running_max == 0, 1.0, running_max)
    return (running_max - equity_curve) / safe_max * 100.0
