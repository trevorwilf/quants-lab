"""Compare summary metrics across base/conservative/severe cost-stress levels."""
from __future__ import annotations

import pandas as pd

from ..sim.cost_model import COST_STRESS_LEVELS


def cost_stress_compare(summaries_by_level: dict[str, dict]) -> pd.DataFrame:
    rows = []
    for lvl in COST_STRESS_LEVELS:
        s = summaries_by_level.get(lvl)
        if s is None:
            continue
        rows.append({
            "cost_stress": lvl,
            "n_trades": s.get("n_trades"),
            "win_rate": s.get("win_rate"),
            "total_pnl": s.get("total_pnl"),
            "net_return_pct": s.get("net_return_pct"),
            "max_drawdown_pct": s.get("max_drawdown_pct"),
        })
    return pd.DataFrame(rows)
