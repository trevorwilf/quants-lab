"""Simulation-mode adapter of the v2 strategy event consumer.

§15 remediations applied:
- Reads ``signal_strength`` from ``features.signal_strength`` (§15.2 P1 fix —
  archive read from a top-level key that didn't exist).
- Emits ENTRY decision AFTER broker confirm; on reject emits a canonical
  ``broker_reject`` record via ``schemas.decisions.build_broker_reject_record``
  (§15.1 P0).
"""
from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Any, Optional

from ..schemas.decisions import (
    build_accepted_entry_decision,
    build_broker_reject_record,
    build_rejected_entry_decision,
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
            symbol=candidate_event["symbol"], at=decision_ts,
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

        # Sizing.
        dollars_per_position = float(sizing_cfg.get("dollars_per_position", 5000))
        max_position_dollars = float(sizing_cfg.get("max_position_dollars", 25_000))
        target_notional = min(dollars_per_position, max_position_dollars)
        candidate_adv = float(
            (candidate_event.get("prior_daily_baselines") or {}).get("avg_dollar_volume_20d") or 0.0
        )

        gate = evaluate_risk_gates(
            portfolio=self._portfolio,
            risk_cfg=risk_cfg, sizing_cfg=sizing_cfg,
            candidate_adv=candidate_adv,
            target_notional=target_notional,
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

        qty = max(1, int(target_notional / quote.ask)) if quote.ask > 0 else 0
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
            stop_pct=float(exits_cfg.get("stop_loss_pct", 0.02)),
            target_pct=float(exits_cfg.get("take_profit_pct", 0.06)),
            max_hold_days=int(exits_cfg.get("max_hold_days", 5)),
            estimated_notional=qty * quote.ask,
        )
        parent = ParentOrder(
            parent_order_id=ParentOrder.make_id(),
            symbol=candidate_event["symbol"],
            plan=plan,
            candidate_event_id=candidate_event["event_id"],
            created_at=str(decision_ts),
        )
        # Submit to broker AFTER all gates pass.
        submit_result = self._broker.submit(parent)
        result.parent_orders.append(parent)

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

        # §15.1 P0: broker_reject emits canonical decision.
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

        # Submit succeeded → emit ACCEPTED.
        result.decisions.append(build_accepted_entry_decision(
            candidate_event=candidate_event,
            decision_ts=decision_ts,
            entry_trigger=plan.order_style,
            quote=quote.__dict__,
            risk_snapshot=risk_snapshot_dict,
            order_plan=order_plan_dict,
        ))

        # Add the position (entry price = quote.ask for buy marketable-limit).
        ts_pts = candidate_event.get("scan_timestamp", str(decision_ts))
        entry_date = _dt.datetime.fromisoformat(ts_pts.replace("Z", "+00:00")).date() if isinstance(ts_pts, str) else _dt.date.today()
        position = Position(
            symbol=candidate_event["symbol"],
            entry_date=entry_date,
            entry_price=quote.ask,
            qty=qty,
            stop_pct=plan.stop_pct,
            target_pct=plan.target_pct,
            max_hold_days=plan.max_hold_days,
            candidate_event_id=candidate_event["event_id"],
            current_price=quote.ask,
        )
        self._portfolio.add_position(position)
        result.new_positions.append(position)
        return result
