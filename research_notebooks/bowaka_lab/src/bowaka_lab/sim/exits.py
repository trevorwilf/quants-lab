"""Exit resolution: stop, target, time-stop, gap-through-stop, ambiguity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Literal

import pandas as pd

from bowaka_lab.config.models import ExitConfig
from bowaka_lab.sim.ambiguity import resolve as resolve_ambiguity
from bowaka_lab.sim.fill_model import BowakaFillModel
from bowaka_lab.sim.positions import SimulatedPosition


@dataclass(frozen=True)
class ExitEvent:
    fill_price: float
    fill_time: pd.Timestamp
    exit_reason: Literal[
        "target_hit",
        "stop_hit",
        "stop_gap",
        "time_stop",
        "ambiguous_bar_stop",
        "ambiguous_bar_target",
        "signal_fade",
        "manual",
    ]
    ambiguous_bar: bool = False
    diagnostics: dict = None  # type: ignore[assignment]


def evaluate_bar_exit(
    *,
    position: SimulatedPosition,
    bar: dict,
    cfg: ExitConfig,
    fill_model: BowakaFillModel,
) -> ExitEvent | None:
    """Evaluate stop / target / gap-through-stop / ambiguous-bar exits.

    Bar ordering rule (matches ``[Report §F]``):

    1. If session open is at or below stop, stop_gap fires immediately.
    2. Otherwise, evaluate ambiguity policy on the bar's [low, high].
    3. Caller is responsible for emitting ``time_stop`` after the bar.
    """
    bar_high = float(bar["high"])
    bar_low = float(bar["low"])
    bar_open = float(bar["open"])
    ts = pd.Timestamp(bar["timestamp"])

    if bar_open <= position.stop_price:
        # Gap-through-stop. Fill at the open under next_available_open policy.
        fill_price = fill_model.stop_fill(
            stop_price=position.stop_price,
            intrabar_low=bar_low,
            bar_open=bar_open,
            stop_gap_policy=cfg.stop_gap_policy,
            stop_slippage_pct=cfg.stop_slippage_pct,
        )
        return ExitEvent(
            fill_price=fill_price,
            fill_time=ts,
            exit_reason="stop_gap",
            ambiguous_bar=False,
            diagnostics={"bar_open": bar_open, "stop_price": position.stop_price},
        )

    resolution = resolve_ambiguity(
        bar_high=bar_high,
        bar_low=bar_low,
        stop_price=position.stop_price,
        target_price=position.target_price,
        policy=cfg.ambiguous_bar_policy,
    )
    if resolution.outcome == "stop":
        fill_price = fill_model.stop_fill(
            stop_price=position.stop_price,
            intrabar_low=bar_low,
            bar_open=bar_open,
            stop_gap_policy=cfg.stop_gap_policy,
            stop_slippage_pct=cfg.stop_slippage_pct,
        )
        reason: Literal[
            "target_hit",
            "stop_hit",
            "stop_gap",
            "time_stop",
            "ambiguous_bar_stop",
            "ambiguous_bar_target",
            "signal_fade",
            "manual",
        ] = "ambiguous_bar_stop" if resolution.ambiguous_bar else "stop_hit"
        return ExitEvent(
            fill_price=fill_price,
            fill_time=ts,
            exit_reason=reason,
            ambiguous_bar=resolution.ambiguous_bar,
            diagnostics={"resolution": resolution.reason},
        )

    if resolution.outcome == "target":
        fill_price = fill_model.target_fill(
            target_price=position.target_price,
            intrabar_high=bar_high,
            bar_open=bar_open,
            target_fill_policy=cfg.target_fill_policy,
        )
        reason = "ambiguous_bar_target" if resolution.ambiguous_bar else "target_hit"
        return ExitEvent(
            fill_price=fill_price,
            fill_time=ts,
            exit_reason=reason,
            ambiguous_bar=resolution.ambiguous_bar,
            diagnostics={"resolution": resolution.reason},
        )

    return None


def is_time_stop_due(*, today_session: date, max_hold_exit_date: date) -> bool:
    return today_session >= max_hold_exit_date
