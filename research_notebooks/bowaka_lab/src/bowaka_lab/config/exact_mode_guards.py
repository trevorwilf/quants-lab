"""Fail-fast invariants for ``project.fidelity_mode == "exact"``.

Exact mode pins the lab to the source-strategy paper-mode YAML semantics so the
backtest cannot silently drift from the live contract. Each invariant accrues an
error message; missing or wrong values raise a single aggregate ``ValueError``.
Later phases extend this with sizing (Phase 5), confirmation (Phase 3), and
signal-fade (Phase 6) assertions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from bowaka_lab.config.models import BowakaBacktestConfig


_REQUIRED_BLOCKED = {"TSLL", "CONL", "SMCX"}


def assert_exact_mode_invariants(
    cfg: "BowakaBacktestConfig",
    *,
    asset_snapshot: pd.DataFrame | None = None,
) -> None:
    """Raise ``ValueError`` if a config tagged ``fidelity_mode=exact`` drifted.

    Pass-through for ``research`` mode — this function is a no-op outside exact.

    Parameters
    ----------
    cfg
        Loaded ``BowakaBacktestConfig``.
    asset_snapshot
        Optional. When ``cfg.is_exact_mode`` and the caller has loaded an
        asset snapshot, pass it in so the guard can fail closed on an empty
        snapshot. Callers that haven't loaded one yet can omit this — the
        check is skipped.
    """
    if not cfg.is_exact_mode:
        return

    errs: list[str] = []

    if not cfg.universe.ticker_blocklist:
        errs.append("exact mode requires universe.ticker_blocklist non-empty")
    elif not _REQUIRED_BLOCKED.issubset(set(cfg.universe.ticker_blocklist)):
        errs.append(
            f"exact mode requires {sorted(_REQUIRED_BLOCKED)} present in ticker_blocklist; "
            f"got {sorted(cfg.universe.ticker_blocklist)}"
        )

    if not cfg.universe.exclude_leveraged_etp:
        errs.append("exact mode requires universe.exclude_leveraged_etp=true")
    if not cfg.universe.exclude_inverse_etp:
        errs.append("exact mode requires universe.exclude_inverse_etp=true")
    if not cfg.universe.exclude_etn:
        errs.append("exact mode requires universe.exclude_etn=true")

    if not cfg.realism.adv_tier_caps:
        errs.append("exact mode requires realism.adv_tier_caps non-empty")

    if cfg.signal_fade.enabled:
        errs.append(
            "exact mode: signal_fade.enabled must be false (source default after the "
            "2026-05-15 incident; flip only after a counterfactual study validates "
            "the thresholds)"
        )

    if asset_snapshot is not None and asset_snapshot.empty:
        errs.append(
            "exact mode: asset_snapshot is empty — instrument-class filtering "
            "cannot run. Generate an asset snapshot first (notebook 01)."
        )

    if errs:
        raise ValueError("exact-mode invariant failures:\n  - " + "\n  - ".join(errs))
