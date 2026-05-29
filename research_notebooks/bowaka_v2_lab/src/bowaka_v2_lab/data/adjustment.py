"""Daily-bar adjustment resolution (audit 2026-05-29 §5.3 / §13.1).

The shared market-data lake stores ``raw`` and ``split_adjusted`` daily
partitions in separate directories. ``MarketDataStore.daily_bars`` and
``available_symbols`` default ``adjustment="raw"`` — so any caller that
does not pass an explicit ``adjustment`` reads raw bars even when the
strategy contract requires adjusted/split-adjusted data. This helper is
the SINGLE source of truth that maps a resolved lab config to the
correct ``adjustment`` string; every daily-bar reader in the lab must
call it instead of relying on the store default.
"""
from __future__ import annotations
from typing import Any, Mapping


def daily_adjustment_for_config(cfg: Mapping[str, Any]) -> str:
    """Return the adjustment string daily-bar readers must pass to the lake.

    Resolution order:
    1. ``market_data.require_split_adjustment: true`` -> ``split_adjusted``
    2. ``market_data.require_adjusted_daily_bars: true`` -> ``split_adjusted``
    3. explicit ``market_data.daily_adjustment: <value>`` -> as written
    4. otherwise -> ``raw``
    """
    md = (cfg or {}).get("market_data") or {}
    if md.get("require_split_adjustment") or md.get("require_adjusted_daily_bars"):
        return "split_adjusted"
    return str(md.get("daily_adjustment", "raw"))


__all__ = ["daily_adjustment_for_config"]
