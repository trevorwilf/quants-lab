"""Stop-manager shadow models.

Three models are available out of the box:

- ``none`` — never adjusts the stop.
- ``breakeven_after_5pct`` — once MFE >= 5%, raises the stop to entry price.
- ``mfe_ladder_v1`` — staircase: MFE 5% → BE; MFE 8% → +3% of entry; MFE 12% → +6%.

The model is evaluated bar-by-bar and emits a ``StopUpdate`` whenever the stop
should change. Callers (counterfactual engine) decide whether to actually
re-stop the position or to log shadow values.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class StopUpdate:
    new_stop_price: float
    reason: str


class StopManager(Protocol):
    name: str

    def maybe_update(self, *, entry_price: float, current_stop: float, mfe_pct: float) -> StopUpdate | None:
        ...


class NoOpStopManager:
    name = "none"

    def maybe_update(self, *, entry_price: float, current_stop: float, mfe_pct: float) -> StopUpdate | None:
        return None


class BreakevenAfter5PctStopManager:
    name = "breakeven_after_5pct"

    def __init__(self, *, trigger: float = 0.05):
        self.trigger = trigger

    def maybe_update(self, *, entry_price: float, current_stop: float, mfe_pct: float) -> StopUpdate | None:
        be_stop = entry_price
        if mfe_pct >= self.trigger and current_stop < be_stop:
            return StopUpdate(new_stop_price=be_stop, reason="breakeven_after_5pct")
        return None


class MfeLadderStopManager:
    name = "mfe_ladder_v1"

    def __init__(self, *, ladder: list[tuple[float, float]] | None = None):
        # Each (mfe_min, stop_at_pct_of_entry) tier. Sorted ascending by mfe_min.
        self.ladder = sorted(ladder or [(0.05, 0.00), (0.08, 0.03), (0.12, 0.06)], key=lambda t: t[0])

    def maybe_update(self, *, entry_price: float, current_stop: float, mfe_pct: float) -> StopUpdate | None:
        target_pct: float | None = None
        for mfe_min, stop_pct in self.ladder:
            if mfe_pct >= mfe_min:
                target_pct = stop_pct
        if target_pct is None:
            return None
        new_stop = entry_price * (1.0 + target_pct)
        if new_stop > current_stop:
            return StopUpdate(new_stop_price=new_stop, reason=f"mfe_ladder>={target_pct:.2f}")
        return None


_REGISTRY: dict[str, type[StopManager]] = {
    "none": NoOpStopManager,
    "breakeven_after_5pct": BreakevenAfter5PctStopManager,
    "mfe_ladder_v1": MfeLadderStopManager,
}


def get_stop_manager(name: str, **kw) -> StopManager:
    cls = _REGISTRY.get(name)
    if cls is None:
        raise ValueError(f"Unknown stop manager {name!r}; known: {sorted(_REGISTRY)}")
    return cls(**kw)


def list_stop_managers() -> list[str]:
    return sorted(_REGISTRY)
