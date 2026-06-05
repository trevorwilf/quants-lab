"""``_resolve_symbols`` must read daily bars at the config's daily adjustment.

The lab stores daily bars at ``split_adjusted`` (``require_split_adjustment``),
but ``available_symbols`` defaults to ``adjustment="raw"``. ``_resolve_symbols``
passed no adjustment, so under SIP / ``current_code_parity`` it returned an EMPTY
symbol list -> the per-fold preflight had nothing to probe -> every fold failed
``missing_minute_coverage`` ("no minute bars for any probed (symbol, scan_ts)")
even though the lake was fully populated. These pin that ``_resolve_symbols``
requests the daily adjustment the bars are actually stored under.
"""
from __future__ import annotations

import pandas as pd

from bowaka_common.marketdata import layout
from bowaka_v2_lab.optuna.walkforward_runner import _resolve_symbols


def _write_daily(lake, sym: str, adjustment: str) -> None:
    p = layout.daily_bars_path(lake, sym, feed="sip", adjustment=adjustment)
    p.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({
        "symbol": [sym], "timestamp": [pd.Timestamp("2025-08-01", tz="UTC")],
        "open": [10.0], "high": [10.5], "low": [9.5], "close": [10.0], "volume": [1_000_000],
    }).to_parquet(p, index=False)


def _cfg(lake):
    return {
        "market_data": {"feed": "sip", "minute_bar_source": "alpaca",
                        "shared_root": str(lake), "require_split_adjustment": True},
        "simulation": {"mode": "current_code_parity"},
    }


def test_resolve_symbols_reads_split_adjusted_daily(tmp_path):
    # daily bars live at split_adjusted (the require_split_adjustment default)
    _write_daily(tmp_path, "AAA", "split_adjusted")
    cfg = _cfg(tmp_path)
    syms = _resolve_symbols(cfg, cfg["market_data"], sim_mode="current_code_parity", plan=None)
    assert syms == ["AAA"]  # found via split_adjusted; was [] when it defaulted to raw


def test_resolve_symbols_respects_required_adjustment(tmp_path):
    # only raw daily present, but the config REQUIRES split_adjusted -> genuinely
    # missing the required daily, so the symbol set is empty (adjustment-sensitive).
    _write_daily(tmp_path, "AAA", "raw")
    cfg = _cfg(tmp_path)
    syms = _resolve_symbols(cfg, cfg["market_data"], sim_mode="current_code_parity", plan=None)
    assert syms == []
