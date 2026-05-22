"""Simulation-mode adapter of the v2 strategy event consumer.

§15 remediations applied:
- Reads ``signal_strength`` from ``features.signal_strength`` (§15.2 P1 fix —
  archive read from a top-level key that didn't exist).
- Emits a canonical ``broker_reject`` record via
  ``schemas.decisions.build_broker_reject_record`` (§15.1 P0).

Realism remediation Phase 5:

- Multi-lot per symbol. A symbol with open lots is NOT blocked from re-entry.
  ``same_symbol_entries_per_day`` (default 1) is enforced against the
  portfolio's per-session ``entered_symbols_today`` set, and
  ``risk.max_lots_per_symbol`` against ``portfolio.lots_for_symbol(symbol)``.
- ``accepted_event_sequencing`` controls the temporal ORDER of decision events:
  - ``pre_submit`` (parity / smoke): emit ``decision: accepted`` immediately
    after the gates pass, BEFORE broker submission. On broker reject emit a
    follow-up canonical ``broker_reject`` record. No position is created.
  - ``post_submit`` (realism): emit ``decision: submitted_pending`` after the
    gates pass; emit ``decision: accepted`` only after the broker confirms;
    ``broker_reject`` on reject.
  A broker reject NEVER creates a position, in either mode.
"""
from __future__ import annotations

import datetime as _dt
import random
from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from ..config.models import SimulationConfig
from ..schemas.decisions import (
    build_accepted_entry_decision,
    build_broker_reject_record,
    build_rejected_entry_decision,
    build_submitted_pending_decision,
)
from .broker import SimulatedBroker
from .fills import (
    FillResult,
    simulate_market_fill,
    simulate_marketable_limit_fill,
)
from .orders import OrderPlan, OrderSide, OrderStatus, ParentOrder
from .portfolio import Portfolio, Position
from .quote_model import QuoteResolution, QuoteSnapshot, resolve_quote
from .risk_gates import RiskGateResult, evaluate_risk_gates


@dataclass
class StrategyConsumerResult:
    decisions: list[dict] = field(default_factory=list)
    new_positions: list[Position] = field(default_factory=list)
    parent_orders: list[ParentOrder] = field(default_factory=list)
    #: Realism Phase 6 — per-candidate execution-quality records (one per
    #: position created, plus a counter of missing-quote rejects). Consumed by
    #: the backtester to build ``execution_quality.parquet``.
    fills: list[dict] = field(default_factory=list)
    missing_quote_count: int = 0


def compute_target_notional(sizing_cfg: Mapping[str, Any]) -> float:
    """Per-position target notional from the sizing config (realism Phase 1).

    ``equal_slice`` (live default): ``equal_slice_bankroll_fraction *
    bankroll_fixed_dollars / max_concurrent_positions``. ``fixed_dollar``
    (back-compat): ``min(dollars_per_position, max_position_dollars)``. The
    result is floored at ``min_order_notional`` and capped at
    ``max_per_trade_dollars`` when set.
    """
    mode = str(sizing_cfg.get("sizing_mode", "equal_slice"))
    if mode == "fixed_dollar":
        vals = [
            float(v)
            for v in (sizing_cfg.get("dollars_per_position"), sizing_cfg.get("max_position_dollars"))
            if v is not None
        ]
        target = min(vals) if vals else 5_000.0
    else:  # equal_slice
        bankroll = float(sizing_cfg.get("bankroll_fixed_dollars", 90_000.0))
        n_slots = max(1, int(sizing_cfg.get("max_concurrent_positions", 18)))
        frac = float(sizing_cfg.get("equal_slice_bankroll_fraction", 0.80))
        target = frac * bankroll / n_slots
    target = max(target, float(sizing_cfg.get("min_order_notional", 0.0)))
    cap = sizing_cfg.get("max_per_trade_dollars")
    if cap is not None:
        target = min(target, float(cap))
    return target


def size_quantity(target_notional: float, price: float) -> int:
    """Whole-share quantity for ``target_notional`` at ``price`` (floor division)."""
    if price <= 0:
        return 0
    return int(target_notional // price)


class StrategyConsumer:
    def __init__(
        self,
        *,
        portfolio: Portfolio,
        broker: SimulatedBroker,
        cfg: dict,
    ) -> None:
        self._portfolio = portfolio
        self._broker = broker
        self._cfg = cfg
        # Resolve the simulation contract once. ``accepted_event_sequencing``
        # is mode-coupled (pre_submit for parity/smoke, post_submit for
        # realism) but a config may pin it explicitly.
        self._sim_cfg = SimulationConfig.model_validate(cfg.get("simulation") or {})

    @property
    def accepted_event_sequencing(self) -> str:
        """Resolved event-ordering policy — ``pre_submit`` or ``post_submit``."""
        return self._sim_cfg.accepted_event_sequencing or "pre_submit"

    def consume(
        self,
        candidate_event: dict,
        *,
        decision_ts: Any,
        historical_quote: Optional[dict] = None,
        forward_minute_bars: Optional[Any] = None,
    ) -> StrategyConsumerResult:
        """Consume one candidate event and emit decision(s) / a position.

        ``historical_quote`` is the real quote from the quote supplier (``None``
        when the lake has none for this symbol/ts). ``forward_minute_bars`` is
        the minute path forward from ``scan_ts`` — the order lifetime a
        marketable-limit fill walks to detect a timeout (Phase 6).
        """
        result = StrategyConsumerResult()
        cfg = self._cfg
        feats = candidate_event.get("features", {}) or {}
        signal_strength = float(feats.get("signal_strength", 0.0))  # §15.2 P1 fix

        execution_cfg = cfg.get("execution") or {}
        sizing_cfg = cfg.get("sizing") or {}
        risk_cfg = cfg.get("risk") or {}
        exits_cfg = cfg.get("exits") or {}
        market_data_cfg = cfg.get("market_data") or {}
        symbol = candidate_event["symbol"]
        cost_stress = str((cfg.get("backtest") or {}).get("cost_stress", "conservative"))

        # Reject low signal strength early.
        min_signal_strength = float(
            (cfg.get("scanner") or {}).get("min_signal_strength", 0.0)
        )
        if signal_strength < min_signal_strength:
            result.decisions.append(build_rejected_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=execution_cfg.get("order_type", "marketable_limit"),
                reason="lost_signal_before_entry",
            ))
            return result

        # Build the quote — historical when available, else fall back per
        # ``simulation.quote_fallback_policy`` (Phase 6).
        last_price = float((candidate_event.get("forming_session_bar") or {}).get("last_price") or 0.0)
        candidate_adv_for_quote = float(
            (candidate_event.get("prior_daily_baselines") or {}).get("avg_dollar_volume_20d") or 0.0
        ) or 5_000_000.0
        volatility_pct = float(
            (candidate_event.get("prior_daily_baselines") or {}).get("prior_atr_pct") or 0.0
        ) or 0.02
        max_quote_age = int(execution_cfg.get("max_quote_age_seconds", 5))
        # Deterministic RNG seeded on (symbol, scan_ts) so synthetic quote ages
        # are reproducible run-to-run.
        rng = random.Random(hash((symbol, str(candidate_event.get("scan_timestamp", decision_ts)))))
        resolution: QuoteResolution = resolve_quote(
            symbol=symbol, at=decision_ts,
            signal_price=last_price or 1.0,
            historical_quote=historical_quote,
            quote_fallback_policy=self._sim_cfg.quote_fallback_policy or "zero_spread",
            adv_dollars=candidate_adv_for_quote,
            volatility_pct=volatility_pct,
            max_quote_age_seconds=max_quote_age,
            stress_level=cost_stress,
        )
        # ``require_real`` with no historical quote — reject the candidate.
        if resolution.missing_quote or resolution.quote is None:
            result.missing_quote_count += 1
            result.decisions.append(build_rejected_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=execution_cfg.get("order_type", "marketable_limit"),
                reason="missing_quote",
            ))
            return result
        quote: QuoteSnapshot = resolution.quote

        # Spread / age checks.
        max_spread_bps = int(execution_cfg.get("max_spread_bps", 50))
        spread_bps = quote.spread_pct * 10_000.0
        if spread_bps > max_spread_bps:
            result.decisions.append(build_rejected_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=execution_cfg.get("order_type", "marketable_limit"),
                reason="spread_too_wide",
                quote=quote.__dict__,
            ))
            return result
        if quote.quote_age_seconds > max_quote_age:
            result.decisions.append(build_rejected_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=execution_cfg.get("order_type", "marketable_limit"),
                reason="quote_stale",
                quote=quote.__dict__,
            ))
            return result

        # Multi-lot portfolio gates (Realism Phase 5). A symbol with open lots
        # is NOT blocked from re-entry: instead `same_symbol_entries_per_day`
        # caps how many entries it may take in a single session, and
        # `max_lots_per_symbol` caps how many concurrent lots it may hold.
        portfolio_state = self._portfolio.state
        entered_today = (
            portfolio_state.entered_symbols_today if portfolio_state is not None else set()
        )
        same_symbol_per_day = int(risk_cfg.get("same_symbol_entries_per_day", 1))
        # `entered_symbols_today` records each symbol opened this session. With a
        # cap of 1 (the live default) a symbol already in the set is rejected;
        # for caps > 1, count this session's lots for the symbol.
        if same_symbol_per_day <= 1:
            already_entered_today = symbol in entered_today
        else:
            session_date = portfolio_state.session_date if portfolio_state else None
            lots_today = sum(
                1
                for p in self._portfolio.positions_for_symbol(symbol)
                if p.entry_session == session_date
            )
            already_entered_today = lots_today >= same_symbol_per_day
        if already_entered_today:
            result.decisions.append(build_rejected_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=execution_cfg.get("order_type", "marketable_limit"),
                reason="same_symbol_entries_per_day",
                quote=quote.__dict__,
            ))
            return result

        max_lots = int(risk_cfg.get("max_lots_per_symbol", 1))
        if self._portfolio.lots_for_symbol(symbol) >= max_lots:
            result.decisions.append(build_rejected_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=execution_cfg.get("order_type", "marketable_limit"),
                reason="max_lots_per_symbol",
                quote=quote.__dict__,
            ))
            return result

        # Sizing (equal-slice by default; see compute_target_notional).
        target_notional = compute_target_notional(sizing_cfg)
        candidate_adv = float(
            (candidate_event.get("prior_daily_baselines") or {}).get("avg_dollar_volume_20d") or 0.0
        )

        gate = evaluate_risk_gates(
            portfolio=self._portfolio,
            risk_cfg=risk_cfg, sizing_cfg=sizing_cfg,
            candidate_adv=candidate_adv,
            target_notional=target_notional,
            symbol=symbol,
        )
        if not gate.accepted:
            result.decisions.append(build_rejected_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=execution_cfg.get("order_type", "marketable_limit"),
                reason=gate.reject_reason or "kill_switch",
                quote=quote.__dict__,
                risk_snapshot={
                    "bankroll": self._portfolio.state.bankroll,
                    "gross_exposure_dollars": self._portfolio.state.gross_exposure_dollars,
                    "gross_exposure_pct": self._portfolio.state.gross_exposure_pct,
                    "entries_today": self._portfolio.state.entries_today,
                    "open_positions": len(self._portfolio.open_positions),
                    "candidate_adv": candidate_adv,
                    "target_notional": target_notional,
                    "adv_participation_frac": gate.adv_participation_frac,
                },
            ))
            return result

        qty = size_quantity(target_notional, quote.ask)
        if qty == 0:
            result.decisions.append(build_rejected_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=execution_cfg.get("order_type", "marketable_limit"),
                reason="lost_signal_before_entry",
                quote=quote.__dict__,
            ))
            return result

        plan = OrderPlan(
            side=OrderSide.BUY,
            order_style=execution_cfg.get("order_type", "marketable_limit"),
            qty=qty,
            stop_pct=float(exits_cfg.get("stop_pct", exits_cfg.get("stop_loss_pct", 0.02))),
            target_pct=float(exits_cfg.get("target_pct", exits_cfg.get("take_profit_pct", 0.06))),
            max_hold_days=int(exits_cfg.get("max_hold_days", 5)),
            estimated_notional=qty * quote.ask,
        )
        parent = ParentOrder(
            parent_order_id=ParentOrder.make_id(),
            symbol=symbol,
            plan=plan,
            candidate_event_id=candidate_event["event_id"],
            created_at=str(decision_ts),
        )

        order_plan_dict = {
            "side": plan.side.value, "order_style": plan.order_style,
            "qty": plan.qty, "estimated_notional": plan.estimated_notional,
            "stop_pct": plan.stop_pct, "target_pct": plan.target_pct,
            "max_hold_days": plan.max_hold_days,
        }
        risk_snapshot_dict = {
            "bankroll": self._portfolio.state.bankroll,
            "gross_exposure_dollars": self._portfolio.state.gross_exposure_dollars,
            "gross_exposure_pct": self._portfolio.state.gross_exposure_pct,
            "entries_today": self._portfolio.state.entries_today,
            "open_positions": len(self._portfolio.open_positions),
            "candidate_adv": candidate_adv,
            "target_notional": target_notional,
            "adv_participation_frac": gate.adv_participation_frac,
        }

        # ---- accepted_event_sequencing (Realism Phase 5) ------------------
        # `pre_submit` (parity / smoke): emit `accepted` immediately, BEFORE
        # broker submission. `post_submit` (realism): emit `submitted_pending`
        # first, then `accepted` only after the broker confirms. In BOTH modes a
        # broker reject emits a canonical `broker_reject` and creates NO
        # position — only the temporal order of events differs.
        sequencing = self.accepted_event_sequencing

        if sequencing == "pre_submit":
            # Decision is final the moment the gates pass — emit `accepted` now.
            result.decisions.append(build_accepted_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=plan.order_style,
                quote=quote.__dict__,
                risk_snapshot=risk_snapshot_dict,
                order_plan=order_plan_dict,
            ))
            submit_result = self._broker.submit(parent)
            result.parent_orders.append(parent)
            if submit_result.status == OrderStatus.REJECTED:
                # Follow-up canonical broker_reject; no position created.
                result.decisions.append(build_broker_reject_record(
                    candidate_event=candidate_event,
                    decision_ts=decision_ts,
                    broker_status="rejected",
                    raw_response_summary=submit_result.raw_response,
                    order_plan=order_plan_dict,
                    quote=quote.__dict__,
                    risk_snapshot=risk_snapshot_dict,
                ))
                return result
        else:  # post_submit
            # Gates passed but the order is still in flight — emit
            # `submitted_pending`, then submit.
            result.decisions.append(build_submitted_pending_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=plan.order_style,
                quote=quote.__dict__,
                risk_snapshot=risk_snapshot_dict,
                order_plan=order_plan_dict,
            ))
            submit_result = self._broker.submit(parent)
            result.parent_orders.append(parent)
            if submit_result.status == OrderStatus.REJECTED:
                result.decisions.append(build_broker_reject_record(
                    candidate_event=candidate_event,
                    decision_ts=decision_ts,
                    broker_status="rejected",
                    raw_response_summary=submit_result.raw_response,
                    order_plan=order_plan_dict,
                    quote=quote.__dict__,
                    risk_snapshot=risk_snapshot_dict,
                ))
                return result
            # Broker confirmed — only now emit `accepted`.
            result.decisions.append(build_accepted_entry_decision(
                candidate_event=candidate_event,
                decision_ts=decision_ts,
                entry_trigger=plan.order_style,
                quote=quote.__dict__,
                risk_snapshot=risk_snapshot_dict,
                order_plan=order_plan_dict,
            ))

        # ---- Fill simulation (Realism Phase 6) ----------------------------
        # The broker accepted; now SIMULATE THE FILL. The position's entry price
        # is the actual fill price (quote.ask + slippage for a market order, or
        # the marketable-limit price), NOT the raw quote.ask. A fill may fail —
        # a marketable-limit timeout, or a partial below min_order_notional — in
        # which case NO position is created.
        ts_pts = candidate_event.get("scan_timestamp", str(decision_ts))
        entry_date = (
            _dt.datetime.fromisoformat(ts_pts.replace("Z", "+00:00")).date()
            if isinstance(ts_pts, str)
            else _dt.date.today()
        )
        # Liquidity proxy — a small fraction of the candidate's prior ADV,
        # expressed in shares. With no ADV the order is unconstrained.
        liquidity_proxy_shares: Optional[float] = None
        if candidate_adv > 0 and quote.ask > 0:
            adv_shares = candidate_adv / quote.ask
            liquidity_cap_frac = float(execution_cfg.get("liquidity_proxy_adv_frac", 0.05))
            liquidity_proxy_shares = adv_shares * liquidity_cap_frac
        min_order_notional = float(sizing_cfg.get("min_order_notional", 0.0))
        commission_per_share = float(execution_cfg.get("commission_per_share", 0.0))
        regulatory_fee_bps = float(execution_cfg.get("regulatory_fee_bps", 0.0))

        if plan.order_style == "market":
            fill: FillResult = simulate_market_fill(
                side="buy", requested_qty=qty, quote=quote,
                liquidity_proxy_shares=liquidity_proxy_shares,
                cost_stress=cost_stress,
                adv_participation_frac=gate.adv_participation_frac,
                min_order_notional=min_order_notional,
                commission_per_share=commission_per_share,
                regulatory_fee_bps=regulatory_fee_bps,
            )
        else:  # marketable_limit (and "limit" — treated as marketable_limit here)
            fill = simulate_marketable_limit_fill(
                side="buy", requested_qty=qty, quote=quote,
                marketable_limit_slippage_pct=float(
                    execution_cfg.get("marketable_limit_slippage_pct",
                                      execution_cfg.get("limit_offset_bps", 5) / 10_000.0)
                ),
                marketable_limit_timeout_seconds=int(
                    execution_cfg.get("marketable_limit_timeout_seconds", 30)
                ),
                minute_bars=forward_minute_bars,
                scan_ts=ts_pts,
                liquidity_proxy_shares=liquidity_proxy_shares,
                cost_stress=cost_stress,
                adv_participation_frac=gate.adv_participation_frac,
                min_order_notional=min_order_notional,
                commission_per_share=commission_per_share,
                regulatory_fee_bps=regulatory_fee_bps,
            )

        # Record the fill outcome (filled or not) for the execution-quality
        # report. ``quote_source`` distinguishes real vs synthetic quotes.
        fill_record = {
            "parent_order_id": parent.parent_order_id,
            "symbol": symbol,
            "order_style": fill.order_style,
            "filled": fill.filled,
            "filled_qty": fill.filled_qty,
            "requested_qty": qty,
            "avg_fill_price": fill.avg_fill_price,
            "notional": fill.notional,
            "slippage_bps": fill.slippage_bps_total,
            "is_partial": fill.is_partial,
            "reason": fill.reason,
            "commission": fill.commission,
            "regulatory_fees": fill.regulatory_fees,
            "total_fees": fill.total_fees,
            "liquidity_participation_frac": fill.liquidity_participation_frac,
            "quote_source": quote.source,
            "quote_spread_pct": quote.spread_pct,
            "quote_age_seconds": quote.quote_age_seconds,
            "cost_stress": cost_stress,
        }
        result.fills.append(fill_record)
        parent.filled_qty = fill.filled_qty
        parent.avg_fill_price = fill.avg_fill_price if fill.filled else None

        if not fill.filled:
            # No executable fill (timeout / partial-below-min / no liquidity).
            # The order was accepted by the broker but produced no position.
            parent.status = OrderStatus.CANCELED
            return result

        # ---- Brackets from the ACTUAL FILL (live bracket_pricing_mode:
        # actual_fill). stop_price / target_price are computed off the fill
        # price, never the signal price, and attach AFTER the fill.
        fill_price = fill.avg_fill_price
        stop_price = round(fill_price * (1.0 - plan.stop_pct), 4)
        target_price = round(fill_price * (1.0 + plan.target_pct), 4)

        position = Position(
            symbol=symbol,
            entry_date=entry_date,
            entry_price=fill_price,
            qty=fill.filled_qty,
            stop_pct=plan.stop_pct,
            target_pct=plan.target_pct,
            max_hold_days=plan.max_hold_days,
            candidate_event_id=candidate_event["event_id"],
            current_price=fill_price,
            parent_order_id=parent.parent_order_id,
            link_id=parent.parent_order_id,
            entry_session=entry_date,
            # Realism Phase 7 — the fill minute the per-lot minute-path exit
            # walk starts AFTER. Taken from the candidate's scan timestamp (the
            # marketable-limit fill lands within the order-lifetime window, so
            # the scan minute is the conservative fill-minute anchor).
            entry_timestamp=str(ts_pts) if ts_pts else None,
            fill_source=quote.source,
            fill_slippage_bps=fill.slippage_bps_total,
            fill_is_partial=fill.is_partial,
            fill_commission=fill.commission,
            fill_regulatory_fees=fill.regulatory_fees,
            fill_liquidity_participation=fill.liquidity_participation_frac,
            stop_price=stop_price,
            target_price=target_price,
            bracket_pricing_mode="actual_fill",
            bracket_attached=True,
        )
        parent.status = OrderStatus.FILLED if not fill.is_partial else OrderStatus.PARTIALLY_FILLED
        self._portfolio.add_position(position)
        result.new_positions.append(position)
        return result
