"""bowaka_v2 simulator — event-driven historical backtester."""
from .backtester import BacktestResult, run_backtest
from .portfolio import Portfolio, PortfolioState, Position, new_position_id
from .orders import ChildOrder, OrderPlan, ParentOrder, OrderStatus, OrderSide
from .quote_model import QuoteSnapshot, get_quote, synthesize_quote
from .cost_model import COST_STRESS_LEVELS, slippage_bps
from .exits import ExitEvent, evaluate_exits, trading_days_since
from .ambiguity import resolve_same_bar
from .risk_gates import RiskGateResult, evaluate_risk_gates
from .strategy_consumer import StrategyConsumer
from .broker import SimulatedBroker, BrokerSubmitResult
from .fills import FillResult, simulate_fill

__all__ = [
    "run_backtest", "BacktestResult",
    "Portfolio", "PortfolioState", "Position", "new_position_id",
    "ChildOrder", "OrderPlan", "ParentOrder", "OrderStatus", "OrderSide",
    "QuoteSnapshot", "get_quote", "synthesize_quote",
    "COST_STRESS_LEVELS", "slippage_bps",
    "ExitEvent", "evaluate_exits", "trading_days_since",
    "resolve_same_bar",
    "RiskGateResult", "evaluate_risk_gates",
    "StrategyConsumer",
    "SimulatedBroker", "BrokerSubmitResult",
    "FillResult", "simulate_fill",
]
