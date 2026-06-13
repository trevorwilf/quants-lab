"""Per-lot exit driver — Realism Phase 7 (audit P0-009, §11 Phase 7, Ticket 6).

The pre-Phase-7 backtester drove exits **per symbol** off the symbol's last
daily bar. This module drives them **per lot** through one of two paths:

* ``smoke_fixture`` mode → :func:`drive_session_exits_daily`. The legacy
  single-daily-bar evaluator keeps the smoke suite fast.
* ``current_code_parity`` / ``intended_realism`` modes →
  :func:`drive_session_exits_minute`. Each open lot is walked over the session's
  minute bars (Phase-4 intraday-window policy) and closed by ``position_id``.

A lot is evaluated at the end of *every* session from its entry session
onwards; :func:`sim.exits.walk_lot_exit` itself caps the walk at the max-hold
trading-day horizon, so a lot that survives session N is re-walked at session
N+1, and so on, until a bracket / time-stop / max-hold / signal-fade fires.
"""
from __future__ import annotations

import datetime as _dt
from typing import Any, Callable, Optional

import pandas as pd

from .exits import FadeTelemetry, evaluate_exits, walk_lot_exit
from .portfolio import Portfolio


def _session_minute_bars(
    symbol: str,
    session_date: _dt.date,
    *,
    session_minute_supplier: Optional[Callable[[str, _dt.date], Optional[pd.DataFrame]]],
    minute_bars_supplier: Optional[Callable[[str, Any], Optional[pd.DataFrame]]],
) -> Optional[pd.DataFrame]:
    """The regular-session minute bars for ``(symbol, session_date)``.

    Prefers an explicit ``session_minute_supplier``; otherwise falls back to the
    ordinary forming-session ``minute_bars_supplier`` queried at the 16:00 ET
    close (by the close its forming-session window covers the whole session).
    """
    if session_minute_supplier is not None:
        try:
            df = session_minute_supplier(symbol, session_date)
        except Exception:  # noqa: BLE001 - a missing session is non-fatal
            df = None
        if df is not None and len(df) > 0:
            return df
    if minute_bars_supplier is not None:
        close_ts = pd.Timestamp(
            _dt.datetime.combine(session_date, _dt.time(16, 0)),
            tz="America/New_York",
        ).tz_convert("UTC")
        try:
            df = minute_bars_supplier(symbol, close_ts)
        except Exception:  # noqa: BLE001
            df = None
        if df is not None and len(df) > 0:
            return df
    return None


def drive_session_exits_minute(
    portfolio: Portfolio,
    session_date: _dt.date,
    *,
    cfg: dict,
    session_minute_supplier: Optional[Callable[[str, _dt.date], Optional[pd.DataFrame]]] = None,
    minute_bars_supplier: Optional[Callable[[str, Any], Optional[pd.DataFrame]]] = None,
    quote_supplier: Optional[Callable[..., Optional[dict]]] = None,
    trades_supplier: Optional[Callable[..., Any]] = None,
    signal_score_fn: Optional[Callable[[Any, pd.Timestamp], Optional[float]]] = None,
    cost_stress: str = "base",
    seed: int = 0,
) -> dict[str, Any]:
    """Walk every open lot over ``session_date``'s minute bars; close by id.

    Returns ``{"trades": [...], "ambiguous": n, "fade_telemetry": [...]}``.
    Only lots whose ``session_date`` is on/after their entry session are
    evaluated (a lot cannot exit before it filled).
    """
    exits_cfg = cfg.get("exits") or {}
    same_minute = (
        ((cfg.get("simulation") or {}).get("same_minute_resolution"))
        or "conservative"
    )
    trades: list[dict] = []
    ambiguous = 0
    fade_telemetry: list[FadeTelemetry] = []

    # Fetch the session's minute bars once per distinct symbol.
    symbols = sorted({p.symbol for p in portfolio.open_positions.values()})
    bars_by_symbol: dict[str, Optional[pd.DataFrame]] = {}
    for sym in symbols:
        bars_by_symbol[sym] = _session_minute_bars(
            sym, session_date,
            session_minute_supplier=session_minute_supplier,
            minute_bars_supplier=minute_bars_supplier,
        )

    # Walk each lot. Snapshot the lots — closing a lot mutates open_positions.
    for pos in list(portfolio.open_positions.values()):
        entry_session = pos.entry_session or pos.entry_date
        if session_date < entry_session:
            continue
        minute_bars = bars_by_symbol.get(pos.symbol)
        if minute_bars is None or len(minute_bars) == 0:
            continue
        ev = walk_lot_exit(
            pos, minute_bars,
            exit_cfg=exits_cfg,
            same_minute_resolution=str(same_minute),
            cost_stress=cost_stress,
            quote_supplier=quote_supplier,
            trades_supplier=trades_supplier,
            signal_score_fn=signal_score_fn,
            seed=seed,
            fade_telemetry_out=fade_telemetry,
            # L11: the contract drives the default exit cross_spread (stops pay).
            simulation_mode=str((cfg.get("simulation") or {}).get("mode") or "smoke_fixture"),
        )
        if ev is None:
            continue
        if ev.ambiguous_bar_resolved:
            ambiguous += 1
        trade = portfolio.close_position_by_id(
            ev.position_id or pos.position_id,
            exit_price=ev.exit_price,
            exit_reason=ev.exit_reason,
            exit_date=ev.exit_date,
            exit_event=ev,
        )
        trades.append(trade)

    return {"trades": trades, "ambiguous": ambiguous, "fade_telemetry": fade_telemetry}


def drive_session_exits_daily(
    portfolio: Portfolio,
    session_date: _dt.date,
    *,
    cfg: dict,
    daily_bars_supplier: Callable[[str, _dt.date], Optional[pd.DataFrame]],
) -> dict[str, Any]:
    """Legacy daily-bar exit driving — ``smoke_fixture`` mode ONLY.

    Each open lot is evaluated against its symbol's last daily bar and closed by
    ``position_id``. Returns ``{"trades": [...], "ambiguous": n,
    "closes": {symbol: close}}`` — ``closes`` feeds the end-of-session
    mark-to-market.
    """
    exits_cfg = cfg.get("exits") or {}
    same_bar_policy = exits_cfg.get("same_bar_policy", "stop_first")
    trades: list[dict] = []
    ambiguous = 0

    symbols = sorted({p.symbol for p in portfolio.open_positions.values()})
    closes: dict[str, float] = {}
    rows_by_symbol: dict[str, dict] = {}
    for sym in symbols:
        day_bars = daily_bars_supplier(sym, session_date)
        if day_bars is None or len(day_bars) == 0:
            continue
        row = day_bars.iloc[-1].to_dict()
        closes[sym] = float(row.get("close", row.get("Close", 0.0)) or 0.0)
        rows_by_symbol[sym] = row

    for pos in list(portfolio.open_positions.values()):
        row = rows_by_symbol.get(pos.symbol)
        if row is None:
            continue
        ev = evaluate_exits(
            pos, bar=row, bar_date=session_date,
            exit_cfg=exits_cfg, same_bar_policy=same_bar_policy,
        )
        if ev is None:
            continue
        if ev.ambiguous_bar_resolved:
            ambiguous += 1
        trade = portfolio.close_position_by_id(
            pos.position_id, exit_price=ev.exit_price,
            exit_reason=ev.exit_reason, exit_date=session_date,
            exit_event=ev,
        )
        trades.append(trade)

    return {"trades": trades, "ambiguous": ambiguous, "closes": closes}
