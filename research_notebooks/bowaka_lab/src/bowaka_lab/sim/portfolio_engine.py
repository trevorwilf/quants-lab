"""BowakaPortfolioBacktester loop.

Implements the high-level flow from ``[Report §12.3]``:

  for signal_date in sessions(start, end):
      trade_date = next_session(signal_date)
      candidate_set = prefilter_replay(signal_date)
      update_existing_positions(trade_date)
      for candidate in candidates_by_rank:
          if portfolio_can_accept(candidate):
              maybe_enter(candidate, trade_date)
      run_intraday_position_simulation(trade_date)
      persist_daily_summary(trade_date)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Callable, Iterable

import pandas as pd

from bowaka_lab.config.models import (
    BowakaBacktestConfig,
    ExitConfig,
    PortfolioConfig,
    RealismConfig,
    ShadowRiskConfig,
)
from bowaka_lab.data.calendar import USEquityCalendar
from bowaka_lab.sim.exits import ExitEvent, evaluate_bar_exit, is_time_stop_due
from bowaka_lab.sim.fill_model import BowakaFillModel
from bowaka_lab.sim.intraday_confirmation import (
    ConfirmationResult,
    confirm_entry,
    latest_quote_at_or_before,
)
from bowaka_lab.sim.positions import SimulatedPosition
from bowaka_lab.utils.ids import trade_id


@dataclass
class TradeRecord:
    trade_id: str
    symbol: str
    signal_date: date
    trade_date: date
    prefilter_rank: int
    entry_rule: str
    entry_time: pd.Timestamp
    entry_price: float
    qty: int
    notional: float
    stop_price: float
    target_price: float
    exit_time: pd.Timestamp
    exit_price: float
    exit_reason: str
    pnl: float
    pnl_pct: float
    mfe_pct: float
    mae_pct: float
    time_to_mfe_minutes: int | None
    time_to_mae_minutes: int | None
    first_touch: str
    ambiguous_bar: bool
    data_feed: str = "iex"
    diagnostics: dict = field(default_factory=dict)


@dataclass
class EntrySkipRecord:
    """One row per (symbol, trade_date) that the confirmation gate skipped.

    Persisted as ``entry_skips.parquet`` so the weekly report and Phase 8
    reconciliation can see which candidates the engine refused to enter and
    why.
    """
    symbol: str
    trade_date: date
    fail_reason: str
    candidate_rank: int
    bar_ts: pd.Timestamp | None = None
    mid: float | None = None
    spread_pct: float | None = None
    quote_age_seconds: float | None = None


@dataclass
class BowakaBacktestResult:
    trades: list[TradeRecord]
    daily_summary: pd.DataFrame
    open_positions: list[SimulatedPosition]
    shadow_blocks: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    entry_skips: list[EntrySkipRecord] = field(default_factory=list)

    def entry_skips_df(self) -> pd.DataFrame:
        if not self.entry_skips:
            return pd.DataFrame(
                columns=[
                    "symbol", "trade_date", "fail_reason", "candidate_rank",
                    "bar_ts", "mid", "spread_pct", "quote_age_seconds",
                ]
            )
        return pd.DataFrame([s.__dict__ for s in self.entry_skips])

    def trades_df(self) -> pd.DataFrame:
        if not self.trades:
            return pd.DataFrame(
                columns=[
                    "trade_id",
                    "symbol",
                    "signal_date",
                    "trade_date",
                    "prefilter_rank",
                    "entry_rule",
                    "entry_time",
                    "entry_price",
                    "qty",
                    "notional",
                    "stop_price",
                    "target_price",
                    "exit_time",
                    "exit_price",
                    "exit_reason",
                    "pnl",
                    "pnl_pct",
                    "mfe_pct",
                    "mae_pct",
                    "first_touch",
                    "ambiguous_bar",
                ]
            )
        return pd.DataFrame([t.__dict__ for t in self.trades])


@dataclass
class _OpenPositionState:
    position: SimulatedPosition
    minutes_since_entry: int = 0


class BowakaPortfolioBacktester:
    """Multi-symbol, session-based, next-bar-fill backtester."""

    def __init__(
        self,
        config: BowakaBacktestConfig,
        *,
        candidate_source: Callable[[date], pd.DataFrame],
        minute_bars_for: Callable[[date, list[str]], pd.DataFrame],
        fill_model: BowakaFillModel | None = None,
        calendar: USEquityCalendar | None = None,
        quote_loader: Callable[[date, list[str]], pd.DataFrame] | None = None,
    ):
        self.cfg = config
        self.candidate_source = candidate_source
        self.minute_bars_for = minute_bars_for
        self.fill_model = fill_model or BowakaFillModel(slippage_bps=config.entry.slippage_bps)
        self.cal = calendar or USEquityCalendar(config.calendar.exchange)
        self.quote_loader = quote_loader

        # Engine-init guard: exact mode requires intraday_confirmation.enabled=true.
        if config.is_exact_mode and not config.entry.intraday_confirmation.enabled:
            raise RuntimeError(
                "exact mode requires entry.intraday_confirmation.enabled=true; "
                "research mode keeps the legacy bar-fill behavior."
            )

    def _confirmation_time_for_session(self, trade_date: date) -> pd.Timestamp:
        """Source uses ``09:30 + window_minutes`` for the confirmation tick."""
        ic = self.cfg.entry.intraday_confirmation
        session_open = pd.Timestamp(trade_date).tz_localize("America/New_York") + pd.Timedelta(
            hours=9, minutes=30
        )
        ts = session_open + pd.Timedelta(minutes=ic.window_minutes)
        return ts.tz_convert("UTC")

    def _entry_time_for_session(self, trade_date: date, rule: str) -> pd.Timestamp:
        """For the default 'fixed_time_HHMM' rule, return that ET timestamp."""
        if not rule.startswith("fixed_time_"):
            raise ValueError(f"Unsupported entry rule {rule!r}")
        hhmm = rule.split("fixed_time_", 1)[1]
        if len(hhmm) == 4:
            hh, mm = hhmm[:2], hhmm[2:]
        elif ":" in hhmm:
            hh, mm = hhmm.split(":", 1)
        else:
            raise ValueError(f"Cannot parse time {hhmm!r}")
        ts = pd.Timestamp(trade_date).tz_localize("America/New_York") + pd.Timedelta(hours=int(hh), minutes=int(mm))
        return ts.tz_convert("UTC")

    def _qty_for(self, *, entry_price: float, portfolio: PortfolioConfig) -> int:
        if portfolio.sizing_mode == "equal_slice":
            return max(0, int(portfolio.per_trade_notional // entry_price))
        # risk_per_trade requires stop_pct context — handled by caller in v1.
        return max(0, int(portfolio.per_trade_notional // entry_price))

    def _maybe_apply_realism_cap(
        self, *, qty: int, candidate: dict, realism: RealismConfig
    ) -> int:
        if not realism.max_position_as_adv_frac_enabled:
            return qty
        adv = float(candidate.get("avg_dollar_volume") or 0.0)
        if adv <= 0:
            return qty
        cap_frac = realism.max_position_as_adv_frac
        for tier in realism.adv_tier_caps:
            if tier.reject_if_below and tier.max_adv_dollars is not None and adv < tier.max_adv_dollars:
                return 0
            if tier.max_adv_dollars is None or adv <= tier.max_adv_dollars:
                if tier.max_position_as_adv_frac is not None:
                    cap_frac = tier.max_position_as_adv_frac
                    break
        entry_price = float(candidate.get("close") or 1.0)
        max_dollars = adv * cap_frac
        max_qty = int(max_dollars // entry_price)
        return max(0, min(qty, max_qty))

    def _check_shadow_risk(
        self,
        *,
        date_today: date,
        entries_today: int,
        gross_notional: float,
        loss_today: float,
        shadow: ShadowRiskConfig,
    ) -> list[dict]:
        blocks: list[dict] = []
        for thr in shadow.max_entries_thresholds:
            if entries_today >= thr:
                blocks.append({"rule": "max_entries", "threshold": thr, "trade_date": date_today})
        for thr in shadow.max_gross_exposure_thresholds:
            if gross_notional >= thr * self.cfg.portfolio.per_trade_notional:
                blocks.append({"rule": "max_gross_exposure", "threshold": thr, "trade_date": date_today})
        for thr in shadow.daily_loss_thresholds:
            if loss_today <= -thr * self.cfg.portfolio.per_trade_notional:
                blocks.append({"rule": "daily_loss", "threshold": thr, "trade_date": date_today})
        return blocks

    def run(self) -> BowakaBacktestResult:
        cfg = self.cfg
        trades: list[TradeRecord] = []
        open_positions: dict[str, _OpenPositionState] = {}
        shadow_blocks: list[dict] = []
        daily_rows: list[dict] = []
        entry_skips: list[EntrySkipRecord] = []

        sessions = self.cal.sessions(cfg.data.start_date, cfg.data.end_date)
        for signal_date in sessions:
            try:
                trade_date = self.cal.next_session(signal_date)
            except ValueError:
                continue
            if trade_date > cfg.data.end_date:
                continue
            candidates = self.candidate_source(signal_date)
            if candidates is None:
                candidates = pd.DataFrame(columns=["symbol", "rank"])

            symbols_to_load: list[str] = list(open_positions.keys())
            if not candidates.empty:
                symbols_to_load.extend({c["symbol"] for _, c in candidates.iterrows()})
            symbols_to_load = list(set(symbols_to_load))
            if symbols_to_load:
                minute_bars = self.minute_bars_for(trade_date, symbols_to_load)
            else:
                minute_bars = pd.DataFrame()

            entries_today = 0
            exits_today = 0
            loss_today = 0.0

            # 1. Process exits for open positions across the trade_date bars.
            for sym in list(open_positions.keys()):
                state = open_positions[sym]
                pos = state.position
                bars = minute_bars[minute_bars["symbol"] == sym].sort_values("timestamp") if not minute_bars.empty else pd.DataFrame()
                if bars.empty:
                    continue
                for _, bar in bars.iterrows():
                    state.minutes_since_entry += 1
                    pos.update_mfe_mae(
                        ts=pd.Timestamp(bar["timestamp"]),
                        high=float(bar["high"]),
                        low=float(bar["low"]),
                        minutes_since_entry=state.minutes_since_entry,
                    )
                    ev = evaluate_bar_exit(position=pos, bar=bar.to_dict(), cfg=cfg.exits, fill_model=self.fill_model)
                    if ev:
                        pos.close(exit_time=ev.fill_time, exit_price=ev.fill_price, exit_reason=ev.exit_reason)
                        rank_val = 0
                        if not candidates.empty and "symbol" in candidates.columns and sym in candidates["symbol"].values:
                            rank_val = int(candidates.loc[candidates["symbol"] == sym, "rank"].iloc[0])
                        trades.append(self._build_record(pos, prefilter_rank=rank_val, ambiguous_bar=ev.ambiguous_bar))
                        exits_today += 1
                        loss_today += min(0.0, pos.realized_pnl)
                        open_positions.pop(sym, None)
                        break
                else:
                    if is_time_stop_due(today_session=trade_date, max_hold_exit_date=pos.max_hold_exit_date):
                        # Close at the day's last bar close.
                        last_bar = bars.iloc[-1]
                        exit_price = float(last_bar["close"])
                        pos.close(exit_time=pd.Timestamp(last_bar["timestamp"]), exit_price=exit_price, exit_reason="time_stop")
                        trades.append(self._build_record(pos, prefilter_rank=0, ambiguous_bar=False))
                        exits_today += 1
                        loss_today += min(0.0, pos.realized_pnl)
                        open_positions.pop(sym, None)

            # 2. Evaluate entries for ranked candidates on trade_date.
            ic_cfg = cfg.entry.intraday_confirmation
            if ic_cfg.enabled:
                entry_time = self._confirmation_time_for_session(trade_date)
            else:
                entry_time = self._entry_time_for_session(trade_date, cfg.entry.default_rule)

            # Load quotes once per session (callable returns empty when missing).
            quotes_today = pd.DataFrame()
            if ic_cfg.enabled and self.quote_loader is not None:
                symbols_for_quotes = (
                    candidates["symbol"].astype(str).tolist() if not candidates.empty else []
                )
                if symbols_for_quotes:
                    try:
                        quotes_today = self.quote_loader(trade_date, symbols_for_quotes)
                    except Exception:
                        quotes_today = pd.DataFrame()

            entries_blocked = False
            candidates_to_iter = candidates.sort_values("rank") if not candidates.empty else pd.DataFrame()
            for _, candidate in candidates_to_iter.iterrows():
                sym = candidate["symbol"]
                if sym in open_positions:
                    continue
                if len(open_positions) >= cfg.portfolio.max_concurrent_positions:
                    entries_blocked = True
                    break
                if cfg.portfolio.max_total_entries_per_day is not None and entries_today >= cfg.portfolio.max_total_entries_per_day:
                    entries_blocked = True
                    break
                sym_bars = minute_bars[minute_bars["symbol"] == sym].sort_values("timestamp") if not minute_bars.empty else pd.DataFrame()
                if sym_bars.empty:
                    continue
                entry_bar = sym_bars[sym_bars["timestamp"] >= entry_time]
                if entry_bar.empty:
                    continue
                entry_bar = entry_bar.iloc[0]
                bar_ts = pd.Timestamp(entry_bar["timestamp"])

                # Intraday confirmation gate (Phase fidelity-3).
                fill_label = "no_confirmation"
                confirmation: ConfirmationResult | None = None
                latest_q: dict | None = None
                if ic_cfg.enabled:
                    sym_quotes = (
                        quotes_today[quotes_today["symbol"] == sym]
                        if not quotes_today.empty else pd.DataFrame()
                    )
                    latest_q = latest_quote_at_or_before(sym_quotes, bar_ts)
                    if latest_q is None:
                        # No quote available: exact mode fails closed, research
                        # mode falls back to bar fill with a 'no_quote' label.
                        if cfg.is_exact_mode:
                            entry_skips.append(EntrySkipRecord(
                                symbol=str(sym), trade_date=trade_date,
                                fail_reason="no_quote_exact_mode",
                                candidate_rank=int(candidate.get("rank") or 0),
                                bar_ts=bar_ts,
                            ))
                            continue
                        fill_label = "no_quote"
                    else:
                        confirmation = confirm_entry(
                            candidate_close=float(candidate.get("close") or 0.0),
                            quote_row=latest_q,
                            now_utc=bar_ts,
                            max_spread_pct=ic_cfg.max_spread_pct,
                            max_quote_age_seconds=ic_cfg.max_quote_age_seconds,
                            price_band_max_above=ic_cfg.price_band.max_pct_above_close,
                            price_band_min_below=ic_cfg.price_band.min_pct_below_close,
                        )
                        if not confirmation.passed:
                            entry_skips.append(EntrySkipRecord(
                                symbol=str(sym), trade_date=trade_date,
                                fail_reason=confirmation.fail_reason or "confirmation_failed",
                                candidate_rank=int(candidate.get("rank") or 0),
                                bar_ts=bar_ts,
                                mid=confirmation.mid,
                                spread_pct=confirmation.spread_pct,
                                quote_age_seconds=confirmation.quote_age_seconds,
                            ))
                            continue
                        fill_label = "quote_confirmed"

                # Build the fill. Quote-confirmed entries can use the ask
                # (when use_quotes_if_available is on). Bar-fill is the fallback.
                use_quote_fill = (
                    confirmation is not None
                    and latest_q is not None
                    and cfg.entry.use_quotes_if_available
                )
                if use_quote_fill:
                    fill = self.fill_model.buy_from_quote(latest_q)
                else:
                    fill = self.fill_model.buy_from_bar(entry_bar.to_dict())
                entry_price = fill.fill_price
                fill_diag = {**(fill.diagnostics or {}), "fill_label": fill_label}
                qty = self._qty_for(entry_price=entry_price, portfolio=cfg.portfolio)
                qty = self._maybe_apply_realism_cap(qty=qty, candidate=candidate.to_dict(), realism=cfg.realism)
                if qty <= 0:
                    continue
                tid = trade_id(symbol=sym, trade_date=trade_date, entry_rule=cfg.entry.default_rule, config_hash="cfg")
                stop_price = entry_price * (1.0 - cfg.exits.stop_pct)
                target_price = entry_price * (1.0 + cfg.exits.target_pct)
                max_hold_date = self.cal.add_sessions(trade_date, cfg.exits.max_hold_days)
                pos = SimulatedPosition(
                    trade_id=tid,
                    symbol=sym,
                    signal_date=signal_date,
                    trade_date=trade_date,
                    entry_time=fill.fill_time,
                    entry_price=entry_price,
                    qty=qty,
                    stop_price=stop_price,
                    target_price=target_price,
                    max_hold_exit_date=max_hold_date,
                )
                state = _OpenPositionState(position=pos, minutes_since_entry=0)
                # Walk the rest of the bars on the entry day for same-day exit evaluation.
                rest = sym_bars[sym_bars["timestamp"] > fill.fill_time]
                exited_intraday = False
                for _, bar in rest.iterrows():
                    state.minutes_since_entry += 1
                    pos.update_mfe_mae(
                        ts=pd.Timestamp(bar["timestamp"]),
                        high=float(bar["high"]),
                        low=float(bar["low"]),
                        minutes_since_entry=state.minutes_since_entry,
                    )
                    ev = evaluate_bar_exit(position=pos, bar=bar.to_dict(), cfg=cfg.exits, fill_model=self.fill_model)
                    if ev:
                        pos.close(exit_time=ev.fill_time, exit_price=ev.fill_price, exit_reason=ev.exit_reason)
                        trades.append(self._build_record(pos, prefilter_rank=int(candidate["rank"]), ambiguous_bar=ev.ambiguous_bar))
                        exits_today += 1
                        loss_today += min(0.0, pos.realized_pnl)
                        exited_intraday = True
                        break
                if not exited_intraday:
                    if cfg.exits.max_hold_days == 0:
                        last_bar = sym_bars.iloc[-1]
                        pos.close(exit_time=pd.Timestamp(last_bar["timestamp"]), exit_price=float(last_bar["close"]), exit_reason="time_stop")
                        trades.append(self._build_record(pos, prefilter_rank=int(candidate["rank"]), ambiguous_bar=False))
                        exits_today += 1
                    else:
                        open_positions[sym] = state
                        entries_today += 1
                else:
                    entries_today += 1

            # 3. Shadow-risk telemetry only (not enforced).
            gross_notional = sum(s.position.notional for s in open_positions.values())
            shadow_blocks.extend(
                self._check_shadow_risk(
                    date_today=trade_date,
                    entries_today=entries_today,
                    gross_notional=gross_notional,
                    loss_today=loss_today,
                    shadow=cfg.shadow_risk,
                )
            )

            daily_rows.append({
                "trade_date": trade_date,
                "candidates": int(candidates.shape[0]),
                "entries": entries_today,
                "exits": exits_today,
                "open_at_close": len(open_positions),
                "entries_blocked": entries_blocked,
            })

        daily_df = pd.DataFrame(daily_rows)
        return BowakaBacktestResult(
            trades=trades,
            daily_summary=daily_df,
            open_positions=[s.position for s in open_positions.values()],
            shadow_blocks=shadow_blocks,
            metadata={"sessions": len(sessions)},
            entry_skips=entry_skips,
        )

    def _build_record(self, pos: SimulatedPosition, *, prefilter_rank: int, ambiguous_bar: bool) -> TradeRecord:
        first_touch = {"stop_hit": "stop", "stop_gap": "stop", "ambiguous_bar_stop": "stop",
                       "target_hit": "target", "ambiguous_bar_target": "target"}.get(pos.exit_reason or "", "none")
        return TradeRecord(
            trade_id=pos.trade_id,
            symbol=pos.symbol,
            signal_date=pos.signal_date,
            trade_date=pos.trade_date,
            prefilter_rank=prefilter_rank,
            entry_rule=self.cfg.entry.default_rule,
            entry_time=pos.entry_time,
            entry_price=pos.entry_price,
            qty=pos.qty,
            notional=pos.notional,
            stop_price=pos.stop_price,
            target_price=pos.target_price,
            exit_time=pos.exit_time or pos.entry_time,
            exit_price=pos.exit_price or pos.entry_price,
            exit_reason=pos.exit_reason or "open",
            pnl=pos.realized_pnl,
            pnl_pct=(pos.exit_price or pos.entry_price) / pos.entry_price - 1.0 if pos.entry_price else 0.0,
            mfe_pct=pos.mfe_pct,
            mae_pct=pos.mae_pct,
            time_to_mfe_minutes=pos.time_to_mfe_minutes,
            time_to_mae_minutes=pos.time_to_mae_minutes,
            first_touch=first_touch,
            ambiguous_bar=ambiguous_bar,
            data_feed=self.cfg.data.feed,
        )
