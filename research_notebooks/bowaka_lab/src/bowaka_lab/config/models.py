"""Pydantic v2 models for Bowaka Lab configuration.

These mirror `[Report §B.3, §17.1]`. Field defaults match the recommended
`bowaka_backtest_iex_exploratory.yml` defaults so a partial config still loads.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    """Base with extras forbidden to surface typos at load time."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class ProjectConfig(StrictModel):
    name: str = "bowaka_lab"
    mode: Literal["research", "validation", "live_candidate"] = "research"
    run_label: str = "bowaka_iex_exploratory_v1"
    fidelity_mode: Literal["exact", "research"] = "research"


class StorageConfig(StrictModel):
    data_root: str | None = None
    output_root: str | None = None
    mongo_uri: str | None = None
    mongo_database: str = "quants_lab"
    write_mongo: bool = True
    write_parquet: bool = True


class DataConfig(StrictModel):
    vendor: Literal["alpaca"] = "alpaca"
    feed: str = "iex"
    adjustment: Literal["raw", "split", "dividend", "all"] = "raw"
    allow_feed_fallback: bool = False
    fallback_feed: str = "iex"
    rate_limit_requests_per_minute: int = Field(default=180, gt=0, le=2000)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def _check_dates(self) -> "DataConfig":
        if self.start_date > self.end_date:
            raise ValueError(f"start_date {self.start_date} > end_date {self.end_date}")
        return self


class CalendarConfig(StrictModel):
    exchange: str = "XNYS"
    timezone: str = "America/New_York"
    session: Literal["regular", "extended"] = "regular"


class UniverseConfig(StrictModel):
    mode: Literal["alpaca_current_assets", "point_in_time"] = "alpaca_current_assets"
    allowed_exchanges: list[str] = Field(default_factory=lambda: ["NASDAQ", "NYSE", "ARCA", "AMEX", "BATS"])
    exclude_otc: bool = True
    exclude_leveraged_etp: bool = True
    exclude_inverse_etp: bool = True
    exclude_etn: bool = True
    ticker_blocklist: list[str] = Field(default_factory=list)


class ScoreConfig(StrictModel):
    bounded: bool = False
    rvol_score_cap: float = 5.0
    range_score_cap: float = 2.5
    ema_distance_score_cap: float = 0.40
    ema_slope_score_cap: float = 0.25
    gap_penalty_above: float = 0.25


class PrefilterConfig(StrictModel):
    lookback_days: int = Field(default=20, ge=2, le=252)
    atr_days: int = Field(default=14, ge=2, le=252)
    ema_days: int = Field(default=10, ge=2, le=252)
    ema_slope_lookback: int = Field(default=3, ge=1, le=64)

    price_min: float = Field(default=1.0, ge=0)
    price_max: float = Field(default=20.0, gt=0)

    avg_dollar_volume_min: float | None = 200_000
    avg_dollar_volume_max: float | None = None

    rvol_min: float | None = 1.5
    atr_pct_min: float | None = 0.06
    range_expansion_min: float | None = 1.25
    close_location_min: float | None = 0.60
    ema_distance_min: float | None = 0.0
    ema_slope_min: float | None = 0.0

    rvol_max: float | None = None
    range_expansion_max: float | None = None
    gap_pct_max: float | None = None

    score: ScoreConfig = Field(default_factory=ScoreConfig)

    @model_validator(mode="after")
    def _check_price_range(self) -> "PrefilterConfig":
        if self.price_max <= self.price_min:
            raise ValueError(f"price_max {self.price_max} must exceed price_min {self.price_min}")
        return self


class EntryPriceBand(StrictModel):
    max_pct_above_close: float = 0.15
    min_pct_below_close: float = -0.02


class IntradayConfirmationConfig(StrictModel):
    """Source-aligned intraday-confirmation gate. Disabled by default so
    research-mode configs that don't load quotes keep working unchanged."""

    enabled: bool = False
    window_minutes: int = Field(default=15, ge=0, le=120)
    max_spread_pct: float = Field(default=0.01, ge=0, lt=1.0)
    max_quote_age_seconds: float = Field(default=15.0, ge=0, le=300.0)
    price_band: EntryPriceBand = Field(default_factory=EntryPriceBand)


class EntryConfig(StrictModel):
    default_rule: str = "fixed_time_0945"
    fixed_times: list[str] = Field(default_factory=lambda: ["09:35", "09:40", "09:45", "10:00"])
    fill_model: str = "next_minute_open_plus_slippage"
    slippage_bps: float = Field(default=25.0, ge=0)
    use_quotes_if_available: bool = True
    price_band: EntryPriceBand = Field(default_factory=EntryPriceBand)
    intraday_confirmation: IntradayConfirmationConfig = Field(
        default_factory=IntradayConfirmationConfig
    )


class ExitConfig(StrictModel):
    stop_pct: float = Field(default=0.08, gt=0, lt=1.0)
    target_pct: float = Field(default=0.15, gt=0, lt=10.0)
    max_hold_days: int = Field(default=3, ge=1, le=60)
    ambiguous_bar_policy: Literal["stop_first", "target_first", "skip"] = "stop_first"
    stop_gap_policy: Literal["next_available_open", "stop_price"] = "next_available_open"
    target_fill_policy: Literal["limit_touch", "next_minute_open"] = "limit_touch"
    stop_slippage_pct: float = Field(default=0.0, ge=0, lt=0.20)


class SignalFadeConfig(StrictModel):
    enabled: bool = True
    rth_eval_time: str = "15:45"
    after_close_eval_time: str = "16:05"
    after_close_action: Literal["log_only", "exit"] = "log_only"
    execute_threshold: int = Field(default=8, ge=0, le=20)
    shadow_thresholds: list[int] = Field(default_factory=lambda: [4, 5, 6, 7, 8, 9])

    @field_validator("rth_eval_time", "after_close_eval_time")
    @classmethod
    def _hhmm(cls, v: str) -> str:
        # naive HH:MM check; full parsing happens in time utils
        parts = v.split(":")
        if len(parts) != 2 or not all(p.isdigit() for p in parts):
            raise ValueError(f"expected HH:MM, got {v!r}")
        hh, mm = int(parts[0]), int(parts[1])
        if not (0 <= hh <= 23 and 0 <= mm <= 59):
            raise ValueError(f"invalid time {v!r}")
        return v


class StopManagerRule(StrictModel):
    mfe_min: float = Field(ge=0)
    stop_at: float


class StopManagerShadowConfig(StrictModel):
    enabled: bool = True
    rules: list[StopManagerRule] = Field(
        default_factory=lambda: [
            StopManagerRule(mfe_min=0.05, stop_at=0.00),
            StopManagerRule(mfe_min=0.08, stop_at=0.03),
            StopManagerRule(mfe_min=0.12, stop_at=0.06),
        ]
    )


class PortfolioConfig(StrictModel):
    mode: Literal["paper_data_collection", "validation", "live_candidate"] = "paper_data_collection"
    sizing_mode: Literal["equal_slice", "risk_per_trade"] = "equal_slice"
    per_trade_notional: float = Field(default=5_000.0, gt=0)
    max_concurrent_positions: int = Field(default=18, ge=1, le=500)
    max_total_entries_per_day: int | None = 25
    max_gross_exposure_pct: float | None = 2.0
    daily_loss_pct: float | None = None
    max_stopouts_per_day: int | None = None
    stop_trading_after_consecutive_stopouts: int | None = None


class ShadowRiskConfig(StrictModel):
    daily_loss_thresholds: list[float] = Field(default_factory=lambda: [0.01, 0.03, 0.05, 0.10])
    max_gross_exposure_thresholds: list[float] = Field(default_factory=lambda: [0.40, 0.80, 1.00, 2.00])
    max_entries_thresholds: list[int] = Field(default_factory=lambda: [4, 10, 15, 25])


class AdvTierCap(StrictModel):
    max_adv_dollars: float | None = None
    max_position_as_adv_frac: float | None = None
    reject_if_below: bool = False


class RealismConfig(StrictModel):
    max_position_as_adv_frac_enabled: bool = True
    max_position_as_adv_frac: float = Field(default=0.03, gt=0, lt=1.0)
    adv_tier_caps: list[AdvTierCap] = Field(default_factory=list)


class CounterfactualConfig(StrictModel):
    include_rejected_candidates: bool = True
    entry_rules: list[str] = Field(
        default_factory=lambda: ["fixed_time_0935", "fixed_time_0940", "fixed_time_0945", "fixed_time_1000"]
    )
    stop_pct: list[float] = Field(default_factory=lambda: [0.05, 0.06, 0.08, 0.10])
    target_pct: list[float] = Field(default_factory=lambda: [0.08, 0.10, 0.12, 0.15, 0.20])
    max_hold_days: list[int] = Field(default_factory=lambda: [1, 2, 3])
    signal_fade_thresholds: list[int | None] = Field(default_factory=lambda: [None, 6, 7, 8, 9])
    stop_manager_models: list[str] = Field(default_factory=lambda: ["none", "breakeven_after_5pct", "mfe_ladder_v1"])


class OutputConfig(StrictModel):
    write_candidates: bool = True
    write_trades: bool = True
    write_counterfactuals: bool = True
    write_daily_summary: bool = True
    write_report_markdown: bool = True


class BowakaBacktestConfig(StrictModel):
    """Top-level Bowaka backtest configuration."""

    project: ProjectConfig = Field(default_factory=ProjectConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    data: DataConfig
    calendar: CalendarConfig = Field(default_factory=CalendarConfig)
    universe: UniverseConfig = Field(default_factory=UniverseConfig)
    prefilter: PrefilterConfig = Field(default_factory=PrefilterConfig)
    entry: EntryConfig = Field(default_factory=EntryConfig)
    exits: ExitConfig = Field(default_factory=ExitConfig)
    signal_fade: SignalFadeConfig = Field(default_factory=SignalFadeConfig)
    stop_manager_shadow: StopManagerShadowConfig = Field(default_factory=StopManagerShadowConfig)
    portfolio: PortfolioConfig = Field(default_factory=PortfolioConfig)
    shadow_risk: ShadowRiskConfig = Field(default_factory=ShadowRiskConfig)
    realism: RealismConfig = Field(default_factory=RealismConfig)
    counterfactuals: CounterfactualConfig = Field(default_factory=CounterfactualConfig)
    outputs: OutputConfig = Field(default_factory=OutputConfig)

    def canonical_dict(self) -> dict[str, Any]:
        """Return a dict suitable for stable hashing (sorted, JSON-friendly)."""
        return self.model_dump(mode="json")

    @property
    def is_exact_mode(self) -> bool:
        return self.project.fidelity_mode == "exact"
