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
from .orders import OrderPlan, OrderSide, OrderStatus, ParentOrder
from .portfolio import Portfolio, Position
from .quote_model import QuoteSnapshot, get_quote
from .risk_gates import RiskGateResult, evaluate_risk_gates


@dataclass
class StrategyConsumerResult:
    decisions: list[dict] = field(default_factory=list)
    new_positions: list[Position] = field(default_factory=list)
    parent_orders: list[ParentOrder] = field(default_factory=list)


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
    ) -> StrategyConsumerResult:
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

        # Build the quote (historical or synthetic).
        last_price = float((candidate_event.get("forming_session_bar") or {}).get("last_price") or 0.0)
        quote: QuoteSnapshot = get_quote(
            symbol=symbol, at=decision_ts,
            last_price=last_price, historical_quote=historical_quote,
            stress_level=cfg.get("backtest", {}).get("cost_stress", "conservative"),
        )

        # Spread / age checks.
        max_spread_bps = int(execution_cfg.get("max_spread_bps", 50))
        max_quote_age = int(execution_cfg.get("max_quote_age_seconds", 5))
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

        # Broker accepted (both modes reach here only on a non-reject). Add the
        # position lot (entry price = quote.ask for a buy marketable-limit).
        ts_pts = candidate_event.get("scan_timestamp", str(decision_ts))
        entry_date = (
            _dt.datetime.fromisoformat(ts_pts.replace("Z", "+00:00")).date()
            if isinstance(ts_pts, str)
            else _dt.date.today()
        )
        position = Position(
            symbol=symbol,
            entry_date=entry_date,
            entry_price=quote.ask,
            qty=qty,
            stop_pct=plan.stop_pct,
            target_pct=plan.target_pct,
            max_hold_days=plan.max_hold_days,
            candidate_event_id=candidate_event["event_id"],
            current_price=quote.ask,
            parent_order_id=parent.parent_order_id,
            link_id=parent.parent_order_id,
            entry_session=entry_date,
        )
        self._portfolio.add_position(position)
        result.new_positions.append(position)
        return result
