"""bowaka_v2 simulator — event-driven historical backtester."""
from .backtester import BacktestResult, run_backtest
from .portfolio import Portfolio, PortfolioState, Position, new_position_id
from .orders import ChildOrder, OrderPlan, ParentOrder, OrderStatus, OrderSide
from .quote_model import (
    QuoteResolution,
    QuoteSnapshot,
    get_quote,
    resolve_quote,
    synthesize_calibrated_quote,
    synthesize_quote,
    synthesize_zero_spread_quote,
)
from .cost_model import COST_STRESS_LEVELS, slippage_bps
from .exits import (
    ExitEvent,
    FadeTelemetry,
    evaluate_exits,
    max_hold_exit_session,
    trading_days_since,
    walk_lot_exit,
)
from .ambiguity import resolve_same_bar
from .risk_gates import RiskGateResult, evaluate_risk_gates
from .strategy_consumer import StrategyConsumer
from .broker import SimulatedBroker, BrokerSubmitResult
from .fills import (
    FillResult,
    simulate_fill,
    simulate_market_fill,
    simulate_marketable_limit_fill,
    stress_fill_rate_cap,
    stress_slippage_multiplier,
)

__all__ = [
    "run_backtest", "BacktestResult",
    "Portfolio", "PortfolioState", "Position", "new_position_id",
    "ChildOrder", "OrderPlan", "ParentOrder", "OrderStatus", "OrderSide",
    "QuoteSnapshot", "QuoteResolution", "get_quote", "resolve_quote",
    "synthesize_quote", "synthesize_zero_spread_quote", "synthesize_calibrated_quote",
    "COST_STRESS_LEVELS", "slippage_bps",
    "ExitEvent", "FadeTelemetry", "evaluate_exits", "trading_days_since",
    "walk_lot_exit", "max_hold_exit_session",
    "resolve_same_bar",
    "RiskGateResult", "evaluate_risk_gates",
    "StrategyConsumer",
    "SimulatedBroker", "BrokerSubmitResult",
    "FillResult", "simulate_fill", "simulate_market_fill",
    "simulate_marketable_limit_fill",
    "stress_slippage_multiplier", "stress_fill_rate_cap",
]
