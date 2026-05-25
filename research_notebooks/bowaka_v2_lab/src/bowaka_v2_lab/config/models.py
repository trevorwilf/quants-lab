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

from pydantic import AliasChoices, BaseModel, Field, ConfigDict, field_validator, model_validator


class _StrictBase(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


# --------------------------------------------------------------------------
# Simulation-mode contract (realism remediation Phase 0).
# --------------------------------------------------------------------------
#: Per-mode defaults for the four behavior-coupling policy fields. A field left
#: unset (``None``) in the YAML is resolved from the run's ``mode`` via these
#: tables, so a config either inherits the mode's behavior wholesale or
#: overrides a single axis explicitly.
_SIMULATION_MODE_DEFAULTS: dict[str, dict[str, str]] = {
    "current_code_parity": {
        "intraday_window_policy": "scanner_start_to_scan",
        "accepted_event_sequencing": "pre_submit",
        "unknown_instrument_class_policy": "fail_open",
        "quote_fallback_policy": "zero_spread",
    },
    "intended_realism": {
        "intraday_window_policy": "regular_open_to_scan",
        "accepted_event_sequencing": "post_submit",
        "unknown_instrument_class_policy": "fail_closed",
        "quote_fallback_policy": "require_real",
    },
    "smoke_fixture": {
        "intraday_window_policy": "regular_open_to_scan",
        "accepted_event_sequencing": "pre_submit",
        "unknown_instrument_class_policy": "fail_open",
        "quote_fallback_policy": "synthetic_calibrated",
    },
}


class SimulationConfig(_StrictBase):
    """Declares *which strategy* the simulator reproduces.

    ``mode`` selects one of three contracts:

    - ``current_code_parity`` — reproduce the *live code as written* (warts and
      all) so the lab can reconcile a run against live Bowaka v2.
    - ``intended_realism`` — model the *intended* strategy (audit §16 fixes).
    - ``smoke_fixture`` — deterministic synthetic data for plumbing tests; never
      a research- or promotion-grade run.

    The four policy fields default to ``None`` and are resolved from ``mode``
    (see :data:`_SIMULATION_MODE_DEFAULTS`) by a post-validator, so after
    validation every field is concrete and can be written to the run manifest.
    """

    mode: Literal["current_code_parity", "intended_realism", "smoke_fixture"] = "smoke_fixture"
    allow_research_relaxed: bool = False
    intraday_window_policy: Optional[
        Literal["scanner_start_to_scan", "regular_open_to_scan", "extended_hours_to_scan"]
    ] = None
    accepted_event_sequencing: Optional[Literal["pre_submit", "post_submit"]] = None
    unknown_instrument_class_policy: Optional[Literal["fail_open", "fail_closed"]] = None
    quote_fallback_policy: Optional[
        Literal["zero_spread", "synthetic_calibrated", "require_real"]
    ] = None
    #: Realism Phase 6: the minimum fraction (percent) of (symbol, scan_ts) pairs
    #: that must be backed by a *historical* quote for an ``intended_realism`` run
    #: to pass the finalize-step quote-coverage gate. Below this, the run fails.
    #: Ignored in ``current_code_parity`` / ``smoke_fixture`` modes.
    min_quote_coverage_pct: float = Field(default=95.0, ge=0.0, le=100.0)
    #: Realism Phase 7: when a single minute bar touches BOTH the stop and the
    #: target the order in which an OCO bracket would have filled is genuinely
    #: ambiguous (the minute bar has no sub-minute path). This axis resolves it:
    #:   - ``conservative`` (realism default) — assume the STOP filled first.
    #:   - ``optimistic`` — assume the TARGET filled first.
    #:   - ``random_with_seed`` — a deterministic coin flip seeded on
    #:     ``run.seed`` + the lot identity, so two runs of the same config agree.
    same_minute_resolution: Literal[
        "conservative", "optimistic", "random_with_seed"
    ] = "conservative"
    #: Realism remediation 2 Phase 4 — decoupled poll cadences (audit P1-009).
    #: The live strategy has ``loop_interval_seconds: 5`` (the strategy poll
    #: loop) and ``scan_interval_seconds: 60`` (the scanner). These four fields
    #: let a config drive PROTECTION_CHECK / FILL_POLL / TIME_STOP_CHECK at
    #: independent cadences from the SCAN cadence. ``None`` (the default) falls
    #: back to :class:`sim.event_loop.CadenceConfig`'s field defaults, which in
    #: turn read ``session.loop_interval_seconds`` for the protection/fill poll
    #: and ``session.scan_interval_seconds`` for the scan.
    protection_poll_interval_seconds: Optional[int] = Field(default=None, ge=1)
    fill_poll_interval_seconds: Optional[int] = Field(default=None, ge=1)
    time_stop_check_interval_seconds: Optional[int] = Field(default=None, ge=1)
    #: Realism remediation 2 Phase 6 (audit P0-007) — optional OCO / protected-
    #: position lifecycle stress injection used by the protection-acceptance
    #: tests. ``"none"`` (default) is the live happy path; other values
    #: simulate attach failures (``"oco_attach_fail_once"`` /
    #: ``"oco_attach_fail_always"``) or a delayed / halted attach
    #: (``"delayed_attach"`` / ``"halt_during_unprotected"``). The resolved
    #: :class:`sim.protection.ProtectionConfig` consumes the value via
    #: :meth:`ProtectionConfig.from_cfg`.
    protection_stress: Optional[
        Literal[
            "none",
            "oco_attach_fail_once",
            "oco_attach_fail_always",
            "delayed_attach",
            "halt_during_unprotected",
        ]
    ] = None

    @model_validator(mode="after")
    def _resolve_mode_coupled_defaults(self) -> "SimulationConfig":
        """Fill any unset policy field from the mode-coupled default table."""
        defaults = _SIMULATION_MODE_DEFAULTS[self.mode]
        for field_name, default_value in defaults.items():
            if getattr(self, field_name) is None:
                setattr(self, field_name, default_value)
        return self


class MarketDataConfig(_StrictBase):
    feed: Literal["iex", "sip"]
    allow_non_sip_for_research_only: bool = True
    max_bar_age_seconds: int = Field(default=90, ge=1)
    minute_bar_source: str = "alpaca"
    daily_bar_source: str = "alpaca"
    quote_source: str = "alpaca"
    assume_naive_timezone: bool = False
    # Realism Phase 2 / remediation-2 Phase 1: when True, a run whose lake
    # declares ``adjustment: raw`` (corporate actions not applied to daily bars)
    # fails the data-quality gate. The live contract sets this ``true``
    # (``data.require_adjusted_daily_bars``). The field defaults to ``None`` so a
    # ``BowakaV2Config`` cross-field validator can require it to be set
    # *explicitly* for ``intended_realism`` / ``current_code_parity`` configs
    # (an unset value there is a config defect); ``smoke_fixture`` configs keep
    # the historical ``False`` default. After validation it is always concrete.
    require_adjusted_daily_bars: Optional[bool] = None
    # Realism remediation-2 Phase 1: the live contract requires split-adjusted
    # daily bars (``data.require_split_adjustment``). When True a run whose lake
    # has not applied split adjustments fails the data-quality gate.
    require_split_adjustment: bool = False
    # Realism remediation-2 Phase 1: maximum quote age (seconds) tolerated by the
    # quote gate; mirrors the live contract ``data.max_quote_age_seconds``.
    max_quote_age_seconds: int = Field(default=15, ge=0)
    # Optional override of the shared market-data lake root. None -> resolve
    # MARKET_DATA_ROOT / the in-repo default. NOT routed through BowakaV2Paths,
    # so assert_strategy_isolation() keeps governing only lab-owned paths.
    shared_root: Optional[str] = None


class SessionConfig(_StrictBase):
    """Session window. Live key names; legacy ``scan_window_local_*`` keys are
    accepted as aliases so pre-remediation configs still parse."""

    calendar: str = "XNYS"
    timezone: str = "America/New_York"
    # 09:30 regular open. Legacy alias: scan_window_local_start.
    start: str = Field(default="09:30", validation_alias=AliasChoices("start", "scan_window_local_start"))
    # 15:55 regular-session cutoff. Legacy alias: scan_window_local_end.
    end: str = Field(default="15:55", validation_alias=AliasChoices("end", "scan_window_local_end"))
    scanner_start: str = "09:45"
    scanner_end: str = "15:30"
    loop_interval_seconds: int = Field(default=5, ge=1)
    scan_interval_seconds: int = Field(default=60, ge=1)


class UniverseConfig(_StrictBase):
    """Universe gate config — defaults match the live contract.

    Audit 2026-05-23 §P2-001: pre-remediation ``max_price=1000.0`` and
    ``min_adv_dollars=1_000_000`` were stale (the live contract gates penny
    stocks at $1-20 with ADV >= $250k). Defaults are now the live values.
    """

    asset_classes: list[str] = Field(default_factory=lambda: ["operating_equity"])
    min_price: float = 1.0
    max_price: float = 20.0
    min_adv_dollars: float = 250_000.0
    exclude_pattern_class: bool = True
    symbols: Optional[list[str]] = None


class ScannerConfig(_StrictBase):
    """Live ``scanner:`` block — all keys from the actual contract.

    Audit 2026-05-23 §P1-003 — every live ``scanner:`` key is exposed at the
    lab schema level (was just three: max_candidates / max_entries /
    min_signal_strength). The other keys (cadence, expiry, per-symbol caps,
    baseline gating) were buried in code defaults; without them the generated
    Optuna configs hid the live contract.

    ``same_symbol_entries_per_day`` lives here (not on ``RiskConfig``) — the
    live contract treats it as a scanner / candidate-gating field. A config
    that sets it under both ``scanner`` and ``risk`` is a parity error and the
    config loader raises :class:`ConfigParityError`.
    """

    max_candidates_per_scan: int = 25
    max_entries_per_scan: int = 3
    min_signal_strength: float = 0.0
    # Audit 2026-05-23 §P1-003 — the rest of the live scanner block.
    enabled: bool = True
    debug_gate_dump: bool = False
    scan_interval_seconds: int = 60
    full_universe_refresh_interval_minutes: int = 5
    in_play_refresh_interval_seconds: int = 60
    signal_expiry_seconds: int = 600
    same_symbol_entries_per_day: int = 1
    symbol_cooldown_minutes: int = 390
    require_prior_daily_baseline: bool = True
    require_fresh_intraday_bar: bool = True


#: Live signal gates that must be set when simulation.mode is a real mode and
#: allow_research_relaxed is False. All gates the live strategy actually uses —
#: i.e. every threshold except avg_dollar_volume_max (null in the live config).
_REALISM_REQUIRED_SIGNAL_GATES: tuple[str, ...] = (
    "rvol_so_far_min",
    "projected_full_day_rvol_min",
    "prior_atr_pct_min",
    "range_expansion_so_far_min",
    "close_location_so_far_min",
    "ema_distance_min",
    "ema_slope_min",
    "price_min",
    "price_max",
    "avg_dollar_volume_min",
    "rvol_so_far_max",
    "projected_full_day_rvol_max",
    "range_expansion_so_far_max",
    "gap_pct_max",
    "current_return_pct_max",
)


class SignalsConfig(_StrictBase):
    """v2 signal-gate thresholds.

    Each threshold is ``Optional[float]`` — ``None`` disables that gate, per the
    live ``apply_v2_gates`` contract. The cross-field validator on
    :class:`BowakaV2Config` requires the full set in realism / parity modes.
    """

    allow_unknown_instrument_class_for_research: bool = False
    # Lower-bound gates.
    rvol_so_far_min: Optional[float] = None
    projected_full_day_rvol_min: Optional[float] = None
    prior_atr_pct_min: Optional[float] = None
    range_expansion_so_far_min: Optional[float] = None
    close_location_so_far_min: Optional[float] = None
    ema_distance_min: Optional[float] = None
    ema_slope_min: Optional[float] = None
    price_min: Optional[float] = None
    avg_dollar_volume_min: Optional[float] = None
    # Upper-bound / exhaustion gates.
    price_max: Optional[float] = None
    avg_dollar_volume_max: Optional[float] = None
    rvol_so_far_max: Optional[float] = None
    projected_full_day_rvol_max: Optional[float] = None
    range_expansion_so_far_max: Optional[float] = None
    gap_pct_max: Optional[float] = None
    current_return_pct_max: Optional[float] = None


class ExecutionConfig(_StrictBase):
    order_type: Literal["marketable_limit", "market", "limit"] = "marketable_limit"
    limit_offset_bps: int = 5
    max_quote_age_seconds: int = Field(default=5, ge=0)
    max_spread_bps: int = Field(default=50, ge=1)


class SizingConfig(_StrictBase):
    """Position sizing.

    ``equal_slice`` (default) splits a fixed bankroll across
    ``max_concurrent_positions`` slots — the live strategy's model. ``fixed_dollar``
    uses ``dollars_per_position`` and is retained for back-compat.
    """

    sizing_mode: Literal["equal_slice", "fixed_dollar"] = "equal_slice"
    bankroll_fixed_dollars: float = Field(default=90_000.0, gt=0.0)
    max_concurrent_positions: int = Field(default=18, ge=1)
    equal_slice_bankroll_fraction: float = Field(default=0.80, gt=0.0, le=1.0)
    target_risk_dollars: float = Field(default=200.0, ge=0.0)
    min_order_notional: float = Field(default=500.0, ge=0.0)
    max_per_trade_dollars: Optional[float] = None
    # Back-compat — consulted only when sizing_mode == "fixed_dollar".
    dollars_per_position: Optional[float] = None
    max_position_dollars: Optional[float] = None
    # Deprecated legacy key; tolerated so pre-remediation configs still parse.
    method: Optional[str] = None


class AdvTierCap(_StrictBase):
    """One ADV tier (live schema).

    ``adv_tier_caps`` is an ordered list; the first tier whose ``max_adv_dollars``
    is ``None`` or >= the candidate's ADV wins. ``reject_if_below: true`` rejects;
    otherwise the position notional is capped at ``adv * max_position_as_adv_frac``.
    """

    max_adv_dollars: Optional[float] = None
    reject_if_below: bool = False
    max_position_as_adv_frac: Optional[float] = None


class RiskConfig(_StrictBase):
    # Live `_risk_gates` reads max_concurrent_positions from `sizing`; kept here
    # Optional only so pre-remediation configs still parse (Phase 5 wires the
    # read from sizing).
    max_concurrent_positions: Optional[int] = Field(default=None, ge=1)
    max_total_entries_per_day: int = Field(default=12, ge=1)
    max_gross_exposure_pct: float = Field(default=0.50, ge=0.0, le=1.0)
    daily_loss_pct: float = Field(default=0.02, ge=0.0, le=1.0)
    strategy_slice_loss_pct: float = Field(default=0.05, ge=0.0, le=1.0)
    max_stopouts_per_day: int = Field(default=4, ge=0)
    stop_trading_after_consecutive_stopouts: int = Field(default=3, ge=0)
    # One entry per symbol per day; this many concurrent lots per symbol.
    max_lots_per_symbol: int = Field(default=1, ge=1)
    # Ordered tiered ADV policy. Empty -> fall back to max_position_as_adv_frac.
    adv_tier_caps: list[AdvTierCap] = Field(default_factory=list)
    max_position_as_adv_frac: Optional[float] = None
    # Shadow-risk mirrors (stricter "would have blocked" controls); Phase 5 wires.
    shadow: Optional[dict[str, Any]] = None


class ExitsConfig(_StrictBase):
    """Exit policy.

    ``stop_pct`` / ``target_pct`` are the canonical (live) names;
    ``stop_loss_pct`` / ``take_profit_pct`` are accepted as aliases so
    pre-remediation configs and tests still parse.
    """

    stop_pct: float = Field(
        default=0.02, validation_alias=AliasChoices("stop_pct", "stop_loss_pct")
    )
    target_pct: float = Field(
        default=0.06, validation_alias=AliasChoices("target_pct", "take_profit_pct")
    )
    max_hold_days: int = Field(default=5, ge=1)
    signal_fade_mode: Literal["telemetry_only", "active"] = "telemetry_only"
    # Live exit substructures (Phase 7 promotes these to typed sub-models).
    time_stop: Optional[dict[str, Any]] = None
    signal_fade: Optional[dict[str, Any]] = None


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
    n_trials: int = Field(default=50, ge=1)
    n_jobs: int = 1
    #: Random-sampling trials before TPE-guided search begins. None -> sampler default.
    n_startup_trials: Optional[int] = None
    study_name_prefix: str = "bowaka_v2"
    cost_stress: Literal["base", "conservative", "severe"] = "conservative"
    #: Speedup report §5.1 / §11.2 Phase 1 — opt-in fast path: when set to
    #: ``"objective_minimal"`` the per-trial fold backtests skip every disk
    #: artifact write (parquet, jsonl, json, markdown, promotion checklist,
    #: suitability decision) and the objective scores from the in-memory
    #: :class:`BacktestResult`. Default ``"full"`` preserves the legacy
    #: ``report.json``-reading path; Phase 5 flips this on for the actual
    #: optuna configs after parity is proven.
    objective_artifact_mode: Literal["full", "objective_minimal"] = "full"
    #: Speedup report §5.3 / §11.2 Phase 3 — opt-in: route per-fold supplier
    #: calls through the Bowaka-local LRU adapter
    #: (:class:`bowaka_v2_lab.data.cached_suppliers.CachedSessionMarketData`)
    #: instead of `bowaka_common.marketdata.MarketDataStore` directly. The
    #: cache eliminates repeated Parquet reads while preserving the
    #: ``[start, end]`` inclusive boundary semantics and the `quote_supplier`
    #: dict shape exactly. Default ``False`` until Phase 3 parity is proven;
    #: Phase 5 flips this on for the actual optuna configs.
    cached_suppliers: bool = False
    #: Speedup report §6.1 / §11.3 Phase 5 — process-parallel launcher
    #: knobs. Free-form dict so the dispatcher can read additive fields
    #: (``memory_reserve_gib``, ``max_workers``, ``strict_parallel``,
    #: ``blas_thread_pin``) without further schema churn.
    parallel: dict[str, Any] = Field(default_factory=dict)
    #: Speedup report §6.2 / §11.2 Phase 7 — conservative fold-level
    #: pruning. Free-form dict so the runner can read additive knobs
    #: without schema churn. Recognised keys: ``enabled`` (bool),
    #: ``min_completed_trials_before_pruning`` (int),
    #: ``catastrophic_floor`` (float),
    #: ``use_running_median_after_warmup`` (bool),
    #: ``allow_pruned_in_promotion`` (bool). Default empty dict ≡
    #: pruning disabled.
    pruning: dict[str, Any] = Field(default_factory=dict)
    #: Speedup report §6.4 / matrix doc §17 Phase 8 — scan-matrix
    #: acceleration knobs (default disabled). Free-form dict;
    #: recognised keys (under ``acceleration.scan_matrix``):
    #: ``enabled`` (bool), ``build_if_missing`` (bool), ``scope`` (str),
    #: ``separate_holdout_matrix`` (bool), ``root`` (str),
    #: ``dtype_policy`` (str), ``storage_format`` (str),
    #: ``precompute_workers`` (int), ``max_optuna_workers`` (int),
    #: ``require_parity_manifest`` (bool),
    #: ``fail_on_matrix_sensitive_search_space`` (bool),
    #: ``allow_full_history_matrix`` (bool).
    acceleration: dict[str, Any] = Field(default_factory=dict)
    #: Speedup report §9 / Phase 10 — expanded robustness:
    #: ``top_k_replays`` (int, default 3), ``sensitivity`` (dict with
    #: ``enabled``, ``n_steps``), ``stress`` (dict with ``enabled``,
    #: ``floors``). Default empty dict ≡ legacy single-best replay.
    robustness: dict[str, Any] = Field(default_factory=dict)
    walkforward: dict[str, Any] = Field(default_factory=dict)
    search_space_overrides: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_n_startup_trials(self) -> "OptunaConfig":
        if self.n_startup_trials is not None and not (
            0 <= self.n_startup_trials <= self.n_trials
        ):
            raise ValueError(
                f"optuna.n_startup_trials ({self.n_startup_trials}) must be in "
                f"[0, n_trials={self.n_trials}]"
            )
        return self


class ReconcileConfig(_StrictBase):
    paper_logs_root: Optional[str] = None
    symbol_window_seconds: int = 120


class PromotionConfig(_StrictBase):
    target_tier: Literal["research_only", "backtesting_only", "paper_candidate", "live_candidate"] = "backtesting_only"
    #: Minimum closed-trade count a run must produce to clear the promotion
    #: gate's ``qr.09_min_trade_count`` check (realism Phase 8). A run with
    #: fewer trades is statistically uninformative and cannot be promoted.
    min_trade_count: int = Field(default=30, ge=0)


class BowakaV2Config(_StrictBase):
    strategy_id: Literal["bowaka_v2"]
    strategy_version: str = "0.1.0"
    # Declares which strategy the simulator reproduces (parity / realism / smoke).
    simulation: SimulationConfig = Field(default_factory=SimulationConfig)
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

    @model_validator(mode="after")
    def _require_full_signals_in_realism_modes(self) -> "BowakaV2Config":
        """A real-mode config must set every live signal gate.

        In ``current_code_parity`` / ``intended_realism`` (and not
        ``allow_research_relaxed``) the simulator must reproduce the live gate
        set — a missing threshold would silently disable a gate.
        """
        if (
            self.simulation.mode in ("current_code_parity", "intended_realism")
            and not self.simulation.allow_research_relaxed
        ):
            missing = [
                gate
                for gate in _REALISM_REQUIRED_SIGNAL_GATES
                if getattr(self.signals, gate) is None
            ]
            if missing:
                raise ValueError(
                    f"simulation.mode={self.simulation.mode!r} requires every live "
                    f"signal gate to be set; missing: {sorted(missing)}. Set them, "
                    f"or set simulation.allow_research_relaxed: true for a research run."
                )
        return self

    @model_validator(mode="after")
    def _resolve_require_adjusted_daily_bars(self) -> "BowakaV2Config":
        """Enforce / resolve ``market_data.require_adjusted_daily_bars``.

        The field defaults to ``None`` (unset). The live contract requires
        adjusted daily bars (``data.require_adjusted_daily_bars: true``), so a
        real-mode config that omits the flag would silently allow raw daily
        baselines — a config defect.

        - ``intended_realism`` / ``current_code_parity`` — the flag MUST be set
          explicitly (by the loader / the contract->config mapper). Unset raises.
        - ``smoke_fixture`` — synthetic plumbing data; an unset flag resolves to
          the historical ``False`` default.

        After validation ``require_adjusted_daily_bars`` is always a concrete
        ``bool``, so the data-quality layer / run manifest never see ``None``.
        """
        if self.market_data.require_adjusted_daily_bars is None:
            if self.simulation.mode in ("intended_realism", "current_code_parity"):
                raise ValueError(
                    f"simulation.mode={self.simulation.mode!r} requires "
                    f"market_data.require_adjusted_daily_bars to be set explicitly "
                    f"(the live contract sets data.require_adjusted_daily_bars: true). "
                    f"Generate the config with `bowaka-v2-lab import-actual-config`, "
                    f"or set the field explicitly in the YAML."
                )
            # smoke_fixture — resolve the unset flag to the historical default.
            self.market_data.require_adjusted_daily_bars = False
        return self
