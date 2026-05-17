"""Counterfactual grid generator and outcome simulator.

The counterfactual engine generates a cartesian product over

  entry_rule × stop_pct × target_pct × max_hold_days × signal_fade_threshold ×
  stop_manager_model

for both passed and rejected candidates. For each combination, it answers:

  - would_enter (True/False)
  - entry_price, exit_price, exit_reason
  - mfe / mae
  - first_touch
  - pnl_pct

Outcomes are stored to Parquet at ``backtests/run_id=<run_id>/counterfactuals.parquet``
and Mongo collection ``bowaka_counterfactuals``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date
from itertools import product
from typing import Any, Iterable

import pandas as pd

from bowaka_lab.config.models import CounterfactualConfig, ExitConfig
from bowaka_lab.sim.ambiguity import resolve as resolve_ambiguity
from bowaka_lab.sim.fill_model import BowakaFillModel
from bowaka_lab.sim.stop_manager import get_stop_manager
from bowaka_lab.utils.ids import counterfactual_id


@dataclass(frozen=True)
class CounterfactualVariant:
    entry_rule: str
    stop_pct: float
    target_pct: float
    max_hold_days: int
    signal_fade_threshold: int | None
    stop_manager_model: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CounterfactualOutcome:
    counterfactual_id: str
    symbol: str
    signal_date: date
    trade_date: date
    prefilter_rank: int
    passed_actual_prefilter: bool
    variant: CounterfactualVariant
    would_enter: bool
    entry_price: float | None
    exit_price: float | None
    exit_reason: str
    pnl_pct: float
    mfe_pct: float
    mae_pct: float
    first_touch: str
    diagnostics: dict = field(default_factory=dict)


def build_variant_grid(cfg: CounterfactualConfig) -> list[CounterfactualVariant]:
    """Enumerate all counterfactual variants from a config."""
    variants: list[CounterfactualVariant] = []
    for er, sp, tp, mh, fade, sm in product(
        cfg.entry_rules,
        cfg.stop_pct,
        cfg.target_pct,
        cfg.max_hold_days,
        cfg.signal_fade_thresholds,
        cfg.stop_manager_models,
    ):
        variants.append(
            CounterfactualVariant(
                entry_rule=er,
                stop_pct=float(sp),
                target_pct=float(tp),
                max_hold_days=int(mh),
                signal_fade_threshold=None if fade is None else int(fade),
                stop_manager_model=sm,
            )
        )
    return variants


def _entry_time_for_rule(rule: str, trade_date: date) -> pd.Timestamp:
    if not rule.startswith("fixed_time_"):
        # opening_range / vwap_reclaim / etc. fall back to 09:45 ET for v1.
        hhmm = "0945"
    else:
        hhmm = rule.split("fixed_time_", 1)[1]
    hh, mm = hhmm[:2], hhmm[2:]
    ts = pd.Timestamp(trade_date).tz_localize("America/New_York") + pd.Timedelta(hours=int(hh), minutes=int(mm))
    return ts.tz_convert("UTC")


def simulate_variant(
    *,
    symbol: str,
    signal_date: date,
    trade_date: date,
    prefilter_rank: int,
    passed_actual_prefilter: bool,
    variant: CounterfactualVariant,
    minute_bars: pd.DataFrame,
    fill_model: BowakaFillModel,
    ambiguous_bar_policy: str = "stop_first",
    target_fill_policy: str = "limit_touch",
    stop_gap_policy: str = "next_available_open",
    stop_slippage_pct: float = 0.0,
) -> CounterfactualOutcome:
    """Simulate a single counterfactual variant against minute_bars for one symbol-day.

    ``minute_bars`` should already be filtered to the symbol and the trade_date's
    session.
    """
    cfid = counterfactual_id(symbol=symbol, trade_date=trade_date, variant=variant.as_dict())
    if minute_bars.empty:
        return CounterfactualOutcome(
            counterfactual_id=cfid,
            symbol=symbol,
            signal_date=signal_date,
            trade_date=trade_date,
            prefilter_rank=prefilter_rank,
            passed_actual_prefilter=passed_actual_prefilter,
            variant=variant,
            would_enter=False,
            entry_price=None,
            exit_price=None,
            exit_reason="no_data",
            pnl_pct=0.0,
            mfe_pct=0.0,
            mae_pct=0.0,
            first_touch="none",
            diagnostics={"reason": "empty_minute_bars"},
        )

    df = minute_bars.sort_values("timestamp").reset_index(drop=True)
    entry_time = _entry_time_for_rule(variant.entry_rule, trade_date)
    eligible = df[df["timestamp"] >= entry_time]
    if eligible.empty:
        return CounterfactualOutcome(
            counterfactual_id=cfid,
            symbol=symbol,
            signal_date=signal_date,
            trade_date=trade_date,
            prefilter_rank=prefilter_rank,
            passed_actual_prefilter=passed_actual_prefilter,
            variant=variant,
            would_enter=False,
            entry_price=None,
            exit_price=None,
            exit_reason="no_entry_bar",
            pnl_pct=0.0,
            mfe_pct=0.0,
            mae_pct=0.0,
            first_touch="none",
            diagnostics={"reason": "no_bar_at_or_after_entry_time"},
        )

    entry_bar = eligible.iloc[0]
    entry_fill = fill_model.buy_from_bar(entry_bar.to_dict())
    entry_price = entry_fill.fill_price
    stop_price = entry_price * (1.0 - variant.stop_pct)
    target_price = entry_price * (1.0 + variant.target_pct)

    rest = eligible.iloc[1:].copy()
    mfe_high = entry_price
    mae_low = entry_price
    stop_mgr = get_stop_manager(variant.stop_manager_model)

    exit_price = None
    exit_reason = "time_stop"
    first_touch = "none"

    for _, bar in rest.iterrows():
        bar_high = float(bar["high"])
        bar_low = float(bar["low"])
        bar_open = float(bar["open"])
        mfe_high = max(mfe_high, bar_high)
        mae_low = min(mae_low, bar_low)
        mfe_pct = mfe_high / entry_price - 1.0

        update = stop_mgr.maybe_update(entry_price=entry_price, current_stop=stop_price, mfe_pct=mfe_pct)
        if update is not None:
            stop_price = update.new_stop_price

        # Gap-through-stop fires immediately.
        if bar_open <= stop_price:
            exit_price = bar_open if stop_gap_policy == "next_available_open" else stop_price
            exit_reason = "stop_gap"
            first_touch = "stop"
            break

        resolution = resolve_ambiguity(
            bar_high=bar_high,
            bar_low=bar_low,
            stop_price=stop_price,
            target_price=target_price,
            policy=ambiguous_bar_policy,
        )
        if resolution.outcome == "stop":
            exit_price = stop_price * (1.0 - stop_slippage_pct)
            exit_reason = "ambiguous_bar_stop" if resolution.ambiguous_bar else "stop_hit"
            first_touch = "stop"
            break
        if resolution.outcome == "target":
            exit_price = target_price if target_fill_policy == "limit_touch" else bar_open
            exit_reason = "ambiguous_bar_target" if resolution.ambiguous_bar else "target_hit"
            first_touch = "target"
            break

    if exit_price is None:
        last_bar = df.iloc[-1]
        exit_price = float(last_bar["close"])
        exit_reason = "time_stop"

    return CounterfactualOutcome(
        counterfactual_id=cfid,
        symbol=symbol,
        signal_date=signal_date,
        trade_date=trade_date,
        prefilter_rank=prefilter_rank,
        passed_actual_prefilter=passed_actual_prefilter,
        variant=variant,
        would_enter=True,
        entry_price=entry_price,
        exit_price=exit_price,
        exit_reason=exit_reason,
        pnl_pct=exit_price / entry_price - 1.0,
        mfe_pct=mfe_high / entry_price - 1.0,
        mae_pct=mae_low / entry_price - 1.0,
        first_touch=first_touch,
    )


def run_grid_for_candidates(
    *,
    candidates: pd.DataFrame,
    minute_bars_by_symbol: dict[str, pd.DataFrame],
    cfg: CounterfactualConfig,
    fill_model: BowakaFillModel,
    signal_date: date,
    trade_date: date,
) -> pd.DataFrame:
    """Run all variants × all candidates and return a tidy outcomes DataFrame.

    ``candidates`` must include columns ``symbol``, ``rank``, ``passed_prefilter``.
    Rejected candidates are included when ``cfg.include_rejected_candidates``.
    """
    variants = build_variant_grid(cfg)
    rows: list[dict] = []
    eligible = candidates if cfg.include_rejected_candidates else candidates[candidates.get("passed_prefilter", False)]
    for _, row in eligible.iterrows():
        sym = row["symbol"]
        bars = minute_bars_by_symbol.get(sym, pd.DataFrame())
        for v in variants:
            outcome = simulate_variant(
                symbol=sym,
                signal_date=signal_date,
                trade_date=trade_date,
                prefilter_rank=int(row.get("rank", 0) or 0),
                passed_actual_prefilter=bool(row.get("passed_prefilter", False)),
                variant=v,
                minute_bars=bars,
                fill_model=fill_model,
            )
            rec = asdict(outcome)
            rec["variant"] = v.as_dict()
            rows.append(rec)
    return pd.DataFrame(rows)


def persist_outcomes(outcomes: pd.DataFrame, *, parquet_path=None, mongo_store=None, run_id: str | None = None) -> None:
    """Persist outcomes to Parquet and/or Mongo.

    Parquet does not allow empty-struct columns; any dict-typed column is
    serialized to a JSON string before writing so the file is round-trippable.
    """
    if parquet_path is not None:
        import json as _json
        from pathlib import Path as _P

        path = _P(parquet_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df = outcomes.copy()
        for col in df.columns:
            if df[col].dtype == object:
                if df[col].map(lambda v: isinstance(v, dict)).any():
                    df[col] = df[col].map(lambda v: _json.dumps(v, default=str) if isinstance(v, dict) else v)
        df.to_parquet(path, index=False)
    if mongo_store is not None and not outcomes.empty:
        docs = []
        for _, row in outcomes.iterrows():
            d = row.to_dict()
            if run_id is not None:
                d["backtest_run_id"] = run_id
            docs.append(d)
        mongo_store.insert_many("bowaka_counterfactuals", docs)
