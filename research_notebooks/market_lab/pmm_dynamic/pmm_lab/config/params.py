"""Configuration dataclasses for PMM Lab."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class FeeConfig:
    """Fee configuration for a connector/pair."""
    maker_fee: float
    taker_fee: float


@dataclass(frozen=True)
class PairRules:
    """Exchange rules for a specific trading pair."""
    price_tick: float
    amount_step: float
    min_notional_quote: float
    min_order_size_base: float = 0.0
    max_order_size_base: Optional[float] = None
    fees: FeeConfig = field(default_factory=lambda: FeeConfig(0.001, 0.002))


@dataclass(frozen=True)
class DataQuery:
    """Parameters for a candle data query."""
    connector: str
    trading_pair: str
    interval: str
    start_ts: Optional[int] = None   # seconds since epoch, inclusive
    end_ts: Optional[int] = None     # seconds since epoch, inclusive


@dataclass(frozen=True)
class AuditResult:
    """Result of a dataset quality audit."""
    total_rows: int
    first_timestamp: int
    last_timestamp: int
    expected_rows: int
    missing_rows: int
    duplicate_count: int
    null_counts: dict              # field_name -> count
    ohlc_violations: int
    ohlc_violation_details: dict   # violation_type -> count
    volume_zero_count: int
    volume_zero_fraction: float
    forward_fill_count: int
    forward_fill_fraction: float
    dataset_hash: str
    interval_seconds: int
    gap_histogram: dict            # gap_size_seconds -> count
    longest_gap_seconds: int
    passed_strict: bool
    failure_reasons: list          # list of strings explaining failures
    # Source-declared vs heuristic forward-fill split
    source_synthetic_count: int = 0
    source_synthetic_fraction: float = 0.0
    heuristic_forward_fill_count: int = 0
    unexpected_forward_fill_count: int = 0
    unexpected_forward_fill_fraction: float = 0.0
