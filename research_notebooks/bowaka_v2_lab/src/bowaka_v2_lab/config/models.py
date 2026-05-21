"""Pydantic v2 models for bowaka_v2_lab configs.

Each section maps 1:1 to a top-level key in the YAML config (see
``loader.ALLOWED_TOP_LEVEL_KEYS``). Models enforce hard invariants:

- ``strategy_id`` must equal ``"bowaka_v2"``.
- ``market_data.feed`` must be one of ``"iex"`` / ``"sip"``.
- ``execution.max_spread_bps`` must be positive.
- ``risk.max_gross_exposure_pct`` and ``risk.daily_loss_pct`` are 0.0–1.0.
"""
from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class MarketDataConfig(_StrictBase):
    feed: Literal["iex", "sip"]
    allow_non_sip_for_research_only: bool = True
    max_bar_age_seconds: int = Field(default=90, ge=1)
    minute_bar_source: str = "alpaca"
    daily_bar_source: str = "alpaca"
    quote_source: str = "alpaca"
    assume_naive_timezone: bool = False
    # Optional override of the shared market-data lake root. None -> resolve
    # MARKET_DATA_ROOT / the in-repo default. NOT routed through BowakaV2Paths,
    # so assert_strategy_isolation() keeps governing only lab-owned paths.
    shared_root: Optional[str] = None


class SessionConfig(_StrictBase):
    calendar: str = "XNYS"
    scan_window_local_start: str = "09:30"
    scan_window_local_end: str = "15:55"
    scan_interval_seconds: int = Field(default=60, ge=1)


class UniverseConfig(_StrictBase):
    asset_classes: list[str] = Field(default_factory=lambda: ["operating_equity"])
    min_price: float = 1.0
    max_price: float = 1000.0
    min_adv_dollars: float = 1_000_000
    exclude_pattern_class: bool = True
    symbols: Optional[list[str]] = None


class ScannerConfig(_StrictBase):
    max_candidates_per_scan: int = 10
    max_entries_per_scan: int = 3
    min_signal_strength: float = 0.5


class SignalsConfig(_StrictBase):
    allow_unknown_instrument_class_for_research: bool = False


class ExecutionConfig(_StrictBase):
    order_type: Literal["marketable_limit", "market", "limit"] = "marketable_limit"
    limit_offset_bps: int = 5
    max_quote_age_seconds: int = Field(default=5, ge=0)
    max_spread_bps: int = Field(default=50, ge=1)


class SizingConfig(_StrictBase):
    method: str = "fixed_dollar"
    dollars_per_position: float = 5000
    max_position_dollars: float = 25_000


class AdvTierCap(_StrictBase):
    min_adv_dollars: float
    max_position_dollars: float


class RiskConfig(_StrictBase):
    max_concurrent_positions: int = Field(default=5, ge=1)
    max_total_entries_per_day: int = Field(default=12, ge=1)
    max_gross_exposure_pct: float = Field(default=0.50, ge=0.0, le=1.0)
    daily_loss_pct: float = Field(default=0.02, ge=0.0, le=1.0)
    strategy_slice_loss_pct: float = Field(default=0.05, ge=0.0, le=1.0)
    max_stopouts_per_day: int = Field(default=4, ge=0)
    stop_trading_after_consecutive_stopouts: int = Field(default=3, ge=0)
    adv_tier_caps: list[AdvTierCap] = Field(default_factory=list)


class ExitsConfig(_StrictBase):
    stop_loss_pct: float = 0.02
    take_profit_pct: float = 0.06
    max_hold_days: int = 5
    signal_fade_mode: Literal["telemetry_only", "active"] = "telemetry_only"


class BacktestConfig(_StrictBase):
    start_date: str
    end_date: str
    cost_stress: Literal["base", "conservative", "severe"] = "base"
    entry_delay_minutes: int = 0


class ArtifactsConfig(_StrictBase):
    write_parquet: bool = True
    write_jsonl: bool = True


class RunConfig(_StrictBase):
    kind: Literal["backtest", "replay", "smoke", "optuna", "reconcile"] = "backtest"
    seed: int = 1337


class PathsConfig(_StrictBase):
    lab_root: str
    data_root: str
    artifact_root: str


class OptunaConfig(_StrictBase):
    storage: Optional[str] = None
    n_trials: int = 50
    n_jobs: int = 1
    study_name_prefix: str = "bowaka_v2"
    cost_stress: Literal["base", "conservative", "severe"] = "conservative"
    walkforward: dict[str, Any] = Field(default_factory=dict)
    search_space_overrides: dict[str, Any] = Field(default_factory=dict)


class ReconcileConfig(_StrictBase):
    paper_logs_root: Optional[str] = None
    symbol_window_seconds: int = 120


class PromotionConfig(_StrictBase):
    target_tier: Literal["research_only", "backtesting_only", "paper_candidate", "live_candidate"] = "backtesting_only"


class BowakaV2Config(_StrictBase):
    strategy_id: Literal["bowaka_v2"]
    strategy_version: str = "0.1.0"
    market_data: MarketDataConfig
    session: SessionConfig = Field(default_factory=SessionConfig)
    universe: UniverseConfig = Field(default_factory=UniverseConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    signals: SignalsConfig = Field(default_factory=SignalsConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    sizing: SizingConfig = Field(default_factory=SizingConfig)
    risk: RiskConfig = Field(default_factory=RiskConfig)
    exits: ExitsConfig = Field(default_factory=ExitsConfig)
    backtest: Optional[BacktestConfig] = None
    artifacts: ArtifactsConfig = Field(default_factory=ArtifactsConfig)
    run: RunConfig = Field(default_factory=RunConfig)
    paths: PathsConfig
    optuna: Optional[OptunaConfig] = None
    reconcile: Optional[ReconcileConfig] = None
    promotion: Optional[PromotionConfig] = None

    # Source-of-truth metadata propagated by ``loader.load_config``. Not part of the
    # public API but tolerated for downstream introspection.
    source_path: Optional[str] = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def _accept_source_path_alias(cls, data: Any) -> Any:
        if isinstance(data, dict) and "_source_path" in data:
            data = dict(data)
            data["source_path"] = data.pop("_source_path")
        return data
