"""Plot builders for the weekly report.

Functions return ``Figure`` objects so the caller decides where to save them.
Static PNG output uses matplotlib; interactive HTML uses plotly.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover
    go = None  # type: ignore[assignment]


def equity_curve_png(daily: pd.DataFrame, output: Path) -> Path:
    fig, ax = plt.subplots(figsize=(8, 4))
    if daily.empty:
        ax.text(0.5, 0.5, "no equity data", ha="center", va="center")
    else:
        ax.plot(daily["trade_date"].astype(str), daily.get("equity", daily.get("cumulative_pnl", 0)), marker="o")
        ax.set_xlabel("trade_date")
        ax.set_ylabel("equity")
        ax.set_title("Equity curve")
        ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)
    return output


def equity_curve_html(daily: pd.DataFrame, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    if go is None:
        output.write_text("<html><body>plotly not available</body></html>")
        return output
    fig = go.Figure()
    if not daily.empty:
        fig.add_trace(go.Scatter(x=daily["trade_date"].astype(str), y=daily.get("equity", daily.get("cumulative_pnl", 0)), mode="lines+markers"))
    fig.update_layout(title="Equity curve", xaxis_title="trade_date", yaxis_title="equity")
    fig.write_html(output, include_plotlyjs="cdn")
    return output


def exit_reason_bar_png(counts: pd.DataFrame, output: Path) -> Path:
    fig, ax = plt.subplots(figsize=(6, 4))
    if counts.empty:
        ax.text(0.5, 0.5, "no exit data", ha="center", va="center")
    else:
        ax.bar(counts["exit_reason"], counts["count"])
        ax.set_title("Exit reasons")
        ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output)
    plt.close(fig)
    return output
