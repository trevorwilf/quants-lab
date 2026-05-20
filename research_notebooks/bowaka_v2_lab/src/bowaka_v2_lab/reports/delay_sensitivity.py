"""Entry-delay sensitivity grid (1 / 5 / 15 / 30 minutes)."""
from __future__ import annotations

import pandas as pd


_DEFAULT_DELAYS = (1, 5, 15, 30)


def delay_sensitivity_grid(summaries_by_delay: dict[int, dict]) -> pd.DataFrame:
    """Tabulate summary metrics by entry-delay minutes."""
    rows = []
    for d in sorted(summaries_by_delay.keys()):
        s = summaries_by_delay[d]
        rows.append({
            "entry_delay_minutes": d,
            "n_trades": s.get("n_trades"),
            "win_rate": s.get("win_rate"),
            "total_pnl": s.get("total_pnl"),
            "net_return_pct": s.get("net_return_pct"),
        })
    return pd.DataFrame(rows)


def standard_delays() -> tuple[int, ...]:
    return _DEFAULT_DELAYS
