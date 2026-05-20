"""Developer tooling — NOT for performance reporting.

Contains the v2 archive's preserved single-file backtester (``smoke_backtester``),
tagged ``performance_use="prohibited"`` per [Report §9.1].
"""
from .smoke_backtester import run_smoke_backtest, SMOKE_ARTIFACT_TAGS

__all__ = ["run_smoke_backtest", "SMOKE_ARTIFACT_TAGS"]
